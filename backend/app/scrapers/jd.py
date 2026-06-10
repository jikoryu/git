"""JD.com (京东) product scraper."""

import json
import logging
import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ProductInfo

logger = logging.getLogger(__name__)


class JdScraper(BaseScraper):
    platform = "jd"

    # JD item ID patterns
    _SKU_RE = re.compile(r"/(\d+)\.html")
    _PRICE_RE = re.compile(r'"p":"(\d+\.?\d*)"')

    async def scrape(self, url: str) -> ProductInfo:
        """Scrape a JD product page for title, price, and metadata."""
        sku_id = self._extract_sku(url)
        client = self._client()

        try:
            # Fetch product page HTML
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Extract title
            title = ""
            title_tag = soup.select_one(".sku-name") or soup.select_one("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Extract price via JD's price API
            price = None
            try:
                price_url = (
                    f"https://p.3.cn/prices/mgets"
                    f"?skuIds=J_{sku_id}"
                )
                price_resp = await client.get(price_url)
                price_data = price_resp.json()
                if price_data and "p" in price_data[0]:
                    price = float(price_data[0]["p"])
            except Exception as e:
                logger.warning(f"JD price API failed for {sku_id}: {e}")
                # Try to extract from page as fallback
                price = self._extract_price_from_page(soup)

            # Extract image
            image_url = None
            img_tag = soup.select_one("#spec-img")
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-origin")

            # Extract shop name
            shop_name = None
            shop_tag = soup.select_one(".J-hove-wrap .name a") or soup.select_one(".shop-name")
            if shop_tag:
                shop_name = shop_tag.get_text(strip=True)

            return ProductInfo(
                platform=self.platform,
                platform_id=sku_id,
                title=title or "Unknown Product",
                url=url,
                image_url=f"https:{image_url}" if image_url and image_url.startswith("//") else image_url,
                shop_name=shop_name,
                current_price=price,
            )

        finally:
            await client.aclose()

    async def search(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> list[ProductInfo]:
        """Search JD for products matching the keyword."""
        client = self._client()
        try:
            search_url = (
                f"https://search.jd.com/Search"
                f"?keyword={keyword}&page={page}&psort=3"
            )
            response = await client.get(search_url)
            soup = BeautifulSoup(response.text, "lxml")

            results: list[ProductInfo] = []
            items = soup.select(".gl-item")[:page_size]

            for item in items:
                sku = item.get("data-sku", "")
                link_tag = item.select_one(".p-name a")
                img_tag = item.select_one(".p-img img")
                price_tag = item.select_one(".p-price i")

                if not sku or not link_tag:
                    continue

                title = link_tag.get_text(strip=True) or link_tag.get("title", "")
                image = img_tag.get("src") or img_tag.get("data-lazy-img", "") if img_tag else None
                price_str = price_tag.get_text(strip=True) if price_tag else ""
                try:
                    price = float(price_str.replace(",", "")) if price_str else None
                except ValueError:
                    price = None

                results.append(ProductInfo(
                    platform=self.platform,
                    platform_id=sku,
                    title=title,
                    url=f"https://item.jd.com/{sku}.html",
                    image_url=f"https:{image}" if image and image.startswith("//") else image,
                    current_price=price,
                ))

            return results

        finally:
            await client.aclose()

    def _extract_sku(self, url: str) -> str:
        """Extract the JD SKU ID from a product URL."""
        match = self._SKU_RE.search(url)
        if match:
            return match.group(1)
        # Try query parameter
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "sku" in params:
            return params["sku"][0]
        return url  # fallback

    def _extract_price_from_page(self, soup: BeautifulSoup) -> float | None:
        """Extract price from embedded page scripts as a fallback."""
        for script in soup.find_all("script"):
            if script.string and '"p":"' in script.string:
                match = self._PRICE_RE.search(script.string)
                if match:
                    return float(match.group(1))
        return None
