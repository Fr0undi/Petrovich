import re
import json
import logging
from typing import List, Optional, Dict, Any

from src.scrapers.scraper import PageScraper
from src.schemas.product import Product, Supplier, SupplierOffer, PriceInfo, Attribute

logger = logging.getLogger(__name__)


class ProductPropertyParser:
    """Парсер для извлечения информации о товаре через API"""

    def __init__(self):
        self.scraper = PageScraper()
        self.api_base_url = "https://api.petrovich.ru/catalog/v5/products"
        self.api_params = "?city_code=msk&client_id=pet_site"

    async def parse_product(self, url: str) -> Optional[Product]:
        """Парсит страницу товара через API, возвращая объект Product"""

        logger.info(f"Парсинг товара: {url}")

        # Извлекаем ID товара из URL
        product_id = self._extract_product_id(url)
        if not product_id:
            logger.error(f"Не удалось извлечь ID товара из URL: {url}")
            return None

        # Формируем API URL
        api_url = f"{self.api_base_url}/{product_id}{self.api_params}"
        logger.debug(f"API URL: {api_url}")

        # Получаем данные из API
        json_data = await self._fetch_api_data(api_url)
        if not json_data:
            logger.error(f"Не удалось получить данные из API: {api_url}")
            return None

        # Проверяем успешность ответа
        if json_data.get('state', {}).get('code') != 20001:
            logger.error(f"API вернул ошибку: {json_data.get('state', {})}")
            return None

        product_data = json_data.get('data', {}).get('product', {})
        if not product_data:
            logger.error("Данные о товаре отсутствуют в ответе API")
            return None

        # Извлекаем данные из JSON
        try:
            title = self._extract_title(product_data)
            description = self._extract_description(product_data)
            article = self._extract_article(product_data)
            brand = self._extract_brand(product_data)
            country_of_origin = self._extract_country(product_data)
            warranty_months = self._extract_warranty_months(product_data)
            category = self._extract_category(product_data)
            attributes = self._extract_attributes(product_data)
            suppliers = self._extract_supplier_info(product_data, url)

            return Product(
                title=title,
                description=description,
                article=article,
                brand=brand,
                country_of_origin=country_of_origin,
                warranty_months=warranty_months,
                category=category,
                attributes=attributes,
                suppliers=suppliers
            )

        except Exception as e:
            logger.error(f"Ошибка при парсинге JSON данных товара {product_id}: {e}")
            return None

    def _extract_product_id(self, url: str) -> Optional[str]:
        """Извлекает ID товара из URL"""

        pattern = r'/product/(\d+)/?'
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        logger.warning(f"Не удалось извлечь ID товара из URL: {url}")
        return None

    async def _fetch_api_data(self, api_url: str) -> Optional[Dict[str, Any]]:
        """Получает JSON данные из API"""

        try:
            response_text = await self.scraper.scrape_page(api_url)
            if not response_text:
                return None

            json_data = json.loads(response_text)
            return json_data

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None

        except Exception as e:
            logger.error(f"Ошибка получения данных из API: {e}")
            return None

    def _extract_title(self, product_data: Dict[str, Any]) -> str:
        """Извлекает название товара"""

        title = product_data.get('title', '')
        if title and title.strip():
            return title.strip()
        return 'Нет данных'

    def _extract_description(self, product_data: Dict[str, Any]) -> str:
        """Извлекает описание товара"""

        desc_no_html = product_data.get('description_no_html', {})
        if isinstance(desc_no_html, dict):
            description = desc_no_html.get('description', '')
            if description and description.strip():
                return description.strip()

        return 'Нет данных'

    def _extract_article(self, product_data: Dict[str, Any]) -> str:
        """Извлекает артикул товара"""

        article = product_data.get('code')
        if article is not None:
            return str(article)

        return 'Нет данных'

    def _extract_brand(self, product_data: Dict[str, Any]) -> str:
        """Извлекает бренд товара"""

        properties = product_data.get('properties', [])
        if isinstance(properties, list):
            for prop in properties:
                if prop.get('slug') == 'brend':
                    values = prop.get('value', [])
                    if isinstance(values, list) and values and len(values) > 0:
                        brand = values[0].get('title', '')
                        if brand:
                            return brand

        return 'Нет данных'

    def _extract_country(self, product_data: Dict[str, Any]) -> str:
        """Извлекает страну происхождения"""

        properties = product_data.get('properties', [])
        if isinstance(properties, list):
            for prop in properties:
                if prop.get('slug') == 'stranamproizvoditel':
                    values = prop.get('value', [])
                    if values and len(values) > 0:
                        country = values[0].get('title', '')
                        if country:
                            return country

        return 'Нет данных'

    def _extract_warranty_months(self, product_data: Dict[str, Any]) -> str:
        """Извлекает гарантию товара"""

        properties = product_data.get('properties', [])
        if isinstance(properties, list):
            for prop in properties:
                if prop.get('slug') == 'garantiya':
                    values = prop.get('value', [])
                    if values and len(values) > 0:
                        warranty_months = values[0].get('title', '')
                        if warranty_months:
                            return warranty_months

        return 'Нет данных'

    def _extract_category(self, product_data: Dict[str, Any]) -> str:
        """Извлекает категорию товара"""

        # Ищем в breadcrumbs, извлекая последнюю категорию
        breadcrumbs = product_data.get('breadcrumbs', [])
        if isinstance(breadcrumbs, list) and len(breadcrumbs) > 0:
            last_crumb = breadcrumbs[-1]
            category = last_crumb.get('title', '')
            if category:
                return category

        # Ищем в секции товара
        section = product_data.get('section', {})
        if isinstance(section, dict):
            section_title = section.get('title', '')
            if section_title:
                return section_title

        return 'Нет данных'

    def _extract_retail_price(self, product_data: Dict[str, Any]) -> float:
        """Извлекает розничную цену товара"""

        price_data = product_data.get('price', {})
        if isinstance(price_data, dict):
            retail_price = price_data.get('retail')

            if retail_price:
                try:
                    return float(retail_price)
                except (ValueError, TypeError):
                    pass

        return 0.0

    def _extract_gold_price(self, product_data: Dict[str, Any]) -> Optional[float]:
        """Извлекает цену товара по карте"""

        price_data = product_data.get('price', {})
        if isinstance(price_data, dict):
            gold_price = price_data.get('gold')

            if gold_price:
                try:
                    return float(gold_price)
                except (ValueError, TypeError):
                    pass

        return None

    def _extract_stock(self, product_data: Dict[str, Any]) -> str:
        """Извлекает информацию о наличии"""

        remains = product_data.get('remains', {})
        if isinstance(remains, dict):
            delivery = remains.get('delivery', {})
            if isinstance(delivery, dict):
                delivery_list = delivery.get('list', [])
                if isinstance(delivery_list, list) and len(delivery_list) > 0:
                    first_delivery = delivery_list[0]
                    description = first_delivery.get('description', '')
                    if description:
                        return description

        return 'Нет данных'

    def _extract_delivery_time(self, product_data: Dict[str, Any]) -> str:
        """Извлекает время доставки"""

        remains = product_data.get('remains', {})
        if isinstance(remains, dict):

            delivery = remains.get('delivery', {})
            if isinstance(delivery, dict):
                delivery_list = delivery.get('list', [])
                if isinstance(delivery_list, list) and delivery_list:
                    first_delivery = delivery_list[0]
                    delivery_title = first_delivery.get('title', '')
                    if delivery_title:
                        return delivery_title

        return 'Нет данных'

    def _extract_package_info(self, product_data: Dict[str, Any]) -> str:
        """Извлекает информацию об упаковке"""

        # Список возможных slug'ов для информации об упокавке
        package_slugs = ['fasovka', 'kolichestvo_v_upakovke', 'kolichestvo_shtuk_v_upakovke']

        # Ищем упаковку в характеристиках товара
        properties = product_data.get('properties', [])
        if isinstance(properties, list):
            for prop in properties:
                slug = prop.get('slug', '')
                if slug in package_slugs:
                    values = prop.get('value', [])
                    if isinstance(values, list) and len(values) > 0:
                        unit = prop.get('unit', '')
                        quantity = values[0].get('title', '')
                        if quantity:
                            if unit:
                                return f"{quantity} {unit}"
                            else:
                                return quantity

        # Ищем через единицу измерения
        unit_title = product_data.get('unit_title', '')
        unit_ratio = product_data.get('unit_ratio')

        if unit_title and unit_ratio:
            return f'{unit_ratio} {unit_title}'

        return 'Нет данных'

    def _extract_attributes(self, product_data: Dict[str, Any]) -> List[Attribute]:
        """Извлекает атрибуты товара"""

        attributes = []
        seen_attributes = set()
        processed_slugs = set()

        excluded_attributes = {
            'brend', 'stranamproizvoditel', 'chasto_ischut',
            'garantiya', 'fasovka', 'kolichestvo_v_upakovke',
            'kolichestvo_shtuk_v_upakovke'
        }

        properties = product_data.get('properties', [])
        if isinstance(properties, list):
            for prop in properties:
                slug = prop.get('slug', '')
                title = prop.get('title', '')
                values = prop.get('value', [])
                unit = prop.get('unit', '')

                processed_slugs.add(slug)

                # Пропускаем исключенные атрибуты
                if slug in excluded_attributes:
                    continue

                # Пропускаем если атрибуты не для описания
                if not prop.get('is_description', True):
                    continue

                if title and values:
                    value_parts = []
                    for val in values:
                        val_title = val.get('title', '')
                        if val_title:
                            value_parts.append(val_title)

                    if value_parts:
                        value_str = ', '.join(value_parts)
                        if unit:
                            attr_name_with_unit = f"{title}, {unit}"
                        else:
                            attr_name_with_unit = title

                        # Проверяем на дубликаты
                        title_lower = title.lower().strip()
                        if title_lower not in seen_attributes:
                            attributes.append(Attribute(
                                attr_name=attr_name_with_unit,
                                attr_value=value_str
                            ))
                            seen_attributes.add(title_lower)

        return attributes

    def _extract_supplier_info(self, product_data: Dict[str, Any], page_url: str) -> List[Supplier]:
        """Извлекает информацию о поставщике и предложениях"""

        suppliers = []

        retail_price = self._extract_retail_price(product_data)
        gold_price = self._extract_gold_price(product_data)
        stock = self._extract_stock(product_data)
        delivery_time = self._extract_delivery_time(product_data)
        package_info = self._extract_package_info(product_data)

        supplier_offers = []

        # Основное предложение (розничная цена)
        if retail_price > 0:
            price_info = PriceInfo(qnt=1, discount=0, price=retail_price)
            retail_offer = SupplierOffer(
                price=[price_info],
                stock=stock,
                delivery_time=delivery_time,
                package_info=package_info,
                purchase_url=page_url
            )
            supplier_offers.append(retail_offer)

        # Предложение по карте (если отличается от розничной)
        if gold_price and gold_price > 0 and gold_price != retail_price:
            gold_price_info = PriceInfo(qnt=1, discount=0, price=gold_price)
            gold_offer = SupplierOffer(
                price=[gold_price_info],
                stock=stock,
                delivery_time=delivery_time,
                package_info=package_info,
                purchase_url=page_url
            )
            supplier_offers.append(gold_offer)

        supplier = Supplier(
            supplier_name='Петрович',
            supplier_tel='8 (499) 334-88-88; 8 (499) 334-88-95',
            supplier_address='г. Москва, ул. Бутырский Вал, д. 68/70 (строение 1), БЦ «Бейкер Плаза», офис 66 (6 этаж)',
            supplier_description='Описание отсутсвует',
            supplier_offers=supplier_offers
        )

        suppliers.append(supplier)
        return suppliers



