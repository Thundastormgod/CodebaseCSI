/**
 * Tree view data provider for results panel
 */

import * as vscode from 'vscode';
import * as path from 'path';

interface ResultItem {
    file: string;
    confidence: number;
    patterns: number;
}

export class CSITreeDataProvider implements vscode.TreeDataProvider<ResultTreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<ResultTreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private results: ResultItem[] = [];

    refresh(): void {
        this._onDidChangeTreeData.fire(undefined);
    }

    addResult(result: ResultItem): void {
        // Update or add result
        const existingIndex = this.results.findIndex(r => r.file === result.file);
        if (existingIndex >= 0) {
            this.results[existingIndex] = result;
        } else {
            this.results.push(result);
        }
        
        // Sort by confidence (highest first)
        this.results.sort((a, b) => b.confidence - a.confidence);
        
        this.refresh();
    }

    clear(): void {
        this.results = [];
        this.refresh();
    }

    getResults(): ResultItem[] {
        return this.results;
    }

    getTreeItem(element: ResultTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: ResultTreeItem): ResultTreeItem[] {
        if (!element) {
            // Root level - show all files
            return this.results.map(r => new ResultTreeItem(
                path.basename(r.file),
                r.file,
                r.confidence,
                r.patterns,
                vscode.TreeItemCollapsibleState.None
            ));
        }
        return [];
    }
}

class ResultTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly filePath: string,
        public readonly confidence: number,
        public readonly patternCount: number,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);

        this.tooltip = `${filePath}\nConfidence: ${(confidence * 100).toFixed(1)}%\nPatterns: ${patternCount}`;
        this.description = `${(confidence * 100).toFixed(0)}%`;
        
        // Set icon based on confidence
        if (confidence >= 0.7) {
            this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('codebase-csi.highRisk'));
        } else if (confidence >= 0.4) {
            this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('codebase-csi.mediumRisk'));
        } else {
            this.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('codebase-csi.lowRisk'));
        }

        // Command to open file when clicked
        this.command = {
            command: 'vscode.open',
            title: 'Open File',
            arguments: [vscode.Uri.file(filePath)]
        };
    }
}
