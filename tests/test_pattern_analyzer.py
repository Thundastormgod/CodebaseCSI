"""
Tests for Pattern Analyzer
Tests detection of AI code patterns including generic naming, verbose comments,
boolean traps, magic numbers, and god functions.
"""

import pytest
from pathlib import Path
from codebase_csi.analyzers.pattern_analyzer import PatternAnalyzer, PatternMatch


class TestPatternAnalyzer:
    """Test suite for Pattern Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PatternAnalyzer()
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        file_path = tmp_path / "test_code.py"
        return file_path
    
    # === Generic Naming Tests ===
    
    def test_detect_generic_names_temp_variables(self, analyzer, temp_file):
        """Test detection of generic 'temp' variables."""
        code = """
def process():
    temp = get_data()
    tmp = calculate(temp)
    temporary = transform(tmp)
    return temporary
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        generic_patterns = [p for p in patterns if p.pattern_type == 'generic_naming']
        assert len(generic_patterns) > 0
        assert any('temp' in p.context.lower() for p in generic_patterns)
    
    def test_detect_generic_names_data_variables(self, analyzer, temp_file):
        """Test detection of generic 'data' variables."""
        code = """
def analyze(data, info, result, obj):
    processed_data = transform(data)
    result = calculate(info)
    output = merge(processed_data, obj)
    return result
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        generic_patterns = [p for p in patterns if p.pattern_type == 'generic_naming']
        assert len(generic_patterns) >= 3  # data, info, result, obj
    
    def test_no_false_positive_descriptive_names(self, analyzer, temp_file):
        """Test that descriptive names don't trigger false positives."""
        code = """
def calculate_user_balance(user_account, transaction_history):
    current_balance = user_account.balance
    total_debits = sum(t.amount for t in transaction_history if t.is_debit)
    total_credits = sum(t.amount for t in transaction_history if t.is_credit)
    new_balance = current_balance - total_debits + total_credits
    return new_balance
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence since names are descriptive
        assert result['confidence'] < 0.3
    
    def test_detect_numbered_variables(self, analyzer, temp_file):
        """Test detection of numbered variables (func1, func2, var1, var2)."""
        code = """
def process():
    var1 = get_input()
    var2 = transform(var1)
    result1 = calculate(var2)
    result2 = finalize(result1)
    return result2
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        generic_patterns = [p for p in patterns if p.pattern_type == 'generic_naming']
        assert any('var1' in p.context or 'var2' in p.context for p in generic_patterns)
    
    # === Verbose Comments Tests ===
    
    def test_detect_verbose_ai_phrases(self, analyzer, temp_file):
        """Test detection of verbose AI-style comment phrases."""
        code = """
def calculate(x, y):
    # Note that we need to validate the inputs first
    # Let's break this down step by step:
    # 1. First, we check if x is positive
    if x > 0:
        # Simply put, we multiply x and y
        result = x * y
    return result
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        patterns = result.get('patterns', [])
        comment_patterns = [p for p in patterns if p.pattern_type == 'verbose_comments']
        assert len(comment_patterns) > 0
        assert any('note that' in p.context.lower() for p in comment_patterns)
    
    def test_detect_high_comment_to_code_ratio(self, analyzer, temp_file):
        """Test detection of high comment-to-code ratio."""
        code = """
# This function calculates the sum
# It takes two numbers as parameters
# First number is x
# Second number is y
# We add them together
# Then we return the result
def add(x, y):
    # Add the numbers
    result = x + y
    # Return the sum
    return result
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should detect high comment-to-code ratio (10 comment lines vs 3 code lines)
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        comment_patterns = [p for p in patterns if p.pattern_type == 'verbose_comments']
        assert len(comment_patterns) > 0
    
    def test_acceptable_comment_ratio(self, analyzer, temp_file):
        """Test that reasonable comments don't trigger false positives."""
        code = """
def calculate_compound_interest(principal, rate, years):
    '''Calculate compound interest using the formula A = P(1 + r)^t'''
    # Convert percentage to decimal
    decimal_rate = rate / 100
    # Apply compound interest formula
    final_amount = principal * ((1 + decimal_rate) ** years)
    return final_amount
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - comments are reasonable
        assert result['confidence'] < 0.4
    
    # === Boolean Trap Tests ===
    
    def test_detect_boolean_trap(self, analyzer, temp_file):
        """Test detection of multiple consecutive boolean parameters."""
        code = """
def create_user(name, active, verified, premium, admin, enabled):
    user = User(name)
    user.active = active
    user.verified = verified
    user.premium = premium
    user.admin = admin
    user.enabled = enabled
    return user

# Called like: create_user("John", True, False, True, False, True)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        patterns = result.get('patterns', [])
        boolean_patterns = [p for p in patterns if p.pattern_type == 'boolean_trap']
        assert len(boolean_patterns) > 0
    
    def test_acceptable_boolean_usage(self, analyzer, temp_file):
        """Test that reasonable boolean usage doesn't trigger false positives."""
        code = """
def is_valid_email(email):
    has_at = '@' in email
    has_dot = '.' in email
    return has_at and has_dot

def set_active(user, is_active):
    user.active = is_active
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - boolean usage is clear
        assert result['confidence'] < 0.3
    
    # === Magic Numbers Tests ===
    
    def test_detect_magic_numbers(self, analyzer, temp_file):
        """Test detection of magic numbers without explanation."""
        code = """
def calculate():
    x = 42
    y = x * 3.14159
    if y > 273.15:
        z = y / 86400
    return z
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        magic_patterns = [p for p in patterns if p.pattern_type == 'magic_numbers']
        assert len(magic_patterns) > 0
    
    def test_acceptable_numbers_no_false_positive(self, analyzer, temp_file):
        """Test that common constants don't trigger false positives."""
        code = """
def process(items):
    count = 0
    total = 1
    factor = 2
    
    for item in items:
        if count < 10:
            total *= factor
            count += 1
    
    return total / 100
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - these are common constants
        assert result['confidence'] < 0.3
    
    def test_named_constants_acceptable(self, analyzer, temp_file):
        """Test that named constants are acceptable."""
        code = """
# Named constants are good practice
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
PI = 3.14159
ABSOLUTE_ZERO = -273.15

def calculate(value):
    if value > ABSOLUTE_ZERO:
        return value * PI
    return 0
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have lower confidence - constants are named
        assert result['confidence'] < 0.4
    
    # === God Function Tests ===
    
    def test_detect_god_function_by_length(self, analyzer, temp_file):
        """Test detection of god functions (>50 lines)."""
        # Create a function with 60 lines
        lines = ["def process():\n"]
        lines.extend([f"    x{i} = calculate_{i}()\n" for i in range(58)])
        lines.append("    return x57\n")
        code = "".join(lines)
        
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        god_patterns = [p for p in patterns if p.pattern_type == 'god_function']
        assert len(god_patterns) > 0
    
    def test_detect_god_function_by_parameters(self, analyzer, temp_file):
        """Test detection of god functions (>5 parameters)."""
        code = """
def create_record(id, name, email, phone, address, city, state, zip_code, country):
    record = {
        'id': id,
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip': zip_code,
        'country': country
    }
    return record
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        god_patterns = [p for p in patterns if p.pattern_type == 'god_function']
        assert len(god_patterns) > 0
    
    def test_acceptable_function_size(self, analyzer, temp_file):
        """Test that reasonable functions don't trigger false positives."""
        code = """
def calculate_total(items, tax_rate=0.08):
    subtotal = sum(item.price for item in items)
    tax = subtotal * tax_rate
    total = subtotal + tax
    return total

def validate_email(email):
    if '@' not in email:
        return False
    if '.' not in email.split('@')[1]:
        return False
    return True
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - functions are reasonable
        assert result['confidence'] < 0.3
    
    # === Edge Cases & Integration Tests ===
    
    def test_empty_file(self, analyzer, temp_file):
        """Test analyzer handles empty files gracefully."""
        code = ""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] == 0.0
        assert 'patterns' in result
        assert len(result['patterns']) == 0
    
    def test_only_comments(self, analyzer, temp_file):
        """Test analyzer handles files with only comments."""
        code = """
# This is a comment
# Another comment
# Yet another comment
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] >= 0.0
        assert 'patterns' in result
    
    def test_multiple_patterns_combined(self, analyzer, temp_file):
        """Test detection of multiple patterns in same file."""
        code = """
# Note that this function is very important
# Let's break down what it does step by step
def process_data(temp, data, result, active, enabled, premium):
    # Simply put, we transform the data
    x = 42  # Magic number
    y = temp * 3.14159  # Another magic number
    
    if active and enabled and premium:
        result = x + y
    
    return result
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should detect multiple patterns: generic names, verbose comments,
        # boolean trap, magic numbers
        assert result['confidence'] > 0.7
        patterns = result.get('patterns', [])
        pattern_types = {p.pattern_type for p in patterns}
        assert 'generic_naming' in pattern_types
        assert 'verbose_comments' in pattern_types
        assert 'magic_numbers' in pattern_types
    
    def test_javascript_support(self, analyzer, temp_file):
        """Test analyzer works with JavaScript code."""
        code = """
// Note that this is an important function
// Let's break this down step by step
function processData(temp, data, result) {
    // Simply put, we multiply the values
    let x = 42;
    let y = temp * 3.14159;
    return x + y;
}
"""
        result = analyzer.analyze(temp_file, code, "javascript")
        
        assert result['confidence'] > 0.5
        patterns = result.get('patterns', [])
        assert len(patterns) > 0
    
    def test_confidence_scoring_proportional(self, analyzer, temp_file):
        """Test that confidence score is proportional to pattern density."""
        # Code with few patterns
        code_low = """
def calculate_user_balance(account):
    return account.balance + account.credits - account.debits
"""
        
        # Code with many patterns
        code_high = """
# Note that we need to process the data carefully
# Let's break this down step by step
def process(temp, data, result, obj, active, enabled, premium):
    # Simply put, we calculate the result
    x = 42
    y = temp * 3.14159
    z = data / 86400
    return x + y + z
"""
        
        result_low = analyzer.analyze(temp_file, code_low, "python")
        result_high = analyzer.analyze(temp_file, code_high, "python")
        
        assert result_high['confidence'] > result_low['confidence']
        assert result_high['confidence'] - result_low['confidence'] > 0.3
    
    def test_summary_statistics(self, analyzer, temp_file):
        """Test that summary statistics are generated correctly."""
        code = """
def process(temp, data, result):
    # Note that this is important
    x = 42
    return x + temp
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert 'summary' in result
        summary = result['summary']
        assert 'total_patterns' in summary
        assert 'confidence' in summary
        assert 'pattern_distribution' in summary
        assert summary['total_patterns'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
