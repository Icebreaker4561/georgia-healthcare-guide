"""Владелец 20.11.2026: «да, ставь первой» — в разделе меню «Здоровье и безопасность» первой стоит статья
о скорой и 112 (en ambulance-georgia, ru 112-v-gruzii): на сайте о здоровье экстренная помощь — главное.
Порядок задаёт поле order в шапке исходника (меньше — выше), без него статья идёт после.

Проверяет на каждой собранной странице: первая ссылка в разделе health меню и первая карточка блока #health
на главной ведут на статью о скорой.

Запуск: python3 tests/test_menu_emergency_first.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
FIRST = {"en": "ambulance-georgia/", "ru": "112-v-gruzii/"}
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)


def lang_of(h):
    return re.search(r'<html lang="(\w+)"', h).group(1)


class EmergencyFirst(unittest.TestCase):
    def test_menu_health_starts_with_emergency(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            if '<nav class="menu"' not in h:
                continue
            m = re.search(r'data-sec="health">.*?<a href="([^"]+)"', h, re.S)
            if not m or not m.group(1).endswith(FIRST[lang_of(h)]):
                bad.append(f"{p.parent.relative_to(ROOT)}: первая в «Здоровье» — {m.group(1) if m else '—'}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_home_health_block_starts_with_emergency(self):
        for rel, lang in (("index.html", "en"), ("ru/index.html", "ru")):
            h = (ROOT / rel).read_text(encoding="utf-8")
            m = re.search(r'<section class="hub" id="health".*?<a class="card" href="([^"]+)"', h, re.S)
            self.assertTrue(m and m.group(1).endswith(FIRST[lang]), f"{rel}: первая карточка {m.group(1) if m else '—'}")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
