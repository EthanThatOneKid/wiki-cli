"""Local HTTP server for browsing the wiki as HTML -- no external web frameworks."""

from __future__ import annotations

import html as html_module
import json
import re
import signal
import sys
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional

from .site import (
    WikiSite,
    VirtualPage,
    INLINE_CSS,
    build_site,
    build_index_html,
    build_page_html
)




class WikiHandler(BaseHTTPRequestHandler):
    site: WikiSite = None  # type: ignore[assignment]

    def do_GET(self) -> None:
        parsed = re.sub(r"\?.*$", "", self.path)
        parsed = parsed.rstrip("/")

        if parsed == "" or parsed == "/index":
            self._send_html(build_index_html(self.site))
        elif parsed.startswith("/wiki/"):
            slug = parsed[6:]
            target = self._find_page(slug)
            if target:
                self._send_html(build_page_html(target, self.site))
            else:
                self._send_error(404, f"Page not found: {slug}")
        else:
            self._send_error(404, f"Not found: {self.path}")

    def _find_page(self, slug: str) -> VirtualPage | None:
        for page in self.site.pages:
            if page.full_slug == slug:
                return page
        for page in self.site.pages:
            if page.file_slug == slug and not page.section_slug:
                return page
        for page in self.site.pages:
            if page.file_slug == slug:
                return page
        return None

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code: int, message: str) -> None:
        body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{code}</title>
<style>{INLINE_CSS}</style>
</head>
<body>
<header><a href="/" class="site-title">Wiki</a></header>
<main>
<h1>{code}</h1>
<p>{html_module.escape(message)}</p>
</main>
</body>
</html>""".encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")


def create_server(
    wiki_dir: Path,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> HTTPServer:
    """Build the site and return a configured HTTPServer (not yet started)."""
    site = build_site(wiki_dir)
    WikiHandler.site = site

    server = HTTPServer((host, port), WikiHandler)
    print(f"Wiki server ready at http://{host}:{port}/")
    print(f"Serving {len(site.pages)} pages from {wiki_dir}")
    return server


def run_server(
    wiki_dir: Path,
    host: str = "127.0.0.1",
    port: int = 8080,
) -> None:
    """Create and start the wiki HTTP server, blocking until shutdown."""
    server = create_server(wiki_dir, host=host, port=port)

    def shutdown(*_: Any) -> None:
        print("\nShutting down server...")
        server.shutdown()

    try:
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
    except ValueError:
        pass  # not in main thread – no interactive signal handling

    print("Press Ctrl+C to stop.")
    server.serve_forever()
