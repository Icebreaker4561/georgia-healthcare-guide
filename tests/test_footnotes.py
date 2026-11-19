"""Владелец 19.11.2026: «Да, делай сноски в стиле Википедии» — на каждое упоминание источника релевантная ссылка.

Формат: в тексте статьи после утверждения стоит сноска [N] (<sup class="fn"><a href="#src-N">[N]</a></sup>),
N — номер источника в разделе «Источники»; список источников нумерованный (<ol class="sources">),
у пункта id="src-N" и обратная ссылка ↑ к первому месту в тексте (id="ref-N").

Проверки по всем статьям (ru и en):
- каждая сноска ведёт на существующий пункт списка источников;
- у каждого пункта, на который есть сноска, есть обратная ссылка, и она ведёт на существующий id;
- каждое предложение с атрибуцией («по GOV.UK», «пишет Канада», «по Википедии», «according to NHS» …) несёт сноску;
- в разметке FAQPage (JSON-LD) нет «[N]» — поисковикам отдаём чистый текст.

ВОЗ/WHO — только заглавными и целым словом: «по возможности» не атрибуция (владелец 19.11.2026: «Тест поправь»).

Запуск: python3 tests/test_footnotes.py
"""
import html
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)

SRC = (r"(GOV\.UK|FCDO|Канад\w*|Canada|Википеди\w*|Wikipedia|NHS|(?-i:ВОЗ|WHO)\b|TravelHealthPro|CDC|нацпарк\w*|национальн\w+ парк\w*|"
       r"national park\w*|nationalparks\.ge|парк[аеу]?\b|брошюр\w*|brochure|постановлени\w*|resolution|закон\w*|the law|Минздрав\w*|"
       r"Geostat|GoBatumi|Georgia Today|georgia\.travel|EUAA|112\.gov\.ge|сайт\w* служб\w*|railway\.ge|Агентств\w+)")
ATTR = re.compile(
    rf"(?i)(\bпо (данным |словам |сведениям )?{SRC}|{SRC},? (пишет|пишут|советует|советуют|предупреждает|называет|сообщает|"
    rf"рекомендует|указывает|отмечает|says|say|advises|warns|recommends|notes|lists|puts)|\b(пишет|советует|предупреждает) {SRC}|"
    rf"\baccording to (the )?{SRC})"
)


def article(h):
    m = re.search(r'<article class="body">(.*?)</article>', h, re.S)
    return m.group(1) if m else ""


class Footnotes(unittest.TestCase):
    def test_links_resolve_and_backlinks(self):
        bad, pages_with_fn = [], 0
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            art = article(h)
            if 'id="sources"' not in art:
                continue
            refs = set(re.findall(r'<sup class="fn"><a href="#src-(\d+)"', art))
            if refs:
                pages_with_fn += 1
            ids = set(re.findall(r'<li id="src-(\d+)"', art))
            if 'class="sources"' in art and not re.search(r'<ol class="sources">', art):
                bad.append(f"{p.relative_to(ROOT)}: список источников не нумерованный")
            for n in refs - ids:
                bad.append(f"{p.relative_to(ROOT)}: сноска [{n}] без источника")
            for n in refs:
                if f'id="ref-{n}"' not in art or f'href="#ref-{n}"' not in art:
                    bad.append(f"{p.relative_to(ROOT)}: у источника {n} нет обратной ссылки")
        self.assertGreater(pages_with_fn, 40, f"страниц со сносками {pages_with_fn}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_every_attribution_has_footnote(self):
        bad = []
        for p in PAGES:
            art = article(p.read_text(encoding="utf-8"))
            if 'id="sources"' not in art:
                continue
            body = re.split(r'<h2 id="sources"', art)[0]
            body = re.sub(r"<figure.*?</figure>", " ", body, flags=re.S)
            body = re.sub(r'<dl class="stats">.*?</dl>', " ", body, flags=re.S)
            for blk in re.findall(r"<(p|li|dd|td)[^>]*>(.*?)</\1>", body, re.S):
                for s in re.split(r"(?<=[.!?])\s+(?=[А-ЯA-Z«\"(<])", blk[1]):
                    text = html.unescape(re.sub(r"<[^>]+>", "", s))
                    if ATTR.search(text) and 'class="fn"' not in s:
                        bad.append(f"{p.relative_to(ROOT)}: «{text.strip()[:130]}»")
        self.assertEqual(bad, [], f"{len(bad)} атрибуций без сноски:\n" + "\n".join(bad[:30]))

    def test_faq_ld_clean(self):
        bad = []
        for p in PAGES:
            for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', p.read_text(encoding="utf-8"), re.S):
                d = json.loads(m.group(1))
                if d.get("@type") == "FAQPage" and re.search(r"\[\d+\]", json.dumps(d, ensure_ascii=False)):
                    bad.append(str(p.relative_to(ROOT)))
        self.assertEqual(bad, [], "\n".join(bad))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
