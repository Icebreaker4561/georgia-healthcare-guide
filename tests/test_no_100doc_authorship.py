"""Владелец 22.11.2026: путеводитель переезжает на guide.100doc.ge — теперь это проект 100doc.ge. Заменяет прежний тест
«убери авторство 100doc.ge» (решение 19.11.2026 отменено владельцем вместе с псевдонимом).

Проверяет:
- у каждой статьи schema.org Article.publisher — та же организация 100doc.ge, что в разметке блога 100doc.ge
  (@id https://tourist.100doc.ge/#organization, url, logo, sameAs);
- на главных CollectionPage.publisher — она же;
- псевдонима «Павел Шереметьев» / «Pavel Sheremetyev» нет нигде: в собранных страницах, исходниках, сборщике.
Запуск: python3 tests/test_no_100doc_authorship.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
ORG = {"@type": "Organization", "@id": "https://tourist.100doc.ge/#organization", "name": "100doc.ge",
       "url": "https://tourist.100doc.ge/",
       "logo": {"@type": "ImageObject", "url": "https://tourist.100doc.ge/logo.png", "width": 360, "height": 100},
       "sameAs": ["https://www.trustpilot.com/review/tourist.100doc.ge"]}
PSEUDO = re.compile(r"Шереметьев|Sheremetyev|Павел Ш|Pavel S")


def ld_blocks(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        yield json.loads(m.group(1))


class Publisher(unittest.TestCase):
    def test_pages_found(self):
        self.assertGreater(len(PAGES), 40, f"собранных страниц {len(PAGES)}")

    def test_publisher_is_100doc(self):
        bad, n = [], 0
        for p in PAGES:
            for block in ld_blocks(p.read_text(encoding="utf-8")):
                if block.get("@type") in ("Article", "CollectionPage"):
                    n += 1
                    if block.get("publisher") != ORG:
                        bad.append(f"{p.relative_to(ROOT)}: publisher {block.get('publisher')}")
        self.assertEqual(n, len(PAGES))
        self.assertEqual(bad, [], "\n".join(bad[:10]))

    def test_no_pseudonym_anywhere(self):
        files = PAGES + sorted((ROOT / "content").rglob("*.md")) + [ROOT / "build" / "build.py", ROOT / "build" / "site.json",
                                                                    ROOT / "llms.txt"]
        bad = [str(f.relative_to(ROOT)) for f in files if f.exists() and PSEUDO.search(f.read_text(encoding="utf-8"))]
        self.assertEqual(bad, [], "\n".join(bad[:10]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
