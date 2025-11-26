"""
Training script for Codebase CSI ML model
Fine-tunes CodeBERT for AI code detection
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import RobertaTokenizer, get_linear_schedule_with_warmup
from pathlib import Path
import json
from typing import List, Dict, Tuple
from tqdm import tqdm
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
import sys
sys.path.append('..')
from ml_detector import CodebaseCSIModel


class CodeDataset(Dataset):
    """Dataset for code samples with labels."""
    
    def __init__(self, data_dir: Path, tokenizer: RobertaTokenizer, max_length: int = 512):
        """
        Initialize dataset.
        
        Args:
            data_dir: Directory containing labeled code samples
            tokenizer: CodeBERT tokenizer
            max_length: Maximum sequence length
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        
        # Load samples from JSON files
        for json_file in data_dir.glob('*.json'):
            with open(json_file) as f:
                data = json.load(f)
                self.samples.extend(data)
        
        print(f"Loaded {len(self.samples)} samples from {data_dir}")
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        
        # Tokenize code
        encoding = self.tokenizer(
            sample['code'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Get rule-based scores (if available)
        rule_scores = sample.get('rule_scores', {})
        rule_tensor = torch.tensor([
            rule_scores.get('pattern', 0.0),
            rule_scores.get('statistical', 0.0),
            rule_scores.get('security', 0.0),
            rule_scores.get('emoji', 0.0),
            rule_scores.get('semantic', 0.0),
            rule_scores.get('architectural', 0.0),
        ], dtype=torch.float32)
        
        # Get metadata
        metadata = torch.tensor(sample.get('metadata', [0.0] * 10), dtype=torch.float32)
        
        # Get label (0.0 = human, 1.0 = AI)
        label = torch.tensor([sample['label']], dtype=torch.float32)
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'rule_scores': rule_tensor,
            'metadata': metadata,
            'label': label,
        }


class CSILoss(nn.Module):
    """Custom loss combining MSE with consistency loss."""
    
    def __init__(self, consistency_weight: float = 0.3):
        super().__init__()
        self.consistency_weight = consistency_weight
        self.mse = nn.MSELoss()
    
    def forward(
        self,
        predictions: torch.Tensor,
        labels: torch.Tensor,
        rule_scores: torch.Tensor
    ) -> torch.Tensor:
        """
        Calculate loss.
        
        Args:
            predictions: Model predictions [batch, 1]
            labels: Ground truth labels [batch, 1]
            rule_scores: Rule-based scores [batch, 6]
        
        Returns:
            Total loss
        """
        # Primary loss: MSE between prediction and ground truth
        primary_loss = self.mse(predictions, labels)
        
        # Secondary loss: Consistency with rule-based average
        rule_avg = rule_scores.mean(dim=1, keepdim=True)
        consistency_loss = self.mse(predictions, rule_avg)
        
        # Weighted combination
        total_loss = (
            (1 - self.consistency_weight) * primary_loss +
            self.consistency_weight * consistency_loss
        )
        
        return total_loss


def train_epoch(
    model: CodebaseCSIModel,
    dataloader: DataLoader,
    criterion: CSILoss,
    optimizer: optim.Optimizer,
    scheduler: optim.lr_scheduler.LambdaLR,
    device: torch.device
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    progress_bar = tqdm(dataloader, desc='Training')
    for batch in progress_bar:
        # Move to device
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        rule_scores = batch['rule_scores'].to(device)
        metadata = batch['metadata'].to(device)
        labels = batch['label'].to(device)
        
        # Forward pass
        predictions, confidence = model(input_ids, attention_mask, rule_scores, metadata)
        
        # Calculate loss
        loss = criterion(predictions, labels, rule_scores)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        progress_bar.set_postfix({'loss': loss.item()})
    
    return total_loss / len(dataloader)


def evaluate(
    model: CodebaseCSIModel,
    dataloader: DataLoader,
    device: torch.device
) -> Dict[str, float]:
    """Evaluate model on validation set."""
    model.eval()
    all_predictions = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc='Evaluating'):
            # Move to device
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            rule_scores = batch['rule_scores'].to(device)
            metadata = batch['metadata'].to(device)
            labels = batch['label'].to(device)
            
            # Forward pass
            predictions, confidence = model(input_ids, attention_mask, rule_scores, metadata)
            
            all_predictions.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    # Convert to numpy arrays
    predictions = np.array(all_predictions).flatten()
    labels = np.array(all_labels).flatten()
    
    # Binary classification (threshold at 0.5)
    binary_preds = (predictions > 0.5).astype(int)
    binary_labels = (labels > 0.5).astype(int)
    
    # Calculate metrics
    accuracy = accuracy_score(binary_labels, binary_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        binary_labels, binary_preds, average='binary'
    )
    auc_roc = roc_auc_score(binary_labels, predictions)
    mae = np.mean(np.abs(predictions - labels))
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'auc_roc': auc_roc,
        'mae': mae,
    }


def main():
    """Main training script."""
    # Configuration
    CONFIG = {
        'data_dir': Path('data/labeled'),
        'output_dir': Path('models'),
        'batch_size': 16,
        'learning_rate': 2e-5,
        'epochs': 10,
        'warmup_steps': 500,
        'weight_decay': 0.01,
        'max_seq_length': 512,
        'train_split': 0.8,
        'val_split': 0.1,
        'test_split': 0.1,
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'seed': 42,
    }
    
    print("=" * 60)
    print("Codebase CSI ML Training")
    print("=" * 60)
    print(f"Device: {CONFIG['device']}")
    print(f"Batch size: {CONFIG['batch_size']}")
    print(f"Learning rate: {CONFIG['learning_rate']}")
    print(f"Epochs: {CONFIG['epochs']}")
    print()
    
    # Set seed for reproducibility
    torch.manual_seed(CONFIG['seed'])
    np.random.seed(CONFIG['seed'])
    
    # Initialize tokenizer
    print("Loading tokenizer...")
    tokenizer = RobertaTokenizer.from_pretrained('microsoft/codebert-base')
    
    # Load dataset
    print("Loading dataset...")
    dataset = CodeDataset(CONFIG['data_dir'], tokenizer, CONFIG['max_seq_length'])
    
    # Split dataset
    train_size = int(CONFIG['train_split'] * len(dataset))
    val_size = int(CONFIG['val_split'] * len(dataset))
    test_size = len(dataset) - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = random_split(
        dataset, [train_size, val_size, test_size]
    )
    
    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")
    print()
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'])
    test_loader = DataLoader(test_dataset, batch_size=CONFIG['batch_size'])
    
    # Initialize model
    print("Initializing model...")
    model = CodebaseCSIModel()
    device = torch.device(CONFIG['device'])
    model.to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print()
    
    # Initialize optimizer and scheduler
    optimizer = optim.AdamW(
        model.parameters(),
        lr=CONFIG['learning_rate'],
        weight_decay=CONFIG['weight_decay']
    )
    
    total_steps = len(train_loader) * CONFIG['epochs']
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=CONFIG['warmup_steps'],
        num_training_steps=total_steps
    )
    
    # Initialize loss function
    criterion = CSILoss(consistency_weight=0.3)
    
    # Training loop
    best_val_f1 = 0.0
    CONFIG['output_dir'].mkdir(exist_ok=True)
    
    for epoch in range(CONFIG['epochs']):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch + 1}/{CONFIG['epochs']}")
        print(f"{'='*60}")
        
        # Phase 1: Freeze CodeBERT (epochs 1-5)
        if epoch < 5:
            print("Phase 1: Training classifier head only")
            for param in model.codebert.parameters():
                param.requires_grad = False
        else:
            print("Phase 2: Fine-tuning entire model")
            for param in model.codebert.parameters():
                param.requires_grad = True
            # Lower learning rate for fine-tuning
            optimizer.param_groups[0]['lr'] = 1e-6
        
        # Train
        train_loss = train_epoch(model, train_loader, criterion, optimizer, scheduler, device)
        print(f"Train Loss: {train_loss:.4f}")
        
        # Evaluate
        val_metrics = evaluate(model, val_loader, device)
        print(f"\nValidation Metrics:")
        print(f"  Accuracy:  {val_metrics['accuracy']:.4f}")
        print(f"  Precision: {val_metrics['precision']:.4f}")
        print(f"  Recall:    {val_metrics['recall']:.4f}")
        print(f"  F1 Score:  {val_metrics['f1_score']:.4f}")
        print(f"  AUC-ROC:   {val_metrics['auc_roc']:.4f}")
        print(f"  MAE:       {val_metrics['mae']:.4f}")
        
        # Save best model
        if val_metrics['f1_score'] > best_val_f1:
            best_val_f1 = val_metrics['f1_score']
            model_path = CONFIG['output_dir'] / 'codebase_csi_best.pt'
            torch.save(model.state_dict(), model_path)
            print(f"\n✅ Saved best model to {model_path}")
        
        # Save checkpoint
        checkpoint_path = CONFIG['output_dir'] / f'checkpoint_epoch_{epoch + 1}.pt'
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'train_loss': train_loss,
            'val_metrics': val_metrics,
        }, checkpoint_path)
    
    # Final evaluation on test set
    print(f"\n{'='*60}")
    print("Final Evaluation on Test Set")
    print(f"{'='*60}")
    
    # Load best model
    model.load_state_dict(torch.load(CONFIG['output_dir'] / 'codebase_csi_best.pt'))
    test_metrics = evaluate(model, test_loader, device)
    
    print(f"\nTest Metrics:")
    print(f"  Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"  Precision: {test_metrics['precision']:.4f}")
    print(f"  Recall:    {test_metrics['recall']:.4f}")
    print(f"  F1 Score:  {test_metrics['f1_score']:.4f}")
    print(f"  AUC-ROC:   {test_metrics['auc_roc']:.4f}")
    print(f"  MAE:       {test_metrics['mae']:.4f}")
    
    # Save final metrics
    with open(CONFIG['output_dir'] / 'test_metrics.json', 'w') as f:
        json.dump(test_metrics, f, indent=2)
    
    print(f"\n✅ Training complete! Best model saved to {CONFIG['output_dir'] / 'codebase_csi_best.pt'}")


if __name__ == '__main__':
    main()
