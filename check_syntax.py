#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для быстрой проверки синтаксиса всех Python файлов в проекте.

Использование:
    python check_syntax.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def find_python_files(project_root: Path) -> List[Path]:
    """Найти все Python файлы в проекте.
    
    Args:
        project_root: Корневая директория проекта.
        
    Returns:
        List[Path]: Список путей к Python файлам.
    """
    python_files = []
    
    # Поиск в корневой директории
    for file_path in project_root.glob("*.py"):
        python_files.append(file_path)
    
    # Поиск в поддиректориях
    for directory in ["tests"]:
        dir_path = project_root / directory
        if dir_path.exists():
            for file_path in dir_path.glob("*.py"):
                python_files.append(file_path)
    
    return sorted(python_files)


def check_file_syntax(file_path: Path) -> Tuple[bool, str]:
    """Проверить синтаксис одного Python файла.
    
    Args:
        file_path: Путь к файлу для проверки.
        
    Returns:
        Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Проверка синтаксиса с помощью ast
        ast.parse(content, filename=str(file_path))
        return True, ""
        
    except SyntaxError as e:
        error_msg = (
            f"Синтаксическая ошибка в строке {e.lineno}: {e.msg}\n"
            f"Текст: {e.text.strip() if e.text else 'N/A'}"
        )
        return False, error_msg
    except Exception as e:
        return False, f"Ошибка при чтении файла: {e}"


def main():
    """Основная функция проверки синтаксиса."""
    project_root = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    print(f"Проверка синтаксиса {len(python_files)} Python файлов...\n")
    
    errors = []
    success_count = 0
    
    for file_path in python_files:
        relative_path = file_path.relative_to(project_root)
        print(f"Проверяю: {relative_path}", end=" ... ")
        
        is_valid, error_msg = check_file_syntax(file_path)
        
        if is_valid:
            print("✓ OK")
            success_count += 1
        else:
            print("✗ ОШИБКА")
            errors.append(f"\n{relative_path}:\n{error_msg}")
    
    print(f"\n{'='*50}")
    print(f"Результат проверки:")
    print(f"  Успешно: {success_count}/{len(python_files)}")
    print(f"  Ошибок: {len(errors)}")
    
    if errors:
        print(f"\nДетали ошибок:")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("\n🎉 Все файлы имеют корректный синтаксис!")
        sys.exit(0)


if __name__ == '__main__':
    main()