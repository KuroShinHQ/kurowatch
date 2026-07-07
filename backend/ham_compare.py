#!/usr/bin/env python3
"""
ham_compare.py v2 — Ham JSON Data vs KuroWatch DB content type comparison.
Safe matching: no startswith (too many false positives).
"""
import json, re, sqlite3, sys
from pathlib import Path

HAM_PATH = Path(r"C:\Kuroshin\kurowatch\docs\hamjsondata.md")
DB_PATH  = Path(r"C:\Kuroshin\kurowatch\memory\kurowatch.db")

TYPE_MAP = {"anime":"anime","series":"series","movie":"movie","cartoon":"cartoon",
            "tv-show":"series","manhwa":"manhwa","manga":"manga"}

def norm(t):
    return re.sub(r"\s+", " ", t.strip().lower())

def rm_paren(t):
    return re.sub(r"\([^)]*\)", "", t).strip()

def find_matching_bracket(text, start):
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "[": depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0: return i
    return len(text) - 1

def parse_ham(path):
    text = path.read_text(encoding="utf-8")
    items, text = [], text.strip()
    while text:
        text = text.lstrip()
        if not text or text[0] != "[": break
        end = find_matching_bracket(text, 0)
        try:
            arr = json.loads(text[:end+1])
            for obj in arr:
                if isinstance(obj, dict) and "title" in obj:
                    items.append({"title": obj["title"], "type": obj.get("type","")})
            text = text[end+1:].lstrip()
        except:
            break
    return items

def match_single(jt, dt):
    if norm(jt) == norm(dt):
        return True
    jp = rm_paren(jt)
    dp = rm_paren(dt)
    if jp and dp and norm(jp) == norm(dp):
        return True
    return False

def split_by_slash(title):
    """Split by ' / ' but not inside parentheses."""
    parts, cur, depth = [], "", 0
    for ch in title:
        if ch == "(": depth += 1
        elif ch == ")": depth -= 1
        elif ch == "/" and depth == 0:
            cur = cur.strip()
            if cur:
                parts.append(cur)
            cur = ""
            continue
        cur += ch
    cur = cur.strip()
    if cur: parts.append(cur)
    return parts

def main():
    apply = "--apply" in sys.argv
    items = parse_ham(HAM_PATH)
    print(f"Total JSON items parsed: {len(items)}")

    conn = sqlite3.connect(str(DB_PATH))
    db_rows = conn.execute("SELECT id, title, type FROM content ORDER BY id").fetchall()
    db_map = {r[0]: {"title": r[1], "type": r[2]} for r in db_rows}

    # Build index for matching: norm(title) -> [id, norm(title), norm(rm_paren(title))]
    db_index = []
    for r in db_rows:
        db_index.append({
            "id": r[0],
            "title": r[1],
            "type": r[2],
            "norm": norm(r[1]),
            "norm_np": norm(rm_paren(r[1])),
        })

    matched_ids = set()
    mismatches = []
    unmatched = []

    for item in items:
        jt = item["title"]
        jt_raw_type = item["type"]
        jt_type = TYPE_MAP.get(jt_raw_type.strip().lower())
        if not jt_type:
            print(f"  SKIP (unknown type '{jt_raw_type}'): \"{jt}\"")
            continue

        # Split multi titles (but respect parentheses)
        titles_check = [jt]
        if " / " in jt:
            titles_check = split_by_slash(jt)

        found_any = False
        for check_title in titles_check:
            ct_norm = norm(check_title)
            ct_norm_np = norm(rm_paren(check_title))
            ct_norm_full = norm(check_title)

            best = None
            for dbe in db_index:
                # Exact match first
                if ct_norm == dbe["norm"]:
                    best = dbe
                    break
                # Parens removed match
                if ct_norm_np and dbe["norm_np"] and ct_norm_np == dbe["norm_np"]:
                    best = dbe
                    break

            if best:
                found_any = True
                matched_ids.add(best["id"])
                if jt_type != best["type"]:
                    mismatches.append({
                        "id": best["id"],
                        "json_type": jt_type,
                        "db_type": best["type"],
                        "title": check_title,
                        "db_title": best["title"],
                    })

        if not found_any:
            unmatched.append(item)

    # Deduplicate mismatches by ID (keep last occurrence)
    seen_ids = set()
    deduped = []
    for m in reversed(mismatches):
        if m["id"] not in seen_ids:
            seen_ids.add(m["id"])
            deduped.append(m)
    deduped.reverse()
    mismatches = deduped

    print(f"Matched in DB: {len(matched_ids)}")
    print(f"Unmatched JSON items: {len(unmatched)}")
    print(f"Mismatches found: {len(mismatches)}")
    print()

    if mismatches:
        print("--- Mismatch Details ---\n")
        for m in mismatches:
            print(f"  ID={m['id']:>4} | {m['json_type']:>8} => {m['db_type']:<8} | \"{m['title']}\"")
            if m["title"] != m["db_title"]:
                print(f"         | DB:  \"{m['db_title']}\"")

    if unmatched:
        print(f"\n--- Unmatched ({len(unmatched)}) ---")
        for u in unmatched:
            print(f"  \"{u['title']}\" ({u['type']})")

    if apply and mismatches:
        print("\n--- Applying changes (--apply) ---")
        cur = conn.cursor()
        updated = 0
        for m in mismatches:
            cur.execute("UPDATE content SET type = ? WHERE id = ?", (m["json_type"], m["id"]))
            if cur.rowcount:
                updated += 1
                print(f"  ID={m['id']}: {m['db_type']} => {m['json_type']} | \"{m['db_title']}\"")
        conn.commit()
        print(f"\nTotal updated: {updated}")
    else:
        print("\nDry-run mode. Use --apply to write to DB.")

    conn.close()

if __name__ == "__main__":
    main()
