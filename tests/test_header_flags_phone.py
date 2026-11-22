"""Владелец 22.11.2026: «надо из шапки на мобиле номер телефона убрать, а селектор языков сделать флажками».

Проверяет все собранные страницы:
- в шапке выбор языка — компактный, выпадающий вниз (владелец 22.11.2026: «селектор языков сделай компактным,
  выпадающим вниз!»): details.langs, в summary — флажок текущего языка (SVG) и стрелка, aria-label с названием языка;
  в выпадающем списке — ссылка a.lang на другой язык (hreflang, флажок SVG и название языка); работает без скрипта;
  вне списка слов «English» / «Русский» в шапке нет;
- ссылка-флажок ведёт туда же, куда вёл прежний переключатель: на пару статьи, иначе на главную другого языка;
- на телефоне (до 767 px) номер телефона в шапке скрыт, на компьютере виден.

Запуск: python3 tests/test_header_flags_phone.py
"""
import json
import pathlib
import re
import sys
import unittest
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
BASE = SITE["base"]
NAME = {"ru": "Русский", "en": "English"}


def rel(p):
    if p["slug"] == "":
        return "" if p["lang"] == "en" else "ru/"
    return (p["slug"] if p["lang"] == "en" else "ru/" + p["slug"]) + "/"


class FlagsPhone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [(p, (ROOT / rel(p) / "index.html").read_text(encoding="utf-8")) for p in SITE["pages"]]
        cls.css = (ROOT / "assets" / "guide.css").read_text(encoding="utf-8")

    def test_flags(self):
        bad = []
        for p, h in self.pages:
            key = p["lang"] + ":" + p["slug"]
            hdr = re.search(r'<header class="top">.*?</header>', h, re.S)
            hdr = hdr.group(0) if hdr else ""
            m = re.search(r'<details class="langs">\s*<summary aria-label="([^"]+)"[^>]*>(.*?)</summary>(.*?)</details>', hdr, re.S)
            if not m:
                bad.append(f"{key}: нет выпадающего выбора языка details.langs"); continue
            slabel, summ, menu = m.groups()
            other = "en" if p["lang"] == "ru" else "ru"
            if NAME[p["lang"]] not in slabel or "<svg" not in summ or re.sub(r"<[^>]+>", "", summ).strip() not in ("", "▾"):
                bad.append(f"{key}: в кнопке выбора языка не флажок текущего языка: «{summ[:80]}»")
            a = re.search(r'<a class="lang" href="([^"]+)" hreflang="(\w+)" lang="\w+"[^>]*>(.*?)</a>', menu, re.S)
            if not a:
                bad.append(f"{key}: нет ссылки на другой язык в списке"); continue
            href, hl, body = a.groups()
            if hl != other or "<svg" not in body or NAME[other] not in re.sub(r"<[^>]+>", "", body):
                bad.append(f"{key}: пункт списка hreflang={hl} «{re.sub(r'<[^>]+>', '', body).strip()}»")
            pair = next((q for q in SITE["pages"] if p.get("pair") and q.get("pair") == p.get("pair") and q["lang"] == other), None)
            target = pair or next(q for q in SITE["pages"] if q["lang"] == other and q["slug"] == "")
            if urllib.parse.urljoin(BASE + rel(p), href) != BASE + rel(target):
                bad.append(f"{key}: флажок ведёт на {href}")
            if re.search(r">\s*(English|Русский)\s*<", hdr.replace(menu, "")):
                bad.append(f"{key}: в шапке осталось слово-переключатель")
        self.assertEqual(bad, [], "\n".join(bad[:20]))

    def test_phone_hidden_on_mobile(self):
        self.assertRegex(self.css, r"@media\s*\(max-width:\s*767px\)\s*\{[^@]*\.hdr-phone\s*\{[^}]*display:\s*none")
        for p, h in self.pages[:3]:
            self.assertIn('class="hdr-phone"', h, "на компьютере телефон в шапке должен остаться")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
