"""Чача на страницах кухни не спорит со статьёй о чаче (ru-chacha/DECISIONS.md, шаг 10, 22.11.2026).

Статья «Грузинская чача» (/ru/chacha/, /chacha-georgia/) берёт крепость только из Закона и спецификации; «до 85 % у домашней»
и «самогон из жмыха» в разделе кухни ей противоречили. Правило: в разделе #vino кухни — короткий абзац и ссылка на статью
о чаче той же языковой версии, без цифр крепости домашней и без «самогон».
Запуск: python3 -m pytest -q tests/test_chacha_crosslink.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://guide.100doc.ge/"


def section(md, sid):
    m = re.search(rf"^## [^\n]*\{{#{sid}\}}\n(.*?)(?=^## )", md, re.S | re.M)
    assert m, f"нет раздела #{sid}"
    return m.group(1)


def test_ru_kitchen_links_to_chacha():
    md = (ROOT / "content/ru/kuhnya-gruzii.md").read_text(encoding="utf-8")
    vino = section(md, "vino")
    assert BASE + "ru/chacha/" in vino, "в #vino /ru/kuhnya-gruzii/ нет ссылки на /ru/chacha/"
    assert not re.search(r"(?<![\d,])85\s?%", vino), "крепость домашней чачи — только в статье о чаче"
    assert not re.search(r"(?i)самогон", vino), "«самогон» противоречит Закону (виноградная водка)"


def test_en_food_links_to_chacha():
    md = (ROOT / "content/en/georgian-food.md").read_text(encoding="utf-8")
    assert BASE + "chacha-georgia/" in md, "в /georgian-food/ нет ссылки на /chacha-georgia/"


def test_chacha_pages_exist_in_site_json():
    sj = (ROOT / "build/site.json").read_text(encoding="utf-8")
    assert '"content/ru/chacha.md"' in sj and '"content/en/chacha-georgia.md"' in sj
