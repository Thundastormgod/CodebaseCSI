"""
Integration example: Using ML detector with existing Codebase CSI
Shows how to integrate ml_detector.py with the core detector
"""

import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent.parent / 'src'))
sys.path.append(str(Path(__file__).parent))

from codebase_csi.core.detector import CodebaseDetector
from ml_detector import MLDetector, EnsembleDetector


class EnhancedDetector:
    """
    Enhanced detector that combines rule-based (v1.1) with ML (v2.0).
    """
    
    def __init__(self, ml_model_path: str = None, use_ml: bool = True):
        """
        Initialize enhanced detector.
        
        Args:
            ml_model_path: Path to trained ML model (optional)
            use_ml: Whether to use ML (False = rule-based only)
        """
        # Initialize core rule-based detector
        self.rule_detector = CodebaseDetector()
        
        # Initialize ML detector if available
        self.ml_detector = None
        if use_ml and ml_model_path and Path(ml_model_path).exists():
            try:
                self.ml_detector = MLDetector(
                    model_path=ml_model_path,
                    device='cpu',
                    use_quantization=True
                )
                print(f"✅ ML detector loaded from {ml_model_path}")
            except Exception as e:
                print(f"⚠️  Failed to load ML detector: {e}")
                print("Falling back to rule-based only")
        
        # Initialize ensemble
        self.ensemble = EnsembleDetector(self.ml_detector)
        
        print(f"Detector mode: {'Ensemble (ML + Rules)' if self.ml_detector else 'Rule-based only'}")
    
    def analyze_file(self, file_path: str) -> dict:
        """
        Analyze a single file with ensemble detection.
        
        Args:
            file_path: Path to code file
        
        Returns:
            Enhanced results with both rule-based and ML scores
        """
        # Get rule-based analysis
        rule_result = self.rule_detector.analyze_file(file_path)
        
        # Read code
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Get individual analyzer scores
        rule_scores = {
            'pattern': rule_result['patterns']['confidence'],
            'statistical': rule_result['statistical']['confidence'],
            'security': rule_result['security']['confidence'],
            'emoji': rule_result['emoji']['confidence'],
            'semantic': rule_result.get('semantic', {}).get('confidence', 0.0),
            'architectural': rule_result.get('architectural', {}).get('confidence', 0.0),
        }
        
        # Get ensemble prediction
        ensemble_result = self.ensemble.predict(code, file_path, rule_scores)
        
        # Combine results
        enhanced_result = {
            **rule_result,
            'ensemble': {
                'confidence': ensemble_result['ensemble_confidence'],
                'rule_confidence': ensemble_result['rule_confidence'],
                'classification': self._classify(ensemble_result['ensemble_confidence']),
            }
        }
        
        # Add ML-specific results if available
        if 'ml_score' in ensemble_result:
            enhanced_result['ensemble'].update({
                'ml_score': ensemble_result['ml_score'],
                'ml_confidence': ensemble_result['ml_confidence'],
                'weights': ensemble_result['weights'],
                'disagreement': ensemble_result['disagreement'],
                'requires_review': ensemble_result['requires_review'],
            })
        
        return enhanced_result
    
    def _classify(self, confidence: float) -> str:
        """Classify based on confidence threshold."""
        if confidence >= 0.7:
            return "AI-generated"
        elif confidence >= 0.3:
            return "Mixed/Uncertain"
        else:
            return "Human-written"


def demo_basic():
    """Demo: Basic usage with rule-based only."""
    print("=" * 60)
    print("Demo 1: Rule-Based Detection (v1.1)")
    print("=" * 60)
    
    detector = EnhancedDetector(use_ml=False)
    
    # Example code
    code_file = "example_code.py"
    with open(code_file, 'w') as f:
        f.write("""
def calculate_sum(numbers):
    # Calculate the sum of all numbers 🎯
    result = 0
    for number in numbers:
        result += number
    return result
""")
    
    result = detector.analyze_file(code_file)
    
    print(f"\nFile: {code_file}")
    print(f"Ensemble Confidence: {result['ensemble']['confidence']:.2f}")
    print(f"Classification: {result['ensemble']['classification']}")
    print(f"\nAnalyzer Breakdown:")
    print(f"  Pattern:       {result['patterns']['confidence']:.2f}")
    print(f"  Statistical:   {result['statistical']['confidence']:.2f}")
    print(f"  Security:      {result['security']['confidence']:.2f}")
    print(f"  Emoji:         {result['emoji']['confidence']:.2f}")
    
    # Cleanup
    Path(code_file).unlink()


def demo_ml():
    """Demo: ML-enhanced detection (v2.0)."""
    print("\n" + "=" * 60)
    print("Demo 2: ML-Enhanced Detection (v2.0)")
    print("=" * 60)
    
    # Check if model exists
    model_path = "models/codebase_csi_best.pt"
    if not Path(model_path).exists():
        print(f"\n⚠️  Model not found at {model_path}")
        print("To use ML detection:")
        print("  1. cd ml-integration/data_collection")
        print("  2. python collect_data.py")
        print("  3. cd ../training")
        print("  4. python train_model.py")
        return
    
    detector = EnhancedDetector(ml_model_path=model_path, use_ml=True)
    
    # Example code
    code_file = "example_ml_code.py"
    with open(code_file, 'w') as f:
        f.write("""
def process_data(items: list) -> list:
    \"\"\"
    Process a list of items and return the results.
    
    This function iterates through the items and processes each one.
    
    Args:
        items: A list of items to process
    
    Returns:
        A list of processed items
    \"\"\"
    # Initialize the results list 🎯
    results = []
    
    # Iterate through each item in the input list
    for item in items:
        # Process the current item ✨
        processed = item.upper()
        
        # Add the processed item to the results list
        results.append(processed)
    
    # Return the final results 🚀
    return results
""")
    
    result = detector.analyze_file(code_file)
    
    print(f"\nFile: {code_file}")
    print(f"Rule Confidence:     {result['ensemble']['rule_confidence']:.2f}")
    print(f"ML Score:            {result['ensemble']['ml_score']:.2f}")
    print(f"ML Confidence:       {result['ensemble']['ml_confidence']:.2f}")
    print(f"Ensemble Confidence: {result['ensemble']['confidence']:.2f}")
    print(f"Classification:      {result['ensemble']['classification']}")
    
    print(f"\nEnsemble Weights:")
    print(f"  ML:    {result['ensemble']['weights']['ml']:.1%}")
    print(f"  Rules: {result['ensemble']['weights']['rules']:.1%}")
    
    if result['ensemble']['requires_review']:
        print("\n⚠️  DISAGREEMENT DETECTED")
        print(f"   Disagreement: {result['ensemble']['disagreement']:.2f}")
        print("   Manual review recommended")
    
    # Cleanup
    Path(code_file).unlink()


def demo_comparison():
    """Demo: Compare rule-based vs ML-enhanced."""
    print("\n" + "=" * 60)
    print("Demo 3: Rule-Based vs ML Comparison")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Obvious AI (Emojis + Perfect comments)',
            'code': '''
def calculate_total(numbers: list) -> int:
    """Calculate the total sum of numbers."""
    # Initialize the sum variable 🎯
    total = 0
    # Iterate through all numbers ✨
    for num in numbers:
        total += num
    return total  # Return the result 🚀
''',
        },
        {
            'name': 'Obvious Human (Minimal comments)',
            'code': '''
def calc(nums):
    res = 0
    for n in nums:
        res += n
    return res
''',
        },
        {
            'name': 'Edge Case (Mixed)',
            'code': '''
def process(data):
    """Process the data and return results."""
    out = []
    for item in data:
        if item > 0:
            out.append(item * 2)
    return out
''',
        },
    ]
    
    # Rule-based detector
    rule_detector = EnhancedDetector(use_ml=False)
    
    # ML detector (if available)
    model_path = "models/codebase_csi_best.pt"
    ml_detector = None
    if Path(model_path).exists():
        ml_detector = EnhancedDetector(ml_model_path=model_path, use_ml=True)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}: {test['name']}")
        print(f"{'='*60}")
        
        # Save code to temp file
        temp_file = f"temp_test_{i}.py"
        with open(temp_file, 'w') as f:
            f.write(test['code'])
        
        # Rule-based result
        rule_result = rule_detector.analyze_file(temp_file)
        print(f"\n[Rule-Based]")
        print(f"  Confidence: {rule_result['ensemble']['confidence']:.2f}")
        print(f"  Class: {rule_result['ensemble']['classification']}")
        
        # ML result
        if ml_detector:
            ml_result = ml_detector.analyze_file(temp_file)
            print(f"\n[ML-Enhanced]")
            print(f"  Confidence: {ml_result['ensemble']['confidence']:.2f}")
            print(f"  Class: {ml_result['ensemble']['classification']}")
            print(f"  ML Score: {ml_result['ensemble']['ml_score']:.2f}")
        
        # Cleanup
        Path(temp_file).unlink()


if __name__ == '__main__':
    print("=" * 60)
    print("Codebase CSI - ML Integration Examples")
    print("=" * 60)
    
    # Run demos
    demo_basic()
    demo_ml()
    demo_comparison()
    
    print("\n" + "=" * 60)
    print("✅ All demos complete!")
    print("=" * 60)
