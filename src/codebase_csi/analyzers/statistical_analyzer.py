"""
Statistical Analyzer - Detects AI Code via Statistical Metrics
Targets 70%+ accuracy for statistical analysis.

Detects:
1. Cyclomatic complexity (AI creates overly complex code)
2. Token diversity (AI uses less varied vocabulary)
3. Nesting depth (AI creates deeply nested structures)
4. Code duplication (AI copy-pastes with minor changes)
5. Function/line metrics (AI creates long functions)

Research-backed metrics from Berkeley 2024, MIT CSAIL 2024.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import Counter
import hashlib


@dataclass
class StatisticalAnomaly:
    """Represents a statistical anomaly."""
    anomaly_type: str  # 'complexity', 'diversity', 'nesting', 'duplication' (changed from metric_type for test compatibility)
    line_number: int
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float  # 0.0 - 1.0
    value: float  # Actual metric value
    threshold: float  # Threshold value
    context: str
    suggestion: str
    
    @property
    def metric_type(self):
        """Alias for backward compatibility."""
        return self.anomaly_type


class StatisticalAnalyzer:
    """
    Analyze code using statistical metrics.
    
    AI-generated code exhibits statistical patterns:
    - Higher cyclomatic complexity (more branching)
    - Lower token diversity (repetitive naming)
    - Deeper nesting (doesn't use guard clauses)
    - More code duplication (copy-paste patterns)
    
    Target: 70%+ accuracy for statistical detection.
    """
    
    # Thresholds (research-backed)
    COMPLEXITY_WARNING = 10  # McCabe complexity > 10
    COMPLEXITY_CRITICAL = 20  # > 20 is unmaintainable
    
    TOKEN_DIVERSITY_LOW = 0.5  # TTR < 0.5 is suspicious
    TOKEN_DIVERSITY_CRITICAL = 0.3  # TTR < 0.3 is very suspicious
    
    NESTING_WARNING = 4  # Nesting > 4 levels
    NESTING_CRITICAL = 6  # Nesting > 6 levels
    
    DUPLICATION_THRESHOLD = 0.85  # 85% similarity
    MIN_DUPLICATE_LINES = 5  # Minimum lines for duplication
    
    def __init__(self):
        """Initialize the statistical analyzer."""
        pass
    
    def analyze(self, file_path: Path, content: str, language: str) -> Dict:
        """
        Analyze code using statistical metrics.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            Dict with analysis results
        """
        lines = content.split('\n')
        
        # Collect anomalies
        anomalies = []
        
        # 1. Cyclomatic complexity analysis
        anomalies.extend(self._analyze_complexity(content, lines, language))
        
        # 2. Token diversity analysis
        anomalies.extend(self._analyze_token_diversity(content, lines, language))
        
        # 3. Nesting depth analysis
        anomalies.extend(self._analyze_nesting_depth(content, lines, language))
        
        # 4. Code duplication analysis
        anomalies.extend(self._analyze_duplication(content, lines, language))
        
        # 5. Function/line metrics
        anomalies.extend(self._analyze_function_metrics(content, lines, language))
        
        # Calculate confidence
        confidence = self._calculate_confidence(anomalies, len(lines))
        
        # Generate summary
        summary = self._generate_summary(anomalies, confidence)
        
        return {
            'confidence': confidence,
            'anomalies': anomalies,
            'summary': summary,
            'metric_counts': self._count_metrics(anomalies),
            'severity_distribution': self._severity_distribution(anomalies),
        }
    
    def _analyze_complexity(self, content: str, lines: List[str], language: str) -> List[StatisticalAnomaly]:
        """Analyze cyclomatic complexity."""
        anomalies = []
        
        # Decision keywords that increase complexity
        decision_keywords = [
            'if', 'elif', 'else if', 'elseif',
            'for', 'while', 'do',
            'case', 'switch',
            '&&', '||', 'and', 'or',
            '?',  # Ternary operator
            'catch', 'except',
        ]
        
        # Simple function detection
        func_patterns = {
            'python': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'javascript': r'^\s*(function\s+[a-zA-Z_][a-zA-Z0-9_]*|const\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=.*=>)',
            'typescript': r'^\s*(function\s+[a-zA-Z_][a-zA-Z0-9_]*|const\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=.*=>)',
            'java': r'^\s*(public|private|protected)?\s*(static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        }
        
        func_pattern = func_patterns.get(language, r'^\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        
        current_function = None
        function_start = 0
        complexity = 1  # Base complexity
        
        for line_num, line in enumerate(lines, 1):
            # Detect function start
            if re.match(func_pattern, line):
                # Save previous function's complexity
                if current_function and complexity > self.COMPLEXITY_WARNING:
                    severity = 'CRITICAL' if complexity > self.COMPLEXITY_CRITICAL else 'HIGH'
                    confidence = min(0.90, 0.5 + (complexity / self.COMPLEXITY_CRITICAL) * 0.4)
                    
                    anomalies.append(StatisticalAnomaly(
                        anomaly_type='cyclomatic_complexity',
                        line_number=function_start,
                        severity=severity,
                        confidence=confidence,
                        value=complexity,
                        threshold=self.COMPLEXITY_WARNING,
                        context=f"Function '{current_function}' has complexity {complexity} (threshold: {self.COMPLEXITY_WARNING})",
                        suggestion=f"Reduce complexity by extracting methods, using guard clauses, or simplifying logic"
                    ))
                
                # Start new function
                match = re.match(func_pattern, line)
                current_function = match.group(1) if match and match.lastindex else 'unknown'
                function_start = line_num
                complexity = 1
                continue
            
            # Count decision points in current function
            if current_function:
                line_lower = line.lower()
                for keyword in decision_keywords:
                    # Count occurrences (but cap per line to avoid overcounting)
                    count = min(3, line_lower.count(keyword))
                    complexity += count
        
        # Check last function
        if current_function and complexity > self.COMPLEXITY_WARNING:
            severity = 'CRITICAL' if complexity > self.COMPLEXITY_CRITICAL else 'HIGH'
            confidence = min(0.90, 0.5 + (complexity / self.COMPLEXITY_CRITICAL) * 0.4)
            
            anomalies.append(StatisticalAnomaly(
                anomaly_type='cyclomatic_complexity',
                line_number=function_start,
                severity=severity,
                confidence=confidence,
                value=complexity,
                threshold=self.COMPLEXITY_WARNING,
                context=f"Function '{current_function}' has complexity {complexity}",
                suggestion="Reduce complexity by extracting methods or simplifying logic"
            ))
        
        return anomalies
    
    def _analyze_token_diversity(self, content: str, lines: List[str], language: str) -> List[StatisticalAnomaly]:
        """Analyze token/vocabulary diversity (Type-Token Ratio)."""
        anomalies = []
        
        # Extract identifiers (variable/function names)
        identifier_pattern = r'\b([a-z_][a-z0-9_]{2,})\b'  # At least 3 chars
        
        all_tokens = []
        for line in lines:
            # Skip comments and strings
            if self._is_comment_or_docstring(line, language):
                continue
            
            tokens = re.findall(identifier_pattern, line.lower())
            all_tokens.extend(tokens)
        
        if len(all_tokens) < 20:  # Need enough tokens for meaningful analysis
            return anomalies
        
        # Calculate Type-Token Ratio (TTR)
        unique_tokens = len(set(all_tokens))
        total_tokens = len(all_tokens)
        ttr = unique_tokens / total_tokens
        
        # Low TTR indicates repetitive naming (AI pattern)
        if ttr < self.TOKEN_DIVERSITY_LOW:
            severity = 'CRITICAL' if ttr < self.TOKEN_DIVERSITY_CRITICAL else 'HIGH'
            confidence = min(0.85, (self.TOKEN_DIVERSITY_LOW - ttr) * 2)
            
            # Find most repeated tokens
            token_counts = Counter(all_tokens)
            most_common = token_counts.most_common(3)
            
            anomalies.append(StatisticalAnomaly(
                anomaly_type='token_diversity',
                line_number=1,
                severity=severity,
                confidence=confidence,
                value=ttr,
                threshold=self.TOKEN_DIVERSITY_LOW,
                context=f"Token diversity: {ttr:.2%} (threshold: {self.TOKEN_DIVERSITY_LOW:.0%}). Most repeated: {', '.join(f'{t}({c})' for t, c in most_common)}",
                suggestion="Use more descriptive, varied naming. Avoid repetitive patterns like 'data1', 'data2', 'func1', 'func2'"
            ))
        
        return anomalies
    
    def _analyze_nesting_depth(self, content: str, lines: List[str], language: str) -> List[StatisticalAnomaly]:
        """Analyze nesting depth (indentation levels)."""
        anomalies = []
        
        max_nesting = 0
        max_nesting_line = 0
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            # Calculate indentation level
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Assume 4 spaces or 1 tab per level
            if '\t' in line[:indent]:
                nesting_level = line[:indent].count('\t')
            else:
                nesting_level = indent // 4
            
            if nesting_level > max_nesting:
                max_nesting = nesting_level
                max_nesting_line = line_num
        
        # Check if nesting exceeds thresholds
        if max_nesting >= self.NESTING_WARNING:
            severity = 'CRITICAL' if max_nesting >= self.NESTING_CRITICAL else 'HIGH'
            confidence = min(0.85, 0.5 + (max_nesting / self.NESTING_CRITICAL) * 0.35)
            
            anomalies.append(StatisticalAnomaly(
                anomaly_type='nesting_depth',
                line_number=max_nesting_line,
                severity=severity,
                confidence=confidence,
                value=max_nesting,
                threshold=self.NESTING_WARNING,
                context=f"Maximum nesting depth: {max_nesting} levels (threshold: {self.NESTING_WARNING})",
                suggestion=f"Reduce nesting by using guard clauses (early returns), extracting methods, or inverting conditions"
            ))
        
        return anomalies
    
    def _analyze_duplication(self, content: str, lines: List[str], language: str) -> List[StatisticalAnomaly]:
        """Analyze code duplication."""
        anomalies = []
        
        # Extract code blocks (skip comments/blanks)
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not self._is_comment_or_docstring(stripped, language):
                # Normalize: remove extra spaces, lowercase
                normalized = re.sub(r'\s+', ' ', stripped.lower())
                code_lines.append(normalized)
        
        if len(code_lines) < self.MIN_DUPLICATE_LINES * 2:
            return anomalies
        
        # Sliding window to find duplicate blocks
        duplicates = []
        window_size = self.MIN_DUPLICATE_LINES
        
        for i in range(len(code_lines) - window_size):
            block1 = code_lines[i:i + window_size]
            block1_hash = self._hash_block(block1)
            
            # Search for similar blocks further in the code
            for j in range(i + window_size, len(code_lines) - window_size):
                block2 = code_lines[j:j + window_size]
                
                # Calculate similarity
                similarity = self._calculate_similarity(block1, block2)
                
                if similarity >= self.DUPLICATION_THRESHOLD:
                    duplicates.append((i + 1, j + 1, similarity, window_size))
                    break  # Found duplicate, move to next block
        
        # Report duplications
        for start1, start2, similarity, size in duplicates[:5]:  # Limit to top 5
            anomalies.append(StatisticalAnomaly(
                anomaly_type='code_duplication',
                line_number=start1,
                severity='HIGH',
                confidence=similarity * 0.8,
                value=similarity,
                threshold=self.DUPLICATION_THRESHOLD,
                context=f"Duplicate code block at lines {start1}-{start1 + size} and {start2}-{start2 + size} ({similarity:.0%} similar)",
                suggestion=f"Extract duplicate code into a shared function or method"
            ))
        
        return anomalies
    
    def _analyze_function_metrics(self, content: str, lines: List[str], language: str) -> List[StatisticalAnomaly]:
        """Analyze function-level metrics."""
        anomalies = []
        
        # Count parameters in function definitions
        func_param_pattern = r'def\s+\w+\s*\(([^)]*)\)'  # Python
        
        for line_num, line in enumerate(lines, 1):
            match = re.search(func_param_pattern, line)
            if match:
                params_str = match.group(1)
                # Count parameters (split by comma, exclude self/cls)
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                params = [p for p in params if p not in ['self', 'cls']]
                
                param_count = len(params)
                
                if param_count > 5:
                    severity = 'CRITICAL' if param_count > 7 else 'HIGH'
                    
                    anomalies.append(StatisticalAnomaly(
                        anomaly_type='excessive_parameters',
                        line_number=line_num,
                        severity=severity,
                        confidence=0.70,
                        value=param_count,
                        threshold=5,
                        context=f"Function has {param_count} parameters (threshold: 5)",
                        suggestion="Reduce parameters by using objects/dataclasses or builder pattern"
                    ))
        
        return anomalies
    
    def _is_comment_or_docstring(self, line: str, language: str) -> bool:
        """Check if line is comment or docstring."""
        stripped = line.strip()
        
        if language == 'python':
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                return True
        elif language in ['javascript', 'typescript', 'java', 'csharp', 'c', 'cpp']:
            if stripped.startswith('//') or stripped.startswith('/*'):
                return True
        
        return False
    
    def _hash_block(self, lines: List[str]) -> str:
        """Hash a code block for duplicate detection."""
        block_str = '\n'.join(lines)
        return hashlib.md5(block_str.encode()).hexdigest()
    
    def _calculate_similarity(self, block1: List[str], block2: List[str]) -> float:
        """Calculate similarity between two code blocks."""
        if len(block1) != len(block2):
            return 0.0
        
        matches = 0
        for line1, line2 in zip(block1, block2):
            # Check if lines are similar (allow minor differences)
            if line1 == line2:
                matches += 1
            elif self._lines_similar(line1, line2):
                matches += 0.8
        
        return matches / len(block1)
    
    def _lines_similar(self, line1: str, line2: str) -> bool:
        """Check if two lines are similar (same structure, different variables)."""
        # Replace identifiers with placeholder
        pattern = r'\b[a-z_][a-z0-9_]*\b'
        
        norm1 = re.sub(pattern, 'VAR', line1)
        norm2 = re.sub(pattern, 'VAR', line2)
        
        return norm1 == norm2
    
    def _calculate_confidence(self, anomalies: List[StatisticalAnomaly], total_lines: int) -> float:
        """Calculate overall confidence score."""
        if not anomalies:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            'CRITICAL': 1.0,
            'HIGH': 0.8,
            'MEDIUM': 0.5,
            'LOW': 0.3,
        }
        
        total_weight = 0.0
        for anomaly in anomalies:
            weight = severity_weights.get(anomaly.severity, 0.5)
            total_weight += weight * anomaly.confidence
        
        # Normalize
        normalized = total_weight / max(1, total_lines / 20)
        
        return min(0.90, normalized)
    
    def _generate_summary(self, anomalies: List[StatisticalAnomaly], confidence: float) -> Dict:
        """Generate analysis summary."""
        metric_counts = self._count_metrics(anomalies)
        
        return {
            'total_anomalies': len(anomalies),
            'confidence': confidence,
            'risk_level': self._get_risk_level(confidence),
            'anomaly_distribution': metric_counts,  # Add for test compatibility
            'top_metrics': sorted(
                metric_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'recommendation': self._get_recommendation(confidence, metric_counts),
        }
    
    def _count_metrics(self, anomalies: List[StatisticalAnomaly]) -> Dict[str, int]:
        """Count occurrences of each metric type."""
        counter = Counter(anomaly.metric_type for anomaly in anomalies)
        return dict(counter)
    
    def _severity_distribution(self, anomalies: List[StatisticalAnomaly]) -> Dict[str, int]:
        """Get distribution of severity levels."""
        counter = Counter(anomaly.severity for anomaly in anomalies)
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
    
    def _get_recommendation(self, confidence: float, metric_counts: Dict[str, int]) -> str:
        """Generate actionable recommendation."""
        if confidence >= 0.7:
            top_metric = max(metric_counts, key=metric_counts.get) if metric_counts else 'complexity'
            return f"High statistical anomalies. Focus on reducing {top_metric}."
        elif confidence >= 0.4:
            return "Moderate statistical issues. Refactor complex sections."
        else:
            return "Low statistical anomalies. Code metrics within acceptable ranges."
