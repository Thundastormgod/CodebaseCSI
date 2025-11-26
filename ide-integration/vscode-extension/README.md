# VS Code Extension for Codebase CSI

Real-time AI code detection integrated into Visual Studio Code.

## Features

- 🔍 **Real-time Detection** - Scan files as you type (optional)
- 🎯 **Inline Warnings** - See AI patterns directly in your code
- 📊 **Detailed Reports** - Interactive HTML reports with charts
- 🔧 **Auto-Fix** - Automatically fix simple issues (emoji removal, etc.)
- 🌳 **Results Panel** - Tree view of all detected files
- ⚡ **Fast Scanning** - Only scans when needed

## Installation

### Prerequisites

1. Install Python 3.8+ and Codebase CSI:
```bash
pip install codebase-csi
```

2. Verify installation:
```bash
csi --version
```

### Install Extension

#### From VSIX (Recommended)
```bash
code --install-extension codebase-csi-1.0.0.vsix
```

#### From Source
```bash
cd ide-integration/vscode-extension
npm install
npm run compile
code --install-extension .
```

## Usage

### Commands

Access via Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`):

- **CSI: Scan Current File** - Analyze the active file
- **CSI: Scan Entire Workspace** - Scan all files in workspace
- **CSI: Explain Detection** - Show detailed explanation
- **CSI: Auto-Fix Issues** - Automatically fix simple problems
- **CSI: Toggle Real-Time Detection** - Enable/disable real-time scanning
- **CSI: Show Detailed Report** - Open interactive HTML report

### Context Menu

Right-click in editor:
- Scan Current File
- Explain Detection
- Auto-Fix Issues

### Automatic Scanning

The extension automatically scans files:
- When file is opened
- When file is saved
- When you type (if real-time mode enabled)

## Configuration

Access settings via `File > Preferences > Settings` > Search "Codebase CSI"

### Available Settings

```json
{
  "codebase-csi.enabled": true,
  "codebase-csi.realTimeDetection": false,
  "codebase-csi.confidenceThreshold": 0.4,
  "codebase-csi.pythonPath": "python",
  "codebase-csi.showInlineWarnings": true,
  "codebase-csi.analyzers": [
    "emoji",
    "pattern",
    "statistical",
    "security",
    "semantic",
    "architectural"
  ],
  "codebase-csi.excludePatterns": [
    "**/node_modules/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/.git/**"
  ],
  "codebase-csi.autoFixOnSave": false
}
```

### Settings Explained

- **enabled**: Enable/disable the extension
- **realTimeDetection**: Scan as you type (may impact performance)
- **confidenceThreshold**: Minimum confidence to flag code (0.0-1.0)
- **pythonPath**: Path to Python executable with codebase-csi installed
- **showInlineWarnings**: Show warnings directly in editor
- **analyzers**: Which analyzers to enable
- **excludePatterns**: File patterns to exclude from scanning
- **autoFixOnSave**: Automatically fix issues when saving

## Results Panel

The extension adds a "Codebase CSI Results" panel to the Explorer sidebar:

- 🔴 **Red (High Risk)**: 70%+ AI confidence
- 🟡 **Yellow (Medium Risk)**: 40-70% confidence  
- 🟢 **Green (Low Risk)**: Below 40% confidence

Click any file to open it.

## Status Bar

The status bar shows current scan status:

- `$(search) CSI` - Idle (click to scan)
- `$(sync~spin) CSI Scanning...` - Scanning in progress
- `$(error) CSI: 85%` - High risk detected
- `$(warning) CSI: 55%` - Medium risk detected
- `$(check) CSI: 20%` - Low risk, looks good

## Quick Fixes

When AI patterns are detected, use Quick Fix (`Ctrl+.` / `Cmd+.`):

- Remove emoji
- Suggest better name
- Scan entire file
- Explain detection

## Performance Tips

1. **Disable real-time detection** for large files
2. **Exclude large directories** (node_modules, venv)
3. **Increase threshold** to reduce noise
4. **Disable specific analyzers** if not needed

## Troubleshooting

### Extension not working

1. Verify Python and codebase-csi installation:
```bash
python -m codebase_csi --version
```

2. Check Python path in settings
3. Look at Output panel: View > Output > Select "Codebase CSI"

### Scans are slow

1. Disable real-time detection
2. Add more patterns to excludePatterns
3. Reduce enabled analyzers
4. Increase confidence threshold

### False positives

1. Increase confidence threshold
2. Disable specific analyzers
3. Report false positives at: https://github.com/Thundastormgod/CodebaseCSI/issues

## Development

### Build from Source

```bash
cd ide-integration/vscode-extension
npm install
npm run compile
```

### Package Extension

```bash
npm run package
```

This creates `codebase-csi-1.0.0.vsix`.

### Publish to Marketplace

```bash
npm run publish
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../../docs/official/CONTRIBUTING.md)

## License

MIT - See [LICENSE](../../LICENSE)

## Links

- [GitHub Repository](https://github.com/Thundastormgod/CodebaseCSI)
- [Issue Tracker](https://github.com/Thundastormgod/CodebaseCSI/issues)
- [Documentation](https://github.com/Thundastormgod/CodebaseCSI#readme)
