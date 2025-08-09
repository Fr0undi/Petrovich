import re
import logging
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.scraper import PageScraper

logger = logging.getLogger(__name__)


class CategoryPageParser:
    """Парсер ссылок на товары"""

    def __init__(self):
        self.scraper = PageScraper()

    async def get_page_count(self, url: str) -> int:
        """Определяет количество страниц, сравнивая содержимое страниц"""

        logger.debug(f"Определение количества страниц для: {url}")

        # Сначала смотрим на первую страницу
        html = await self.scraper.scrape_page(url)
        if not html:
            return 1

        soup = BeautifulSoup(html, 'html.parser')

        # Получаем товары с первой страницы для сравнения
        first_page_products = self._extract_product_urls_from_soup(soup)
        if not first_page_products:
            logger.info("На первой странице товары не найдены")
            return 1

        # Ищем видимые номера страниц в пагинации
        pattern = r'p=(\d+)'
        matches = re.findall(pattern, html)

        if matches:
            visible_max = max(int(match) for match in matches)
            logger.debug(f"Максимальная видимая страница: p={visible_max}")
        else:
            logger.info("Пагинация не найдена, возвращаем 1 страницу")
            return 1

        # Проверяем наличие кнопки "..."
        dots_button = soup.select_one('a[data-test="paginator-next-chunk-btn"]')

        if not dots_button:
            # Если нет кнопки "..." - берем максимальную видимую страницу
            total_pages = visible_max + 1
            logger.info(f"Кнопка '...' не найдена. Всего страниц: {total_pages}")
            return total_pages

        # Если есть кнопка "..." - проверяем страницы, сравнивая содержимое
        logger.info("Есть кнопка '...', определяем общее количество страниц сравнением содержимого")

        # Начинаем с последней видимой
        current_page = visible_max + 1
        last_valid_page = visible_max

        while current_page < 1000:
            test_url = f"{url}?p={current_page}"

            logger.debug(f"Проверяем страницу p={current_page}")
            test_html = await self.scraper.scrape_page(test_url)

            if test_html:
                test_soup = BeautifulSoup(test_html, 'html.parser')
                current_page_products = self._extract_product_urls_from_soup(test_soup)

                if current_page_products:
                    # Сравниваем с первой страницей
                    if set(current_page_products) == set(first_page_products):
                        # Содержимое совпадает с первой страницей - конец страниц
                        logger.debug(f"Страница p={current_page} содержит те же товары, что и p=0 - достигнут конец")
                        break
                    else:
                        # Содержимое отличается - страница валидная
                        last_valid_page = current_page
                        logger.debug(
                            f"Страница p={current_page} содержит {len(current_page_products)} уникальных товаров")
                else:
                    # Нет товаров на странице - конец
                    logger.debug(f"Страница p={current_page} не содержит товаров")
                    break
            else:
                # HTML не получен - конец
                logger.debug(f"Страница p={current_page} недоступна")
                break

            current_page += 1

        total_pages = last_valid_page + 1
        logger.info(f"Методом сравнения найдено страниц: {total_pages} (до p={last_valid_page})")
        return total_pages

    def _extract_product_urls_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает список URL товаров из BeautifulSoup объекта"""

        product_links = set()
        petrovich_url = 'https://moscow.petrovich.ru'

        item_blocks = soup.find_all('div', class_='pt-flex pt-flex-col pt-justify-between')

        for block in item_blocks:
            title_links = block.find_all('a')
            for link in title_links:
                href = link.get('href')
                if href and href.startswith('/product'):
                    full_url = urljoin(petrovich_url, href)
                    product_links.add(full_url)

        return sorted(list(product_links))

    async def create_page_links(self, url: str) -> List[str]:
        """Создает ссылки на все страницы категории"""

        pages = []
        page_count = await self.get_page_count(url)

        logger.info(f"Создание ссылок для {page_count} страниц")

        # Страницы нумеруются с 0: ?p=0, ?p=1, ?p=2
        for page_number in range(0, page_count):
            pages.append(f'{url}?p={page_number}')

        logger.debug(f"Создано ссылок на страницы: {len(pages)}")
        return pages

    async def get_product_links(self, url: str) -> List[str]:
        """Извлекает ссылки на товары со страницы категории"""

        logger.debug(f"Извлечение товаров с: {url}")

        html = await self.scraper.scrape_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        products_list = self._extract_product_urls_from_soup(soup)

        logger.info(f"Найдено товаров: {len(products_list)}")
        return products_list