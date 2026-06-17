"""FastAPI app: scraper dashboard + JSON API."""
from pathlib import Path

import httpx
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from .database import SessionLocal, get_db, init_db
from .models import ScrapeItem, ScrapeJob
from .scraper import fetch_html, parse_html

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title="Web Scraper Dashboard", version="1.0.0")


@app.on_event("startup")
async def _on_startup() -> None:
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Dashboard pages ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with SessionLocal() as session:
        jobs = (
            await session.execute(
                select(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(10)
            )
        ).scalars().all()
    return templates.TemplateResponse(request, "dashboard.html", {"jobs": jobs})


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    async with SessionLocal() as session:
        jobs = (
            await session.execute(
                select(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(100)
            )
        ).scalars().all()
    return templates.TemplateResponse(request, "history.html", {"jobs": jobs})


@app.get("/scrape/{job_id}", response_class=HTMLResponse)
async def view_job(request: Request, job_id: int):
    async with SessionLocal() as session:
        job = await session.get(ScrapeJob, job_id)
        if not job:
            return RedirectResponse("/", status_code=303)
        items = (
            await session.execute(
                select(ScrapeItem).where(ScrapeItem.job_id == job_id)
            )
        ).scalars().all()
    return templates.TemplateResponse(
        request, "results.html", {"job": job, "items": items}
    )


# --- Scraping actions ---

async def _run_scrape(url: str, selector: str | None) -> ScrapeJob:
    """Fetch, parse, persist, and return the ScrapeJob (with id)."""
    job = ScrapeJob(url=url, selector=selector or None)
    try:
        html = await fetch_html(url)
        page_title, items = parse_html(html, selector)
        job.page_title = page_title
        job.item_count = len(items)
        job.status = "ok"
    except httpx.HTTPError as exc:
        job.status = "error"
        job.error = str(exc)
        job.item_count = 0
        items = []
    except Exception as exc:  # parsing errors etc.
        job.status = "error"
        job.error = f"{type(exc).__name__}: {exc}"
        job.item_count = 0
        items = []

    async with SessionLocal() as session:
        session.add(job)
        await session.flush()
        for it in items:
            session.add(
                ScrapeItem(
                    job_id=job.id,
                    label=it["label"],
                    price=it["price"],
                    value=it["value"],
                )
            )
        await session.commit()
        await session.refresh(job)
    return job


@app.post("/scrape")
async def scrape_form(url: str = Form(...), selector: str = Form("")):
    job = await _run_scrape(url, selector.strip() or None)
    return RedirectResponse(f"/scrape/{job.id}", status_code=303)


@app.get("/api/scrape")
async def scrape_api(
    url: str = Query(...),
    selector: str | None = Query(default=None),
):
    """JSON endpoint for programmatic use. Does not persist to history."""
    try:
        html = await fetch_html(url)
        page_title, items = parse_html(html, selector)
        return {
            "url": url,
            "page_title": page_title,
            "item_count": len(items),
            "items": items,
        }
    except httpx.HTTPError as exc:
        return {"url": url, "error": str(exc), "items": []}
