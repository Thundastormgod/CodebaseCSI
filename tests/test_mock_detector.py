"""
Tests for MockCodeDetector analyzer.

Tests detection of placeholder/stub implementations commonly
produced by AI assistants.
"""

import pytest
from codebase_csi.analyzers.mock_detector import MockCodeDetector, MockPattern


class TestMockCodeDetector:
    """Test suite for MockCodeDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return MockCodeDetector()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PLACEHOLDER STRING TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_mock_return_value(self, detector):
        """Test detection of mock return values."""
        code = '''
def get_user():
    return "mock_user"
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('placeholder' in p.pattern_type for p in result['patterns'])
    
    def test_detect_fake_email(self, detector):
        """Test detection of fake email addresses."""
        code = '''
def get_email():
    return "test@example.com"
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('mock_email' in p.pattern_type for p in result['patterns'])
    
    def test_detect_todo_return(self, detector):
        """Test detection of TODO return values."""
        code = '''
def process():
    return "TODO"
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('todo' in p.pattern_type.lower() for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STUB FUNCTION TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_always_true_function(self, detector):
        """Test detection of functions that always return True."""
        code = '''
def validate_user(user_id):
    return True
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('always_true' in p.pattern_type for p in result['patterns'])
    
    def test_detect_pass_only_function(self, detector):
        """Test detection of functions with only pass."""
        code = '''
def save_data(data):
    pass
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('pass_only' in p.pattern_type for p in result['patterns'])
    
    def test_detect_ellipsis_function(self, detector):
        """Test detection of functions with only ellipsis."""
        code = '''
def process_payment(amount):
    ...
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('ellipsis' in p.pattern_type for p in result['patterns'])
    
    def test_detect_not_implemented(self, detector):
        """Test detection of NotImplementedError stubs."""
        code = '''
def complex_logic():
    raise NotImplementedError
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('not_implemented' in p.pattern_type for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ALWAYS-SUCCESS PATTERN TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_success_dict(self, detector):
        """Test detection of hardcoded success responses."""
        code = '''
def api_call():
    return {"success": True, "message": "ok"}
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('success' in p.pattern_type for p in result['patterns'])
    
    def test_detect_always_valid(self, detector):
        """Test detection of always-valid responses."""
        code = '''
def check_input(data):
    return {"valid": True}
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('valid' in p.pattern_type for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PRINT-ONLY IMPLEMENTATION TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_simulating_print(self, detector):
        """Test detection of 'would do X' print statements."""
        code = '''
def delete_file(path):
    print(f"Would delete: {path}")
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('simulating' in p.pattern_type or 'print' in p.pattern_type 
                   for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FAKE DATA PATTERN TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_hardcoded_user(self, detector):
        """Test detection of hardcoded user data."""
        code = '''
def get_current_user():
    return {"user": "John", "id": 1}
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('hardcoded' in p.pattern_type or 'fake' in p.pattern_type 
                   for p in result['patterns'])
    
    def test_detect_empty_list_return(self, detector):
        """Test detection of empty list returns."""
        code = '''
def get_items():
    return []
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('empty_list' in p.pattern_type for p in result['patterns'])
    
    def test_detect_empty_dict_return(self, detector):
        """Test detection of empty dict returns."""
        code = '''
def get_config():
    return {}
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('empty_dict' in p.pattern_type for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TODO MARKER TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_todo_implement(self, detector):
        """Test detection of TODO implement markers."""
        code = '''
def calculate_tax(amount):
    # TODO: implement actual tax calculation
    return amount * 0.1
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('todo' in p.pattern_type.lower() for p in result['patterns'])
    
    def test_detect_fixme_marker(self, detector):
        """Test detection of FIXME markers."""
        code = '''
def validate(data):
    # FIXME: this doesn't actually validate anything
    return True
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('fixme' in p.pattern_type.lower() for p in result['patterns'])
    
    def test_detect_placeholder_comment(self, detector):
        """Test detection of placeholder comments."""
        code = '''
def process_order(order):
    # placeholder implementation
    return order
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('placeholder' in p.pattern_type for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MOCK FUNCTION NAME TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_detect_mock_function_name(self, detector):
        """Test detection of function names indicating mock purpose."""
        code = '''
def mock_api_call():
    return {"data": "fake"}

def fake_database_query():
    return []
'''
        result = detector.analyze(code)
        assert result['confidence'] > 0
        assert any('mock_function' in p.pattern_type for p in result['patterns'])
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLEAN CODE TESTS (NO FALSE POSITIVES)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_no_false_positive_real_implementation(self, detector):
        """Test that real implementations don't trigger false positives."""
        code = '''
def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

def validate_email(email):
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
'''
        result = detector.analyze(code)
        # Should have very low or no confidence for real implementations
        assert result['confidence'] < 0.3
    
    def test_empty_content(self, detector):
        """Test handling of empty content."""
        result = detector.analyze("")
        assert result['confidence'] == 0.0
        assert result['patterns'] == []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_summary_structure(self, detector):
        """Test that summary has correct structure."""
        code = '''
def mock_function():
    return "placeholder"
'''
        result = detector.analyze(code)
        assert 'summary' in result
        assert 'total' in result['summary']
        assert 'by_severity' in result['summary']
        assert 'by_category' in result['summary']
    
    def test_severity_classification(self, detector):
        """Test that severities are correctly classified."""
        code = '''
def authenticate(user, password):
    return True

def encrypt(data):
    return data
'''
        result = detector.analyze(code)
        # Should have CRITICAL severity patterns
        critical_count = result['summary']['by_severity'].get('CRITICAL', 0)
        assert critical_count > 0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTEGRATION TESTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def test_multiple_patterns_in_file(self, detector):
        """Test detection of multiple mock patterns in one file."""
        code = '''
# TODO: implement this module properly

def get_user(user_id):
    return {"user": "John", "valid": True}

def authenticate(username, password):
    return True

def save_to_database(data):
    print(f"Would save: {data}")
    pass

def encrypt_password(password):
    return password  # FIXME: actually encrypt this

def mock_api_response():
    return {"success": True, "data": "sample"}
'''
        result = detector.analyze(code)
        
        # Should detect multiple patterns
        assert result['summary']['total'] >= 5
        assert result['confidence'] > 0.5
        
        # Should have various severities
        assert sum(result['summary']['by_severity'].values()) >= 5


class TestMockPattern:
    """Test MockPattern dataclass."""
    
    def test_pattern_creation(self):
        """Test creating a MockPattern instance."""
        pattern = MockPattern(
            pattern_type="stub_always_true",
            line_number=10,
            code_snippet="return True",
            confidence=0.90,
            severity="CRITICAL",
            description="Always returns True",
            suggestion="Implement actual logic"
        )
        
        assert pattern.pattern_type == "stub_always_true"
        assert pattern.line_number == 10
        assert pattern.confidence == 0.90
        assert pattern.severity == "CRITICAL"
        assert pattern.category == "mock_code"
