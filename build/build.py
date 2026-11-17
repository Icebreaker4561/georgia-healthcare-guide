"""Сборщик микросайта georgia-healthcare-guide: content/<lang>/<slug>.md → <slug>/index.html (en), ru/<slug>/index.html (ru),
sitemap.xml, robots.txt. Без внешних зависимостей.

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

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
CSS = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
CSS = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
CSS = re.sub(r"\s*\n\s*", "", CSS)

UI = {
    "en": {"home": "Guide", "contents": "On this page", "reviewed": "Reviewed", "min": "min read",
           "related": "More practical guides", "faq": "Frequently asked questions", "lang_other": "Русский",
           "about": "An independent practical guide to healthcare in Georgia (the country) for visitors and expats, "
                    "prepared by the team behind 100doc.ge, a directory of doctors and clinics in Georgia.",
           "disclaimer": "General information, not medical or legal advice. Rules change: check the official sources before you travel.",
           "skip": "Skip to content", "menu": "Guides", "sources": "Sources"},
    "ru": {"home": "Справочник", "contents": "Содержание", "reviewed": "Проверено", "min": "мин чтения",
           "related": "Ещё по теме", "faq": "Частые вопросы", "lang_other": "English",
           "about": "Независимый практический справочник о медицине в Грузии для туристов и тех, кто здесь живёт. "
                    "Подготовлен командой 100doc.ge — каталога врачей и клиник Грузии.",
           "disclaimer": "Это справочная информация, а не медицинская или юридическая консультация. Правила меняются: перед поездкой сверьтесь с официальными источниками.",
           "skip": "К тексту", "menu": "Разделы", "sources": "Источники"},
}
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
    return f'<figure class="fig">{body}{capt}</figure>'


def parse_md(text, page):
    meta, body = {}, text
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
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
            faq.append((q, " ".join(re.sub(r"<[^>]+>", "", x) for x in parts)))
            faq_html.append(f'<details class="qa"><summary>{inline(q)}</summary><div class="a">{"".join(parts)}</div></details>')
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
    return meta, "\n".join(out), toc, faq


def render_block(b, section):
    lines = b.splitlines()
    first = lines[0]
    if first.startswith("<"):
        return b
    if first.startswith("> [!"):
        km = re.match(r"> \[!(\w+)\]\s*(.*)", first)
        kind, title = km.group(1), km.group(2)
        inner = "\n".join(l[2:] if l.startswith("> ") else l.lstrip(">") for l in lines[1:])
        inner_html = "".join(render_block(x, section) for x in re.split(r"\n\s*\n", inner) if x.strip())
        head = f'<p class="box-h">{inline(title)}</p>' if title else ""
        return f'<aside class="box {kind}">{head}{inner_html}</aside>'
    if first.startswith("> "):
        inner = " ".join(l[2:] for l in lines)
        return f"<blockquote><p>{inline(inner)}</p></blockquote>"
    if first.startswith("| "):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|[\s\-:|]+\|$", l.strip())]
        head, data = rows[0], rows[1:]
        th = "".join(f"<th scope=\"col\">{inline(c)}</th>" for c in head)
        tr = "".join("<tr>" + "".join(f"<td data-label=\"{esc(re.sub(r'[*]', '', head[i]))}\">{inline(c)}</td>" for i, c in enumerate(r)) + "</tr>" for r in data)
        return f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
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
        tag = "ol" if ordered else "ul"
        cls = ' class="sources"' if section == "sources" else ""
        return f"<{tag}{cls}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>"
    return f"<p>{inline(' '.join(l.strip() for l in lines))}</p>"


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
    lang_switch = (f'<a class="lang" href="{pre}{out_rel(lang_link)[:-len("index.html")] or "./"}" hreflang="{lang_link["lang"]}" '
                   f'lang="{lang_link["lang"]}">{ui["lang_other"]}</a>') if lang_link else ""
    # меню
    nav = "".join(f'<li><a href="{pre}{out_rel(p)[:-len("index.html")]}"'
                  f'{" aria-current=\"page\"" if p is page else ""}>{esc(p["nav"])}</a></li>'
                  for p in pages_same if p.get("nav") and p["slug"] != "")
    # хлебные крошки
    crumbs_ld = [{"@type": "ListItem", "position": 1, "name": ui["home"], "item": url(home)}]
    crumbs = ""
    if not is_home:
        crumbs_ld.append({"@type": "ListItem", "position": 2, "name": meta.get("crumb", meta["h1"]), "item": url(page)})
        crumbs = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="{pre}{out_rel(home)[:-len("index.html")] or "./"}">'
                  f'{ui["home"]}</a><span aria-hidden="true">›</span><span>{esc(meta.get("crumb", meta["h1"]))}</span></nav>')
    # содержание
    toc_items = [(i, t) for i, t in toc if i not in ("sources",)]
    toc_html = ""
    if len(toc_items) >= 3:
        toc_html = (f'<nav class="toc" aria-label="{ui["contents"]}"><p class="toc-h">{ui["contents"]}</p><ol>'
                    + "".join(f'<li><a href="#{i}">{inline(t)}</a></li>' for i, t in toc_items) + "</ol></nav>")
    # похожие
    related = [p for p in pages_same if p["slug"] and p is not page][:6 if is_home else 3]
    rel_html = ""
    if related:
        cards = "".join(f'<a class="card" href="{pre}{out_rel(p)[:-len("index.html")]}"><span class="card-k">{esc(p.get("kicker", ""))}</span>'
                        f'<span class="card-t">{esc(p["card"])}</span><span class="card-d">{esc(p.get("card_desc", ""))}</span></a>'
                        for p in related)
        rel_title = ui["menu"] if is_home else ui["related"]
        rel_html = f'<section class="related" aria-labelledby="related"><h2 id="related">{rel_title}</h2><div class="cards">{cards}</div></section>'
    # разметка
    ld = [{
        "@context": "https://schema.org", "@type": "Article", "headline": meta["h1"], "description": meta["description"],
        "inLanguage": lang, "datePublished": meta.get("published", meta["updated"]), "dateModified": meta["updated"],
        "mainEntityOfPage": url(page),
        "author": {"@type": "Organization", "name": "100doc.ge editorial team", "url": "https://100doc.ge/en/"},
        "publisher": {"@type": "Organization", "name": "100doc.ge", "url": "https://100doc.ge/en/"},
    }, {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs_ld}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    og_img = meta.get("og")
    og_img_html = f'<meta property="og:image" content="{BASE}assets/img/{page["key"]}/{og_img}">' if og_img else ""
    # Выноска «главное» в начале текста — над содержанием: читатель видит ответ раньше списка разделов.
    first_box = ""
    if body.startswith('<aside class="box facts">'):
        cut = body.index("</aside>") + len("</aside>")
        first_box, body = body[:cut], body[cut:]
    toc_html = first_box + toc_html
    lead = f'<p class="lead">{inline(meta["lead"])}</p>' if meta.get("lead") else ""
    kicker = f'<p class="kicker">{esc(meta["kicker"])}</p>' if meta.get("kicker") else ""
    reviewed = f'{ui["reviewed"]} {fmt_date(meta["updated"], lang)} · {minutes} {ui["min"]}'
    footer_links = "".join(f'<li><a href="{pre}{out_rel(p)[:-len("index.html")] or "./"}">{esc(p.get("nav") or ui["home"])}</a></li>'
                           for p in pages_same if p.get("nav") or p["slug"] == "")
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(meta["title"])}</title>
<meta name="description" content="{esc(meta["description"])}">
<link rel="canonical" href="{url(page)}">
{hreflang}<meta property="og:type" content="article"><meta property="og:title" content="{esc(meta["title"])}"><meta property="og:description" content="{esc(meta["description"])}"><meta property="og:url" content="{url(page)}">{og_img_html}
<meta name="theme-color" content="#0f6b5e">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%230f6b5e'/%3E%3Cpath d='M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z' fill='%23fff'/%3E%3C/svg%3E">
<style>{CSS}</style>
{ld_html}
</head>
<body>
<a class="skip" href="#main">{ui["skip"]}</a>
<header class="top"><div class="wrap top-in">
<a class="brand" href="{pre}{out_rel(home)[:-len("index.html")] or "./"}"><span class="mark" aria-hidden="true"></span>{esc(SITE["name"] if lang == "en" else SITE.get("name_ru", SITE["name"]))}</a>
{lang_switch}
</div>{f'<nav class="menu wrap" aria-label="{ui["menu"]}"><ul>{nav}</ul></nav>' if nav else ""}</header>
<div class="hero"><div class="wrap">{crumbs}{kicker}<h1>{inline(meta["h1"])}</h1>{lead}<p class="meta">{reviewed}</p></div></div>
<main id="main" class="wrap">
{toc_html}
<article class="body">
{body}
</article>
{rel_html}
</main>
<footer class="foot"><div class="wrap">
<p>{ui["about"]}</p>
<ul class="foot-links">{footer_links}</ul>
<p class="small">{ui["disclaimer"]}</p>
</div></footer>
</body>
</html>
"""


def main():
    built = []
    for page in SITE["pages"]:
        page.setdefault("key", page["slug"] or "home")
        src = ROOT / page["src"]
        meta, body, toc, faq = parse_md(src.read_text(encoding="utf-8"), page)
        for k in ("nav", "card", "card_desc", "kicker"):
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
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print("собрано:", len(built))


if __name__ == "__main__":
    main()
