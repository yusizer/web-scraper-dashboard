"""Tests for the scraper: price extraction, parsing, and API routes."""
import httpx
import pytest

from app import web
from app.scraper import extract_price, parse_html

SAMPLE_HTML = """
<html><head><title>Demo Shop</title></head><body>
  <h1>Demo Shop</h1>
  <div class="product-card"><h3>Coffee Mug</h3><span>$12.99</span></div>
  <div class="product-card"><h3>T-Shirt</h3><span>€19.95</span></div>
  <div class="product-card"><h3>Book</h3><span>250 000 сум</span></div>
  <p>Free shipping over $50</p>
</body></html>
"""


# --- Unit: price extraction ---

def test_extract_price_dollar():
    assert extract_price("Coffee Mug $12.99") == "$12.99"

def test_extract_price_euro():
    assert "19.95" in extract_price("T-Shirt €19.95")

def test_extract_price_sum():
    assert "250 000" in extract_price("Book 250 000 сум")

def test_extract_price_none():
    assert extract_price("no price here") is None


# --- Unit: parsing ---

def test_parse_with_selector():
    title, items = parse_html(SAMPLE_HTML, ".product-card")
    assert title == "Demo Shop"
    assert len(items) == 3
    assert any("12.99" in (i["price"] or "") for i in items)
    assert any("Coffee Mug" in i["label"] for i in items)

def test_parse_generic_finds_prices():
    title, items = parse_html(SAMPLE_HTML, None)
    assert title == "Demo Shop"
    assert len(items) > 0
    prices = [i["price"] for i in items if i["price"]]
    assert any("12.99" in p or "19.95" in p for p in prices)


# --- API routes ---

async def _fake_fetch(url):
    return SAMPLE_HTML


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_api_scrape(client, monkeypatch):
    monkeypatch.setattr(web, "fetch_html", _fake_fetch)
    r = await client.get("/api/scrape", params={"url": "http://example.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["page_title"] == "Demo Shop"
    assert data["item_count"] > 0
    assert any("12.99" in (i["price"] or "") for i in data["items"])


async def test_api_scrape_with_selector(client, monkeypatch):
    monkeypatch.setattr(web, "fetch_html", _fake_fetch)
    r = await client.get(
        "/api/scrape", params={"url": "http://example.com", "selector": ".product-card"}
    )
    assert r.status_code == 200
    assert r.json()["item_count"] == 3


async def test_api_scrape_error(client, monkeypatch):
    async def boom(url):
        raise httpx.ConnectError("connection refused")
    monkeypatch.setattr(web, "fetch_html", boom)
    r = await client.get("/api/scrape", params={"url": "http://nope.invalid"})
    assert r.status_code == 200  # graceful: returns error in body
    assert "error" in r.json()


async def test_form_scrape_persists_and_redirects(client, monkeypatch):
    monkeypatch.setattr(web, "fetch_html", _fake_fetch)
    r = await client.post(
        "/scrape",
        data={"url": "http://example.com", "selector": ".product-card"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    location = r.headers["location"]
    assert location.startswith("/scrape/")

    r2 = await client.get(location)
    assert r2.status_code == 200
    assert "Coffee Mug" in r2.text


async def test_history_page(client, monkeypatch):
    monkeypatch.setattr(web, "fetch_html", _fake_fetch)
    await client.post("/scrape", data={"url": "http://example.com"})
    r = await client.get("/history")
    assert r.status_code == 200
    assert "example.com" in r.text
