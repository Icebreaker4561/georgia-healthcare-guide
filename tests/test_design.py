"""Оформление как у блога 100doc.ge. Владелец 22.11.2026, вариант А («Да, под шаблон блога»): CSS страницы — CSS шаблона
блога ~/SEO_Vasiliy/standards/blog-template.html целиком + EXTRA_CSS сборщика блога, разметка блога (site-hdr, law-strip,
art-head, byline, ai-read, art-body, cf), без полос слева у наших блоков; проверки Inter, #f9fafb, .top, .card, .foot и
запрета Google Fonts сняты (шрифт — Manrope, как в блоге).

Было (до 22.11.2026, вечер): оформление как у блога 100doc.ge (владелец 22.11.2026: путеводитель переезжает на guide.100doc.ge и выглядит как
https://100doc.ge/ru/blog/ — белая шапка, светло-серый фон, синие ссылки, розовая кнопка, белые карточки с тонкой рамкой
и мягкой тенью, системный шрифт в духе Inter, серый подвал). Заменяет прежний тест «как thegeorgianguide.com».

Проверяет собранные страницы и build/style.css:
- шапка белая, логотип — картинка «100doc.ge / Guide» в стиле логотипов разделов 100doc.ge (/Tourist, /Review; владелец 22.11.2026:
  «должен быть такой же, как и в остальных разделах сайта»), alt «100doc.ge Guide», ведёт на главную путеводителя своего языка;
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
TEMPLATE = pathlib.Path.home() / "SEO_Vasiliy" / "standards" / "blog-template.html"
BLOG_BUILD = pathlib.Path.home() / "SEO_Vasiliy" / "tools" / "blog_article_build.py"


# Б1 (владелец 22.11.2026): из CSS шаблона блога вырезано всё, что относится к логотипу страховщика в шапке — ровно эти правила
CUT_FROM_TEMPLATE = (
    ".hdr-irao, .hdr-divider { display: none; }",
    ".hdr-irao { width: auto; height: 15px; flex-shrink: 0; }",
    ".hdr-divider { width: 1px; height: 20px; background: var(--border); flex-shrink: 0; }",
    "@media (min-width: 361px) { .hdr-irao, .hdr-divider { display: block; } }",
    " .hdr-irao { height: 17px; }",
)


def squeeze(css):
    """То же сжатие, что делает сборщик справочника: без комментариев и переводов строк."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s*\n\s*", "", css).strip()
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
        # владелец 22.11.2026, А2: общий CSS — в одном файле assets/guide.css (страница его подключает)
        cls.css = (ROOT / "assets" / "guide.css").read_text(encoding="utf-8")

    def test_white_header_with_guide_logo(self):
        bad = []
        for key, (p, h) in self.pages.items():
            m = re.search(r'<header class="top">.*?<a class="logo" href="([^"]+)"[^>]*>(.*?)</a>', h, re.S)
            if not m:
                bad.append(f"{key}: нет логотипа"); continue
            img = re.search(r'<img [^>]*src="([^"]*assets/img/logo-100doc-guide-1x\.webp)"[^>]*>', m.group(2))
            if not img or 'alt="100doc.ge Guide"' not in img.group(0) or "logo-100doc-guide.webp 2x" not in img.group(0):
                bad.append(f"{key}: логотип не картинка 100doc.ge / Guide: «{m.group(2)[:120]}»")
            elif not (ROOT / urllib.parse.urljoin("/" + rel(p), img.group(1)).lstrip("/")).exists():
                bad.append(f"{key}: файла логотипа нет: {img.group(1)}")
            home = BASE + ("ru/" if p["lang"] == "ru" else "")
            if urllib.parse.urljoin(BASE + rel(p), m.group(1)) != home:
                bad.append(f"{key}: логотип ведёт на {m.group(1)}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_guide_css_linked(self):
        """А2: каждая страница подключает один общий файл стилей assets/guide.css (путь — относительно страницы)."""
        bad = []
        for key, (p, h) in self.pages.items():
            hrefs = re.findall(r'<link rel="stylesheet" href="([^"]+)">', h)
            if BASE + "assets/guide.css" not in [urllib.parse.urljoin(BASE + rel(p), x) for x in hrefs]:
                bad.append(key)
            if "<style>" in h and len(re.search(r"<style>(.*?)</style>", h, re.S).group(1)) > 2000:
                bad.append(f"{key}: общий CSS снова встроен в страницу")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_no_fraunces(self):
        for key, (p, h) in self.pages.items():
            self.assertNotIn("Fraunces", h, key)

    def test_pink_button(self):
        self.assertRegex(self.css, r"\.btn-pink\{[^}]*background:var\(--pink\)")

    # ── владелец 22.11.2026, вариант А: «Да, под шаблон блога» — CSS и разметка как у статьи блога 100doc.ge ──
    def test_blog_css_whole(self):
        """CSS страницы содержит CSS шаблона блога целиком и EXTRA_CSS сборщика статей блога (в том же сжатии, что у сборщика)."""
        tpl = TEMPLATE.read_text(encoding="utf-8")
        tpl_css = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
        for cut in CUT_FROM_TEMPLATE:
            self.assertEqual(tpl_css.count(cut), 1, f"в шаблоне блога нет вырезаемого правила «{cut}»")
            tpl_css = tpl_css.replace(cut, "")
        self.assertNotIn("irao", self.css.lower(), "в CSS осталось правило логотипа страховщика")
        extra = re.search(r'EXTRA_CSS = """(.*?)"""', BLOG_BUILD.read_text(encoding="utf-8"), re.S).group(1)
        for name, part in (("шаблон блога", tpl_css), ("EXTRA_CSS", extra)):
            self.assertIn(squeeze(part), self.css, f"на странице нет CSS: {name}")
        for key, (p, h) in self.pages.items():
            self.assertIn("family=Manrope:wght@400;500;600;700;800", h, f"{key}: нет шрифта Manrope, как в блоге")

    def test_no_left_stripes(self):
        """У наших блоков и блоков «Прочитать с ИИ», «Коротко», оглавления — никаких полос слева (владелец: «вот эта рамка откуда?»)."""
        bad = []
        for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", self.css):
            if re.search(r"\.(box|facts|ai-read|toc|toc-m|stats|card|faq|qa|sources|glance|hub|law|chip|byline|lead|fig|tbl|note|call)\b|blockquote", sel) \
                    and "border-left" in body:
                bad.append(sel.strip())
        self.assertEqual(bad, [], f"border-left у {bad}")

    def test_blog_markup(self):
        bad = []
        need_all = ('<div class="site-hdr">', '<a class="law-strip"', '<header class="art-head">', '<div class="byline">',
                    'class="art-body"', '<div class="cf"')
        need_art = ('id="ai-read"', '<div class="art-main">', '<section class="page-rate"', '<section class="share"',
                    '<aside class="author-bio"', '<div class="related-grid">', '<div class="disclaimer">')
        for key, (p, h) in self.pages.items():
            for frag in need_all + (need_art if p["slug"] else ()):
                if frag not in h:
                    bad.append(f"{key}: нет {frag}")
        self.assertEqual(bad, [], "\n".join(bad[:30]))

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
        # как в блоге (владелец 22.11.2026): заголовок статьи — в сетке .layout, оглавление справа вровень с крошками и H1,
        # две колонки — с 1100 px (сетка и липкое оглавление — правила шаблона блога); на телефоне — свёрнутое details.toc-m
        self.assertRegex(self.art, re.compile(r'<div class="layout"><div class="hero">.*<aside class="side"><nav class="toc"', re.S))
        self.assertIn("@media (min-width: 1100px) {.layout { grid-template-columns:", self.css)
        self.assertNotRegex(self.css, r"@media \(min-width:1024px\)")
        self.assertRegex(self.css, r"@media \(min-width:1100px\)\{[^@]*\.toc-m\{display:none\}")
        self.assertRegex(self.css, r"@media \(min-width:1100px\)\{[^@]*\.side\{display:contents\}")
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
        for sel in (r"\.logo", r"\.lang", r"\.mbtn", r"\.chip", r"\.btn-pink", r"a\.law-strip p", r"\.byline-author"):
            self.assertRegex(self.css, sel + r"\{[^}]*min-height:44px", sel)
        self.assertRegex(self.css, r"img\{[^}]*max-width:100%")
        for key, (p, h) in self.pages.items():
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', h, key)


if __name__ == "__main__":
    unittest.main()
