"""Владелец 22.11.2026 (снимок шапки с обведённой строкой «Insurance that actually works in Georgia»):
«это убери из всех страниц гайда». Под шапкой нет строки hdr-tagline шаблона блога — ни на одной странице, ни на одном
языке; жёлтая полоса law-strip остаётся.

Запуск: python3 tests/test_no_tagline.py
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts and "assets" not in p.parts)


class NoTagline(unittest.TestCase):
    def test_no_tagline_anywhere(self):
        self.assertTrue(PAGES)
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            body = re.sub(r"<style.*?</style>", "", h, flags=re.S)
            if 'class="hdr-tagline"' in body or re.search(r"(?i)insurance that actually works|страховка, которая действительно работает", body):
                bad.append(str(p.parent.relative_to(ROOT)))
            if 'class="law-strip"' not in body:
                bad.append(f"{p.parent.relative_to(ROOT)}: пропала жёлтая полоса")
        self.assertEqual(bad, [], "\n".join(bad[:20]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
