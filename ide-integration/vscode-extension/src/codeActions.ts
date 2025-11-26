/**
 * Code actions provider for quick fixes
 */

import * as vscode from 'vscode';

export class CSICodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source === 'Codebase CSI') {
                actions.push(...this.createQuickFixes(document, diagnostic));
            }
        }

        return actions;
    }

    private createQuickFixes(document: vscode.TextDocument, diagnostic: vscode.Diagnostic): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];
        const patternType = diagnostic.code?.toString();

        // Remove emoji
        if (patternType === 'emoji') {
            const action = new vscode.CodeAction('Remove emoji', vscode.CodeActionKind.QuickFix);
            action.edit = new vscode.WorkspaceEdit();
            const line = document.lineAt(diagnostic.range.start.line);
            const emojiRegex = /[\u{1F300}-\u{1F9FF}]/gu;
            const newText = line.text.replace(emojiRegex, '');
            action.edit.replace(document.uri, line.range, newText);
            action.diagnostics = [diagnostic];
            actions.push(action);
        }

        // Fix generic naming
        if (patternType === 'generic_naming') {
            const suggestionsAction = new vscode.CodeAction(
                'Suggest better name',
                vscode.CodeActionKind.QuickFix
            );
            suggestionsAction.command = {
                command: 'codebase-csi.suggestName',
                title: 'Suggest better name',
                arguments: [document, diagnostic.range]
            };
            actions.push(suggestionsAction);
        }

        // Scan entire file
        const scanAction = new vscode.CodeAction('Scan entire file', vscode.CodeActionKind.QuickFix);
        scanAction.command = {
            command: 'codebase-csi.scanFile',
            title: 'Scan file'
        };
        actions.push(scanAction);

        // Explain detection
        const explainAction = new vscode.CodeAction('Explain detection', vscode.CodeActionKind.QuickFix);
        explainAction.command = {
            command: 'codebase-csi.explainDetection',
            title: 'Explain'
        };
        actions.push(explainAction);

        return actions;
    }
}
