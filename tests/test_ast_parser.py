"""
Tests for AST Parser Module

Tests cover:
1. Python AST parsing (built-in)
2. Regex fallback parsing
3. Multi-language support
4. Edge cases and error handling
5. Complexity calculation
6. Function/class extraction
"""

import pytest
from pathlib import Path
import tempfile
import os

from codebase_csi.parsers import (
    ASTParser,
    ParseResult,
    FunctionInfo,
    ClassInfo,
    parse_file,
    parse_code,
    get_supported_languages,
    is_language_supported,
)
from codebase_csi.parsers.ast_parser import (
    PythonASTParser,
    RegexParser,
    TreeSitterParser,
    ParserBackend,
    LANGUAGE_EXTENSIONS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON AST PARSER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPythonASTParser:
    """Tests for Python AST parsing."""
    
    def test_simple_function(self):
        """Test parsing a simple function."""
        code = '''
def hello(name):
    """Say hello."""
    return f"Hello, {name}!"
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert result.backend == ParserBackend.PYTHON_AST
        assert len(result.functions) == 1
        assert result.functions[0].name == 'hello'
        assert 'name' in result.functions[0].parameters
        assert result.functions[0].docstring == "Say hello."
    
    def test_async_function(self):
        """Test parsing async function."""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    async with aiohttp.ClientSession() as session:
        response = await session.get(url)
        return await response.json()
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert len(result.functions) == 1
        assert result.functions[0].name == 'fetch_data'
        assert result.functions[0].is_async
        assert result.functions[0].return_type == 'dict'
    
    def test_class_extraction(self):
        """Test extracting class information."""
        code = '''
from dataclasses import dataclass

@dataclass
class Person:
    """A person."""
    name: str
    age: int
    
    def greet(self):
        return f"Hello, I'm {self.name}"
    
    async def async_method(self):
        pass
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert len(result.classes) == 1
        cls = result.classes[0]
        assert cls.name == 'Person'
        assert cls.is_dataclass
        assert cls.docstring == "A person."
        assert len(cls.methods) == 2
        assert cls.methods[0].name == 'greet'
        assert cls.methods[1].is_async
    
    def test_nested_functions(self):
        """Test parsing nested functions."""
        code = '''
def outer():
    def inner():
        def innermost():
            pass
        return innermost
    return inner
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        # All functions should be found
        assert len(result.functions) == 3
        names = [f.name for f in result.functions]
        assert 'outer' in names
        assert 'inner' in names
        assert 'innermost' in names
    
    def test_complexity_calculation(self):
        """Test cyclomatic complexity calculation."""
        # Simple function - complexity 1
        simple = '''
def simple():
    return 42
'''
        result = PythonASTParser.parse(simple)
        assert result.complexity == 1
        
        # Complex function
        complex_code = '''
def complex_func(x, y):
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        for i in range(10):
            if i % 2 == 0:
                continue
        return -x
    else:
        try:
            return x / y
        except ZeroDivisionError:
            return 0
'''
        result = PythonASTParser.parse(complex_code)
        # if, if, elif, for, if, try, except = 7+ decision points
        assert result.complexity >= 6  # At least 6 decision points
    
    def test_import_extraction(self):
        """Test extracting imports."""
        code = '''
import os
import sys as system
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict as dd
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert len(result.imports) >= 4
        
        # Check import types
        modules = [imp.module for imp in result.imports]
        assert 'os' in modules
        assert 'pathlib' in modules or any('Path' in imp.names for imp in result.imports)
    
    def test_variable_extraction(self):
        """Test extracting module-level variables."""
        code = '''
MAX_SIZE = 100
name: str = "test"
items = []
_private = True
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert len(result.variables) >= 3
        
        var_names = [v.name for v in result.variables]
        assert 'MAX_SIZE' in var_names
        assert 'name' in var_names
        
        # Check constant detection
        max_size = next(v for v in result.variables if v.name == 'MAX_SIZE')
        assert max_size.is_constant
    
    def test_decorator_extraction(self):
        """Test extracting decorators."""
        code = '''
@property
def name(self):
    return self._name

@staticmethod
def create():
    pass

@lru_cache(maxsize=128)
def cached_func():
    pass
'''
        result = PythonASTParser.parse(code)
        
        assert result.parse_success
        assert len(result.functions) == 3
        
        decorators = {f.name: f.decorators for f in result.functions}
        assert 'property' in decorators['name']
        assert 'staticmethod' in decorators['create']
        assert any('lru_cache' in d for d in decorators['cached_func'])
    
    def test_syntax_error_fallback(self):
        """Test fallback on syntax error."""
        code = '''
def broken(
    # Missing closing parenthesis
    return 42
'''
        result = PythonASTParser.parse(code)
        
        # Should fall back to regex
        assert not result.parse_success or result.backend == ParserBackend.REGEX
        assert len(result.parse_errors) > 0
    
    def test_line_counts(self):
        """Test line counting."""
        code = '''# Comment line
"""Docstring"""

def func():
    # Inline comment
    pass

# Another comment
x = 1
'''
        result = PythonASTParser.parse(code)
        
        assert result.total_lines == 10
        assert result.blank_lines >= 2
        assert result.comment_lines >= 2
        assert result.code_lines >= 2
    
    def test_max_nesting_depth(self):
        """Test nesting depth calculation."""
        code = '''
def deep():
    if True:
        for i in range(10):
            while True:
                with open("f") as f:
                    try:
                        pass
                    except:
                        pass
'''
        result = PythonASTParser.parse(code)
        
        assert result.max_nesting_depth >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# REGEX PARSER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegexParser:
    """Tests for regex-based fallback parser."""
    
    def test_javascript_parsing(self):
        """Test parsing JavaScript code."""
        code = '''
// Comment
function hello(name) {
    return `Hello, ${name}!`;
}

const greet = async (name) => {
    console.log(`Hi ${name}`);
};

class Person {
    constructor(name) {
        this.name = name;
    }
    
    sayHello() {
        return this.name;
    }
}

import { something } from 'module';
const fs = require('fs');
'''
        result = RegexParser.parse(code, 'javascript')
        
        assert result.parse_success
        assert result.backend == ParserBackend.REGEX
        assert len(result.functions) >= 2
        assert len(result.classes) >= 1
        assert len(result.imports) >= 1
    
    def test_typescript_parsing(self):
        """Test parsing TypeScript code."""
        code = '''
interface User {
    name: string;
    age: number;
}

type Status = 'active' | 'inactive';

function greet(user: User): string {
    return `Hello, ${user.name}`;
}

class UserService {
    private users: User[] = [];
    
    async getUser(id: string): Promise<User | null> {
        return this.users.find(u => u.name === id) || null;
    }
}

import { Injectable } from '@angular/core';
'''
        result = RegexParser.parse(code, 'typescript')
        
        assert result.parse_success
        assert len(result.functions) >= 1
        assert len(result.classes) >= 1
    
    def test_java_parsing(self):
        """Test parsing Java code."""
        code = '''
package com.example;

import java.util.List;
import java.util.ArrayList;

public class Person {
    private String name;
    
    public Person(String name) {
        this.name = name;
    }
    
    public String getName() {
        return this.name;
    }
    
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}

interface Greeting {
    String greet();
}
'''
        result = RegexParser.parse(code, 'java')
        
        assert result.parse_success
        assert len(result.classes) >= 1
        assert len(result.functions) >= 2  # constructor, getName, main
        assert len(result.imports) >= 1
    
    def test_go_parsing(self):
        """Test parsing Go code."""
        code = '''
package main

import (
    "fmt"
    "net/http"
)

type Person struct {
    Name string
    Age  int
}

func (p *Person) Greet() string {
    return fmt.Sprintf("Hello, %s", p.Name)
}

func main() {
    p := Person{Name: "Alice", Age: 30}
    fmt.Println(p.Greet())
}

type Greeter interface {
    Greet() string
}
'''
        result = RegexParser.parse(code, 'go')
        
        assert result.parse_success
        assert len(result.functions) >= 2  # Greet, main
    
    def test_rust_parsing(self):
        """Test parsing Rust code."""
        code = '''
use std::collections::HashMap;

pub struct Person {
    name: String,
    age: u32,
}

impl Person {
    pub fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }
    
    pub fn greet(&self) -> String {
        format!("Hello, {}!", self.name)
    }
}

pub trait Greeter {
    fn greet(&self) -> String;
}

fn main() {
    let p = Person::new("Alice".to_string(), 30);
    println!("{}", p.greet());
}
'''
        result = RegexParser.parse(code, 'rust')
        
        assert result.parse_success
        assert len(result.functions) >= 3  # new, greet, main
    
    def test_ruby_parsing(self):
        """Test parsing Ruby code."""
        code = '''
require 'json'
require_relative 'helper'

module Greeting
  def greet
    "Hello!"
  end
end

class Person
  include Greeting
  
  attr_reader :name
  
  def initialize(name)
    @name = name
  end
  
  def say_hello
    "Hello, #{@name}!"
  end
end
'''
        result = RegexParser.parse(code, 'ruby')
        
        assert result.parse_success
        assert len(result.functions) >= 2
        assert len(result.classes) >= 1
    
    def test_php_parsing(self):
        """Test parsing PHP code."""
        code = '''
<?php
require_once 'config.php';

use App\\Models\\User;

interface Greeting {
    public function greet(): string;
}

class Person implements Greeting {
    private string $name;
    
    public function __construct(string $name) {
        $this->name = $name;
    }
    
    public function greet(): string {
        return "Hello, {$this->name}!";
    }
    
    public static function create(string $name): self {
        return new self($name);
    }
}
'''
        result = RegexParser.parse(code, 'php')
        
        assert result.parse_success
        assert len(result.classes) >= 1
        assert len(result.functions) >= 2
    
    def test_c_parsing(self):
        """Test parsing C code."""
        code = '''
#include <stdio.h>
#include <stdlib.h>
#include "myheader.h"

typedef struct {
    char* name;
    int age;
} Person;

void greet(Person* p) {
    printf("Hello, %s!\\n", p->name);
}

int main(int argc, char** argv) {
    Person p = {"Alice", 30};
    greet(&p);
    return 0;
}
'''
        result = RegexParser.parse(code, 'c')
        
        assert result.parse_success
        assert len(result.functions) >= 2  # greet, main
        assert len(result.imports) >= 2  # includes
    
    def test_cpp_parsing(self):
        """Test parsing C++ code."""
        code = '''
#include <iostream>
#include <string>
#include <vector>

namespace myapp {

class Person {
private:
    std::string name;
    int age;

public:
    Person(const std::string& name, int age) 
        : name(name), age(age) {}
    
    std::string greet() const {
        return "Hello, " + name + "!";
    }
    
    virtual ~Person() = default;
};

}  // namespace myapp

int main() {
    myapp::Person p("Alice", 30);
    std::cout << p.greet() << std::endl;
    return 0;
}
'''
        result = RegexParser.parse(code, 'cpp')
        
        assert result.parse_success
        assert len(result.classes) >= 1
    
    def test_complexity_calculation(self):
        """Test complexity calculation with regex."""
        code = '''
function complex(x, y) {
    if (x > 0) {
        if (y > 0) {
            return x + y;
        } else {
            return x - y;
        }
    } else if (x < 0) {
        for (let i = 0; i < 10; i++) {
            if (i % 2 === 0) {
                continue;
            }
        }
        return -x;
    } else {
        try {
            return x / y;
        } catch (e) {
            return 0;
        }
    }
}
'''
        result = RegexParser.parse(code, 'javascript')
        
        # Should detect multiple decision points
        assert result.complexity >= 5
    
    def test_comment_handling(self):
        """Test that comments are properly counted."""
        code = '''
// Single line comment
function hello() {
    /* Multi-line
       comment */
    return 42;
}
'''
        result = RegexParser.parse(code, 'javascript')
        
        assert result.comment_lines >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# AST PARSER INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestASTParser:
    """Tests for the main ASTParser class."""
    
    def test_parse_python_file(self):
        """Test parsing a Python file."""
        import tempfile
        
        # Create temp file with delete=False
        fd, temp_path = tempfile.mkstemp(suffix='.py')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write('''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"

class Greeter:
    def greet(self):
        pass
''')
            
            parser = ASTParser()
            result = parser.parse_file(temp_path)
            
            assert result.parse_success
            assert result.language == 'python'
            assert len(result.functions) >= 1
            assert len(result.classes) >= 1
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # Windows may still have file locked
    
    def test_parse_javascript_file(self):
        """Test parsing a JavaScript file."""
        import tempfile
        
        # Create temp file with delete=False  
        fd, temp_path = tempfile.mkstemp(suffix='.js')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write('''
function hello(name) {
    return `Hello, ${name}!`;
}

class Person {
    constructor(name) {
        this.name = name;
    }
}
''')
            
            parser = ASTParser()
            result = parser.parse_file(temp_path)
            
            assert result.parse_success
            assert result.language == 'javascript'
        finally:
            try:
                os.unlink(temp_path)
            except PermissionError:
                pass  # Windows may still have file locked
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        parser = ASTParser()
        result = parser.parse_file('/nonexistent/path/file.py')
        
        assert not result.parse_success
        assert len(result.parse_errors) > 0
    
    def test_language_detection(self):
        """Test language detection from file extensions."""
        parser = ASTParser()
        
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.c': 'c',
            '.cpp': 'cpp',
        }
        
        for ext, lang in extensions.items():
            detected = parser._detect_language(Path(f'test{ext}'))
            assert detected == lang, f"Expected {lang} for {ext}, got {detected}"
    
    def test_parse_code_direct(self):
        """Test parsing code directly."""
        parser = ASTParser()
        
        result = parser.parse_code('''
def test():
    if True:
        return 1
    return 0
''', 'python')
        
        assert result.parse_success
        assert len(result.functions) == 1
        assert result.complexity >= 2


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_parse_code_function(self):
        """Test parse_code convenience function."""
        result = parse_code('def hello(): pass', 'python')
        
        assert result.parse_success
        assert len(result.functions) == 1
    
    def test_get_supported_languages(self):
        """Test getting supported languages."""
        languages = get_supported_languages()
        
        assert 'python' in languages
        assert 'javascript' in languages
        assert 'java' in languages
    
    def test_is_language_supported(self):
        """Test language support check."""
        assert is_language_supported('python')
        assert is_language_supported('javascript')
        assert not is_language_supported('brainfuck')


# ═══════════════════════════════════════════════════════════════════════════════
# TREE-SITTER TESTS (Skip if not installed)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTreeSitter:
    """Tests for tree-sitter integration."""
    
    def test_availability_check(self):
        """Test tree-sitter availability check."""
        available = TreeSitterParser.is_available()
        # Should return bool without error
        assert isinstance(available, bool)
    
    @pytest.mark.skipif(
        not TreeSitterParser.is_available(),
        reason="tree-sitter not installed"
    )
    def test_tree_sitter_parsing(self):
        """Test tree-sitter parsing when available."""
        code = '''
def hello(name):
    return f"Hello, {name}!"
'''
        parser = ASTParser(prefer_tree_sitter=True)
        result = parser.parse_code(code, 'python')
        
        # If tree-sitter is available and has Python grammar
        if 'python' in TreeSitterParser.get_available_languages():
            assert result.backend == ParserBackend.TREE_SITTER
        
        assert result.parse_success


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_file(self):
        """Test parsing empty file."""
        result = parse_code('', 'python')
        
        assert result.parse_success
        assert result.total_lines == 1
        assert len(result.functions) == 0
    
    def test_only_comments(self):
        """Test file with only comments."""
        result = parse_code('''
# Comment 1
# Comment 2
# Comment 3
''', 'python')
        
        assert result.parse_success
        assert result.comment_lines >= 3
        assert len(result.functions) == 0
    
    def test_unicode_content(self):
        """Test parsing file with unicode content."""
        code = '''
def greet(name: str) -> str:
    """Приветствие на русском."""
    return f"Привет, {name}! 你好! مرحبا!"
'''
        result = parse_code(code, 'python')
        
        assert result.parse_success
        assert len(result.functions) == 1
    
    def test_very_long_lines(self):
        """Test file with very long lines."""
        long_string = 'x' * 10000
        code = f'''
def long_string():
    return "{long_string}"
'''
        result = parse_code(code, 'python')
        
        assert result.parse_success
    
    def test_deeply_nested_code(self):
        """Test deeply nested code."""
        code = '''
def deep():
    if True:
        for i in range(10):
            while True:
                with open("f") as f:
                    try:
                        if True:
                            for j in range(5):
                                while True:
                                    pass
                    except:
                        pass
'''
        result = parse_code(code, 'python')
        
        assert result.parse_success
        assert result.max_nesting_depth >= 8
    
    def test_lambda_functions(self):
        """Test that lambda functions don't break parsing."""
        code = '''
square = lambda x: x ** 2
items = list(map(lambda x: x * 2, range(10)))
sorted_items = sorted(items, key=lambda x: -x)
'''
        result = parse_code(code, 'python')
        
        assert result.parse_success
    
    def test_decorators_with_arguments(self):
        """Test decorators with complex arguments."""
        code = '''
@decorator(arg1="value", arg2=True)
@another.decorator
@parametrized.test([(1, 2), (3, 4)])
def complex_decorated():
    pass
'''
        result = parse_code(code, 'python')
        
        assert result.parse_success
        assert len(result.functions) == 1
        assert len(result.functions[0].decorators) >= 2
    
    def test_unknown_language(self):
        """Test parsing unknown language falls back to regex."""
        result = parse_code('some code here', 'unknown_language')
        
        # Should use regex fallback
        assert result.backend == ParserBackend.REGEX
    
    def test_mixed_indentation(self):
        """Test file with mixed tabs and spaces."""
        code = "def func():\n\treturn 1\n    pass"
        
        # Python will fail to parse this
        result = parse_code(code, 'python')
        
        # Should handle gracefully (either parse or fallback)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS ACCURACY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetricsAccuracy:
    """Tests to verify metrics accuracy."""
    
    def test_function_line_ranges(self):
        """Test that function line ranges are accurate."""
        code = '''
def func1():
    pass

def func2():
    x = 1
    y = 2
    return x + y

def func3():
    pass
'''
        result = parse_code(code, 'python')
        
        assert len(result.functions) == 3
        
        # func1 should span 2 lines
        func1 = next(f for f in result.functions if f.name == 'func1')
        assert func1.line_end - func1.line_start == 1
        
        # func2 should span more lines
        func2 = next(f for f in result.functions if f.name == 'func2')
        assert func2.line_end - func2.line_start >= 3
    
    def test_class_method_count(self):
        """Test accurate method counting in classes."""
        code = '''
class MyClass:
    def __init__(self):
        pass
    
    def method1(self):
        pass
    
    def method2(self):
        pass
    
    @staticmethod
    def static_method():
        pass
    
    @classmethod
    def class_method(cls):
        pass
'''
        result = parse_code(code, 'python')
        
        assert len(result.classes) == 1
        assert len(result.classes[0].methods) == 5
    
    def test_import_count(self):
        """Test accurate import counting."""
        code = '''
import os
import sys
from pathlib import Path
from typing import (
    List,
    Dict,
    Optional,
)
from collections import defaultdict, Counter
import json as j
'''
        result = parse_code(code, 'python')
        
        # Should detect all import statements
        assert len(result.imports) >= 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
