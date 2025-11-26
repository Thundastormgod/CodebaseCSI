"""
Emoji Detection Analyzer
Detects emoji usage in source code - a strong indicator of AI-generated code.

Professional production codebases rarely use emojis. Their presence suggests:
1. AI training on casual content (forums, tutorials)
2. ChatGPT/Claude default "friendly" style
3. Violation of enterprise coding standards
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class EmojiMatch:
    """Represents a detected emoji."""
    emoji: str
    line_number: int
    column: int
    unicode_code: str
    context: str  # 'comment', 'docstring', 'string', 'code'


class EmojiDetector:
    """
    Detect emojis in source code.
    
    Emojis are a strong indicator of AI-generated code because:
    - Professional code rarely uses them
    - AI models default to "friendly" emoji usage
    - Enterprise coding standards prohibit them
    - They cause encoding/terminal issues
    """
    
    # Unicode ranges for emojis
    EMOJI_RANGES = [
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F300, 0x1F5FF),  # Symbols & Pictographs
        (0x1F680, 0x1F6FF),  # Transport & Map Symbols
        (0x1F1E0, 0x1F1FF),  # Flags (iOS)
        (0x2702, 0x27B0),    # Dingbats
        (0x24C2, 0x1F251),   # Enclosed characters
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x2600, 0x26FF),    # Miscellaneous Symbols
        (0x2700, 0x27BF),    # Dingbats
    ]
    
    # Common AI emoji patterns with confidence weights
    AI_EMOJI_PATTERNS = {
        # Task/Status markers (very common in AI code)
        '✅': {'weight': 0.9, 'category': 'task_marker', 'description': 'Check mark'},
        '❌': {'weight': 0.9, 'category': 'task_marker', 'description': 'Cross mark'},
        '⚠️': {'weight': 0.5, 'category': 'warning', 'description': 'Warning'},
        
        # Operation indicators (AI loves these)
        '🔄': {'weight': 0.9, 'category': 'operation', 'description': 'Loop/refresh'},
        '➕': {'weight': 0.8, 'category': 'operation', 'description': 'Addition'},
        '➖': {'weight': 0.8, 'category': 'operation', 'description': 'Subtraction'},
        '✖️': {'weight': 0.8, 'category': 'operation', 'description': 'Multiplication'},
        '➗': {'weight': 0.8, 'category': 'operation', 'description': 'Division'},
        
        # Business/Finance (common in payment code)
        '💰': {'weight': 0.9, 'category': 'finance', 'description': 'Money bag'},
        '💵': {'weight': 0.9, 'category': 'finance', 'description': 'Dollar'},
        '💳': {'weight': 0.9, 'category': 'finance', 'description': 'Credit card'},
        
        # Documentation markers
        '📝': {'weight': 0.8, 'category': 'docs', 'description': 'Memo'},
        '📄': {'weight': 0.8, 'category': 'docs', 'description': 'Page'},
        '📊': {'weight': 0.8, 'category': 'docs', 'description': 'Chart'},
        
        # "Cool feature" markers (AI enthusiasm)
        '🚀': {'weight': 1.0, 'category': 'enthusiasm', 'description': 'Rocket'},
        '⚡': {'weight': 0.9, 'category': 'enthusiasm', 'description': 'Lightning'},
        '🔥': {'weight': 1.0, 'category': 'enthusiasm', 'description': 'Fire'},
        '✨': {'weight': 0.9, 'category': 'enthusiasm', 'description': 'Sparkles'},
        
        # Bug/Issue markers
        '🐛': {'weight': 0.7, 'category': 'bug', 'description': 'Bug'},
        '🪲': {'weight': 0.7, 'category': 'bug', 'description': 'Beetle'},
        
        # Achievement markers
        '🎯': {'weight': 0.9, 'category': 'achievement', 'description': 'Target'},
        '🎉': {'weight': 0.9, 'category': 'achievement', 'description': 'Party'},
        '🏆': {'weight': 0.9, 'category': 'achievement', 'description': 'Trophy'},
        
        # Security/Lock
        '🔒': {'weight': 0.8, 'category': 'security', 'description': 'Lock'},
        '🔓': {'weight': 0.8, 'category': 'security', 'description': 'Unlock'},
        '🔐': {'weight': 0.8, 'category': 'security', 'description': 'Locked'},
    }
    
    def __init__(self):
        """Initialize emoji detector."""
        # Build emoji regex pattern
        patterns = []
        for start, end in self.EMOJI_RANGES:
            patterns.append(f'[\\U{start:08X}-\\U{end:08X}]')
        
        self.emoji_regex = re.compile('|'.join(patterns))
        
        # Comment patterns for different languages
        self.comment_patterns = {
            'line_comment': re.compile(r'^\s*(#|//|--|;)'),
            'block_comment_start': re.compile(r'/\*|\(\*|<!--'),
            'docstring': re.compile(r'^\s*("""|\'\'\'|###)')
        }
    
    def detect_emojis_in_line(self, line: str, line_number: int) -> List[EmojiMatch]:
        """
        Detect all emojis in a single line.
        
        Args:
            line: Line of code to analyze
            line_number: Line number in file
            
        Returns:
            List of EmojiMatch objects
        """
        matches = []
        
        for match in self.emoji_regex.finditer(line):
            emoji = match.group()
            context = self._detect_context(line, match.start())
            
            matches.append(EmojiMatch(
                emoji=emoji,
                line_number=line_number,
                column=match.start(),
                unicode_code=f'U+{ord(emoji):04X}',
                context=context
            ))
        
        return matches
    
    def analyze(self, file_path: Path, content: str, lines: List[str]) -> Dict:
        """
        Analyze file for emoji usage.
        
        Args:
            file_path: Path to file
            content: Full file content
            lines: List of lines
            
        Returns:
            Detection result dictionary
        """
        all_emojis = []
        emoji_lines = []
        context_counts = {
            'comment': 0,
            'docstring': 0,
            'string': 0,
            'code': 0  # Worst case!
        }
        
        in_block_comment = False
        in_docstring = False
        
        for line_num, line in enumerate(lines, 1):
            # Track block comment state
            if self.comment_patterns['block_comment_start'].search(line):
                in_block_comment = True
            if '*/' in line or '-->' in line:
                in_block_comment = False
            
            # Track docstring state
            if self.comment_patterns['docstring'].search(line):
                in_docstring = not in_docstring
            
            # Detect emojis in line
            emojis = self.detect_emojis_in_line(line, line_num)
            
            if emojis:
                all_emojis.extend(emojis)
                emoji_lines.append({
                    'line': line_num,
                    'content': line.strip()[:100],
                    'emojis': [e.emoji for e in emojis],
                    'count': len(emojis)
                })
                
                # Count by context
                for emoji in emojis:
                    context_counts[emoji.context] += 1
        
        # Calculate confidence and severity
        total_emojis = len(all_emojis)
        confidence = self._calculate_confidence(
            total_emojis, 
            len(lines), 
            context_counts
        )
        severity = self._get_severity(total_emojis, len(lines), context_counts)
        
        # Analyze emoji categories
        category_analysis = self._analyze_categories(all_emojis)
        
        return {
            'phase': 'emoji_detection',
            'confidence': confidence,
            'indicators': self._build_indicators(emoji_lines, all_emojis),
            'metrics': {
                'total_emojis': total_emojis,
                'emoji_lines': len(emoji_lines),
                'total_lines': len(lines),
                'emoji_density': total_emojis / max(len(lines), 1),
                'context_distribution': context_counts,
                'category_distribution': category_analysis
            },
            'notes': f"Found {total_emojis} emojis across {len(emoji_lines)} lines",
            'severity': severity,
            'patterns': self._extract_patterns(all_emojis)
        }
    
    def _detect_context(self, line: str, position: int) -> str:
        """
        Detect context where emoji appears.
        
        Args:
            line: Line containing emoji
            position: Position of emoji in line
            
        Returns:
            Context type: 'comment', 'docstring', 'string', 'code'
        """
        # Check if in comment (most common case)
        if self.comment_patterns['line_comment'].match(line):
            return 'comment'
        
        # Check if in docstring (triple quotes)
        if '"""' in line or "'''" in line:
            # More sophisticated check - ensure emoji is actually inside docstring
            before_emoji = line[:position]
            triple_double = before_emoji.count('"""')
            triple_single = before_emoji.count("'''")
            if triple_double % 2 == 1 or triple_single % 2 == 1:
                return 'docstring'
        
        # Check if in string literal - improved detection
        before_emoji = line[:position]
        
        # Count unescaped quotes before emoji position
        double_quotes = 0
        single_quotes = 0
        i = 0
        while i < len(before_emoji):
            if i > 0 and before_emoji[i-1] == '\\':
                # Skip escaped character (but handle \\ properly)
                escaped_count = 1
                j = i - 2
                while j >= 0 and before_emoji[j] == '\\':
                    escaped_count += 1
                    j -= 1
                # If even number of backslashes, the quote is NOT escaped
                if escaped_count % 2 == 0:
                    if before_emoji[i] == '"':
                        double_quotes += 1
                    elif before_emoji[i] == "'":
                        single_quotes += 1
                i += 1
                continue
            
            if before_emoji[i] == '"':
                double_quotes += 1
            elif before_emoji[i] == "'":
                single_quotes += 1
            i += 1
        
        # If odd number of quotes, we're inside a string
        if double_quotes % 2 == 1 or single_quotes % 2 == 1:
            return 'string'
        
        # Check for f-strings
        if before_emoji.rstrip().endswith(('f"', "f'", 'F"', "F'")):
            return 'string'
        
        # Default: in actual code (WORST CASE!)
        return 'code'
    
    def _calculate_confidence(
        self, 
        emoji_count: int, 
        line_count: int,
        context_counts: Dict[str, int]
    ) -> float:
        """
        Calculate confidence that code is AI-generated based on emoji usage.
        
        Args:
            emoji_count: Total emojis found
            line_count: Total lines in file
            context_counts: Where emojis appear
            
        Returns:
            Confidence score 0.0-1.0
        """
        if emoji_count == 0:
            return 0.0
        
        # Base confidence from emoji density (more conservative)
        density = emoji_count / max(line_count, 1)
        base_confidence = min(density * 20, 0.3)  # Up to 0.3 from density
        
        # Boost for emojis in actual code (extremely suspicious!)
        if context_counts['code'] > 0:
            base_confidence += 0.5  # Major boost for code context
        
        # Small boost for emojis in comments (mildly suspicious)
        if context_counts['comment'] > 0:
            base_confidence += 0.05
        
        # Boost for very high emoji count (strong AI signal)
        if emoji_count > 8:
            base_confidence += 0.15
        elif emoji_count > 4:
            base_confidence += 0.10
        
        return min(base_confidence, 1.0)
    
    def _get_severity(
        self, 
        emoji_count: int, 
        line_count: int,
        context_counts: Dict[str, int]
    ) -> str:
        """
        Determine severity based on emoji usage.
        
        Args:
            emoji_count: Total emojis found
            line_count: Total lines in file
            context_counts: Where emojis appear
            
        Returns:
            Severity level
        """
        if emoji_count == 0:
            return 'NONE'
        
        # Emojis in actual code = CRITICAL (highest severity)
        if context_counts['code'] > 0:
            return 'CRITICAL'
        
        # Calculate density
        density = emoji_count / max(line_count, 1)
        
        # More reasonable thresholds for comments/docstrings/strings
        # (Professional code might have occasional emoji in comments)
        if density > 0.20:  # >20% of lines have emojis
            return 'CRITICAL'
        elif density > 0.10 or emoji_count > 10:  # >10% or many emojis
            return 'HIGH'
        elif density > 0.05 or emoji_count > 5:  # >5% or several emojis
            return 'MEDIUM'
        elif emoji_count > 0:
            return 'LOW'
        else:
            return 'NONE'
    
    def _analyze_categories(self, emojis: List[EmojiMatch]) -> Dict[str, int]:
        """
        Analyze emoji categories found.
        
        Args:
            emojis: List of emoji matches
            
        Returns:
            Dictionary of category counts
        """
        categories = {}
        
        for emoji_match in emojis:
            emoji = emoji_match.emoji
            if emoji in self.AI_EMOJI_PATTERNS:
                category = self.AI_EMOJI_PATTERNS[emoji]['category']
                categories[category] = categories.get(category, 0) + 1
            else:
                categories['other'] = categories.get('other', 0) + 1
        
        return categories
    
    def _build_indicators(
        self, 
        emoji_lines: List[Dict],
        all_emojis: List[EmojiMatch]
    ) -> List[Dict]:
        """
        Build indicator list for detection result.
        
        Args:
            emoji_lines: Lines containing emojis
            all_emojis: All emoji matches
            
        Returns:
            List of indicator dictionaries
        """
        indicators = []
        
        for emoji_line in emoji_lines:
            # Determine severity for this line
            emoji_count = emoji_line['count']
            if emoji_count > 3:
                severity = 'HIGH'
            elif emoji_count > 1:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            
            indicators.append({
                'line': emoji_line['line'],
                'type': 'EMOJI_USAGE',
                'severity': severity,
                'content': emoji_line['content'],
                'emojis': emoji_line['emojis'],
                'count': emoji_count,  # Add count field for tests
                'weight': min(emoji_count * 2, 10)
            })
        
        return indicators
    
    def _extract_patterns(self, emojis: List[EmojiMatch]) -> List[Dict]:
        """
        Extract detection patterns from emoji matches.
        
        Args:
            emojis: List of emoji matches
            
        Returns:
            List of detection patterns
        """
        patterns = []
        
        for emoji_match in emojis:
            emoji = emoji_match.emoji
            
            # Get pattern info if known
            if emoji in self.AI_EMOJI_PATTERNS:
                pattern_info = self.AI_EMOJI_PATTERNS[emoji]
                weight = pattern_info['weight']
                category = pattern_info['category']
                description = pattern_info['description']
            else:
                weight = 0.5
                category = 'unknown'
                description = 'Unknown emoji'
            
            patterns.append({
                'type': 'emoji',
                'emoji': emoji,
                'unicode': emoji_match.unicode_code,
                'line': emoji_match.line_number,
                'column': emoji_match.column,
                'context': emoji_match.context,
                'category': category,
                'description': description,
                'confidence': weight,
                'remediation': f"Remove emoji '{emoji}' ({description})"
            })
        
        return patterns


def detect_emojis(file_path: Path, content: str, lines: List[str]) -> Dict:
    """
    Convenience function to detect emojis in a file.
    
    Args:
        file_path: Path to file
        content: File content
        lines: Lines of file
        
    Returns:
        Detection result
    """
    detector = EmojiDetector()
    return detector.analyze(file_path, content, lines)
