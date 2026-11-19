"""Сноски [N] не попадают в текст страницы (19.11.2026).

Номер сноски рисуется стилем (sup.fn a::before из data-n), а не текстом в HTML: так в выдаче Google и в подсчёте
объёма статьи нет мусорных «[3]», а читатель видит тот же «[3]». У ссылки есть aria-label для экранного диктора.

Запуск: python3 tests/test_footnote_markers.py
"""
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)


class Markers(unittest.TestCase):
    def test_marker_not_in_text(self):
        bad, n = [], 0
        for p in PAGES:
            for m in re.finditer(r'<sup class="fn"[^>]*>(<a [^>]*>)(.*?)</a></sup>', p.read_text(encoding="utf-8")):
                n += 1
                a, inner = m.group(1), m.group(2)
                if inner.strip() or not re.search(r'data-n="\d+"', a) or "aria-label=" not in a:
                    bad.append(f"{p.parent.relative_to(ROOT)}: {m.group(0)[:120]}")
        self.assertGreater(n, 500)
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_css_draws_number(self):
        css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r'sup\.fn a::before\{content:"\[" attr\(data-n\) "\]"')


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
