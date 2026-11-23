"""Служебные HTML-комментарии исходника не попадают на страницу (reviewer abastumani-ru, 23.11.2026).

Сборщик делил текст на абзацы по пустым строкам и пропускал только абзац, начинающийся с «<!--»: многоабзацный
комментарий («<!-- служебное, не для публикации …») утекал на страницу как текст — так было на /ru/ureki/.
Правило: в собранных страницах нет экранированных «&lt;!--» / «--&gt;» и служебных пометок редакции.
Запуск: python3 tests/test_no_comment_leak.py
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKERS = ("--&gt;", "&lt;!--", "не для публикации", "Проверить перед публикацией", "зона счёта", "Зона счёта")


class NoCommentLeak(unittest.TestCase):
    def test_no_service_text_in_pages(self):
        bad = []
        for p in sorted(ROOT.rglob("index.html")):
            if ".git" in p.parts or "node_modules" in p.parts:
                continue
            h = p.read_text(encoding="utf-8")
            for m in MARKERS:
                if m in h:
                    bad.append(f"{p.relative_to(ROOT)}: «{m}»")
        self.assertEqual(bad, [], "служебный текст на страницах:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
