/**
 * Status bar item for showing scan status
 */

import * as vscode from 'vscode';

export class CSIStatusBar {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'codebase-csi.scanFile';
        this.setIdle();
        this.statusBarItem.show();
    }

    setScanning(target: string): void {
        this.statusBarItem.text = `$(sync~spin) CSI Scanning...`;
        this.statusBarItem.tooltip = `Scanning ${target}`;
    }

    setResult(confidence: number): void {
        const percentage = (confidence * 100).toFixed(0);
        
        if (confidence >= 0.7) {
            this.statusBarItem.text = `$(error) CSI: ${percentage}%`;
            this.statusBarItem.tooltip = 'High AI confidence detected';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
        } else if (confidence >= 0.4) {
            this.statusBarItem.text = `$(warning) CSI: ${percentage}%`;
            this.statusBarItem.tooltip = 'Medium AI confidence detected';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            this.statusBarItem.text = `$(check) CSI: ${percentage}%`;
            this.statusBarItem.tooltip = 'Low AI confidence - code looks good';
            this.statusBarItem.backgroundColor = undefined;
        }
    }

    setIdle(): void {
        this.statusBarItem.text = `$(search) CSI`;
        this.statusBarItem.tooltip = 'Click to scan current file';
        this.statusBarItem.backgroundColor = undefined;
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
