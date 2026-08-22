"""backend.services.url_patterns birim testleri — saf fonksiyonlar (ag yok)."""
import pytest

from backend.services.url_patterns import (
    CONTENT_TYPE_PATTERNS,
    UrlPattern,
    learn_pattern_from_urls,
)


class TestUrlPatternGenerate:
    def test_generate_with_episode_number(self):
        # Normal durum: {ep} yer tutucusu sayiyla degisir.
        p = UrlPattern("tranimaci.com", "anime", "/{slug}-{ep}-bolum-izle",
                       has_ep_number=True, slug_style="english")
        url = p.generate("tranimaci.com", "one-piece", ep_num=5)
        assert url == "https://www.tranimaci.com/one-piece-5-bolum-izle"

    def test_generate_with_season(self):
        # Normal durum: {season} + {ep} birlikte.
        p = UrlPattern("dizibox.so", "series", "/{slug}/sezon-{season}/bolum-{ep}/",
                       has_ep_number=True, has_season=True)
        url = p.generate("dizibox.so", "breaking-bad", ep_num=7, season=2)
        assert url == "https://www.dizibox.so/breaking-bad/sezon-2/bolum-7/"

    def test_generate_without_domain_www_prefix_adds_it(self):
        # Sinir durumu: www. ile baslamayan domain'e prefix eklenir.
        p = UrlPattern("example.com", "movie", "/{slug}/")
        url = p.generate("example.com", "test")
        assert url.startswith("https://www.example.com/")

    def test_generate_with_www_domain_not_duplicated(self):
        # Sinir durumu: zaten www. ile basliyorsa cift eklenmez.
        p = UrlPattern("www.example.com", "movie", "/{slug}/")
        url = p.generate("www.example.com", "test")
        assert url == "https://www.example.com/test/"

    def test_generate_ep_number_none_leaves_placeholder(self):
        # Hata durumu: ep_num=None ama sablon {ep} iceriyor — placeholder kalir,
        # bu davranis dokumele yazilmalidir (sessiz veri bozulmasi yerine).
        p = UrlPattern("x.com", "anime", "/{slug}-{ep}-bolum-izle", has_ep_number=True)
        url = p.generate("x.com", "slug")
        assert "{ep}" in url

    def test_generate_slug_with_unicode(self):
        # Sinir durumu: Turkce karakterli slug degistirilmeden kullanilir.
        p = UrlPattern("hdfilmcehennemi.now", "movie", "/film/{slug}/")
        url = p.generate("hdfilmcehennemi.now", "türkçe-film-adı")
        assert "film/türkçe-film-adı/" in url


class TestLearnPattern:
    def test_empty_url_list_returns_none(self):
        # Sinir durumu: bos liste -> None (patlama yok).
        assert learn_pattern_from_urls([]) is None

    def test_single_url_returns_pattern_with_path(self):
        # Normal durum: tek URL'den sabon cikarilir.
        pattern = learn_pattern_from_urls(["https://site.com/anime/one-piece/"])
        assert pattern is not None
        assert "/anime/one-piece/" in pattern.path_template


class TestRegistry:
    def test_all_content_types_have_patterns(self):
        # Sinir durumu: her icerik tipi icin en az 1 desen kayitli olmali.
        for ctype in ("anime", "manga", "manhwa", "movie", "series", "game"):
            assert len(CONTENT_TYPE_PATTERNS.get(ctype, [])) >= 1, f"{ctype} deseni eksik"

    def test_unknown_content_type_has_no_patterns(self):
        # Hata durumu: bilinmeyen tip icin kayit yok — KeyError yerine .get kullanimi.
        assert CONTENT_TYPE_PATTERNS.get("unknown-type") is None
