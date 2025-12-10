"""
Конфигурация pytest
Автоматически добавляет корневую директорию проекта в sys.path
"""

import os
import sys
from pathlib import Path

import pytest

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session", autouse=True)
def configure_proxy():
    """
    Автоматически конфигурирует прокси для совместимости с LangChain/Groq.

    Конвертирует socks:// в socks5:// для всех прокси переменных окружения,
    так как httpx (используемый Groq API) не поддерживает схему socks://.
    """
    # Сохраняем оригинальные значения
    original_proxies = {}
    proxy_vars = [
        "ALL_PROXY",
        "all_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "HTTPS_PROXY",
        "https_proxy",
    ]

    for var in proxy_vars:
        original_value = os.environ.get(var)
        if original_value:
            original_proxies[var] = original_value

            # Конвертируем socks:// в socks5://
            if original_value.startswith("socks://"):
                new_value = original_value.replace("socks://", "socks5://", 1)
                os.environ[var] = new_value
                print(f"🔧 Прокси {var}: {original_value} -> {new_value}")

    # Выполняем тесты
    yield

    # Восстанавливаем оригинальные значения (опционально, если нужно)
    # for var, value in original_proxies.items():
    #     os.environ[var] = value
