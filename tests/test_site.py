"""Приёмка микросайта georgia-healthcare-guide. Пишется ДО сборщика (правило владельца: тесты до кода).

Запуск: python3 -m pytest -q tests   (или python3 tests/test_site.py)

Контракты:
- каждая страница из site.json собрана в <slug>/index.html (en) или ru/<slug>/index.html (ru), главная — index.html;
- один H1; <title> до 60 знаков; description 110–165 знаков; canonical на свой адрес; <html lang> по языку;
- у пары en/ru — hreflang в обе стороны и x-default;
- ссылки на 100doc.ge: в статье 1–2 (владелец 17.11.2026: «не переспамлено»), на главной не больше 6;
  без nofollow/ugc/sponsored; адреса только https://100doc.ge/…; текст ссылки — не голый бренд;
- у каждого утверждения о законе — ссылка на первоисточник: в статье не меньше 2 внешних ссылок на
  официальные сайты (.gov.ge, matsne, gov.uk);
- картинки: файл существует, есть alt, width, height; у <picture> источник для телефона;
- FAQ: вопросы в <details>, разметка FAQPage совпадает с видимыми вопросами;
- внутренние ссылки ведут на собранные файлы; sitemap.xml перечисляет все страницы; robots.txt указывает sitemap;
- на странице нет слова «free» рядом с 112/ambulance (факт-противоречие, site-facts статьи 112);
- страница весит до 120 КБ HTML.
"""
import json
import pathlib
import re
import sys
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://icebreaker4561.github.io/georgia-healthcare-guide/"
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
OFFICIAL = re.compile(r"https?://([a-z0-9-]+\.)*(gov\.ge|matsne\.gov\.ge|gov\.uk|smartraveller\.gov\.au|who\.int)(/|$)")


def page_path(p):
    if p["slug"] == "":
        return ROOT / ("index.html" if p["lang"] == "en" else "ru/index.html")
    return ROOT / (p["slug"] if p["lang"] == "en" else "ru/" + p["slug"]) / "index.html"


def page_url(p):
    if p["slug"] == "":
        return BASE if p["lang"] == "en" else BASE + "ru/"
    return BASE + (p["slug"] if p["lang"] == "en" else "ru/" + p["slug"]) + "/"


class Doc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.text = []
        self.stack = []
        self.ld = []
        self._ld = None
        self.a = []
        self._a = None
        self.details_q = []
        self._in_summary = False
        self._sum = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "script" and a.get("type") == "application/ld+json":
            self._ld = []
        if tag == "a":
            self._a = [a, []]
        if tag == "summary":
            self._in_summary, self._sum = True, []

    def handle_endtag(self, tag):
        if tag == "script" and self._ld is not None:
            self.ld.append("".join(self._ld))
            self._ld = None
        if tag == "a" and self._a:
            self.a.append((self._a[0], "".join(self._a[1]).strip()))
            self._a = None
        if tag == "summary":
            self._in_summary = False
            self.details_q.append(" ".join("".join(self._sum).split()))

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
            return
        if self._a:
            self._a[1].append(data)
        if self._in_summary:
            self._sum.append(data)
        self.text.append(data)


def parse(path):
    d = Doc()
    d.feed(path.read_text(encoding="utf-8"))
    return d


class SiteTest(unittest.TestCase):
    def test_pages_built(self):
        for p in SITE["pages"]:
            self.assertTrue(page_path(p).exists(), f"не собрана {page_path(p)}")

    def test_head(self):
        for p in SITE["pages"]:
            f = page_path(p)
            h = f.read_text(encoding="utf-8")
            d = parse(f)
            h1 = [t for t, _ in d.tags if t == "h1"]
            self.assertEqual(len(h1), 1, f"{f}: H1 {len(h1)}")
            title = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
            self.assertLessEqual(len(title), 60, f"{f}: title {len(title)} знаков")
            desc = [a.get("content", "") for t, a in d.tags if t == "meta" and a.get("name") == "description"]
            self.assertTrue(desc and 110 <= len(desc[0]) <= 165, f"{f}: description {len(desc[0]) if desc else 0}")
            canon = [a["href"] for t, a in d.tags if t == "link" and a.get("rel") == "canonical"]
            self.assertEqual(canon, [page_url(p)], f"{f}: canonical")
            html_lang = [a.get("lang") for t, a in d.tags if t == "html"]
            self.assertEqual(html_lang, [p["lang"]])
            self.assertLessEqual(len(h.encode()), 120 * 1024, f"{f}: тяжелее 120 КБ")

    def test_hreflang_pairs(self):
        by_key = {}
        for p in SITE["pages"]:
            by_key.setdefault(p.get("pair") or p["slug"] + p["lang"], []).append(p)
        for key, group in by_key.items():
            if len(group) < 2:
                continue
            for p in group:
                d = parse(page_path(p))
                alts = {a.get("hreflang"): a.get("href") for t, a in d.tags if t == "link" and a.get("rel") == "alternate"}
                for q in group:
                    self.assertEqual(alts.get(q["lang"]), page_url(q), f"{page_path(p)}: hreflang {q['lang']}")
                self.assertIn("x-default", alts)

    def test_links_to_100doc(self):
        for p in SITE["pages"]:
            d = parse(page_path(p))
            ours = [(a, t) for a, t in d.a if "100doc.ge" in (a.get("href") or "")]
            limit = (1, 6) if p["slug"] == "" else (1, 2)
            self.assertTrue(limit[0] <= len(ours) <= limit[1], f"{page_path(p)}: ссылок на 100doc.ge {len(ours)}, нужно {limit}")
            for a, t in ours:
                self.assertTrue(a["href"].startswith("https://100doc.ge/"), a["href"])
                rel = a.get("rel") or ""
                self.assertNotRegex(rel, r"nofollow|ugc|sponsored", f"{page_path(p)}: rel={rel}")
                self.assertNotRegex(t.strip().lower(), r"^(100doc(\.ge)?|here|click here|this site)$", f"голый анкор «{t}»")

    def test_official_sources(self):
        for p in SITE["pages"]:
            if p["slug"] == "":
                continue
            d = parse(page_path(p))
            off = {a.get("href") for a, _ in d.a if OFFICIAL.match(a.get("href") or "")}
            self.assertGreaterEqual(len(off), 2, f"{page_path(p)}: официальных источников {len(off)}")

    def test_images(self):
        for p in SITE["pages"]:
            f = page_path(p)
            d = parse(f)
            for t, a in d.tags:
                if t == "img":
                    self.assertTrue(a.get("alt"), f"{f}: img без alt {a.get('src')}")
                    self.assertTrue(a.get("width") and a.get("height"), f"{f}: img без размеров {a.get('src')}")
                    src = (f.parent / a["src"]).resolve()
                    self.assertTrue(src.exists(), f"{f}: нет файла {a['src']}")
                if t == "source" and a.get("srcset"):
                    for part in a["srcset"].split(","):
                        rel = part.strip().split(" ")[0]
                        self.assertTrue((f.parent / rel).resolve().exists(), f"{f}: нет файла {rel}")

    def test_faq_markup(self):
        for p in SITE["pages"]:
            d = parse(page_path(p))
            faq = [json.loads(x) for x in d.ld if '"FAQPage"' in x]
            if not d.details_q:
                self.assertFalse(faq, f"{page_path(p)}: FAQPage без видимых вопросов")
                continue
            self.assertEqual(len(faq), 1, f"{page_path(p)}: FAQPage {len(faq)}")
            qs = [q["name"] for q in faq[0]["mainEntity"]]
            self.assertEqual(qs, d.details_q, f"{page_path(p)}: разметка FAQ ≠ видимые вопросы")

    def test_internal_links(self):
        for p in SITE["pages"]:
            f = page_path(p)
            for a, _ in parse(f).a:
                href = a.get("href") or ""
                if href.startswith(BASE):
                    rel = href[len(BASE):].split("#")[0]
                    target = ROOT / rel / "index.html" if rel and not rel.endswith(".html") else ROOT / (rel or "index.html")
                    if rel.endswith("/") or rel == "":
                        target = ROOT / rel / "index.html"
                    self.assertTrue(target.exists(), f"{f}: битая внутренняя ссылка {href}")

    def test_sitemap_robots(self):
        sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for p in SITE["pages"]:
            self.assertIn(f"<loc>{page_url(p)}</loc>", sm)
        self.assertIn(f"Sitemap: {BASE}sitemap.xml", (ROOT / "robots.txt").read_text(encoding="utf-8"))

    def test_no_free_ambulance(self):
        for p in SITE["pages"]:
            t = " ".join(parse(page_path(p)).text)
            for m in re.finditer(r"(?i)\bfree\b|бесплатн", t):
                ctx = t[max(0, m.start() - 80): m.end() + 80]
                self.assertNotRegex(ctx, r"(?i)112|ambulance|скор", f"{page_path(p)}: «free» рядом со скорой: …{ctx}…")


if __name__ == "__main__":
    unittest.main(verbosity=1)
