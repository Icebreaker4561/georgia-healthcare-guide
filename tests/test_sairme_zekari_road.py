"""Поправка владельца 23.11.2026 (d73 → d75, «Смягчить»): в «Саирме» (RU и EN) дорога за курортом к Абастумани
и перевал Зекари — по официальным данным, как в /ru/abastumani/: участок через перевал отремонтирован и заасфальтирован
(Департамент автодорог через BM.ge), графика зимнего закрытия мы не нашли. Блоговые «грунтовая и очень плохая» и
«закрыт с декабря по март» больше не допускаются — ни в тексте, ни на инфографике."""
import pathlib, re, unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
FOLDERS = pathlib.Path.home() / "SEO_Vasiliy" / "content" / "microsite-healthcare-guide"
BM = "https://bm.ge/en/news/construction-of-16-km-road-on-zekari-pass-completed-15-years-behind-schedule"
PAGES = {
    "ru": (REPO / "content" / "ru" / "sairme.md", REPO / "ru" / "sairme" / "index.html", FOLDERS / "ru-sairme" / "img" / "src" / "figs.py",
           [r"(?i)грунтов[а-я]* и очень плох", r"(?i)декабр[а-я]* по март", r"(?i)обычно закрыт"], r"(?i)асфальт"),
    "en": (REPO / "content" / "en" / "sairme.md", REPO / "sairme" / "index.html", FOLDERS / "sairme-en" / "img" / "src" / "figs.py",
           [r"(?i)unpaved and very rough", r"(?i)December to March", r"(?i)(usually|normally) closed"], r"(?i)asphalt"),
}


class SairmeZekariRoad(unittest.TestCase):
    def test_no_old_claims(self):
        for lang, (md, html, figs, bad, _) in PAGES.items():
            for src in (md.read_text(encoding="utf-8"), figs.read_text(encoding="utf-8")):
                for pat in bad:
                    self.assertNotRegex(src, pat, f"{lang}: {pat}")

    def test_official_data_with_footnote(self):
        for lang, (md, html, figs, bad, paved) in PAGES.items():
            t = md.read_text(encoding="utf-8")
            para = [p for p in t.split("\n\n") if re.search(r"Зекари|Zekari", p) and not p.lstrip().startswith("<!--")]
            self.assertTrue(para, f"{lang}: нет абзаца о Зекари")
            road = [p for p in para if re.search(paved, p) and re.search(r"BM\.ge|Roads Department|Департамент автодорог", p)]
            self.assertTrue(road, f"{lang}: нет абзаца об асфальте через перевал со ссылкой на Департамент автодорог")
            self.assertRegex(road[0], r"\[\^\d+\]", f"{lang}: нет сноски")
            self.assertRegex(t, r"(?i)графика закрытия[^.]*не нашли|found no (official )?(winter )?closure schedule", f"{lang}: нет «графика закрытия не нашли»")
            self.assertIn(BM, t, f"{lang}: BM.ge нет в источниках")

    def test_built(self):
        for lang, (md, html, *_ ) in PAGES.items():
            self.assertIn("bm.ge/en/news/construction-of-16-km-road-on-zekari-pass", html.read_text(encoding="utf-8"), f"{lang}: страница не пересобрана")


if __name__ == "__main__":
    unittest.main()
