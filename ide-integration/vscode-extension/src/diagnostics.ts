/**
 * Diagnostics provider for VS Code
 */

import * as vscode from 'vscode';

interface Pattern {
    type: string;
    line: number;
    severity: string;
    confidence: number;
    context: string;
    remediation: string;
}

interface ScanResult {
    confidence: number;
    patterns: Pattern[];
    language: string;
    lines_of_code: number;
}

export class CSIDiagnosticsProvider {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private cachedResults = new Map<string, ScanResult>();

    constructor(diagnosticCollection: vscode.DiagnosticCollection) {
        this.diagnosticCollection = diagnosticCollection;
    }

    updateDiagnostics(uri: vscode.Uri, result: ScanResult): void {
        this.cachedResults.set(uri.toString(), result);
        
        const diagnostics: vscode.Diagnostic[] = [];
        const config = vscode.workspace.getConfiguration('codebase-csi');
        const showInline = config.get('showInlineWarnings', true);

        if (!showInline) {
            return;
        }

        for (const pattern of result.patterns) {
            const line = Math.max(0, pattern.line - 1); // Convert to 0-indexed
            const range = new vscode.Range(line, 0, line, 1000);
            
            const diagnostic = new vscode.Diagnostic(
                range,
                this.formatMessage(pattern, result.confidence),
                this.getSeverity(pattern.severity, result.confidence)
            );

            diagnostic.code = pattern.type;
            diagnostic.source = 'Codebase CSI';
            
            // Add related information
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    pattern.remediation
                )
            ];

            diagnostics.push(diagnostic);
        }

        this.diagnosticCollection.set(uri, diagnostics);
    }

    getDiagnostics(uri: vscode.Uri): readonly vscode.Diagnostic[] | undefined {
        return this.diagnosticCollection.get(uri);
    }

    getCachedResult(uri: vscode.Uri): ScanResult | undefined {
        return this.cachedResults.get(uri.toString());
    }

    clear(): void {
        this.diagnosticCollection.clear();
        this.cachedResults.clear();
    }

    private formatMessage(pattern: Pattern, overallConfidence: number): string {
        const emoji = this.getPatternEmoji(pattern.type);
        return `${emoji} ${pattern.type.replace(/_/g, ' ')} (${(pattern.confidence * 100).toFixed(0)}% confidence) - ${pattern.context.slice(0, 100)}`;
    }

    private getSeverity(severity: string, confidence: number): vscode.DiagnosticSeverity {
        if (confidence >= 0.7) {
            return vscode.DiagnosticSeverity.Error;
        } else if (confidence >= 0.4) {
            return vscode.DiagnosticSeverity.Warning;
        } else {
            return vscode.DiagnosticSeverity.Information;
        }
    }

    private getPatternEmoji(type: string): string {
        const emojiMap: Record<string, string> = {
            'emoji': '😀',
            'generic_naming': '🏷️',
            'verbose_comments': '💬',
            'sql_injection': '🔒',
            'command_injection': '⚠️',
            'magic_numbers': '🔢',
            'god_function': '👹',
            'cyclomatic_complexity': '🔀',
            'token_diversity': '📊',
            'ai_writing_style': '✍️',
            'god_class': '🏛️',
        };
        return emojiMap[type] || '❓';
    }
}
