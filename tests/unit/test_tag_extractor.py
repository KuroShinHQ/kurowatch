"""backend.scraper.tag_extractor saf fonksiyon birim testleri (ag/html yok)."""
import pytest

from backend.scraper.tag_extractor import (
    normalize_tag,
    tag_color,
    title_case_tag,
    turkish_to_english,
)


class TestNormalizeTag:
    def test_plain_name_unchanged(self):
        # Normal durum.
        assert normalize_tag("Aksiyon") == "Aksiyon"

    def test_strips_category_prefix(self):
        # Normal durum: kategori oneki atilir.
        result = normalize_tag("Kategori: Aksiyon")
        assert "Kategori" not in result
        assert "Aksiyon" in result

    def test_empty_string_returns_empty(self):
        # Sinir durumu: bos girdi -> bos cikti (patlama yok).
        assert normalize_tag("") == ""

    def test_none_like_whitespace_returns_empty(self):
        # Sinir durumu: sadece bosluk -> bos.
        assert normalize_tag("   ") == ""

    def test_html_tags_stripped(self):
        # Hata durumu: HTML icine gomulmus etiket — temizlenmeli.
        result = normalize_tag("<b>Aksiyon</b>")
        assert "<" not in result and ">" not in result
        assert "Aksiyon" in result

    def test_long_input_truncated_to_60_chars(self):
        # Sinir durumu: 60 karakterden uzun etiket kisaltilir.
        result = normalize_tag("x" * 200)
        assert len(result) == 60

    def test_html_entities_decoded(self):
        # Normal durum: yaygin encode hatalari duzeltilir.
        assert normalize_tag("Shounen &amp; Seinen") == "Shounen & Seinen"


class TestTitleCaseTag:
    def test_first_letter_capitalized(self):
        assert title_case_tag("aksiyon filmi") == "Aksiyon Filmi"

    def test_small_words_kept_lowercase(self):
        # Turkce kucuk baglaclar buyutulmez (ilk kelime haric).
        result = title_case_tag("savas ve baris")
        assert result == "Savas ve Baris"

    def test_empty_returns_as_is(self):
        # Sinir durumu: bos string aynen doner.
        assert title_case_tag("") == ""


class TestTurkishToEnglish:
    def test_known_translation(self):
        # Normal durum: bilinen Turkce etiket cevrilir.
        result = turkish_to_english("Aksiyon")
        assert result is not None
        assert result.lower() in ("action",)

    def test_unknown_returns_none(self):
        # Hata durumu: bilinmeyen etiket None doner (patlama yok).
        assert turkish_to_english("zzz-bilinmeyen-etiket-xyz") is None

    def test_empty_returns_none(self):
        # Sinir durumu: bos girdi.
        assert turkish_to_english("") is None


class TestTagColor:
    def test_known_tag_has_theme_color(self):
        result = tag_color("action")
        assert result.startswith("#")

    def test_unknown_tag_gets_default_gray(self):
        # Sinir durumu: bilinmeyen etiket varsayilan gri alir.
        assert tag_color("zzz-unknown") == "#9090b0"
