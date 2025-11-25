"""
Pattern Analyzer - Detects AI Code Patterns
Targets 70%+ accuracy for pattern-based AI detection.

Detects:
1. Generic naming (temp, data, result, obj, item)
2. Verbose comments (over-explaining obvious code)
3. Boolean traps (unclear boolean parameters)
4. Magic numbers (unexplained constants)
5. God functions (functions too long, too complex)

Research-backed patterns from Google Research 2024, Stanford CS 2024.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import Counter


@dataclass
class PatternMatch:
    """Represents a detected pattern."""
    pattern_type: str  # 'generic_naming', 'verbose_comment', etc.
    line_number: int
    column: int
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float  # 0.0 - 1.0
    context: str
    suggestion: str


class PatternAnalyzer:
    """
    Detect AI code patterns.
    
    AI models exhibit characteristic patterns:
    - Generic variable names (temp, data, result, obj, item)
    - Verbose comments explaining obvious operations
    - Boolean traps (unclear boolean parameters)
    - Magic numbers without explanation
    - God functions (too long, too complex)
    
    Target: 70%+ accuracy for pattern detection.
    """
    
    # Generic variable names (AI loves these)
    GENERIC_NAMES = {
        # Critical indicators (very generic)
        'temp', 'tmp', 'temporary',
        'data', 'datum', 'info', 'information',
        'result', 'results', 'output', 'ret', 'retval',
        'obj', 'object', 'item', 'items',
        'thing', 'things', 'stuff',
        'value', 'values', 'val', 'vals',
        'var', 'variable',
        'foo', 'bar', 'baz',
        
        # Numbered variables (func1, func2, var1, var2)
        # Detected via regex
        
        # High indicators (somewhat generic)
        'handler', 'manager', 'helper', 'utility', 'util',
        'processor', 'builder', 'factory',
        'param', 'params', 'parameter', 'parameters',
        'arg', 'args', 'argument', 'arguments',
        'config', 'configuration', 'settings',
        'options', 'opts',
    }
    
    # AI-characteristic comment phrases
    AI_COMMENT_PHRASES = [
        # Tutorial/teaching style
        r'\b[Nn]ote that\b',
        r"\b[Ii]t'?s worth noting\b",
        r'\b[Kk]eep in mind\b',
        r"\b[Ii]t'?s important to\b",
        r'\b[Pp]lease note\b',
        r'\b[Aa]s you can see\b',
        r"\b[Ll]et'?s break this down\b",
        r'\b[Ii]n this example\b',
        r"\b[Hh]ere'?s how it works\b",
        r'\b[Ss]imply put\b',
        r'\b[Ee]ssentially\b',
        r'\b[Ii]mportantly\b',
        r'\b[Cc]rucially\b',
        r'\b[Nn]otably\b',
        
        # Over-explaining obvious operations
        r'\b[Aa]dd.*together\b',
        r'\b[Rr]eturn.*result\b',
        r'\b[Cc]reate.*new\b',
        r'\b[Ii]nitialize.*to\b',
        r'\b[Ss]et.*to.*value\b',
        r'\b[Ll]oop through\b',
        r'\b[Ii]terate over\b',
    ]
    
    # Magic number patterns (excluding common constants)
    ACCEPTABLE_NUMBERS = {0, 1, -1, 2, 10, 100, 1000}
    
    # God function thresholds
    MAX_FUNCTION_LINES = 50  # Functions > 50 lines are suspicious
    MAX_FUNCTION_PARAMETERS = 5  # > 5 params is a code smell
    
    def __init__(self):
        """Initialize the pattern analyzer."""
        self.compiled_ai_phrases = [
            re.compile(phrase, re.IGNORECASE) 
            for phrase in self.AI_COMMENT_PHRASES
        ]
    
    def analyze(self, file_path: Path, content: str, language: str) -> Dict:
        """
        Analyze code for AI patterns.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            Dict with analysis results
        """
        lines = content.split('\n')
        
        # Collect all pattern matches
        matches = []
        
        # 1. Generic naming detection
        matches.extend(self._detect_generic_naming(content, lines, language))
        
        # 2. Verbose comments detection
        matches.extend(self._detect_verbose_comments(content, lines, language))
        
        # 3. Boolean trap detection
        matches.extend(self._detect_boolean_traps(content, lines, language))
        
        # 4. Magic number detection
        matches.extend(self._detect_magic_numbers(content, lines, language))
        
        # 5. God function detection
        matches.extend(self._detect_god_functions(content, lines, language))
        
        # Calculate confidence score
        confidence = self._calculate_confidence(matches, len(lines))
        
        # Generate summary
        summary = self._generate_summary(matches, confidence)
        
        return {
            'confidence': confidence,
            'patterns': matches,  # Changed from 'matches' to 'patterns' for test compatibility
            'matches': matches,  # Keep for backward compatibility
            'summary': summary,
            'pattern_counts': self._count_patterns(matches),
            'pattern_distribution': self._count_patterns(matches),  # Add for test compatibility
            'severity_distribution': self._severity_distribution(matches),
        }
    
    def _detect_generic_naming(self, content: str, lines: List[str], language: str) -> List[PatternMatch]:
        """Detect generic variable/function names."""
        matches = []
        
        # Language-specific identifier patterns
        if language in ['python', 'javascript', 'typescript', 'ruby', 'php']:
            # Snake_case or camelCase
            identifier_pattern = r'\b([a-z_][a-z0-9_]*)\b'
        elif language in ['java', 'csharp', 'kotlin', 'swift', 'go']:
            # camelCase or PascalCase
            identifier_pattern = r'\b([a-z][a-zA-Z0-9]*)\b'
        else:
            # Generic
            identifier_pattern = r'\b([a-z_][a-z0-9_]*)\b'
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and strings
            if self._is_comment_or_string(line, language):
                continue
            
            # Find all identifiers
            identifiers = re.findall(identifier_pattern, line.lower())
            
            for identifier in identifiers:
                # Check against generic names
                if identifier in self.GENERIC_NAMES:
                    severity = self._get_naming_severity(identifier, line)
                    confidence = self._get_naming_confidence(identifier)
                    
                    matches.append(PatternMatch(
                        pattern_type='generic_naming',
                        line_number=line_num,
                        column=line.find(identifier),
                        severity=severity,
                        confidence=confidence,
                        context=line.strip(),
                        suggestion=f"Replace generic name '{identifier}' with descriptive name (e.g., 'user_data', 'api_response', 'validated_input')"
                    ))
                
                # Check for numbered variables (temp1, temp2, func1, func2)
                if re.match(r'^[a-z]+\d+$', identifier):
                    matches.append(PatternMatch(
                        pattern_type='numbered_variable',
                        line_number=line_num,
                        column=line.find(identifier),
                        severity='HIGH',
                        confidence=0.85,
                        context=line.strip(),
                        suggestion=f"Replace numbered variable '{identifier}' with descriptive name"
                    ))
        
        return matches
    
    def _detect_verbose_comments(self, content: str, lines: List[str], language: str) -> List[PatternMatch]:
        """Detect verbose, over-explaining comments."""
        matches = []
        
        # Calculate comment-to-code ratio
        comment_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if self._is_comment_line(stripped, language):
                comment_lines += 1
            else:
                code_lines += 1
        
        # AI code often has comment-to-code ratio > 0.4
        if code_lines > 0:
            ratio = comment_lines / (comment_lines + code_lines)
            
            if ratio > 0.4:
                matches.append(PatternMatch(
                    pattern_type='verbose_comments',
                    line_number=1,
                    column=0,
                    severity='MEDIUM',
                    confidence=min(0.9, ratio * 1.5),
                    context=f"Comment-to-code ratio: {ratio:.2%} (threshold: 40%)",
                    suggestion="Reduce comment verbosity. Comment 'why', not 'what'."
                ))
        
        # Check for AI-characteristic phrases
        for line_num, line in enumerate(lines, 1):
            if not self._is_comment_line(line.strip(), language):
                continue
            
            for phrase_regex in self.compiled_ai_phrases:
                if phrase_regex.search(line):
                    matches.append(PatternMatch(
                        pattern_type='ai_comment_phrase',
                        line_number=line_num,
                        column=0,
                        severity='MEDIUM',
                        confidence=0.80,
                        context=line.strip(),
                        suggestion="Remove tutorial-style phrases. Keep comments concise and technical."
                    ))
                    break  # One match per line
        
        # Check for line-by-line explanations (comment after every line)
        consecutive_commented_lines = 0
        for line_num, line in enumerate(lines, 1):
            if '#' in line or '//' in line:  # Inline comment
                consecutive_commented_lines += 1
                if consecutive_commented_lines >= 5:
                    matches.append(PatternMatch(
                        pattern_type='excessive_inline_comments',
                        line_number=line_num - 4,
                        column=0,
                        severity='MEDIUM',
                        confidence=0.75,
                        context="Line-by-line comments detected",
                        suggestion="Avoid explaining every line. Trust the reader understands basic operations."
                    ))
                    consecutive_commented_lines = 0
            else:
                consecutive_commented_lines = 0
        
        return matches
    
    def _detect_boolean_traps(self, content: str, lines: List[str], language: str) -> List[PatternMatch]:
        """Detect boolean trap patterns."""
        matches = []
        
        # Pattern: function_call(True, False, True) or similar
        # Multiple consecutive boolean literals
        boolean_pattern = r'\b(True|False|true|false)\s*,\s*(True|False|true|false)'
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment_line(line.strip(), language):
                continue
            
            if re.search(boolean_pattern, line):
                # Count consecutive booleans
                bool_count = len(re.findall(r'\b(True|False|true|false)\b', line))
                
                if bool_count >= 2:
                    matches.append(PatternMatch(
                        pattern_type='boolean_trap',
                        line_number=line_num,
                        column=0,
                        severity='HIGH',
                        confidence=0.80,
                        context=line.strip(),
                        suggestion=f"Use named parameters instead of {bool_count} positional booleans (e.g., include_metadata=True)"
                    ))
        
        return matches
    
    def _detect_magic_numbers(self, content: str, lines: List[str], language: str) -> List[PatternMatch]:
        """Detect magic numbers (unexplained constants)."""
        matches = []
        
        # Pattern for numeric literals in code
        number_pattern = r'\b(\d+\.?\d*)\b'
        
        for line_num, line in enumerate(lines, 1):
            if self._is_comment_or_string(line, language):
                continue
            
            # Skip lines with assignments to constants (CONST = 100)
            if re.match(r'^\s*[A-Z_]+\s*=', line):
                continue
            
            numbers = re.findall(number_pattern, line)
            
            for num_str in numbers:
                try:
                    num = float(num_str)
                    
                    # Skip acceptable numbers
                    if num in self.ACCEPTABLE_NUMBERS:
                        continue
                    
                    # Skip if number has an explaining comment
                    if '#' in line or '//' in line:
                        continue
                    
                    # Magic number found
                    severity = 'MEDIUM' if num < 100 else 'HIGH'
                    
                    matches.append(PatternMatch(
                        pattern_type='magic_number',
                        line_number=line_num,
                        column=line.find(num_str),
                        severity=severity,
                        confidence=0.70,
                        context=line.strip(),
                        suggestion=f"Replace magic number {num_str} with named constant (e.g., MAX_RETRIES = {num_str})"
                    ))
                except ValueError:
                    continue
        
        return matches
    
    def _detect_god_functions(self, content: str, lines: List[str], language: str) -> List[PatternMatch]:
        """Detect god functions (too long, too complex)."""
        matches = []
        
        # Simple function detection (language-agnostic patterns)
        func_patterns = {
            'python': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'javascript': r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'typescript': r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'java': r'^\s*(public|private|protected)?\s*(static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'csharp': r'^\s*(public|private|protected)?\s*(static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        }
        
        func_pattern = func_patterns.get(language, r'^\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        
        current_function = None
        function_start = 0
        function_lines = 0
        indent_level = 0
        
        for line_num, line in enumerate(lines, 1):
            # Detect function start
            match = re.match(func_pattern, line)
            if match:
                # Save previous function if too long
                if current_function and function_lines > self.MAX_FUNCTION_LINES:
                    matches.append(PatternMatch(
                        pattern_type='god_function',
                        line_number=function_start,
                        column=0,
                        severity='HIGH',
                        confidence=0.75,
                        context=f"Function '{current_function}' has {function_lines} lines (threshold: {self.MAX_FUNCTION_LINES})",
                        suggestion=f"Break '{current_function}' into smaller functions (Single Responsibility Principle)"
                    ))
                
                # Start new function
                current_function = match.group(1) if match.lastindex else 'unknown'
                function_start = line_num
                function_lines = 0
                indent_level = len(line) - len(line.lstrip())
            
            # Count function lines
            if current_function:
                current_indent = len(line) - len(line.lstrip())
                
                # Still in function
                if line.strip() and current_indent > indent_level:
                    function_lines += 1
                elif line.strip() and current_indent == 0:
                    # Function ended
                    if function_lines > self.MAX_FUNCTION_LINES:
                        matches.append(PatternMatch(
                            pattern_type='god_function',
                            line_number=function_start,
                            column=0,
                            severity='HIGH',
                            confidence=0.75,
                            context=f"Function '{current_function}' has {function_lines} lines",
                            suggestion=f"Break '{current_function}' into smaller functions"
                        ))
                    current_function = None
        
        return matches
    
    def _is_comment_or_string(self, line: str, language: str) -> bool:
        """Check if line is primarily a comment or string."""
        stripped = line.strip()
        
        # Comment detection
        if language in ['python', 'ruby', 'shell']:
            if stripped.startswith('#'):
                return True
        elif language in ['javascript', 'typescript', 'java', 'csharp', 'go', 'rust', 'c', 'cpp']:
            if stripped.startswith('//') or stripped.startswith('/*'):
                return True
        
        # String detection (basic)
        if stripped.startswith('"') or stripped.startswith("'"):
            return True
        
        return False
    
    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if line is a comment."""
        if language in ['python', 'ruby', 'shell']:
            return line.startswith('#')
        elif language in ['javascript', 'typescript', 'java', 'csharp', 'go', 'rust', 'c', 'cpp']:
            return line.startswith('//') or line.startswith('/*') or line.startswith('*')
        return False
    
    def _get_naming_severity(self, name: str, context: str) -> str:
        """Determine severity of generic naming."""
        # Critical generic names
        if name in ['temp', 'tmp', 'data', 'result', 'obj', 'item']:
            # Check if in main logic (not utility/test)
            if any(word in context.lower() for word in ['def ', 'function ', 'class ']):
                return 'CRITICAL'
            return 'HIGH'
        
        # High generic names
        if name in ['handler', 'manager', 'helper', 'processor']:
            return 'MEDIUM'
        
        return 'LOW'
    
    def _get_naming_confidence(self, name: str) -> float:
        """Calculate confidence for generic naming."""
        critical_names = ['temp', 'tmp', 'data', 'result', 'obj', 'item', 'thing', 'stuff']
        
        if name in critical_names:
            return 0.90
        else:
            return 0.70
    
    def _calculate_confidence(self, matches: List[PatternMatch], total_lines: int) -> float:
        """Calculate overall confidence score."""
        if not matches:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            'CRITICAL': 1.0,
            'HIGH': 0.8,
            'MEDIUM': 0.5,
            'LOW': 0.3,
        }
        
        # Calculate weighted score
        total_weight = 0.0
        for match in matches:
            weight = severity_weights.get(match.severity, 0.5)
            total_weight += weight * match.confidence
        
        # Normalize by file size (larger files expected to have more issues)
        normalized_score = total_weight / max(1, total_lines / 10)
        
        # Cap at 0.95
        return min(0.95, normalized_score)
    
    def _generate_summary(self, matches: List[PatternMatch], confidence: float) -> Dict:
        """Generate analysis summary."""
        pattern_counts = self._count_patterns(matches)
        
        return {
            'total_patterns': len(matches),
            'confidence': confidence,
            'risk_level': self._get_risk_level(confidence),
            'pattern_distribution': pattern_counts,  # Add for test compatibility
            'top_patterns': sorted(
                pattern_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            'recommendation': self._get_recommendation(confidence, pattern_counts),
        }
    
    def _count_patterns(self, matches: List[PatternMatch]) -> Dict[str, int]:
        """Count occurrences of each pattern type."""
        counter = Counter(match.pattern_type for match in matches)
        return dict(counter)
    
    def _severity_distribution(self, matches: List[PatternMatch]) -> Dict[str, int]:
        """Get distribution of severity levels."""
        counter = Counter(match.severity for match in matches)
        return dict(counter)
    
    def _get_risk_level(self, confidence: float) -> str:
        """Determine risk level from confidence."""
        if confidence >= 0.7:
            return 'HIGH'
        elif confidence >= 0.4:
            return 'MEDIUM'
        elif confidence >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _get_recommendation(self, confidence: float, pattern_counts: Dict[str, int]) -> str:
        """Generate actionable recommendation."""
        if confidence >= 0.7:
            top_pattern = max(pattern_counts, key=pattern_counts.get) if pattern_counts else 'patterns'
            return f"High AI likelihood. Focus on fixing {top_pattern}. Consider manual review."
        elif confidence >= 0.4:
            return "Moderate AI indicators. Review flagged sections and refactor as needed."
        elif confidence >= 0.2:
            return "Low AI indicators. Minor cleanup suggested."
        else:
            return "Minimal AI indicators detected. Code appears human-written."
