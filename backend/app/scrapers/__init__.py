"""Scraper registry — maps platform names and URL patterns to scraper instances."""

import re

from app.scrapers.base import BaseScraper, ProductInfo
from app.scrapers.jd import JdScraper
from app.scrapers.taobao import TaobaoScraper
from app.scrapers.pdd import PddScraper

# Platform URL patterns
URL_PATTERNS: dict[str, re.Pattern] = {
    "jd": re.compile(r"https?://(?:item\.)?jd\.com/", re.IGNORECASE),
    "taobao": re.compile(r"https?://(?:item\.)?taobao\.com/", re.IGNORECASE),
    "pdd": re.compile(r"https?://(?:mobile\.)?yangkeduo\.com/|https?://(?:www\.)?pinduoduo\.com/", re.IGNORECASE),
}

SCRAPERS: dict[str, BaseScraper] = {
    "jd": JdScraper(),
    "taobao": TaobaoScraper(),
    "pdd": PddScraper(),
}


def get_scraper_for_url(url: str) -> BaseScraper | None:
    """Return the appropriate scraper for the given product URL, or None."""
    for platform, pattern in URL_PATTERNS.items():
        if pattern.search(url):
            return SCRAPERS.get(platform)
    return None


__all__ = ["BaseScraper", "ProductInfo", "get_scraper_for_url", "SCRAPERS"]
