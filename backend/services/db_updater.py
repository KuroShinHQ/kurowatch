"""
SOHBET-147 — DB Updater
Updates the database with new domain alternatives for dead sites.
"""
import json, logging, os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "db_updater.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("db_updater")


@dataclass
class UpdateResult:
    content_id: int
    content_title: str
    old_domain: str
    new_domain: str
    site_updated: bool = False
    episodes_updated: int = 0
    error: Optional[str] = None


async def add_new_site_entry(db_session, content_id: int, site_name: str,
                              site_url: str, is_primary: bool = False) -> bool:
    """Add a new site entry to the site table if it doesn't exist."""
    from sqlalchemy import text

    # Check if already exists
    result = await db_session.execute(text("""
        SELECT id FROM site WHERE content_id = :cid AND site_url = :url
    """), {"cid": content_id, "url": site_url})
    if result.fetchone():
        return False  # already exists

    await db_session.execute(text("""
        INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
        VALUES (:cid, :name, :url, :primary, 0)
    """), {"cid": content_id, "name": site_name, "url": site_url, "primary": 1 if is_primary else 0})
    logger.info(f"Added site {site_name}: {site_url} for content {content_id}")
    return True


async def update_episode_urls(db_session, content_id: int, old_domain: str,
                               new_domain: str) -> int:
    """Update all episode URLs replacing old domain with new domain."""
    from sqlalchemy import text

    result = await db_session.execute(text("""
        UPDATE episode
        SET url = REPLACE(url, :old_domain, :new_domain)
        WHERE content_id = :cid
        AND url LIKE :pattern
    """), {
        "old_domain": old_domain,
        "new_domain": new_domain,
        "cid": content_id,
        "pattern": f"%{old_domain}%",
    })
    count = result.rowcount
    if count > 0:
        logger.info(f"Updated {count} episode URLs for content {content_id}: {old_domain} -> {new_domain}")
    return count


async def update_site_url(db_session, site_id: int, new_url: str) -> bool:
    """Update a single site entry's URL."""
    from sqlalchemy import text
    await db_session.execute(text("UPDATE site SET site_url = :url WHERE id = :id"),
                             {"url": new_url, "id": site_id})
    logger.info(f"Updated site {site_id}: -> {new_url}")
    return True


async def mark_site_dead(db_session, site_id: int) -> bool:
    """Mark a site as dead."""
    from sqlalchemy import text
    await db_session.execute(text("UPDATE site SET is_dead = 1 WHERE id = :id"),
                             {"id": site_id})
    return True


async def mark_site_alive(db_session, site_id: int) -> bool:
    """Mark a site as alive."""
    from sqlalchemy import text
    await db_session.execute(text("UPDATE site SET is_dead = 0 WHERE id = :id"),
                             {"id": site_id})
    return True


async def replace_domain_globally(db_session, old_domain: str, new_domain: str) -> tuple[int, int]:
    """
    Replace a domain across all tables.
    Returns (site_count, episode_count).
    """
    from sqlalchemy import text

    # Update site URLs
    site_result = await db_session.execute(text("""
        UPDATE site SET site_url = REPLACE(site_url, :old_d, :new_d)
        WHERE site_url LIKE :pattern
    """), {"old_d": old_domain, "new_d": new_domain, "pattern": f"%{old_domain}%"})
    site_count = site_result.rowcount

    # Update episode URLs
    ep_result = await db_session.execute(text("""
        UPDATE episode SET url = REPLACE(url, :old_d, :new_d)
        WHERE url LIKE :pattern
    """), {"old_d": old_domain, "new_d": new_domain, "pattern": f"%{old_domain}%"})
    ep_count = ep_result.rowcount

    # Mark old site entries as dead
    await db_session.execute(text("""
        UPDATE site SET is_dead = 1
        WHERE site_url LIKE :pattern AND is_dead IS NULL
    """), {"pattern": f"%{old_domain}%"})

    await db_session.commit()
    logger.info(f"Global replacement: {old_domain} -> {new_domain}: {site_count} sites, {ep_count} episodes")
    return site_count, ep_count


async def apply_alternative_domain(
    db_session,
    dead_domain: str,
    new_domain: str,
    content_type: Optional[str] = None,
    progress_callback=None,
) -> list[UpdateResult]:
    """Apply a new alternative domain for all content using the dead domain."""
    from sqlalchemy import text
    from backend.services.url_patterns import apply_new_domain_to_url, extract_slug

    # Get all content affected
    result = await db_session.execute(text("""
        SELECT DISTINCT c.id, c.title, c.type, s.id as site_id, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE s.site_url LIKE :pattern
    """), {"pattern": f"%{dead_domain}%"})
    rows = result.fetchall()

    if not rows:
        logger.info(f"No content found for dead domain: {dead_domain}")
        return []

    # Group by content_id
    content_map = {}
    for row in rows:
        cid = row[0]
        if cid not in content_map:
            content_map[cid] = {"title": row[1], "type": row[2], "sites": []}
        content_map[cid]["sites"].append({"site_id": row[3], "site_url": row[4]})

    results = []
    for idx, (cid, info) in enumerate(content_map.items()):
        slug = extract_slug(info["sites"][0]["site_url"])
        new_url = apply_new_domain_to_url(
            info["sites"][0]["site_url"],
            new_domain,
            info["type"] or content_type or "",
            slug,
        )

        update_result = UpdateResult(
            content_id=cid,
            content_title=info["title"],
            old_domain=dead_domain,
            new_domain=new_domain,
        )

        try:
            # Update each site entry
            for site in info["sites"]:
                site_new_url = site["site_url"].replace(dead_domain, new_domain)
                await update_site_url(db_session, site["site_id"], site_new_url)
                update_result.site_updated = True

            # Update episode URLs
            ep_count = await update_episode_urls(db_session, cid, dead_domain, new_domain)
            update_result.episodes_updated = ep_count

            results.append(update_result)

        except Exception as e:
            update_result.error = str(e)[:100]
            results.append(update_result)
            logger.error(f"Error updating content {cid}: {e}")

        if progress_callback:
            await progress_callback(idx + 1, len(content_map), cid, info["title"])

    await db_session.commit()
    logger.info(f"Applied alternative domain {new_domain} for {len(results)} content items")
    return results


async def rollback_update(db_session, update_result: UpdateResult) -> bool:
    """Rollback a domain update for a single content."""
    from sqlalchemy import text

    try:
        # Revert site URLs
        await db_session.execute(text("""
            UPDATE site SET site_url = REPLACE(site_url, :new_d, :old_d)
            WHERE content_id = :cid AND site_url LIKE :pattern
        """), {
            "new_d": update_result.new_domain,
            "old_d": update_result.old_domain,
            "cid": update_result.content_id,
            "pattern": f"%{update_result.new_domain}%",
        })

        # Revert episode URLs
        await db_session.execute(text("""
            UPDATE episode SET url = REPLACE(url, :new_d, :old_d)
            WHERE content_id = :cid AND url LIKE :pattern
        """), {
            "new_d": update_result.new_domain,
            "old_d": update_result.old_domain,
            "cid": update_result.content_id,
            "pattern": f"%{update_result.new_domain}%",
        })

        await db_session.commit()
        logger.info(f"Rolled back content {update_result.content_id}: {update_result.new_domain} -> {update_result.old_domain}")
        return True
    except Exception as e:
        logger.error(f"Rollback failed for content {update_result.content_id}: {e}")
        return False


__all__ = [
    "UpdateResult", "add_new_site_entry", "update_episode_urls",
    "update_site_url", "mark_site_dead", "mark_site_alive",
    "replace_domain_globally", "apply_alternative_domain", "rollback_update",
]
