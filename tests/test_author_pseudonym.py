"""Владелец 22.11.2026: автор каждой статьи — Алекс Полански / Alex Polansky, как в блоге 100doc.ge. Заменяет прежний
тест псевдонима «Павел Шереметьев».

На каждой статье (en и ru, кроме главных):
- видимая строка автора div.byline: ссылка на страницу автора, которую использует блог (ru https://tourist.100doc.ge/about,
  en https://tourist.100doc.ge/en/about), фото assets/img/founder-320.webp (файл есть, alt и размеры), имя
  (ru «Алекс Полански», en «Alex Polansky») и должность дословно из разметки Person блога
  (ru «Основатель и руководитель 100doc.ge», en «Founder and CEO of 100doc.ge»);
- schema.org Article.author — Person с тем же @id, что в блоге (ru …/about#person, en …/en/about#person), имя, должность,
  фото и адрес — как в блоге.
Запуск: python3 tests/test_author_pseudonym.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
NAME = {"ru": "Алекс Полански", "en": "Alex Polansky"}
JOB = {"ru": "Основатель и руководитель 100doc.ge", "en": "Founder and CEO of 100doc.ge"}
ABOUT = {"ru": "https://tourist.100doc.ge/about", "en": "https://tourist.100doc.ge/en/about"}
PERSON = {
    "ru": {"@type": "Person", "@id": "https://tourist.100doc.ge/about#person", "name": "Alex Polansky",
           "alternateName": "Алекс Полански", "jobTitle": JOB["ru"], "image": "https://tourist.100doc.ge/img/founder-320.webp",
           "url": ABOUT["ru"]},
    "en": {"@type": "Person", "@id": "https://tourist.100doc.ge/en/about#person", "name": "Alex Polansky",
           "jobTitle": JOB["en"], "image": "https://tourist.100doc.ge/img/founder-320.webp", "url": ABOUT["en"]},
}


def lang_of(html):
    m = re.search(r'<html lang="(\w+)"', html)
    return m.group(1) if m else "en"


def article_ld(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        d = json.loads(m.group(1))
        if d.get("@type") == "Article":
            return d
    return None


class Author(unittest.TestCase):
    def test_photo_file(self):
        self.assertTrue((ROOT / "assets" / "img" / "founder-320.webp").exists())

    def test_articles_have_author(self):
        bad, checked = [], 0
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            ld = article_ld(h)
            if ld is None:
                continue
            checked += 1
            lang = lang_of(h)
            if ld.get("author") != PERSON[lang]:
                bad.append(f"{p.relative_to(ROOT)}: author {ld.get('author')}")
            m = re.search(r'<div class="byline"><a class="byline-author" href="([^"]+)"[^>]*>(.*?)</a>', h, re.S)
            if not m:
                bad.append(f"{p.relative_to(ROOT)}: нет строки автора"); continue
            href, inner = m.groups()
            if href != ABOUT[lang]:
                bad.append(f"{p.relative_to(ROOT)}: ссылка автора {href}")
            img = re.search(r'<img class="byline-photo" src="([^"]+)" width="\d+" height="\d+" alt="([^"]+)"', inner)
            if not img or not img.group(1).endswith("assets/img/founder-320.webp") or not (p.parent / img.group(1)).resolve().exists():
                bad.append(f"{p.relative_to(ROOT)}: фото автора {img.group(1) if img else '—'}")
            if f'<span class="byline-name">{NAME[lang]}</span>' not in inner:
                bad.append(f"{p.relative_to(ROOT)}: нет имени «{NAME[lang]}»")
            if f'<span class="byline-role">{JOB[lang]}</span>' not in inner:
                bad.append(f"{p.relative_to(ROOT)}: нет должности «{JOB[lang]}»")
        self.assertGreater(checked, 40, f"статей с Article {checked}")
        self.assertEqual(bad, [], "\n".join(bad[:10]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
