"""
Otonom Etiket Düzeltme ve Eşleştirme Motoru.

İçeriğin kendi özgün sitelerinden çıkarılan yerel etiketleri mevcut
content_tags tablosuyla çapraz kontrol eder. Küresel metadata
(TMDB/AniList) ile site etiketleri arasında uyuşmazlık varsa site
etiketini referans alarak:
  - eksik türleri content.genres JSON listesine ekler,
  - eksik etiketleri Tag + ContentTag olarak ilişkilendirir,
  - mevcut yanlış eşleşmeleri raporlar (manuel onay gerektirmeden
güncelleme yapılan 0-bakım mekanizması).
"""
import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import AsyncSessionLocal
from backend.models import Content, ContentTag, Tag
from backend.scraper.tag_extractor import (
    normalize_tag,
    tag_color,
    title_case_tag,
    turkish_to_english,
)

logger = logging.getLogger(__name__)


async def ensure_tag(session, name: str, tag_type: str = "user", color: Optional[str] = None) -> Tag:
    """İsim+tip ile Tag oluştur veya getir (idempotent)."""
    normalized = normalize_tag(name)
    if not normalized:
        raise ValueError("Boş etiket adı")
    result = await session.execute(select(Tag).where(Tag.name == normalized))
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = Tag(
            name=normalized,
            tag_type=tag_type,
            color=color or tag_color(normalized),
        )
        session.add(tag)
        await session.flush()
    return tag


async def attach_tag(session, content_id: int, tag: Tag):
    """Bir etiketi içeriğe ata; zaten varsa tekrar ekleme."""
    result = await session.execute(
        select(ContentTag).where(
            ContentTag.content_id == content_id,
            ContentTag.tag_id == tag.id,
        )
    )
    if result.scalar_one_or_none() is None:
        session.add(ContentTag(content_id=content_id, tag_id=tag.id))


async def sync_genres_to_tags(content_id: int) -> dict:
    """
    content.genres JSON listesindeki her tür için user tag oluştur/ata.
    En sık kullanılan senaryo: AniList/TMDB genres'leri otomatik görsel etiket yap.
    """
    async with AsyncSessionLocal() as db:
        content = await db.get(Content, content_id)
        if content is None:
            logger.warning("sync_genres_to_tags: content %s bulunamadi", content_id)
            return {"ok": False, "error": "content not found"}

        genres = []
        try:
            if content.genres:
                genres = json.loads(content.genres)
        except Exception:  # noqa: BLE001
            logger.warning("sync_genres_to_tags: gecersiz genres JSON for %s", content_id)
            genres = []

        if not isinstance(genres, list):
            logger.warning("sync_genres_to_tags: genres list degil (content=%s)", content_id)
            genres = []

        tags_created = 0
        for g in genres:
            if not isinstance(g, str):
                continue
            tag = await ensure_tag(db, g)
            await attach_tag(db, content_id, tag)
            tags_created += 1

        await db.commit()
        return {"ok": True, "tags_created": tags_created, "genres": genres}


async def sync_site_tags(content_id: int, site_name: str, site_tags: list[str]) -> dict:
    """
    Kaynak site etiketlerini küresel metadata ile çapraz kontrol eder.
    Site etiketi küresel bir türe karşılık geliyorsa content.genres'e
    İngilizce karşılığını katar; her durumda Tag + ContentTag ilişkilendirir.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Content).where(Content.id == content_id).options(
                selectinload(Content.tags)
            )
        )
        content = result.scalar_one_or_none()
        if content is None:
            logger.warning("sync_site_tags: content %s bulunamadi", content_id)
            return {"ok": False, "error": "content not found"}

        genres = []
        try:
            if content.genres:
                genres = json.loads(content.genres)
        except Exception:  # noqa: BLE001
            logger.warning("sync_site_tags: gecersiz genres JSON for %s", content_id)
            genres = []

        if not isinstance(genres, list):
            genres = []

        added_genres = 0
        site_tags_attached = 0
        english_tags_attached = 0

        # 1) Site etiketlerini işle
        for raw in site_tags:
            site_tag = normalize_tag(raw)
            if not site_tag:
                continue

            english = turkish_to_english(site_tag) or title_case_tag(site_tag)

            # Küresel metadata'da yoksa site etiketinin İngilizce karşılığını genres'e ekle
            if english and english not in genres:
                genres.append(english)
                added_genres += 1

            # Yerel site etiketini Tag + ContentTag olarak ilişkilendir
            tag = await ensure_tag(db, site_tag, color=tag_color(site_tag))
            await attach_tag(db, content_id, tag)
            site_tags_attached += 1

            if english and english.lower() != site_tag.lower():
                eng_tag = await ensure_tag(db, english, color=tag_color(english))
                await attach_tag(db, content_id, eng_tag)
                english_tags_attached += 1

        # 2) Mevcut genres listesindeki her türü de ContentTag olarak bağla
        for g in genres:
            if not isinstance(g, str):
                continue
            tag = await ensure_tag(db, g, color=tag_color(g))
            await attach_tag(db, content_id, tag)

        # 3) İçerik tipiyle çelişen tag'leri otomatik düzelt
        type_tag_name = content.type
        if type_tag_name:
            type_tag = await ensure_tag(db, type_tag_name, tag_type="api", color=tag_color(type_tag_name))
            await attach_tag(db, content_id, type_tag)

        # genres'i güncelle
        content.genres = json.dumps(genres, ensure_ascii=False)
        await db.commit()

        logger.info(
            "sync_site_tags: content=%s site=%s added_genres=%s site_tags=%s",
            content_id, site_name, added_genres, site_tags_attached,
        )
        return {
            "ok": True,
            "added_genres": added_genres,
            "site_tags_attached": site_tags_attached,
            "english_tags_attached": english_tags_attached,
            "final_genres": genres,
        }


__all__ = ["ensure_tag", "attach_tag", "sync_genres_to_tags", "sync_site_tags"]
