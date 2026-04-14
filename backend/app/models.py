from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db import Base


class SourceType(str, enum.Enum):
    rss = "rss"
    api = "api"


class ProductionFormat(str, enum.Enum):
    short = "short"
    long = "long"
    community = "community"


class Status(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    reliability: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RawItem(Base):
    __tablename__ = "raw_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship()


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_key: Mapped[str] = mapped_column(String(200), index=True)
    topic: Mapped[str] = mapped_column(String(64), default="general")
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sources: Mapped[list["EventSource"]] = relationship(back_populates="event")


class EventSource(Base):
    __tablename__ = "event_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"), nullable=False)

    event: Mapped[Event] = relationship(back_populates="sources")
    raw_item: Mapped[RawItem] = relationship()


class Production(Base):
    __tablename__ = "productions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    format: Mapped[ProductionFormat] = mapped_column(Enum(ProductionFormat), nullable=False)
    rules_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.pending)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assets: Mapped[list["Asset"]] = relationship(back_populates="production")


class AssetKind(str, enum.Enum):
    script = "script"
    audio = "audio"
    image = "image"
    video = "video"
    thumb = "thumb"
    srt = "srt"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_id: Mapped[int] = mapped_column(ForeignKey("productions.id"), nullable=False, index=True)
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    production: Mapped[Production] = relationship(back_populates="assets")


class YouTubeUpload(Base):
    __tablename__ = "youtube_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_id: Mapped[int] = mapped_column(ForeignKey("productions.id"), nullable=False, index=True)
    video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.pending)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

