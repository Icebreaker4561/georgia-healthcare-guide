"""Владелец 19.11.2026 о фразе «Зимой в горах нужны зимние шины или цепи, пишет Канада.[6]»:
«Да что такое, при чем тут Канада в статье про Грузию?»

Обычный факт не атрибутируем стране в тексте — источник показывает сноска [N] (стиль Википедии). Прямая цитата и разговор
о самих советах правительств называют источник полностью: «правительство Канады», «Government of Canada».
Проверка: в тексте статей (кроме списка источников) нет «пишет Канада», «по данным Канады», «Канада советует/предупреждает»,
«(Канада)», «Canada says/warns/advises», «according to Canada», «(Canada)» и голого «Канада …» в роли подлежащего-источника.

Запуск: python3 tests/test_no_bare_canada.py
"""
import html
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
BAD = re.compile(
    r"(?<!правительство )(?<!правительства )(?<!Правительство )(?<!Правительства )"
    r"(пишет|пишут|советует|предупреждает|сообщает|напоминает|отмечает)\s+Канада\b"
    r"|по (данным|словам|сведениям) Канады\b|\(Канада\)|\bКанада\s+(пишет|советует|предупреждает|сообщает|отмечает|напоминает|называет|рекомендует)"
    r"|(?<!of )\bCanada\s+(says|warns|advises|notes|recommends|lists|puts|adds)\b|according to Canada\b|\(Canada\)"
    r"|(says|warns|adds|notes)\s+Canada\b"
)


class NoBareCanada(unittest.TestCase):
    def test_no_bare_canada(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            parts = re.findall(r'<div class="hero">.*?</div></div>|<div class="lead-box">.*?</div>|<article class="body">.*?</article>', h, re.S)
            text = " ".join(parts)
            text = re.split(r'<h2 id="sources"', text)[0]
            plain = html.unescape(re.sub(r"<[^>]+>", " ", text))
            alts = " ".join(re.findall(r'<figcaption>(.*?)</figcaption>', text, re.S))
            for m in BAD.finditer(plain + " " + html.unescape(re.sub(r"<[^>]+>", " ", alts))):
                s = plain[max(0, m.start() - 60): m.end() + 20] if m.start() < len(plain) else m.group(0)
                bad.append(f"{p.parent.relative_to(ROOT)}: «…{' '.join(s.split())}…»")
        self.assertEqual(bad, [], f"{len(bad)} мест:\n" + "\n".join(bad[:40]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
