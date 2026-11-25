"""/georgian-wine-regions/: Mukuzani без «oak» и «33 entries» как наш подсчёт (отложенное дело d85, 26.11.2026).

Описание наименования Mukuzani (wine.gov.ge/En/Files/Download/15310): «In case of aging the process shall take place in wood
barrels, within no less than 6 months» — дуб не назван. Список наименований на wine.gov.ge — три страницы (12+12+9 = 33 строки),
среди них заявка Болниси и записи без номера; число 33 агентство не публикует — это наш подсчёт.
Правило: на странице нет «oak»; везде, где стоит «33 entries», рядом пометка «our count».
Запуск: python3 -m pytest -q tests/test_wine_regions_en_count.py
"""
import pathlib
import re

MD = pathlib.Path(__file__).resolve().parent.parent / "content/en/georgian-wine-regions.md"


def test_no_oak():
    md = MD.read_text(encoding="utf-8")
    assert not re.search(r"(?i)\boak\b", md), "в описании Mukuzani — wood barrels, не oak"
    assert "ageing in wooden barrels is optional" in md


def test_33_marked_as_our_count():
    md = MD.read_text(encoding="utf-8")
    lines = [l for l in md.splitlines() if re.search(r"\b33\b", l) and not l.lstrip().startswith("<!--")]
    assert lines, "нет числа 33"
    for l in lines:
        for sent in re.split(r"(?<=[.!?])\s+", l):
            if re.search(r"\b33\b", sent):
                assert "our count" in sent, f"33 без пометки «our count»: {sent[:140]}"
