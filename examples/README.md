# Examples

This directory contains example scripts demonstrating how to use CodebaseCSI programmatically.

## Scripts

### `scan_and_report.py`

A complete example showing how to:
- Scan a codebase with all 8 analyzers
- Generate a JSON report with findings
- Process and display results

**Usage:**
```bash
cd examples
python scan_and_report.py
```

**Output:**
- `codebase_analysis_report.json` - Detailed analysis report

## Using the CLI Instead

For production use, prefer the built-in CLI:

```bash
# Install the package
pip install -e .

# Scan a directory
codebase-csi scan /path/to/project

# Generate JSON report
codebase-csi scan /path/to/project --format json --output report.json

# CI/CD mode
codebase-csi cicd /path/to/project --max-confidence 0.6
```

## Programmatic Usage

```python
from codebase_csi import AICodeDetector
from codebase_csi.analyzers import (
    PatternAnalyzer,
    StatisticalAnalyzer,
    SecurityAnalyzer,
    AntipatternAnalyzer,
)
from codebase_csi.core import ReportGenerator

# Initialize detector
detector = AICodeDetector()

# Analyze a file
result = detector.analyze_file("path/to/file.py")
print(f"AI Confidence: {result.confidence:.1%}")

# Generate report
generator = ReportGenerator()
report = generator.generate_report(scan_results)
```
