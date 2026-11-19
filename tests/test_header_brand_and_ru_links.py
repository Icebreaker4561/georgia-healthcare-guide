"""Владелец 19.11.2026: «Ссылки из русских статей не должны вести на английские статьи, это точно» и
«название сайта поменяй, как мы договорились» (ru «Путеводитель по Грузии», en «Georgia Travel Guide»).

Проверяет все собранные страницы:
- в шапке (a.brand) — новое название на языке страницы; в шапке и подвале нет «Справочник» / «Health Guide»;
- в build/site.json нет старых названий;
- в тексте русских страниц (article.body, блок «Коротко», лид) нет ссылок на английские статьи путеводителя.
  Переключатель языка и hreflang в шапке — не текст статьи, их не трогаем.

Запуск: python3 tests/test_header_brand_and_ru_links.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
BRAND = {"ru": "Путеводитель по Грузии", "en": "Georgia Travel Guide"}
OLD = re.compile(r"(?i)справочник|health ?(care)? guide")
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]


def lang_of(h):
    m = re.search(r'<html lang="(\w+)"', h)
    return m.group(1) if m else "en"


class HeaderBrand(unittest.TestCase):
    def test_brand_in_header(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            m = re.search(r'<a class="brand"[^>]*>(?:<span[^>]*></span>)?(.*?)</a>', h, re.S)
            want = BRAND[lang_of(h)]
            if not m or m.group(1).strip() != want:
                bad.append(f"{p.parent.relative_to(ROOT)}: шапка «{m.group(1).strip() if m else '—'}», нужно «{want}»")
            for part in re.findall(r'<header class="top">.*?</header>|<footer class="foot">.*?</footer>', h, re.S):
                if OLD.search(re.sub(r"<[^>]+>", " ", part)):
                    bad.append(f"{p.parent.relative_to(ROOT)}: старое название в шапке или подвале")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_site_json_names(self):
        for k in ("name", "name_ru"):
            if k in SITE:
                self.assertNotRegex(SITE[k], OLD, k)
        self.assertEqual(SITE["name"], BRAND["en"])
        self.assertEqual(SITE.get("name_ru"), BRAND["ru"])


class RuLinksStayRu(unittest.TestCase):
    def test_no_links_from_ru_text_to_en_articles(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            if lang_of(h) != "ru":
                continue
            text = " ".join(re.findall(r'<div class="hero">.*?</div></div>|<div class="lead-box">.*?</div>|<article class="body">.*?</article>', h, re.S))
            for href in re.findall(r'<a [^>]*href="([^"]+)"', text):
                if href.startswith(BASE) and not href.startswith(BASE + "ru/"):
                    bad.append(f"{p.parent.relative_to(ROOT)}: {href}")
                elif not href.startswith(("http", "#", "mailto:", "tel:")) and "ru/" not in href and href.strip("./") not in ("",):
                    # относительная ссылка вне /ru/
                    if re.match(r"(\.\./)+[a-z]", href) and not re.search(r"(\.\./)+ru/", href):
                        bad.append(f"{p.parent.relative_to(ROOT)}: {href}")
        self.assertEqual(bad, [], f"{len(bad)} ссылок с русских страниц на английские статьи:\n" + "\n".join(bad[:30]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
