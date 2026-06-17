"""SQLAlchemy models."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048))
    selector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_title: Mapped[str] = mapped_column(String(500), default="")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ok")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScrapeItem(Base):
    __tablename__ = "scrape_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("scrape_jobs.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(300))
    price: Mapped[str | None] = mapped_column(String(60), nullable=True)
    value: Mapped[str] = mapped_column(Text, default="")
