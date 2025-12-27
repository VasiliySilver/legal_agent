"""
Модуль для загрузки списка статей с главной страницы ТК РФ
"""

import httpx
from bs4 import BeautifulSoup
import re

URL = "https://www.consultant.ru/document/cons_doc_LAW_34683/"


async def fetch_article_links() -> tuple[str, list[dict]]:
    """
    Загружает главную страницу и извлекает ссылки на все статьи.

    Returns:
        tuple: (html страницы, список словарей со ссылками)
               [{text: "Статья X. Название", href: "https://..."}, ...]
    """
    async with httpx.AsyncClient(
        timeout=30.0, trust_env=False, follow_redirects=True
    ) as client:
        response = await client.get(URL)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Извлекаем ссылки на статьи
    article_links = []
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True)
        if "Статья" in text and re.search(r"\d+", text):
            article_links.append(
                {"text": text, "href": "https://www.consultant.ru" + link["href"]}
            )

    return html, article_links
