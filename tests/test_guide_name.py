"""Владелец 19.11.2026: переименовать справочник — «Гайд по путешествиям и медицине Грузии», самое сильное SEO-название.

Выбрано по Вордстату (19.11.2026): «путеводитель по грузии» 1 283, «грузия для туристов» 1 303,
«поездка в грузию» 11 111, «отдых в грузии» 5 182.
- Бренд: ru «Путеводитель по Грузии», en «Georgia Travel Guide» — первая крошка, подвал, schema.org publisher.
- Главная ru: H1 начинается с «Путеводитель по Грузии для туристов», в H1 есть «поездка», «отдых», «медицин».
- Старого названия «Справочник о медицине в Грузии» / «Georgia Healthcare Guide» нигде нет.

Запуск: python3 tests/test_guide_name.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
BRAND = {"ru": "Путеводитель по Грузии", "en": "Georgia Travel Guide"}


def lang_of(h):
    m = re.search(r'<html lang="(\w+)"', h)
    return m.group(1) if m else "en"


class GuideName(unittest.TestCase):
    def test_brand_everywhere(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            lang = lang_of(h)
            if "Справочник о медицине в Грузии" in h or "Georgia Healthcare Guide" in h:
                bad.append(f"{p.relative_to(ROOT)}: старое название")
            for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
                d = json.loads(m.group(1))
                if d.get("@type") == "Article" and d.get("publisher", {}).get("name") != "100doc.ge":  # издатель — 100doc.ge, как в блоге (владелец 22.11.2026)
                    bad.append(f"{p.relative_to(ROOT)}: publisher {d.get('publisher')}")
            foot = re.search(r'<footer.*?</footer>', h, re.S)
            if not foot or BRAND[lang] not in foot.group(0):
                bad.append(f"{p.relative_to(ROOT)}: нет названия в подвале")
        self.assertEqual(bad, [], "\n".join(bad[:10]))

    def test_first_crumb(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            c = re.search(r'<nav class="crumbs"[^>]*>(.*?)</nav>', h, re.S)
            if c and BRAND[lang_of(h)] not in c.group(1):
                bad.append(str(p.relative_to(ROOT)))
        self.assertEqual(bad, [], "\n".join(bad[:10]))

    def test_home_ru(self):
        h = (ROOT / "ru" / "index.html").read_text(encoding="utf-8")
        h1 = re.search(r"<h1>(.*?)</h1>", h).group(1)
        self.assertRegex(h1, r"^Путеводитель по Грузии для туристов")
        for w in ("поездк", "отдых", "медицин"):
            self.assertIn(w, h1.lower(), w)
        title = re.search(r"<title>(.*?)</title>", h).group(1)
        self.assertRegex(title, r"^Путеводитель по Грузии")

    def test_home_en(self):
        h = (ROOT / "index.html").read_text(encoding="utf-8")
        h1 = re.search(r"<h1>(.*?)</h1>", h).group(1)
        self.assertRegex(h1, r"^Georgia Travel Guide")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
