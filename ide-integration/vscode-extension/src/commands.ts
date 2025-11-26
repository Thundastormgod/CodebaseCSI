/**
 * Command implementations for VS Code extension
 */

import * as vscode from 'vscode';
import { spawn } from 'child_process';
import { CSIDiagnosticsProvider } from './diagnostics';
import { CSIStatusBar } from './statusBar';
import { CSITreeDataProvider } from './treeView';

interface ScanResult {
    confidence: number;
    patterns: Pattern[];
    language: string;
    lines_of_code: number;
}

interface Pattern {
    type: string;
    line: number;
    severity: string;
    confidence: number;
    context: string;
    remediation: string;
}

/**
 * Execute Python CLI command and parse JSON output
 */
async function executePythonCommand(args: string[]): Promise<any> {
    const config = vscode.workspace.getConfiguration('codebase-csi');
    const pythonPath = config.get('pythonPath', 'python');

    return new Promise((resolve, reject) => {
        const process = spawn(pythonPath, ['-m', 'codebase_csi.cli.main', ...args]);
        
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        process.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        process.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (e) {
                    reject(new Error(`Failed to parse output: ${stdout}`));
                }
            } else {
                reject(new Error(`Process exited with code ${code}: ${stderr}`));
            }
        });
    });
}

/**
 * Scan a single file
 */
export async function scanFile(
    document: vscode.TextDocument,
    diagnosticsProvider: CSIDiagnosticsProvider,
    statusBar: CSIStatusBar,
    treeDataProvider: CSITreeDataProvider,
    silent: boolean = false
): Promise<void> {
    if (!silent) {
        statusBar.setScanning(document.fileName);
    }

    try {
        const config = vscode.workspace.getConfiguration('codebase-csi');
        const threshold = config.get('confidenceThreshold', 0.4);
        const analyzers = config.get('analyzers', []);

        // Execute scan
        const result: ScanResult = await executePythonCommand([
            'scan',
            document.uri.fsPath,
            '--format', 'json',
            '--threshold', threshold.toString(),
            '--analyzers', ...analyzers
        ]);

        // Update diagnostics
        diagnosticsProvider.updateDiagnostics(document.uri, result);

        // Update tree view
        treeDataProvider.addResult({
            file: document.fileName,
            confidence: result.confidence,
            patterns: result.patterns.length
        });

        // Update status bar
        statusBar.setResult(result.confidence);

        if (!silent && result.confidence >= threshold) {
            const level = result.confidence >= 0.7 ? 'High' : result.confidence >= 0.4 ? 'Medium' : 'Low';
            vscode.window.showWarningMessage(
                `${level} AI confidence detected: ${(result.confidence * 100).toFixed(1)}%`,
                'Explain',
                'Auto-Fix'
            ).then(selection => {
                if (selection === 'Explain') {
                    vscode.commands.executeCommand('codebase-csi.explainDetection');
                } else if (selection === 'Auto-Fix') {
                    vscode.commands.executeCommand('codebase-csi.autoFix');
                }
            });
        }
    } catch (error) {
        if (!silent) {
            vscode.window.showErrorMessage(`Scan failed: ${error}`);
        }
        statusBar.setIdle();
    }
}

/**
 * Scan entire workspace
 */
export async function scanWorkspace(
    diagnosticsProvider: CSIDiagnosticsProvider,
    statusBar: CSIStatusBar,
    treeDataProvider: CSITreeDataProvider
): Promise<void> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showWarningMessage('No workspace folder open');
        return;
    }

    statusBar.setScanning('workspace');

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Scanning workspace with Codebase CSI',
        cancellable: true
    }, async (progress, token) => {
        try {
            const config = vscode.workspace.getConfiguration('codebase-csi');
            const threshold = config.get('confidenceThreshold', 0.4);
            const excludePatterns = config.get('excludePatterns', []);

            progress.report({ increment: 10, message: 'Finding files...' });

            const result = await executePythonCommand([
                'scan',
                workspaceFolder.uri.fsPath,
                '--format', 'json',
                '--threshold', threshold.toString(),
                '--exclude', ...excludePatterns
            ]);

            progress.report({ increment: 90, message: 'Processing results...' });

            // Update tree view with all results
            treeDataProvider.clear();
            for (const fileResult of result.file_analyses || []) {
                treeDataProvider.addResult({
                    file: fileResult.file_path,
                    confidence: fileResult.confidence_score,
                    patterns: fileResult.pattern_count
                });
            }

            statusBar.setIdle();

            const totalFiles = result.scanned_files || 0;
            const aiFiles = result.ai_file_count || 0;
            
            vscode.window.showInformationMessage(
                `Scan complete: ${aiFiles}/${totalFiles} files flagged`,
                'Show Report'
            ).then(selection => {
                if (selection === 'Show Report') {
                    vscode.commands.executeCommand('codebase-csi.showReport');
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Workspace scan failed: ${error}`);
            statusBar.setIdle();
        }
    });
}

/**
 * Show detailed explanation for detection
 */
export async function explainDetection(
    document: vscode.TextDocument,
    diagnosticsProvider: CSIDiagnosticsProvider
): Promise<void> {
    const diagnostics = diagnosticsProvider.getDiagnostics(document.uri);
    
    if (!diagnostics || diagnostics.length === 0) {
        vscode.window.showInformationMessage('No detections found in this file');
        return;
    }

    const panel = vscode.window.createWebviewPanel(
        'csiExplanation',
        `CSI Explanation: ${document.fileName}`,
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );

    panel.webview.html = generateExplanationHTML(document, diagnostics ? Array.from(diagnostics) : []);
}

function generateExplanationHTML(document: vscode.TextDocument, diagnostics: vscode.Diagnostic[]): string {
    const groupedByType = diagnostics.reduce((acc, d) => {
        const type = d.code?.toString() || 'unknown';
        if (!acc[type]) {
            acc[type] = [];
        }
        acc[type].push(d);
        return acc;
    }, {} as Record<string, vscode.Diagnostic[]>);

    return `
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: var(--vscode-font-family);
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
                padding: 20px;
            }
            .pattern-group {
                margin-bottom: 30px;
                padding: 15px;
                background-color: var(--vscode-editor-inactiveSelectionBackground);
                border-radius: 8px;
            }
            .pattern-type {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .issue {
                margin: 10px 0;
                padding: 10px;
                background-color: var(--vscode-editor-background);
                border-left: 3px solid var(--vscode-editorWarning-foreground);
                border-radius: 4px;
            }
            .line-number {
                color: var(--vscode-editorLineNumber-foreground);
                font-weight: bold;
            }
            .recommendation {
                margin-top: 20px;
                padding: 15px;
                background-color: var(--vscode-editor-inactiveSelectionBackground);
                border-left: 3px solid var(--vscode-editorInfo-foreground);
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>🔍 Detection Explanation</h1>
        <p><strong>File:</strong> ${document.fileName}</p>
        
        ${Object.entries(groupedByType).map(([type, issues]) => `
            <div class="pattern-group">
                <div class="pattern-type">${type.replace(/_/g, ' ').toUpperCase()}</div>
                <p>Found ${issues.length} occurrence(s)</p>
                ${issues.slice(0, 5).map(issue => `
                    <div class="issue">
                        <div><span class="line-number">Line ${issue.range.start.line + 1}:</span> ${issue.message}</div>
                    </div>
                `).join('')}
            </div>
        `).join('')}
        
        <div class="recommendation">
            <h2>💡 Recommendations</h2>
            <ul>
                <li>Review the flagged sections carefully</li>
                <li>Consider refactoring to follow best practices</li>
                <li>Use the Auto-Fix command for quick remediation</li>
                <li>Document any intentional AI assistance used</li>
            </ul>
        </div>
    </body>
    </html>
    `;
}

/**
 * Auto-fix issues in file
 */
export async function autoFixIssues(
    document: vscode.TextDocument,
    diagnosticsProvider: CSIDiagnosticsProvider
): Promise<void> {
    const edit = new vscode.WorkspaceEdit();
    
    // Get Python to perform fixes
    try {
        const result = await executePythonCommand([
            'fix',
            document.uri.fsPath,
            '--dry-run', 'false'
        ]);

        await vscode.workspace.applyEdit(edit);
        
        vscode.window.showInformationMessage(
            `Fixed ${result.fixes_applied} issues`,
            'Rescan'
        ).then(selection => {
            if (selection === 'Rescan') {
                vscode.commands.executeCommand('codebase-csi.scanFile');
            }
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Auto-fix failed: ${error}`);
    }
}
