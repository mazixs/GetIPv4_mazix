# Python Best Practices: AI-Powered Development Guide

## 🤖 Мета-промпты для ИИ-помощников

### Основной промпт для code review
```
Ты - эксперт Python разработчик. Проанализируй код на соответствие лучшим практикам Python 3.13+. 
Проверь:
1. Соответствие PEP 8 и современным стандартам
2. Правильность типизации (используй встроенные типы, а не typing.List/Dict)
3. Безопасность и обработку ошибок
4. Производительность и идиоматичность
5. Современные возможности Python 3.13

Для каждого найденного нарушения предоставь:
- Описание проблемы
- Конкретное исправление
- Объяснение почему это лучше
```

### Промпт для рефакторинга
```
Рефактори этот Python код согласно современным практикам:
1. Используй встроенные типы вместо typing.List/Dict
2. Примени новые возможности Python 3.13
3. Улучши читаемость и производительность
4. Добавь правильную типизацию
5. Обеспечь безопасность

Покажи код до и после с объяснением изменений.
```

---

## 📋 Структура документа

1. [Стиль кода и форматирование](#стиль-кода)
2. [Современная типизация](#типизация)
3. [Структура проекта](#структура)
4. [Обработка ошибок](#ошибки)
5. [Безопасность](#безопасность)
6. [Производительность](#производительность)
7. [Тестирование](#тестирование)
8. [Современные возможности Python 3.13](#python313)

---

## 🎨 Стиль кода и форматирование {#стиль-кода}

### 🤖 Промпт для ИИ
```
Проверь код на соответствие PEP 8:
- Длина строк (88 символов для Black)
- Именование переменных, функций, классов
- Импорты и их порядок
- Пробелы и отступы
- Docstring-и в формате Google/NumPy

Исправь все нарушения и объясни изменения.
```

### ✅ Правильно
```python
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests
from mypackage import mymodule


class UserManager:
    """Управление пользователями системы.
    
    Args:
        database_url: URL подключения к базе данных
        timeout: Таймаут подключения в секундах
    """
    
    def __init__(self, database_url: str, timeout: int = 30) -> None:
        self.database_url = database_url
        self.timeout = timeout
    
    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Получить пользователя по ID.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            
        Returns:
            Словарь с данными пользователя или None если не найден
            
        Raises:
            ValueError: Если user_id меньше 1
        """
        if user_id < 1:
            raise ValueError("User ID должен быть положительным числом")
        
        # Логика получения пользователя
        return {"id": user_id, "name": "John Doe"}
```

### ❌ Неправильно
```python
import requests,os,sys
from mypackage import *
from typing import Dict,List,Optional

class userManager:
    def __init__(self,database_url,timeout=30):
        self.database_url=database_url
        self.timeout=timeout
    def getUserById(self,userId):
        if userId<1:raise ValueError("bad id")
        return {"id":userId,"name":"John Doe"}
```

### 🔍 Чек-лист
- [ ] Импорты отсортированы (isort)
- [ ] Код отформатирован (black)
- [ ] Длина строк не превышает 88 символов
- [ ] Используется snake_case для функций и переменных
- [ ] Используется PascalCase для классов
- [ ] Docstring-и присутствуют для всех публичных методов
- [ ] Используется `from __future__ import annotations`

---

## 🏷️ Современная типизация {#типизация}

### 🤖 Промпт для ИИ
```
Обнови типизацию в коде:
1. Замени typing.List/Dict/Tuple на встроенные list/dict/tuple
2. Используй Union[X, None] → X | None
3. Добавь TypedDict для структурированных словарей
4. Используй Generic для обобщенных классов
5. Примени новые возможности: TypeIs, Self, Unpack

Покажи до и после с объяснениями.
```

### ✅ Правильно (Python 3.13+)
```python
from __future__ import annotations

from typing import TypedDict, Generic, TypeVar, Self, TypeIs
from collections.abc import Sequence, Mapping

# Используем встроенные типы
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# TypedDict для структурированных данных
class UserData(TypedDict):
    id: int
    name: str
    email: str | None
    roles: list[str]

# Generic классы
T = TypeVar('T')

class Repository(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []
    
    def add(self, item: T) -> Self:
        self._items.append(item)
        return self
    
    def get_all(self) -> list[T]:
        return self._items.copy()

# TypeIs для type guards
def is_user_data(data: dict[str, any]) -> TypeIs[UserData]:
    required_keys = {'id', 'name'}
    return (
        isinstance(data, dict) and
        required_keys.issubset(data.keys()) and
        isinstance(data['id'], int) and
        isinstance(data['name'], str)
    )
```

### ❌ Устаревший подход
```python
from typing import List, Dict, Optional, Union

def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}

class Repository:
    def __init__(self):
        self._items: List = []
    
    def add(self, item) -> 'Repository':
        self._items.append(item)
        return self
```

### 🔍 Чек-лист типизации
- [ ] Используются встроенные типы (list, dict, tuple) вместо typing
- [ ] Union[X, None] заменен на X | None
- [ ] Добавлен `from __future__ import annotations`
- [ ] TypedDict используется для структурированных словарей
- [ ] Generic классы правильно типизированы
- [ ] Используется Self для методов, возвращающих экземпляр класса

---

## 🏗️ Структура проекта {#структура}

### 🤖 Промпт для ИИ
```
Проанализируй структуру Python проекта:
1. Проверь правильность организации модулей
2. Убедись в наличии __init__.py файлов
3. Проверь правильность импортов
4. Оцени разделение ответственности
5. Предложи улучшения архитектуры

Предоставь рекомендации по реструктуризации.
```

### ✅ Правильная структура
```
project/
├── pyproject.toml          # Современная конфигурация
├── README.md
├── src/
│   └── mypackage/
│       ├── __init__.py     # Публичный API
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── services.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       └── utils/
│           ├── __init__.py
│           └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   └── test_api/
└── docs/
```

### ✅ Правильные импорты
```python
# src/mypackage/__init__.py
"""MyPackage - описание пакета."""

from .core.models import User, Product
from .core.services import UserService, ProductService

__version__ = "1.0.0"
__all__ = ["User", "Product", "UserService", "ProductService"]

# src/mypackage/core/services.py
from __future__ import annotations

from .models import User
from ..utils.helpers import validate_email

class UserService:
    """Сервис для работы с пользователями."""
    
    def create_user(self, email: str, name: str) -> User:
        if not validate_email(email):
            raise ValueError("Некорректный email")
        return User(email=email, name=name)
```

### 🔍 Чек-лист структуры
- [ ] Используется src/ layout
- [ ] Все пакеты содержат __init__.py
- [ ] Публичный API определен в корневом __init__.py
- [ ] Относительные импорты используются внутри пакета
- [ ] Тесты отделены от исходного кода
- [ ] pyproject.toml используется для конфигурации

---

## ⚠️ Обработка ошибок {#ошибки}

### 🤖 Промпт для ИИ
```
Проанализируй обработку ошибок в коде:
1. Проверь использование специфичных исключений
2. Убедись в правильном использовании try/except
3. Проверь логирование ошибок
4. Оцени graceful degradation
5. Найди места где нужно добавить обработку ошибок

Предложи улучшения с примерами кода.
```

### ✅ Правильная обработка
```python
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Ошибка конфигурации приложения."""
    pass

class DataValidationError(Exception):
    """Ошибка валидации данных."""
    
    def __init__(self, field: str, value: Any, message: str) -> None:
        self.field = field
        self.value = value
        super().__init__(message)

def load_config(config_path: Path) -> dict[str, Any]:
    """Загрузить конфигурацию из файла.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Словарь с конфигурацией
        
    Raises:
        ConfigError: Если файл не найден или содержит ошибки
    """
    try:
        if not config_path.exists():
            raise ConfigError(f"Файл конфигурации не найден: {config_path}")
        
        with config_path.open('r', encoding='utf-8') as f:
            import json
            config = json.load(f)
            
        # Валидация обязательных полей
        required_fields = ['database_url', 'secret_key']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ConfigError(f"Отсутствуют обязательные поля: {missing_fields}")
            
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON в {config_path}: {e}")
        raise ConfigError(f"Некорректный JSON в файле конфигурации: {e}") from e
    except OSError as e:
        logger.error(f"Ошибка чтения файла {config_path}: {e}")
        raise ConfigError(f"Не удалось прочитать файл конфигурации: {e}") from e

def validate_user_age(age: int) -> None:
    """Валидация возраста пользователя.
    
    Args:
        age: Возраст пользователя
        
    Raises:
        DataValidationError: Если возраст некорректный
    """
    if not isinstance(age, int):
        raise DataValidationError(
            field='age',
            value=age,
            message=f"Возраст должен быть целым числом, получен {type(age).__name__}"
        )
    
    if age < 0:
        raise DataValidationError(
            field='age',
            value=age,
            message="Возраст не может быть отрицательным"
        )
    
    if age > 150:
        raise DataValidationError(
            field='age',
            value=age,
            message="Возраст не может превышать 150 лет"
        )
```

### ❌ Неправильная обработка
```python
def load_config(config_path):
    try:
        with open(config_path) as f:
            import json
            return json.load(f)
    except:
        return {}

def validate_user_age(age):
    if age < 0 or age > 150:
        raise Exception("Bad age")
```

### 🔍 Чек-лист обработки ошибок
- [ ] Используются специфичные исключения
- [ ] Избегается голый except:
- [ ] Ошибки логируются с контекстом
- [ ] Используется raise ... from для цепочки исключений
- [ ] Docstring-и документируют возможные исключения
- [ ] Реализован graceful degradation где возможно

---

## 🔒 Безопасность {#безопасность}

### 🤖 Промпт для ИИ
```
Проведи аудит безопасности Python кода:
1. Найди уязвимости инъекций (SQL, command, path traversal)
2. Проверь обработку пользовательского ввода
3. Оцени управление секретами
4. Найди небезопасные функции (eval, exec, pickle)
5. Проверь валидацию и санитизацию данных

Для каждой проблемы предоставь безопасную альтернативу.
```

### ✅ Безопасный код
```python
import os
import secrets
import hashlib
from pathlib import Path
from typing import Any
import sqlalchemy as sa
from sqlalchemy.orm import Session

# Безопасная работа с паролями
def hash_password(password: str) -> str:
    """Хеширование пароля с солью."""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Проверка пароля."""
    try:
        salt, hash_hex = stored_hash.split(':')
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(hash_hex, password_hash.hex())
    except ValueError:
        return False

# Безопасные SQL запросы
def get_user_by_email(session: Session, email: str) -> Any | None:
    """Получить пользователя по email (защищено от SQL инъекций)."""
    # Валидация входных данных
    if not email or '@' not in email or len(email) > 254:
        return None
    
    # Параметризованный запрос
    stmt = sa.text("SELECT * FROM users WHERE email = :email")
    result = session.execute(stmt, {"email": email})
    return result.fetchone()

# Безопасная работа с файлами
def read_user_file(filename: str, base_dir: Path) -> str:
    """Безопасное чтение пользовательского файла."""
    # Валидация имени файла
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Недопустимое имя файла")
    
    # Проверка расширения
    allowed_extensions = {'.txt', '.json', '.csv'}
    file_path = Path(filename)
    if file_path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Недопустимое расширение файла: {file_path.suffix}")
    
    # Построение безопасного пути
    safe_path = base_dir / filename
    
    # Проверка что файл находится в разрешенной директории
    try:
        safe_path.resolve().relative_to(base_dir.resolve())
    except ValueError:
        raise ValueError("Попытка доступа за пределы разрешенной директории")
    
    # Чтение файла
    try:
        return safe_path.read_text(encoding='utf-8')
    except OSError as e:
        raise ValueError(f"Ошибка чтения файла: {e}")

# Безопасная работа с секретами
def get_secret(secret_name: str) -> str:
    """Получение секрета из переменных окружения."""
    secret = os.getenv(secret_name)
    if not secret:
        raise ValueError(f"Секрет {secret_name} не найден в переменных окружения")
    return secret

# Генерация безопасных токенов
def generate_api_token() -> str:
    """Генерация криптографически стойкого API токена."""
    return secrets.token_urlsafe(32)
```

### ❌ Небезопасный код
```python
import os
import hashlib

# Небезопасное хеширование
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# SQL инъекция
def get_user(email):
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return execute_query(query)

# Path traversal
def read_file(filename):
    with open(f"/uploads/{filename}") as f:
        return f.read()

# Небезопасное выполнение кода
def calculate(expression):
    return eval(expression)
```

### 🔍 Чек-лист безопасности
- [ ] Пароли хешируются с солью (bcrypt/pbkdf2)
- [ ] SQL запросы параметризованы
- [ ] Пользовательский ввод валидируется
- [ ] Файловые пути проверяются на path traversal
- [ ] Секреты хранятся в переменных окружения
- [ ] Избегается eval(), exec(), pickle.loads()
- [ ] Используются криптографически стойкие генераторы

---

## ⚡ Производительность {#производительность}

### 🤖 Промпт для ИИ
```
Оптимизируй производительность Python кода:
1. Найди неэффективные алгоритмы и структуры данных
2. Проверь использование генераторов vs списков
3. Оцени необходимость кеширования
4. Найди возможности для асинхронности
5. Проверь memory leaks и избыточное потребление памяти

Предложи конкретные оптимизации с измерениями.
```

### ✅ Оптимизированный код
```python
from __future__ import annotations

import asyncio
from functools import lru_cache, cached_property
from collections import defaultdict, deque
from typing import Iterator, Any
from dataclasses import dataclass, field

@dataclass
class User:
    """Пользователь системы."""
    id: int
    name: str
    email: str
    _cache: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    
    @cached_property
    def display_name(self) -> str:
        """Отображаемое имя (кешируется)."""
        return f"{self.name} <{self.email}>"

# Эффективная работа с большими данными
def process_large_dataset(data: Iterator[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Обработка больших данных через генераторы."""
    for item in data:
        # Обработка по одному элементу без загрузки всего в память
        if item.get('active', False):
            yield {
                'id': item['id'],
                'processed_name': item['name'].strip().title(),
                'score': calculate_score(item)
            }

@lru_cache(maxsize=1000)
def calculate_score(item: dict[str, Any]) -> float:
    """Вычисление score с кешированием."""
    # Дорогостоящие вычисления
    base_score = item.get('base_score', 0)
    multiplier = item.get('multiplier', 1.0)
    return base_score * multiplier * 1.1

# Эффективная группировка
def group_users_by_domain(users: list[User]) -> dict[str, list[User]]:
    """Группировка пользователей по доменам email."""
    groups = defaultdict(list)
    for user in users:
        domain = user.email.split('@')[1] if '@' in user.email else 'unknown'
        groups[domain].append(user)
    return dict(groups)

# Асинхронная обработка
async def fetch_user_data(user_ids: list[int]) -> list[dict[str, Any]]:
    """Асинхронное получение данных пользователей."""
    async def fetch_single_user(user_id: int) -> dict[str, Any]:
        # Имитация асинхронного API вызова
        await asyncio.sleep(0.1)
        return {'id': user_id, 'name': f'User {user_id}'}
    
    # Параллельное выполнение запросов
    tasks = [fetch_single_user(user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)

# Эффективный поиск
class UserIndex:
    """Индекс для быстрого поиска пользователей."""
    
    def __init__(self) -> None:
        self._by_id: dict[int, User] = {}
        self._by_email: dict[str, User] = {}
        self._by_domain: defaultdict[str, list[User]] = defaultdict(list)
    
    def add_user(self, user: User) -> None:
        """Добавить пользователя в индекс."""
        self._by_id[user.id] = user
        self._by_email[user.email] = user
        
        domain = user.email.split('@')[1] if '@' in user.email else 'unknown'
        self._by_domain[domain].append(user)
    
    def find_by_id(self, user_id: int) -> User | None:
        """O(1) поиск по ID."""
        return self._by_id.get(user_id)
    
    def find_by_email(self, email: str) -> User | None:
        """O(1) поиск по email."""
        return self._by_email.get(email)
    
    def find_by_domain(self, domain: str) -> list[User]:
        """O(1) поиск по домену."""
        return self._by_domain[domain].copy()

# Эффективная работа со строками
def format_user_list(users: list[User]) -> str:
    """Форматирование списка пользователей."""
    # Используем join вместо конкатенации
    parts = []
    for user in users:
        parts.append(f"- {user.display_name}")
    return '\n'.join(parts)

# Batch обработка
def process_users_in_batches(
    users: list[User], 
    batch_size: int = 100
) -> Iterator[list[dict[str, Any]]]:
    """Обработка пользователей батчами."""
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        yield [{'id': user.id, 'name': user.name} for user in batch]
```

### ❌ Неэффективный код
```python
# Неэффективная обработка данных
def process_data(data):
    result = []
    for item in data:
        if item['active']:
            result.append(process_item(item))
    return result

# Неэффективная группировка
def group_by_domain(users):
    groups = {}
    for user in users:
        domain = user.email.split('@')[1]
        if domain not in groups:
            groups[domain] = []
        groups[domain].append(user)
    return groups

# Неэффективный поиск
def find_user_by_id(users, user_id):
    for user in users:
        if user.id == user_id:
            return user
    return None
```

### 🔍 Чек-лист производительности
- [ ] Используются генераторы для больших данных
- [ ] Применяется кеширование для дорогих операций
- [ ] Используются эффективные структуры данных
- [ ] Асинхронность применяется для I/O операций
- [ ] Избегается преждевременная оптимизация
- [ ] Профилируется код перед оптимизацией

---

## 🧪 Тестирование {#тестирование}

### 🤖 Промпт для ИИ
```
Проанализируй тестовое покрытие и качество тестов:
1. Проверь структуру и организацию тестов
2. Оцени покрытие edge cases
3. Найди дублирование в тестах
4. Проверь использование fixtures и mocks
5. Оцени читаемость и поддерживаемость тестов

Предложи улучшения и дополнительные тесты.
```

### ✅ Качественные тесты
```python
from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import Any

from myapp.services import UserService
from myapp.models import User
from myapp.exceptions import UserNotFoundError, ValidationError


class TestUserService:
    """Тесты для UserService."""
    
    @pytest.fixture
    def mock_database(self) -> Mock:
        """Mock базы данных."""
        return Mock()
    
    @pytest.fixture
    def user_service(self, mock_database: Mock) -> UserService:
        """Экземпляр UserService с mock базой."""
        return UserService(database=mock_database)
    
    @pytest.fixture
    def sample_user_data(self) -> dict[str, Any]:
        """Образец данных пользователя."""
        return {
            'id': 1,
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }
    
    def test_create_user_success(self, user_service: UserService, sample_user_data: dict[str, Any]) -> None:
        """Тест успешного создания пользователя."""
        # Arrange
        user_service.database.save.return_value = sample_user_data
        
        # Act
        result = user_service.create_user(
            name=sample_user_data['name'],
            email=sample_user_data['email'],
            age=sample_user_data['age']
        )
        
        # Assert
        assert result.id == sample_user_data['id']
        assert result.name == sample_user_data['name']
        assert result.email == sample_user_data['email']
        user_service.database.save.assert_called_once()
    
    @pytest.mark.parametrize('invalid_email', [
        '',
        'invalid-email',
        'test@',
        '@example.com',
        'test..test@example.com',
        'a' * 250 + '@example.com'  # слишком длинный
    ])
    def test_create_user_invalid_email(self, user_service: UserService, invalid_email: str) -> None:
        """Тест создания пользователя с некорректным email."""
        with pytest.raises(ValidationError, match="Некорректный email"):
            user_service.create_user(
                name='John Doe',
                email=invalid_email,
                age=30
            )
    
    @pytest.mark.parametrize('invalid_age', [-1, 0, 151, 'not_a_number', None])
    def test_create_user_invalid_age(self, user_service: UserService, invalid_age: Any) -> None:
        """Тест создания пользователя с некорректным возрастом."""
        with pytest.raises(ValidationError, match="Некорректный возраст"):
            user_service.create_user(
                name='John Doe',
                email='john@example.com',
                age=invalid_age
            )
    
    def test_get_user_by_id_success(self, user_service: UserService, sample_user_data: dict[str, Any]) -> None:
        """Тест успешного получения пользователя по ID."""
        # Arrange
        user_service.database.find_by_id.return_value = sample_user_data
        
        # Act
        result = user_service.get_user_by_id(1)
        
        # Assert
        assert result.id == sample_user_data['id']
        user_service.database.find_by_id.assert_called_once_with(1)
    
    def test_get_user_by_id_not_found(self, user_service: UserService) -> None:
        """Тест получения несуществующего пользователя."""
        # Arrange
        user_service.database.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError, match="Пользователь с ID 999 не найден"):
            user_service.get_user_by_id(999)
    
    @pytest.mark.asyncio
    async def test_async_update_user(self, user_service: UserService) -> None:
        """Тест асинхронного обновления пользователя."""
        # Arrange
        user_service.database.update_async = AsyncMock(return_value=True)
        
        # Act
        result = await user_service.update_user_async(1, {'name': 'Jane Doe'})
        
        # Assert
        assert result is True
        user_service.database.update_async.assert_called_once_with(1, {'name': 'Jane Doe'})
    
    def test_database_error_handling(self, user_service: UserService) -> None:
        """Тест обработки ошибок базы данных."""
        # Arrange
        user_service.database.find_by_id.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            user_service.get_user_by_id(1)
    
    @patch('myapp.services.send_email')
    def test_user_creation_sends_welcome_email(self, mock_send_email: Mock, user_service: UserService) -> None:
        """Тест отправки приветственного email при создании пользователя."""
        # Arrange
        user_service.database.save.return_value = {'id': 1, 'name': 'John', 'email': 'john@example.com'}
        
        # Act
        user_service.create_user('John', 'john@example.com', 30)
        
        # Assert
        mock_send_email.assert_called_once_with(
            to='john@example.com',
            subject='Добро пожаловать!',
            template='welcome'
        )


# Интеграционные тесты
class TestUserServiceIntegration:
    """Интеграционные тесты для UserService."""
    
    @pytest.fixture(scope='session')
    def test_database(self):
        """Тестовая база данных."""
        # Настройка тестовой БД
        pass
    
    def test_full_user_lifecycle(self, test_database) -> None:
        """Тест полного жизненного цикла пользователя."""
        service = UserService(database=test_database)
        
        # Создание
        user = service.create_user('John Doe', 'john@example.com', 30)
        assert user.id is not None
        
        # Получение
        retrieved_user = service.get_user_by_id(user.id)
        assert retrieved_user.name == 'John Doe'
        
        # Обновление
        service.update_user(user.id, {'name': 'Jane Doe'})
        updated_user = service.get_user_by_id(user.id)
        assert updated_user.name == 'Jane Doe'
        
        # Удаление
        service.delete_user(user.id)
        with pytest.raises(UserNotFoundError):
            service.get_user_by_id(user.id)


# Property-based тесты
from hypothesis import given, strategies as st

class TestUserValidation:
    """Property-based тесты для валидации пользователей."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_valid_names_accepted(self, name: str) -> None:
        """Тест что валидные имена принимаются."""
        # Предполагаем что любая непустая строка до 100 символов валидна
        if name.strip():  # не пустая после trim
            # Тест должен пройти
            assert UserService.validate_name(name) is True
    
    @given(st.emails())
    def test_valid_emails_accepted(self, email: str) -> None:
        """Тест что валидные email принимаются."""
        assert UserService.validate_email(email) is True
```

### 🔍 Чек-лист тестирования
- [ ] Тесты организованы в классы по функциональности
- [ ] Используются fixtures для переиспользования
- [ ] Покрыты edge cases и error cases
- [ ] Используется parametrize для множественных входных данных
- [ ] Асинхронные функции тестируются с @pytest.mark.asyncio
- [ ] Используются mocks для внешних зависимостей
- [ ] Есть интеграционные тесты
- [ ] Применяется property-based тестирование где уместно

---

## 🚀 Современные возможности Python 3.13 {#python313}

### 🤖 Промпт для ИИ
```
Обнови код для использования новых возможностей Python 3.13:
1. Используй новый REPL и улучшенные сообщения об ошибках
2. Примени улучшения в typing (TypeIs, новые generic)
3. Используй новые возможности pathlib
4. Примени улучшения в asyncio
5. Используй новые методы str и dict

Покажи примеры до и после с объяснениями.
```

### ✅ Python 3.13+ возможности
```python
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TypeIs, Generic, TypeVar, Self
from collections.abc import Sequence
from dataclasses import dataclass

# Улучшенная типизация с TypeIs
def is_positive_int(value: object) -> TypeIs[int]:
    """Type guard для положительных целых чисел."""
    return isinstance(value, int) and value > 0

def process_positive_numbers(values: list[object]) -> list[int]:
    """Обработка только положительных чисел."""
    result = []
    for value in values:
        if is_positive_int(value):
            # Здесь TypeChecker знает что value: int
            result.append(value * 2)
    return result

# Улучшенные Generic классы
T = TypeVar('T')
U = TypeVar('U')

@dataclass
class Result(Generic[T, U]):
    """Результат операции с данными или ошибкой."""
    success: bool
    data: T | None = None
    error: U | None = None
    
    @classmethod
    def ok(cls, data: T) -> Self:
        """Создать успешный результат."""
        return cls(success=True, data=data)
    
    @classmethod
    def error(cls, error: U) -> Self:
        """Создать результат с ошибкой."""
        return cls(success=False, error=error)
    
    def map(self, func: callable[[T], U]) -> Result[U, U]:
        """Применить функцию к данным если успешно."""
        if self.success and self.data is not None:
            try:
                return Result.ok(func(self.data))
            except Exception as e:
                return Result.error(e)
        return Result.error(self.error)

# Улучшенная работа с Path (Python 3.13)
def process_config_files(config_dir: Path) -> dict[str, dict]:
    """Обработка конфигурационных файлов."""
    configs = {}
    
    # Новые методы Path в Python 3.13
    if not config_dir.is_dir():
        return configs
    
    for config_file in config_dir.glob('*.json'):
        try:
            # Улучшенная обработка ошибок в Python 3.13
            config_data = config_file.read_text(encoding='utf-8')
            import json
            configs[config_file.stem] = json.loads(config_data)
        except (OSError, json.JSONDecodeError) as e:
            # Более информативные сообщения об ошибках
            print(f"Ошибка загрузки {config_file}: {e}")
            continue
    
    return configs

# Улучшенный asyncio (Python 3.13)
class AsyncDataProcessor:
    """Асинхронный процессор данных."""
    
    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(10)  # Ограничение параллельности
    
    async def process_item(self, item: dict) -> dict:
        """Обработка одного элемента."""
        async with self._semaphore:
            # Имитация асинхронной обработки
            await asyncio.sleep(0.1)
            return {'id': item['id'], 'processed': True}
    
    async def process_batch(self, items: Sequence[dict]) -> list[dict]:
        """Обработка батча элементов."""
        # Используем TaskGroup для лучшего управления задачами (Python 3.11+)
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self.process_item(item)) for item in items]
        
        return [task.result() for task in tasks]
    
    async def process_stream(self, items: Sequence[dict]) -> list[dict]:
        """Потоковая обработка с контролем памяти."""
        results = []
        batch_size = 50
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self.process_batch(batch)
            results.extend(batch_results)
            
            # Принудительная сборка мусора для больших данных
            if i % (batch_size * 10) == 0:
                import gc
                gc.collect()
        
        return results

# Улучшенная работа со строками (Python 3.13)
def format_user_data(users: list[dict]) -> str:
    """Форматирование данных пользователей."""
    lines = []
    
    for user in users:
        # Новые методы строк в Python 3.13
        name = user.get('name', '').strip()
        email = user.get('email', '').strip().lower()
        
        if name and email:
            # Улучшенное форматирование
            line = f"{name:<20} | {email:<30} | ID: {user.get('id', 'N/A')}"
            lines.append(line)
    
    return '\n'.join(lines)

# Контекстные менеджеры с улучшенной обработкой ошибок
class DatabaseConnection:
    """Подключение к базе данных с автоматическим управлением."""
    
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self.connection = None
    
    async def __aenter__(self) -> Self:
        """Асинхронное подключение."""
        try:
            # Имитация подключения к БД
            await asyncio.sleep(0.1)
            self.connection = f"Connected to {self.connection_string}"
            return self
        except Exception as e:
            # Улучшенная обработка ошибок в Python 3.13
            raise ConnectionError(f"Не удалось подключиться к БД: {e}") from e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Автоматическое закрытие подключения."""
        if self.connection:
            await asyncio.sleep(0.05)  # Имитация закрытия
            self.connection = None
    
    async def execute(self, query: str) -> list[dict]:
        """Выполнение запроса."""
        if not self.connection:
            raise RuntimeError("Нет подключения к БД")
        
        # Имитация выполнения запроса
        await asyncio.sleep(0.1)
        return [{'result': f'Query executed: {query}'}]

# Пример использования новых возможностей
async def main() -> None:
    """Демонстрация новых возможностей Python 3.13."""
    # Асинхронная обработка данных
    processor = AsyncDataProcessor()
    test_data = [{'id': i} for i in range(100)]
    
    results = await processor.process_stream(test_data)
    print(f"Обработано {len(results)} элементов")
    
    # Работа с базой данных
    async with DatabaseConnection("postgresql://localhost/test") as db:
        data = await db.execute("SELECT * FROM users")
        print(f"Получено записей: {len(data)}")
    
    # Обработка конфигураций
    config_dir = Path("./configs")
    configs = process_config_files(config_dir)
    print(f"Загружено конфигураций: {len(configs)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 🔍 Чек-лист Python 3.13
- [ ] Используется `from __future__ import annotations`
- [ ] Применяется TypeIs для type guards
- [ ] Используются встроенные типы вместо typing
- [ ] Применяется Self для методов класса
- [ ] Используются новые возможности asyncio
- [ ] Применяются улучшения в обработке ошибок
- [ ] Используются новые методы pathlib

---

## 📚 Заключение и рекомендации

### 🎯 Основные принципы

1. **Читаемость превыше всего** - код читается чаще чем пишется
2. **Явное лучше неявного** - следуйте Zen of Python
3. **Безопасность по умолчанию** - всегда думайте о безопасности
4. **Тестируемость** - пишите код который легко тестировать
5. **Производительность** - оптимизируйте только после измерений

### 🔄 Процесс разработки

1. **Планирование** - продумайте архитектуру заранее
2. **Итеративная разработка** - маленькие изменения, частые коммиты
3. **Code Review** - используйте ИИ и коллег для проверки
4. **Автоматизация** - настройте CI/CD, линтеры, форматтеры
5. **Документация** - документируйте API и сложную логику

### 🛠️ Инструменты

```bash
# Обязательные инструменты
pip install black isort mypy pytest ruff

# Настройка pre-commit
pre-commit install

# Запуск проверок
black .
isort .
mypy .
ruff check .
pytest
```

### 📖 Дополнительные ресурсы

- [PEP 8](https://peps.python.org/pep-0008/) - Стиль кода
- [PEP 484](https://peps.python.org/pep-0484/) - Type Hints
- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/)
- [Real Python](https://realpython.com/) - Практические руководства
- [Python Security](https://python-security.readthedocs.io/) - Безопасность

---

*Этот документ регулярно обновляется с учетом новых версий Python и изменений в лучших практиках. Последнее обновление: Python 3.13.5*