# Web Scraper + Dashboard 🕸️

![CI](https://github.com/yusizer/web-scraper-dashboard/actions/workflows/ci.yml/badge.svg)
**Live demo:** https://web-scraper-dashboard-ba4x.onrender.com/

Enter a URL → the scraper pulls out price-shaped snippets (or exactly the
elements you select) and shows them in a web dashboard, with a persistent
history of every scrape. FastAPI + BeautifulSoup, Dockerized, tested.

> **Live demo:** _<добавь Railway-домен>_ ·
> **Source:** https://github.com/yusizer/web-scraper-dashboard

## Features

- **Generic mode**: no selector needed — scans the page for price-shaped snippets
  (`$12.99`, `€19.95`, `250 000 сум`, `1 299 руб`, `USD 50`, …) with their context.
- **Precise mode**: pass a CSS selector (e.g. `.product-card`) to extract exactly
  those elements — reliable for a known site structure.
- **Dashboard**: web UI with a form, a results table, and a history of past scrapes.
- **JSON API**: `GET /api/scrape?url=...&selector=...` for programmatic use.
- **Persistent history**: every scrape is stored in SQLite with its items.
- **Swagger UI** at `/docs`, health at `/health`.
- **Robust**: timeouts, a browser-like User-Agent, graceful error handling.

## Stack

| Layer   | Technology                              |
|---------|-----------------------------------------|
| API/UI  | FastAPI + Jinja2 + Bootstrap 5          |
| Scraping| httpx (async) + BeautifulSoup           |
| DB      | SQLAlchemy 2 (async) + aiosqlite        |
| Tests   | pytest, httpx, pytest-asyncio           |
| Deploy  | Docker → Railway                        |

## Structure

```
web-scraper-dashboard/
├── app/
│   ├── __main__.py     # entrypoint (uvicorn)
│   ├── config.py       # settings from .env
│   ├── models.py       # ScrapeJob, ScrapeItem
│   ├── database.py     # async engine + get_db
│   ├── scraper.py      # fetch_html + parse_html (price extraction)
│   └── web.py          # FastAPI routes + dashboard templates
│   └── templates/      # base / dashboard / results / history
├── tests/              # unit + API tests (mocked fetch)
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
python -m app
```

- Dashboard: http://localhost:8000
- Swagger:  http://localhost:8000/docs
- Health:   http://localhost:8000/health

### Try it

1. Open http://localhost:8000
2. Paste a product page URL (e.g. a shop's category page) → **Scrape**
3. See extracted price snippets in the table
4. For precision, add a CSS selector like `.product-card` or `.price`

### JSON API

```bash
curl "http://localhost:8000/api/scrape?url=https://example.com&selector=.product-card"
```

## Run tests

```bash
pip install -r requirements.txt
pytest -v
```

## Deploy to Railway

1. Push the repo to GitHub.
2. https://railway.app → **New Project → Deploy from GitHub repo** → select this repo.
3. Railway auto-detects the `Dockerfile`.
4. **Variables** (optional): `DATABASE_URL`, `REQUEST_TIMEOUT_SECONDS`, `MAX_ITEMS`.
5. Railway sets `PORT` automatically.
6. Open the public domain → the dashboard is your live demo.

## API reference

| Method | Path                | Description                          |
|--------|---------------------|--------------------------------------|
| GET    | /                   | Dashboard (form + recent scrapes)    |
| POST   | /scrape             | Run a scrape (form: url, selector)   |
| GET    | /scrape/{id}        | View a past scrape's results         |
| GET    | /history            | Full scrape history                  |
| GET    | /api/scrape         | JSON scrape (url, selector)          |
| GET    | /health             | Health check                         |

## Notes & ethics

- Scrapes **public** pages only, with a descriptive User-Agent and timeouts.
- Many sites serve prices via JavaScript (not in the initial HTML); for those,
  the CSS-selector mode against the rendered DOM or a headless browser
  (Playwright) would be the next step — happy to extend on request.
- Always respect a site's terms of service and `robots.txt` for production use.

## Screenshots

| Dashboard | Results |
|:---:|:---:|
| ![dashboard](docs/dashboard.png) | ![results](docs/results.png) |

_Drop screenshots in `docs/` after running._
