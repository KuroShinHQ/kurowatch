"""Find Madara chapter images - search for hidden data"""
import re

with open("/mnt/c/Kuroshin/kurowatch/tmp_mangawow_ch1.html", "r", encoding="utf-8") as f:
    html = f.read()

# Madara typically stores images in data- attributes of divs
print("=== MADARA IMAGE SEARCH ===")

# Check for data-src (Madara lazy loading)
for attr in ['data-src', 'data-lazy-src', 'data-original', 'data-url', 'src="data:']:
    count = html.count(attr)
    print(f"  {attr}: {count}")

# Find all reading-related divs and their children
reading_areas = re.findall(r'<div[^>]*class="[^"]*reading-content[^"]*"[^>]*>.*?</div>\s*</div>', html, re.DOTALL)
print(f"\nReading content divs: {len(reading_areas)}")
for i, area in enumerate(reading_areas[:3]):
    # Find any images or URLs inside
    imgs = re.findall(r'<img[^>]*>', area)
    print(f"  Area {i}: {len(imgs)} img tags")
    for img in imgs[:5]:
        print(f"    {img[:200]}")

# Check for chapter-page or page-break classes
page_divs = re.findall(r'<div[^>]*class="[^"]*(?:page-break|page-content|chapter-page|text-left)[^"]*"[^>]*>', html)
print(f"\nPage divs: {len(page_divs)}")

# Check for the madara-specific chapter data
for var in ['manga_data', 'chapter_images', 'wp_manga', 'manga_ajax']:
    if var in html.lower():
        print(f"Found var: {var}")
        # Find context
        idx = html.lower().find(var)
        print(f"  Context: {html[idx:idx+300]}")

# Find wp-manga or manga-related hidden inputs
hidden = re.findall(r'<input[^>]*type="hidden"[^>]*>', html)
print(f"\nHidden inputs: {len(hidden)}")
for h in hidden:
    print(f"  {h[:200]}")

# Look for any JSON blobs 
json_objects = re.findall(r'\{[^{}]*"https?://[^"]*\.(?:jpg|png|webp)[^}]*\}', html)
print(f"\nJSON objects with image URLs: {len(json_objects)}")
for j in json_objects[:5]:
    print(f"  {j[:300]}")

# Check for admin-ajax.php calls
ajax_calls = re.findall(r'admin-ajax\.php[^"]*', html)
print(f"\nadmin-ajax.php calls: {len(ajax_calls)}")
for a in ajax_calls[:10]:
    print(f"  {a}")
