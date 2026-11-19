"""Числовая таблица (все ячейки, кроме первой колонки, короткие — до 6 знаков) остаётся сеткой на телефоне: класс «tbl num»,
CSS не превращает её строки в карточки. Таблицы с текстом — по-старому карточками (19.11.2026, погода Батуми по месяцам:
12 карточек по 4 строки — 2 800 px прокрутки на 390 px)."""
import pathlib, re, subprocess, sys, unittest
from playwright.sync_api import sync_playwright
import http.server, threading, functools, socketserver

REPO = pathlib.Path(__file__).resolve().parent.parent


class CompactTable(unittest.TestCase):
    def test_classes(self):
        b = (REPO / "batumi" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<div class="tbl num">', b)
        k = (REPO / "kazbegi" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="tbl num"', k, "текстовая таблица Казбеги должна остаться карточками")

    def test_mobile_height(self):
        H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO))
        H.log_message = lambda *a: None
        class S(socketserver.TCPServer): allow_reuse_address = True
        srv = S(("127.0.0.1", 8792), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as p:
                br = p.chromium.launch(channel="chrome")
                pg = br.new_page(viewport={"width": 390, "height": 844})
                pg.goto("http://127.0.0.1:8792/batumi/"); pg.wait_for_timeout(800)
                h = pg.evaluate("document.querySelector('.tbl.num').getBoundingClientRect().height")
                w = pg.evaluate("document.documentElement.scrollWidth")
                br.close()
        finally:
            srv.shutdown()
        self.assertLess(h, 900, f"таблица {h}px на 390")
        self.assertEqual(w, 390, "прокрутка вбок")


if __name__ == "__main__":
    unittest.main()
