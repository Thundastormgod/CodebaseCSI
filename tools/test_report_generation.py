from pathlib import Path
from src.codebase_csi.core.report_generator import ReportGenerator

# Build mock scan results pointing at this repo file for demonstration
repo_root = Path(__file__).resolve().parents[1]
file_path = str(repo_root / 'src' / 'codebase_csi' / 'core' / 'report_generator.py')

mock_scan = {
    'codebase_path': str(repo_root),
    'duration': 0.12,
    'files': {
        file_path: {
            'language': 'python',
            'lines_of_code': 300,
            'results': {
                'Pattern': {
                    'confidence': 0.9,
                    'patterns': [
                        {
                            'type': 'generic_naming',
                            'line': 120,
                            'message': "Variable 'temp' is generic",
                            'suggestion': "Use descriptive name 'item_value'"
                        }
                    ]
                },
                'Security': {
                    'confidence': 0.2,
                    'vulnerabilities': []
                }
            }
        }
    }
}

rg = ReportGenerator()
output = rg.generate_report(mock_scan)
print(output)
