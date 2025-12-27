"""
Модуль для парсинга иерархии ТК РФ (Часть → Раздел → Глава → Статья)
"""

import re
from bs4 import BeautifulSoup


def parse_tk_rf_hierarchy(html: str) -> dict:
    """
    Парсит оглавление ТК РФ и создает маппинг: номер статьи → иерархия.

    Args:
        html: HTML код главной страницы ТК РФ

    Returns:
        dict: {
            '1': {'part': 'Часть I', 'section': '...', 'chapter': '...'},
            '2': {...},
            ...
        }
    """
    soup = BeautifulSoup(html, "html.parser")
    hierarchy_map = {}

    # Текущий контекст
    current_part = None
    current_section = None
    current_chapter = None

    # Ищем все элементы в оглавлении
    content = soup.find("div", class_="document")
    if not content:
        content = soup

    # Ищем все ссылки и заголовки
    for elem in content.find_all(["a", "div", "p", "h2", "h3", "h4"]):
        text = elem.get_text(strip=True)

        # Проверяем на "Часть"
        part_match = re.match(r"Часть\s+([IVXLCDM]+)", text, re.IGNORECASE)
        if part_match:
            current_part = f"Часть {part_match.group(1)}"
            continue

        # Проверяем на "Раздел"
        section_match = re.match(
            r"(Раздел\s+[IVXLCDM]+\.?\s*[^\n]*)", text, re.IGNORECASE
        )
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        # Проверяем на "Глава"
        chapter_match = re.match(r"(Глава\s+\d+\.?\s*[^\n]*)", text, re.IGNORECASE)
        if chapter_match:
            current_chapter = chapter_match.group(1).strip()
            continue

        # Проверяем на "Статья"
        article_match = re.search(r"Статья\s+(\d+)", text)
        if article_match:
            article_num = article_match.group(1)
            hierarchy_map[article_num] = {
                "part": current_part,
                "section": current_section,
                "chapter": current_chapter,
            }

    return hierarchy_map
