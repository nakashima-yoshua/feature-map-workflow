"""Synthetic puzzle-registration web app for isolated E2E evidence demos."""

from __future__ import annotations

import html
import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PUZZLE_ID = "PZ-001"


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            yield conn
    finally:
        conn.close()


def setup_database(db_path: Path) -> None:
    """Make an isolated fixture with a required master and no registered puzzle."""
    with connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE puzzle_catalog (id TEXT PRIMARY KEY);
            CREATE TABLE puzzle_record (
                id TEXT PRIMARY KEY REFERENCES puzzle_catalog(id),
                name TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('pending', 'completed'))
            );
            INSERT INTO puzzle_catalog (id) VALUES ('PZ-001');
        """)


def read_records(db_path: Path) -> list[dict[str, str]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT id, name, state FROM puzzle_record ORDER BY id").fetchall()
    return [{"id": item[0], "name": item[1], "state": item[2]} for item in rows]


def make_handler(db_path: Path, log_path: Path) -> type[BaseHTTPRequestHandler]:
    class PuzzleHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            # Never log request bodies. The app runs only with fictional data.
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write((format % args) + "\n")

        def page(self, status: int, message: str = "") -> None:
            output = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Fictional Puzzle Log</title></head><body>
<h1>Fictional Puzzle Log</h1>
<form action="/register" method="post">
<label>Puzzle ID <input id="puzzle-id" name="id" required></label>
<label>Name <input id="puzzle-name" name="name" required></label>
<button id="register" type="submit">Register</button>
</form><p id="result" role="status">{html.escape(message)}</p>
</body></html>""".encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(output)))
            self.end_headers()
            self.wfile.write(output)

        def do_GET(self) -> None:
            if self.path != "/":
                self.send_error(404)
                return
            self.page(200)

        def do_POST(self) -> None:
            if self.path != "/register":
                self.send_error(404)
                return
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2048:
                self.page(400, "Invalid request")
                return
            form = parse_qs(self.rfile.read(size).decode("utf-8"))
            item_id = form.get("id", [""])[0]
            name = form.get("name", [""])[0].strip()
            if not name or len(name) > 40:
                self.page(400, "Invalid puzzle name")
                return
            try:
                with connect(db_path) as conn:
                    match = conn.execute("SELECT 1 FROM puzzle_catalog WHERE id = ?", (item_id,)).fetchone()
                    if not match:
                        self.page(400, "Unknown puzzle ID")
                        return
                    conn.execute(
                        "INSERT INTO puzzle_record (id, name, state) VALUES (?, ?, 'pending')",
                        (item_id, name),
                    )
            except sqlite3.IntegrityError:
                self.page(409, "Already registered")
                return
            self.page(200, "Registered")

    return PuzzleHandler


def make_server(db_path: Path, log_path: Path) -> ThreadingHTTPServer:
    # Explicitly bind to loopback. Never connect to customer or production systems.
    return ThreadingHTTPServer(("127.0.0.1", 0), make_handler(db_path, log_path))
