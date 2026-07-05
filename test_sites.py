"""Test site availability for manga download sites"""
import httpx

sites_to_test = {
    "ragnarscans.com": "https://ragnarscans.com",
    "ragnarscans.net": "https://ragnarscans.net",
    "mangasehri.net": "https://mangasehri.net",
    "mangagezgini.com": "https://mangagezgini.com",
    "manhwahentai.me": "https://manhwahentai.me",
    "mangawow.com": "https://mangawow.com",
}

for name, url in sites_to_test.items():
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        status = r.status_code
        content_len = len(r.text)
        # Check for CF challenge
        is_cf = "cf-browser-verification" in r.text or "challenge-platform" in r.text or "cloudflare" in r.text.lower()
        print(f"{name}: HTTP {status} | {content_len} bytes | CF={'YES' if is_cf else 'no'}")
        if status == 200:
            # Check for Madara theme
            is_madara = "wp-manga" in r.text or "manga-chapter-img" in r.text or "reading-content" in r.text
            print(f"  Madara theme: {'YES' if is_madara else 'no'}")
            # First few lines
            lines = r.text[:300].strip()[:150]
            print(f"  Head: {lines}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
