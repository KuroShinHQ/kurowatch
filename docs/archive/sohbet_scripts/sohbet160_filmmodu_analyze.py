"""Analyze filmmodu page HTML"""
import re

with open("/mnt/c/Kuroshin/kurowatch/tmp_filmmodu.html", "r", encoding="utf-8") as f:
    html = f.read()

print(f"Total length: {len(html)}")

# Find all links
links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]{1,100})</a>', html)
print(f"Links: {len(links)}")
for href, text in links[:30]:
    print(f"  {text.strip()[:50]:50s} -> {href[:80]}")

# Check for keywords
for keyword in ["404", "not found", "bulunamadı", "error", "hata", "üzgünüz"]:
    count = html.lower().count(keyword)
    if count > 0:
        print(f"Keyword '{keyword}': {count} occurrences")

# Look for page title
titles = re.findall(r'<title[^>]*>([^<]+)</title>', html)
print(f"\nPage title: {titles}")

# Check meta description
desc = re.findall(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
print(f"Meta desc: {desc}")

# Check for film name in page
for name in ["Esaretin Bedeli", "esaretin", "bedeli", "Shawshank"]:
    count = html.count(name)
    if count > 0:
        print(f"Name '{name}': {count} occurrences")

# Look for JSON data in script tags
scripts = re.findall(r'<script[^>]*>([^<]{50,5000})</script>', html)
print(f"\nInline scripts (50-5000 chars): {len(scripts)}")
for s in scripts[:3]:
    if len(s) > 100:
        print(f"  Script ({len(s)} chars): {s[:300]}...")
