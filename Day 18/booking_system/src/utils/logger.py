# src/utils/logger.py
"""
Модуль логирования для системы логистики и бронирования

Предоставляет:
- Настраиваемое логирование с разными уровнями
- Ротацию логов
- Логирование в файл и консоль
- Структурированное логирование (JSON)
- Контекстное логирование (с ID запроса, пользователем и т.д.)
- Декораторы для автоматического логирования

Поддерживает:
- Разные форматы вывода (текстовый, JSON, цветной)
- Разные уровни логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Фильтрацию по модулям
- Контекстную информацию (request_id, user_id, session_id)
"""

import logging
import logging.config
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
import traceback
from pathlib import Path
import time
from contextvars import ContextVar
import uuid

# --- Контекстные переменные для логирования ---
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
session_id_var: ContextVar[str] = ContextVar('session_id', default='')


# --- Форматтеры ---

class JSONFormatter(logging.Formatter):
    """
    Форматтер для структурированного логирования в JSON
    
    Example:
        {"timestamp": "2026-06-27T10:00:00.123Z", "level": "INFO", 
         "message": "User logged in", "module": "auth", 
         "request_id": "abc-123", "user_id": "user-456"}
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True,
        include_extra: bool = True
    ):
        super().__init__(fmt, datefmt, style, validate)
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматировать запись в JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'session_id': session_id_var.get(),
        }
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Добавляем дополнительные поля из record
        if self.include_extra:
            extra_fields = {
                key: value
                for key, value in record.__dict__.items()
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename',
                    'funcName', 'levelname', 'levelno', 'lineno',
                    'module', 'msecs', 'pathname', 'process',
                    'processName', 'relativeCreated', 'thread',
                    'threadName', 'exc_info', 'exc_text', 'stack_info'
                ]
            }
            if extra_fields:
                log_data['extra'] = extra_fields
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ColorFormatter(logging.Formatter):
    """
    Форматтер с цветным выводом для консоли
    
    Цвета:
    - DEBUG: Голубой
    - INFO: Зеленый
    - WARNING: Желтый
    - ERROR: Красный
    - CRITICAL: Красный + жирный
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Голубой
        'INFO': '\033[32m',       # Зеленый
        'WARNING': '\033[33m',    # Желтый
        'ERROR': '\033[31m',      # Красный
        'CRITICAL': '\033[31;1m', # Красный + жирный
        'RESET': '\033[0m'        # Сброс
    }
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True
    ):
        super().__init__(fmt, datefmt, style, validate)
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматировать запись с цветами"""
        # Сохраняем оригинальный уровень
        levelname = record.levelname
        levelno = record.levelno
        
        # Добавляем цвет
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        
        # Форматируем сообщение
        result = super().format(record)
        
        # Восстанавливаем оригинальный уровень
        record.levelname = levelname
        
        return result


class ContextualFormatter(logging.Formatter):
    """
    Форматтер с контекстной информацией
    
    Формат: [TIMESTAMP] [LEVEL] [REQUEST_ID] [USER_ID] MESSAGE
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = '%',
        validate: bool = True
    ):
        super().__init__(fmt, datefmt, style, validate)
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматировать запись с контекстом"""
        # Получаем контекстные переменные
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()
        
        # Добавляем контекст к сообщению
        context_parts = []
        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        if user_id:
            context_parts.append(f"user={user_id[:8]}")
        if session_id:
            context_parts.append(f"session={session_id[:8]}")
        
        context_str = f"[{' '.join(context_parts)}] " if context_parts else ""
        
        # Сохраняем оригинальное сообщение
        original_msg = record.getMessage()
        
        # Форматируем с контекстом
        record.msg = f"{context_str}{original_msg}"
        
        # Вызываем родительский форматтер
        result = super().format(record)
        
        # Восстанавливаем оригинальное сообщение
        record.msg = original_msg
        
        return result


# --- Фильтры ---

class RequestIdFilter(logging.Filter):
    """Фильтр для добавления request_id в записи"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        record.session_id = session_id_var.get()
        return True


class ModuleFilter(logging.Filter):
    """Фильтр для ограничения логирования по модулям"""
    
    def __init__(self, modules: list):
        self.modules = modules
    
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name in self.modules


class LevelFilter(logging.Filter):
    """Фильтр для ограничения логирования по уровням"""
    
    def __init__(self, min_level: int, max_level: int):
        self.min_level = min_level
        self.max_level = max_level
    
    def filter(self, record: logging.LogRecord) -> bool:
        return self.min_level <= record.levelno <= self.max_level


# --- Хендлеры ---

class RotatingFileHandler(logging.Handler):
    """
    Хендлер с ротацией файлов
    
    Создает новый файл при достижении максимального размера
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        super().__init__()
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._current_size = 0
        self._file = None
        self._open_file()
    
    def _open_file(self):
        """Открыть файл для записи"""
        if self._file:
            self._file.close()
        
        # Создаем директорию, если не существует
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)
        
        self._file = open(self.filename, 'a', encoding='utf-8')
        self._current_size = self._file.tell()
    
    def _rotate(self):
        """Выполнить ротацию файла"""
        # Закрываем текущий файл
        if self._file:
            self._file.close()
        
        # Переименовываем существующие файлы
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.filename}.{i}"
            dst = f"{self.filename}.{i + 1}"
            if os.path.exists(src):
                os.rename(src, dst)
        
        # Переименовываем основной файл
        if os.path.exists(self.filename):
            os.rename(self.filename, f"{self.filename}.1")
        
        # Открываем новый файл
        self._open_file()
    
    def emit(self, record: logging.LogRecord):
        """Записать запись в файл"""
        try:
            msg = self.format(record) + '\n'
            msg_size = len(msg.encode('utf-8'))
            
            # Проверяем размер файла
            if self._current_size + msg_size > self.max_bytes:
                self._rotate()
                self._current_size = 0
            
            # Записываем сообщение
            self._file.write(msg)
            self._file.flush()
            self._current_size += msg_size
            
        except Exception:
            self.handleError(record)
    
    def close(self):
        """Закрыть файл"""
        if self._file:
            self._file.close()
        super().close()


# --- Конфигурация логирования ---

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'color': {
            '()': ColorFormatter,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': JSONFormatter,
        },
        'contextual': {
            '()': ContextualFormatter,
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'filters': {
        'request_id': {
            '()': RequestIdFilter,
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'color',
            'filters': ['request_id']
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filters': ['request_id'],
            'filename': 'logs/app.log'
        },
        'json_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'json',
            'filters': ['request_id'],
            'filename': 'logs/app.json'
        },
        'rotating_file': {
            '()': RotatingFileHandler,
            'level': 'DEBUG',
            'formatter': 'contextual',
            'filters': ['request_id'],
            'filename': 'logs/app.log',
            'max_bytes': 10 * 1024 * 1024,
            'backup_count': 5
        }
    },
    'loggers': {
        'src': {
            'level': 'DEBUG',
            'handlers': ['console', 'rotating_file'],
            'propagate': False
        },
        'src.presentation': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'src.infrastructure': {
            'level': 'DEBUG',
            'handlers': ['rotating_file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}


# --- Класс Logger ---

class Logger:
    """
    Основной класс логирования
    
    Предоставляет удобные методы для логирования с контекстом
    """
    
    def __init__(self, name: str = 'src'):
        self.logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
    
    @classmethod
    def configure(cls, config: Optional[Dict[str, Any]] = None):
        """Настроить логирование"""
        if config is None:
            config = DEFAULT_LOGGING_CONFIG
        
        # Создаем директорию для логов
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.config.dictConfig(config)
    
    def with_context(self, **kwargs) -> 'Logger':
        """Добавить контекст к логгеру"""
        new_logger = Logger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def _log(self, level: int, message: str, *args, **kwargs):
        """Внутренний метод для логирования"""
        # Добавляем контекст к extra
        extra = kwargs.get('extra', {})
        extra.update(self._context)
        kwargs['extra'] = extra
        
        self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Логирование на уровне DEBUG"""
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Логирование на уровне INFO"""
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Логирование на уровне WARNING"""
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Логирование на уровне ERROR"""
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Логирование на уровне CRITICAL"""
        self._log(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Логирование исключения"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def log_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Логирование HTTP запроса"""
        self.info(
            f"Request: {method} {path}",
            extra={
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': duration_ms
            }
        )


# --- Декораторы для логирования ---

def log_execution(logger: Optional[Logger] = None):
    """
    Декоратор для логирования выполнения функции
    
    Логирует:
    - Начало выполнения
    - Время выполнения
    - Результат или исключение
    
    Example:
        @log_execution()
        def calculate_distance(a, b):
            return a.distance_to(b)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Получаем логгер
            _logger = logger or get_logger(func.__module__)
            
            # Логируем начало
            _logger.debug(f"Starting: {func.__name__}")
            start_time = time.time()
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Логируем успешное выполнение
                duration = (time.time() - start_time) * 1000
                _logger.debug(
                    f"Completed: {func.__name__}",
                    extra={'duration_ms': duration, 'result': str(result)[:100]}
                )
                return result
                
            except Exception as e:
                # Логируем ошибку
                _logger.error(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_method_call(logger: Optional[Logger] = None):
    """
    Декоратор для логирования вызовов методов класса
    
    Логирует:
    - Имя метода
    - Аргументы
    - Результат
    - Время выполнения
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            _logger = logger or get_logger(self.__class__.__module__)
            
            # Формируем информацию о вызове
            class_name = self.__class__.__name__
            method_name = func.__name__
            
            # Логируем вызов
            args_str = ', '.join([repr(a) for a in args])
            kwargs_str = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
            params = ', '.join(filter(None, [args_str, kwargs_str]))
            
            _logger.debug(f"Calling: {class_name}.{method_name}({params})")
            start_time = time.time()
            
            try:
                result = func(self, *args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                _logger.debug(
                    f"Completed: {class_name}.{method_name}",
                    extra={'duration_ms': duration}
                )
                return result
                
            except Exception as e:
                _logger.error(
                    f"Error in {class_name}.{method_name}: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# --- Контекстные менеджеры для логирования ---

class LogContext:
    """
    Контекстный менеджер для логирования с контекстом
    
    Example:
        with LogContext(request_id="abc-123", user_id="user-456"):
            # Все логи внутри будут содержать этот контекст
            logger.info("Processing request")
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self._old_context = {}
    
    def __enter__(self):
        """Установить контекст"""
        # Сохраняем текущие значения
        for key, value in self.context.items():
            if key == 'request_id':
                self._old_context['request_id'] = request_id_var.get()
                request_id_var.set(str(value))
            elif key == 'user_id':
                self._old_context['user_id'] = user_id_var.get()
                user_id_var.set(str(value))
            elif key == 'session_id':
                self._old_context['session_id'] = session_id_var.get()
                session_id_var.set(str(value))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Восстановить контекст"""
        for key, value in self._old_context.items():
            if key == 'request_id':
                request_id_var.set(value)
            elif key == 'user_id':
                user_id_var.set(value)
            elif key == 'session_id':
                session_id_var.set(value)


def with_request_id():
    """
    Контекстный менеджер с автоматической генерацией request_id
    
    Example:
        with with_request_id():
            logger.info("Processing request")  # Автоматически добавит request_id
    """
    return LogContext(request_id=str(uuid.uuid4()))


# --- Функции для получения логгера ---

def get_logger(name: Optional[str] = None) -> Logger:
    """Получить логгер"""
    if name is None:
        name = 'src'
    return Logger(name)


def get_request_logger() -> Logger:
    """Получить логгер для HTTP запросов"""
    return Logger('src.presentation.api')


def get_service_logger() -> Logger:
    """Получить логгер для сервисов"""
    return Logger('src.application.services')


def get_repository_logger() -> Logger:
    """Получить логгер для репозиториев"""
    return Logger('src.infrastructure.repositories')


# --- Настройка по умолчанию ---

def setup_logging(env: str = 'development'):
    """
    Настроить логирование в зависимости от окружения
    
    Args:
        env: Окружение (development, production, testing)
    """
    config = DEFAULT_LOGGING_CONFIG.copy()
    
    if env == 'production':
        # В продакшене используем JSON формат
        config['handlers']['console']['formatter'] = 'json'
        config['handlers']['console']['level'] = 'WARNING'
        config['root']['level'] = 'WARNING'
        
    elif env == 'testing':
        # В тестах логируем только ошибки
        config['handlers']['console']['level'] = 'ERROR'
        config['root']['level'] = 'ERROR'
        config['loggers']['src']['level'] = 'ERROR'
    
    # Настройка логов
    Logger.configure(config)


# --- Инициализация ---

# Настраиваем логирование по умолчанию
setup_logging('development')

# Создаем глобальный логгер
logger = get_logger()


# --- Пример использования ---

def example_usage():
    """Пример использования логирования"""
    
    print("="*50)
    print("Пример использования логирования")
    print("="*50)
    
    # 1. Базовое логирование
    print("\n1. Базовое логирование:")
    logger.info("Приложение запущено")
    logger.warning("Предупреждение: низкое количество свободной памяти")
    logger.error("Ошибка при обработке запроса")
    
    # 2. Логирование с контекстом
    print("\n2. Логирование с контекстом:")
    with LogContext(request_id="req-123", user_id="user-456"):
        logger.info("Обработка запроса пользователя")
        logger.debug("Детали запроса", extra={'endpoint': '/api/routes'})
    
    # 3. Логирование исключений
    print("\n3. Логирование исключений:")
    try:
        raise ValueError("Неверные данные")
    except Exception as e:
        logger.exception("Ошибка валидации данных")
    
    # 4. Использование декоратора
    print("\n4. Использование декоратора @log_execution:")
    
    @log_execution()
    def calculate_demo(a: float, b: float) -> float:
        """Демонстрационная функция"""
        time.sleep(0.1)
        return a + b
    
    result = calculate_demo(5, 3)
    print(f"  Результат: {result}")
    
    # 5. Специализированные логгеры
    print("\n5. Специализированные логгеры:")
    api_logger = get_request_logger()
    api_logger.info("Получен API запрос", extra={
        'method': 'GET',
        'path': '/api/routes',
        'ip': '192.168.1.1'
    })
    
    service_logger = get_service_logger()
    service_logger.info("Создан маршрут", extra={
        'route_id': 123,
        'distance': 634.5
    })
    
    # 6. Логирование производительности
    print("\n6. Логирование производительности:")
    start_time = time.time()
    time.sleep(0.05)
    duration = (time.time() - start_time) * 1000
    
    logger.log_request('POST', '/api/routes', 201, duration)
    
    print("\n" + "="*50)
    print("Пример завершен. Проверьте файлы логов в папке logs/")
    print("="*50)


if __name__ == "__main__":
    example_usage()