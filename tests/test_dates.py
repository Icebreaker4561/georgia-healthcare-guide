"""Владелец 19.11.2026: «надо писать для повышения доверия поисковиков дату создания [и] обновления статьи …
в стандарте это есть» (blog-article-standard.md, раздел 2 п. 5 и раздел 3: строка автора с датой публикации и
«обновлено <дата>»; article:published_time / article:modified_time совпадают с датами в тексте и в Schema).

Проверки по каждой собранной странице:
- в строке автора (p.meta) — «Опубликовано <дата>» и «Обновлено <дата>» (en: Published / Updated) в <time datetime>;
- те же даты в JSON-LD (datePublished / dateModified) и в метатегах article:published_time / article:modified_time;
- дата публикации не позже даты обновления; обе — из исходника (published / updated);
- в sitemap.xml lastmod страницы = дате обновления.

Запуск: python3 tests/test_dates.py
"""
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
LABEL = {"ru": ("Опубликовано", "Обновлено"), "en": ("Published", "Updated")}


def front(md):
    m = re.match(r"---\n(.*?)\n---\n", md, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*?)\s*$", m.group(1), re.M))


class Dates(unittest.TestCase):
    def test_dates_everywhere_and_equal(self):
        sitemap = dict(re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", (ROOT / "sitemap.xml").read_text()))
        bad, n = [], 0
        for page in SITE["pages"]:
            fm = front((ROOT / page["src"]).read_text(encoding="utf-8"))
            pub, upd = fm.get("published"), fm.get("updated")
            rel = (page["lang"] == "ru" and "ru/" or "") + (page["slug"] + "/" if page["slug"] else "")
            h = (ROOT / rel / "index.html").read_text(encoding="utf-8")
            n += 1
            name = rel or "/"
            if not pub or not upd or pub > upd:
                bad.append(f"{name}: в исходнике published={pub} updated={upd}")
                continue
            meta = re.search(r'<p class="meta">(.*?)</p>', h, re.S)
            meta = meta.group(1) if meta else ""
            lp, lu = LABEL[page["lang"]]
            if not re.search(rf'{lp} <time datetime="{pub}">', meta):
                bad.append(f"{name}: в строке автора нет «{lp} <time datetime={pub}>»")
            if not re.search(rf'{lu} <time datetime="{upd}">', meta):
                bad.append(f"{name}: в строке автора нет «{lu} <time datetime={upd}>»")
            if f'<meta property="article:published_time" content="{pub}">' not in h:
                bad.append(f"{name}: нет article:published_time={pub}")
            if f'<meta property="article:modified_time" content="{upd}">' not in h:
                bad.append(f"{name}: нет article:modified_time={upd}")
            lds = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
            arts = [d for d in lds if d.get("datePublished")]
            if not arts or any(d["datePublished"] != pub or d.get("dateModified") != upd for d in arts):
                bad.append(f"{name}: JSON-LD даты не совпадают с {pub}/{upd}")
            if sitemap.get(BASE + rel) != upd:
                bad.append(f"{name}: sitemap lastmod {sitemap.get(BASE + rel)} ≠ {upd}")
        self.assertEqual(n, len(SITE["pages"]))
        self.assertEqual(bad, [], f"{len(bad)} проблем:\n" + "\n".join(bad[:40]))


    def test_text_check_date_equals_updated(self):
        """«Проверено 18 ноября 2026» в тексте статьи = дате обновления (разные даты в разных местах обнуляют доверие)."""
        M = {"января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6, "июля": 7, "августа": 8, "сентября": 9,
             "октября": 10, "ноября": 11, "декабря": 12, "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
             "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
        bad = []
        for page in SITE["pages"]:
            md = (ROOT / page["src"]).read_text(encoding="utf-8")
            upd = front(md).get("updated")
            for d, m, y in re.findall(r"(?:Проверено|[Cc]hecked on|[Rr]eviewed on)\s+(\d{1,2})\s+([А-Яа-яA-Za-z]+)\s+(\d{4})", md):
                iso = f"{y}-{M.get(m, 0):02d}-{int(d):02d}"
                if iso != upd:
                    bad.append(f"{page['src']}: в тексте {iso}, обновлено {upd}")
        self.assertEqual(bad, [], "\n".join(bad))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
