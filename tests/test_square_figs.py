"""Квадратные иллюстрации показываются в оригинале (владелец 18.11.2026: «на широких версиях не надо дорисовывать сбоку мутные
поля картинки. Давай просто менять верстку, чтобы квадратная картинка туда помещалась в оригинале»).

Если файл картинки квадратный (±3 %), сборщик даёт figure класс «sq», а стиль ограничивает ширину и центрирует — без обрезки
и без полей. Широкие картинки (инфографика, снимки) остаются на всю ширину колонки."""
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


class SquareFigs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)
        cls.h = (ROOT / "mtskheta" / "index.html").read_text(encoding="utf-8")

    def test_square_figure_has_class(self):
        m = re.search(r'<figure class="([^"]*)"><picture>(?:(?!</figure>).)*jvari-confluence\.webp', self.h, re.S)
        self.assertIsNotNone(m)
        self.assertIn("sq", m.group(1).split())
        self.assertRegex(self.h, r'jvari-confluence\.webp"[^>]*width="(\d+)" height="\1"')

    def test_wide_figure_has_no_class(self):
        m = re.search(r'<figure class="([^"]*)"><picture>(?:(?!</figure>).)*mtskheta-timeline\.webp', self.h, re.S)
        self.assertIsNotNone(m)
        self.assertNotIn("sq", m.group(1).split())

    def test_css_limits_square(self):
        css = (ROOT / "assets" / "guide.css").read_text(encoding="utf-8")  # владелец 22.11.2026, А2: общий CSS в assets/guide.css
        self.assertRegex(css, r"\.fig\.sq img\{[^}]*max-width:")
        self.assertRegex(css, r"\.fig\.sq img\{[^}]*margin:0 auto")


if __name__ == "__main__":
    unittest.main()
