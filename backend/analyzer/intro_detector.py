"""
Chromaprint fingerprint karşılaştırma ile otomatik intro tespiti.
Algoritma: sliding window hamming distance, en uzun eşleşen segment = intro.
"""
from typing import Optional

_HAMMING_THRESHOLD = 6    # 32 bit içinde max farklı bit sayısı
_MIN_MATCH_FRAMES = 80    # minimum intro uzunluğu (≈10 saniye @ 8fps)
_MAX_OFFSET_FRAMES = 480  # offset tarama aralığı (≈60 saniye)
_MIN_SCORE = 0.45         # eşleşen frame oranı eşiği


def _popcount(n: int) -> int:
    """32-bit integer'daki 1 bitleri say."""
    n &= 0xFFFFFFFF
    n = n - ((n >> 1) & 0x55555555)
    n = (n & 0x33333333) + ((n >> 2) & 0x33333333)
    n = (n + (n >> 4)) & 0x0F0F0F0F
    return ((n * 0x01010101) & 0xFFFFFFFF) >> 24


def _match(a: int, b: int) -> bool:
    return _popcount(a ^ b) <= _HAMMING_THRESHOLD


def _longest_run(fp1: list, fp2: list, offset: int) -> tuple[int, int, int]:
    """
    Verilen offset'te fp1[i1..] ile fp2[i2..] arasında
    en uzun ardışık eşleşme bloğunu bul.
    Returns: (i1_start, i2_start, run_length)
    """
    i1 = max(0, offset)
    i2 = max(0, -offset)
    limit = min(len(fp1) - i1, len(fp2) - i2)

    best_start1 = i1
    best_start2 = i2
    best_len = 0
    cur_start1 = i1
    cur_start2 = i2
    cur_len = 0

    for k in range(limit):
        if _match(fp1[i1 + k], fp2[i2 + k]):
            if cur_len == 0:
                cur_start1 = i1 + k
                cur_start2 = i2 + k
            cur_len += 1
        else:
            if cur_len > best_len:
                best_len = cur_len
                best_start1 = cur_start1
                best_start2 = cur_start2
            cur_len = 0

    if cur_len > best_len:
        best_len = cur_len
        best_start1 = cur_start1
        best_start2 = cur_start2

    return best_start1, best_start2, best_len


def compare_fingerprints(
    fp1: list[int], fps1: float,
    fp2: list[int], fps2: float,
) -> Optional[dict]:
    """
    İki bölümün fingerprint'ini karşılaştır.
    Returns:
        {ep1_start, ep1_end, ep2_start, ep2_end, confidence}  (saniye cinsinden)
        veya None (intro bulunamazsa)
    """
    if not fp1 or not fp2:
        return None

    fps = (fps1 + fps2) / 2  # yaklaşık aynı (chromaprint sabit)

    best_len = 0
    best_result = None

    for offset in range(-_MAX_OFFSET_FRAMES, _MAX_OFFSET_FRAMES + 1):
        s1, s2, run = _longest_run(fp1, fp2, offset)
        if run < _MIN_MATCH_FRAMES:
            continue

        # overlap oranı
        overlap = min(len(fp1) - s1, len(fp2) - s2, run)
        score_frames = sum(
            1 for k in range(overlap) if _match(fp1[s1 + k], fp2[s2 + k])
        )
        score = score_frames / overlap if overlap > 0 else 0

        if run > best_len and score >= _MIN_SCORE:
            best_len = run
            best_result = {
                "ep1_start": s1 / fps,
                "ep1_end":   (s1 + run) / fps,
                "ep2_start": s2 / fps,
                "ep2_end":   (s2 + run) / fps,
                "confidence": round(score, 3),
            }

    return best_result


def consensus_intro(results: list[dict], episode_number: int) -> Optional[dict]:
    """
    Birden fazla karşılaştırma sonucundan bu bölüme ait intro zamanını çıkar.
    results: compare_fingerprints çıktıları (hangi bölüm ep1/ep2 olduğu ile birlikte)
    Returns: {start, end, confidence}
    """
    starts, ends, confs = [], [], []
    for r in results:
        key = "ep1" if r.get("ep1_number") == episode_number else "ep2"
        starts.append(r[f"{key}_start"])
        ends.append(r[f"{key}_end"])
        confs.append(r["confidence"])

    if not starts:
        return None

    avg_start = sum(starts) / len(starts)
    avg_end = sum(ends) / len(ends)
    avg_conf = sum(confs) / len(confs)

    if (avg_end - avg_start) < 10:  # 10 saniyeden kısa intro kabul edilmez
        return None

    return {
        "start": round(avg_start, 1),
        "end":   round(avg_end, 1),
        "confidence": round(avg_conf, 3),
    }
