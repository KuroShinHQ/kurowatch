from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Boolean, Float, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

# ── İçerik Tipleri & Durum Enum'ları ────────────────────────────────
CONTENT_TYPES = ("anime", "manga", "manhwa", "game")
STATUS_VALUES = ("watching", "completed", "on_hold", "dropped", "planning", "rewatching")
TAG_TYPES     = ("api", "user")


class Content(Base):
    __tablename__ = "content"

    id:              Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    title:           Mapped[str]            = mapped_column(String(500), nullable=False)
    type:            Mapped[str]            = mapped_column(String(20),  nullable=False)   # CONTENT_TYPES
    cover_url:       Mapped[Optional[str]]  = mapped_column(Text,   nullable=True)
    external_id:     Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)   # AniList/IGDB id
    status:          Mapped[str]            = mapped_column(String(20),  nullable=False, default="planning")
    total_episodes:  Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    total_chapters:  Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    my_progress:     Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    my_progress_pct: Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)  # oyunlar
    my_score:        Mapped[Optional[float]]= mapped_column(Float,   nullable=True)
    external_score:  Mapped[Optional[float]]= mapped_column(Float,   nullable=True)  # AniList averageScore/10
    note_text:       Mapped[Optional[str]]  = mapped_column(Text,    nullable=True)
    note_is_spoiler: Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    synopsis:        Mapped[Optional[str]]  = mapped_column(Text,    nullable=True)   # EN (AniList/IGDB'den)
    synopsis_tr:     Mapped[Optional[str]]  = mapped_column(Text,    nullable=True)   # TR çeviri
    genres:          Mapped[Optional[str]]  = mapped_column(Text,    nullable=True)   # JSON list: ["Action","Fantasy"]
    added_at:        Mapped[datetime]       = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at:      Mapped[datetime]       = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sites:    Mapped[List["Site"]]       = relationship("Site",       back_populates="content", cascade="all, delete-orphan")
    episodes: Mapped[List["Episode"]]    = relationship("Episode",    back_populates="content", cascade="all, delete-orphan")
    updates:  Mapped[List["Update"]]     = relationship("Update",     back_populates="content", cascade="all, delete-orphan")
    tags:     Mapped[List["ContentTag"]] = relationship("ContentTag", back_populates="content", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "site"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("content.id"), nullable=False)
    site_name:      Mapped[str]           = mapped_column(String(200), nullable=False)
    site_url:       Mapped[str]           = mapped_column(Text,        nullable=False)
    is_primary:     Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    latest_known_ep:Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    content: Mapped["Content"] = relationship("Content", back_populates="sites")


class Episode(Base):
    __tablename__ = "episode"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int]            = mapped_column(Integer, ForeignKey("content.id"), nullable=False)
    season:     Mapped[int]            = mapped_column(Integer, nullable=False, default=1)
    number:     Mapped[int]            = mapped_column(Integer, nullable=False)
    title:      Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    url:        Mapped[Optional[str]]  = mapped_column(Text,        nullable=True)
    is_watched: Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    watched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_new:     Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)

    content: Mapped["Content"] = relationship("Content", back_populates="episodes")


class Update(Base):
    __tablename__ = "update"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id:     Mapped[int]      = mapped_column(Integer, ForeignKey("content.id"), nullable=False)
    episode_number: Mapped[int]      = mapped_column(Integer, nullable=False)
    site_name:      Mapped[str]      = mapped_column(String(200), nullable=False)
    detected_at:    Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    is_read:        Mapped[bool]     = mapped_column(Boolean, nullable=False, default=False)

    content: Mapped["Content"] = relationship("Content", back_populates="updates")


class Tag(Base):
    __tablename__ = "tag"

    id:       Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:     Mapped[str]           = mapped_column(String(100), nullable=False, unique=True)
    tag_type: Mapped[str]           = mapped_column(String(10),  nullable=False, default="user")  # TAG_TYPES
    color:    Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    contents: Mapped[List["ContentTag"]] = relationship("ContentTag", back_populates="tag", cascade="all, delete-orphan")


class ContentTag(Base):
    __tablename__ = "content_tag"

    content_id: Mapped[int] = mapped_column(Integer, ForeignKey("content.id"), primary_key=True)
    tag_id:     Mapped[int] = mapped_column(Integer, ForeignKey("tag.id"),     primary_key=True)

    content: Mapped["Content"] = relationship("Content", back_populates="tags")
    tag:     Mapped["Tag"]     = relationship("Tag",     back_populates="contents")


class IntroTimestamp(Base):
    """FAZ-4: Chromaprint ile tespit edilen intro başlangıç/bitiş zamanları."""
    __tablename__ = "intro_timestamp"

    id:             Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id:     Mapped[int]   = mapped_column(Integer, nullable=False)
    episode_number: Mapped[int]   = mapped_column(Integer, nullable=False)
    intro_start:    Mapped[float] = mapped_column(Float,   nullable=False)  # saniye
    intro_end:      Mapped[float] = mapped_column(Float,   nullable=False)  # saniye
    confidence:     Mapped[float] = mapped_column(Float,   nullable=False, default=1.0)
    created_at:     Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class OutroTimestamp(Base):
    """FAZ-4: FFmpeg blackdetect ile tespit edilen outro başlangıç/bitiş zamanları."""
    __tablename__ = "outro_timestamp"

    id:             Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id:     Mapped[int]   = mapped_column(Integer, nullable=False)
    episode_number: Mapped[int]   = mapped_column(Integer, nullable=False)
    outro_start:    Mapped[float] = mapped_column(Float,   nullable=False)  # saniye
    outro_end:      Mapped[float] = mapped_column(Float,   nullable=False)  # saniye
    confidence:     Mapped[float] = mapped_column(Float,   nullable=False, default=0.85)
    created_at:     Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class GameSession(Base):
    """FAZ-7b: Oyun oturumu — oynama süresi takibi."""
    __tablename__ = "game_session"

    id:               Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id:       Mapped[int]      = mapped_column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False)
    duration_minutes: Mapped[int]      = mapped_column(Integer, nullable=False, default=0)
    started_at:       Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
