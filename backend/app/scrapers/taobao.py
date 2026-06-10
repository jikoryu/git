"""Taobao (淘宝) product scraper.

Taobao's anti-scraping is aggressive. This implementation:
1. Tries to use the mobile-optimized pages (h5.m.taobao.com)
2. Falls back to page-level extraction for basic info
3. In development, uses mock data when scraping is blocked
"""

import logging
import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ProductInfo

logger = logging.getLogger(__name__)


class TaobaoScraper(BaseScraper):
    platform = "taobao"

    _ID_RE = re.compile(r"[?&]id=(\d+)")

    async def scrape(self, url: str) -> ProductInfo:
        """Scrape a Taobao product page."""
        item_id = self._extract_item_id(url)
        client = self._client()

        try:
            # Try mobile page first (less aggressive anti-bot)
            mobile_url = f"https://h5.m.taobao.com/awp/core/detail.htm?id={item_id}"
            response = await client.get(mobile_url)
            soup = BeautifulSoup(response.text, "lxml")

            title = self._extract_title(soup)
            price = self._extract_price(soup)
            image_url = self._extract_image(soup)
            shop_name = self._extract_shop(soup)

            if not title:
                # Try desktop page as fallback
                response = await client.get(url)
                soup = BeautifulSoup(response.text, "lxml")
                title = self._extract_title(soup) or "Unknown Product"
                price = price or self._extract_price(soup)

            return ProductInfo(
                platform=self.platform,
                platform_id=item_id,
                title=title or "Unknown Product",
                url=url,
                image_url=image_url,
                shop_name=shop_name,
                current_price=price,
            )

        except Exception as e:
            logger.warning(f"Taobao scrape failed for {item_id}: {e}")
            # Return minimal info — the product URL and ID may still be useful
            return ProductInfo(
                platform=self.platform,
                platform_id=item_id,
                title="Product (fetch pending)",
                url=url,
                current_price=None,
            )

        finally:
            await client.aclose()

    async def search(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> list[ProductInfo]:
        """Search Taobao for products. Uses the s.taobao.com search page."""
        client = self._client()
        try:
            search_url = (
                f"https://s.taobao.com/search"
                f"?q={keyword}&s={ (page - 1) * page_size}"
            )
            response = await client.get(
                search_url,
                headers={
                    **client.headers,
                    "Referer": "https://www.taobao.com/",
                },
            )
            soup = BeautifulSoup(response.text, "lxml")

            results: list[ProductInfo] = []
            items = soup.select(".item")[:page_size]

            for item in items:
                link_tag = item.select_one(".title a") or item.select_one("a.J_ClickStat")
                img_tag = item.select_one(".pic img") or item.select_one("img")
                price_tag = item.select_one(".price strong") or item.select_one(".price")

                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                title = link_tag.get_text(strip=True) or link_tag.get("title", "")
                item_id = self._extract_item_id(href)

                image = img_tag.get("src") or img_tag.get("data-src", "") if img_tag else None
                price_str = price_tag.get_text(strip=True) if price_tag else ""
                try:
                    price = float(re.sub(r"[¥￥,]", "", price_str)) if price_str else None
                except ValueError:
                    price = None

                results.append(ProductInfo(
                    platform=self.platform,
                    platform_id=item_id or href,
                    title=title,
                    url=f"https:{href}" if href.startswith("//") else href,
                    image_url=f"https:{image}" if image and image.startswith("//") else image,
                    current_price=price,
                ))

            return results

        except Exception as e:
            logger.warning(f"Taobao search failed: {e}")
            return []

        finally:
            await client.aclose()

    def _extract_item_id(self, url: str) -> str:
        """Extract the numeric item ID from a Taobao URL."""
        match = self._ID_RE.search(url)
        if match:
            return match.group(1)
        # Try path-based (e.g., /item.htm?...)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "id" in params:
            return params["id"][0]
        return url

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        """Try multiple selectors to extract product title."""
        selectors = [
            ".tb-main-title",
            ".ItemTitle--mainTitle--",
            "h1[data-spm='1000983']",
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
        """Try multiple selectors to extract price."""
        selectors = [
            ".tb-rmb-num",
            ".Price--price--",
            ".tm-price",
            "#J_StrPrice .tb-rmb-num",
        ]
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                text = tag.get_text(strip=True)
                try:
                    return float(re.sub(r"[¥￥,\s]", "", text))
                except ValueError:
                    continue

        # Try meta tag
        meta = soup.select_one('meta[property="product:price:amount"]')
        if meta and meta.get("content"):
            try:
                return float(meta["content"])
            except ValueError:
                pass
        return None

    def _extract_image(self, soup: BeautifulSoup) -> str | None:
        """Try to extract the main product image."""
        img = soup.select_one("#J_ImgBooth") or soup.select_one(".tb-main-pic img")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                return f"https:{src}" if src.startswith("//") else src
        return None

    def _extract_shop(self, soup: BeautifulSoup) -> str | None:
        """Extract shop/seller name."""
        shop = soup.select_one(".tb-shop-name") or soup.select_one(".slogo-shopname")
        if shop:
            return shop.get_text(strip=True)
        return None
