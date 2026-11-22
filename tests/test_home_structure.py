"""Главные guide.100doc.ge (/ru/ и /) по утверждённым макетам владельца 22.11.2026
(~/SEO_Vasiliy/content/microsite-healthcare-guide/migration/home-mockup-{ru,en}.html).

Порядок: H1 (из home.md) → лид «Путеводитель 100doc.ge — …» / «The 100doc.ge Georgia Travel Guide covers …» → строка доверия →
чипы-якоря → «Коротко» (4 пункта из home.md) → H2 таблица «Грузия коротко: главное из каждой статьи» (с числом строк) →
H2 по разделам (Куда поехать / Здоровье и безопасность / Дорога и быт) с карточками, заголовок карточки — H3, регионы —
подписи, не заголовки → разделы текста home.md → H2 «Частые вопросы» (5 вопросов H3 в <details>) → «Официальные источники».
Глубина заголовков — не больше H3.

Таблица строится из ВСЕХ статей языка, строка на статью: 1-я закреплена — 112 / скорая; 2-я — «Страховка для въезда»
(пункт про 30 000 лари из «Коротко» главной, источник matsne, розовая кнопка на 100doc.ge/tourist); дальше
строки-разделители (не заголовки) по разделам и регионам. В строке статьи: что = crumb, ответ = дословно пункт «Коротко»
статьи (home_fact: N в шапке или первый пункт со сноской), источник = первая ссылка источника этой сноски,
«Подробно» = ссылка на статью. Источник есть у каждой строки.
Разметка: CollectionPage (about: Грузия, sameAs Wikidata Q230; publisher 100doc.ge; ItemList всех статей), FAQPage,
BreadcrumbList.
Запуск: python3 -m pytest -q tests/test_home_structure.py
"""
import html as H
import json
import pathlib
import re
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
NEW = "https://guide.100doc.ge/"
SECTIONS = ["places", "health", "practical"]
REGIONS = ["tbilisi", "mountains", "west", "south-east"]
SEC = {"ru": {"health": "Здоровье и безопасность", "places": "Куда поехать", "practical": "Дорога и быт"},
       "en": {"health": "Health & safety", "places": "Places", "practical": "Getting around"}}
REG = {"ru": {"tbilisi": "Тбилиси и рядом", "mountains": "Горы", "west": "Запад и море", "south-east": "Юг и восток"},
       "en": {"tbilisi": "Tbilisi and around", "mountains": "Mountains", "west": "West and the coast", "south-east": "South and east"}}
GLANCE = {"ru": "Грузия коротко: главное из каждой статьи", "en": "Georgia at a glance: the key fact from every article"}
LEAD = {"ru": "Путеводитель 100doc.ge — ", "en": "The 100doc.ge Georgia Travel Guide covers places to go, getting around and staying safe."}
PIN112 = {"ru": "112-v-gruzii", "en": "ambulance-georgia"}
INS = {"ru": ("Страховка для въезда", "https://100doc.ge/tourist/", "Оформить полис для въезда на 100doc.ge →"),
       "en": ("Entry insurance", "https://100doc.ge/tourist/en", "Get Georgia entry insurance on 100doc.ge →")}
MATSNE = "https://matsne.gov.ge/ka/document/view/6728816"
CHECKED = {"ru": "Проверено", "en": "Checked"}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
          "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]}
CHIPS = ["#places", "#health", "#practical", "#faq", "#emergency"]


def text(s):
    s = re.sub(r'<sup class="fn".*?</sup>', "", s, flags=re.S)
    return " ".join(H.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def rel(p):
    r = (p["slug"] if p["lang"] == "en" else ("ru/" + p["slug"] if p["slug"] else "ru"))
    return r + "/" if r else ""


def unq(v):
    """Кавычки вокруг значения в шапке исходника — не часть значения (так читает и сборщик)."""
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def front(src):
    t = (ROOT / src).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    return {k.strip(): unq(v.strip()) for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}, t[m.end():]


def date(d, lang):
    y, m, dd = map(int, d.split("-"))
    return f"{dd} {MONTHS[lang][m - 1]} {y}"


class Home(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = {}
        for lang in ("ru", "en"):
            home = next(p for p in SITE["pages"] if p["lang"] == lang and not p["slug"])
            arts = [p for p in SITE["pages"] if p["lang"] == lang and p["slug"]]
            fm = {p["slug"]: front(p["src"])[0] for p in arts}
            hfm, hbody = front(home["src"])
            h = (ROOT / rel(home) / "index.html").read_text(encoding="utf-8")
            cls.d[lang] = dict(home=home, arts=arts, fm=fm, hfm=hfm, hbody=hbody, h=h, url=NEW + rel(home))

    def each(self):
        for lang in ("ru", "en"):
            yield lang, self.d[lang]

    def test_head_h1_lead_trust_chips(self):
        for lang, d in self.each():
            h, hfm = d["h"], d["hfm"]
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, lang)
            self.assertEqual(text(re.search(r"<h1>(.*?)</h1>", h, re.S).group(1)), text(hfm["h1"]), lang)
            self.assertEqual(H.unescape(re.search(r"<title>(.*?)</title>", h).group(1)), hfm["title"])
            self.assertIn(f'<meta name="description" content="{H.escape(hfm["description"])}">', h)
            lead = text(re.search(r'<p class="lead">(.*?)</p>', h, re.S).group(1))
            self.assertTrue(lead.startswith(LEAD[lang]), f"{lang}: лид «{lead[:80]}»")
            want = hfm["lead"] if lang == "en" else hfm["lead"][0].lower() + hfm["lead"][1:]
            self.assertIn(want, lead, lang)
            trust = re.search(r'<p class="trust">(.*?)</p>', h, re.S)
            self.assertTrue(trust and "100doc.ge" in trust.group(1) and str(len(d["arts"])) in trust.group(1), lang)
            chips = re.search(r'<nav class="chips"[^>]*>(.*?)</nav>', h, re.S)
            self.assertTrue(chips, lang)
            self.assertEqual(re.findall(r'<a class="chip" href="([^"]+)"', chips.group(1)), CHIPS, lang)
            facts = re.search(r'<aside class="box facts">(.*?)</aside>', h, re.S)
            self.assertTrue(facts, lang)
            self.assertEqual(facts.group(1).count("<li>"), 4, lang)
            order = [h.find(x) for x in ('<p class="lead">', '<p class="trust">', '<nav class="chips"', '<aside class="box facts">',
                                         '<section class="glance"')]
            self.assertEqual(order, sorted(order), f"{lang}: порядок блоков {order}")

    def test_headings(self):
        for lang, d in self.each():
            h = d["h"]
            self.assertIsNone(re.search(r"<h[4-6][ >]", h), f"{lang}: H4–H6 на главной")
            got = [text(re.sub(r'<span class="n">\d+</span>', "", x)) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", h, re.S)]
            md = re.findall(r"^## (.+?) \{#([\w-]+)\}\s*$", d["hbody"], re.M)
            titles = {i: t for t, i in md}
            self.assertIn("faq", titles, f"{lang}: в home.md нет раздела {{#faq}}")
            want = ([GLANCE[lang]] + [SEC[lang][s] for s in SECTIONS] + [t for t, i in md if i not in ("faq", "sources")]
                    + [titles["faq"], titles["sources"]])
            self.assertEqual(got, [text(w) for w in want], lang)

    def test_cards(self):
        for lang, d in self.each():
            h = d["h"]
            for s in SECTIONS:
                m = re.search(rf'<section class="hub" id="{s}"[^>]*>(.*?)</section>', h, re.S)
                self.assertTrue(m, f"{lang}: нет #{s}")
                cards = re.findall(r'<a class="card" href="([^"]+)">(.*?)</a>', m.group(1), re.S)
                self.assertTrue(cards, f"{lang} #{s}")
                for href, inner in cards:
                    u = urllib.parse.urljoin(d["url"], href)
                    p = next(x for x in d["arts"] if NEW + rel(x) == u)
                    f = d["fm"][p["slug"]]
                    self.assertIn(f"<h3>{H.escape(f['card'], quote=False)}</h3>", inner, u)
                    self.assertIn(H.escape(f["card_desc"], quote=False), inner, u)
                    self.assertIn(f"{CHECKED[lang]} {date(f['updated'], lang)}", text(inner), u)
                    if f.get("og"):
                        img = re.search(r'<img src="([^"]+)" alt="([^"]+)" width="\d+" height="\d+"', inner)
                        self.assertTrue(img and img.group(1).endswith("/" + f["og"]), u)
                if s == "places":
                    labels = [text(x) for x in re.findall(r'<p class="grp">(.*?)</p>', m.group(1), re.S)]
                    want = [REG[lang][r] for r in REGIONS if any(d["fm"][x["slug"]].get("region") == r for x in d["arts"])]
                    self.assertEqual(labels, want, lang)

    def test_faq(self):
        for lang, d in self.each():
            m = re.search(r'<section class="faq"[^>]*><h2 id="faq">.*?</section>', d["h"], re.S)
            self.assertTrue(m, lang)
            qs = re.findall(r'<details class="qa"><summary><h3[^>]*>(.*?)</h3></summary>', m.group(0), re.S)
            self.assertEqual(len(qs), 5, lang)

    def rows(self, lang):
        h = self.d[lang]["h"]
        sec = re.search(r'<section class="glance" id="glance"[^>]*>(.*?)</section>', h, re.S)
        self.assertTrue(sec, lang)
        self.assertRegex(sec.group(1), r'<div class="tbl glance-tbl"><table>')
        body = re.search(r"<tbody>(.*?)</tbody>", sec.group(1), re.S).group(1)
        return sec.group(1), re.findall(r"<tr( class=\"[^\"]+\")?>(.*?)</tr>", body, re.S)

    def test_table_rows(self):
        for lang, d in self.each():
            sec, trs = self.rows(lang)
            data = [(c, r) for c, r in trs if c != ' class="g"']
            groups = [text(r) for c, r in trs if c == ' class="g"']
            n = re.search(r'<h2[^>]*>.*?<span class="n">(\d+)</span></h2>', sec, re.S)
            self.assertEqual(int(n.group(1)), len(data), lang)
            # строки-разделители — не заголовки
            for c, r in trs:
                if c == ' class="g"':
                    self.assertRegex(r, r'^<td colspan="4">[^<]+</td>$')
            want_groups = [SEC[lang]["health"], SEC[lang]["practical"]] + [
                f"{SEC[lang]['places']} · {REG[lang][r]}" for r in REGIONS
                if any(d["fm"][x["slug"]].get("section") == "places" and d["fm"][x["slug"]].get("region") == r for x in d["arts"])]
            self.assertEqual(groups, [text(g) for g in want_groups], lang)
            # 1 — 112
            mores = [self._more(lang, r) for c, r in data]
            self.assertEqual(mores[0], NEW + rel(next(x for x in d["arts"] if x["slug"] == PIN112[lang])), f"{lang}: первая строка не 112")
            # 2 — страховка
            label, href, btn = INS[lang]
            r2 = data[1][1]
            self.assertEqual(text(re.search(r'<th scope="row">(.*?)</th>', r2).group(1)), label)
            bullet = [l[4:] for l in d["hbody"].splitlines() if l.startswith("> - ") and re.search(r"30[~,]000", l)]
            self.assertEqual(len(bullet), 1)
            facts = re.search(r'<aside class="box facts">(.*?)</aside>', d["h"], re.S).group(1)
            ins_li = [text(x) for x in re.findall(r"<li>(.*?)</li>", facts, re.S) if re.search(r"30.000", text(x))]
            self.assertEqual(text(re.findall(r"<td[^>]*>(.*?)</td>", r2, re.S)[0]), ins_li[0])
            self.assertIn(f'href="{MATSNE}"', r2)
            self.assertIn(f'<a class="btn-pink" href="{href}">{H.escape(btn, quote=False)}</a>', r2)
            # все статьи — по строке, ни одна не пропущена
            self.assertEqual(len(data), len(d["arts"]) + 1,
                             f"{lang}: строк {len(data)}, статей {len(d['arts'])} + страховка; без строки: "
                             + ", ".join(sorted(x["slug"] for x in d["arts"] if NEW + rel(x) not in mores)))

    def _more(self, lang, r):
        m = re.search(r'<td class="more"><a href="([^"]+)"', r)
        return urllib.parse.urljoin(self.d[lang]["url"], m.group(1)) if m else None

    def test_rows_verbatim_with_source(self):
        bad = []
        for lang, d in self.each():
            sec, trs = self.rows(lang)
            data = [r for c, r in trs if c != ' class="g"']
            for r in data:
                src = re.search(r'<td class="src"><a href="(https?://[^"]+)"', r)
                if not src:
                    bad.append(f"{lang}: строка без источника: {text(r)[:60]}")
            for r in [x for i, x in enumerate(data) if i != 1]:
                more = re.search(r'<td class="more"><a href="([^"]+)"', r)
                u = urllib.parse.urljoin(d["url"], more.group(1)) if more else ""
                p = next((x for x in d["arts"] if NEW + rel(x) == u), None)
                if not p:
                    bad.append(f"{lang}: «Подробно» не на статью: {u}"); continue
                f = d["fm"][p["slug"]]
                if text(re.search(r'<th scope="row">(.*?)</th>', r).group(1)) != text(f.get("crumb", "")):
                    bad.append(f"{lang}/{p['slug']}: «что» ≠ crumb")
                ah = (ROOT / rel(p) / "index.html").read_text(encoding="utf-8")
                box = re.search(r'<aside class="box facts">(.*?)</aside>', ah, re.S).group(1)
                lis = re.findall(r"<li>(.*?)</li>", box, re.S)
                if f.get("home_fact"):
                    k = int(f["home_fact"]) - 1
                else:
                    k = next((i for i, li in enumerate(lis) if '<sup class="fn"' in li), None)
                if k is None:
                    bad.append(f"{lang}/{p['slug']}: в «Коротко» нет пункта со сноской"); continue
                answer = text(re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)[0])
                if answer != text(lis[k]):
                    bad.append(f"{lang}/{p['slug']}: ответ не дословно пункт {k + 1} «Коротко»")
                n = re.search(r'<sup class="fn"[^>]*><a href="#src-(\d+)"', lis[k]).group(1)
                li = re.search(rf'<li id="src-{n}">(.*?)</li>', ah, re.S).group(1)
                want = H.unescape(re.search(r'<a href="([^"]+)"', li).group(1))
                got = re.search(r'<td class="src"><a href="([^"]+)"', r)
                if not got or H.unescape(got.group(1)) != want:
                    bad.append(f"{lang}/{p['slug']}: источник {got and got.group(1)} ≠ сноска [{n}] {want}")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_sources_last(self):
        for lang, d in self.each():
            h = d["h"]
            self.assertLess(h.find('<h2 id="faq"'), h.find('<h2 id="sources"'), lang)
            self.assertGreater(h.find('<h2 id="sources"'), max(m.start() for m in re.finditer(r"<h2", h)) - 1, lang)

    def test_json_ld(self):
        for lang, d in self.each():
            lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', d["h"], re.S)]
            types = [x.get("@type") for x in lds]
            for t in ("CollectionPage", "FAQPage", "BreadcrumbList"):
                self.assertIn(t, types, lang)
            self.assertNotIn("Article", types, lang)
            cp = next(x for x in lds if x["@type"] == "CollectionPage")
            self.assertEqual(cp["url"], d["url"])
            self.assertEqual(cp["inLanguage"], lang)
            self.assertEqual(cp["name"], d["hfm"]["title"])
            self.assertEqual(cp["about"]["@type"], "Country")
            self.assertEqual(cp["about"]["name"], "Грузия" if lang == "ru" else "Georgia")
            self.assertIn("https://www.wikidata.org/wiki/Q230", cp["about"]["sameAs"])
            self.assertEqual(cp["publisher"]["@id"], "https://tourist.100doc.ge/#organization")
            il = cp["mainEntity"]
            self.assertEqual(il["@type"], "ItemList")
            self.assertEqual(il["numberOfItems"], len(d["arts"]))
            self.assertEqual(sorted(i["url"] for i in il["itemListElement"]), sorted(NEW + rel(x) for x in d["arts"]))
            faq = next(x for x in lds if x["@type"] == "FAQPage")
            self.assertEqual(len(faq["mainEntity"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=1)
