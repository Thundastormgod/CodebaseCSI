"""
Data collection and preparation for ML training
Generates labeled dataset from various sources
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
import requests
from datetime import datetime
import time
from tqdm import tqdm


class DataCollector:
    """Collects and prepares training data."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize data collector.
        
        Args:
            output_dir: Directory to save labeled data
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # AI prompt templates for generating samples
        self.ai_prompts = [
            "Write a Python function to {task}",
            "Implement a {algorithm} in {language}",
            "Create a REST API endpoint for {feature}",
            "Write a class that {description}",
            "Fix this code: {code}",
            "Refactor this code: {code}",
            "Add error handling to: {code}",
            "Optimize this function: {code}",
        ]
        
        self.tasks = [
            "calculate factorial",
            "sort a list",
            "reverse a string",
            "find prime numbers",
            "merge two dictionaries",
            "parse JSON data",
            "validate email addresses",
            "generate random passwords",
            "format dates",
            "calculate statistics",
        ]
        
        self.algorithms = [
            "binary search",
            "bubble sort",
            "quicksort",
            "depth-first search",
            "breadth-first search",
            "hash table",
            "linked list",
            "binary tree",
        ]
    
    def collect_human_code(self, num_samples: int = 1000) -> List[Dict]:
        """
        Collect human-written code samples.
        
        Note: This is a placeholder. Real implementation would:
        - Use GitHub API to fetch code
        - Filter by date (pre-2020)
        - Verify human authorship
        - Extract functions/classes
        
        Args:
            num_samples: Number of samples to collect
        
        Returns:
            List of samples with metadata
        """
        print(f"Collecting {num_samples} human-written code samples...")
        
        samples = []
        
        # Placeholder: Generate synthetic "human-like" code
        # In production, this would use GitHub API
        for i in tqdm(range(num_samples)):
            sample = {
                'id': f'human_{i:05d}',
                'code': self._generate_human_like_code(),
                'label': 0.0,  # Human
                'source': 'synthetic_human',
                'language': 'python',
                'timestamp': datetime.now().isoformat(),
                'metadata': self._extract_metadata(self._generate_human_like_code()),
            }
            samples.append(sample)
        
        return samples
    
    def collect_ai_code(self, num_samples: int = 1000) -> List[Dict]:
        """
        Collect AI-generated code samples.
        
        Note: This would use ChatGPT/Claude API in production.
        
        Args:
            num_samples: Number of samples to collect
        
        Returns:
            List of samples with metadata
        """
        print(f"Collecting {num_samples} AI-generated code samples...")
        
        samples = []
        
        # Placeholder: Generate synthetic "AI-like" code
        # In production, this would use GPT-4/Claude API
        for i in tqdm(range(num_samples)):
            prompt = self._generate_prompt()
            
            sample = {
                'id': f'ai_{i:05d}',
                'code': self._generate_ai_like_code(),
                'label': 1.0,  # AI
                'source': 'synthetic_ai',
                'language': 'python',
                'prompt': prompt,
                'timestamp': datetime.now().isoformat(),
                'metadata': self._extract_metadata(self._generate_ai_like_code()),
            }
            samples.append(sample)
        
        return samples
    
    def collect_mixed_code(self, num_samples: int = 500) -> List[Dict]:
        """
        Collect mixed human/AI code (edge cases).
        
        Args:
            num_samples: Number of samples to collect
        
        Returns:
            List of samples with metadata
        """
        print(f"Collecting {num_samples} mixed code samples...")
        
        samples = []
        
        for i in tqdm(range(num_samples)):
            # Mix of human and AI (50-50)
            label = random.uniform(0.4, 0.6)
            
            sample = {
                'id': f'mixed_{i:05d}',
                'code': self._generate_mixed_code(),
                'label': label,
                'source': 'synthetic_mixed',
                'language': 'python',
                'timestamp': datetime.now().isoformat(),
                'metadata': self._extract_metadata(self._generate_mixed_code()),
            }
            samples.append(sample)
        
        return samples
    
    def _generate_prompt(self) -> str:
        """Generate random AI prompt."""
        template = random.choice(self.ai_prompts)
        
        if '{task}' in template:
            return template.format(task=random.choice(self.tasks))
        elif '{algorithm}' in template:
            return template.format(
                algorithm=random.choice(self.algorithms),
                language='Python'
            )
        else:
            return template.format(
                feature='user authentication',
                description='manages user accounts',
                code='def old_func(): pass'
            )
    
    def _generate_human_like_code(self) -> str:
        """Generate synthetic human-like code."""
        # Characteristics: variable names, fewer comments, some inconsistency
        templates = [
            '''def calc(x, y):
    res = x + y
    return res
''',
            '''class MyClass:
    def __init__(self):
        self.val = 0
    
    def inc(self):
        self.val += 1
''',
            '''def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
''',
        ]
        return random.choice(templates)
    
    def _generate_ai_like_code(self) -> str:
        """Generate synthetic AI-like code."""
        # Characteristics: verbose comments, perfect formatting, emojis
        templates = [
            '''def calculate_sum(numbers: list) -> int:
    """
    Calculate the sum of all numbers in the list.
    
    Args:
        numbers: A list of integers
    
    Returns:
        The sum of all numbers
    """
    # Initialize the result variable 🎯
    result = 0
    
    # Iterate through each number in the list
    for number in numbers:
        # Add the current number to the result
        result += number
    
    # Return the final result ✨
    return result
''',
            '''class UserManager:
    """
    A class to manage user accounts.
    
    This class provides methods for creating, updating, and deleting users.
    """
    
    def __init__(self):
        """Initialize the UserManager with an empty user dictionary."""
        self.users = {}
    
    def add_user(self, username: str, email: str) -> bool:
        """
        Add a new user to the system.
        
        Args:
            username: The username for the new user
            email: The email address for the new user
        
        Returns:
            True if user was added successfully, False otherwise
        """
        # Check if user already exists 🔍
        if username in self.users:
            return False
        
        # Add the new user to the dictionary ➕
        self.users[username] = {"email": email}
        
        # Return success status ✅
        return True
''',
        ]
        return random.choice(templates)
    
    def _generate_mixed_code(self) -> str:
        """Generate mixed human/AI code."""
        human = self._generate_human_like_code()
        ai = self._generate_ai_like_code()
        
        # Combine parts from both
        lines = human.split('\n')[:3] + ai.split('\n')[3:]
        return '\n'.join(lines)
    
    def _extract_metadata(self, code: str) -> List[float]:
        """Extract metadata features from code."""
        lines = code.split('\n')
        
        return [
            len(code),                          # File size
            len(lines),                         # Line count
            len(code.split()),                  # Token count
            code.count('\n\n'),                 # Blank lines
            code.count('#'),                    # Comments
            max((len(line) for line in lines), default=0),  # Max line length
            sum(len(line) for line in lines) / max(len(lines), 1),  # Avg line length
            code.count('def ') + code.count('class '),  # Function/class count
            1.0,                                # Is Python
            len(set(code.split())) / max(len(code.split()), 1),  # Unique ratio
        ]
    
    def augment_data(self, samples: List[Dict]) -> List[Dict]:
        """
        Augment data with variations.
        
        Args:
            samples: Original samples
        
        Returns:
            Augmented samples (2x original)
        """
        print("Augmenting data...")
        
        augmented = []
        
        for sample in tqdm(samples):
            # Original
            augmented.append(sample)
            
            # Augmented version
            aug_sample = sample.copy()
            aug_sample['id'] = sample['id'] + '_aug'
            
            # Apply random augmentation
            aug_type = random.choice(['rename', 'format', 'comment'])
            
            if aug_type == 'rename':
                aug_sample['code'] = self._augment_rename(sample['code'])
            elif aug_type == 'format':
                aug_sample['code'] = self._augment_format(sample['code'])
            else:
                aug_sample['code'] = self._augment_comment(sample['code'])
            
            aug_sample['metadata'] = self._extract_metadata(aug_sample['code'])
            augmented.append(aug_sample)
        
        return augmented
    
    def _augment_rename(self, code: str) -> str:
        """Rename variables."""
        # Simple variable name replacement
        replacements = {
            'result': 'output',
            'data': 'items',
            'value': 'val',
            'number': 'num',
        }
        
        for old, new in replacements.items():
            code = code.replace(old, new)
        
        return code
    
    def _augment_format(self, code: str) -> str:
        """Change formatting."""
        # Add/remove blank lines
        lines = code.split('\n')
        
        # Add extra blank line occasionally
        if random.random() > 0.5:
            insert_pos = random.randint(0, len(lines))
            lines.insert(insert_pos, '')
        
        return '\n'.join(lines)
    
    def _augment_comment(self, code: str) -> str:
        """Add/remove comments."""
        if random.random() > 0.5:
            # Add comment
            return '# Added comment\n' + code
        else:
            # Remove comments
            lines = [l for l in code.split('\n') if not l.strip().startswith('#')]
            return '\n'.join(lines)
    
    def save_dataset(self, samples: List[Dict], filename: str):
        """Save dataset to JSON file."""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(samples, f, indent=2)
        
        print(f"✅ Saved {len(samples)} samples to {output_path}")


def main():
    """Main data collection script."""
    print("=" * 60)
    print("Codebase CSI Data Collection")
    print("=" * 60)
    print()
    
    # Configuration
    output_dir = Path('data/labeled')
    num_human = 1000
    num_ai = 1000
    num_mixed = 500
    
    # Initialize collector
    collector = DataCollector(output_dir)
    
    # Collect samples
    print("\n[1/4] Collecting human-written code...")
    human_samples = collector.collect_human_code(num_human)
    
    print("\n[2/4] Collecting AI-generated code...")
    ai_samples = collector.collect_ai_code(num_ai)
    
    print("\n[3/4] Collecting mixed code...")
    mixed_samples = collector.collect_mixed_code(num_mixed)
    
    # Combine all samples
    all_samples = human_samples + ai_samples + mixed_samples
    
    print(f"\nTotal samples collected: {len(all_samples)}")
    print(f"  Human: {len(human_samples)}")
    print(f"  AI: {len(ai_samples)}")
    print(f"  Mixed: {len(mixed_samples)}")
    
    # Augment data
    print("\n[4/4] Augmenting data...")
    augmented_samples = collector.augment_data(all_samples)
    
    print(f"\nTotal samples after augmentation: {len(augmented_samples)}")
    
    # Shuffle
    random.shuffle(augmented_samples)
    
    # Save dataset
    print("\nSaving dataset...")
    collector.save_dataset(augmented_samples, 'training_data.json')
    
    # Save statistics
    stats = {
        'total_samples': len(augmented_samples),
        'human_samples': len(human_samples) * 2,
        'ai_samples': len(ai_samples) * 2,
        'mixed_samples': len(mixed_samples) * 2,
        'generated_at': datetime.now().isoformat(),
    }
    
    with open(output_dir / 'dataset_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Data collection complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review collected data in data/labeled/")
    print("2. (Optional) Add real GitHub/API samples")
    print("3. Run training: python training/train_model.py")


if __name__ == '__main__':
    main()
