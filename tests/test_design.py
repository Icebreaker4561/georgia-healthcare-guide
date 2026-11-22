"""Оформление как у блога 100doc.ge (владелец 22.11.2026: путеводитель переезжает на guide.100doc.ge и выглядит как
https://100doc.ge/ru/blog/ — белая шапка, светло-серый фон, синие ссылки, розовая кнопка, белые карточки с тонкой рамкой
и мягкой тенью, системный шрифт в духе Inter, серый подвал). Заменяет прежний тест «как thegeorgianguide.com».

Проверяет собранные страницы и build/style.css:
- шапка белая, логотип — текст «100doc.ge/Guide» и ведёт на главную путеводителя своего языка;
- токены цвета блога: фон #f9fafb, ссылки #0f68ae, розовый #fe1d95, рамка #e0e0e8, белая поверхность;
- шрифт: стек Inter → системные, без Google Fonts и без Fraunces;
- карточки: белые, рамка 1px, скруглённые, с тенью; подвал серый, не тёмный;
- статья как статья блога: крошки, H1, лид, строка автора (фото + имя + должность), «Опубликовано … · Обновлено … ·
  N мин чтения», «Прочитать с ИИ», оглавление справа на компьютере и свёрнутое сверху на телефоне, «Ещё по теме», подвал;
- структура, на которую опираются тесты статей, на месте: div.hero, article.body, p.lead, details.qa, aside.box.facts,
  ol.sources, sup.fn;
- телефон: viewport, поля 16 px, цели нажатия 44 px, prefers-reduced-motion.
Запуск: python3 -m pytest -q tests/test_design.py
"""
import json
import pathlib
import re
import subprocess
import sys
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = "https://guide.100doc.ge/"
META = {"ru": r"Опубликовано <time datetime=\"\d{4}-\d\d-\d\d\">[^<]+</time> · Обновлено <time datetime=\"\d{4}-\d\d-\d\d\">[^<]+</time> · \d+ мин чтения",
        "en": r"Published <time datetime=\"\d{4}-\d\d-\d\d\">[^<]+</time> · Updated <time datetime=\"\d{4}-\d\d-\d\d\">[^<]+</time> · \d+ min read"}


def build():
    subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)


def rel(p):
    r = (p["slug"] if p["lang"] == "en" else ("ru/" + p["slug"] if p["slug"] else "ru"))
    return r + "/" if r else ""


class DesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.pages = {p["lang"] + ":" + p["slug"]: (p, (ROOT / rel(p) / "index.html").read_text(encoding="utf-8")) for p in SITE["pages"]}
        cls.art = (ROOT / "ru" / "kazbegi" / "index.html").read_text(encoding="utf-8")
        cls.css = re.search(r"<style>(.*?)</style>", cls.art, re.S).group(1)

    def test_white_header_with_guide_logo(self):
        self.assertRegex(self.css, r"\.top\{[^}]*background:#fff")
        bad = []
        for key, (p, h) in self.pages.items():
            m = re.search(r'<header class="top">.*?<a class="logo" href="([^"]+)"[^>]*>(.*?)</a>', h, re.S)
            if not m:
                bad.append(f"{key}: нет логотипа"); continue
            if re.sub(r"<[^>]+>", "", m.group(2)).strip() != "100doc.ge/Guide":
                bad.append(f"{key}: логотип «{m.group(2)}»")
            home = BASE + ("ru/" if p["lang"] == "ru" else "")
            if urllib.parse.urljoin(BASE + rel(p), m.group(1)) != home:
                bad.append(f"{key}: логотип ведёт на {m.group(1)}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_blog_palette_and_font(self):
        css = self.css.lower()
        for token, val in {"--paper": "#f9fafb", "--teal": "#0f68ae", "--pink": "#fe1d95", "--line": "#e0e0e8",
                           "--surface": "#fff", "--ink": "#101820"}.items():
            self.assertRegex(css, re.escape(token) + r":" + re.escape(val) + r"[;}]", token)
        self.assertRegex(self.css, r"body\{[^}]*background:var\(--paper\)")
        self.assertRegex(self.css, r"--sans:Inter,-apple-system,")
        self.assertRegex(self.css, r"a\{[^}]*color:var\(--teal\)")
        for key, (p, h) in self.pages.items():
            self.assertNotIn("fonts.googleapis.com", h, key)
            self.assertNotIn("Fraunces", h, key)

    def test_cards_and_gray_footer(self):
        self.assertRegex(self.css, r"\.card\{[^}]*background:var\(--surface\)")
        self.assertRegex(self.css, r"\.card\{[^}]*border:1px solid var\(--line\)")
        self.assertRegex(self.css, r"\.card\{[^}]*border-radius:12px")
        self.assertRegex(self.css, r"\.card\{[^}]*box-shadow:")
        self.assertRegex(self.css, r"\.foot\{[^}]*background:#f3f4f6")
        self.assertNotRegex(self.css, r"\.foot\{[^}]*background:var\(--ink\)")
        self.assertRegex(self.css, r"\.btn-pink\{[^}]*background:var\(--pink\)")

    def test_structure_kept(self):
        self.assertRegex(self.art, r'<div class="hero"><div class="wrap">.*?</div></div>')
        for frag in ('<article class="body">', '<p class="lead">', '<details class="qa">', '<aside class="box facts">',
                     '<ol class="sources">', '<sup class="fn">'):
            self.assertIn(frag, self.art, frag)

    def test_article_like_blog(self):
        bad = []
        for key, (p, h) in self.pages.items():
            if not p["slug"]:
                continue
            hero = re.search(r'<div class="hero"><div class="wrap">(.*?)</div></div>\n', h, re.S)
            hero = hero.group(1) if hero else ""
            order = [hero.find(x) for x in ('<nav class="crumbs"', "<h1>", '<p class="lead">', '<div class="byline">', '<p class="meta">')]
            if -1 in order or order != sorted(order):
                bad.append(f"{key}: в шапке статьи нет порядка крошки → H1 → лид → автор → дата {order}")
            m = re.search(r'<p class="meta">(.*?)</p>', h, re.S)
            if not m or not re.fullmatch(META[p["lang"]], m.group(1).strip()):
                bad.append(f"{key}: строка дат «{m.group(1) if m else '—'}»")
            if '<section class="related"' not in h:
                bad.append(f"{key}: нет «Ещё по теме»")
            if h.count('<nav class="toc"') == 1:
                if '<aside class="side"><nav class="toc"' not in h or h.count('<details class="toc-m">') != 1:
                    bad.append(f"{key}: оглавление не справа или нет свёрнутого для телефона")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_layout_side_toc(self):
        self.assertRegex(self.art, r'<div class="layout">.*<aside class="side"><nav class="toc"')
        self.assertRegex(self.css, r"@media \(min-width:1024px\)\{[^@]*\.layout\{[^}]*grid-template-columns")
        self.assertRegex(self.css, r"@media \(min-width:1024px\)\{[^@]*\.toc-m\{display:none\}")
        self.assertRegex(self.css, r"\.side \.toc\{[^}]*position:sticky")
        self.assertRegex(self.css, r"(^|\})\.side\{display:none\}")

    def test_figures_have_captions(self):
        figs = re.findall(r'<figure class="fig[^"]*">(.*?)</figure>', self.art, re.S)
        self.assertTrue(figs)
        self.assertTrue(all("<figcaption>" in f for f in figs))

    def test_stats_tiles(self):
        sys.path.insert(0, str(ROOT / "build"))
        import build as b
        html = b.render_block("> [!stats]\n> - Elevation: 1,750 m\n> - From Tbilisi: 157 km", None)
        self.assertEqual(html, '<dl class="stats"><div><dt>Elevation</dt><dd>1,750&nbsp;m</dd></div>'
                               '<div><dt>From Tbilisi</dt><dd>157&nbsp;km</dd></div></dl>')

    def test_mobile_basics(self):
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertRegex(self.css, r"\.wrap\{[^}]*padding:0 16px")
        for sel in (r"\.logo", r"\.lang", r"\.mbtn", r"\.chip", r"\.btn-pink", r"\.law a", r"\.byline-author"):
            self.assertRegex(self.css, sel + r"\{[^}]*min-height:44px", sel)
        self.assertRegex(self.css, r"img\{[^}]*max-width:100%")
        for key, (p, h) in self.pages.items():
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', h, key)


if __name__ == "__main__":
    unittest.main()
