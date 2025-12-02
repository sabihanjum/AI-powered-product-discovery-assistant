"""
Simple scraper scaffold. Implement site-specific scraping logic here.
For JS-heavy sites consider using Playwright or a paid scraping API.
"""
from typing import List, Dict
import requests
from bs4 import BeautifulSoup


def scrape_site(site: str) -> List[Dict]:
    """Return a list of product dicts with fields matching schemas.ProductCreate.
    This is a scaffold that currently returns mock/sample items. Replace
    with real scraping logic for `furlenco`, `hunnit` or `traya`.
    """
    site = site.lower()
    results = []

    # Real site scrapers
    if site in ("traya", "traya.health"):
        try:
            from .traya_scraper import scrape_traya

            results = scrape_traya(max_products=100, delay=1.0)
        except Exception:
            results = []
    elif site in ("furlenco", "furlenco.com"):
        # placeholder for furlenco scraper implementation
        results = []
    else:
        # Quick mock fallback for development
        for i in range(1, 6):
            results.append(
                {
                    "title": f"Sample Product {i} ({site})",
                    "price": "N/A",
                    "description": f"This is a sample description for product {i} scraped from {site}.",
                    "features": {"color": "black", "size": "M"},
                    "image_url": "https://via.placeholder.com/300",
                    "category": "sample",
                    "source_url": f"https://{site}/product/{i}",
                }
            )

    return results
