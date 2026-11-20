"""Владелец 20.11.2026: «структурируем меню, потому что сейчас в нём вперемешку статьи про здоровье и статьи про
достопримечательности» → выбран вариант А: три раздела.

  Здоровье и безопасность / Health & safety   — section: health
  Куда поехать / Places                        — section: places, region: tbilisi | mountains | west | south-east
  Дорога и быт / Getting around                — section: practical

Проверяет исходники и все собранные страницы:
- у каждой статьи в шапке исходника есть section, у мест — region; статья о здоровье с region (Гудаури: высота)
  показывается и в своём разделе, и среди мест под подписью nav_place;
- меню на каждой странице — три раскрывающихся раздела <details name="menu"> (без скриптов) в этом порядке;
  внутри — все статьи раздела на языке страницы; у мест — подзаголовки регионов в постоянном порядке;
- в меню нет ссылок на статьи другого языка; текущая статья помечена aria-current;
- хлебные крошки: Главная › Раздел › Статья (раздел ведёт на блок главной), в разметке BreadcrumbList — те же три шага;
- на главной — три блока карточек с id health / places / practical, в каждом все статьи раздела;
- «Ещё по теме» в статье — статьи того же раздела;
- цели нажатия в меню не меньше 44 px (стиль).

Запуск: python3 tests/test_menu.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
SECTIONS = ["health", "places", "practical"]
REGIONS = ["tbilisi", "mountains", "west", "south-east"]
LABEL = {"ru": {"health": "Здоровье и безопасность", "places": "Куда поехать", "practical": "Дорога и быт"},
         "en": {"health": "Health & safety", "places": "Places", "practical": "Getting around"}}
REGION_LABEL = {"ru": {"tbilisi": "Тбилиси и рядом", "mountains": "Горы", "west": "Запад и море", "south-east": "Юг и восток"},
                "en": {"tbilisi": "Tbilisi and around", "mountains": "Mountains", "west": "West and the coast",
                       "south-east": "South and east"}}


def front(p):
    t = (ROOT / p["src"]).read_text(encoding="utf-8")
    head = t.split("---")[1]
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in head.strip().splitlines() if ":" in l)}


def out(p):
    rel = p["slug"] if p["lang"] == "en" else ("ru/" + p["slug"] if p["slug"] else "ru")
    return ROOT / (rel + "/index.html" if rel else "index.html")


def url(p):
    rel = p["slug"] if p["lang"] == "en" else ("ru/" + p["slug"] if p["slug"] else "ru")
    return BASE + (rel + "/" if rel else "")


ARTICLES = [p for p in SITE["pages"] if p["slug"]]
FM = {(p["lang"], p["slug"]): front(p) for p in ARTICLES}


def html(p):
    return out(p).read_text(encoding="utf-8")


def menu(h):
    m = re.search(r'<nav class="menu[^"]*"[^>]*>(.*?)</nav>', h, re.S)
    return m.group(1) if m else ""


def blocks(m):
    """data-sec -> содержимое раздела меню."""
    return dict(re.findall(r'<details class="msec" name="menu" data-sec="([\w-]+)">(.*?)</details>', m, re.S))


def hrefs(fragment, page):
    """Абсолютные адреса ссылок фрагмента (относительно страницы)."""
    import urllib.parse
    return [urllib.parse.urljoin(url(page), h).split("#")[0] for h in re.findall(r'href="([^"]+)"', fragment)]


def members(lang, sec):
    """Статьи раздела: свои + статьи здоровья с region — среди мест."""
    res = []
    for p in ARTICLES:
        if p["lang"] != lang:
            continue
        f = FM[(lang, p["slug"])]
        if f.get("section") == sec or (sec == "places" and f.get("region")):
            res.append(p)
    return res


class Sources(unittest.TestCase):
    def test_every_article_has_section_and_places_have_region(self):
        bad = []
        for (lang, slug), f in FM.items():
            if f.get("section") not in SECTIONS:
                bad.append(f"{lang}/{slug}: section «{f.get('section')}»")
            if f.get("section") == "places" and f.get("region") not in REGIONS:
                bad.append(f"{lang}/{slug}: место без region (или неизвестный «{f.get('region')}»)")
            if f.get("region") and f.get("region") not in REGIONS:
                bad.append(f"{lang}/{slug}: неизвестный region «{f.get('region')}»")
            if f.get("section") != "places" and f.get("region") and not f.get("nav_place"):
                bad.append(f"{lang}/{slug}: статья среди мест без nav_place")
        self.assertEqual(bad, [], "\n".join(bad))


class Menu(unittest.TestCase):
    def test_three_sections_in_order_on_every_page(self):
        bad = []
        for p in SITE["pages"]:
            m = menu(html(p))
            secs = re.findall(r'<details class="msec" name="menu" data-sec="([\w-]+)">', m)
            if secs != SECTIONS:
                bad.append(f"{out(p).relative_to(ROOT)}: разделы {secs}")
            for s in SECTIONS:
                if f"<summary>{LABEL[p['lang']][s]}" not in m.replace("&amp;", "&"):
                    bad.append(f"{out(p).relative_to(ROOT)}: нет подписи «{LABEL[p['lang']][s]}»")
            if "<script" in m:
                bad.append(f"{out(p).relative_to(ROOT)}: в меню скрипт")
        self.assertEqual(bad, [], "\n".join(bad[:30]))

    def test_each_section_lists_all_its_articles_same_language_only(self):
        bad = []
        for p in SITE["pages"]:
            b = blocks(menu(html(p)))
            lang_urls = {url(x) for x in ARTICLES if x["lang"] == p["lang"]}
            for s in SECTIONS:
                got = set(hrefs(b.get(s, ""), p))
                want = {url(x) for x in members(p["lang"], s)}
                if got != want:
                    bad.append(f"{out(p).relative_to(ROOT)} [{s}]: лишние {sorted(got - want)[:3]}, нет {sorted(want - got)[:3]}")
                if got - lang_urls:
                    bad.append(f"{out(p).relative_to(ROOT)} [{s}]: ссылки на другой язык {sorted(got - lang_urls)[:3]}")
        self.assertEqual(bad, [], "\n".join(bad[:30]))

    def test_places_grouped_by_region_in_fixed_order(self):
        bad = []
        for p in [x for x in SITE["pages"] if not x["slug"]]:
            places = blocks(menu(html(p))).get("places", "")
            heads = re.findall(r'<p class="mreg">(.*?)</p>', places)
            want = [REGION_LABEL[p["lang"]][r] for r in REGIONS if any(FM[(p["lang"], x["slug"])].get("region") == r
                                                                      for x in members(p["lang"], "places"))]
            if [h.replace("&amp;", "&") for h in heads] != want:
                bad.append(f"{p['lang']}: регионы {heads}, нужно {want}")
            parts = re.split(r'<p class="mreg">', places)[1:]
            for part in parts:
                label = part.split("</p>")[0].replace("&amp;", "&")
                reg = next(k for k, v in REGION_LABEL[p["lang"]].items() if v == label)
                for u in hrefs(part, p):
                    x = next(a for a in ARTICLES if url(a) == u)
                    if FM[(x["lang"], x["slug"])].get("region") != reg:
                        bad.append(f"{p['lang']}: {u} не в своём регионе «{label}»")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_current_page_marked(self):
        bad = []
        for p in ARTICLES:
            m = menu(html(p))
            cur = re.findall(r'<a href="([^"]+)" aria-current="page"', m)
            if not cur or any(u != url(p) for u in hrefs(" ".join(f'href="{c}"' for c in cur), p)):
                bad.append(f"{out(p).relative_to(ROOT)}: aria-current {cur}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))


class Crumbs(unittest.TestCase):
    def test_three_step_crumbs_with_section(self):
        bad = []
        for p in ARTICLES:
            h = html(p)
            sec = FM[(p["lang"], p["slug"])]["section"]
            c = re.search(r'<nav class="crumbs"[^>]*>(.*?)</nav>', h, re.S)
            links = re.findall(r'<a href="([^"]+)">(.*?)</a>', c.group(1)) if c else []
            if len(links) != 2 or links[1][1].replace("&amp;", "&") != LABEL[p["lang"]][sec] or not links[1][0].endswith("#" + sec):
                bad.append(f"{out(p).relative_to(ROOT)}: крошки {links}")
            ld = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
            bl = next((x for x in ld if x.get("@type") == "BreadcrumbList"), None)
            items = bl["itemListElement"] if bl else []
            home = BASE + ("ru/" if p["lang"] == "ru" else "")
            if [i.get("item") for i in items] != [home, home + "#" + sec, url(p)]:
                bad.append(f"{out(p).relative_to(ROOT)}: BreadcrumbList {[i.get('item') for i in items]}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))


class Home(unittest.TestCase):
    def test_home_has_three_card_blocks(self):
        bad = []
        for p in [x for x in SITE["pages"] if not x["slug"]]:
            h = html(p)
            for s in SECTIONS:
                m = re.search(rf'<section class="hub" id="{s}"[^>]*>(.*?)</section>', h, re.S)
                if not m:
                    bad.append(f"{p['lang']}: нет блока #{s}"); continue
                got = set(re.findall(r'<a class="card" href="([^"]+)"', m.group(1)))
                got = set(hrefs(" ".join(f'href="{g}"' for g in got), p))
                want = {url(x) for x in members(p["lang"], s)}
                if got != want:
                    bad.append(f"{p['lang']} #{s}: лишние {sorted(got - want)[:3]}, нет {sorted(want - got)[:3]}")
        self.assertEqual(bad, [], "\n".join(bad))


class Related(unittest.TestCase):
    def test_related_from_same_section(self):
        bad = []
        for p in ARTICLES:
            h = html(p)
            m = re.search(r'<section class="related"[^>]*>(.*?)</section>', h, re.S)
            if not m:
                continue
            same = {url(x) for x in members(p["lang"], FM[(p["lang"], p["slug"])]["section"])}
            for u in hrefs(" ".join(f'href="{g}"' for g in re.findall(r'<a class="card" href="([^"]+)"', m.group(1))), p):
                if u not in same:
                    bad.append(f"{out(p).relative_to(ROOT)}: «Ещё по теме» ведёт в другой раздел: {u}")
        self.assertEqual(bad, [], "\n".join(bad[:20]))


class Style(unittest.TestCase):
    def test_tap_targets_44(self):
        css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
        for sel in (r"\.msec>summary", r"\.mpanel a"):
            m = re.search(sel + r"\{[^}]*min-height:44px", css)
            self.assertTrue(m, f"нет min-height:44px у {sel}")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
