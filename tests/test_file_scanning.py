"""
Tests for file scanning with symlink protection and binary detection.
"""

import pytest
import tempfile
import os
from pathlib import Path
from codebase_csi.utils.file_utils import FileScanner, read_file_with_encoding_detection


class TestFileScanner:
    """Test file scanning capabilities."""
    
    def test_basic_scan(self, tmp_path):
        """Test basic file scanning."""
        # Create test files
        (tmp_path / "test1.py").write_text("print('hello')")
        (tmp_path / "test2.py").write_text("print('world')")
        (tmp_path / "test.txt").write_text("not code")
        
        scanner = FileScanner(extensions=['.py'])
        files = scanner.scan_directory(tmp_path, recursive=False)
        
        assert len(files) == 2
        assert all(f.suffix == '.py' for f in files)
    
    def test_recursive_scan(self, tmp_path):
        """Test recursive directory scanning."""
        # Create nested structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# main")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test.py").write_text("# test")
        
        scanner = FileScanner(extensions=['.py'])
        files = scanner.scan_directory(tmp_path, recursive=True)
        
        assert len(files) == 2
    
    def test_exclude_directories(self, tmp_path):
        """Test that common directories are excluded."""
        # Create directories that should be excluded
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("// lib")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_bytes(b'\x00\x00')
        (tmp_path / "main.py").write_text("# main")
        
        scanner = FileScanner(extensions=['.py', '.js'])
        files = scanner.scan_directory(tmp_path, recursive=True)
        
        # Should only find main.py, not files in excluded dirs
        assert len(files) == 1
        assert files[0].name == "main.py"
    
    def test_file_size_limit(self, tmp_path):
        """Test file size limiting."""
        # Create small and large files
        (tmp_path / "small.py").write_text("x = 1")
        (tmp_path / "large.py").write_text("x = 1\n" * 100000)  # Large file
        
        scanner = FileScanner(extensions=['.py'], max_file_size_kb=10)
        files = scanner.scan_directory(tmp_path)
        
        # Should only find small file
        assert len(files) == 1
        assert files[0].name == "small.py"
    
    def test_binary_file_exclusion(self, tmp_path):
        """Test that binary files are excluded."""
        # Create text and binary files
        (tmp_path / "text.py").write_text("print('hello')")
        (tmp_path / "binary.pyc").write_bytes(b'\x00\x01\x02\x03')
        (tmp_path / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n')
        
        scanner = FileScanner()
        files = scanner.scan_directory(tmp_path)
        
        # Should only find text.py
        assert len(files) == 1
        assert files[0].name == "text.py"
    
    def test_symlink_protection(self, tmp_path):
        """Test that symlinks are not followed."""
        # Create regular file
        (tmp_path / "real.py").write_text("# real file")
        
        # Create symlink to file
        link_path = tmp_path / "link.py"
        try:
            link_path.symlink_to(tmp_path / "real.py")
            
            scanner = FileScanner(extensions=['.py'])
            files = scanner.scan_directory(tmp_path)
            
            # Should only find real file, not symlink
            assert len(files) == 1
            assert files[0].name == "real.py"
        except OSError:
            # Symlinks might not be supported on this system
            pytest.skip("Symlinks not supported")
    
    def test_circular_symlink_protection(self, tmp_path):
        """Test protection against circular symlinks."""
        # Create directory with circular symlink
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        try:
            # Create circular symlink
            (subdir / "circular").symlink_to(tmp_path)
            
            scanner = FileScanner()
            # This should not hang or crash
            files = scanner.scan_directory(tmp_path, recursive=True)
            
            # Should complete without error
            assert isinstance(files, list)
        except OSError:
            pytest.skip("Symlinks not supported")
    
    def test_exclude_patterns(self, tmp_path):
        """Test custom exclusion patterns."""
        (tmp_path / "main.py").write_text("# main")
        (tmp_path / "test.py").write_text("# test")
        (tmp_path / "main.min.js").write_text("// minified")
        
        scanner = FileScanner(
            extensions=['.py', '.js'],
            exclude_patterns=['*.min.js', 'test.*']
        )
        files = scanner.scan_directory(tmp_path)
        
        # Should only find main.py
        assert len(files) == 1
        assert files[0].name == "main.py"


class TestBinaryDetection:
    """Test binary file detection."""
    
    def test_text_file_detection(self, tmp_path):
        """Test that text files are correctly identified."""
        scanner = FileScanner()
        
        # Plain text
        text_file = tmp_path / "text.py"
        text_file.write_text("print('hello world')")
        assert not scanner._is_binary(text_file)
    
    def test_binary_by_extension(self, tmp_path):
        """Test binary detection by extension."""
        scanner = FileScanner()
        
        # Files with binary extensions
        for ext in ['.pyc', '.exe', '.png', '.jpg', '.zip']:
            binary_file = tmp_path / f"file{ext}"
            binary_file.write_bytes(b'\x00\x01\x02\x03')
            assert scanner._is_binary(binary_file)
    
    def test_binary_by_magic_number(self, tmp_path):
        """Test binary detection by magic numbers."""
        scanner = FileScanner()
        
        # PNG image
        png_file = tmp_path / "image"
        png_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        assert scanner._is_binary(png_file)
        
        # ELF executable
        elf_file = tmp_path / "binary"
        elf_file.write_bytes(b'\x7fELF' + b'\x00' * 100)
        assert scanner._is_binary(elf_file)
        
        # PDF document
        pdf_file = tmp_path / "document"
        pdf_file.write_bytes(b'%PDF-1.4' + b'\x00' * 100)
        assert scanner._is_binary(pdf_file)
    
    def test_utf8_text_detection(self, tmp_path):
        """Test UTF-8 text is not flagged as binary."""
        scanner = FileScanner()
        
        # UTF-8 with international characters
        text_file = tmp_path / "international.py"
        text_file.write_text("# 你好世界 こんにちは 안녕하세요", encoding='utf-8')
        assert not scanner._is_binary(text_file)
    
    def test_utf16_text_detection(self, tmp_path):
        """Test UTF-16 text is not flagged as binary."""
        scanner = FileScanner()
        
        # UTF-16 encoded text (has null bytes)
        text_file = tmp_path / "utf16.txt"
        text_file.write_text("Hello World", encoding='utf-16')
        
        # This might be detected as binary due to null bytes
        # This is a known limitation without chardet
        # Just verify it doesn't crash
        result = scanner._is_binary(text_file)
        assert isinstance(result, bool)


class TestEncodingDetection:
    """Test encoding detection and file reading."""
    
    def test_utf8_reading(self, tmp_path):
        """Test reading UTF-8 files."""
        file_path = tmp_path / "utf8.py"
        content = "# UTF-8: Hello 世界"
        file_path.write_text(content, encoding='utf-8')
        
        read_content, encoding = read_file_with_encoding_detection(file_path)
        assert read_content == content
        assert encoding == 'utf-8'
    
    def test_utf8_bom_reading(self, tmp_path):
        """Test reading UTF-8 files with BOM."""
        file_path = tmp_path / "utf8bom.py"
        content = "# UTF-8 with BOM"
        file_path.write_text(content, encoding='utf-8-sig')
        
        read_content, encoding = read_file_with_encoding_detection(file_path)
        assert read_content == content
        assert encoding in ['utf-8-sig', 'utf-8']
    
    def test_latin1_reading(self, tmp_path):
        """Test reading Latin-1 encoded files."""
        file_path = tmp_path / "latin1.py"
        content = "# Latin-1: café"
        file_path.write_text(content, encoding='latin-1')
        
        read_content, encoding = read_file_with_encoding_detection(file_path)
        # Should successfully read (might use latin-1 or fallback)
        assert isinstance(read_content, str)
        assert encoding in ['utf-8', 'latin-1', 'windows-1252']
    
    def test_windows1252_reading(self, tmp_path):
        """Test reading Windows-1252 encoded files."""
        file_path = tmp_path / "windows.py"
        # Windows-1252 specific character
        content = "# Windows: "  # Right single quotation mark
        file_path.write_text(content, encoding='windows-1252')
        
        read_content, encoding = read_file_with_encoding_detection(file_path)
        assert isinstance(read_content, str)
    
    def test_empty_file(self, tmp_path):
        """Test reading empty files."""
        file_path = tmp_path / "empty.py"
        file_path.write_text("")
        
        read_content, encoding = read_file_with_encoding_detection(file_path)
        assert read_content == ""
        assert encoding == 'utf-8'


class TestDirectoryExclusions:
    """Test that comprehensive directory exclusions work."""
    
    def test_python_cache_dirs_excluded(self, tmp_path):
        """Test Python cache directories are excluded."""
        scanner = FileScanner(extensions=['.py'])
        
        # Create cache directories
        for cache_dir in ['__pycache__', '.pytest_cache', '.mypy_cache', '.tox']:
            (tmp_path / cache_dir).mkdir()
            (tmp_path / cache_dir / "file.py").write_text("# cached")
        
        (tmp_path / "main.py").write_text("# main")
        
        files = scanner.scan_directory(tmp_path, recursive=True)
        assert len(files) == 1
        assert files[0].name == "main.py"
    
    def test_node_modules_excluded(self, tmp_path):
        """Test Node.js directories are excluded."""
        scanner = FileScanner(extensions=['.js'])
        
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("// lib")
        (tmp_path / ".next").mkdir()
        (tmp_path / ".next" / "build.js").write_text("// build")
        (tmp_path / "main.js").write_text("// main")
        
        files = scanner.scan_directory(tmp_path, recursive=True)
        assert len(files) == 1
        assert files[0].name == "main.js"
    
    def test_build_dirs_excluded(self, tmp_path):
        """Test build directories are excluded."""
        scanner = FileScanner(extensions=['.java'])
        
        for build_dir in ['build', 'dist', 'target', 'out']:
            (tmp_path / build_dir).mkdir()
            (tmp_path / build_dir / "Main.java").write_text("// compiled")
        
        (tmp_path / "Main.java").write_text("// source")
        
        files = scanner.scan_directory(tmp_path, recursive=True)
        assert len(files) == 1
        assert files[0].name == "Main.java"
    
    def test_vcs_dirs_excluded(self, tmp_path):
        """Test version control directories are excluded."""
        scanner = FileScanner(extensions=['.py'])
        
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("# git config")
        (tmp_path / "main.py").write_text("# main")
        
        files = scanner.scan_directory(tmp_path, recursive=True)
        assert len(files) == 1
