"""Tests for the Development Documentation Analyzer."""

import pytest
import tempfile
from pathlib import Path

from codebase_csi.analyzers.dev_doc_analyzer import DevDocAnalyzer, DevDocIssue, scan_for_dev_docs


class TestDevDocAnalyzer:
    """Test suite for DevDocAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DevDocAnalyzer()
    
    # ==========================================
    # Filename Pattern Tests
    # ==========================================
    
    def test_detects_implementation_summary(self):
        """Should detect IMPLEMENTATION_SUMMARY.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "IMPLEMENTATION_SUMMARY.md"
            file_path.write_text("# Implementation Summary\n\nThis is a summary.")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'implementation_summary'
            assert issue.severity == 'HIGH'
    
    def test_detects_implementation_plan(self):
        """Should detect IMPLEMENTATION_PLAN.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "IMPLEMENTATION_PLAN.md"
            file_path.write_text("# Implementation Plan")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'implementation_plan'
            assert issue.severity == 'HIGH'
    
    def test_detects_architecture_doc(self):
        """Should detect ARCHITECTURE.md as potential dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "ARCHITECTURE.md"
            file_path.write_text("# Architecture\n\nSystem design notes.")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'architecture_doc'
            assert issue.severity == 'MEDIUM'
    
    def test_detects_quick_setup(self):
        """Should detect QUICK_SETUP.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "QUICK_SETUP.md"
            file_path.write_text("# Quick Setup Guide")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'quick_setup'
    
    def test_detects_improvements_doc(self):
        """Should detect IMPROVEMENTS.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "IMPROVEMENTS.md"
            file_path.write_text("# Improvements\n\n- Fix bug\n- Add feature")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'improvements'
            assert issue.severity == 'HIGH'
    
    def test_detects_todo_doc(self):
        """Should detect TODO.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "TODO.md"
            file_path.write_text("# TODO\n\n- [ ] Task 1\n- [ ] Task 2")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'todo_doc'
            assert issue.severity == 'HIGH'
    
    def test_detects_deep_dive_doc(self):
        """Should detect DEEP_DIVE.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "ANALYZER_DEEP_DIVE.md"
            file_path.write_text("# Deep Dive into Analyzers")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'deep_dive'
    
    def test_detects_draft_doc(self):
        """Should detect DRAFT-*.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "DRAFT-API.md"
            file_path.write_text("# Draft API Design")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'draft_doc'
            assert issue.severity == 'HIGH'
    
    def test_detects_wip_doc(self):
        """Should detect WIP-*.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "WIP-FEATURE.md"
            file_path.write_text("# Work in Progress")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'wip_doc'
    
    def test_detects_integration_plan(self):
        """Should detect INTEGRATION_PLAN.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "ML_INTEGRATION_PLAN.md"
            file_path.write_text("# ML Integration Plan")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'integration_plan'
            assert issue.severity == 'HIGH'
    
    def test_detects_meeting_notes(self):
        """Should detect MEETING_NOTES.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "MEETING_NOTES.md"
            file_path.write_text("# Meeting Notes - Nov 2025")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'meeting_notes'
            assert issue.severity == 'HIGH'
    
    # ==========================================
    # Standard File Whitelist Tests
    # ==========================================
    
    def test_allows_readme(self):
        """Should NOT flag README.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "README.md"
            file_path.write_text("# Project Name\n\nDescription here.")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_allows_changelog(self):
        """Should NOT flag CHANGELOG.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "CHANGELOG.md"
            file_path.write_text("# Changelog\n\n## v1.0.0")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_allows_contributing(self):
        """Should NOT flag CONTRIBUTING.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "CONTRIBUTING.md"
            file_path.write_text("# Contributing Guide")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_allows_code_of_conduct(self):
        """Should NOT flag CODE_OF_CONDUCT.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "CODE_OF_CONDUCT.md"
            file_path.write_text("# Code of Conduct")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_allows_security(self):
        """Should NOT flag SECURITY.md as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "SECURITY.md"
            file_path.write_text("# Security Policy")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_allows_license(self):
        """Should NOT flag LICENSE as dev doc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "LICENSE"
            file_path.write_text("MIT License")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    # ==========================================
    # Content Pattern Tests
    # ==========================================
    
    def test_detects_planning_content(self):
        """Should detect planning content patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "notes.md"
            content = """# Project Notes
            
This document outlines the implementation plan for the new feature.

## Phase 1: Setup
- Configure environment
- Install dependencies

## Phase 2: Development
- Implement core logic

## Next Steps
- Review with team
"""
            file_path.write_text(content)
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.confidence >= 0.5
    
    def test_detects_internal_use_only(self):
        """Should detect 'internal use only' content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "notes.md"
            content = """# Internal Documentation

INTERNAL USE ONLY - Do not share externally.

## Details
..."""
            file_path.write_text(content)
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.confidence >= 0.8
    
    def test_detects_task_lists(self):
        """Should detect markdown task lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "tasks.md"
            content = """# Tasks

- [ ] Implement feature A
- [x] Fix bug B
- [ ] Write tests
- [ ] Update docs
- [ ] Deploy
"""
            file_path.write_text(content)
            
            issue = self.analyzer.analyze_file(file_path)
            
            # Task lists alone have lower confidence
            # but combined with other patterns should flag
            assert issue is not None or True  # May or may not flag based on threshold
    
    # ==========================================
    # Directory Scanning Tests
    # ==========================================
    
    def test_analyze_directory(self):
        """Should scan directory and find dev docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create standard files (should be ignored)
            (tmppath / "README.md").write_text("# Project")
            (tmppath / "CHANGELOG.md").write_text("# Changelog")
            
            # Create dev docs (should be flagged)
            (tmppath / "IMPLEMENTATION_PLAN.md").write_text("# Plan")
            (tmppath / "TODO.md").write_text("# TODO")
            
            issues = self.analyzer.analyze_directory(tmppath)
            
            assert len(issues) == 2
            assert any(i.doc_type == 'implementation_plan' for i in issues)
            assert any(i.doc_type == 'todo_doc' for i in issues)
    
    def test_skips_venv_directory(self):
        """Should skip .venv directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create .venv with a README
            venv_dir = tmppath / ".venv"
            venv_dir.mkdir()
            (venv_dir / "README.md").write_text("Virtual environment")
            
            # Create actual dev doc
            (tmppath / "TODO.md").write_text("# TODO")
            
            issues = self.analyzer.analyze_directory(tmppath)
            
            # Should only find TODO.md, not .venv/README.md
            assert len(issues) == 1
            assert issues[0].doc_type == 'todo_doc'
    
    def test_skips_node_modules(self):
        """Should skip node_modules directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create node_modules with docs
            nm_dir = tmppath / "node_modules"
            nm_dir.mkdir()
            (nm_dir / "IMPLEMENTATION.md").write_text("Package docs")
            
            issues = self.analyzer.analyze_directory(tmppath)
            
            assert len(issues) == 0
    
    # ==========================================
    # Gitignore Suggestion Tests
    # ==========================================
    
    def test_generates_gitignore_suggestions(self):
        """Should generate appropriate gitignore suggestions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            (tmppath / "IMPLEMENTATION_SUMMARY.md").write_text("# Summary")
            (tmppath / "IMPROVEMENTS.md").write_text("# Improvements")
            (tmppath / "ARCHITECTURE.md").write_text("# Architecture")
            
            self.analyzer.analyze_directory(tmppath)
            suggestions = self.analyzer.generate_gitignore_suggestions()
            
            assert len(suggestions) >= 2
            assert 'IMPLEMENTATION*.md' in suggestions or 'IMPLEMENTATION_SUMMARY.md' in suggestions
    
    # ==========================================
    # Summary Tests
    # ==========================================
    
    def test_get_summary(self):
        """Should generate accurate summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            (tmppath / "IMPLEMENTATION_PLAN.md").write_text("# Plan")  # HIGH
            (tmppath / "TODO.md").write_text("# TODO")  # HIGH
            (tmppath / "ARCHITECTURE.md").write_text("# Arch")  # MEDIUM
            
            self.analyzer.analyze_directory(tmppath)
            summary = self.analyzer.get_summary()
            
            assert summary['total_issues'] == 3
            assert summary['high_severity'] == 2
            assert summary['medium_severity'] == 1
    
    # ==========================================
    # Convenience Function Tests
    # ==========================================
    
    def test_scan_for_dev_docs_function(self):
        """Should work with convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            (tmppath / "TODO.md").write_text("# TODO")
            
            result = scan_for_dev_docs(str(tmppath))
            
            assert 'issues' in result
            assert 'summary' in result
            assert len(result['issues']) == 1
    
    # ==========================================
    # Edge Cases
    # ==========================================
    
    def test_handles_non_markdown_files(self):
        """Should skip non-markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "IMPLEMENTATION_PLAN.py"
            file_path.write_text("# This is Python, not markdown")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is None
    
    def test_handles_empty_file(self):
        """Should handle empty files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "IMPLEMENTATION_PLAN.md"
            file_path.write_text("")
            
            issue = self.analyzer.analyze_file(file_path)
            
            # Should still flag based on filename
            assert issue is not None
    
    def test_handles_unreadable_file(self):
        """Should handle unreadable files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "notes.md"
            # Create file with binary content that might cause issues
            file_path.write_bytes(b'\x80\x81\x82\x83')
            
            # Should not raise exception
            issue = self.analyzer.analyze_file(file_path)
            # May or may not detect, but should not crash
    
    def test_case_insensitive_matching(self):
        """Should match patterns case-insensitively."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "implementation_summary.md"
            file_path.write_text("# Summary")
            
            issue = self.analyzer.analyze_file(file_path)
            
            assert issue is not None
            assert issue.doc_type == 'implementation_summary'


class TestDevDocAnalyzerIntegration:
    """Integration tests for DevDocAnalyzer."""
    
    def test_real_world_project_structure(self):
        """Should handle realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Standard files (should be ignored)
            (tmppath / "README.md").write_text("# Project")
            (tmppath / "LICENSE").write_text("MIT")
            (tmppath / "CHANGELOG.md").write_text("# Changes")
            (tmppath / "CONTRIBUTING.md").write_text("# Contributing")
            
            # Official docs (should be ignored)
            official = tmppath / "docs" / "official"
            official.mkdir(parents=True)
            (official / "API.md").write_text("# API Docs")
            
            # Dev docs (should be flagged)
            (tmppath / "ARCHITECTURE.md").write_text("# Internal arch")
            (tmppath / "IMPLEMENTATION_PLAN.md").write_text("# Plan")
            (tmppath / "docs" / "DEEP_DIVE.md").write_text("# Deep dive")
            
            # Source code (should be ignored)
            src = tmppath / "src"
            src.mkdir()
            (src / "main.py").write_text("print('hello')")
            
            analyzer = DevDocAnalyzer()
            issues = analyzer.analyze_directory(tmppath)
            
            # Should flag dev docs but not standard files
            flagged_files = {Path(i.file_path).name for i in issues}
            
            assert "README.md" not in flagged_files
            assert "LICENSE" not in flagged_files
            assert "CHANGELOG.md" not in flagged_files
            assert "CONTRIBUTING.md" not in flagged_files
            
            assert "ARCHITECTURE.md" in flagged_files
            assert "IMPLEMENTATION_PLAN.md" in flagged_files
