"""
Site-specific scraper for traya.health
This module attempts to find product pages under the traya.health domain, fetch each product page,
and extract fields required by the Product schema: title, price, description, features, image_url, category, source_url.

The scraper uses a crawler-like approach: start from a small set of seed pages and collect unique
product links containing '/products/'. It's defensive and uses common metadata tags as fallbacks.
"""
from typing import List, Dict
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

DOMAIN = "traya.health"


def is_product_url(href: str) -> bool:
    if not href:
        return False
    return "/products/" in href and DOMAIN in href


def extract_text_or_none(soup, selectors):
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return None


def fetch_product(url: str) -> Dict:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")

    # title: prefer h1 or og:title
    title = None
    if soup.title:
        title = soup.title.string.strip()
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title.get("content").strip()

    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)

    # price: look for meta tags or classes containing 'price'
    price = None
    price_meta = soup.find("meta", property="product:price:amount")
    if price_meta and price_meta.get("content"):
        price = price_meta.get("content")
    # fallback find price-like text
    price_el = soup.select_one(".price, .product-price, .price--main, .product__price")
    if price_el:
        price = price_el.get_text(strip=True)

    # description
    description = None
    desc_meta = soup.find("meta", attrs={"name": "description"})
    if desc_meta and desc_meta.get("content"):
        description = desc_meta.get("content").strip()
    if not description:
        desc = soup.select_one(".product-description, .description, #description, .product__description")
        if desc:
            description = desc.get_text(separator=" ", strip=True)

    # features: gather list items in feature sections
    features = {}
    feature_sections = soup.select(".product-features, .features, .product-details, .product-specs")
    for sec in feature_sections:
        items = sec.find_all(["li", "p"])
        for it in items:
            text = it.get_text(strip=True)
            if ":" in text:
                k, v = map(str.strip, text.split(":", 1))
                features[k] = v
            else:
                # fallback numbered keys
                features.setdefault("features", []).append(text)

    # images: og:image or first product image
    image_url = None
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image_url = og_img.get("content")
    # fallback to product image selectors
    img = soup.select_one("img.product__image, img.featured-image, img[src*='/products/']")
    if img and img.get("src"):
        image_url = urljoin(url, img.get("src"))

    # category: try breadcrumb or meta tags
    category = None
    breadcrumb = soup.select_one(".breadcrumb, .breadcrumbs")
    if breadcrumb:
        parts = [a.get_text(strip=True) for a in breadcrumb.find_all("a") if a.get_text(strip=True)]
        if parts:
            category = parts[-1]

    data = {
        "title": title or "",
        "price": price or "",
        "description": description or "",
        "features": features or None,
        "image_url": image_url or "",
        "category": category or "",
        "source_url": url,
    }

    return data


def scrape_traya(max_products: int = 100, delay: float = 1.0) -> List[Dict]:
    """Crawl a few seed pages and collect product pages, return list of product dicts.
    The function is conservative about requests (includes delay).
    """
    seeds = ["https://traya.health/", "https://traya.health/collections/all", "https://traya.health/collections"]
    found = set()
    product_urls = []

    for seed in seeds:
        try:
            r = requests.get(seed, timeout=15)
            r.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(seed, a["href"]) if a["href"].startswith("/") else a["href"]
            parsed = urlparse(href)
            if DOMAIN not in parsed.netloc:
                continue
            if is_product_url(href) and href not in found:
                found.add(href)
                product_urls.append(href)
            if len(product_urls) >= max_products:
                break
        if len(product_urls) >= max_products:
            break
        time.sleep(delay)

    # Now fetch each product page
    products = []
    for url in product_urls:
        data = fetch_product(url)
        if data and data.get("title"):
            products.append(data)
        time.sleep(delay)
        if len(products) >= max_products:
            break

    return products
