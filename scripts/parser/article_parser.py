"""
Модуль для парсинга отдельных статей через Playwright
"""

import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright


async def fetch_article_v4(
    url: str, article_title: str, hierarchy_map: dict
) -> dict | None:
    """
    Загружает статью с полными метаданными (v4).

    Args:
        url: URL статьи
        article_title: Заголовок статьи (например, "Статья 80. Расторжение...")
        hierarchy_map: Словарь с иерархией {номер: {part, section, chapter}}

    Returns:
        dict с полями:
            - title, text, text_length, url
            - status: 'active' | 'abolished' | 'suspended'
            - part, section, chapter: иерархия из маппинга
            - source, source_url, fetched_at
        или None в случае ошибки
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"⏳ Загружаем: {article_title[:50]}...")

            # Загружаем страницу
            await page.goto(url, timeout=60000)

            # Ждем контейнер
            await page.wait_for_selector("div.document-page__content", timeout=20000)
            print("✓ Контейнер найден")

            # Ждем появления текста (адаптировано для коротких статей)
            try:
                await page.wait_for_function(
                    """
                    () => {
                        const container = document.querySelector('div.document-page__content');
                        if (!container) return false;
                        const text = container.innerText || container.textContent || '';
                        return text.trim().length > 50;
                    }
                """,
                    timeout=15000,
                )
                print("✓ Текст загружен")
            except Exception:
                print("  ⚠️ Таймаут ожидания текста, продолжаем...")

            # Небольшая пауза для стабилизации
            await asyncio.sleep(1)

            # === ИЗВЛЕКАЕМ ЗАГОЛОВОК ===
            title_elem = await page.query_selector("h1")
            title = await title_elem.inner_text() if title_elem else article_title
            title = title.strip()

            # === ИЗВЛЕКАЕМ ТЕКСТ ===
            content_elem = await page.query_selector("div.document-page__content")
            if content_elem:
                text = await content_elem.inner_text()
                text = text.strip()
            else:
                text = "Текст не найден"

            # === ОПРЕДЕЛЯЕМ СТАТУС ===
            text_lower = text.lower()
            if "утратил силу" in text_lower or "утратила силу" in text_lower:
                status = "abolished"
            elif "приостановлен" in text_lower or "приостановлена" in text_lower:
                status = "suspended"
            else:
                status = "active"

            # === ИЗВЛЕКАЕМ НОМЕР СТАТЬИ ===
            article_num_match = re.search(r"Статья\s+(\d+)", article_title)
            article_number = article_num_match.group(1) if article_num_match else None

            # === ПОЛУЧАЕМ ИЕРАРХИЮ ИЗ МАППИНГА ===
            hierarchy = hierarchy_map.get(article_number, {}) if article_number else {}
            part = hierarchy.get("part")
            section = hierarchy.get("section")
            chapter = hierarchy.get("chapter")

            await browser.close()

            return {
                "title": title,
                "text": text,
                "text_length": len(text),
                "status": status,
                "part": part,
                "section": section,
                "chapter": chapter,
                "source": "ConsultantPlus",
                "source_url": url,
                "fetched_at": datetime.now().isoformat(),
            }

        except Exception as e:
            await browser.close()
            print(f"❌ Ошибка: {e}")
            return None
