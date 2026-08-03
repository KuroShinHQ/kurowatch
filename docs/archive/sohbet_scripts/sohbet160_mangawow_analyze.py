"""Find mangawow chapter images via WordPress data"""
import re

with open("/mnt/c/Kuroshin/kurowatch/tmp_mangawow_ch1.html", "r", encoding="utf-8") as f:
    html = f.read()

# Check for WP reader scripts
checks = {
    "madara": "madara" in html.lower(),
    "ajax": "admin-ajax" in html,
    "wp-json": "wp-json" in html,
    "wp-content": "wp-content" in html,
    "ts_reader": "ts_reader" in html or "tsreader" in html.lower(),
    "manga_reader": "manga_reader" in html.lower(),
    "chapter_data": "chapter_data" in html or "chapterData" in html,
    "images": "var images" in html or "var chapters" in html,
    "manga_pages": "manga_pages" in html or "mangaPages" in html,
    "json_data": "json_data" in html or "jsonData" in html,
}

print("Content checks:")
for k, v in checks.items():
    print(f"  {k}: {v}")

# Find all script tags with content
import json
scripts_with_data = re.findall(r'<script[^>]*>([^<]{100,5000})</script>', html)
print(f"\nLarge scripts (>100 chars): {len(scripts_with_data)}")
for i, s in enumerate(scripts_with_data[:5]):
    # Look for chapter data
    if 'var ' in s or 'let ' in s or 'const ' in s:
        # Check for image URLs
        imgs = re.findall(r'(?:https?://[^"\']*?(?:jpg|jpeg|png|webp)[^"\']*)', s)
        if imgs:
            print(f"  Script {i}: Found {len(imgs)} image URLs")
            for img in imgs[:5]:
                print(f"    {img}")
    
    # Check for JSON-like content
    if '{' in s:
        # Try to find image arrays
        img_arrays = re.findall(r'\[(?:["\'](?:https?://[^"\']*?(?:jpg|png))["\'][,\s]*){2,}\]', s)
        if img_arrays:
            print(f"  Script {i}: Found {len(img_arrays)} image arrays")

# Find all URLs that look like manga pages (not thumbnails)
all_urls = re.findall(r'(https?://[^"\']*?(?:jpg|jpeg|png|webp)[^"\']*)', html)
print(f"\nAll image URLs: {len(all_urls)}")
for u in all_urls:
    if '75x106' not in u and 'logo' not in u:
        print(f"  FULL: {u}")

# Check for shortcodes or embedded data
for pattern in ['[manga_', 'gallery', 'tp=', 'data-src']:
    matches = re.findall(rf'{pattern}[^<]*', html)
    if matches:
        print(f"\nPattern '{pattern}': {len(matches)}")
        for m in matches[:5]:
            print(f"  {m[:200]}")
