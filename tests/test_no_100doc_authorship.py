"""Владелец 19.11.2026: «убери упоминание авторства 100doc.ge ото всюду».

Проверяет все собранные страницы (en и ru): нигде нет 100doc.ge в роли автора или издателя —
ни в видимом тексте (подвал «подготовлен командой 100doc.ge»), ни в разметке schema.org (author/publisher).
Обычные ссылки на каталог 100doc.ge в тексте статей — не авторство, их проверяет test_site.py.

Запуск: python3 tests/test_no_100doc_authorship.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)

AUTHOR_TEXT = re.compile(
    r"(?i)(team behind 100doc|100doc\.ge editorial|editorial team|prepared by[^<.]{0,40}100doc|by the 100doc"
    r"|командой 100doc|команд[аы] 100doc|редакци[яи] 100doc|подготовлен[^<.]{0,40}100doc|автор[^<.]{0,20}100doc)"
)


def ld_blocks(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        yield json.loads(m.group(1))


class NoAuthorship(unittest.TestCase):
    def test_pages_found(self):
        self.assertGreater(len(PAGES), 40, f"собранных страниц {len(PAGES)}")

    def test_no_authorship_text(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            h = re.sub(r'<script type="application/ld\+json">.*?</script>', " ", h, flags=re.S)
            m = AUTHOR_TEXT.search(h)
            if m:
                bad.append(f"{p.relative_to(ROOT)}: «{m.group(0)}»")
        self.assertEqual(bad, [], "\n".join(bad[:10]))

    def test_no_100doc_in_author_publisher(self):
        bad = []
        for p in PAGES:
            for block in ld_blocks(p.read_text(encoding="utf-8")):
                for key in ("author", "publisher", "creator", "copyrightHolder"):
                    if key in block and "100doc" in json.dumps(block[key], ensure_ascii=False).lower():
                        bad.append(f"{p.relative_to(ROOT)}: {key}")
        self.assertEqual(bad, [], "\n".join(bad[:10]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
