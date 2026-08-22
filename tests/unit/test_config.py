"""backend.config birim testleri — normal/hata/sinir durumlari."""
import json

import pytest

from backend import config as config_mod


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    """config.py _CONFIG_PATH'ini gecici dizine yonlendirir."""
    cfg_path = tmp_path / "config.json"
    monkeypatch.setattr(config_mod, "_CONFIG_PATH", str(cfg_path))
    return cfg_path


def test_get_config_missing_file_returns_empty_dict(config_dir):
    # Normal durum: dosya yok -> bos sozluk, patlama yok.
    assert config_mod.get_config() == {}


def test_get_config_reads_existing_file(config_dir):
    # Normal durum: gecerli JSON okunur.
    config_dir.write_text(json.dumps({"tmdb_api_key": "abc", "max_concurrent_downloads": 3}),
                          encoding="utf-8")
    cfg = config_mod.get_config()
    assert cfg["tmdb_api_key"] == "abc"
    assert cfg["max_concurrent_downloads"] == 3


def test_get_config_malformed_json_raises(config_dir):
    # Hata durumu: bozuk JSON — sessizce yutulmaz, cagiran gorur.
    config_dir.write_text("{ bozuk json !!!", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        config_mod.get_config()


def test_get_config_empty_object(config_dir):
    # Sinir durumu: gecerli ama bos JSON.
    config_dir.write_text("{}", encoding="utf-8")
    assert config_mod.get_config() == {}


def test_get_config_unicode_values_preserved(config_dir):
    # Sinir durumu: Turkce karakterler UTF-8 olarak korunmali.
    config_dir.write_text(json.dumps({"note": "Türkçe ĞÜŞİÖÇ"}, ensure_ascii=False),
                          encoding="utf-8")
    assert config_mod.get_config()["note"] == "Türkçe ĞÜŞİÖÇ"
