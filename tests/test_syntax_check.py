#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки синтаксиса всех Python файлов в проекте.

Этот модуль содержит тесты для автоматической проверки синтаксиса
всех Python файлов в проекте, включая основные модули и тесты.
"""

import ast
import os
import sys
import unittest
from pathlib import Path
from typing import List


class TestPythonSyntax(unittest.TestCase):
    """Тесты для проверки синтаксиса Python файлов."""

    def setUp(self):
        """Настройка тестов."""
        self.project_root = Path(__file__).parent.parent
        self.python_files = self._find_python_files()

    def _find_python_files(self) -> List[Path]:
        """Найти все Python файлы в проекте.
        
        Returns:
            List[Path]: Список путей к Python файлам.
        """
        python_files = []
        
        # Поиск в корневой директории
        for file_path in self.project_root.glob("*.py"):
            python_files.append(file_path)
        
        # Поиск в поддиректориях
        for directory in ["tests"]:
            dir_path = self.project_root / directory
            if dir_path.exists():
                for file_path in dir_path.glob("*.py"):
                    python_files.append(file_path)
        
        return python_files

    def test_python_syntax_all_files(self):
        """Проверить синтаксис всех Python файлов в проекте."""
        errors = []
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Проверка синтаксиса с помощью ast
                ast.parse(content, filename=str(file_path))
                
            except SyntaxError as e:
                error_msg = (
                    f"Синтаксическая ошибка в файле {file_path}:\n"
                    f"  Строка {e.lineno}: {e.text}\n"
                    f"  Ошибка: {e.msg}"
                )
                errors.append(error_msg)
            except Exception as e:
                error_msg = (
                    f"Ошибка при чтении файла {file_path}: {e}"
                )
                errors.append(error_msg)
        
        if errors:
            self.fail("\n\n".join(errors))

    def test_individual_files_syntax(self):
        """Проверить синтаксис каждого файла отдельно."""
        for file_path in self.python_files:
            with self.subTest(file=str(file_path)):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Проверка синтаксиса
                    ast.parse(content, filename=str(file_path))
                    
                except SyntaxError as e:
                    self.fail(
                        f"Синтаксическая ошибка в строке {e.lineno}: "
                        f"{e.msg}\n{e.text}"
                    )
                except Exception as e:
                    self.fail(f"Ошибка при чтении файла: {e}")

    def test_files_not_empty(self):
        """Проверить, что Python файлы не пустые."""
        for file_path in self.python_files:
            with self.subTest(file=str(file_path)):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                    
                    self.assertTrue(
                        len(content) > 0,
                        f"Файл {file_path} пустой"
                    )
                    
                except Exception as e:
                    self.fail(f"Ошибка при чтении файла {file_path}: {e}")

    def test_no_hanging_code(self):
        """Проверить отсутствие висящего кода (код вне функций/классов)."""
        for file_path in self.python_files:
            with self.subTest(file=str(file_path)):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Парсинг AST
                    tree = ast.parse(content, filename=str(file_path))
                    
                    # Проверка на висящий код
                    hanging_statements = []
                    for node in tree.body:
                        # Разрешенные типы узлов на верхнем уровне
                        allowed_types = (
                            ast.Import,
                            ast.ImportFrom,
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                            ast.ClassDef,
                            ast.If,  # для if __name__ == "__main__"
                            ast.Assign,  # для констант
                            ast.AnnAssign,  # для аннотированных переменных
                            ast.Expr,  # для docstring модуля
                        )
                        
                        if not isinstance(node, allowed_types):
                            hanging_statements.append(
                                f"Строка {node.lineno}: {ast.dump(node)[:50]}..."
                            )
                        
                        # Специальная проверка для If (должен быть if __name__)
                        if isinstance(node, ast.If):
                            # Проверяем, что это if __name__ == "__main__"
                            if not self._is_main_guard(node):
                                hanging_statements.append(
                                    f"Строка {node.lineno}: "
                                    f"If-блок не является проверкой __name__"
                                )
                    
                    if hanging_statements:
                        self.fail(
                            f"Найден висящий код в {file_path}:\n" +
                            "\n".join(hanging_statements)
                        )
                        
                except Exception as e:
                    self.fail(f"Ошибка при анализе файла {file_path}: {e}")

    def _is_main_guard(self, node: ast.If) -> bool:
        """Проверить, является ли If-узел проверкой __name__ == '__main__'.
        
        Args:
            node: AST узел If для проверки.
            
        Returns:
            bool: True, если это проверка __name__ == '__main__'.
        """
        if not isinstance(node.test, ast.Compare):
            return False
        
        compare = node.test
        
        # Проверяем левую часть сравнения
        if not (isinstance(compare.left, ast.Name) and 
                compare.left.id == '__name__'):
            return False
        
        # Проверяем операторы сравнения
        if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq):
            return False
        
        # Проверяем правую часть сравнения
        if (len(compare.comparators) != 1 or 
            not isinstance(compare.comparators[0], ast.Constant) or
            compare.comparators[0].value != '__main__'):
            return False
        
        return True


if __name__ == '__main__':
    unittest.main()