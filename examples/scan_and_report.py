"""
Full Codebase Scan with JSON Report Generation
Scans the codebase and generates a comprehensive JSON report.
"""
import time
from pathlib import Path
from datetime import datetime
from codebase_csi.analyzers import (
    PatternAnalyzer,
    StatisticalAnalyzer,
    SecurityAnalyzer,
    EmojiDetector,
    SemanticAnalyzer,
    ArchitecturalAnalyzer,
    CommentAnalyzer,
    AntipatternAnalyzer,
)
from codebase_csi.core.report_generator import ReportGenerator


def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cs': 'csharp',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
    }
    return ext_map.get(file_path.suffix.lower(), 'unknown')


def scan_codebase(codebase_path: Path) -> dict:
    """
    Scan a codebase with all analyzers and collect results.
    
    Args:
        codebase_path: Path to the codebase directory
        
    Returns:
        Dictionary with scan results ready for report generation
    """
    print(f"🔍 Starting scan of: {codebase_path}")
    start_time = time.time()
    
    # Initialize analyzers
    analyzers = {
        'Pattern': PatternAnalyzer(),
        'Statistical': StatisticalAnalyzer(),
        'Security': SecurityAnalyzer(),
        'Emoji': EmojiDetector(),
        'Architectural': ArchitecturalAnalyzer(),
        'Comment': CommentAnalyzer(),
        'Antipattern': AntipatternAnalyzer(),
    }
    
    # Find all source files
    extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
    source_files = []
    for ext in extensions:
        source_files.extend(codebase_path.rglob(f'*{ext}'))
    
    # Filter out common non-source directories
    exclude_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env', 'dist', 'build', '.tox'}
    source_files = [f for f in source_files if not any(d in f.parts for d in exclude_dirs)]
    
    print(f"📁 Found {len(source_files)} source files")
    
    # Scan each file
    results = {
        'codebase_path': str(codebase_path.absolute()),
        'files': {},
    }
    
    for i, file_path in enumerate(source_files, 1):
        relative_path = str(file_path.relative_to(codebase_path))
        print(f"  [{i}/{len(source_files)}] Scanning: {relative_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            language = detect_language(file_path)
            
            file_results = {
                'language': language,
                'lines_of_code': len(lines),
                'results': {},
            }
            
            # Run each analyzer
            for name, analyzer in analyzers.items():
                try:
                    if name == 'Emoji':
                        result = analyzer.analyze(file_path, content, lines, language)
                    else:
                        result = analyzer.analyze(file_path, content, language)
                    
                    file_results['results'][name] = {
                        'confidence': result.get('confidence', 0),
                        'patterns': result.get('patterns', result.get('anomalies', 
                                   result.get('vulnerabilities', result.get('antipatterns',
                                   result.get('issues', []))))),
                    }
                except Exception as e:
                    file_results['results'][name] = {'error': str(e)[:100]}
            
            results['files'][relative_path] = file_results
            
        except Exception as e:
            print(f"    ⚠️ Error reading file: {e}")
            results['files'][relative_path] = {'error': str(e)[:100]}
    
    # Calculate duration
    results['duration'] = time.time() - start_time
    print(f"\n✅ Scan complete in {results['duration']:.2f} seconds")
    
    return results


def main():
    """Main entry point for scan and report generation."""
    # Define codebase to scan
    codebase_path = Path('src/codebase_csi')
    
    # Run the scan
    scan_results = scan_codebase(codebase_path)
    
    # Generate JSON report
    print("\n📄 Generating JSON report...")
    generator = ReportGenerator()
    
    json_report = generator.generate_report(
        scan_results,
        output_path=Path('codebase_analysis_report.json')
    )
    print(f"  ✅ JSON report: codebase_analysis_report.json")
    
    print("\n🎉 Report generated successfully!")


if __name__ == '__main__':
    main()
