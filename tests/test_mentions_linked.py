"""Владелец 19.11.2026: «Если статья ссылается на какой-то раздел, должна быть ссылка. Проверь, чтобы не было
каких-то упоминаний без ссылок» (пример: «клиники собраны в каталоге из раздела «Где врач»» — без ссылки).

Проверяет все собранные страницы: в предложении, где текст отсылает к разделу, каталогу, отдельной статье
или нашему путеводителю, должна стоять ссылка (<a href>) — на якорь раздела, на статью или на каталог.

Запуск: python3 tests/test_mentions_linked.py
"""
import html
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = sorted(p for p in ROOT.rglob("index.html") if ".git" not in p.parts)

MENTION = re.compile(
    r"(?i)(раздел[аеу]?\s+«|в разделе\s|из раздела\s|см\.\s|выше в разделе|ниже в разделе|в каталоге|каталог[аеу]? из"
    r"|в отдельн(ом|ой) (материал|статье|путеводител)|в нашем (путеводител|материал|справочник)|в нашей статье"
    r"|отдельн(ый|ая) (путеводитель|статья|материал)|о н[её]м у нас есть|рассказываем в"
    r"|see (the|our) .{0,40}section|in the section|our (guide|article) (to|on|about)|separate (guide|article)|in our directory)"
)


def sentences(block):
    # делим блок на предложения, сохраняя разметку внутри
    return re.split(r"(?<=[.!?])\s+(?=[А-ЯA-Z«\"(])", block)


class MentionsLinked(unittest.TestCase):
    def test_mentions_have_links(self):
        bad = []
        for p in PAGES:
            h = p.read_text(encoding="utf-8")
            art = re.search(r'<article class="body">(.*?)</article>', h, re.S)
            if not art:
                continue
            body = re.split(r'<h2 id="sources"', art.group(1))[0]
            body = re.sub(r"<figure.*?</figure>", " ", body, flags=re.S)
            for blk in re.findall(r"<(p|li|dd|summary|td)[^>]*>(.*?)</\1>", body, re.S):
                for s in sentences(blk[1]):
                    text = html.unescape(re.sub(r"<[^>]+>", "", s))
                    if MENTION.search(text) and "<a " not in s:
                        bad.append(f"{p.relative_to(ROOT)}: «{text.strip()[:140]}»")
        self.assertEqual(bad, [], f"{len(bad)} упоминаний без ссылки:\n" + "\n".join(bad[:40]))


if __name__ == "__main__":
    res = unittest.main(exit=False, verbosity=1).result
    sys.exit(0 if res.wasSuccessful() else 1)
