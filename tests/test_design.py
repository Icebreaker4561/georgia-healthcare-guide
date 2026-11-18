"""Оформление в стиле thegeorgianguide.com (владелец 18.11.2026: «Сделай вёрстку и оформление так же, как и на этом сайте»).
Проверяет собранные страницы: шрифты, палитру, раскладку с боковым оглавлением, блок «короткий ответ», плитки цифр,
тёмный подвал. Структура, на которую опираются тесты статей (div.hero, article.body, p.lead, details.qa), не меняется.
"""
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def build():
    subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)


class DesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.pages = {p: p.read_text(encoding="utf-8") for p in ROOT.glob("**/index.html") if "assets" not in p.parts}
        cls.art = (ROOT / "gudauri-altitude" / "index.html").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_fonts(self):
        for p, h in self.pages.items():
            self.assertRegex(h, r'<link[^>]+fonts\.googleapis\.com/css2\?[^"]*family=Fraunces', p)
            self.assertIn("Source+Sans+3", h, p)
            self.assertIn('rel="preconnect" href="https://fonts.gstatic.com"', h, p)

    def test_palette(self):
        css = re.search(r"<style>(.*?)</style>", self.art, re.S).group(1)
        for token, val in {"--paper": "#f8f5ef", "--ink": "#1b1a17", "--teal": "#14655f", "--line": "#ddd5c7",
                           "--paper-deep": "#efe9de", "--amber": "#d9a441"}.items():
            self.assertRegex(css.lower(), re.escape(token) + r":" + re.escape(val), token)
        self.assertRegex(css, r"body\{[^}]*background:var\(--paper\)")
        self.assertRegex(css, r"font-family:Fraunces")
        self.assertNotIn("linear-gradient", css, "герой без градиента — на бумажном фоне, как у образца")

    def test_structure_kept(self):
        self.assertRegex(self.art, r'<div class="hero"><div class="wrap">.*?</div></div>')
        self.assertIn('<article class="body">', self.art)
        self.assertIn('<p class="lead">', self.art)
        self.assertIn('<details class="qa">', self.art)

    def test_layout_side_toc(self):
        # на широком экране — колонка текста и закреплённое оглавление справа
        self.assertRegex(self.art, r'<div class="layout">.*<aside class="side">.*<nav class="toc"', )
        css = re.search(r"<style>(.*?)</style>", self.art, re.S).group(1)
        self.assertRegex(css, r"@media \(min-width:1024px\)\{[^@]*\.layout\{[^}]*grid-template-columns")
        self.assertRegex(css, r"\.side \.toc\{[^}]*position:sticky")

    def test_quick_answer_box(self):
        self.assertRegex(self.art, r'<aside class="box facts"><p class="box-h eyebrow">')
        css = re.search(r"<style>(.*?)</style>", self.art, re.S).group(1)
        self.assertRegex(css, r"\.box\.facts\{[^}]*border:1px solid var\(--ink\)")

    def test_stats_tiles(self):
        sys.path.insert(0, str(ROOT / "build"))
        import build as b
        html = b.render_block("> [!stats]\n> - Elevation: 1,750 m\n> - From Tbilisi: 157 km", None)
        self.assertEqual(html, '<dl class="stats"><div><dt>Elevation</dt><dd>1,750&nbsp;m</dd></div>'
                               '<div><dt>From Tbilisi</dt><dd>157&nbsp;km</dd></div></dl>')

    def test_dark_footer_and_header(self):
        css = re.search(r"<style>(.*?)</style>", self.art, re.S).group(1)
        self.assertRegex(css, r"\.foot\{[^}]*background:var\(--ink\)")
        self.assertRegex(css, r"\.top\{[^}]*position:sticky")

    def test_mobile_basics(self):
        css = re.search(r"<style>(.*?)</style>", self.art, re.S).group(1)
        self.assertIn("prefers-reduced-motion", css)
        self.assertRegex(css, r"\.wrap\{[^}]*padding:0 16px")


if __name__ == "__main__":
    unittest.main()
