"""Владелец 19.11.2026: «Напиши что автор Павел Шереметьев (будет такой творческий псевдоним)».

На каждой статье (en и ru, кроме главных): видимая подпись автора и schema.org Article.author —
Person с этим именем (ru: «Павел Шереметьев», en: «Pavel Sheremetyev»). Должностей и регалий у псевдонима нет.

Запуск: python3 tests/test_author_pseudonym.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
NAME = {"ru": "Павел Шереметьев", "en": "Pavel Sheremetyev"}


def lang_of(html):
    m = re.search(r'<html lang="(\w+)"', html)
    return m.group(1) if m else "en"


def article_ld(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        d = json.loads(m.group(1))
        if d.get("@type") == "Article":
            return d
    return None


class AuthorPseudonym(unittest.TestCase):
    def test_articles_have_author(self):
        bad, checked = [], 0
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            ld = article_ld(h)
            if ld is None:
                continue
            checked += 1
            name = NAME[lang_of(h)]
            a = ld.get("author") or {}
            if not (a.get("@type") == "Person" and a.get("name") == name):
                bad.append(f"{p.relative_to(ROOT)}: author {a}")
            if "jobTitle" in a or "honorificPrefix" in a:
                bad.append(f"{p.relative_to(ROOT)}: регалии у псевдонима")
            visible = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
            if name not in visible:
                bad.append(f"{p.relative_to(ROOT)}: нет видимой подписи «{name}»")
        self.assertGreater(checked, 40, f"статей с Article {checked}")
        self.assertEqual(bad, [], "\n".join(bad[:10]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
