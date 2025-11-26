/**
 * Codebase CSI - VS Code Extension
 * Real-time AI code detection integrated into your editor
 */

import * as vscode from 'vscode';
import { CSICodeActionProvider } from './codeActions';
import { CSIDiagnosticsProvider } from './diagnostics';
import { CSITreeDataProvider } from './treeView';
import { CSIStatusBar } from './statusBar';
import { scanFile, scanWorkspace, explainDetection, autoFixIssues } from './commands';

let diagnosticCollection: vscode.DiagnosticCollection;
let diagnosticsProvider: CSIDiagnosticsProvider;
let statusBar: CSIStatusBar;
let realTimeEnabled = false;

export function activate(context: vscode.ExtensionContext) {
    console.log('Codebase CSI extension is now active');

    // Create diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('codebase-csi');
    context.subscriptions.push(diagnosticCollection);

    // Initialize providers
    diagnosticsProvider = new CSIDiagnosticsProvider(diagnosticCollection);
    statusBar = new CSIStatusBar();

    // Register tree view
    const treeDataProvider = new CSITreeDataProvider();
    vscode.window.registerTreeDataProvider('codebase-csi-results', treeDataProvider);

    // Register code actions provider
    const codeActionProvider = new CSICodeActionProvider();
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file' },
            codeActionProvider,
            { providedCodeActionKinds: CSICodeActionProvider.providedCodeActionKinds }
        )
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.scanFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active file to scan');
                return;
            }
            await scanFile(editor.document, diagnosticsProvider, statusBar, treeDataProvider);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.scanWorkspace', async () => {
            await scanWorkspace(diagnosticsProvider, statusBar, treeDataProvider);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.explainDetection', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active file');
                return;
            }
            await explainDetection(editor.document, diagnosticsProvider);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.autoFix', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active file to fix');
                return;
            }
            await autoFixIssues(editor.document, diagnosticsProvider);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.toggleRealTime', () => {
            realTimeEnabled = !realTimeEnabled;
            const config = vscode.workspace.getConfiguration('codebase-csi');
            config.update('realTimeDetection', realTimeEnabled, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(
                `Real-time detection ${realTimeEnabled ? 'enabled' : 'disabled'}`
            );
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('codebase-csi.showReport', () => {
            showDetailedReport(treeDataProvider);
        })
    );

    // Listen to configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('codebase-csi')) {
                const config = vscode.workspace.getConfiguration('codebase-csi');
                realTimeEnabled = config.get('realTimeDetection', false);
            }
        })
    );

    // Real-time detection on document change
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(async e => {
            const config = vscode.workspace.getConfiguration('codebase-csi');
            if (config.get('realTimeDetection', false) && e.document === vscode.window.activeTextEditor?.document) {
                // Debounce: wait 1 second after last change
                setTimeout(async () => {
                    await scanFile(e.document, diagnosticsProvider, statusBar, treeDataProvider, true);
                }, 1000);
            }
        })
    );

    // Scan on file save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(async document => {
            const config = vscode.workspace.getConfiguration('codebase-csi');
            if (config.get('enabled', true)) {
                await scanFile(document, diagnosticsProvider, statusBar, treeDataProvider);
                
                // Auto-fix on save if enabled
                if (config.get('autoFixOnSave', false)) {
                    await autoFixIssues(document, diagnosticsProvider);
                }
            }
        })
    );

    // Scan when file is opened
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(async document => {
            const config = vscode.workspace.getConfiguration('codebase-csi');
            if (config.get('enabled', true)) {
                await scanFile(document, diagnosticsProvider, statusBar, treeDataProvider, true);
            }
        })
    );

    // Initialize status bar
    context.subscriptions.push(statusBar);

    // Show welcome message
    vscode.window.showInformationMessage(
        'Codebase CSI is active! Right-click in editor to scan files.',
        'Scan Workspace',
        'Settings'
    ).then(selection => {
        if (selection === 'Scan Workspace') {
            vscode.commands.executeCommand('codebase-csi.scanWorkspace');
        } else if (selection === 'Settings') {
            vscode.commands.executeCommand('workbench.action.openSettings', 'codebase-csi');
        }
    });
}

function showDetailedReport(treeDataProvider: CSITreeDataProvider) {
    const panel = vscode.window.createWebviewPanel(
        'csiReport',
        'Codebase CSI Report',
        vscode.ViewColumn.One,
        { enableScripts: true }
    );

    const results = treeDataProvider.getResults();
    
    panel.webview.html = generateReportHTML(results);
}

function generateReportHTML(results: any[]): string {
    const totalFiles = results.length;
    const highRisk = results.filter(r => r.confidence >= 0.7).length;
    const mediumRisk = results.filter(r => r.confidence >= 0.4 && r.confidence < 0.7).length;
    const lowRisk = results.filter(r => r.confidence < 0.4).length;

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
            .header { margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
            .stat-card {
                padding: 20px;
                border-radius: 8px;
                background-color: var(--vscode-editor-inactiveSelectionBackground);
            }
            .high-risk { border-left: 4px solid #ff6b6b; }
            .medium-risk { border-left: 4px solid #ffd93d; }
            .low-risk { border-left: 4px solid #6bcf7f; }
            .stat-number { font-size: 36px; font-weight: bold; }
            .stat-label { font-size: 14px; opacity: 0.8; }
            .file-list { margin-top: 20px; }
            .file-item {
                padding: 10px;
                margin: 5px 0;
                background-color: var(--vscode-editor-inactiveSelectionBackground);
                border-radius: 4px;
            }
            .confidence-bar {
                height: 4px;
                background-color: var(--vscode-progressBar-background);
                border-radius: 2px;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Codebase CSI Analysis Report</h1>
            <p>Total files scanned: ${totalFiles}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card high-risk">
                <div class="stat-number">${highRisk}</div>
                <div class="stat-label">High Risk Files</div>
            </div>
            <div class="stat-card medium-risk">
                <div class="stat-number">${mediumRisk}</div>
                <div class="stat-label">Medium Risk Files</div>
            </div>
            <div class="stat-card low-risk">
                <div class="stat-number">${lowRisk}</div>
                <div class="stat-label">Low Risk Files</div>
            </div>
        </div>
        
        <div class="file-list">
            <h2>Detected Files</h2>
            ${results.map(r => `
                <div class="file-item">
                    <strong>${r.file}</strong>
                    <div>Confidence: ${(r.confidence * 100).toFixed(1)}%</div>
                    <div class="confidence-bar" style="width: ${r.confidence * 100}%; background-color: ${r.confidence >= 0.7 ? '#ff6b6b' : r.confidence >= 0.4 ? '#ffd93d' : '#6bcf7f'}"></div>
                </div>
            `).join('')}
        </div>
    </body>
    </html>
    `;
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
}
