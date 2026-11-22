"""Общие элементы каждой страницы guide.100doc.ge (владелец 22.11.2026).

- тонкая жёлтая полоса сразу под шапкой: ru «С 1 января 2026 года страховка обязательна при въезде в Грузию» →
  https://100doc.ge/tourist/ ; en «Since 1 January 2026, insurance is mandatory to enter Georgia» → https://100doc.ge/tourist/en ;
- в шаблонах (сборщик, стиль, шапка, полоса, подвал, таблица главной) нет названий страховых компаний: логотип страховщика
  из шапки блога не копируем;
- телефон: meta viewport, каждая таблица внутри обёртки .tbl с горизонтальной прокруткой, картинки не шире экрана.
Запуск: python3 -m pytest -q tests/test_strip_and_brands.py
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
STRIP = {"ru": ("https://100doc.ge/tourist/", "С 1 января 2026 года страховка обязательна при въезде в Грузию"),
         "en": ("https://100doc.ge/tourist/en", "Since 1 January 2026, insurance is mandatory to enter Georgia")}
INSURERS = re.compile(r"(?i)\b(IRAO|Imedi|Aldagi|GPI|Ardi|Unison|Tao)\b")


def lang_of(h):
    return re.search(r'<html lang="(\w+)"', h).group(1)


class Strip(unittest.TestCase):
    def test_pages_found(self):
        self.assertGreater(len(PAGES), 80)

    def test_yellow_strip_everywhere(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            href, text = STRIP[lang_of(h)]
            # владелец 22.11.2026: полоса как в блоге (law-strip под шапкой и строкой hdr-tagline, иконка слева), вся полоса — ссылка
            if not re.search(r'</header>\n(<div class="hdr-tagline">[^\n]*</div>\n)?<a class="law-strip" href="'
                             + re.escape(href) + r'"><p>(<svg [^>]*aria-hidden="true">.*?</svg>)?' + re.escape(text) + r"</p></a>", h):
                bad.append(str(p.relative_to(ROOT)))
        self.assertEqual(bad, [], "\n".join(bad[:10]))


class NoInsurers(unittest.TestCase):
    def test_templates(self):
        for f in ("build/build.py", "build/style.css"):
            m = INSURERS.search((ROOT / f).read_text(encoding="utf-8"))
            self.assertIsNone(m, f"{f}: {m and m.group(0)}")

    def test_page_chrome(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            chrome = " ".join(re.findall(r'<header class="top">.*?</header>|<div class="hdr-tagline">.*?</div>|<a class="law-strip".*?</a>|<footer class="foot">.*?</footer>'
                                         r'|<section class="glance"[^>]*>.*?</section>', h, re.S))
            m = INSURERS.search(chrome)
            if m:
                bad.append(f"{p.relative_to(ROOT)}: {m.group(0)}")
        self.assertEqual(bad, [], "\n".join(bad[:10]))


class Mobile(unittest.TestCase):
    def test_viewport_and_tables_wrapped(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            if '<meta name="viewport" content="width=device-width, initial-scale=1">' not in h:
                bad.append(f"{p.relative_to(ROOT)}: viewport")
            if h.count("<table") != len(re.findall(r'<div class="tbl[^"]*"><table', h)):
                bad.append(f"{p.relative_to(ROOT)}: таблица без обёртки .tbl")
        self.assertEqual(bad, [], "\n".join(bad[:10]))
        css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.tbl\{[^}]*overflow-x:auto")
        self.assertRegex(css, r"(^|\n|\})img\{[^}]*max-width:100%")
        self.assertRegex(css, r"body\{[^}]*overflow-wrap:(break-word|anywhere)")


if __name__ == "__main__":
    unittest.main(verbosity=1)
