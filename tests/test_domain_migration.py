"""Переезд на guide.100doc.ge (владелец 22.11.2026).

- build/site.json: base = https://guide.100doc.ge/; в корне файл CNAME с guide.100doc.ge;
- старого адреса icebreaker4561.github.io нет нигде: страницы, исходники, sitemap, robots, llms.txt, сборщик;
- canonical, og:url, hreflang, sitemap — на новом адресе, пути прежние (en в корне, ru в /ru/);
- robots.txt: User-agent: * Allow, отдельные группы Allow для поисковых и ИИ-роботов, Sitemap на новом адресе;
- llms.txt в корне: короткое описание, затем по каждому языку все статьи строкой «- [title](url): card_desc».
Запуск: python3 -m pytest -q tests/test_domain_migration.py
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
NEW = "https://guide.100doc.ge/"
OLD = "icebreaker4561"
BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "ClaudeBot", "Claude-SearchBot", "Google-Extended",
        "Googlebot", "YandexBot", "Bingbot"]


def rel(p):
    r = (p["slug"] if p["lang"] == "en" else ("ru/" + p["slug"] if p["slug"] else "ru"))
    return r + "/" if r else ""


def unq(v):
    """Кавычки вокруг значения в шапке исходника — не часть значения (так читает и сборщик)."""
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def front(p):
    t = (ROOT / p["src"]).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    return {k.strip(): unq(v.strip()) for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}


class Domain(unittest.TestCase):
    def test_base_and_cname(self):
        self.assertEqual(SITE["base"], NEW)
        self.assertEqual((ROOT / "CNAME").read_text(encoding="utf-8").strip(), "guide.100doc.ge")

    def test_no_old_domain(self):
        files = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)
        files += sorted((ROOT / "content").rglob("*.md"))
        files += [ROOT / x for x in ("sitemap.xml", "robots.txt", "llms.txt", "build/build.py", "build/site.json")]
        bad = [str(f.relative_to(ROOT)) for f in files if OLD in f.read_text(encoding="utf-8")]
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_canonical_og_hreflang(self):
        bad = []
        for p in SITE["pages"]:
            h = (ROOT / rel(p) / "index.html").read_text(encoding="utf-8")
            u = NEW + rel(p)
            if f'<link rel="canonical" href="{u}">' not in h:
                bad.append(f"{rel(p)}: canonical")
            if f'<meta property="og:url" content="{u}">' not in h:
                bad.append(f"{rel(p)}: og:url")
            for href in re.findall(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)">', h):
                if not href.startswith(NEW):
                    bad.append(f"{rel(p)}: hreflang {href}")
            if not re.search(r'hreflang="x-default" href="' + re.escape(NEW), h) and p.get("pair") in [q.get("pair") for q in SITE["pages"] if q is not p]:
                bad.append(f"{rel(p)}: нет x-default")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_sitemap(self):
        sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        locs = re.findall(r"<loc>([^<]+)</loc>", sm)
        self.assertEqual(sorted(locs), sorted(NEW + rel(p) for p in SITE["pages"]))

    def test_robots(self):
        r = (ROOT / "robots.txt").read_text(encoding="utf-8")
        groups = {}
        for block in re.split(r"\n\s*\n", r.strip()):
            agents = re.findall(r"(?im)^User-agent:\s*(\S+)", block)
            for a in agents:
                groups[a] = block
        self.assertIn("*", groups)
        self.assertRegex(groups["*"], r"(?m)^Allow: /$")
        for b in BOTS:
            self.assertIn(b, groups, f"нет группы {b}")
            self.assertRegex(groups[b], r"(?m)^Allow: /$", b)
            self.assertNotRegex(groups[b], r"(?m)^Disallow: /\s*$", b)
        self.assertIn(f"Sitemap: {NEW}sitemap.xml", r)

    def test_llms_txt(self):
        t = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(t.startswith("# "), "llms.txt начинается с заголовка")
        self.assertRegex(t, r"(?m)^> .{40,}", "нет короткого описания")
        for lang, head in (("en", "## English"), ("ru", "## Русский")):
            self.assertIn(head, t)
            part = t.split(head, 1)[1].split("\n## ", 1)[0]
            arts = [p for p in SITE["pages"] if p["lang"] == lang and p["slug"]]
            lines = re.findall(r"(?m)^- \[(.+?)\]\((\S+)\): (.+)$", part)
            self.assertEqual(len(lines), len(arts), lang)
            by_url = {u: (t_, d) for t_, u, d in lines}
            for p in arts:
                fm = front(p)
                self.assertIn(NEW + rel(p), by_url, f"llms.txt без {rel(p)}")
                self.assertEqual(by_url[NEW + rel(p)], (fm["title"], fm["card_desc"]), rel(p))


if __name__ == "__main__":
    unittest.main(verbosity=1)
