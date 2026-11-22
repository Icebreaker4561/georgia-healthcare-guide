"""Сборщик путеводителя guide.100doc.ge: content/<lang>/<slug>.md → <slug>/index.html (en), ru/<slug>/index.html (ru),
sitemap.xml, robots.txt, llms.txt. Без внешних зависимостей. Оформление — как у блога 100doc.ge (владелец 22.11.2026).

    python3 build/build.py

Формат исходника — шапка «ключ: значение» между строками --- и упрощённая разметка:
## Заголовок {#id}, ### Подзаголовок, абзацы, списки «- » и «1. », таблицы «| », цитата «> »,
выноски «> [!note]» и «> [!facts] Заголовок», картинка <!-- схема: img/файл.webp | alt | подпись -->,
сырые HTML-строки (начинаются с «<»). Раздел с id faq: каждый ### — вопрос (<details>), разметка FAQPage
собирается из тех же вопросов. Раздел с id sources — список источников мелким шрифтом.
"""
import datetime
import html
import json
import pathlib
import re
import sys
import urllib.parse

# «Прочитать с ИИ» — тот же модуль, что у статей 100doc.ge (стандарт, раздел 6а; владелец 19.11.2026)
sys.path.insert(0, str(pathlib.Path.home() / "SEO_Vasiliy" / "tools"))
import ai_read  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]


def squeeze(css):
    """Сжатие CSS: без комментариев и переводов строк (тест test_design сжимает шаблон блога так же)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s*\n\s*", "", css).strip()


# Оформление 1:1 как у блога 100doc.ge (владелец 22.11.2026, вариант А «Да, под шаблон блога»): CSS и куски разметки
# берутся из самого шаблона блога и его сборщика, а не переписываются руками.
BLOG_TPL = (pathlib.Path.home() / "SEO_Vasiliy" / "standards" / "blog-template.html").read_text(encoding="utf-8")
BLOG_BUILD = (pathlib.Path.home() / "SEO_Vasiliy" / "tools" / "blog_article_build.py").read_text(encoding="utf-8")
BLOG_CSS = re.search(r"<style>(.*?)</style>", BLOG_TPL, re.S).group(1)
# Б1 (владелец 22.11.2026): без правил логотипа страховщика в шапке. Класс картинки страховщика берём из разметки шапки
# шаблона (картинка после разделителя hdr-divider), чтобы не писать название страховщика в сборщике; вырезаем её правила,
# правила разделителя и опустевший @media. Точный перечень вырезанного проверяет tests/test_design.py.
_INS = re.search(r'<span class="hdr-divider"[^>]*></span>\s*<img class="([\w-]+)"', BLOG_TPL).group(1)
for _sel in (rf"\.{_INS}, \.hdr-divider", rf"\.{_INS}", r"\.hdr-divider"):
    BLOG_CSS = re.sub(rf" ?{_sel} \{{[^}}]*\}}", "", BLOG_CSS)
BLOG_CSS = re.sub(r"@media \([^)]*\) \{\s*\}\n?", "", BLOG_CSS)
BLOG_EXTRA_CSS = re.search(r'EXTRA_CSS = """(.*?)"""', BLOG_BUILD, re.S).group(1)
BLOG_ANCHOR_JS = re.search(r'ANCHOR_JS = r"""(.*?)"""', BLOG_BUILD, re.S).group(1)
CSS = "".join(squeeze(x) for x in (BLOG_CSS, BLOG_EXTRA_CSS, ai_read.CSS,
                                    (ROOT / "build" / "blog-cf.css").read_text(encoding="utf-8"),
                                    (ROOT / "build" / "style.css").read_text(encoding="utf-8")))


def tpl_part(rx):
    """Кусок разметки шаблона блога одной строкой (переводы строк и отступы — убраны)."""
    return re.sub(r">\s*\n\s*<", "><", re.search(rx, BLOG_TPL, re.S).group(0)).replace("\n", " ")


TPL_LAW_ICON = re.search(r'<div class="law-strip">\s*<p>(<svg .*?</svg>)', BLOG_TPL, re.S).group(1)
TPL_PHONE = tpl_part(r'<a class="hdr-phone".*?</a>')
TPL_SHARE = tpl_part(r'<section class="share".*?</section>')
TPL_RATE = tpl_part(r'<section class="page-rate".*?</section>')
TPL_RATE_JS = re.search(r"ОЦЕНКА СТРАНИЦЫ: поведение ═══ -->\s*<script>(.*?)</script>", BLOG_TPL, re.S).group(1)
# английские подписи — как на английских статьях блога (https://100doc.ge/en/blog/car-accident-in-georgia/)
TPL_EN = [("Позвонить: ", "Call: "), (">Поделиться<", ">Share<"), (">ВКонтакте<", ">VK<"),
          (">Была ли страница полезной?<", ">Was this helpful?<"), ("Да</button>", "Yes</button>"),
          ("Нет</button>", "No</button>"), (">Спасибо за ответ!<", ">Thank you for your feedback!<")]

UI = {
    "en": {"home": "Georgia Travel Guide", "contents": "Contents", "author": "Author", "reviewed": "Reviewed", "published": "Published", "updated": "Updated", "min": "min read",
           "related": "Related articles", "faq": "Frequently asked questions", "lang_other": "Русский",
           "about": "Georgia Travel Guide — a practical 100doc.ge guide to trips, holidays and healthcare in Georgia (the country) for visitors and expats.",
           "disclaimer": "General information, not medical or legal advice. Rules change: check the official sources before you travel.",
           "skip": "Skip to content", "menu": "Guides", "sources": "Sources"},
    "ru": {"home": "Путеводитель по Грузии", "contents": "Содержание", "author": "Автор", "reviewed": "Проверено", "published": "Опубликовано", "updated": "Обновлено", "min": "мин чтения",
           "related": "Похожие материалы", "faq": "Частые вопросы", "lang_other": "English",
           "about": "Путеводитель по Грузии — практический гид 100doc.ge по поездкам, отдыху и медицине в Грузии для туристов и тех, кто здесь живёт.",
           "disclaimer": "Это справочная информация, а не медицинская или юридическая консультация. Правила меняются: перед поездкой сверьтесь с официальными источниками.",
           "skip": "К тексту", "menu": "Разделы", "sources": "Источники"},
}
# Меню из трёх разделов (владелец 20.11.2026, вариант А). Раздел и регион — в шапке исходника статьи:
# section: health | places | practical; у мест region; статья о здоровье с region — ещё и среди мест (nav_place).
SECTIONS = ["health", "places", "practical"]
SEC_LABEL = {"ru": {"health": "Здоровье и безопасность", "places": "Куда поехать", "practical": "Дорога и быт"},
             "en": {"health": "Health & safety", "places": "Places", "practical": "Getting around"}}
REGIONS = ["tbilisi", "mountains", "west", "south-east"]
REGION_LABEL = {"ru": {"tbilisi": "Тбилиси и рядом", "mountains": "Горы", "west": "Запад и море", "south-east": "Юг и восток"},
                "en": {"tbilisi": "Tbilisi and around", "mountains": "Mountains", "west": "West and the coast",
                       "south-east": "South and east"}}
MENU_BTN = {"ru": "Меню", "en": "Menu"}
# Меню работает без скрипта (details/summary + флажок). Скрипт только удобство: клик мимо и Esc закрывают раздел.
MENU_JS = ("document.addEventListener('click',function(e){document.querySelectorAll('details.msec[open]').forEach(function(d){"
           "if(!d.contains(e.target))d.removeAttribute('open')})});document.addEventListener('keydown',function(e){"
           "if(e.key==='Escape'){var d=document.querySelector('details.msec[open]');if(d){d.removeAttribute('open');"
           "d.querySelector('summary').focus()}}});")
# Автор и издатель — как в разметке блога 100doc.ge (владелец 22.11.2026; псевдоним снят). Тексты и @id скопированы
# из JSON-LD статей блога: ru https://100doc.ge/ru/blog/chto-delat-pri-dtp-v-gruzii/, en https://100doc.ge/en/blog/car-accident-in-georgia/
AUTHOR = {"en": "Alex Polansky", "ru": "Алекс Полански"}
JOB = {"en": "Founder and CEO of 100doc.ge", "ru": "Основатель и руководитель 100doc.ge"}
ABOUT = {"en": "https://tourist.100doc.ge/en/about", "ru": "https://tourist.100doc.ge/about"}
PERSON = {
    "ru": {"@type": "Person", "@id": "https://tourist.100doc.ge/about#person", "name": "Alex Polansky",
           "alternateName": "Алекс Полански", "jobTitle": JOB["ru"], "image": "https://tourist.100doc.ge/img/founder-320.webp",
           "url": ABOUT["ru"]},
    "en": {"@type": "Person", "@id": "https://tourist.100doc.ge/en/about#person", "name": "Alex Polansky",
           "jobTitle": JOB["en"], "image": "https://tourist.100doc.ge/img/founder-320.webp", "url": ABOUT["en"]},
}
ORG = {"@type": "Organization", "@id": "https://tourist.100doc.ge/#organization", "name": "100doc.ge",
       "url": "https://tourist.100doc.ge/",
       "logo": {"@type": "ImageObject", "url": "https://tourist.100doc.ge/logo.png", "width": 360, "height": 100},
       "sameAs": ["https://www.trustpilot.com/review/tourist.100doc.ge"]}
# Жёлтая полоса под шапкой на каждой странице (владелец 22.11.2026)
STRIP = {"ru": ("https://100doc.ge/tourist/", "С 1 января 2026 года страховка обязательна при въезде в Грузию"),
         "en": ("https://100doc.ge/tourist/en", "Since 1 January 2026, insurance is mandatory to enter Georgia")}
# Главная по макетам migration/home-mockup-{ru,en}.html (владелец 22.11.2026)
HOME = {
    "ru": {"lead": "Путеводитель 100doc.ge", "glance": "Грузия коротко: главное из каждой статьи",
           "cols": ("Что", "Ответ", "Источник", "Подробно"), "ins": "Страховка для въезда",
           "buy": ("https://100doc.ge/tourist/", "Оформить полис для въезда на 100doc.ge →"),
           "checked": "Проверено", "chips_label": "Разделы", "faq_chip": "Частые вопросы", "sos_chip": "Скорая — 112",
           "tcap": "Путеводитель 100doc.ge. Таблица собирается из статей сама: каждая новая статья добавляет свою строку. "
                   "Ответ — дословно из блока «Коротко» статьи, источник — первоисточник этого факта.",
           "trust": "каждый факт со ссылкой на первоисточник", "trust_checked": "проверено"},
    "en": {"lead": "The 100doc.ge Georgia Travel Guide", "glance": "Georgia at a glance: the key fact from every article",
           "cols": ("Topic", "Answer", "Source", "Read more"), "ins": "Entry insurance",
           "buy": ("https://100doc.ge/tourist/en", "Get Georgia entry insurance on 100doc.ge →"),
           "checked": "Checked", "chips_label": "Sections", "faq_chip": "FAQ", "sos_chip": "Emergency — 112",
           "tcap": "100doc.ge Georgia Travel Guide. This table is built from the articles: each new article adds its own row. "
                   "Each answer is quoted from the article's key facts; the source is the official source for that fact.",
           "trust": "every fact linked to its official source", "trust_checked": "checked"},
}
# Подписи блоков блога. Тексты — со статей блога (ru «Что делать при ДТП в Грузии», en «Car accident in Georgia»);
# био автора без названия страховщика (в блоге оно есть — у нас его быть не должно): en — вторая фраза био блога,
# ru — её перевод. Строка под шапкой — hdr-tagline шаблона блога.
BLOG_UI = {
    "ru": {"tagline": "Страховка, которая действительно работает в Грузии", "about_author": "Об авторе",
           "more": "Подробнее об авторе", "photo_alt": "Алекс Полански, основатель и руководитель 100doc.ge",
           "bio": "Мы сверяем статьи путеводителя с официальными текстами на matsne.gov.ge и сайтах госорганов Грузии.",
           "all_articles": "Статьи путеводителя",
           "eco": '<li><a href="https://100doc.ge/ru/">Отзывы о врачах</a></li><li><a href="https://100doc.ge/ru/blog/">Блог</a></li>'},
    "en": {"tagline": "Insurance that actually works in Georgia", "about_author": "About the author",
           "more": "More about the author", "photo_alt": "Alex Polansky, founder of 100doc.ge",
           "bio": "We check our guides against the official texts on matsne.gov.ge and Georgian government websites.",
           "all_articles": "Guide articles",
           "eco": '<li><a href="https://100doc.ge/en/">Doctor reviews</a></li><li><a href="https://100doc.ge/en/blog/">Blog</a></li>'},
}
PIN112 = {"ru": "112-v-gruzii", "en": "ambulance-georgia"}
MATSNE = "https://matsne.gov.ge/ka/document/view/6728816"
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot", "Claude-SearchBot", "Google-Extended",
           "Googlebot", "YandexBot", "Bingbot"]
SKIPPED = []  # статьи без пункта «Коротко» со сноской — строки в таблице главной нет (печатается при сборке)
AI_SITE = {"en": "Georgia Travel Guide", "ru": "сайте «Путеводитель по Грузии»"}
GUIDE_NAME = {"en": "Georgia Travel Guide", "ru": "Путеводитель по Грузии"}
MONTHS = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December"],
          "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
                 "ноября", "декабря"]}


def esc(s):
    return html.escape(s, quote=True)


def out_rel(p):
    if p["slug"] == "":
        return "index.html" if p["lang"] == "en" else "ru/index.html"
    return (p["slug"] if p["lang"] == "en" else "ru/" + p["slug"]) + "/index.html"


def url(p):
    r = out_rel(p)
    return BASE + r[: -len("index.html")]


def depth_prefix(p):
    return "../" * out_rel(p).count("/")


def slugify(s):
    s = re.sub(r"<[^>]+>", "", s).lower()
    s = re.sub(r"[^a-z0-9а-яё]+", "-", s).strip("-")
    return s[:60] or "s"


def inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)

    def link(m):
        text, href = m.group(1), html.unescape(m.group(2))
        attrs = f' href="{esc(href)}"'
        if href.startswith("http") and not href.startswith(BASE):
            attrs += ' rel="noopener"'
        return f"<a{attrs}>{text}</a>"

    # Сноски в стиле Википедии (владелец 19.11.2026): [^N] — номер источника в разделе «Источники»
    s = re.sub(r"\s*\[\^(\d+)\]", r'<sup class="fn"><a href="#src-\1" data-n="\1" aria-label="[\1]"></a></sup>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = s.replace(" -- ", " – ").replace("~", "&nbsp;")
    return s


def figure(spec, page):
    path, alt, cap = [x.strip() for x in (spec.split("|") + ["", ""])[:3]]
    name = pathlib.Path(path).name
    stem, ext = name.rsplit(".", 1)
    rel_dir = f"assets/img/{page['key']}/"
    src = depth_prefix(page) + rel_dir + name
    disk = ROOT / rel_dir / name
    w, h = 1280, 720
    try:
        from PIL import Image
        w, h = Image.open(disk).size
    except Exception:
        pass
    two_x = ROOT / rel_dir / f"{stem}@2x.{ext}"
    mob = ROOT / rel_dir / f"{stem}-mob.{ext}"
    srcset = f' srcset="{src} 1x, {depth_prefix(page) + rel_dir + two_x.name} 2x"' if two_x.exists() else ""
    mob_src = f'<source media="(max-width: 600px)" srcset="{depth_prefix(page) + rel_dir + mob.name}">' if mob.exists() else ""
    img = f'<img src="{src}"{srcset} alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
    body = f"<picture>{mob_src}{img}</picture>" if mob_src else img
    capt = f"<figcaption>{inline(cap)}</figcaption>" if cap else ""
    cls = "fig sq" if abs(w / h - 1) <= 0.03 else "fig"  # класс ровно «fig»/«fig sq» (тесты статей); вид — .art-figure блога
    return f'<figure class="{cls}">{body}{capt}</figure>'


def parse_md(text, page):
    meta, body = {}, text
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                meta[k.strip()] = v
        body = text[m.end():]
    out, toc, faq = [], [], []
    section = None
    blocks = re.split(r"\n\s*\n", body.strip())
    in_faq_item = None
    faq_html = []

    def close_faq_item():
        nonlocal in_faq_item
        if in_faq_item is not None:
            q, parts = in_faq_item
            faq.append((html.unescape(q), html.unescape(" ".join(re.sub(r"<[^>]+>", "", re.sub(r'<sup class="fn">.*?</sup>', "", x)) for x in parts)).replace("\xa0", " ")))
            # на главной вопрос — H3 внутри summary (макет владельца 22.11.2026); в статьях — как было
            sq = f"<h3>{inline(q)}</h3>" if page["slug"] == "" else inline(q)
            faq_html.append(f'<details class="qa"><summary>{sq}</summary><div class="a"><div class="faq-a">{"".join(parts)}</div></div></details>')
            in_faq_item = None

    def emit(h):
        if section == "faq" and in_faq_item is not None:
            in_faq_item[1].append(h)
        elif section == "faq":
            faq_html.append(h)
        else:
            out.append(h)

    for b in blocks:
        b = b.rstrip()
        first = b.splitlines()[0]
        if first.startswith("<!-- схема:"):
            emit(figure(re.match(r"<!--\s*схема:(.*?)-->", b, re.S).group(1), page))
            continue
        if first.startswith("<!--"):
            continue
        hm = re.match(r"(#{2,3}) (.+?)(?:\s*\{#([\w-]+)\})?$", first)
        if hm:
            level, title, hid = len(hm.group(1)), hm.group(2), hm.group(3)
            rest = "\n".join(b.splitlines()[1:]).strip()
            if level == 2:
                close_faq_item()
                if section == "faq":
                    out.append("".join(faq_html) + "</section>")
                    faq_html.clear()
                hid = hid or slugify(title)
                section = hid
                toc.append((hid, re.sub(r"\*", "", title)))
                if hid == "faq":
                    out.append(f'<section class="faq" aria-labelledby="faq"><h2 id="faq">{inline(title)}</h2>')
                else:
                    cls = ' class="sources-h"' if hid == "sources" else ""
                    out.append(f'<h2 id="{hid}"{cls}>{inline(title)}</h2>')
            else:
                if section == "faq":
                    close_faq_item()
                    in_faq_item = (title, [])
                else:
                    out.append(f'<h3 id="{hid or slugify(title)}">{inline(title)}</h3>')
            if rest:
                blocks_rest = rest
                emit(render_block(blocks_rest, section))
            continue
        emit(render_block(b, section))
    close_faq_item()
    if section == "faq":
        out.append("".join(faq_html) + "</section>")
    body_html = "\n".join(out)
    for n in dict.fromkeys(re.findall(r'<sup class="fn"><a href="#src-(\d+)"', body_html)):
        # якорь ↑ — у первой сноски в тексте статьи; блок «Коротко» выводится над статьёй, его пропускаем
        fx = re.search(r'<aside class="box facts">.*?</aside>', body_html, re.S)
        cut = fx.end() if fx and f'<sup class="fn"><a href="#src-{n}"' in body_html[fx.end():] else 0
        body_html = body_html[:cut] + body_html[cut:].replace(f'<sup class="fn"><a href="#src-{n}"', f'<sup class="fn" id="ref-{n}"><a href="#src-{n}"', 1)
        back = "к тексту" if meta.get("lang", "") == "ru" or re.search("[а-я]", meta.get("h1", "")) else "back to text"
        body_html = re.sub(rf'(<li id="src-{n}">.*?)(</li>)', rf'\1 <a class="fn-back" href="#ref-{n}" aria-label="{back}">↑</a>\2', body_html, count=1, flags=re.S)
    return meta, body_html, toc, faq


def render_block(b, section):
    lines = b.splitlines()
    first = lines[0]
    if first.startswith("<"):
        return b
    if first.startswith("> [!"):
        km = re.match(r"> \[!(\w+)\]\s*(.*)", first)
        kind, title = km.group(1), km.group(2)
        inner = "\n".join(l[2:] if l.startswith("> ") else l.lstrip(">") for l in lines[1:])
        if kind == "stats":
            cells = []
            for l in inner.splitlines():
                mm = re.match(r"\s*- ([^:]+):\s*(.+)", l)
                if mm:
                    cells.append(f"<div><dt>{inline(mm.group(1).strip())}</dt><dd>{re.sub(r'(?<=\d) (?=\S)', '&nbsp;', inline(mm.group(2).strip()))}</dd></div>")
            return f'<dl class="stats">{"".join(cells)}</dl>'
        inner_html = "".join(render_block(x, section) for x in re.split(r"\n\s*\n", inner) if x.strip())
        head = f'<p class="box-h eyebrow">{inline(title)}</p>' if title else ""
        return f'<aside class="box {kind}">{head}{inner_html}</aside>'
    if first.startswith("> "):
        inner = " ".join(l[2:] for l in lines)
        return f"<blockquote><p>{inline(inner)}</p></blockquote>"
    if first.startswith("| "):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|[\s\-:|]+\|$", l.strip())]
        head, data = rows[0], rows[1:]
        th = "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in head)
        tr = "".join("<tr>" + "".join(f"<td data-label=\"{esc(re.sub(r'[*]', '', head[i]))}\">{inline(c)}</td>" for i, c in enumerate(r)) + "</tr>" for r in data)
        # Числовая таблица (все ячейки, кроме первой колонки, до 6 знаков) остаётся сеткой на телефоне — tests/test_compact_table.py
        num = all(len(re.sub(r"[*~]", "", c)) <= 6 for r in data for c in r[1:])
        # div.tbl и голый <table> — для тестов статей; вид — .table-wrap/.data-table блога (правила в style.css, «.tbl table»)
        wide = " tbl-wide" if len(head) >= 4 else ""
        return (f'<div class="tbl{" num" if num else " table-wrap scroll-x" + wide}"><table>'
                f'<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
    if re.match(r"^(- |\d+\. )", first):
        ordered = bool(re.match(r"\d+\. ", first))
        items, cur = [], None
        for l in lines:
            mm = re.match(r"^(?:- |\d+\. )(.*)", l)
            if mm:
                if cur is not None:
                    items.append(cur)
                cur = mm.group(1)
            else:
                cur += " " + l.strip()
        items.append(cur)
        if section == "sources":
            return '<ol class="sources">' + "".join(f'<li id="src-{n}">{inline(i)}</li>' for n, i in enumerate(items, 1)) + "</ol>"
        tag = "ol" if ordered else "ul"
        return f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>"
    return f"<p>{inline(' '.join(l.strip() for l in lines))}</p>"


def members(lang, sec):
    """Статьи раздела на языке lang. Среди мест — ещё статьи других разделов с region; места — по регионам,
    внутри региона первым идёт город, давший региону имя (Тбилиси)."""
    arts = [p for p in SITE["pages"] if p["lang"] == lang and p["slug"]]
    if sec != "places":   # order в шапке статьи: меньше — выше (скорая и 112 — первой, владелец 20.11.2026)
        return sorted((p for p in arts if p.get("section") == sec), key=lambda p: int(p.get("order", 50)))
    res = [p for p in arts if p.get("region")]
    return sorted(res, key=lambda p: (REGIONS.index(p["region"]),
                                      0 if REGION_LABEL[lang][p["region"]].startswith(p.get("nav", "~")) else 1,
                                      SITE["pages"].index(p)))


def place_label(p):
    return p.get("nav_place") if p.get("section") != "places" and p.get("nav_place") else p.get("nav") or p["card"]


def menu_html(page, pre):
    lang = page["lang"]

    def link(p, label):
        cur = ' aria-current="page"' if p is page else ""
        return f'<li><a href="{pre}{out_rel(p)[:-len("index.html")]}"{cur}>{esc(label)}</a></li>'

    parts = []
    for s in SECTIONS:
        ms = members(lang, s)
        if s == "places":
            cols = []
            for r in REGIONS:
                rs = [p for p in ms if p["region"] == r]
                if rs:
                    cols.append(f'<div class="mcol"><p class="mreg">{esc(REGION_LABEL[lang][r])}</p><ul>'
                                + "".join(link(p, place_label(p)) for p in rs) + "</ul></div>")
            inner = f'<div class="mpanel mplaces">{"".join(cols)}</div>'
        else:
            inner = f'<div class="mpanel"><ul>{"".join(link(p, p.get("nav") or p["card"]) for p in ms)}</ul></div>'
        parts.append(f'<details class="msec" name="menu" data-sec="{s}"><summary>{esc(SEC_LABEL[lang][s])}</summary>{inner}</details>')
    return (f'<nav class="menu" aria-label="{UI[lang]["menu"]}"><div class="wrap mbar">{"".join(parts)}</div></nav>')


def tx(s):
    """Текст для узла HTML (кавычки не трогаем — в атрибуты не идёт)."""
    return html.escape(s, quote=False)


def href_to(p, pre):
    return f'{pre}{out_rel(p)[:-len("index.html")]}' or "./"


def img_size(path):
    try:
        from PIL import Image
        return Image.open(path).size
    except Exception:
        return 1280, 720


def thumb(p, pre, meta):
    """Миниатюра карточки — картинка og статьи."""
    og = meta.get("og")
    if not og or not (ROOT / "assets" / "img" / p["key"] / og).exists():
        return ""
    w, h = img_size(ROOT / "assets" / "img" / p["key"] / og)
    return (f'<img src="{pre}assets/img/{p["key"]}/{og}" alt="{esc(p["card"])}" width="{w}" height="{h}" '
            f'loading="lazy" decoding="async">')


def hub_card(p, pre):
    meta = p["_parsed"][0]
    lang = p["lang"]
    return (f'<a class="card" href="{href_to(p, pre)}">{thumb(p, pre, meta)}<div class="ct"><h3>{tx(p["card"])}</h3>'
            f'<p class="card-d">{tx(p.get("card_desc", ""))}</p>'
            f'<p class="card-dt">{HOME[lang]["checked"]} {fmt_date(meta["updated"], lang)}</p></div></a>')


def hubs_html(page, pre):
    """Главная: H2 на раздел, карточки с H3; у мест регионы — подписи, не заголовки (макет 22.11.2026)."""
    lang = page["lang"]
    out = []
    for s in ["places", "health", "practical"]:
        ms = members(lang, s)
        if s == "places":
            body = "".join(f'<p class="grp">{tx(REGION_LABEL[lang][r])}</p><div class="cards">'
                           + "".join(hub_card(p, pre) for p in ms if p["region"] == r) + "</div>"
                           for r in REGIONS if any(p["region"] == r for p in ms))
        else:
            body = f'<div class="cards">{"".join(hub_card(p, pre) for p in ms)}</div>'
        out.append(f'<section class="hub" id="{s}" aria-labelledby="h-{s}"><h2 id="h-{s}">{tx(SEC_LABEL[lang][s])} '
                   f'<span class="n">{len(ms)}</span></h2>{body}</section>')
    return "".join(out)


def md_parts(page):
    """Сырые пункты «Коротко» и адреса источников (сноска [^n] = n-й пункт списка под «## Источники» / «## Sources»)."""
    text = (ROOT / page["src"]).read_text(encoding="utf-8")
    m = re.search(r"^> \[!facts\][^\n]*\n((?:>.*\n?)+)", text, re.M)
    bullets = [l[4:] for l in m.group(1).splitlines() if l.startswith("> - ")] if m else []
    srcs = []
    sm = re.search(r"^## (?:Источники|Sources)\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if sm:
        for line in sm.group(1).splitlines():
            if re.match(r"^(- |\d+\. )", line):
                u = re.search(r"\]\((https?://[^)\s]+)\)", line)
                srcs.append(html.unescape(u.group(1)) if u else "")
    return bullets, srcs


def no_fn(s):
    return re.sub(r"\s*\[\^\d+\]", "", s)


def host(u):
    return re.sub(r"^https?://(www\.)?", "", u).split("/")[0]


def glance_html(page, pre, home_bullets):
    """Таблица «Грузия коротко»: строка на каждую статью языка; 1-я — 112, 2-я — страховка для въезда (макет 22.11.2026)."""
    lang = page["lang"]
    hm = HOME[lang]
    arts = [p for p in SITE["pages"] if p["lang"] == lang and p["slug"]]

    def row(label, answer, src, more, cls=""):
        c = f' class="{cls}"' if cls else ""
        return (f'<tr{c}><th scope="row">{tx(label)}</th><td>{answer}</td><td class="src"><a href="{esc(src)}" rel="noopener">'
                f'{tx(host(src))}</a></td><td class="more">{more}</td></tr>')

    def art_row(p):
        meta = p["_parsed"][0]
        bullets, srcs = md_parts(p)
        if meta.get("home_fact"):
            k = int(meta["home_fact"]) - 1
        else:
            k = next((i for i, b in enumerate(bullets) if re.search(r"\[\^\d+\]", b)), None)
        fn = re.findall(r"\[\^(\d+)\]", bullets[k]) if k is not None and k < len(bullets) else []
        src = srcs[int(fn[0]) - 1] if fn and int(fn[0]) <= len(srcs) else ""
        if not src:
            SKIPPED.append(f"{lang}/{p['slug']}")
            return ""
        return row(meta.get("crumb", p["card"]), inline(no_fn(bullets[k])), src,
                   f'<a href="{href_to(p, pre)}">{tx(p["card"])}</a>')

    rows = []
    pin = next(p for p in arts if p["slug"] == PIN112[lang])
    rows.append(art_row(pin))
    ins = next(b for b in home_bullets if re.search(r"30[~,]000", b))
    rows.append(row(hm["ins"], inline(no_fn(ins)), MATSNE, f'<a class="btn-pink" href="{hm["buy"][0]}">{tx(hm["buy"][1])}</a>', "pin"))
    groups = [("health", None, SEC_LABEL[lang]["health"]), ("practical", None, SEC_LABEL[lang]["practical"])] + \
             [("places", r, f'{SEC_LABEL[lang]["places"]} · {REGION_LABEL[lang][r]}') for r in REGIONS]
    for sec, reg, label in groups:
        items = [p for p in members(lang, sec) if p.get("section") == sec and (reg is None or p.get("region") == reg) and p is not pin]
        if not items:
            continue
        rows.append(f'<tr class="g"><td colspan="4">{tx(label)}</td></tr>')
        rows.extend(art_row(p) for p in items)
    rows = [r for r in rows if r]
    n = sum(1 for r in rows if not r.startswith('<tr class="g">'))
    th = "".join(f'<th scope="col">{c}</th>' for c in hm["cols"])
    return (f'<section class="glance" id="glance" aria-labelledby="glance-h"><h2 id="glance-h">{tx(hm["glance"])} '
            f'<span class="n">{n}</span></h2><div class="tbl glance-tbl"><table><thead><tr>{th}</tr></thead><tbody>'
            f'{"".join(rows)}</tbody></table></div><p class="tcap">{tx(hm["tcap"])}</p></section>')


def plural_ru(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    return few if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else many


def fmt_date(d, lang):
    y, m, dd = map(int, d.split("-"))
    return f"{dd} {MONTHS[lang][m - 1]} {y}"


def page_html(page, meta, body, toc, faq):
    lang = page["lang"]
    ui = UI[lang]
    pre = depth_prefix(page)
    pages_same = [p for p in SITE["pages"] if p["lang"] == lang]
    home = next(p for p in pages_same if p["slug"] == "")
    is_home = page["slug"] == ""
    arts = [p for p in pages_same if p["slug"]]
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    minutes = max(2, round(words / 220))
    # переводы
    pair = page.get("pair")
    alts = [p for p in SITE["pages"] if pair and p.get("pair") == pair]
    hreflang = ""
    if len(alts) > 1:
        en = next((p for p in alts if p["lang"] == "en"), alts[0])
        hreflang = "".join(f'<link rel="alternate" hreflang="{p["lang"]}" href="{url(p)}">' for p in alts)
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{url(en)}">'
    other = next((p for p in alts if p["lang"] != lang), None)
    other_home = next((p for p in SITE["pages"] if p["lang"] != lang and p["slug"] == ""), None)
    lang_link = other or other_home
    lang_switch = (f'<a class="lang" href="{href_to(lang_link, pre)}" hreflang="{lang_link["lang"]}" '
                   f'lang="{lang_link["lang"]}">{ui["lang_other"]}</a>') if lang_link else ""
    nav = menu_html(page, pre)
    home_href = href_to(home, pre)
    # хлебные крошки: Путеводитель по Грузии › Раздел (блок главной) › Статья
    crumbs_ld = [{"@type": "ListItem", "position": 1, "name": ui["home"], "item": url(home)}]
    crumbs = ""
    if not is_home:
        sec = page["section"]
        crumbs_ld.append({"@type": "ListItem", "position": 2, "name": SEC_LABEL[lang][sec], "item": url(home) + "#" + sec})
        crumbs_ld.append({"@type": "ListItem", "position": 3, "name": meta.get("crumb", meta["h1"]), "item": url(page)})
        crumbs = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="{home_href}">{ui["home"]}</a><span aria-hidden="true">›</span>'
                  f'<a href="{home_href}#{sec}">{esc(SEC_LABEL[lang][sec])}</a><span aria-hidden="true">›</span>'
                  f'<span>{esc(meta.get("crumb", meta["h1"]))}</span></nav>')
    # содержание: справа на компьютере (nav.toc блога), свёрнутое над текстом на телефоне (details.toc-m)
    toc_items = [(i, t) for i, t in toc if i not in ("sources",)]
    toc_html = toc_m = ""
    if len(toc_items) >= 3 and not is_home:
        items = "".join(f'<li><a href="#{i}">{inline(t)}</a></li>' for i, t in toc_items)
        toc_html = (f'<nav class="toc" aria-labelledby="toc-title"><p class="toc-title" id="toc-title">{ui["contents"]}</p>'
                    f'<ol>{items}</ol></nav>')
        toc_m = f'<details class="toc-m"><summary>{ui["contents"]}</summary><ol>{items}</ol></details>'
    # «Похожие материалы» — тот же раздел, сначала тот же регион; карточки — card-link блога
    related = []
    if not is_home:
        same = [p for p in members(lang, page["section"]) if p is not page]
        related = sorted(same, key=lambda p: 0 if page.get("region") and p.get("region") == page.get("region") else 1)[:3]
    rel_html = ""
    if related:
        cards = "".join(f'<a class="card" href="{href_to(p, pre)}"><span class="card-label">{tx(SEC_LABEL[lang][p["section"]])}</span>'
                        f'<span class="card-title">{tx(p["card"])}</span></a>' for p in related)
        rel_html = (f'<section class="related" aria-labelledby="related"><h2 id="related">{ui["related"]}</h2>'
                    f'<div class="related-grid">{cards}</div></section>')
    # разметка
    pub, upd = meta.get("published", meta["updated"]), meta["updated"]
    og_img = meta.get("og")
    og_url = f'{BASE}assets/img/{page["key"]}/{og_img}' if og_img else ""
    if is_home:
        main_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url(page) + "#page", "url": url(page),
                   "name": meta["title"], "description": meta["description"], "inLanguage": lang,
                   "datePublished": pub, "dateModified": upd,
                   "about": {"@type": "Country", "name": "Грузия" if lang == "ru" else "Georgia",
                             "sameAs": ["https://www.wikidata.org/wiki/Q230"]},
                   "publisher": ORG,
                   "mainEntity": {"@type": "ItemList", "numberOfItems": len(arts), "itemListElement": [
                       {"@type": "ListItem", "position": i + 1, "url": url(p), "name": p["card"]} for i, p in enumerate(arts)]}}
    else:
        main_ld = {"@context": "https://schema.org", "@type": "Article", "headline": meta["h1"], "description": meta["description"],
                   "inLanguage": lang, "datePublished": pub, "dateModified": upd, "mainEntityOfPage": url(page),
                   "author": PERSON[lang], "publisher": ORG}
        if og_url:
            main_ld["image"] = og_url
    ld = [main_ld, {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs_ld}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    og_img_html = f'<meta property="og:image" content="{og_url}">' if og_url else ""
    # «Коротко» — над текстом
    first_box = ""
    h1_plain = html.unescape(re.sub(r"<[^>]+>", "", inline(meta["h1"])))
    ai_box = ai_read.block(lang, url(page), h1_plain, site=AI_SITE[lang]).replace("\n", "&#10;") if page["slug"] else ""
    if body.startswith('<aside class="box facts">'):
        cut = body.index("</aside>") + len("</aside>")
        first_box, body = body[:cut], body[cut:]
    kicker = f'<p class="kicker">{esc(meta["kicker"])}</p>' if meta.get("kicker") and not is_home else ""
    dates = (f'{ui["published"]} <time datetime="{pub}">{fmt_date(pub, lang)}</time>'
             f' · {ui["updated"]} <time datetime="{upd}">{fmt_date(upd, lang)}</time>')
    logo_img = (f'<img class="hdr-logo" src="{pre}assets/img/logo-100doc-guide-1x.webp" srcset="{pre}assets/img/logo-100doc-guide-1x.webp 1x, '
                f'{pre}assets/img/logo-100doc-guide.webp 2x" width="190" height="28" alt="100doc.ge Guide">')
    bl = BLOG_UI[lang]
    if is_home:
        hm = HOME[lang]
        lead_txt = meta["lead"][0].lower() + meta["lead"][1:] if lang == "ru" else meta["lead"]
        lead = (f'<p class="lead"><strong>{hm["lead"]}</strong> — {inline(lead_txt)}</p>' if lang == "ru" else
                f'<p class="lead"><strong>{hm["lead"]}</strong> covers places to go, getting around and staying safe. {inline(lead_txt)}</p>')
        n = len(arts)
        cnt = f"{n} {plural_ru(n, 'статья', 'статьи', 'статей')}" if lang == "ru" else f"{n} articles"
        trust = (f'<p class="trust">100doc.ge · {cnt} · {hm["trust"]} · {hm["trust_checked"]} '
                 f'<time datetime="{upd}">{fmt_date(upd, lang)}</time></p>')
        chips = (f'<nav class="chips" aria-label="{hm["chips_label"]}">'
                 + "".join(f'<a class="chip" href="#{s}">{tx(SEC_LABEL[lang][s])}</a>' for s in ("places", "health", "practical"))
                 + f'<a class="chip" href="#faq">{hm["faq_chip"]}</a><a class="chip" href="#emergency">{hm["sos_chip"]}</a></nav>')
        head = f'<h1>{inline(meta["h1"])}</h1>{lead}{trust}<div class="byline"><p class="meta">{dates}</p></div>{chips}'
        home_bullets = re.findall(r"^> - (.*)$", (ROOT / page["src"]).read_text(encoding="utf-8"), re.M)
        main_html = (f'<div class="hero"><div class="wrap"><header class="art-head">{head}</header></div></div>\n'
                     f'<div class="art-main">{first_box}{glance_html(page, pre, home_bullets)}{hubs_html(page, pre)}'
                     f'<div class="art-body"><article class="body home-body">\n{body}\n</article></div></div>')
    else:
        lead = f'<p class="lead">{inline(meta["lead"])}</p>' if meta.get("lead") else ""
        byline = (f'<div class="byline"><a class="byline-author" href="{ABOUT[lang]}">'
                  f'<img class="byline-photo" src="{pre}assets/img/founder-320.webp" width="44" height="44" alt="{AUTHOR[lang]}" decoding="async">'
                  f'<span class="byline-who"><span class="byline-name">{AUTHOR[lang]}</span><span class="byline-role">{JOB[lang]}</span></span></a>'
                  f'<p class="meta">{dates} · {minutes} {ui["min"]}</p></div>')
        head = f'{crumbs}{kicker}<h1>{inline(meta["h1"])}</h1>{lead}{byline}'
        lead_box = f'<div class="lead-box">{ai_box}{first_box}{toc_m}</div>' if (ai_box or first_box or toc_m) else ""
        share = TPL_SHARE.replace("{{SHARE_URL_ENC}}", urllib.parse.quote(url(page), safe="")).replace(
            "{{SHARE_TEXT_ENC}}", urllib.parse.quote(h1_plain, safe=""))
        rate = TPL_RATE
        if lang == "en":
            for a, b in TPL_EN:
                share, rate = share.replace(a, b), rate.replace(a, b)
        bio = (f'<aside class="author-bio" aria-labelledby="author-bio-title"><img class="author-photo" src="{pre}assets/img/founder-320.webp" '
               f'width="80" height="80" alt="{bl["photo_alt"]}" loading="lazy" decoding="async"><div class="author-body">'
               f'<p class="author-label" id="author-bio-title">{bl["about_author"]}</p><p class="author-name">{AUTHOR[lang]}</p>'
               f'<p class="author-role">{JOB[lang]}</p><p class="author-text">{bl["bio"]}</p>'
               f'<a class="author-more" href="{ABOUT[lang]}">{bl["more"]}</a></div></aside>')
        # как в блоге: заголовок статьи (art-head) — в сетке .layout, оглавление справа вровень с ним
        main_html = (f'<div class="layout"><div class="hero"><div class="wrap"><header class="art-head">{head}</header></div></div>\n'
                     f'{lead_box}{f"<aside class=\"side\">{toc_html}</aside>" if toc_html else ""}\n'
                     f'<div class="art-main"><div class="art-body"><article class="body">\n{body}\n</article></div>\n'
                     f'{rate}{share}{bio}{rel_html}</div>\n</div>')
    footer_links = "".join(f'<li><a href="{href_to(p, pre)}">{esc(p.get("nav"))}</a></li>' for p in pages_same if p.get("nav"))
    sec_links = "".join(f'<li><a href="{home_href}#{s}">{tx(SEC_LABEL[lang][s])}</a></li>' for s in ("places", "health", "practical"))
    langs = "".join((f'<li><a href="{href_to(page, pre)}" aria-current="page" lang="{lang}">{lang.upper()}</a></li>' if L == lang else
                     f'<li><a href="{href_to(lang_link, pre)}" hreflang="{L}" lang="{L}">{L.upper()}</a></li>')
                    for L in ("ru", "en") if L == lang or lang_link)
    strip_href, strip_text = STRIP[lang]
    phone = TPL_PHONE if lang == "ru" else TPL_PHONE.replace("Позвонить: ", "Call: ")
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta["title"])}</title>
<meta name="description" content="{esc(meta["description"])}">
<link rel="canonical" href="{url(page)}">
{hreflang}<meta property="og:type" content="{"website" if is_home else "article"}"><meta property="og:title" content="{esc(meta["title"])}"><meta property="og:description" content="{esc(meta["description"])}"><meta property="og:url" content="{url(page)}"><meta property="og:site_name" content="100doc.ge"><meta property="article:published_time" content="{pub}"><meta property="article:modified_time" content="{upd}">{og_img_html}
<meta name="theme-color" content="#ffffff">
<meta name="msvalidate.01" content="30A00B524613BF5613542BB815C007B7">
<link rel="icon" href="https://tourist.100doc.ge/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" media="print" onload="this.media='all'" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;display=swap">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;display=swap"></noscript>
<link rel="stylesheet" href="{pre}assets/guide.css">
{ld_html}
</head>
<body>
<a class="skip" href="#main">{ui["skip"]}</a>
<header class="top"><div class="site-hdr"><input type="checkbox" id="mt" class="mt" aria-label="{MENU_BTN[lang]}"><div class="site-hdr-in">
<div class="site-hdr-left"><span class="hdr-logo-link"><a class="logo" href="{home_href}">{logo_img}</a></span></div>
<div class="site-hdr-right">{lang_switch.replace('class="lang"', 'class="lang"')}{phone}<label for="mt" class="mbtn">{MENU_BTN[lang]}</label></div>
</div>{nav}</div></header>
<a class="law-strip" href="{strip_href}"><p>{TPL_LAW_ICON}{strip_text}</p></a>
<main id="main" class="page{" home" if is_home else ""}">
{main_html}
</main>
<div class="disclaimer"><p>{ui["disclaimer"]}</p></div>
<footer class="foot"><div class="cf" data-common-footer><div class="cf-in">
<nav class="ftr-lp" aria-label="{bl["all_articles"]}"><h3>{bl["all_articles"]}</h3><ul>{footer_links}</ul></nav>
<div class="cf-cols"><div class="cf-brand"><img src="{pre}assets/img/logo-100doc-guide-1x.webp" srcset="{pre}assets/img/logo-100doc-guide-1x.webp 1x, {pre}assets/img/logo-100doc-guide.webp 2x" width="190" height="28" alt="100doc.ge Guide" loading="lazy" decoding="async"><p>{ui["about"]}</p></div>
<nav class="cf-col" aria-label="{ui["menu"]}"><h3>{ui["menu"]}</h3><ul>{sec_links}</ul></nav>
<nav class="cf-col" aria-label="100doc.ge"><h3>100doc.ge</h3><ul>{bl["eco"]}</ul></nav></div>
<div class="cf-bottom"><p>© 2026 100doc.ge · {GUIDE_NAME[lang]}</p><nav class="cf-langs" aria-label="Language"><ul>{langs}</ul></nav></div>
</div></div></footer>
{f"<script>{ai_read.JS}</script>" if ai_box else ""}
{f"<script>{TPL_RATE_JS}</script>" if not is_home else ""}
<script>{BLOG_ANCHOR_JS}</script>
<script>{MENU_JS}</script>
</body>
</html>
"""


def front_raw(page):
    m = re.match(r"---\n(.*?)\n---\n", (ROOT / page["src"]).read_text(encoding="utf-8"), re.S)
    return {k.strip(): v.strip().strip('"') for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}


def llms_txt():
    out = ["# Georgia Travel Guide — guide.100doc.ge", "",
           "> Practical guide by 100doc.ge to trips, holidays and healthcare in Georgia (the country): places to go, "
           "getting around, emergencies, entry insurance and doctors. Every fact links to its official source. "
           "English at the site root, Russian under /ru/.", ""]
    for lang, head in (("en", "## English"), ("ru", "## Русский")):
        out += [head, ""]
        for p in SITE["pages"]:
            if p["lang"] == lang and p["slug"]:
                meta = p["_parsed"][0]
                out.append(f'- [{meta["title"]}]({url(p)}): {meta.get("card_desc", "")}')
        out.append("")
    return "\n".join(out)


def robots_txt():
    groups = ["User-agent: *\nAllow: /"] + [f"User-agent: {b}\nAllow: /" for b in AI_BOTS]
    return "\n\n".join(groups) + f"\n\nSitemap: {BASE}sitemap.xml\n"


def main():
    built = []
    for page in SITE["pages"]:
        page.setdefault("key", page["slug"] or "home")
        src = ROOT / page["src"]
        meta, body, toc, faq = parse_md(src.read_text(encoding="utf-8"), page)
        for k in ("nav", "card", "card_desc", "kicker", "section", "region", "nav_place", "order"):
            if meta.get(k) and not page.get(k):
                page[k] = meta[k]
        page["_parsed"] = (meta, body, toc, faq)
    for page in SITE["pages"]:
        meta, body, toc, faq = page["_parsed"]
        out = ROOT / out_rel(page)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_html(page, meta, body, toc, faq), encoding="utf-8")
        built.append((url(page), meta["updated"]))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in built]
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(robots_txt(), encoding="utf-8")
    (ROOT / "llms.txt").write_text(llms_txt(), encoding="utf-8")
    (ROOT / "assets" / "guide.css").write_text(CSS + "\n", encoding="utf-8")  # А2: один общий файл стилей
    print("собрано:", len(built))
    if SKIPPED:
        print("нет строки в таблице главной (в «Коротко» нет пункта со сноской):", ", ".join(SKIPPED))


if __name__ == "__main__":
    main()
