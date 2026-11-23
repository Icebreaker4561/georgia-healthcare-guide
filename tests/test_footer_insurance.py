"""Владелец 23.11.2026: «почему бы нам в гайд не добавить в подвал ссылки на страховки туристические и на маркетплейс
страховок Грузии?» — «Да, классно, начинай делать».

Проверяет все собранные страницы: в подвале, в колонке 100doc.ge (рядом с «Отзывы о врачах» и «Блог»), есть
- «Страховка для туристов» → https://100doc.ge/tourist/ (ru) / «Travel insurance» → https://100doc.ge/tourist/en (en);
- «Маркетплейс страховок Грузии» → https://100doc.ge/ru/insurance/ (ru) /
  «Georgia insurance marketplace» → https://100doc.ge/en/insurance/ (en);
ссылки без nofollow; прежние «Отзывы о врачах» и «Блог» на месте.

Запуск: python3 tests/test_footer_insurance.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
NEED = {
    "ru": [("https://100doc.ge/tourist/", "Страховка для туристов"),
           ("https://100doc.ge/ru/insurance/", "Маркетплейс страховок Грузии"),
           ("https://100doc.ge/ru/", "Отзывы о врачах"), ("https://100doc.ge/ru/blog/", "Блог")],
    "en": [("https://100doc.ge/tourist/en", "Travel insurance"),
           ("https://100doc.ge/en/insurance/", "Georgia insurance marketplace"),
           ("https://100doc.ge/en/", "Doctor reviews"), ("https://100doc.ge/en/blog/", "Blog")],
}


def rel(p):
    if p["slug"] == "":
        return "" if p["lang"] == "en" else "ru/"
    return (p["slug"] if p["lang"] == "en" else "ru/" + p["slug"]) + "/"


class FooterInsurance(unittest.TestCase):
    def test_footer_links(self):
        bad = []
        for p in SITE["pages"]:
            h = (ROOT / rel(p) / "index.html").read_text(encoding="utf-8")
            key = p["lang"] + ":" + p["slug"]
            foot = re.search(r"<footer\b.*?</footer>", h, re.S)
            col = re.search(r'<nav class="cf-col" aria-label="100doc\.ge">(.*?)</nav>', foot.group(0) if foot else "", re.S)
            if not col:
                bad.append(f"{key}: нет колонки 100doc.ge в подвале"); continue
            links = re.findall(r'<a ([^>]*)>(.*?)</a>', col.group(1), re.S)
            got = [(re.search(r'href="([^"]+)"', a).group(1), re.sub(r"<[^>]+>", "", t).strip(), a) for a, t in links]
            for href, text in NEED[p["lang"]]:
                hit = [g for g in got if g[0] == href and g[1] == text]
                if not hit:
                    bad.append(f"{key}: нет ссылки «{text}» → {href}")
                elif "nofollow" in hit[0][2]:
                    bad.append(f"{key}: «{text}» с nofollow")
        self.assertEqual(bad, [], "\n".join(bad[:20]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
