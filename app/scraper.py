"""Fetching + parsing logic for the web scraper."""
import re

import httpx
from bs4 import BeautifulSoup

from .config import settings

USER_AGENT = (
    "Mozilla/5.0 (compatible; PortfolioScraperBot/1.0; "
    "+https://github.com/yusizer)"
)

# Price-shaped strings with a currency context (symbol or code).
_PRICE_RE = re.compile(
    r"(?:USD|EUR|UZS|RUB|KGS|TMT|сум|руб|so['’]?m|som|\$|€|₽)\s?\d[\d.,\s]{0,14}\d"
    r"|\d[\d.,\s]{0,14}\d\s?(?:USD|EUR|UZS|RUB|сум|руб)",
    re.IGNORECASE,
)

# Tags likely to hold a product title + price in one snippet.
_TEXT_TAGS = ["h1", "h2", "h3", "h4", "p", "span", "div", "li", "td", "a", "b", "strong"]


def extract_price(text: str) -> str | None:
    """Return the first price-shaped substring in `text`, or None."""
    m = _PRICE_RE.search(text)
    return m.group(0).strip() if m else None


async def fetch_html(url: str) -> str:
    """Download the HTML at `url` with a browser-like User-Agent."""
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=settings.request_timeout_seconds,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def parse_html(html: str, selector: str | None = None) -> tuple[str, list[dict]]:
    """Parse `html` into (page_title, items).

    If `selector` is given, extract matching elements (precise mode).
    Otherwise, scan visible text for price-shaped snippets (generic mode).
    """
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(strip=True) if soup.title else ""

    items: list[dict] = []
    seen: set[str] = set()
    max_items = settings.max_items

    if selector:
        for el in soup.select(selector):
            text = el.get_text(" ", strip=True)
            if not text:
                continue
            items.append(
                {
                    "label": text[:160],
                    "price": extract_price(text),
                    "value": text[:300],
                }
            )
            if len(items) >= max_items:
                break
        return page_title, items

    # Generic mode: collect snippets that contain a price.
    for tag in soup.find_all(_TEXT_TAGS):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) > 300:
            continue
        price = extract_price(text)
        if not price:
            continue
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        items.append({"label": text[:160], "price": price, "value": text[:300]})
        if len(items) >= max_items:
            break

    return page_title, items
