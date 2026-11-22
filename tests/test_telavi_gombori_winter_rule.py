"""Поправка владельца 22.11.2026 (d43 → d58): английская /telavi/ — правило о зимних шинах/цепях на Гомбори
по Постановлению Правительства Грузии № 526 (с 1 декабря по 1 марта, км 27–65), со сноской на первоисточник,
как в русской /ru/telavi/. Фраза «официального правила нет» больше не допускается."""
import pathlib, re, unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
MD = (REPO / "content" / "en" / "telavi.md").read_text(encoding="utf-8")
HTML = (REPO / "telavi" / "index.html").read_text(encoding="utf-8")


class GomboriWinterRule(unittest.TestCase):
    def test_no_old_claim(self):
        self.assertNotRegex(MD, r"(?i)found no official rule on snow chains")

    def test_rule_stated_with_footnote(self):
        para = [p for p in MD.split("\n\n") if "No. 526" in p]
        self.assertTrue(para, "нет абзаца с Resolution No. 526")
        p = para[0]
        for need in (r"1 December", r"1 March", r"27\D{1,3}65", r"(?i)winter tyres", r"(?i)chains", r"\[\^\d+\]"):
            self.assertRegex(p, need, need)

    def test_source_listed(self):
        self.assertIn("https://matsne.gov.ge/ka/document/view/6040563", MD)

    def test_built(self):
        self.assertIn("No. 526", HTML, "страница не пересобрана")


if __name__ == "__main__":
    unittest.main()
