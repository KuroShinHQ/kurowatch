"""BAT_OLUSTURMA_REHBERI 12a/15.6 parite testi: L10N tr/en key setleri esit olmali."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kurowatch_menu as m


def test_l10n_key_parity():
    assert set(m.L10N["tr"]) == set(m.L10N["en"]), (
        "TR/EN key paritesi bozuk: "
        f"sadece-tr={set(m.L10N['tr']) - set(m.L10N['en'])}, "
        f"sadece-en={set(m.L10N['en']) - set(m.L10N['tr'])}"
    )


def test_default_lang_en():
    # 12a: default dil EN (LANG_FILE yokken)
    assert m._detect_lang() == "en" or m.LANG_FILE.exists()


def test_t_fallback():
    m._LANG = "en"
    assert m.T("kesinlikle_olmayan_key_9x") == "kesinlikle_olmayan_key_9x"


def test_toggle_lang_roundtrip():
    old = m._LANG
    new = m.toggle_lang()
    assert new != old and new in ("tr", "en")
    m._LANG = old


def test_quotes_parity():
    assert len(m.L10N["tr"]["quotes"]) == len(m.L10N["en"]["quotes"]) >= 1


def test_steps_parity():
    assert len(m.L10N["tr"]["steps"]) == len(m.L10N["en"]["steps"]) == 5


def test_actions_covered_by_l10n():
    for key in ("1", "2", "3", "4"):
        name, desc, _fn = m.ACTIONS[key]
        assert name in m.L10N["en"] and name in m.L10N["tr"]
        assert desc in m.L10N["en"] and desc in m.L10N["tr"]
