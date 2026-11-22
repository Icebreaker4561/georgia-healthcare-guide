"""Владелец 19.11.2026: «если ты ссылаешься на какие-то статьи, названия этих статей должны начинаться с большой буквы»
(снимок: «статья «как въехать в Грузию на машине: документы и Верхний Ларс» на 100doc.ge», «Статья входит в путеводитель по Грузии»).

Проверки в тексте статей:
- ссылка, взятая в кавычки «…» или “…” (это название статьи или страницы), начинается с большой буквы;
- ссылка на главную путеводителя называет его по имени: «Путеводитель по Грузии» / «Georgia Travel Guide» — с большой.

Запуск: python3 tests/test_titles_capitalized.py
"""
import html
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
BASE = "https://guide.100doc.ge/"


class Titles(unittest.TestCase):
    def test_quoted_link_titles_capitalized(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            text = " ".join(re.findall(r'<div class="lead-box">.*?</div>|<article class="body">.*?</article>', h, re.S))
            text = re.split(r'<h2 id="sources"', text)[0]
            for m in re.finditer(r'[«“"]\s*<a [^>]*>(.*?)</a>\s*[»”"]', text, re.S):
                t = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
                if t and t[0].isalpha() and t[0].islower():
                    bad.append(f"{p.parent.relative_to(ROOT)}: «{t[:80]}»")
        self.assertEqual(bad, [], f"{len(bad)} названий со строчной:\n" + "\n".join(bad[:40]))

    def test_guide_home_link_named(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            text = " ".join(re.findall(r'<div class="lead-box">.*?</div>|<article class="body">.*?</article>', h, re.S))
            for href, inner in re.findall(r'<a href="(' + re.escape(BASE) + r'(?:ru/)?)"[^>]*>(.*?)</a>', text, re.S):
                t = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
                if t[:1].islower():
                    bad.append(f"{p.parent.relative_to(ROOT)}: [{t}]({href})")
        self.assertEqual(bad, [], f"{len(bad)} ссылок на главную со строчной:\n" + "\n".join(bad[:40]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
