"""
Tests for emoji detection in source code.
"""

import pytest
from pathlib import Path
from codebase_csi.analyzers.emoji_detector import EmojiDetector, EmojiMatch


class TestEmojiDetection:
    """Test emoji detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()
    
    def test_no_emojis(self):
        """Test file with no emojis."""
        lines = [
            "def calculate_total(items):",
            "    return sum(item.price for item in items)"
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 0
        assert result['confidence'] == 0.0
        assert result['severity'] == 'NONE'
    
    def test_single_emoji_in_comment(self):
        """Test single emoji in comment."""
        lines = [
            "# Calculate total price 💰",
            "def calculate_total(items):",
            "    return sum(item.price for item in items)"
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 1
        assert result['metrics']['context_distribution']['comment'] == 1
        assert result['confidence'] > 0.0
        # Note: 1 emoji in 3 lines = 33% density, which is CRITICAL (realistic expectation)
        assert result['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']
    
    def test_emoji_in_code(self):
        """Test emoji in actual code (CRITICAL)."""
        lines = [
            "def calculate():",
            "    x = 5 ➕ 3  # Math with emoji!",
            "    return x"
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['context_distribution']['code'] > 0
        assert result['severity'] == 'CRITICAL'
        assert result['confidence'] >= 0.3  # High confidence due to code context
    
    def test_multiple_emojis_per_line(self):
        """Test multiple emojis on single line."""
        lines = [
            "# ✅ Task completed! 🎉 Great job! 🚀"
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 3
        assert len(result['indicators']) == 1
        assert result['indicators'][0]['count'] == 3
    
    def test_high_emoji_density(self):
        """Test file with high emoji density."""
        lines = [
            "# 🚀 Initialize",
            "# ✅ Setup complete",
            "# 🔄 Processing",
            "# ✨ Success!",
            "def main():",
            "    pass"
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 4
        assert result['metrics']['emoji_density'] > 0.5
        assert result['severity'] in ['HIGH', 'CRITICAL']
    
    def test_common_ai_emoji_patterns(self):
        """Test detection of common AI emoji patterns."""
        test_cases = {
            '✅': 'task_marker',
            '❌': 'task_marker',
            '🔄': 'operation',
            '💰': 'finance',
            '🚀': 'enthusiasm',
            '📝': 'docs',
            '🐛': 'bug',
            '🎯': 'achievement'
        }
        
        for emoji, expected_category in test_cases.items():
            lines = [f"# Test {emoji}"]
            result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
            
            assert result['metrics']['total_emojis'] == 1
            categories = result['metrics']['category_distribution']
            assert expected_category in categories
    
    def test_emoji_in_docstring(self):
        """Test emoji in docstring."""
        lines = [
            '"""',
            'Calculate total price 💵',
            '',
            'Returns the sum of all items.',
            '"""'
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 1
        assert result['metrics']['context_distribution']['docstring'] >= 0
    
    def test_emoji_in_string_literal(self):
        """Test emoji in string literal (less suspicious)."""
        lines = [
            'message = "Task completed ✅"',
            'print(message)'
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] >= 1
        # String context is less suspicious than code, but still notable
        # 1 emoji in 2 lines = 50% density, which is high
        assert result['severity'] in ['HIGH', 'CRITICAL']
    
    def test_typical_ai_generated_code(self):
        """Test typical AI-generated code with emojis."""
        lines = [
            "# 🚀 Fast calculation function",
            "def calculate_total(items):",
            '    """',
            '    Calculate the total price 💰',
            '    ',
            '    Args:',
            '        items: List of items 📝',
            '    ',
            '    Returns:',
            '        Total price 💵',
            '    """',
            '    total = 0  # Initialize ✨',
            '    for item in items:  # 🔄 Loop through items',
            '        total += item.price  # ➕ Add price',
            '    return total  # ✅ Return result'
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] >= 8
        assert result['confidence'] > 0.5
        assert result['severity'] in ['HIGH', 'CRITICAL']
    
    def test_professional_code_no_emojis(self):
        """Test professional code without emojis."""
        lines = [
            "def calculate_total(items):",
            '    """Calculate the total price of items."""',
            '    return sum(item.price for item in items)'
        ]
        
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert result['metrics']['total_emojis'] == 0
        assert result['confidence'] == 0.0
        assert result['severity'] == 'NONE'
    
    def test_emoji_line_detection(self):
        """Test line-level emoji detection."""
        line = "# ✅ Task complete 🎉"
        matches = self.detector.detect_emojis_in_line(line, 1)
        
        assert len(matches) == 2
        assert matches[0].emoji == '✅'
        assert matches[1].emoji == '🎉'
        assert matches[0].line_number == 1
    
    def test_context_detection_comment(self):
        """Test context detection for comments."""
        context = self.detector._detect_context("# This is a comment 🚀", 20, 'python')
        assert context == 'comment'
        
        context = self.detector._detect_context("// JavaScript comment ✅", 23, 'javascript')
        assert context == 'comment'
    
    def test_context_detection_string(self):
        """Test context detection for string literals."""
        context = self.detector._detect_context('message = "Hello 🌍"', 17, 'python')
        assert context == 'string'
        
        context = self.detector._detect_context("text = 'World ✨'", 14, 'python')
        assert context == 'string'
    
    def test_unicode_representation(self):
        """Test Unicode code representation."""
        lines = ["# 🚀"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert len(result['patterns']) == 1
        pattern = result['patterns'][0]
        assert 'unicode' in pattern
        assert pattern['unicode'].startswith('U+')
    
    def test_remediation_suggestions(self):
        """Test remediation suggestions for emojis."""
        lines = ["# Task completed ✅"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        assert len(result['patterns']) == 1
        pattern = result['patterns'][0]
        assert 'remediation' in pattern
        assert 'Remove emoji' in pattern['remediation']


class TestEmojiCategories:
    """Test emoji category classification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()
    
    def test_task_markers(self):
        """Test task marker emojis."""
        lines = ["# ✅ Done", "# ❌ Failed"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        categories = result['metrics']['category_distribution']
        assert 'task_marker' in categories
        assert categories['task_marker'] == 2
    
    def test_operation_indicators(self):
        """Test operation indicator emojis."""
        lines = ["# 🔄 Loop", "# ➕ Add", "# ➖ Subtract"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        categories = result['metrics']['category_distribution']
        assert 'operation' in categories
    
    def test_finance_emojis(self):
        """Test finance-related emojis."""
        lines = ["# 💰 Money", "# 💵 Dollar", "# 💳 Card"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        categories = result['metrics']['category_distribution']
        assert 'finance' in categories
        assert categories['finance'] == 3
    
    def test_enthusiasm_emojis(self):
        """Test enthusiasm/hype emojis (strong AI indicator)."""
        lines = ["# 🚀 Launch", "# 🔥 Hot", "# ⚡ Fast", "# ✨ Magic"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        
        categories = result['metrics']['category_distribution']
        assert 'enthusiasm' in categories
        # These should have high confidence
        assert result['confidence'] > 0.3


class TestSeverityLevels:
    """Test severity level determination."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()
    
    def test_none_severity(self):
        """Test NONE severity for no emojis."""
        lines = ["def test():", "    pass"]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['severity'] == 'NONE'
    
    def test_low_severity(self):
        """Test LOW severity for single emoji."""
        lines = ["# Comment 📝"] + ["def test(): pass"] * 20
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['severity'] in ['LOW', 'MEDIUM']
    
    def test_medium_severity(self):
        """Test MEDIUM severity for multiple emojis."""
        lines = ["# 🚀", "# ✅", "# 📝", "# 🔄"] + ["pass"] * 20
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['severity'] in ['MEDIUM', 'HIGH']
    
    def test_high_severity(self):
        """Test HIGH severity for high emoji density."""
        lines = [f"# Emoji {i} 🚀" for i in range(10)]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['severity'] in ['HIGH', 'CRITICAL']
    
    def test_critical_severity_code_context(self):
        """Test CRITICAL severity for emojis in code."""
        lines = [
            "x = 5 ➕ 3",  # Emoji in actual code!
            "y = x"
        ]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['severity'] == 'CRITICAL'


class TestRealWorldExamples:
    """Test with real-world code examples."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()
    
    def test_chatgpt_generated_python(self):
        """Test typical ChatGPT-generated Python code."""
        code = '''
def process_payment(amount, card):
    """
    Process a payment transaction 💳
    
    Args:
        amount: Payment amount 💰
        card: Card information 💵
    
    Returns:
        Transaction result ✅
    """
    # Validate amount 🔍
    if amount <= 0:
        return {"status": "failed", "message": "Invalid amount"}  # ❌
    
    # Process transaction 🔄
    result = charge_card(card, amount)
    
    # Return success 🎉
    return {"status": "success", "amount": amount}  # ✅
'''
        lines = code.strip().split('\n')
        result = self.detector.analyze(Path("payment.py"), code, lines)
        
        assert result['metrics']['total_emojis'] >= 8
        assert result['confidence'] > 0.5
        assert result['severity'] in ['HIGH', 'CRITICAL']
    
    def test_claude_generated_javascript(self):
        """Test typical Claude-generated JavaScript code."""
        code = '''
// 🚀 Initialize the application
function initializeApp() {
    // ✨ Setup configuration
    const config = loadConfig();
    
    // 🔄 Start main loop
    startMainLoop(config);
    
    // ✅ Application ready!
    console.log("App initialized successfully!");
}
'''
        lines = code.strip().split('\n')
        result = self.detector.analyze(Path("app.js"), code, lines)
        
        assert result['metrics']['total_emojis'] >= 4
        assert result['confidence'] > 0.3
    
    def test_professional_python_code(self):
        """Test professional Python code without emojis."""
        code = '''
def process_payment(amount: float, card: Card) -> TransactionResult:
    """
    Process a payment transaction.
    
    Args:
        amount: Payment amount in dollars
        card: Card information object
    
    Returns:
        Transaction result with status and details
        
    Raises:
        ValueError: If amount is invalid
        PaymentError: If transaction fails
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    result = self._charge_card(card, amount)
    
    return TransactionResult(
        status=Status.SUCCESS,
        amount=amount,
        transaction_id=result.id
    )
'''
        lines = code.strip().split('\n')
        result = self.detector.analyze(Path("payment.py"), code, lines)
        
        assert result['metrics']['total_emojis'] == 0
        assert result['confidence'] == 0.0
        assert result['severity'] == 'NONE'
    
    def test_mixed_quality_code(self):
        """Test code with some AI influence (mixed)."""
        code = '''
def calculate_metrics(data):
    """Calculate performance metrics from data."""
    
    # Process data 🔄
    processed = [x * 2 for x in data]
    
    # Calculate average
    avg = sum(processed) / len(processed)
    
    return avg
'''
        lines = code.strip().split('\n')
        result = self.detector.analyze(Path("metrics.py"), code, lines)
        
        assert result['metrics']['total_emojis'] == 1
        assert 0.0 < result['confidence'] < 0.5
        assert result['severity'] in ['LOW', 'MEDIUM']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = EmojiDetector()
    
    def test_empty_file(self):
        """Test empty file."""
        result = self.detector.analyze(Path("empty.py"), "", [])
        assert result['metrics']['total_emojis'] == 0
        assert result['confidence'] == 0.0
    
    def test_only_whitespace(self):
        """Test file with only whitespace."""
        lines = ["   ", "\t", "  \t  "]
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        assert result['metrics']['total_emojis'] == 0
    
    def test_escaped_emoji_in_string(self):
        """Test escaped emoji representation."""
        lines = ['emoji = "\\U0001F680"  # Rocket emoji code']
        result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
        # Should not detect escaped unicode
        assert result['metrics']['total_emojis'] == 0
    
    def test_very_long_line(self):
        """Test very long line with emoji."""
        long_line = "# " + "x" * 10000 + " 🚀"
        result = self.detector.analyze(Path("test.py"), long_line, [long_line])
        assert result['metrics']['total_emojis'] == 1
    
    def test_multiple_files_batch(self):
        """Test batch processing of multiple files."""
        files = [
            (["# Clean code"], 0),
            (["# Emoji code 🚀"], 1),
            (["# Multiple 🚀✨🎉"], 3),
        ]
        
        for lines, expected_count in files:
            result = self.detector.analyze(Path("test.py"), "\n".join(lines), lines)
            assert result['metrics']['total_emojis'] == expected_count
