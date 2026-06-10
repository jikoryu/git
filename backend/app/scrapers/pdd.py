"""Pinduoduo (拼多多) product scraper.

PDD uses heavy anti-bot measures including CAPTCHAs and API signing.
This implementation uses the mobile web interface (mobile.yangkeduo.com)
which is slightly more accessible.
"""

import logging
import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ProductInfo

logger = logging.getLogger(__name__)


class PddScraper(BaseScraper):
    platform = "pdd"

    _GOODS_ID_RE = re.compile(r"goods_id=(\d+)")
    _PRICE_RE = re.compile(r"[¥￥]?\s*(\d+\.?\d*)")

    async def scrape(self, url: str) -> ProductInfo:
        """Scrape a PDD product page."""
        goods_id = self._extract_goods_id(url)
        client = self._client()

        try:
            # Use mobile web version
            mobile_url = (
                f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}"
            )
            response = await client.get(mobile_url)
            soup = BeautifulSoup(response.text, "lxml")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            image_url = self._extract_image(soup)
            shop_name = self._extract_shop(soup)

            return ProductInfo(
                platform=self.platform,
                platform_id=goods_id,
                title=title or "Unknown Product",
                url=url,
                image_url=image_url,
                shop_name=shop_name,
                current_price=price,
            )

        except Exception as e:
            logger.warning(f"PDD scrape failed for {goods_id}: {e}")
            return ProductInfo(
                platform=self.platform,
                platform_id=goods_id,
                title="Product (fetch pending)",
                url=url,
                current_price=None,
            )

        finally:
            await client.aclose()

    async def search(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> list[ProductInfo]:
        """Search PDD for products."""
        client = self._client()
        try:
            search_url = (
                f"https://mobile.yangkeduo.com/search_result.html"
                f"?search_key={keyword}&page={page}"
            )
            response = await client.get(search_url)
            soup = BeautifulSoup(response.text, "lxml")

            results: list[ProductInfo] = []
            items = soup.select(".goods-item")[:page_size]

            for item in items:
                link_tag = item.select_one("a")
                img_tag = item.select_one("img")
                title_tag = item.select_one(".goods-name") or item.select_one(".title")
                price_tag = item.select_one(".goods-price") or item.select_one(".price")

                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                goods_id = self._extract_goods_id(href)

                title = title_tag.get_text(strip=True) if title_tag else ""
                image = img_tag.get("src") or img_tag.get("data-src", "") if img_tag else None

                price = None
                if price_tag:
                    price_text = price_tag.get_text(strip=True)
                    match = self._PRICE_RE.search(price_text)
                    if match:
                        try:
                            price = float(match.group(1))
                        except ValueError:
                            pass

                results.append(ProductInfo(
                    platform=self.platform,
                    platform_id=goods_id or href,
                    title=title,
                    url=f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}" if goods_id else href,
                    image_url=image,
                    current_price=price,
                ))

            return results

        except Exception as e:
            logger.warning(f"PDD search failed: {e}")
            return []

        finally:
            await client.aclose()

    def _extract_goods_id(self, url: str) -> str:
        """Extract goods_id from a PDD URL."""
        match = self._GOODS_ID_RE.search(url)
        if match:
            return match.group(1)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "goods_id" in params:
            return params["goods_id"][0]
        if "goodsId" in params:
            return params["goodsId"][0]
        return url

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        """Extract product title."""
        selectors = [
            ".goods-name",
            ".goods-title",
            "h1",
            "title",
        ]
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                if text and len(text) > 2:
                    return text
        return None

    def _extract_price(self, soup: BeautifulSoup) -> float | None:
        """Extract current price."""
        selectors = [
            ".goods-price",
            ".current-price",
            ".price",
            ".price-now",
        ]
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                match = self._PRICE_RE.search(text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None

    def _extract_image(self, soup: BeautifulSoup) -> str | None:
        """Extract main product image."""
        img = soup.select_one(".goods-img img") or soup.select_one(".main-image img")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                return f"https:{src}" if src.startswith("//") else src
        return None

    def _extract_shop(self, soup: BeautifulSoup) -> str | None:
        """Extract shop/mall name."""
        shop = (
            soup.select_one(".mall-name")
            or soup.select_one(".shop-name")
            or soup.select_one(".seller-name")
        )
        if shop:
            return shop.get_text(strip=True)
        return None
