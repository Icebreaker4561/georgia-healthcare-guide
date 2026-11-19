"""Владелец 19.11.2026 (снимок плашки цифр на /ru/batumi/: «2 500 мм» обрезано, пустая серая клетка): «вот еще косяки»,
«перепроверь все».

Открывает КАЖДУЮ собранную страницу в браузере на 1440 и 390 точках и проверяет плашку цифр (dl.stats) и страницу:
- ни одно значение и подпись плитки не вылезает за свою плитку (scrollWidth <= clientWidth);
- плитки целиком внутри плашки по ширине;
- нет пустых клеток: плитки последнего ряда дотягиваются до правого края плашки;
- у страницы нет горизонтальной прокрутки.

Запуск: python3 tests/test_stats_layout.py
"""
import pathlib
import sys
import unittest

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts and "assets" not in p.parts)

JS = """() => {
  const out = [];
  const de = document.documentElement;
  if (de.scrollWidth > de.clientWidth + 1) out.push('горизонтальная прокрутка страницы ' + de.scrollWidth + '>' + de.clientWidth);
  document.querySelectorAll('dl.stats').forEach(dl => {
    const box = dl.getBoundingClientRect();
    const tiles = [...dl.children];
    const rows = {};
    tiles.forEach(t => {
      const r = t.getBoundingClientRect();
      if (r.left < box.left - 1 || r.right > box.right + 1) out.push('плитка вне плашки: ' + t.innerText.replace(/\\s+/g, ' '));
      t.querySelectorAll('dt,dd').forEach(e => {
        if (e.scrollWidth > e.clientWidth + 1) out.push('текст вылезает: ' + e.innerText.replace(/\\s+/g, ' '));
      });
      const k = Math.round(r.top);
      rows[k] = Math.max(rows[k] || 0, r.right);
    });
    Object.entries(rows).forEach(([k, right]) => {
      if (right < box.right - 3) out.push('пустая клетка в ряду плашки (не хватает ' + Math.round(box.right - right) + ' px)');
    });
  });
  return out;
}"""


class StatsLayout(unittest.TestCase):
    def test_all_pages_both_widths(self):
        bad = []
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            for w, h in ((1440, 900), (390, 844)):
                pg = b.new_page(viewport={"width": w, "height": h})
                for f in PAGES:
                    pg.goto(f.as_uri())
                    for msg in pg.evaluate(JS):
                        bad.append(f"{w}: {f.parent.relative_to(ROOT)}: {msg}")
                pg.close()
            b.close()
        self.assertGreater(len(PAGES), 40)
        self.assertEqual(bad, [], f"{len(bad)} проблем:\n" + "\n".join(bad[:60]))


class StatsWrapByWords(unittest.TestCase):
    """Снимок 19.11.2026 после первой правки: «Octobe r», «3 0 лари», «м есте» — значение плитки было склеено
    неразрывными пробелами целиком и рвалось посреди слова. Неразрывный пробел — только после цифры («157 km»)."""

    def test_no_glued_words_in_tiles(self):
        import re
        bad = []
        for f in PAGES:
            for dd in re.findall(r"<dd>(.*?)</dd>", f.read_text(encoding="utf-8"), re.S):
                t = re.sub(r"<[^>]+>", "", dd)
                if re.search(r"(?<!\d)(&nbsp;| )", t):
                    bad.append(f"{f.parent.relative_to(ROOT)}: {t[:80]}")
        self.assertEqual(bad, [], f"{len(bad)} плиток со склеенными словами:\n" + "\n".join(bad[:30]))

    def test_no_mid_word_hyphenation(self):
        css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"\.stats[^{]*\{[^}]*hyphens:auto", "переносы слов дефисом в плитках не нужны")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
