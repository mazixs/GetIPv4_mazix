# План рефакторинга проекта GetIPv4_mazix

## 🎯 Цель рефакторинга

Привести проект в соответствие с современными лучшими практиками Python разработки, улучшить читаемость, безопасность и поддерживаемость кода.

## 📋 Этапы рефакторинга

### Этап 1: Структура проекта и конфигурация (Высокий приоритет)

#### 1.1 Реструктуризация проекта

**Текущая структура:**
```
GetIPv4_mazix/
├── get_ipv4.py
├── config_handler.py
├── requirements.txt
├── README.md
├── tests/
└── docs/
```

**Целевая структура:**
```
GetIPv4_mazix/
├── pyproject.toml
├── README.md
├── src/
│   └── getipv4/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── resolver.py
│       │   └── network.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── handler.py
│       ├── exceptions.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   └── test_config/
├── docs/
└── config/
    └── config.ini.example
```

#### 1.2 Создание pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "getipv4-mazix"
version = "1.0.0"
description = "IPv4 address resolution and route generation tool"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "mazix"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    # Добавить зависимости после анализа кода
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "isort>=5.0",
    "mypy>=1.0",
    "ruff>=0.1.0",
]

[project.scripts]
getipv4 = "getipv4.cli:main"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"

[tool.ruff]
select = ["E", "F", "W", "C90", "I", "N", "UP", "S", "B", "A", "C4", "T20"]
ignore = []
line-length = 88
target-version = "py311"
```

### Этап 2: Типизация и современный Python (Высокий приоритет)

#### 2.1 Добавление типизации к основным модулям

**Файл: src/getipv4/exceptions.py**
```python
"""Исключения для модуля getipv4."""

from __future__ import annotations


class GetIPv4Error(Exception):
    """Базовое исключение для модуля getipv4."""
    pass


class DomainResolutionError(GetIPv4Error):
    """Ошибка разрешения доменного имени."""
    
    def __init__(self, domain: str, reason: str) -> None:
        self.domain = domain
        self.reason = reason
        super().__init__(f"Не удалось разрешить домен '{domain}': {reason}")


class NetworkCalculationError(GetIPv4Error):
    """Ошибка вычисления сетевых параметров."""
    
    def __init__(self, ip: str, subnet: str, reason: str) -> None:
        self.ip = ip
        self.subnet = subnet
        self.reason = reason
        super().__init__(
            f"Ошибка вычисления сети для IP '{ip}' с маской '{subnet}': {reason}"
        )


class ConfigurationError(GetIPv4Error):
    """Ошибка конфигурации приложения."""
    pass


class FileOperationError(GetIPv4Error):
    """Ошибка операций с файлами."""
    
    def __init__(self, file_path: str, operation: str, reason: str) -> None:
        self.file_path = file_path
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"Ошибка {operation} файла '{file_path}': {reason}"
        )
```

**Файл: src/getipv4/core/resolver.py**
```python
"""Модуль для разрешения доменных имен в IPv4 адреса."""

from __future__ import annotations

import logging
import socket
from pathlib import Path
from typing import TypedDict

from ..exceptions import DomainResolutionError, FileOperationError

logger = logging.getLogger(__name__)


class DomainInfo(TypedDict):
    """Информация о домене."""
    domain: str
    ipv4_addresses: list[str]
    resolved_via_dns: list[str]


class DNSResolver:
    """Класс для разрешения доменных имен через DNS серверы."""
    
    def __init__(self, dns_servers: list[str] | None = None) -> None:
        """Инициализация DNS resolver.
        
        Args:
            dns_servers: Список DNS серверов. Если None, используется системный.
        """
        self.dns_servers = dns_servers or ["127.0.0.1"]
        self._cache: dict[str, list[str]] = {}
    
    def resolve_domain(self, domain: str) -> list[str]:
        """Разрешить домен в список IPv4 адресов.
        
        Args:
            domain: Доменное имя для разрешения
            
        Returns:
            Список IPv4 адресов
            
        Raises:
            DomainResolutionError: Если не удалось разрешить домен
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("Домен должен быть непустой строкой")
        
        # Проверяем кеш
        if domain in self._cache:
            logger.debug(f"Домен {domain} найден в кеше")
            return self._cache[domain].copy()
        
        ipv4_addresses: list[str] = []
        errors: list[str] = []
        
        for dns_server in self.dns_servers:
            try:
                addresses = self._resolve_via_dns(domain, dns_server)
                ipv4_addresses.extend(addresses)
                logger.debug(f"Домен {domain} разрешен через {dns_server}: {addresses}")
            except socket.gaierror as e:
                error_msg = f"DNS {dns_server}: {e}"
                errors.append(error_msg)
                logger.warning(f"Не удалось разрешить {domain} через {dns_server}: {e}")
            except Exception as e:
                error_msg = f"DNS {dns_server}: неожиданная ошибка {e}"
                errors.append(error_msg)
                logger.error(
                    f"Неожиданная ошибка при разрешении {domain} через {dns_server}: {e}",
                    exc_info=True
                )
        
        # Удаляем дубликаты, сохраняя порядок
        unique_addresses = list(dict.fromkeys(ipv4_addresses))
        
        if not unique_addresses:
            raise DomainResolutionError(
                domain=domain,
                reason=f"Все DNS серверы недоступны: {'; '.join(errors)}"
            )
        
        # Кешируем результат
        self._cache[domain] = unique_addresses.copy()
        
        return unique_addresses
    
    def _resolve_via_dns(self, domain: str, dns_server: str) -> list[str]:
        """Разрешить домен через конкретный DNS сервер.
        
        Args:
            domain: Доменное имя
            dns_server: IP адрес DNS сервера
            
        Returns:
            Список IPv4 адресов
            
        Raises:
            socket.gaierror: Если не удалось разрешить домен
        """
        # Временно устанавливаем DNS сервер
        original_dns = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5.0)  # 5 секунд таймаут
        
        try:
            # Используем gethostbyname_ex для получения всех адресов
            _, _, addresses = socket.gethostbyname_ex(domain)
            return [addr for addr in addresses if self._is_ipv4(addr)]
        finally:
            socket.setdefaulttimeout(original_dns)
    
    @staticmethod
    def _is_ipv4(address: str) -> bool:
        """Проверить, является ли адрес IPv4.
        
        Args:
            address: IP адрес для проверки
            
        Returns:
            True если адрес является IPv4
        """
        try:
            import ipaddress
            ip = ipaddress.ip_address(address)
            return isinstance(ip, ipaddress.IPv4Address)
        except ValueError:
            return False
    
    def clear_cache(self) -> None:
        """Очистить кеш разрешенных доменов."""
        self._cache.clear()
        logger.debug("Кеш DNS resolver очищен")


def read_domains_from_file(file_path: str | Path) -> list[str]:
    """Безопасное чтение списка доменов из файла.
    
    Args:
        file_path: Путь к файлу с доменами
        
    Returns:
        Список доменных имен
        
    Raises:
        FileOperationError: Если произошла ошибка при работе с файлом
        ValueError: Если путь к файлу некорректный
    """
    path = Path(file_path)
    
    # Валидация пути
    if not path.exists():
        raise FileOperationError(
            file_path=str(path),
            operation="чтение",
            reason="файл не существует"
        )
    
    if not path.is_file():
        raise FileOperationError(
            file_path=str(path),
            operation="чтение",
            reason="путь не является файлом"
        )
    
    # Проверка расширения файла
    allowed_extensions = {".txt", ".list", ".domains"}
    if path.suffix.lower() not in allowed_extensions:
        logger.warning(
            f"Файл {path} имеет нестандартное расширение {path.suffix}. "
            f"Рекомендуемые: {', '.join(allowed_extensions)}"
        )
    
    try:
        with path.open('r', encoding='utf-8') as file:
            content = file.read()
        
        # Обработка содержимого
        domains = [
            line.strip() 
            for line in content.splitlines() 
            if line.strip() and not line.strip().startswith('#')
        ]
        
        logger.info(f"Загружено {len(domains)} доменов из файла {path}")
        return domains
        
    except OSError as e:
        raise FileOperationError(
            file_path=str(path),
            operation="чтение",
            reason=str(e)
        ) from e
    except UnicodeDecodeError as e:
        raise FileOperationError(
            file_path=str(path),
            operation="декодирование",
            reason=f"файл не в UTF-8 кодировке: {e}"
        ) from e
```

#### 2.2 Рефакторинг конфигурационного модуля

**Файл: src/getipv4/config/handler.py**
```python
"""Обработчик конфигурации приложения."""

from __future__ import annotations

import configparser
import ipaddress
import logging
from pathlib import Path
from typing import TypedDict

from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class AppSettings(TypedDict):
    """Настройки приложения."""
    use_local_dns: bool
    use_external_dns: bool
    dns_servers: list[str]
    domains_files: list[str]
    output_domain_ip: str
    output_only_ipv4: str
    output_keenetic: str
    subnet_mask: str


class AppConfig:
    """Класс для работы с конфигурацией приложения."""
    
    def __init__(self, config_path: str | Path) -> None:
        """Инициализация конфигурации.
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Raises:
            ConfigurationError: Если конфигурация некорректна
        """
        self.config_path = Path(config_path)
        self._config = configparser.ConfigParser()
        self._settings: AppSettings | None = None
        
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """Загрузить конфигурацию из файла.
        
        Raises:
            ConfigurationError: Если не удалось загрузить конфигурацию
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Файл конфигурации не найден: {self.config_path}"
            )
        
        try:
            with self.config_path.open('r', encoding='utf-8') as f:
                self._config.read_file(f)
        except OSError as e:
            raise ConfigurationError(
                f"Ошибка чтения файла конфигурации {self.config_path}: {e}"
            ) from e
        except configparser.Error as e:
            raise ConfigurationError(
                f"Ошибка парсинга конфигурации {self.config_path}: {e}"
            ) from e
        
        if not self._config.sections():
            raise ConfigurationError(
                f"Файл конфигурации {self.config_path} пуст или некорректен"
            )
    
    def _validate_config(self) -> None:
        """Валидация конфигурации.
        
        Raises:
            ConfigurationError: Если конфигурация некорректна
        """
        if 'settings' not in self._config:
            raise ConfigurationError("Отсутствует секция [settings] в конфигурации")
        
        settings = self._config['settings']
        
        # Валидация обязательных полей
        required_fields = {
            'use_local_dns': self._validate_boolean,
            'use_external_dns': self._validate_boolean,
            'domains_files': self._validate_non_empty_string,
            'output_domain_ip': self._validate_non_empty_string,
            'subnet_mask': self._validate_subnet_mask,
        }
        
        for field, validator in required_fields.items():
            if field not in settings:
                raise ConfigurationError(f"Отсутствует обязательное поле '{field}'")
            
            try:
                validator(settings[field], field)
            except ValueError as e:
                raise ConfigurationError(f"Некорректное значение для '{field}': {e}") from e
        
        # Специальная валидация для DNS серверов
        use_external_dns = settings.getboolean('use_external_dns')
        dns_servers = settings.get('dns_servers', '').strip()
        
        if use_external_dns and not dns_servers:
            raise ConfigurationError(
                "Поле 'dns_servers' должно быть заполнено при use_external_dns=1"
            )
        
        if dns_servers:
            self._validate_dns_servers(dns_servers)
    
    @staticmethod
    def _validate_boolean(value: str, field_name: str) -> None:
        """Валидация булевого значения."""
        if value not in ('0', '1', 'true', 'false', 'yes', 'no'):
            raise ValueError(f"'{field_name}' должно быть 0/1, true/false, или yes/no")
    
    @staticmethod
    def _validate_non_empty_string(value: str, field_name: str) -> None:
        """Валидация непустой строки."""
        if not value.strip():
            raise ValueError(f"'{field_name}' не может быть пустым")
    
    @staticmethod
    def _validate_subnet_mask(value: str, field_name: str) -> None:
        """Валидация маски подсети."""
        value = value.strip()
        
        # Проверяем CIDR нотацию
        if value.startswith('/'):
            try:
                prefix = int(value[1:])
                if not 0 <= prefix <= 32:
                    raise ValueError("Префикс должен быть от 0 до 32")
                return
            except ValueError as e:
                raise ValueError(f"Некорректный CIDR префикс: {e}") from e
        
        # Проверяем числовой префикс
        if value.isdigit():
            prefix = int(value)
            if not 0 <= prefix <= 32:
                raise ValueError("Префикс должен быть от 0 до 32")
            return
        
        # Проверяем полную маску
        try:
            ipaddress.IPv4Network(f"192.168.1.0/{value}", strict=False)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Некорректная маска подсети: {e}") from e
    
    @staticmethod
    def _validate_dns_servers(dns_servers: str) -> None:
        """Валидация списка DNS серверов."""
        servers = [s.strip() for s in dns_servers.split(',') if s.strip()]
        
        for server in servers:
            try:
                ipaddress.IPv4Address(server)
            except ipaddress.AddressValueError as e:
                raise ValueError(f"Некорректный IP адрес DNS сервера '{server}': {e}") from e
    
    def get_settings(self) -> AppSettings:
        """Получить все настройки как типизированный словарь.
        
        Returns:
            Словарь с настройками приложения
        """
        if self._settings is None:
            settings = self._config['settings']
            
            # Формируем список DNS серверов
            dns_servers = []
            if settings.getboolean('use_local_dns'):
                dns_servers.append('127.0.0.1')
            
            if settings.getboolean('use_external_dns'):
                external_dns = settings.get('dns_servers', '').strip()
                if external_dns:
                    dns_servers.extend(
                        s.strip() for s in external_dns.split(',') if s.strip()
                    )
            
            self._settings = AppSettings(
                use_local_dns=settings.getboolean('use_local_dns'),
                use_external_dns=settings.getboolean('use_external_dns'),
                dns_servers=dns_servers,
                domains_files=[
                    f.strip() for f in settings['domains_files'].split(',') if f.strip()
                ],
                output_domain_ip=settings['output_domain_ip'],
                output_only_ipv4=settings.get('output_only_ipv4', ''),
                output_keenetic=settings.get('output_keenetic', ''),
                subnet_mask=settings['subnet_mask'],
            )
        
        return self._settings
    
    def get_dns_servers(self) -> list[str]:
        """Получить список DNS серверов.
        
        Returns:
            Список IP адресов DNS серверов
        """
        return self.get_settings()['dns_servers'].copy()
    
    def get_domains_files(self) -> list[str]:
        """Получить список файлов с доменами.
        
        Returns:
            Список путей к файлам с доменами
        """
        return self.get_settings()['domains_files'].copy()
    
    def get_subnet_mask(self) -> str:
        """Получить маску подсети.
        
        Returns:
            Маска подсети в любом поддерживаемом формате
        """
        return self.get_settings()['subnet_mask']
    
    def get_output_files(self) -> dict[str, str]:
        """Получить пути к выходным файлам.
        
        Returns:
            Словарь с путями к выходным файлам
        """
        settings = self.get_settings()
        return {
            'domain_ip': settings['output_domain_ip'],
            'only_ipv4': settings['output_only_ipv4'],
            'keenetic': settings['output_keenetic'],
        }
```

### Этап 3: Улучшение обработки ошибок и безопасности (Высокий приоритет)

#### 3.1 Безопасная работа с файлами

**Файл: src/getipv4/core/network.py**
```python
"""Модуль для работы с сетевыми вычислениями."""

from __future__ import annotations

import ipaddress
import logging
from pathlib import Path
from typing import NamedTuple

from ..exceptions import NetworkCalculationError, FileOperationError

logger = logging.getLogger(__name__)


class NetworkInfo(NamedTuple):
    """Информация о сети."""
    network_address: str
    netmask: str
    prefix_length: int
    broadcast_address: str


class NetworkCalculator:
    """Класс для вычисления сетевых параметров."""
    
    @staticmethod
    def calculate_network(ip_address: str, subnet_mask: str) -> NetworkInfo:
        """Вычислить параметры сети для IP адреса и маски.
        
        Args:
            ip_address: IP адрес
            subnet_mask: Маска подсети (CIDR, префикс или полная маска)
            
        Returns:
            Информация о сети
            
        Raises:
            NetworkCalculationError: Если не удалось вычислить параметры сети
        """
        try:
            # Нормализуем маску подсети
            normalized_mask = NetworkCalculator._normalize_subnet_mask(subnet_mask)
            
            # Создаем объект сети
            network = ipaddress.IPv4Network(f"{ip_address}/{normalized_mask}", strict=False)
            
            return NetworkInfo(
                network_address=str(network.network_address),
                netmask=str(network.netmask),
                prefix_length=network.prefixlen,
                broadcast_address=str(network.broadcast_address),
            )
            
        except (ipaddress.AddressValueError, ValueError) as e:
            raise NetworkCalculationError(
                ip=ip_address,
                subnet=subnet_mask,
                reason=str(e)
            ) from e
    
    @staticmethod
    def _normalize_subnet_mask(subnet_mask: str) -> str:
        """Нормализовать маску подсети к CIDR формату.
        
        Args:
            subnet_mask: Маска в любом поддерживаемом формате
            
        Returns:
            Маска в CIDR формате (например, "24")
            
        Raises:
            ValueError: Если маска некорректна
        """
        mask = subnet_mask.strip()
        
        # Уже CIDR без слеша
        if mask.isdigit():
            prefix = int(mask)
            if 0 <= prefix <= 32:
                return mask
            raise ValueError(f"Некорректный CIDR префикс: {prefix}")
        
        # CIDR с слешем
        if mask.startswith('/'):
            prefix_str = mask[1:]
            if prefix_str.isdigit():
                prefix = int(prefix_str)
                if 0 <= prefix <= 32:
                    return prefix_str
            raise ValueError(f"Некорректный CIDR префикс: {mask}")
        
        # Полная маска (например, 255.255.255.0)
        try:
            # Создаем временную сеть для получения префикса
            temp_network = ipaddress.IPv4Network(f"192.168.1.0/{mask}", strict=False)
            return str(temp_network.prefixlen)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Некорректная маска подсети: {e}") from e


class FileManager:
    """Класс для безопасной работы с файлами."""
    
    def __init__(self, base_directory: str | Path | None = None) -> None:
        """Инициализация файлового менеджера.
        
        Args:
            base_directory: Базовая директория для операций с файлами
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.base_directory = self.base_directory.resolve()
    
    def safe_write_file(
        self, 
        file_path: str | Path, 
        content: str, 
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> None:
        """Безопасная запись в файл.
        
        Args:
            file_path: Путь к файлу
            content: Содержимое для записи
            encoding: Кодировка файла
            create_dirs: Создавать ли родительские директории
            
        Raises:
            FileOperationError: Если произошла ошибка при записи
            ValueError: Если путь небезопасен
        """
        safe_path = self._validate_and_resolve_path(file_path)
        
        try:
            if create_dirs:
                safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Атомарная запись через временный файл
            temp_path = safe_path.with_suffix(safe_path.suffix + '.tmp')
            
            with temp_path.open('w', encoding=encoding) as f:
                f.write(content)
            
            # Перемещаем временный файл на место целевого
            temp_path.replace(safe_path)
            
            logger.info(f"Файл успешно записан: {safe_path}")
            
        except OSError as e:
            # Очищаем временный файл если он остался
            temp_path = safe_path.with_suffix(safe_path.suffix + '.tmp')
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            
            raise FileOperationError(
                file_path=str(safe_path),
                operation="запись",
                reason=str(e)
            ) from e
    
    def safe_remove_file(self, file_path: str | Path) -> bool:
        """Безопасное удаление файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл был удален, False если файл не существовал
            
        Raises:
            FileOperationError: Если произошла ошибка при удалении
            ValueError: Если путь небезопасен
        """
        safe_path = self._validate_and_resolve_path(file_path)
        
        if not safe_path.exists():
            logger.debug(f"Файл для удаления не существует: {safe_path}")
            return False
        
        if not safe_path.is_file():
            raise FileOperationError(
                file_path=str(safe_path),
                operation="удаление",
                reason="путь не является файлом"
            )
        
        try:
            safe_path.unlink()
            logger.info(f"Файл удален: {safe_path}")
            return True
        except OSError as e:
            raise FileOperationError(
                file_path=str(safe_path),
                operation="удаление",
                reason=str(e)
            ) from e
    
    def _validate_and_resolve_path(self, file_path: str | Path) -> Path:
        """Валидация и разрешение пути к файлу.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Безопасный абсолютный путь
            
        Raises:
            ValueError: Если путь небезопасен
        """
        path = Path(file_path)
        
        # Проверяем на опасные компоненты пути
        if '..' in path.parts:
            raise ValueError(f"Путь содержит '..' компоненты: {path}")
        
        # Если путь относительный, делаем его относительно базовой директории
        if not path.is_absolute():
            path = self.base_directory / path
        
        # Разрешаем символические ссылки
        try:
            resolved_path = path.resolve()
        except OSError as e:
            raise ValueError(f"Не удалось разрешить путь {path}: {e}") from e
        
        # Проверяем что путь находится в разрешенной области
        try:
            resolved_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(
                f"Путь {resolved_path} находится за пределами "
                f"разрешенной директории {self.base_directory}"
            ) from None
        
        return resolved_path
```

### Этап 4: Оптимизация производительности (Средний приоритет)

#### 4.1 Асинхронная обработка доменов

**Файл: src/getipv4/core/async_resolver.py**
```python
"""Асинхронный модуль для разрешения доменных имен."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import TypedDict

from ..exceptions import DomainResolutionError

logger = logging.getLogger(__name__)


class AsyncDomainResult(TypedDict):
    """Результат асинхронного разрешения домена."""
    domain: str
    ipv4_addresses: list[str]
    success: bool
    error: str | None


class AsyncDNSResolver:
    """Асинхронный DNS resolver для обработки больших списков доменов."""
    
    def __init__(
        self, 
        dns_servers: list[str] | None = None,
        max_concurrent: int = 50,
        timeout: float = 5.0
    ) -> None:
        """Инициализация асинхронного DNS resolver.
        
        Args:
            dns_servers: Список DNS серверов
            max_concurrent: Максимальное количество одновременных запросов
            timeout: Таймаут для каждого запроса в секундах
        """
        self.dns_servers = dns_servers or ["127.0.0.1"]
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def resolve_domains(self, domains: list[str]) -> list[AsyncDomainResult]:
        """Асинхронно разрешить список доменов.
        
        Args:
            domains: Список доменных имен
            
        Returns:
            Список результатов разрешения
        """
        if not domains:
            return []
        
        logger.info(f"Начинаем асинхронное разрешение {len(domains)} доменов")
        
        # Создаем задачи для всех доменов
        tasks = [
            self._resolve_domain_with_semaphore(domain)
            for domain in domains
        ]
        
        # Выполняем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Неожиданная ошибка для домена {domains[i]}: {result}")
                processed_results.append(AsyncDomainResult(
                    domain=domains[i],
                    ipv4_addresses=[],
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        # Статистика
        successful = sum(1 for r in processed_results if r['success'])
        logger.info(
            f"Разрешение завершено: {successful}/{len(domains)} доменов успешно"
        )
        
        return processed_results
    
    async def _resolve_domain_with_semaphore(self, domain: str) -> AsyncDomainResult:
        """Разрешить домен с ограничением количества одновременных запросов.
        
        Args:
            domain: Доменное имя
            
        Returns:
            Результат разрешения домена
        """
        async with self._semaphore:
            return await self._resolve_single_domain(domain)
    
    async def _resolve_single_domain(self, domain: str) -> AsyncDomainResult:
        """Разрешить один домен асинхронно.
        
        Args:
            domain: Доменное имя
            
        Returns:
            Результат разрешения домена
        """
        try:
            # Используем asyncio.to_thread для выполнения синхронного DNS запроса
            # в отдельном потоке
            addresses = await asyncio.wait_for(
                asyncio.to_thread(self._resolve_domain_sync, domain),
                timeout=self.timeout
            )
            
            return AsyncDomainResult(
                domain=domain,
                ipv4_addresses=addresses,
                success=True,
                error=None
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"Таймаут при разрешении домена {domain}")
            return AsyncDomainResult(
                domain=domain,
                ipv4_addresses=[],
                success=False,
                error="Таймаут"
            )
        except Exception as e:
            logger.warning(f"Ошибка при разрешении домена {domain}: {e}")
            return AsyncDomainResult(
                domain=domain,
                ipv4_addresses=[],
                success=False,
                error=str(e)
            )
    
    def _resolve_domain_sync(self, domain: str) -> list[str]:
        """Синхронное разрешение домена (для выполнения в отдельном потоке).
        
        Args:
            domain: Доменное имя
            
        Returns:
            Список IPv4 адресов
            
        Raises:
            DomainResolutionError: Если не удалось разрешить домен
        """
        ipv4_addresses = []
        errors = []
        
        for dns_server in self.dns_servers:
            try:
                _, _, addresses = socket.gethostbyname_ex(domain)
                ipv4_addresses.extend(
                    addr for addr in addresses if self._is_ipv4(addr)
                )
                break  # Успешно разрешили, выходим
            except socket.gaierror as e:
                errors.append(f"DNS {dns_server}: {e}")
                continue
        
        if not ipv4_addresses:
            raise DomainResolutionError(
                domain=domain,
                reason=f"Все DNS серверы недоступны: {'; '.join(errors)}"
            )
        
        # Удаляем дубликаты
        return list(dict.fromkeys(ipv4_addresses))
    
    @staticmethod
    def _is_ipv4(address: str) -> bool:
        """Проверить, является ли адрес IPv4.
        
        Args:
            address: IP адрес для проверки
            
        Returns:
            True если адрес является IPv4
        """
        try:
            import ipaddress
            ip = ipaddress.ip_address(address)
            return isinstance(ip, ipaddress.IPv4Address)
        except ValueError:
            return False
```

### Этап 5: CLI интерфейс и точка входа (Средний приоритет)

**Файл: src/getipv4/cli.py**
```python
"""Интерфейс командной строки для getipv4."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import NoReturn

from .config.handler import AppConfig
from .core.async_resolver import AsyncDNSResolver
from .core.network import FileManager, NetworkCalculator
from .core.resolver import read_domains_from_file
from .exceptions import GetIPv4Error


def setup_logging(verbose: bool = False) -> None:
    """Настройка логирования.
    
    Args:
        verbose: Включить подробное логирование
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def create_parser() -> argparse.ArgumentParser:
    """Создать парсер аргументов командной строки.
    
    Returns:
        Настроенный парсер аргументов
    """
    parser = argparse.ArgumentParser(
        description='GetIPv4 - инструмент для разрешения доменов и генерации маршрутов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s -c config.ini
  %(prog)s -c config.ini --async --max-concurrent 100
  %(prog)s -c config.ini --verbose
"""
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help='Путь к файлу конфигурации'
    )
    
    parser.add_argument(
        '--async',
        action='store_true',
        help='Использовать асинхронное разрешение доменов'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=50,
        help='Максимальное количество одновременных запросов (по умолчанию: 50)'
    )
    
    parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Таймаут для DNS запросов в секундах (по умолчанию: 5.0)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Подробное логирование'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


async def process_domains_async(
    config: AppConfig,
    max_concurrent: int,
    timeout: float
) -> dict[str, list[str]]:
    """Асинхронная обработка доменов.
    
    Args:
        config: Конфигурация приложения
        max_concurrent: Максимальное количество одновременных запросов
        timeout: Таймаут для запросов
        
    Returns:
        Словарь домен -> список IP адресов
    """
    logger = logging.getLogger(__name__)
    
    # Загружаем все домены из файлов
    all_domains = []
    for domains_file in config.get_domains_files():
        try:
            domains = read_domains_from_file(domains_file)
            all_domains.extend(domains)
            logger.info(f"Загружено {len(domains)} доменов из {domains_file}")
        except Exception as e:
            logger.error(f"Ошибка загрузки доменов из {domains_file}: {e}")
            continue
    
    if not all_domains:
        logger.warning("Не найдено доменов для обработки")
        return {}
    
    # Удаляем дубликаты
    unique_domains = list(dict.fromkeys(all_domains))
    logger.info(f"Всего уникальных доменов: {len(unique_domains)}")
    
    # Асинхронно разрешаем домены
    resolver = AsyncDNSResolver(
        dns_servers=config.get_dns_servers(),
        max_concurrent=max_concurrent,
        timeout=timeout
    )
    
    results = await resolver.resolve_domains(unique_domains)
    
    # Формируем результат
    domain_to_ips = {}
    for result in results:
        if result['success'] and result['ipv4_addresses']:
            domain_to_ips[result['domain']] = result['ipv4_addresses']
    
    return domain_to_ips


def process_domains_sync(config: AppConfig) -> dict[str, list[str]]:
    """Синхронная обработка доменов.
    
    Args:
        config: Конфигурация приложения
        
    Returns:
        Словарь домен -> список IP адресов
    """
    from .core.resolver import DNSResolver
    
    logger = logging.getLogger(__name__)
    
    # Загружаем все домены из файлов
    all_domains = []
    for domains_file in config.get_domains_files():
        try:
            domains = read_domains_from_file(domains_file)
            all_domains.extend(domains)
            logger.info(f"Загружено {len(domains)} доменов из {domains_file}")
        except Exception as e:
            logger.error(f"Ошибка загрузки доменов из {domains_file}: {e}")
            continue
    
    if not all_domains:
        logger.warning("Не найдено доменов для обработки")
        return {}
    
    # Удаляем дубликаты
    unique_domains = list(dict.fromkeys(all_domains))
    logger.info(f"Всего уникальных доменов: {len(unique_domains)}")
    
    # Синхронно разрешаем домены
    resolver = DNSResolver(dns_servers=config.get_dns_servers())
    domain_to_ips = {}
    
    for i, domain in enumerate(unique_domains, 1):
        try:
            addresses = resolver.resolve_domain(domain)
            if addresses:
                domain_to_ips[domain] = addresses
            
            if i % 10 == 0:
                logger.info(f"Обработано {i}/{len(unique_domains)} доменов")
                
        except Exception as e:
            logger.warning(f"Ошибка обработки домена {domain}: {e}")
            continue
    
    return domain_to_ips


def generate_output_files(
    domain_to_ips: dict[str, list[str]],
    config: AppConfig
) -> None:
    """Генерация выходных файлов.
    
    Args:
        domain_to_ips: Словарь домен -> список IP адресов
        config: Конфигурация приложения
    """
    logger = logging.getLogger(__name__)
    file_manager = FileManager()
    output_files = config.get_output_files()
    
    # Генерируем содержимое файлов
    domain_ip_content = []
    only_ipv4_content = []
    keenetic_content = []
    
    network_calc = NetworkCalculator()
    subnet_mask = config.get_subnet_mask()
    
    for domain, ips in domain_to_ips.items():
        # Файл домен-IP
        for ip in ips:
            domain_ip_content.append(f"{domain} {ip}")
            only_ipv4_content.append(ip)
            
            # Генерируем маршрут для Keenetic
            try:
                network_info = network_calc.calculate_network(ip, subnet_mask)
                route_cmd = (
                    f"ip route {network_info.network_address}/{network_info.prefix_length} "
                    f"Wireguard_Client"
                )
                keenetic_content.append(route_cmd)
            except Exception as e:
                logger.warning(f"Ошибка генерации маршрута для {ip}: {e}")
    
    # Записываем файлы
    files_to_write = [
        (output_files['domain_ip'], '\n'.join(domain_ip_content)),
        (output_files['only_ipv4'], '\n'.join(only_ipv4_content)),
        (output_files['keenetic'], '\n'.join(keenetic_content)),
    ]
    
    for file_path, content in files_to_write:
        if file_path:  # Проверяем что путь не пустой
            try:
                file_manager.safe_write_file(file_path, content)
                logger.info(f"Создан файл: {file_path} ({len(content.splitlines())} строк)")
            except Exception as e:
                logger.error(f"Ошибка записи файла {file_path}: {e}")


async def main_async(args: argparse.Namespace) -> None:
    """Асинхронная главная функция.
    
    Args:
        args: Аргументы командной строки
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Загружаем конфигурацию
        config = AppConfig(args.config)
        logger.info(f"Конфигурация загружена из {args.config}")
        
        # Обрабатываем домены
        if args.async:
            domain_to_ips = await process_domains_async(
                config, args.max_concurrent, args.timeout
            )
        else:
            domain_to_ips = process_domains_sync(config)
        
        # Генерируем выходные файлы
        generate_output_files(domain_to_ips, config)
        
        logger.info(f"Обработка завершена. Разрешено {len(domain_to_ips)} доменов")
        
    except GetIPv4Error as e:
        logger.error(f"Ошибка приложения: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        sys.exit(1)


def main() -> NoReturn:
    """Точка входа в приложение."""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Запускаем асинхронную главную функцию
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
        sys.exit(130)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
```

## 📅 Временные рамки

| Этап | Время | Приоритет |
|------|-------|----------|
| Этап 1: Структура проекта | 2-3 дня | Высокий |
| Этап 2: Типизация | 3-4 дня | Высокий |
| Этап 3: Безопасность | 2-3 дня | Высокий |
| Этап 4: Производительность | 2-3 дня | Средний |
| Этап 5: CLI интерфейс | 1-2 дня | Средний |
| **Общее время** | **10-15 дней** | |

## 🔧 Инструменты для автоматизации

### Настройка pre-commit hooks

**Файл: .pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.287
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Makefile для автоматизации

**Файл: Makefile**
```makefile
.PHONY: help install dev-install format lint type-check test clean build

help:
	@echo "Доступные команды:"
	@echo "  install      - Установка пакета"
	@echo "  dev-install  - Установка для разработки"
	@echo "  format       - Форматирование кода"
	@echo "  lint         - Проверка стиля кода"
	@echo "  type-check   - Проверка типов"
	@echo "  test         - Запуск тестов"
	@echo "  clean        - Очистка временных файлов"
	@echo "  build        - Сборка пакета"

install:
	pip install .

dev-install:
	pip install -e ".[dev]"
	pre-commit install

format:
	black src tests
	isort src tests

lint:
	ruff check src tests
	black --check src tests
	isort --check-only src tests

type-check:
	mypy src

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

build: clean
	python -m build
```

## 📋 Чек-лист выполнения

### Этап 1: Структура проекта
- [ ] Создана новая структура с src/ layout
- [ ] Создан pyproject.toml
- [ ] Добавлены __init__.py файлы
- [ ] Перенесены модули в новую структуру
- [ ] Обновлены импорты

### Этап 2: Типизация
- [ ] Добавлен `from __future__ import annotations`
- [ ] Добавлены типы для всех функций
- [ ] Созданы TypedDict для структурированных данных
- [ ] Добавлены custom exceptions
- [ ] Настроен mypy

### Этап 3: Безопасность
- [ ] Добавлена валидация пользовательского ввода
- [ ] Реализована безопасная работа с файлами
- [ ] Улучшена обработка ошибок
- [ ] Добавлено структурированное логирование

### Этап 4: Производительность
- [ ] Реализован асинхронный DNS resolver
- [ ] Добавлено кеширование
- [ ] Оптимизированы алгоритмы
- [ ] Добавлена batch обработка

### Этап 5: CLI интерфейс
- [ ] Создан современный CLI интерфейс
- [ ] Добавлена поддержка аргументов
- [ ] Реализована точка входа
- [ ] Добавлена обработка сигналов

## 🎯 Ожидаемые результаты

После выполнения рефакторинга проект будет:

1. **Соответствовать современным стандартам Python 3.11+**
2. **Иметь полную типизацию с поддержкой mypy**
3. **Обладать улучшенной безопасностью и обработкой ошибок**
4. **Поддерживать асинхронную обработку для лучшей производительности**
5. **Иметь современную структуру проекта с src/ layout**
6. **Включать автоматизированные инструменты для поддержания качества кода**
7. **Обеспечивать лучшую читаемость и поддерживаемость**

## 📊 Метрики улучшения

| Метрика | До рефакторинга | После рефакторинга |
|---------|-----------------|--------------------|
| Покрытие типами | 0% | 95%+ |
| Соответствие PEP 8 | 60% | 98%+ |
| Безопасность файловых операций | Низкая | Высокая |
| Производительность (большие списки) | Медленная | Быстрая |
| Обработка ошибок | Базовая | Структурированная |
| Логирование | Отсутствует | Полное |
| Тестируемость | Средняя | Высокая |

## 🚀 Дополнительные улучшения

### Мониторинг и метрики
- Добавление метрик производительности
- Мониторинг использования памяти
- Статистика успешности разрешения доменов

### Расширенная функциональность
- Поддержка IPv6 (опционально)
- Кеширование результатов на диск
- Поддержка различных форматов вывода (JSON, CSV)
- Интеграция с внешними DNS провайдерами

### Документация
- Автоматическая генерация API документации
- Примеры использования
- Руководство по развертыванию

## 📝 Заключение

Данный план рефакторинга направлен на кардинальное улучшение качества кода проекта GetIPv4_mazix. Поэтапное выполнение позволит:

- Минимизировать риски при внесении изменений
- Обеспечить обратную совместимость
- Улучшить производительность и безопасность
- Подготовить проект к дальнейшему развитию

Рекомендуется начать с этапов высокого приоритета и постепенно переходить к менее критичным улучшениям.