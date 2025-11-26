"""
Tests for Security Analyzer
Tests detection of security vulnerabilities including SQL injection,
command injection, XSS, path traversal, weak crypto, insecure randomness,
and hardcoded secrets (OWASP Top 10 coverage).
"""

import pytest
from pathlib import Path
from codebase_csi.analyzers.security_analyzer import SecurityAnalyzer, SecurityVulnerability


class TestSecurityAnalyzer:
    """Test suite for Security Analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return SecurityAnalyzer()
    
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        file_path = tmp_path / "test_code.py"
        return file_path
    
    # === SQL Injection Tests ===
    
    def test_detect_sql_injection_string_concatenation(self, analyzer, temp_file):
        """Test detection of SQL injection via string concatenation."""
        code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)
    return cursor.fetchone()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        vulnerabilities = result.get('vulnerabilities', [])
        sql_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'sql_injection']
        assert len(sql_vulns) > 0
        assert any(v.severity == 'CRITICAL' for v in sql_vulns)
        assert any(v.owasp_category == 'A03:2021 - Injection' for v in sql_vulns)
    
    def test_detect_sql_injection_format_string(self, analyzer, temp_file):
        """Test detection of SQL injection via format string."""
        code = """
def search_users(name):
    query = "SELECT * FROM users WHERE name = '{}'".format(name)
    return db.execute(query)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        vulnerabilities = result.get('vulnerabilities', [])
        sql_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'sql_injection']
        assert len(sql_vulns) > 0
    
    def test_detect_sql_injection_fstring(self, analyzer, temp_file):
        """Test detection of SQL injection via f-string."""
        code = """
def get_orders(user_id):
    query = f"SELECT * FROM orders WHERE user_id = {user_id}"
    cursor.execute(query)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        vulnerabilities = result.get('vulnerabilities', [])
        sql_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'sql_injection']
        assert len(sql_vulns) > 0
    
    def test_parameterized_query_safe(self, analyzer, temp_file):
        """Test that parameterized queries don't trigger false positives."""
        code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()

def search_users(name, email):
    query = "SELECT * FROM users WHERE name = %s AND email = %s"
    cursor.execute(query, (name, email))
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - using parameterized queries
        assert result['confidence'] < 0.3
    
    # === Command Injection Tests ===
    
    def test_detect_command_injection_os_system(self, analyzer, temp_file):
        """Test detection of command injection via os.system."""
        code = """
import os

def delete_file(filename):
    os.system("rm -rf " + filename)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        cmd_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'command_injection']
        assert len(cmd_vulns) > 0
        assert any(v.severity == 'CRITICAL' for v in cmd_vulns)
    
    def test_detect_command_injection_subprocess_shell(self, analyzer, temp_file):
        """Test detection of shell=True in subprocess."""
        code = """
import subprocess

def run_command(user_input):
    subprocess.run(user_input, shell=True)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        vulnerabilities = result.get('vulnerabilities', [])
        cmd_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'command_injection']
        assert len(cmd_vulns) > 0
    
    def test_detect_eval_usage(self, analyzer, temp_file):
        """Test detection of dangerous eval() usage."""
        code = """
def calculate(user_expression):
    result = eval(user_expression)
    return result
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        cmd_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'command_injection']
        assert len(cmd_vulns) > 0
        assert any(v.severity == 'CRITICAL' for v in cmd_vulns)
    
    def test_detect_exec_usage(self, analyzer, temp_file):
        """Test detection of dangerous exec() usage."""
        code = """
def run_code(user_code):
    exec(user_code)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
    
    def test_safe_subprocess_usage(self, analyzer, temp_file):
        """Test that safe subprocess usage doesn't trigger false positives."""
        code = """
import subprocess

def safe_command():
    subprocess.run(["ls", "-la"], shell=False)
    subprocess.run(["echo", "hello"])
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - safe subprocess usage
        assert result['confidence'] < 0.3
    
    # === XSS Tests ===
    
    def test_detect_xss_html_concatenation(self, analyzer, temp_file):
        """Test detection of XSS via HTML concatenation."""
        code = """
def render_greeting(username):
    html = "<h1>Welcome " + username + "</h1>"
    return html
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        vulnerabilities = result.get('vulnerabilities', [])
        xss_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'xss']
        assert len(xss_vulns) > 0
    
    def test_detect_xss_innerhtml(self, analyzer, temp_file):
        """Test detection of XSS via innerHTML."""
        code = """
function displayMessage(msg) {
    document.getElementById('message').innerHTML = msg + '<br>';
}
"""
        result = analyzer.analyze(temp_file, code, "javascript")
        
        assert result['confidence'] > 0.5
        vulnerabilities = result.get('vulnerabilities', [])
        xss_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'xss']
        assert len(xss_vulns) > 0
    
    def test_detect_xss_document_write(self, analyzer, temp_file):
        """Test detection of XSS via document.write."""
        code = """
function render(content) {
    document.write("<div>" + content + "</div>");
}
"""
        result = analyzer.analyze(temp_file, code, "javascript")
        
        assert result['confidence'] > 0.5
    
    # === Path Traversal Tests ===
    
    def test_detect_path_traversal_open_concat(self, analyzer, temp_file):
        """Test detection of path traversal in file operations."""
        code = """
def read_file(filename):
    with open("uploads/" + filename) as f:
        return f.read()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
        vulnerabilities = result.get('vulnerabilities', [])
        path_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'path_traversal']
        assert len(path_vulns) > 0
    
    def test_detect_path_traversal_fstring(self, analyzer, temp_file):
        """Test detection of path traversal via f-string."""
        code = """
def load_config(config_name):
    with open(f"configs/{config_name}") as f:
        return f.read()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.5
    
    def test_safe_path_operations(self, analyzer, temp_file):
        """Test that safe path operations don't trigger false positives."""
        code = """
def read_config():
    with open("config.json") as f:
        return f.read()

def save_data(data):
    import json
    with open("data.json", "w") as f:
        json.dump(data, f)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - no user input in paths
        assert result['confidence'] < 0.3
    
    # === Weak Cryptography Tests ===
    
    def test_detect_md5_usage(self, analyzer, temp_file):
        """Test detection of MD5 usage."""
        code = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        crypto_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'weak_cryptography']
        assert len(crypto_vulns) > 0
        assert any(v.owasp_category == 'A02:2021 - Cryptographic Failures' for v in crypto_vulns)
    
    def test_detect_sha1_usage(self, analyzer, temp_file):
        """Test detection of SHA1 usage."""
        code = """
import hashlib

def create_signature(data):
    return hashlib.sha1(data.encode()).hexdigest()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        crypto_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'weak_cryptography']
        assert len(crypto_vulns) > 0
    
    def test_detect_des_usage(self, analyzer, temp_file):
        """Test detection of DES encryption."""
        code = """
from Crypto.Cipher import DES

def encrypt_data(key, data):
    cipher = DES.new(key)
    return cipher.encrypt(data)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
    
    def test_strong_crypto_acceptable(self, analyzer, temp_file):
        """Test that strong cryptography doesn't trigger false positives."""
        code = """
import hashlib

def hash_password(password, salt):
    return hashlib.sha256(password.encode() + salt).hexdigest()

def secure_hash(data):
    return hashlib.sha512(data.encode()).hexdigest()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - using strong algorithms
        assert result['confidence'] < 0.3
    
    # === Insecure Randomness Tests ===
    
    def test_detect_insecure_random_for_security(self, analyzer, temp_file):
        """Test detection of insecure random for security purposes."""
        code = """
import random

def generate_token():
    token = random.randint(1000000, 9999999)
    return token

def create_session_id():
    session = random.random()
    return str(session)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.6
        vulnerabilities = result.get('vulnerabilities', [])
        random_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'insecure_randomness']
        assert len(random_vulns) > 0
    
    def test_random_for_non_security_acceptable(self, analyzer, temp_file):
        """Test that random for non-security purposes is acceptable."""
        code = """
import random

def shuffle_playlist(songs):
    random.shuffle(songs)
    return songs

def pick_random_color():
    return random.choice(['red', 'blue', 'green'])
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - not security-related
        assert result['confidence'] < 0.3
    
    def test_secure_random_acceptable(self, analyzer, temp_file):
        """Test that secure randomness doesn't trigger false positives."""
        code = """
import secrets

def generate_token():
    return secrets.token_hex(16)

def create_password():
    return secrets.token_urlsafe(32)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - using secrets module
        assert result['confidence'] < 0.3
    
    # === Hardcoded Secrets Tests ===
    
    def test_detect_hardcoded_password(self, analyzer, temp_file):
        """Test detection of hardcoded passwords."""
        code = """
def connect_to_database():
    password = "SuperSecret123!"
    db.connect(username="admin", password=password)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        secret_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'hardcoded_secret']
        assert len(secret_vulns) > 0
        assert any(v.severity == 'CRITICAL' for v in secret_vulns)
    
    def test_detect_hardcoded_api_key(self, analyzer, temp_file):
        """Test detection of hardcoded API keys."""
        code = """
def call_api():
    api_key = "1234567890abcdef1234567890abcdef"
    headers = {"Authorization": f"Bearer {api_key}"}
    return requests.get(url, headers=headers)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
        vulnerabilities = result.get('vulnerabilities', [])
        secret_vulns = [v for v in vulnerabilities if v.vulnerability_type == 'hardcoded_secret']
        assert len(secret_vulns) > 0
    
    def test_detect_openai_key(self, analyzer, temp_file):
        """Test detection of OpenAI API keys."""
        code = """
import openai

openai.api_key = "sk-1234567890abcdef1234567890abcdef"
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
    
    def test_detect_aws_secret(self, analyzer, temp_file):
        """Test detection of AWS secrets."""
        code = """
def configure_aws():
    aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYSECRETKEY"
    return aws_secret_access_key
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] > 0.7
    
    def test_ignore_test_secrets(self, analyzer, temp_file):
        """Test that obvious test/example secrets are ignored."""
        code = """
def test_authentication():
    password = "test_password_value"
    api_key = "fake_key_for_testing"
    secret = "dummy_secret_xxx"
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have no hardcoded_secret vulnerabilities - all look like test values
        secret_vulns = [v for v in result.get('vulnerabilities', []) if v.vulnerability_type == 'hardcoded_secret']
        assert len(secret_vulns) == 0
    
    def test_environment_variables_safe(self, analyzer, temp_file):
        """Test that environment variables don't trigger false positives."""
        code = """
import os

def connect():
    password = os.environ.get("DB_PASSWORD")
    api_key = os.getenv("API_KEY")
    secret = os.environ["SECRET_KEY"]
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have low confidence - using environment variables
        assert result['confidence'] < 0.3
    
    # === Multiple Vulnerabilities Tests ===
    
    def test_multiple_vulnerabilities_combined(self, analyzer, temp_file):
        """Test detection of multiple vulnerabilities in same file."""
        code = """
import os
import hashlib

def process_user_data(user_id, filename):
    # SQL injection
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)
    
    # Command injection
    os.system("cat " + filename)
    
    # Weak crypto
    password_hash = hashlib.md5("password123".encode()).hexdigest()
    
    # Hardcoded secret
    api_key = "sk-1234567890abcdef1234567890"
    
    return query
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should detect multiple vulnerabilities
        assert result['confidence'] > 0.8
        vulnerabilities = result.get('vulnerabilities', [])
        vuln_types = {v.vulnerability_type for v in vulnerabilities}
        assert len(vuln_types) >= 3  # Should have at least 3 different types
    
    # === Language Support Tests ===
    
    def test_javascript_support(self, analyzer, temp_file):
        """Test analyzer works with JavaScript code."""
        code = """
function loginUser(username, password) {
    const query = "SELECT * FROM users WHERE username = '" + username + "'";
    db.execute(query);
    
    document.getElementById('welcome').innerHTML = username;
}
"""
        result = analyzer.analyze(temp_file, code, "javascript")
        
        assert result['confidence'] > 0.5
        vulnerabilities = result.get('vulnerabilities', [])
        assert len(vulnerabilities) > 0
    
    def test_php_support(self, analyzer, temp_file):
        """Test analyzer works with PHP code."""
        code = """
<?php
function getUser($userId) {
    $query = "SELECT * FROM users WHERE id = '" . $userId . "'";
    mysql_query($query);
}
?>
"""
        result = analyzer.analyze(temp_file, code, "php")
        
        assert result['confidence'] > 0.5
    
    # === Edge Cases Tests ===
    
    def test_empty_file(self, analyzer, temp_file):
        """Test analyzer handles empty files gracefully."""
        code = ""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert result['confidence'] == 0.0
        assert 'vulnerabilities' in result
        assert len(result['vulnerabilities']) == 0
    
    def test_only_comments(self, analyzer, temp_file):
        """Test analyzer handles files with only comments."""
        code = """
# This is a comment
# Another comment
# password = "secret"  (but it's commented out)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        # Should have very low confidence - no actual code
        assert result['confidence'] < 0.2
    
    def test_confidence_proportional_to_severity(self, analyzer, temp_file):
        """Test that confidence is proportional to vulnerability severity."""
        # Low severity
        code_low = """
def process():
    x = 1 + 1
    return x
"""
        
        # High severity
        code_high = """
import os

def dangerous(user_input):
    os.system("rm -rf " + user_input)
    query = "DELETE FROM users WHERE id = '" + user_input + "'"
    exec(user_input)
"""
        
        result_low = analyzer.analyze(temp_file, code_low, "python")
        result_high = analyzer.analyze(temp_file, code_high, "python")
        
        assert result_high['confidence'] > result_low['confidence']
        assert result_high['confidence'] - result_low['confidence'] > 0.5
    
    def test_summary_statistics(self, analyzer, temp_file):
        """Test that summary statistics are generated correctly."""
        code = """
import os

def unsafe(filename):
    os.system("cat " + filename)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert 'summary' in result
        summary = result['summary']
        assert 'total_vulnerabilities' in summary
        assert 'confidence' in summary
        assert 'risk_level' in summary
    
    def test_owasp_category_distribution(self, analyzer, temp_file):
        """Test OWASP category distribution tracking."""
        code = """
import hashlib

def process(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    password_hash = hashlib.md5("password".encode()).hexdigest()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert 'owasp_categories' in result
        owasp_cats = result['owasp_categories']
        # Should have OWASP categories mapped
        assert isinstance(owasp_cats, dict)
    
    def test_severity_distribution(self, analyzer, temp_file):
        """Test severity distribution tracking."""
        code = """
import os

def dangerous(cmd):
    os.system(cmd)
    eval(cmd)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        assert 'severity_distribution' in result
        severity_dist = result['severity_distribution']
        assert isinstance(severity_dist, dict)
        # Should have CRITICAL severity for eval/os.system
        assert 'CRITICAL' in severity_dist or 'HIGH' in severity_dist
    
    def test_cwe_ids_present(self, analyzer, temp_file):
        """Test that vulnerabilities include CWE IDs."""
        code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return db.execute(query)
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        vulnerabilities = result.get('vulnerabilities', [])
        if vulnerabilities:
            for vuln in vulnerabilities:
                assert hasattr(vuln, 'cwe_id')
                assert vuln.cwe_id.startswith('CWE-')
    
    def test_suggestions_provided(self, analyzer, temp_file):
        """Test that vulnerabilities include remediation suggestions."""
        code = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""
        result = analyzer.analyze(temp_file, code, "python")
        
        vulnerabilities = result.get('vulnerabilities', [])
        if vulnerabilities:
            for vuln in vulnerabilities:
                assert hasattr(vuln, 'suggestion')
                assert vuln.suggestion  # Not empty
                # Suggestion should be helpful
                assert len(vuln.suggestion) > 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
