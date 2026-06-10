"""Abstract base class for platform-specific scrapers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass
class ProductInfo:
    """Scraped product information."""
    platform: str
    platform_id: str
    title: str
    url: str
    image_url: str | None = None
    shop_name: str | None = None
    current_price: float | None = None


class BaseScraper(ABC):
    """Base scraper with shared HTTP client configuration."""

    platform: str = ""

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={
                "User-Agent": settings.user_agent,
                "Accept": "text/html,application/json,application/xhtml+xml,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            follow_redirects=True,
        )

    @abstractmethod
    async def scrape(self, url: str) -> ProductInfo:
        """Scrape product info from the given URL."""
        ...

    @abstractmethod
    async def search(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> list[ProductInfo]:
        """Search for products on the platform."""
        ...
