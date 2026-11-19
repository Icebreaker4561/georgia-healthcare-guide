"""Владелец 19.11.2026: «в начале каждой статьи должен быть блок … «Прочитать статью с помощью AI». У нас уже такая штука
реализована в статьях на 100doc.ge. Ничего не придумывай, сделай так, как сделано там. Просто стилизуй под этот гайд».

Стандарт статьи, раздел 6а; общий модуль ~/SEO_Vasiliy/tools/ai_read.py — тот же, что у 100doc.ge.
Проверки по каждой статье путеводителя (главные страницы — не статьи):
- один блок section#ai-read, в начале: после строки автора и до блока «Коротко», оглавления и текста статьи;
- кнопки ChatGPT, Claude, Perplexity — вопрос в ссылке; Gemini (и Алиса — только на русских) — копируют вопрос;
  «Копировать вопрос»; тексты окошка — в data-атрибутах; скрипт модуля на странице;
- вопрос (data-prompt): адрес и H1 этой статьи, название путеводителя, «5 пунктах / 5 bullets»; про 100doc.ge — ни слова;
- текст вопроса на странице не виден (только в атрибуте);
- стиль — путеводителя: токены --paper/--line/--teal, без синих цветов 100doc.ge.

Запуск: python3 tests/test_ai_read_block.py
"""
import html
import json
import pathlib
import re
import sys
import unittest
import urllib.parse as U

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "build" / "site.json").read_text(encoding="utf-8"))
NAME = {"ru": "Путеводитель по Грузии", "en": "Georgia Travel Guide"}


def articles():
    for p in SITE["pages"]:
        if not p["slug"]:
            continue
        rel = ("ru/" if p["lang"] == "ru" else "") + p["slug"] + "/"
        yield p, rel, (ROOT / rel / "index.html").read_text(encoding="utf-8")


class AiRead(unittest.TestCase):
    def test_block_on_every_article(self):
        bad, n = [], 0
        for p, rel, h in articles():
            n += 1
            lang = p["lang"]
            if h.count('id="ai-read"') != 1:
                bad.append(f"{rel}: блоков {h.count('id=\"ai-read\"')}")
                continue
            i = h.index('id="ai-read"')
            meta = h.find('<p class="meta">')
            for later in ('<aside class="box facts">', '<nav class="toc"', '<article class="body">'):
                j = h.find(later)
                if j >= 0 and j < i:
                    bad.append(f"{rel}: блок ниже, чем {later}")
            if not (0 <= meta < i):
                bad.append(f"{rel}: блок выше строки автора")
            sec = re.search(r'<section class="ai-read" id="ai-read"[^>]*>.*?</section>', h, re.S).group(0)
            prompt = html.unescape(re.search(r'data-prompt="([^"]*)"', sec).group(1))
            url = SITE["base"] + rel
            h1 = html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", h, re.S).group(1))).strip()
            if url not in prompt or h1 not in prompt or NAME[lang] not in prompt or "100doc" in prompt:
                bad.append(f"{rel}: вопрос без адреса/H1/названия путеводителя или с 100doc: {prompt[:120]}")
            if not re.search(r"5 (пунктах|bullets)", prompt):
                bad.append(f"{rel}: в вопросе нет «5 пунктах»")
            for k, base in (("chatgpt", "https://chatgpt.com/?q="), ("claude", "https://claude.ai/new?q="),
                            ("perplexity", "https://www.perplexity.ai/search?q=")):
                m = re.search(rf'<a class="ai-read-{k}" data-ai="{k}" href="([^"]+)"', sec)
                if not m or U.unquote(html.unescape(m.group(1))[len(base):]) != prompt:
                    bad.append(f"{rel}: кнопка {k} не несёт вопрос")
            if 'data-ai="gemini" data-ai-copyfirst' not in sec:
                bad.append(f"{rel}: нет Gemini с копированием")
            if ('data-ai="alice"' in sec) != (lang == "ru"):
                bad.append(f"{rel}: Алиса должна быть только на русских")
            if "data-ai-copy " not in sec and "data-ai-copy>" not in sec:
                bad.append(f"{rel}: нет «Копировать вопрос»")
            for a in ("data-dlg-title", "data-dlg-text", "data-dlg-open", "data-dlg-fail", "data-dlg-close"):
                if a not in sec:
                    bad.append(f"{rel}: нет {a}")
            if "getElementById('ai-read')" not in h or "showModal" not in h:
                bad.append(f"{rel}: нет скрипта блока")
            visible = re.sub(r'<script.*?</script>|<style.*?</style>', " ", h, flags=re.S)
            visible = html.unescape(re.sub(r'"[^"]*"', '""', re.sub(r"<[^>]+>", " ", re.sub(r"<[^>]+>", lambda m: re.sub(r'"[^"]*"', '""', m.group(0)), visible))))
            if prompt.split("\n")[-1][:60] in visible:
                bad.append(f"{rel}: текст вопроса виден на странице")
        self.assertGreater(n, 40)
        self.assertEqual(bad, [], "\n".join(bad[:30]))

    def test_no_block_on_home(self):
        for rel in ("index.html", "ru/index.html"):
            self.assertNotIn('id="ai-read"', (ROOT / rel).read_text(encoding="utf-8"), rel)

    def test_guide_style(self):
        css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
        m = re.search(r"/\* Прочитать с ИИ.*", css, re.S)
        self.assertTrue(m, "в style.css нет раздела «Прочитать с ИИ»")
        part = m.group(0)
        for tok in ("var(--paper", "var(--line", "var(--teal"):
            self.assertIn(tok, part)
        for blue in ("#2b52e8", "#eef2ff", "#dbe3f5", "999px"):
            self.assertNotIn(blue, part, f"цвет/форма 100doc.ge {blue}")
        h = (ROOT / "batumi" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("#2b52e8", h, "в страницу попал стиль 100doc.ge")


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
