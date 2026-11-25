"""Сухой мост в /ru/tbilisi/ не спорит со статьёй «Рынки Тбилиси» (ru-markets/DECISIONS.md, ТЗ §4; отложенное дело d81).

Статья «Рынки Тбилиси» (/ru/rynki-tbilisi/) берёт возраст блошиного базара из georgia.travel: «в нынешнем виде — с 1950-х».
В /ru/tbilisi/#suhoj-most стояло «в конце 1980-х — начале 1990-х» по Википедии — противоречие. Правило: в разделе
#suhoj-most нет «1980-х», есть «1950-х» со сноской на georgia.travel/flea-markets/dry-bridge-flea-market и ссылка
на /ru/rynki-tbilisi/ (рыночный интент — там).
Запуск: python3 -m pytest -q tests/test_tbilisi_dry_bridge_market.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "content/ru/tbilisi.md"
GT = "https://georgia.travel/flea-markets/dry-bridge-flea-market"


def suhoj_most(md):
    m = re.search(r"^### [^\n]*\{#suhoj-most\}\n(.*?)(?=^#{2,3} )", md, re.S | re.M)
    assert m, "нет раздела #suhoj-most"
    return m.group(1)


def sources(md):
    part = md.split("## Источники {#sources}", 1)[1]
    return re.findall(r"^- \[[^\]]*\]\(([^)]+)\)", part, re.M)


def test_no_1980s_market_date():
    sec = suhoj_most(MD.read_text(encoding="utf-8"))
    assert "1980" not in sec, "«1980-х» противоречит georgia.travel («с 1950-х»)"


def test_1950s_with_georgia_travel_footnote():
    md = MD.read_text(encoding="utf-8")
    sec = suhoj_most(md)
    m = re.search(r"1950-х[^.]*\.((?:\[\^\d+\])+)", sec)
    assert m, "нет факта «с 1950-х» со сноской"
    nums = [int(n) for n in re.findall(r"\[\^(\d+)\]", m.group(1))]
    src = sources(md)
    assert any(0 < n <= len(src) and src[n - 1] == GT for n in nums), "сноска «1950-х» не ведёт на georgia.travel"


def test_links_to_markets_article():
    sec = suhoj_most(MD.read_text(encoding="utf-8"))
    assert "https://guide.100doc.ge/ru/rynki-tbilisi/" in sec, "нет ссылки на «Рынки Тбилиси»"
