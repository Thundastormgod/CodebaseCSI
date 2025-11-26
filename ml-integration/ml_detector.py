"""
Machine Learning Detector for Codebase CSI v2.0
Integrates CodeBERT-based model with rule-based analyzers
"""

from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
from transformers import RobertaTokenizer, RobertaModel
import numpy as np


class CodebaseCSIModel(nn.Module):
    """
    Deep learning model for AI code detection.
    Uses CodeBERT embeddings + custom classification head.
    """
    
    def __init__(self, num_rule_features: int = 6):
        super().__init__()
        
        # Load pre-trained CodeBERT
        self.codebert = RobertaModel.from_pretrained('microsoft/codebert-base')
        
        # Feature dimensions
        self.codebert_dim = 768
        self.rule_dim = num_rule_features
        self.metadata_dim = 10
        self.total_dim = self.codebert_dim + self.rule_dim + self.metadata_dim
        
        # Custom classification head
        self.classifier = nn.Sequential(
            nn.Linear(self.total_dim, 512),
            nn.LayerNorm(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(512, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(128, 1),
            nn.Sigmoid()  # Output: 0.0 (human) to 1.0 (AI)
        )
        
        # Confidence estimator (parallel head)
        self.confidence_estimator = nn.Sequential(
            nn.Linear(self.total_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 1),
            nn.Sigmoid()  # Output: 0.0 (uncertain) to 1.0 (confident)
        )
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        rule_scores: torch.Tensor,
        metadata: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Returns:
            (prediction, confidence) tuple
        """
        # Get CodeBERT embeddings
        outputs = self.codebert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Use [CLS] token embedding
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [batch, 768]
        
        # Concatenate all features
        combined_features = torch.cat([
            cls_embedding,
            rule_scores,
            metadata
        ], dim=1)  # [batch, 784]
        
        # Predict AI confidence
        prediction = self.classifier(combined_features)
        
        # Estimate model confidence
        confidence = self.confidence_estimator(combined_features)
        
        return prediction, confidence


class MLDetector:
    """
    Machine learning detector that integrates with rule-based analyzers.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = 'cpu',
        use_quantization: bool = True
    ):
        """
        Initialize ML detector.
        
        Args:
            model_path: Path to trained model weights
            device: 'cpu' or 'cuda'
            use_quantization: Use quantized model for faster inference
        """
        self.device = torch.device(device)
        self.tokenizer = RobertaTokenizer.from_pretrained('microsoft/codebert-base')
        
        # Load model
        self.model = CodebaseCSIModel()
        
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        self.model.to(self.device)
        self.model.eval()
        
        # Quantize for faster inference
        if use_quantization and device == 'cpu':
            self.model = torch.quantization.quantize_dynamic(
                self.model,
                {nn.Linear},
                dtype=torch.qint8
            )
    
    def extract_metadata(self, code: str, file_path: str) -> torch.Tensor:
        """
        Extract metadata features from code.
        
        Returns:
            Tensor of shape [10] with metadata features
        """
        lines = code.split('\n')
        
        features = [
            len(code),                          # File size in chars
            len(lines),                         # Number of lines
            len(code.split()),                  # Number of tokens
            code.count('\n\n'),                 # Blank line count
            code.count('#'),                    # Comment count
            max(len(line) for line in lines),   # Max line length
            sum(len(line) for line in lines) / max(len(lines), 1),  # Avg line length
            code.count('def ') + code.count('class '),  # Function/class count
            1 if file_path.endswith('.py') else 0,      # Is Python
            len(set(code.split())) / max(len(code.split()), 1),  # Unique token ratio
        ]
        
        # Normalize features
        features = np.array(features, dtype=np.float32)
        features = (features - features.mean()) / (features.std() + 1e-8)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def predict(
        self,
        code: str,
        file_path: str,
        rule_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Predict AI confidence for code.
        
        Args:
            code: Source code content
            file_path: Path to file
            rule_scores: Dictionary of rule-based analyzer scores
        
        Returns:
            Dictionary with prediction results
        """
        # Tokenize code
        encoding = self.tokenizer(
            code,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Prepare rule scores tensor
        rule_score_values = [
            rule_scores.get('pattern', 0.0),
            rule_scores.get('statistical', 0.0),
            rule_scores.get('security', 0.0),
            rule_scores.get('emoji', 0.0),
            rule_scores.get('semantic', 0.0),
            rule_scores.get('architectural', 0.0),
        ]
        rule_tensor = torch.tensor([rule_score_values], dtype=torch.float32).to(self.device)
        
        # Extract metadata
        metadata = self.extract_metadata(code, file_path).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            prediction, confidence = self.model(
                input_ids,
                attention_mask,
                rule_tensor,
                metadata
            )
        
        return {
            'ml_score': prediction.item(),
            'ml_confidence': confidence.item(),
        }


class EnsembleDetector:
    """
    Ensemble detector combining rule-based and ML predictions.
    """
    
    def __init__(self, ml_detector: Optional[MLDetector] = None):
        """
        Initialize ensemble detector.
        
        Args:
            ml_detector: ML detector instance (None for rule-based only)
        """
        self.ml_detector = ml_detector
        self.ml_available = ml_detector is not None
    
    def predict(
        self,
        code: str,
        file_path: str,
        rule_scores: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Ensemble prediction combining rules and ML.
        
        Args:
            code: Source code content
            file_path: Path to file
            rule_scores: Dictionary of rule-based analyzer scores
        
        Returns:
            Dictionary with ensemble results
        """
        # Calculate rule-based confidence
        rule_confidence = self._calculate_rule_confidence(rule_scores)
        
        result = {
            'rule_confidence': rule_confidence,
            'rule_scores': rule_scores,
        }
        
        # Add ML prediction if available
        if self.ml_available:
            ml_result = self.ml_detector.predict(code, file_path, rule_scores)
            result.update(ml_result)
            
            # Calculate ensemble confidence
            ml_score = ml_result['ml_score']
            ml_conf = ml_result['ml_confidence']
            
            # Adaptive weighting based on ML confidence
            if ml_conf > 0.8:
                # High ML confidence: trust ML more
                weights = {'ml': 0.7, 'rules': 0.3}
            elif ml_conf > 0.5:
                # Medium ML confidence: balanced
                weights = {'ml': 0.5, 'rules': 0.5}
            else:
                # Low ML confidence: trust rules more
                weights = {'ml': 0.3, 'rules': 0.7}
            
            ensemble_confidence = (
                weights['ml'] * ml_score +
                weights['rules'] * rule_confidence
            )
            
            # Check for disagreement
            disagreement = abs(ml_score - rule_confidence)
            
            result.update({
                'ensemble_confidence': ensemble_confidence,
                'weights': weights,
                'disagreement': disagreement,
                'requires_review': disagreement > 0.3,
            })
        else:
            # Fallback to rule-based only
            result['ensemble_confidence'] = rule_confidence
            result['ml_available'] = False
        
        return result
    
    def _calculate_rule_confidence(self, rule_scores: Dict[str, float]) -> float:
        """
        Calculate weighted average of rule-based scores.
        """
        weights = {
            'pattern': 0.25,
            'statistical': 0.20,
            'security': 0.20,
            'emoji': 0.15,
            'semantic': 0.10,
            'architectural': 0.05,
        }
        
        total = 0.0
        total_weight = 0.0
        
        for analyzer, weight in weights.items():
            if analyzer in rule_scores:
                total += rule_scores[analyzer] * weight
                total_weight += weight
        
        return total / total_weight if total_weight > 0 else 0.0


# Example usage
if __name__ == '__main__':
    # Example: Rule-based only (v1.1)
    print("=" * 60)
    print("Example 1: Rule-Based Only (Fallback Mode)")
    print("=" * 60)
    
    ensemble = EnsembleDetector()
    
    code = """
def calculate_sum(numbers):
    # Calculate the sum of all numbers in the list
    return sum(numbers)
"""
    
    rule_scores = {
        'pattern': 0.6,
        'statistical': 0.7,
        'security': 0.3,
        'emoji': 0.8,
        'semantic': 0.5,
        'architectural': 0.2,
    }
    
    result = ensemble.predict(code, "example.py", rule_scores)
    print(f"Rule Confidence: {result['rule_confidence']:.2f}")
    print(f"Ensemble Confidence: {result['ensemble_confidence']:.2f}")
    
    # Example: With ML (v2.0)
    print("\n" + "=" * 60)
    print("Example 2: Rule-Based + ML (Full Ensemble)")
    print("=" * 60)
    print("Note: Requires trained model weights")
    print("To train model, see training/train_model.py")
    
    """
    # Uncomment when model is trained:
    
    ml_detector = MLDetector(
        model_path='models/codebase_csi_v2.pt',
        device='cpu',
        use_quantization=True
    )
    
    ensemble = EnsembleDetector(ml_detector)
    result = ensemble.predict(code, "example.py", rule_scores)
    
    print(f"Rule Confidence: {result['rule_confidence']:.2f}")
    print(f"ML Score: {result['ml_score']:.2f}")
    print(f"ML Confidence: {result['ml_confidence']:.2f}")
    print(f"Ensemble Confidence: {result['ensemble_confidence']:.2f}")
    print(f"Weights: {result['weights']}")
    if result['requires_review']:
        print("⚠️  DISAGREEMENT DETECTED - Manual review recommended")
    """
