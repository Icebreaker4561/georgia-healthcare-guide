"""Владелец 19.11.2026 о подписях «Иллюстрация, не фото: заросшее здание с колоннами»: «вот эти подписи для кого сделаны? для идиотов?»

Подпись под картинкой (figcaption) — не пересказ того, что и так видно, а полезный факт из раздела.
Проверка по всем собранным страницам:
- подпись не начинается с «Иллюстрация» / «Illustration» и не содержит «не фото» / «not a photo»;
- подпись не короче 25 знаков (одна мысль, а не ярлык).
Описание картинки для поисковиков и экранных дикторов остаётся в alt — его тест не трогает.

Запуск: python3 tests/test_captions_useful.py
"""
import html
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
BAD = re.compile(r"(?i)^\s*(иллюстрац|illustration)|не фото|not a photo")


class UsefulCaptions(unittest.TestCase):
    def test_captions(self):
        bad, total = [], 0
        for p in PAGES:
            for cap in re.findall(r"<figcaption>(.*?)</figcaption>", p.read_text(encoding="utf-8"), re.S):
                total += 1
                text = html.unescape(re.sub(r"<[^>]+>", "", cap)).strip()
                if BAD.search(text) or len(text) < 25:
                    bad.append(f"{p.relative_to(ROOT)}: «{text}»")
        self.assertGreater(total, 150, f"подписей {total}")
        self.assertEqual(bad, [], f"{len(bad)} плохих подписей:\n" + "\n".join(bad[:15]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
