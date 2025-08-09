from typing import Optional

import httpx
import logging

logger = logging.getLogger(__name__)


class PageScraper:

    async def scrape_page(self, url: str) -> Optional[str]:

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://moscow.petrovich.ru",
            "Referer": "https://moscow.petrovich.ru/product/670672/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not.A/Brand";v="99", "Chromium";v="136"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "x-requested-with": "XmlHttpRequest"
        }

        cookies = {
            "ipp_uid": "1754493585232/cG8B1jnMptHWCQwJ/WolH2e1EeqAflCPwkwQvSQ==",
            "SIK": "hgAAALyMNj63g7EXHhENAA",
            "SIV": "1",
            "C_ipXynw3BnsEVcA78fad9znijNwk": "AAAAAAAACEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA8D8AAOA2NHXqQf1w3F0hA8pZopMzKIQeSD8",
            "rerf": "AAAAAGiTcpJO5YfeAxOIAg==",
            "*userGUID": "0:me046krt:9tUH6TnSw169IM9WyTYSmO7wMf*fLGkq",
            "*ym*uid": "1754493588969040631",
            "*ym*d": "1754493588",
            "popmechanic_sbjs_migrations": "popmechanic_1418474375998%3D1%7C%7C%7C1471519752600%3D1%7C%7C%7C1471519752605%3D1",
            "a_b": "installment%3D1",
            "FPID": "e167a8d5-c37e-4c10-b78d-869b255b56f7%3D",
            "count_buy": "0",
            "ser_ym_uid": "1754493588969040631",
            "js_FPID": "e167a8d5-c37e-4c10-b78d-869b255b56f7%3D",
            "SNK": "131",
            "u__typeDevice": "desktop",
            "*ym*isad": "1",
            "u__geoCityCode": "msk",
            "ipp_key": "v1754658617713/93f78bcdd5/leJFMLfl7BT2XhBq9h+ndFu4XTS5l1OJlagM+t7PaWOcBjtmhk2TnWnAOxOpNSciX+o4SAqyxjkA9XS30g/6LA==",
            "dSesn": "d02280b6-7a21-dc68-fae7-a2fa80200b0a",
            "*ym*visorc": "b",
            "mindboxDeviceUUID": "ad4914dc-6a56-4297-b93d-7c95869f04d4",
            "directCrm-session": "%7B%22deviceGuid%22%3A%22ad4914dc-6a56-4297-b93d-7c95869f04d4%22%7D"
        }

        async with httpx.AsyncClient(follow_redirects = True, timeout = 30) as client:
            try:
                response = await client.get(url, headers=headers, cookies=cookies)
                return response.text
            except Exception as e:
                logger.error(f"Ошибка при получении html: {e}")
                return None
