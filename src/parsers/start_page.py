from typing import List
from urllib.parse import urljoin
import logging

from bs4 import BeautifulSoup

from src.core.settings import  settings
from src.scrapers.scraper import PageScraper

logger = logging.getLogger(__name__)


class StartPageParser:
    """Парсер категорий товаров со страницы каталога"""

    def __init__(self):
        self.scraper = PageScraper()

    async def get_categories(self, url: str) -> List[str]:
        """Извлекает ссылки категорий товаров"""

        logger.info(f"Получение категорий с: {url}")

        html = await self.scraper.scrape_page(url)
        soup = BeautifulSoup(html, "html.parser")

        categories = []

        category_block = soup.find('section', class_ = 'pt-row pt-gutter-lg-xlg')
        if category_block:
            paragraphs = category_block.findAll('p')
            for p in paragraphs:
                links = p.findAll('a', href = True)

                for link in links:
                    href = link.get('href')
                    if href:
                        if href.startswith('/catalog/'):
                            href = href[9:]
                            logger.debug(f"Обработана ссылка с '/catalog/': {link.get('href')} -> {href}")

                        full_url = urljoin(settings.base_url, href)
                        categories.append(full_url)
                        logger.debug(f"Найдена категория: {full_url}")

        logger.info(f"Всего найдено категорий: {len(categories)}")

        return categories