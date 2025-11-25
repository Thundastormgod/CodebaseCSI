"""
Security Analyzer - Detects Security Vulnerabilities in AI-Generated Code
Targets 70%+ accuracy for security vulnerability detection.

AI-generated code has 2-3x more security vulnerabilities (NYU 2024 research).

Detects:
1. SQL Injection (string concatenation in queries)
2. Command Injection (os.system with user input)
3. XSS (HTML generation without escaping)
4. Path Traversal (file operations without sanitization)
5. Weak Cryptography (MD5, SHA1, weak algorithms)
6. Insecure Randomness (random instead of secrets)
7. Hardcoded Secrets (passwords, API keys in code)
8. Eval/Exec with user input

OWASP Top 10 coverage.
Research-backed from NYU Cybersecurity 2024.
"""

import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability."""
    vulnerability_type: str  # 'sql_injection', 'command_injection', etc.
    line_number: int
    column: int
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float  # 0.0 - 1.0
    owasp_category: str  # OWASP Top 10 category
    context: str
    suggestion: str
    cwe_id: str  # Common Weakness Enumeration ID


class SecurityAnalyzer:
    """
    Detect security vulnerabilities in code.
    
    AI-generated code exhibits more security issues:
    - SQL injection (string concatenation in queries)
    - Command injection (unvalidated input to shell)
    - XSS (unescaped HTML generation)
    - Weak cryptography (MD5, SHA1)
    - Hardcoded secrets
    
    Target: 70%+ accuracy for vulnerability detection.
    """
    
    # SQL Injection Patterns
    SQL_INJECTION_PATTERNS = [
        # String concatenation/formatting in SQL
        (r'(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE).*["\'].*?\+', 'string_concat'),
        (r'(?:SELECT|INSERT|UPDATE|DELETE).*\.format\s*\(', 'format_injection'),
        (r'(?:SELECT|INSERT|UPDATE|DELETE).*%.*%', 'percent_formatting'),
        (r'(?:execute|executemany|exec|query)\s*\(["\'].*?\+', 'execute_concat'),
        (r'(?:execute|executemany|exec|query)\s*\(.*\.format', 'execute_format'),
        (r'(?:execute|executemany|exec|query)\s*\(f["\']', 'fstring_injection'),
        (r'f["\'].*?(?:SELECT|INSERT|UPDATE|DELETE).*?{.*?}', 'fstring_sql'),  # Direct f-string SQL
    ]
    
    # Command Injection Patterns
    COMMAND_INJECTION_PATTERNS = [
        # Dangerous functions with concatenation
        (r'os\.system\s*\(["\'].*?\+', 'os_system_concat'),
        (r'os\.system\s*\(f["\']', 'os_system_fstring'),
        (r'subprocess\.(?:call|run|Popen)\s*\(["\'].*?\+', 'subprocess_concat'),
        (r'subprocess\.(?:call|run|Popen).*shell\s*=\s*True', 'subprocess_shell'),
        (r'eval\s*\(', 'eval_usage'),
        (r'exec\s*\(', 'exec_usage'),
        (r'__import__\s*\(', 'dynamic_import'),
    ]
    
    # XSS/HTML Injection Patterns
    XSS_PATTERNS = [
        (r'<.*?>.*?\+', 'html_concat'),
        (r'<.*?>.*\.format\s*\(', 'html_format'),
        (r'innerHTML\s*=.*?\+', 'innerhtml_concat'),
        (r'document\.write\s*\(.*?\+', 'document_write'),
        (r'<script>.*?\+', 'script_inject'),
    ]
    
    # Path Traversal Patterns
    PATH_TRAVERSAL_PATTERNS = [
        (r'open\s*\(["\'].*?\+', 'file_open_concat'),
        (r'open\s*\(f["\'].*?{', 'file_open_fstring'),
        (r'os\.path\.join\s*\(["\'][^,)]*["\'],\s*[^)]*user', 'path_join_user_input'),
        (r'Path\s*\(["\'].*?\+', 'path_concat'),
    ]
    
    # Weak Cryptography
    WEAK_CRYPTO_PATTERNS = [
        (r'hashlib\.md5\s*\(', 'md5_usage', 'Use SHA-256 or SHA-512'),
        (r'hashlib\.sha1\s*\(', 'sha1_usage', 'Use SHA-256 or SHA-512'),
        (r'DES\.new\s*\(', 'des_usage', 'Use AES'),
        (r'Crypto\.Cipher\.DES', 'des_cipher', 'Use AES'),
        (r'cipher\s*=\s*["\']DES["\']', 'des_string', 'Use AES'),
    ]
    
    # Insecure Randomness
    INSECURE_RANDOM_PATTERNS = [
        (r'random\.(?:randint|random|choice|shuffle)', 'random_not_cryptographic'),
        (r'Math\.random\s*\(', 'javascript_math_random'),
    ]
    
    # Hardcoded Secrets
    SECRET_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']{3,}["\']', 'hardcoded_password'),
        (r'(?:api_key|apikey|api-key)\s*=\s*["\'][^"\']{8,}["\']', 'hardcoded_api_key'),  # More flexible
        (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'hardcoded_secret'),
        (r'token\s*=\s*["\'][^"\']{10,}["\']', 'hardcoded_token'),
        (r'aws_secret_access_key\s*=\s*["\'][^"\']{10,}["\']', 'aws_secret'),  # Require min length
        (r'["\']sk-[A-Za-z0-9]{20,}["\']', 'openai_key'),  # Allow quotes
    ]
    
    def __init__(self):
        """Initialize the security analyzer."""
        # Compile patterns for performance
        self.sql_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.SQL_INJECTION_PATTERNS]
        self.cmd_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.COMMAND_INJECTION_PATTERNS]
        self.xss_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.XSS_PATTERNS]
        self.path_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.PATH_TRAVERSAL_PATTERNS]
        self.crypto_patterns = [(re.compile(p[0], re.IGNORECASE), p[1], p[2]) for p in self.WEAK_CRYPTO_PATTERNS]
        self.random_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.INSECURE_RANDOM_PATTERNS]
        self.secret_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.SECRET_PATTERNS]
    
    def analyze(self, file_path: Path, content: str, language: str) -> Dict:
        """
        Analyze code for security vulnerabilities.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            Dict with analysis results
        """
        lines = content.split('\n')
        
        # Collect vulnerabilities
        vulnerabilities = []
        
        # 1. SQL Injection detection
        vulnerabilities.extend(self._detect_sql_injection(lines, language))
        
        # 2. Command Injection detection
        vulnerabilities.extend(self._detect_command_injection(lines, language))
        
        # 3. XSS detection
        vulnerabilities.extend(self._detect_xss(lines, language))
        
        # 4. Path Traversal detection
        vulnerabilities.extend(self._detect_path_traversal(lines, language))
        
        # 5. Weak Cryptography detection
        vulnerabilities.extend(self._detect_weak_crypto(lines, language))
        
        # 6. Insecure Randomness detection
        vulnerabilities.extend(self._detect_insecure_random(lines, language))
        
        # 7. Hardcoded Secrets detection
        vulnerabilities.extend(self._detect_hardcoded_secrets(lines, language))
        
        # Calculate confidence
        confidence = self._calculate_confidence(vulnerabilities, len(lines))
        
        # Generate summary
        summary = self._generate_summary(vulnerabilities, confidence)
        
        return {
            'confidence': confidence,
            'vulnerabilities': vulnerabilities,
            'summary': summary,
            'vulnerability_counts': self._count_vulnerabilities(vulnerabilities),
            'owasp_categories': self._owasp_distribution(vulnerabilities),
            'severity_distribution': self._severity_distribution(vulnerabilities),
        }
    
    def _detect_sql_injection(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect SQL injection vulnerabilities."""
        vulnerabilities = []
        
        if language not in ['python', 'javascript', 'typescript', 'php', 'java', 'csharp']:
            return vulnerabilities
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type in self.sql_patterns:
                if pattern.search(line):
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='sql_injection',
                        line_number=line_num,
                        column=0,
                        severity='CRITICAL',
                        confidence=0.90,
                        owasp_category='A03:2021 - Injection',
                        context=line.strip(),
                        suggestion='Use parameterized queries (e.g., cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))) instead of string concatenation',
                        cwe_id='CWE-89'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_command_injection(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect command injection vulnerabilities."""
        vulnerabilities = []
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type in self.cmd_patterns:
                if pattern.search(line):
                    # Determine severity
                    if vuln_type in ['eval_usage', 'exec_usage']:
                        severity = 'CRITICAL'
                        confidence = 0.95
                        suggestion = 'Never use eval/exec with user input. Use safer alternatives like ast.literal_eval() or json.loads()'
                    elif vuln_type == 'subprocess_shell':
                        severity = 'HIGH'
                        confidence = 0.85
                        suggestion = 'Avoid shell=True. Use list arguments: subprocess.run(["command", "arg1", "arg2"]) instead'
                    else:
                        severity = 'CRITICAL'
                        confidence = 0.90
                        suggestion = 'Use subprocess with list arguments, validate and sanitize all user input'
                    
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='command_injection',
                        line_number=line_num,
                        column=0,
                        severity=severity,
                        confidence=confidence,
                        owasp_category='A03:2021 - Injection',
                        context=line.strip(),
                        suggestion=suggestion,
                        cwe_id='CWE-78'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_xss(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect XSS vulnerabilities."""
        vulnerabilities = []
        
        if language not in ['python', 'javascript', 'typescript', 'php', 'java']:
            return vulnerabilities
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type in self.xss_patterns:
                if pattern.search(line):
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='xss',
                        line_number=line_num,
                        column=0,
                        severity='HIGH',
                        confidence=0.85,
                        owasp_category='A03:2021 - Injection',
                        context=line.strip(),
                        suggestion='Escape HTML output using html.escape() (Python), DOMPurify (JavaScript), or framework-specific escaping',
                        cwe_id='CWE-79'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_path_traversal(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect path traversal vulnerabilities."""
        vulnerabilities = []
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type in self.path_patterns:
                if pattern.search(line):
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='path_traversal',
                        line_number=line_num,
                        column=0,
                        severity='HIGH',
                        confidence=0.80,
                        owasp_category='A01:2021 - Broken Access Control',
                        context=line.strip(),
                        suggestion='Validate file paths, use Path.resolve() and check if resolved path is within allowed directory',
                        cwe_id='CWE-22'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_weak_crypto(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect weak cryptography."""
        vulnerabilities = []
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type, suggestion in self.crypto_patterns:
                if pattern.search(line):
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='weak_cryptography',
                        line_number=line_num,
                        column=0,
                        severity='HIGH',
                        confidence=0.95,
                        owasp_category='A02:2021 - Cryptographic Failures',
                        context=line.strip(),
                        suggestion=suggestion,
                        cwe_id='CWE-327'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_insecure_random(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect insecure randomness for security purposes."""
        vulnerabilities = []
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            # Check if line is related to security (token, password, key, etc.)
            security_context = any(word in line.lower() for word in [
                'token', 'password', 'secret', 'key', 'salt', 'nonce', 'session'
            ])
            
            if not security_context:
                continue
            
            for pattern, vuln_type in self.random_patterns:
                if pattern.search(line):
                    suggestion = 'Use secrets module (Python) or crypto.getRandomValues() (JavaScript) for cryptographic operations'
                    
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='insecure_randomness',
                        line_number=line_num,
                        column=0,
                        severity='HIGH',
                        confidence=0.85,
                        owasp_category='A02:2021 - Cryptographic Failures',
                        context=line.strip(),
                        suggestion=suggestion,
                        cwe_id='CWE-338'
                    ))
                    break
        
        return vulnerabilities
    
    def _detect_hardcoded_secrets(self, lines: List[str], language: str) -> List[SecurityVulnerability]:
        """Detect hardcoded secrets."""
        vulnerabilities = []
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment(line, language):
                continue
            
            for pattern, vuln_type in self.secret_patterns:
                if pattern.search(line):
                    # Skip obvious test/example values
                    if any(test_val in line.lower() for test_val in [
                        'test', 'example', 'dummy', 'fake', 'sample', '12345', 'xxx'
                    ]):
                        continue
                    
                    vulnerabilities.append(SecurityVulnerability(
                        vulnerability_type='hardcoded_secret',
                        line_number=line_num,
                        column=0,
                        severity='CRITICAL',
                        confidence=0.90,
                        owasp_category='A07:2021 - Identification and Authentication Failures',
                        context=line.strip()[:50] + '...',  # Truncate to avoid exposing secret
                        suggestion='Store secrets in environment variables, key vault, or secrets manager. Never commit secrets to code',
                        cwe_id='CWE-798'
                    ))
                    break
        
        return vulnerabilities
    
    def _is_comment(self, line: str, language: str) -> bool:
        """Check if line is a comment."""
        stripped = line.strip()
        
        if language in ['python', 'ruby', 'shell']:
            return stripped.startswith('#')
        elif language in ['javascript', 'typescript', 'java', 'csharp', 'c', 'cpp', 'go', 'rust']:
            return stripped.startswith('//') or stripped.startswith('/*')
        elif language == 'html':
            return stripped.startswith('<!--')
        
        return False
    
    def _calculate_confidence(self, vulnerabilities: List[SecurityVulnerability], total_lines: int) -> float:
        """Calculate overall confidence score."""
        if not vulnerabilities:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            'CRITICAL': 1.0,
            'HIGH': 0.8,
            'MEDIUM': 0.5,
            'LOW': 0.3,
        }
        
        total_weight = 0.0
        for vuln in vulnerabilities:
            weight = severity_weights.get(vuln.severity, 0.5)
            total_weight += weight * vuln.confidence
        
        # Normalize
        normalized = total_weight / max(1, total_lines / 10)
        
        return min(0.95, normalized)
    
    def _generate_summary(self, vulnerabilities: List[SecurityVulnerability], confidence: float) -> Dict:
        """Generate analysis summary."""
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'confidence': confidence,
            'risk_level': self._get_risk_level(confidence),
            'critical_count': sum(1 for v in vulnerabilities if v.severity == 'CRITICAL'),
            'high_count': sum(1 for v in vulnerabilities if v.severity == 'HIGH'),
            'owasp_categories': list(set(v.owasp_category for v in vulnerabilities)),
            'recommendation': self._get_recommendation(confidence, vulnerabilities),
        }
    
    def _count_vulnerabilities(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, int]:
        """Count vulnerabilities by type."""
        from collections import Counter
        counter = Counter(v.vulnerability_type for v in vulnerabilities)
        return dict(counter)
    
    def _owasp_distribution(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, int]:
        """Get OWASP category distribution."""
        from collections import Counter
        counter = Counter(v.owasp_category for v in vulnerabilities)
        return dict(counter)
    
    def _severity_distribution(self, vulnerabilities: List[SecurityVulnerability]) -> Dict[str, int]:
        """Get severity distribution."""
        from collections import Counter
        counter = Counter(v.severity for v in vulnerabilities)
        return dict(counter)
    
    def _get_risk_level(self, confidence: float) -> str:
        """Determine risk level."""
        if confidence >= 0.7:
            return 'HIGH'
        elif confidence >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_recommendation(self, confidence: float, vulnerabilities: List[SecurityVulnerability]) -> str:
        """Generate recommendation."""
        critical = sum(1 for v in vulnerabilities if v.severity == 'CRITICAL')
        high = sum(1 for v in vulnerabilities if v.severity == 'HIGH')
        
        if critical > 0:
            return f"URGENT: {critical} critical vulnerabilities found. Fix immediately before deployment."
        elif high > 0:
            return f"WARNING: {high} high-severity vulnerabilities found. Address before production."
        elif vulnerabilities:
            return f"INFO: {len(vulnerabilities)} security issues found. Review and remediate."
        else:
            return "No security vulnerabilities detected."
