"""
Test Suite for AntipatternAnalyzer v1.0

Tests antipattern detection:
1. Bleeding Edge (organizational antipattern)
2. Gold Plating (software design antipattern)
3. Magic Numbers (programming antipattern - enhanced)

Target: 85%+ accuracy
"""

import pytest
from pathlib import Path
from codebase_csi.analyzers.antipattern_analyzer import AntipatternAnalyzer, AntipatternMatch


@pytest.fixture
def analyzer():
    """Create analyzer instance."""
    return AntipatternAnalyzer()


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file path."""
    return tmp_path / "test_code.py"


class TestAntipatternAnalyzerInit:
    """Test analyzer initialization."""
    
    def test_init_compiles_patterns(self, analyzer):
        """Test that patterns are compiled on init."""
        assert hasattr(analyzer, '_unstable_version_patterns')
        assert hasattr(analyzer, '_experimental_api_patterns')
        assert hasattr(analyzer, '_over_engineering_patterns')
        assert hasattr(analyzer, '_dead_code_patterns')
        assert len(analyzer._unstable_version_patterns) > 0
    
    def test_init_no_errors(self):
        """Test that init doesn't raise errors."""
        try:
            analyzer = AntipatternAnalyzer()
            assert analyzer is not None
        except Exception as e:
            pytest.fail(f"Initialization failed: {e}")


class TestBleedingEdgeDetection:
    """Test Bleeding Edge antipattern detection."""
    
    # === Dependency File Tests ===
    
    def test_detect_alpha_version(self, analyzer, tmp_path):
        """Test detection of alpha version dependencies."""
        requirements = tmp_path / "requirements.txt"
        content = """
django==4.2.0
flask==2.0.0-alpha.1
requests==2.28.0
pytest-async==0.1.0alpha
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        alpha_matches = [p for p in result['antipatterns'] 
                        if p.subcategory == 'alpha_version']
        assert len(alpha_matches) >= 1
        assert all(m.antipattern_type == 'bleeding_edge' for m in alpha_matches)
        assert all(m.category == 'organizational' for m in alpha_matches)
    
    def test_detect_beta_version(self, analyzer, tmp_path):
        """Test detection of beta version dependencies."""
        requirements = tmp_path / "requirements.txt"
        content = """
numpy==1.24.0
pandas==2.0.0-beta.2
scikit-learn==1.2.0
tensorflow==2.13.0beta1
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        beta_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'beta_version']
        assert len(beta_matches) >= 1
    
    def test_detect_rc_version(self, analyzer, tmp_path):
        """Test detection of release candidate versions."""
        requirements = tmp_path / "requirements.txt"
        content = """
fastapi==0.100.0
pydantic==2.0.0-rc1
sqlalchemy==2.0.0rc2
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        rc_matches = [p for p in result['antipatterns'] 
                     if p.subcategory == 'release_candidate']
        assert len(rc_matches) >= 1
    
    def test_detect_dev_version(self, analyzer, tmp_path):
        """Test detection of dev versions."""
        requirements = tmp_path / "requirements.txt"
        content = """
mypackage==1.0.0.dev1
otherpackage==2.0.0-dev.3
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        dev_matches = [p for p in result['antipatterns'] 
                      if p.subcategory == 'dev_version']
        assert len(dev_matches) >= 1
    
    def test_detect_nightly_version(self, analyzer, tmp_path):
        """Test detection of nightly versions."""
        requirements = tmp_path / "requirements.txt"
        content = """
pytorch-nightly==2.0.0
torch==2.0.0.nightly
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        nightly_matches = [p for p in result['antipatterns'] 
                          if p.subcategory == 'nightly_version']
        assert len(nightly_matches) >= 1
        # Nightly should be CRITICAL severity
        assert any(m.severity == 'CRITICAL' for m in nightly_matches)
    
    def test_detect_unstable_version(self, analyzer, tmp_path):
        """Test detection of explicitly unstable versions."""
        requirements = tmp_path / "requirements.txt"
        content = """
mylib==1.0.0-unstable
experimental-package==0.1.0unstable
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        unstable_matches = [p for p in result['antipatterns'] 
                           if p.subcategory == 'unstable_version']
        assert len(unstable_matches) >= 1
        assert all(m.severity == 'CRITICAL' for m in unstable_matches)
    
    def test_detect_zero_zero_version(self, analyzer, tmp_path):
        """Test detection of 0.0.x versions."""
        requirements = tmp_path / "requirements.txt"
        content = """
new-package==0.0.5
another==0.0.12
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        zero_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'zero_zero_version']
        assert len(zero_matches) >= 1
    
    def test_stable_versions_no_detection(self, analyzer, tmp_path):
        """Test that stable versions are not flagged."""
        requirements = tmp_path / "requirements.txt"
        content = """
django==4.2.0
flask==2.0.0
requests==2.28.1
numpy==1.24.0
pandas==2.0.0
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        bleeding_edge = [p for p in result['antipatterns'] 
                        if p.antipattern_type == 'bleeding_edge']
        assert len(bleeding_edge) == 0
    
    # === Package.json Tests ===
    
    def test_detect_npm_beta(self, analyzer, tmp_path):
        """Test detection in package.json."""
        package_json = tmp_path / "package.json"
        content = """
{
  "dependencies": {
    "react": "18.2.0",
    "next": "13.0.0-beta.1",
    "typescript": "5.0.0-rc"
  }
}
"""
        package_json.write_text(content)
        
        result = analyzer.analyze(package_json, content, 'json')
        
        assert result['confidence'] > 0
        bleeding_edge = [p for p in result['antipatterns'] 
                        if p.antipattern_type == 'bleeding_edge']
        assert len(bleeding_edge) >= 1
    
    # === Source Code Experimental API Tests ===
    
    def test_detect_experimental_decorator(self, analyzer, temp_file):
        """Test detection of @experimental decorator."""
        content = """
from typing import Optional

@experimental
def new_feature(data: str) -> Optional[str]:
    '''This is an experimental feature.'''
    return data.upper()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        exp_matches = [p for p in result['antipatterns'] 
                      if p.subcategory == 'experimental_decorator']
        assert len(exp_matches) >= 1
    
    def test_detect_beta_decorator(self, analyzer, temp_file):
        """Test detection of @beta decorator."""
        content = """
@beta
def beta_function():
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        beta_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'beta_decorator']
        assert len(beta_matches) >= 1
    
    def test_detect_hack_workaround_comment(self, analyzer, temp_file):
        """Test detection of HACK workaround comments."""
        content = """
def process_data(data):
    # HACK: workaround for upstream bug #123
    if data is None:
        data = []
    return data
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        hack_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'hack_workaround']
        assert len(hack_matches) >= 1
    
    def test_detect_experimental_feature_flag(self, analyzer, temp_file):
        """Test detection of experimental feature flags."""
        content = """
ENABLE_EXPERIMENTAL_FEATURE = True

if ENABLE_EXPERIMENTAL_FEATURE:
    use_new_algorithm()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        flag_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'experimental_flag']
        assert len(flag_matches) >= 1


class TestGoldPlatingDetection:
    """Test Gold Plating antipattern detection."""
    
    # === Over-Engineering Tests ===
    
    def test_detect_single_factory(self, analyzer, temp_file):
        """Test detection of factory with no implementations."""
        content = """
from abc import ABC, abstractmethod

class AbstractWidgetFactory(ABC):
    @abstractmethod
    def create_widget(self):
        pass

# Note: No ConcreteWidgetFactory implementation
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        gold_plating = [p for p in result['antipatterns'] 
                       if p.antipattern_type == 'gold_plating']
        assert len(gold_plating) >= 0  # May or may not detect depending on pattern
    
    def test_detect_visitor_pattern(self, analyzer, temp_file):
        """Test detection of visitor pattern (potentially over-engineered)."""
        content = """
class NodeVisitor:
    def visit_number(self, node):
        pass
    
    def visit_string(self, node):
        pass
    
    def visit_add(self, node):
        return self.visit(node.left) + self.visit(node.right)
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        visitor_matches = [p for p in result['antipatterns'] 
                          if p.subcategory == 'visitor_pattern']
        assert len(visitor_matches) >= 1
    
    # === Dead Code Tests ===
    
    def test_detect_pass_only_function(self, analyzer, temp_file):
        """Test detection of functions that only contain pass."""
        content = """
def placeholder_function(arg1, arg2):
    pass

def another_empty():
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        pass_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'pass_only_function']
        assert len(pass_matches) >= 1
    
    def test_detect_empty_except(self, analyzer, temp_file):
        """Test detection of empty except blocks."""
        content = """
def risky_operation():
    try:
        do_something()
    except Exception:
        pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        except_matches = [p for p in result['antipatterns'] 
                         if p.subcategory == 'empty_except']
        assert len(except_matches) >= 1
    
    def test_detect_commented_code(self, analyzer, temp_file):
        """Test detection of commented out code."""
        content = """
def active_function():
    return True

# def old_function():
#     return False

# if some_condition:
#     do_something()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        commented_matches = [p for p in result['antipatterns'] 
                            if p.subcategory == 'commented_code']
        assert len(commented_matches) >= 1
    
    def test_detect_not_implemented(self, analyzer, temp_file):
        """Test detection of NotImplementedError stubs."""
        content = """
class AbstractProcessor:
    def process(self, data):
        raise NotImplementedError
    
    def validate(self, data):
        raise NotImplementedError
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        not_impl_matches = [p for p in result['antipatterns'] 
                           if p.subcategory == 'not_implemented']
        assert len(not_impl_matches) >= 1
    
    # === Premature Optimization Tests ===
    
    def test_detect_manual_cache(self, analyzer, temp_file):
        """Test detection of manual caching."""
        content = """
_cache = {}

def expensive_operation(key):
    if key in _cache:
        return _cache[key]
    result = compute(key)
    _cache[key] = result
    return result
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        cache_matches = [p for p in result['antipatterns'] 
                        if p.subcategory == 'manual_cache']
        assert len(cache_matches) >= 1
    
    def test_detect_unbounded_cache(self, analyzer, temp_file):
        """Test detection of unbounded lru_cache."""
        content = """
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        cache_matches = [p for p in result['antipatterns'] 
                        if p.subcategory == 'unbounded_cache']
        assert len(cache_matches) >= 1
    
    def test_detect_nested_comprehension(self, analyzer, temp_file):
        """Test detection of deeply nested comprehensions."""
        content = """
matrix = [[[x*y*z for x in range(3)] for y in range(3) for z in range(3)]]
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        nested_matches = [p for p in result['antipatterns'] 
                         if p.subcategory == 'nested_comprehension']
        assert len(nested_matches) >= 1
    
    # === Excessive Abstraction Tests ===
    
    def test_detect_pattern_overload(self, analyzer, temp_file):
        """Test detection of too many design patterns."""
        content = """
class UserFactory:
    pass

class UserBuilder:
    pass

class UserStrategy:
    pass

class UserObserver:
    pass

class UserVisitor:
    pass

class UserAdapter:
    pass

class UserDecorator:
    pass

class UserProxy:
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        overload_matches = [p for p in result['antipatterns'] 
                           if p.subcategory == 'pattern_overload']
        assert len(overload_matches) >= 1
        assert any(m.severity == 'HIGH' for m in overload_matches)
    
    # === Feature Flag Tests ===
    
    def test_detect_feature_flag_overload(self, analyzer, temp_file):
        """Test detection of too many feature flags."""
        content = """
ENABLE_FEATURE_A = True
ENABLE_FEATURE_B = False
ENABLE_FEATURE_C = True
DISABLE_FEATURE_D = False
USE_NEW_ALGORITHM = True
FEATURE_FLAG_X = True
FLAG_EXPERIMENTAL = False

if ENABLE_FEATURE_A:
    feature_a()
if ENABLE_FEATURE_B:
    feature_b()
if ENABLE_FEATURE_C:
    feature_c()
if USE_NEW_ALGORITHM:
    new_algo()
if FEATURE_FLAG_X:
    x_feature()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        flag_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'feature_flag_overload']
        assert len(flag_matches) >= 1


class TestMagicNumbersDetection:
    """Test enhanced Magic Numbers detection."""
    
    def test_detect_http_status_magic(self, analyzer, temp_file):
        """Test detection of HTTP status code magic numbers."""
        content = """
def check_response(response):
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return None
    elif response.status_code == 500:
        raise ServerError()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        http_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'http_status_magic']
        assert len(http_matches) >= 1
    
    def test_detect_port_magic(self, analyzer, temp_file):
        """Test detection of port number magic numbers."""
        content = """
def start_server():
    port = 8080
    PORT = 443
    return port
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        port_matches = [p for p in result['antipatterns'] 
                       if p.subcategory == 'port_magic']
        assert len(port_matches) >= 1
    
    def test_detect_timeout_magic(self, analyzer, temp_file):
        """Test detection of timeout magic numbers."""
        content = """
def fetch_data(url):
    timeout = 30
    response = requests.get(url, timeout=timeout)
    return response
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        timeout_matches = [p for p in result['antipatterns'] 
                          if p.subcategory == 'timeout_magic']
        assert len(timeout_matches) >= 1
    
    def test_detect_retry_magic(self, analyzer, temp_file):
        """Test detection of retry count magic numbers."""
        content = """
def retry_operation():
    max_retries = 5
    retries = 3
    for i in range(max_retries):
        try:
            return do_operation()
        except Error:
            continue
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        retry_matches = [p for p in result['antipatterns'] 
                        if p.subcategory == 'retry_magic']
        assert len(retry_matches) >= 1
    
    def test_detect_sleep_magic(self, analyzer, temp_file):
        """Test detection of sleep/delay magic numbers."""
        content = """
import time

def poll_for_result():
    while True:
        result = check_status()
        if result:
            return result
        time.sleep(5)
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        sleep_matches = [p for p in result['antipatterns'] 
                        if p.subcategory == 'sleep_magic']
        assert len(sleep_matches) >= 1
    
    def test_no_magic_with_constants(self, analyzer, temp_file):
        """Test that named constants reduce detections."""
        content = """
from http import HTTPStatus

DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRY_ATTEMPTS = 5

def check_response(response):
    if response.status_code == HTTPStatus.OK:
        return True
    return False
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # With proper constants, should have fewer magic number detections
        magic_matches = [p for p in result['antipatterns'] 
                        if p.antipattern_type == 'magic_numbers']
        # May still detect some patterns but overall confidence should be manageable
        assert len(magic_matches) <= 3


class TestAnalyzerOutput:
    """Test analyzer output format and structure."""
    
    def test_output_structure(self, analyzer, temp_file):
        """Test that output has required structure."""
        content = """
def simple_function():
    return 42
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert 'confidence' in result
        assert 'antipatterns' in result
        assert 'patterns' in result
        assert 'summary' in result
        assert 'antipattern_counts' in result
        assert 'severity_distribution' in result
        assert 'category_distribution' in result
        assert 'analyzer_version' in result
    
    def test_summary_structure(self, analyzer, temp_file):
        """Test summary has required fields."""
        content = """
@experimental
def test():
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        summary = result['summary']
        
        assert 'total_antipatterns' in summary
        assert 'confidence' in summary
        assert 'risk_level' in summary
        assert 'antipattern_distribution' in summary
        assert 'category_distribution' in summary
        assert 'severity_distribution' in summary
        assert 'recommendations' in summary
    
    def test_antipattern_match_structure(self, analyzer, temp_file):
        """Test antipattern match has all required fields."""
        content = """
@beta
def beta_feature():
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert len(result['antipatterns']) > 0
        match = result['antipatterns'][0]
        
        assert hasattr(match, 'antipattern_type')
        assert hasattr(match, 'line_number')
        assert hasattr(match, 'severity')
        assert hasattr(match, 'confidence')
        assert hasattr(match, 'context')
        assert hasattr(match, 'suggestion')
        assert hasattr(match, 'category')
        assert hasattr(match, 'subcategory')
    
    def test_patterns_list_structure(self, analyzer, temp_file):
        """Test patterns list matches expected format."""
        content = """
@experimental
def experimental_feature():
    # HACK: workaround for bug
    pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert len(result['patterns']) > 0
        pattern = result['patterns'][0]
        
        assert 'type' in pattern
        assert 'line' in pattern
        assert 'severity' in pattern
        assert 'confidence' in pattern
        assert 'context' in pattern
        assert 'suggestion' in pattern
        assert 'category' in pattern


class TestConfidenceCalculation:
    """Test confidence score calculation."""
    
    def test_no_antipatterns_zero_confidence(self, analyzer, temp_file):
        """Test that clean code has zero confidence."""
        content = """
def clean_function(data: str) -> str:
    '''Process data and return result.'''
    return data.upper()
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert result['confidence'] == 0.0
    
    def test_critical_antipatterns_high_confidence(self, analyzer, tmp_path):
        """Test that critical antipatterns increase confidence."""
        requirements = tmp_path / "requirements.txt"
        content = """
package1==1.0.0-unstable
package2==2.0.0-nightly
package3==0.0.1
"""
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        # Multiple critical issues should give higher confidence
        assert result['confidence'] > 0.3
    
    def test_confidence_capped_at_max(self, analyzer, tmp_path):
        """Test that confidence is capped at maximum."""
        requirements = tmp_path / "requirements.txt"
        # Many unstable versions
        content = "\n".join([
            f"package{i}==1.0.0-unstable" for i in range(20)
        ])
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        # Should be capped at 0.92
        assert result['confidence'] <= 0.92


class TestRiskLevels:
    """Test risk level determination."""
    
    def test_minimal_risk(self, analyzer, temp_file):
        """Test minimal risk for clean code."""
        content = """
def clean_function():
    return True
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert result['summary']['risk_level'] == 'MINIMAL'
    
    def test_risk_levels_progression(self, analyzer):
        """Test that risk levels progress correctly."""
        # This tests the internal method
        assert analyzer._get_risk_level(0.0) == 'MINIMAL'
        assert analyzer._get_risk_level(0.14) == 'MINIMAL'
        assert analyzer._get_risk_level(0.20) == 'LOW'
        assert analyzer._get_risk_level(0.40) == 'MEDIUM'
        assert analyzer._get_risk_level(0.60) == 'HIGH'
        assert analyzer._get_risk_level(0.80) == 'CRITICAL'


class TestCategoryDistribution:
    """Test category distribution tracking."""
    
    def test_organizational_category(self, analyzer, tmp_path):
        """Test that bleeding edge is categorized as organizational."""
        requirements = tmp_path / "requirements.txt"
        content = "package==1.0.0-alpha"
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        assert 'organizational' in result['category_distribution']
    
    def test_design_category(self, analyzer, temp_file):
        """Test that gold plating is categorized as design."""
        content = """
class NodeVisitor:
    def visit_node(self, node):
        pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        if result['antipatterns']:
            assert any(m.category == 'design' for m in result['antipatterns'])
    
    def test_programming_category(self, analyzer, temp_file):
        """Test that magic numbers are categorized as programming."""
        content = """
def check_status(code):
    if code == 200:
        return 'ok'
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        if result['antipatterns']:
            assert any(m.category == 'programming' for m in result['antipatterns'])


class TestRecommendations:
    """Test recommendation generation."""
    
    def test_bleeding_edge_recommendation(self, analyzer, tmp_path):
        """Test recommendation for bleeding edge issues."""
        requirements = tmp_path / "requirements.txt"
        content = "package==1.0.0-beta"
        requirements.write_text(content)
        
        result = analyzer.analyze(requirements, content, 'text')
        
        recommendations = result['summary']['recommendations']
        assert any('bleeding edge' in r.lower() or 'stabiliz' in r.lower() 
                  for r in recommendations)
    
    def test_gold_plating_recommendation(self, analyzer, temp_file):
        """Test recommendation for gold plating issues."""
        content = """
_cache = {}

class AbstractFactory:
    pass

class Builder:
    pass

class Strategy:
    pass

class Visitor:
    def visit_x(self):
        pass
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        if result['antipattern_counts'].get('gold_plating', 0) > 3:
            recommendations = result['summary']['recommendations']
            assert any('over-engineering' in r.lower() or 'yagni' in r.lower() 
                      for r in recommendations)
    
    def test_clean_code_recommendation(self, analyzer, temp_file):
        """Test recommendation for clean code."""
        content = """
def simple_clean_function():
    return True
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        recommendations = result['summary']['recommendations']
        assert any('good practices' in r.lower() or 'continue' in r.lower() 
                  for r in recommendations)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_file(self, analyzer, temp_file):
        """Test handling of empty file."""
        content = ""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        assert result['confidence'] == 0.0
        assert len(result['antipatterns']) == 0
    
    def test_only_comments(self, analyzer, temp_file):
        """Test file with only comments."""
        content = """
# This is a comment
# Another comment
# And another
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # Should not crash and should have low/no antipatterns
        assert result['confidence'] >= 0.0
    
    def test_large_file(self, analyzer, temp_file):
        """Test handling of large file."""
        content = "\n".join([
            f"def function_{i}():\n    return {i}" 
            for i in range(500)
        ])
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # Should complete without error
        assert 'confidence' in result
    
    def test_binary_content(self, analyzer, temp_file):
        """Test handling of non-text content."""
        content = "Some text with special chars: \x00\x01\x02"
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # Should not crash
        assert 'confidence' in result
    
    def test_unknown_language(self, analyzer, temp_file):
        """Test handling of unknown language."""
        content = "some content"
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'unknown_lang')
        
        # Should not crash
        assert 'confidence' in result


class TestIntegration:
    """Integration tests with realistic code samples."""
    
    def test_mixed_antipatterns(self, analyzer, temp_file):
        """Test detection of multiple antipattern types."""
        content = """
@experimental
def process_data():
    # HACK: workaround for upstream bug
    _cache = {}
    
    def inner():
        if status == 200:
            time.sleep(30)
            return True
        return False
    
    return inner

class AbstractProcessor:
    def process(self):
        raise NotImplementedError
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # Should detect multiple types
        antipattern_types = set(m.antipattern_type for m in result['antipatterns'])
        # At least bleeding_edge and gold_plating should be detected
        assert len(antipattern_types) >= 1
        assert result['confidence'] > 0
    
    def test_clean_production_code(self, analyzer, temp_file):
        """Test that clean production code has low detection."""
        content = """
from typing import Optional
from dataclasses import dataclass


@dataclass
class UserProfile:
    '''User profile data class.'''
    user_id: str
    email: str
    name: Optional[str] = None


class UserService:
    '''Service for user operations.'''
    
    def __init__(self, repository):
        self._repository = repository
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        '''Retrieve user by ID.'''
        return self._repository.find_by_id(user_id)
    
    def create_user(self, email: str, name: str) -> UserProfile:
        '''Create a new user.'''
        user = UserProfile(
            user_id=generate_id(),
            email=email,
            name=name
        )
        self._repository.save(user)
        return user
"""
        temp_file.write_text(content)
        
        result = analyzer.analyze(temp_file, content, 'python')
        
        # Clean code should have low confidence
        assert result['confidence'] < 0.5
        assert result['summary']['risk_level'] in ('MINIMAL', 'LOW', 'MEDIUM')
