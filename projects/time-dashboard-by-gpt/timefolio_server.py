from __future__ import annotations

import json
import os
import re
import ssl
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))
BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "timefolio_dashboard.html"
INSTALL_FILE = BASE_DIR / "install.html"
TIMEETF_URL = "https://timeetf.co.kr/m11_view.php"

INSECURE_TLS_CONTEXT = ssl._create_unverified_context()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)

TOP_UI = r'''
<style>
  body { padding-top: 92px !important; }

  .timefolio-topbar {
    position: absolute;
    top: 14px;
    left: 25px;
    right: 25px;
    min-height: 64px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    z-index: 100;
    pointer-events: none;
  }

  .timefolio-view-switch {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 4px;
    border: 1px solid #d9dee7;
    border-radius: 10px;
    background: #fff;
    pointer-events: auto;
  }

  .timefolio-view-switch button {
    min-width: 86px;
    min-height: 34px;
    border: 0;
    border-radius: 7px;
    background: transparent;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }

  .timefolio-view-switch button.active {
    background: #1e293b;
    color: #fff;
  }

  .timefolio-qr {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    pointer-events: auto;
    width: 104px;
  }

  .timefolio-qr a {
    display: block;
    line-height: 0;
  }

  .timefolio-qr img {
    display: block;
    width: 88px;
    height: 88px;
    background: #fff;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .timefolio-qr-label {
    font-size: 10px;
    font-weight: 700;
    color: #475569;
    text-align: center;
    white-space: nowrap;
  }

  body.view-web .desktop-dashboard { display: block !important; }
  body.view-web .mobile-dashboard { display: none !important; }
  body.view-mobile .desktop-dashboard { display: none !important; }
  body.view-mobile .mobile-dashboard { display: block !important; }

  @media (max-width: 768px) {
    body { padding-top: 84px !important; }

    .timefolio-topbar {
      top: 8px;
      left: 12px;
      right: 12px;
      min-height: 58px;
      gap: 8px;
    }

    .timefolio-view-switch { padding: 3px; }

    .timefolio-view-switch button {
      min-width: 72px;
      min-height: 32px;
      font-size: 11px;
    }

    .timefolio-qr { width: 82px; }

    .timefolio-qr img {
      width: 68px;
      height: 68px;
    }

    .timefolio-qr-label { font-size: 9px; }
  }
</style>

<div class="timefolio-topbar" aria-label="화면 및 앱 설치">
  <div class="timefolio-view-switch" role="group" aria-label="화면 선택">
    <button type="button" data-view="web">웹 버전</button>
    <button type="button" data-view="mobile">모바일 버전</button>
  </div>

  <div class="timefolio-qr">
    <a href="/install" aria-label="Timefolio 앱 설치 안내">
      <img src="/assets/timefolio-qr.svg" alt="Timefolio 앱 설치 QR 코드">
    </a>
    <div class="timefolio-qr-label">앱 설치</div>
  </div>
</div>

<script>
(() => {
  const storageKey = 'timefolio-view-mode';
  const buttons = Array.from(document.querySelectorAll('.timefolio-view-switch [data-view]'));

  function setMode(mode, persist = true) {
    const normalized = mode === 'mobile' ? 'mobile' : 'web';
    document.body.classList.remove('view-web', 'view-mobile');
    document.body.classList.add(`view-${normalized}`);

    buttons.forEach((button) => {
      const active = button.dataset.view === normalized;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });

    if (persist) {
      try { localStorage.setItem(storageKey, normalized); } catch (_) {}
    }
  }

  let initialMode = null;
  try { initialMode = localStorage.getItem(storageKey); } catch (_) {}

  if (initialMode !== 'web' && initialMode !== 'mobile') {
    initialMode = window.matchMedia('(max-width: 768px)').matches ? 'mobile' : 'web';
  }

  buttons.forEach((button) => {
    button.addEventListener('click', () => setMode(button.dataset.view));
  });

  setMode(initialMode, false);
})();
</script>
'''


def parse_number(text: str) -> float:
    normalized = re.sub(r"[,\s%]", "", text or "")
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def clean_ticker(code: str) -> str:
    return re.sub(r"\s+US\s+EQUITY\s*$", "", code or "", flags=re.IGNORECASE).strip()


class TimeETFTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[tuple[list[str], list[list[str]]]] = []
        self._table_depth = 0
        self._active_rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None
        self._cell_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            if self._table_depth == 0:
                self._active_rows = []
            self._table_depth += 1
            return
        if self._table_depth == 0:
            return
        if tag == "tr":
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell_parts = []
            self._cell_tag = tag

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._table_depth == 0:
            return
        if tag in {"th", "td"} and self._cell_tag == tag and self._cell_parts is not None:
            value = " ".join("".join(self._cell_parts).split())
            if self._row is not None:
                self._row.append(value)
            self._cell_parts = None
            self._cell_tag = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self._active_rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._table_depth -= 1
            if self._table_depth == 0 and self._active_rows:
                self.tables.append((self._active_rows[0], self._active_rows[1:]))
                self._active_rows = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def extract_items(self) -> list[dict[str, object]]:
        for headers, rows in self.tables:
            name_idx = self._find(headers, "종목명")
            qty_idx = self._find(headers, "수량")
            weight_idx = self._find(headers, "비중")
            code_idx = self._find(headers, "종목코드", "티커")
            if min(name_idx, qty_idx, weight_idx) < 0:
                continue

            items: list[dict[str, object]] = []
            for row in rows:
                if len(row) <= max(name_idx, qty_idx, weight_idx, code_idx):
                    continue
                name = row[name_idx].strip()
                if not name:
                    continue
                items.append({
                    "name": name,
                    "code": clean_ticker(row[code_idx]) if code_idx >= 0 else "",
                    "qty": parse_number(row[qty_idx]),
                    "weight": parse_number(row[weight_idx]),
                })
            if items:
                return items
        return []

    @staticmethod
    def _find(headers: list[str], *candidates: str) -> int:
        for index, header in enumerate(headers):
            if any(candidate in header for candidate in candidates):
                return index
        return -1


class Handler(SimpleHTTPRequestHandler):
    server_version = "TimefolioRenderProxy/1.2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/timefolio":
            self.handle_timefolio(parsed.query, response_format="html")
            return
        if parsed.path == "/api/timefolio/data":
            self.handle_timefolio(parsed.query, response_format="json")
            return
        if parsed.path in ("/", "/index.html"):
            self.serve_html(HTML_FILE, inject=TOP_UI)
            return
        if parsed.path in ("/install", "/install/"):
            self.serve_html(INSTALL_FILE)
            return
        return super().do_GET()

    def serve_html(self, html_file: Path, inject: str = "") -> None:
        try:
            body = html_file.read_text(encoding="utf-8")
            if inject and "</body>" in body:
                body = body.replace("</body>", f"{inject}\n</body>", 1)
            payload = body.encode("utf-8")
        except OSError as exc:
            self.send_error(500, f"HTML file read failed: {exc}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _build_request(self, idx: str, pdf_date: str) -> Request:
        url = f"{TIMEETF_URL}?{urlencode({'idx': idx, 'pdfDate': pdf_date})}"
        return Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://timeetf.co.kr/",
                "Connection": "close",
            },
            method="GET",
        )

    def _fetch_timeetf(self, idx: str, pdf_date: str) -> tuple[bytes, int, str]:
        request = self._build_request(idx, pdf_date)
        try:
            with urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
                return response.read(), getattr(response, "status", 200), response.headers.get_content_type() or "text/html"
        except (ssl.SSLError, OSError):
            with urlopen(request, timeout=20, context=INSECURE_TLS_CONTEXT) as response:
                return response.read(), getattr(response, "status", 200), response.headers.get_content_type() or "text/html"

    def handle_timefolio(self, query_string: str, response_format: str = "html") -> None:
        params = parse_qs(query_string)
        idx = params.get("idx", [None])[0]
        pdf_date = params.get("pdfDate", [None])[0]

        if not idx or not pdf_date:
            self.send_json_error(400, "idx와 pdfDate가 필요합니다.")
            return
        if idx not in {"2", "5"}:
            self.send_json_error(400, "허용되지 않은 ETF idx입니다.")
            return

        try:
            body, status, content_type = self._fetch_timeetf(idx, pdf_date)
        except Exception as exc:
            self.send_json_error(502, f"TimeETF 요청 실패: {type(exc).__name__}: {exc}")
            return

        if response_format == "json":
            parser = TimeETFTableParser()
            try:
                parser.feed(body.decode("utf-8", errors="replace"))
                items = parser.extract_items()
            except Exception as exc:
                self.send_json_error(502, f"TimeETF 데이터 파싱 실패: {type(exc).__name__}: {exc}")
                return
            if not items:
                self.send_json_error(404, "구성종목 데이터를 찾지 못했습니다.")
                return

            payload = json.dumps(
                {"idx": idx, "date": pdf_date, "items": items},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            print(f"[OK] JSON idx={idx}, date={pdf_date}, status={status}, items={len(items)}", flush=True)
            return

        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        print(f"[OK] idx={idx}, date={pdf_date}, status={status}, bytes={len(body)}", flush=True)

    def send_json_error(self, status: int, message: str) -> None:
        payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        print(f"[ERROR] {status}: {message}", flush=True)

    def log_message(self, fmt, *args) -> None:
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} - {fmt % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[Timefolio] serving on http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
