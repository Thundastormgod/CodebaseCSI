"""
Tests for language detection including conflict resolution.
"""

import pytest
from pathlib import Path
from codebase_csi.utils.file_utils import LanguageDetector


class TestLanguageDetector:
    """Test language detection capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()
    
    def test_python_detection(self):
        """Test Python file detection."""
        assert self.detector.detect(Path('test.py')) == 'python'
        assert self.detector.detect(Path('test.pyw')) == 'python'
        assert self.detector.detect(Path('test.pyi')) == 'python'
    
    def test_javascript_detection(self):
        """Test JavaScript/TypeScript detection."""
        assert self.detector.detect(Path('test.js')) == 'javascript'
        assert self.detector.detect(Path('test.jsx')) == 'javascript'
        assert self.detector.detect(Path('test.mjs')) == 'javascript'
        assert self.detector.detect(Path('test.ts')) == 'typescript'
        assert self.detector.detect(Path('test.tsx')) == 'typescript'
    
    def test_web_technologies(self):
        """Test web technology detection."""
        assert self.detector.detect(Path('test.html')) == 'html'
        assert self.detector.detect(Path('test.css')) == 'css'
        assert self.detector.detect(Path('test.scss')) == 'scss'
        assert self.detector.detect(Path('test.vue')) == 'vue'
        assert self.detector.detect(Path('test.svelte')) == 'svelte'
    
    def test_config_files(self):
        """Test configuration file detection."""
        assert self.detector.detect(Path('config.json')) == 'json'
        assert self.detector.detect(Path('config.yaml')) == 'yaml'
        assert self.detector.detect(Path('config.yml')) == 'yaml'
        assert self.detector.detect(Path('config.toml')) == 'toml'
        assert self.detector.detect(Path('config.xml')) == 'xml'
    
    def test_markup_languages(self):
        """Test markup language detection."""
        assert self.detector.detect(Path('README.md')) == 'markdown'
        assert self.detector.detect(Path('doc.rst')) == 'restructuredtext'
    
    def test_infrastructure(self):
        """Test infrastructure as code detection."""
        assert self.detector.detect(Path('main.tf')) == 'terraform'
        assert self.detector.detect(Path('Dockerfile')) == 'dockerfile'
        assert self.detector.detect(Path('Makefile')) == 'makefile'
    
    def test_data_science(self):
        """Test data science file detection."""
        assert self.detector.detect(Path('notebook.ipynb')) == 'jupyter'
        assert self.detector.detect(Path('analysis.jl')) == 'julia'
        assert self.detector.detect(Path('script.r')) == 'r'
        assert self.detector.detect(Path('script.R')) == 'r'
    
    def test_systems_languages(self):
        """Test systems programming language detection."""
        assert self.detector.detect(Path('main.rs')) == 'rust'
        assert self.detector.detect(Path('main.go')) == 'go'
        assert self.detector.detect(Path('main.zig')) == 'zig'
        assert self.detector.detect(Path('main.nim')) == 'nim'
    
    def test_binary_extensions(self):
        """Test binary file extension detection."""
        assert self.detector.detect(Path('file.pyc')) == 'binary'
        assert self.detector.detect(Path('file.exe')) == 'binary'
        assert self.detector.detect(Path('image.png')) == 'binary'
        assert self.detector.detect(Path('archive.zip')) == 'binary'
    
    def test_unknown_extension(self):
        """Test unknown extension handling."""
        assert self.detector.detect(Path('file.unknown')) == 'unknown'
        assert self.detector.detect(Path('noextension')) == 'unknown'
    
    def test_matlab_vs_objc_conflict(self):
        """Test MATLAB vs Objective-C conflict resolution."""
        # MATLAB code
        matlab_code = """
        function result = calculate(x, y)
            % This is a MATLAB comment
            result = x + y;
            plot(result);
        end
        """
        assert self.detector.detect(Path('test.m'), matlab_code) == 'matlab'
        
        # Objective-C code
        objc_code = """
        #import <Foundation/Foundation.h>
        @interface MyClass : NSObject
        @property (nonatomic, strong) NSString *name;
        @end
        """
        assert self.detector.detect(Path('test.m'), objc_code) == 'objective-c'
    
    def test_verilog_vs_vlang_conflict(self):
        """Test Verilog vs V language conflict resolution."""
        # Verilog code
        verilog_code = """
        module counter(
            input clk,
            input reset,
            output reg [7:0] count
        );
            always @(posedge clk) begin
                if (reset)
                    count <= 0;
                else
                    count <= count + 1;
            end
        endmodule
        """
        assert self.detector.detect(Path('test.v'), verilog_code) == 'verilog'
        
        # V language code
        vlang_code = """
        fn main() {
            mut count := 0
            println('Count: $count')
        }
        
        pub fn calculate(x int, y int) int {
            return x + y
        }
        """
        assert self.detector.detect(Path('test.v'), vlang_code) == 'vlang'
    
    def test_c_vs_cpp_conflict(self):
        """Test C vs C++ header conflict resolution."""
        # C code
        c_code = """
        #include <stdio.h>
        
        int add(int a, int b) {
            return a + b;
        }
        """
        assert self.detector.detect(Path('test.h'), c_code) == 'c'
        
        # C++ code
        cpp_code = """
        #include <iostream>
        
        namespace MyNamespace {
            class Calculator {
            public:
                int add(int a, int b) {
                    return a + b;
                }
            };
        }
        """
        assert self.detector.detect(Path('test.h'), cpp_code) == 'cpp'
    
    def test_is_supported(self):
        """Test language support checking."""
        assert self.detector.is_supported(Path('test.py')) == True
        assert self.detector.is_supported(Path('test.unknown')) == False
        assert self.detector.is_supported(Path('test.pyc')) == False
    
    def test_is_binary_extension(self):
        """Test binary extension checking."""
        assert self.detector.is_binary_extension(Path('file.pyc')) == True
        assert self.detector.is_binary_extension(Path('file.py')) == False
        assert self.detector.is_binary_extension(Path('image.png')) == True
        assert self.detector.is_binary_extension(Path('script.js')) == False


class TestLanguageCoverage:
    """Test that we support a comprehensive set of languages."""
    
    def test_minimum_language_count(self):
        """Test that we support at least 50 languages."""
        detector = LanguageDetector()
        unique_languages = set(detector.LANGUAGE_MAP.values())
        # Remove 'binary' from count
        unique_languages.discard('binary')
        assert len(unique_languages) >= 50, f"Only {len(unique_languages)} languages supported"
    
    def test_critical_languages_supported(self):
        """Test that all critical modern languages are supported."""
        detector = LanguageDetector()
        
        critical_languages = [
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c',
            'csharp', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin',
            'html', 'css', 'json', 'yaml', 'sql', 'shell', 'markdown'
        ]
        
        supported = set(detector.LANGUAGE_MAP.values())
        
        for lang in critical_languages:
            assert lang in supported, f"Critical language '{lang}' not supported"
