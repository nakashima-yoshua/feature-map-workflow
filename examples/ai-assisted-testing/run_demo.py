"""Run one synthetic UI/HTTP-to-DB scenario and retain reproducible evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import threading
import traceback
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import make_server, read_records, setup_database

ROOT = Path(__file__).resolve().parents[2]
FEATURE_MAP = "examples/fictional-puzzle-log/feature-map.xml"
TEST_REF = "examples/ai-assisted-testing/run_demo.py"
PUZZLE_ID = "PZ-001"
PUZZLE_NAME = "\u6708\u306e\u8ff7\u8def"  # Approved fictional test fixture.


def check_feature_map() -> None:
    """Check that test IDs still resolve to the canonical, existing Feature Map."""
    root = ET.parse(ROOT / FEATURE_MAP).getroot()
    if root.find("./useCase[@id='UC-REGISTER']") is None:
        raise ValueError("Feature Map is missing UC-REGISTER")
    if root.find("./verify/case[@id='TEST-REGISTER']") is None:
        raise ValueError("Feature Map is missing TEST-REGISTER")



def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL, timeout=3,
            text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unversioned"


def run_http(base_url: str, run_dir: Path) -> bool:
    """Dependency-free transport smoke test; not a browser/UI test."""
    with urlopen(base_url + "/", timeout=5) as reply:
        initial_html = reply.read().decode("utf-8")
    if 'id="puzzle-id"' not in initial_html or 'id="puzzle-name"' not in initial_html:
        raise AssertionError("Input fields missing")
    payload = urlencode({"id": PUZZLE_ID, "name": PUZZLE_NAME}).encode("utf-8")
    with urlopen(Request(base_url + "/register", data=payload, method="POST"), timeout=5) as reply:
        body = reply.read().decode("utf-8")
    (run_dir / "operation.log").write_text("GET /\nPOST /register\n", encoding="utf-8")
    return 'id="result" role="status">Registered' in body


def run_browser(base_url: str, run_dir: Path) -> bool:
    """Real Playwright browser typing/clicks/screenshots/trace; optional dependency."""
    from playwright.sync_api import sync_playwright

    screenshots = run_dir / "screenshots"
    screenshots.mkdir()
    actions: list[str] = []
    messages: list[str] = []
    with sync_playwright() as playwright:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        browser = playwright.chromium.launch(
            headless=True, **({"executable_path": executable} if executable else {})
        )
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on("console", lambda message: messages.append(f"{message.type}: {message.text}"))
        try:
            page.goto(base_url + "/")
            actions.append("navigate / (browser)")
            page.screenshot(path=str(screenshots / "01-input.png"))
            page.locator("#puzzle-id").fill(PUZZLE_ID)
            page.locator("#puzzle-name").fill(PUZZLE_NAME)
            actions.append("fill puzzle-id and puzzle-name")
            page.locator("#register").click()
            actions.append("click register")
            page.locator("#result").wait_for()
            page.screenshot(path=str(screenshots / "02-result.png"))
            return page.locator("#result").inner_text() == "Registered"
        except Exception:
            page.screenshot(path=str(screenshots / "failure.png"))
            raise
        finally:
            context.tracing.stop(path=str(run_dir / "trace.zip"))
            (run_dir / "operation.log").write_text("\n".join(actions) + "\n", encoding="utf-8")
            (run_dir / "browser-console.log").write_text("\n".join(messages) + "\n", encoding="utf-8")
            browser.close()


def run_scenario(engine: str = "http", output: Path | None = None,
                 expected_name: str = PUZZLE_NAME) -> tuple[str, Path]:
    if engine not in {"http", "browser"}:
        raise ValueError("engine must be http or browser")
    check_feature_map()
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="fm-test-", dir=output))
    db_path = run_dir / "fixture.sqlite3"
    setup_database(db_path)
    before = read_records(db_path)
    save_json(run_dir / "before.json", before)
    status = "blocked"
    ui_result = False
    error = None
    server = make_server(db_path, run_dir / "application.log")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        if engine == "browser":
            ui_result = run_browser(base_url, run_dir)
        else:
            ui_result = run_http(base_url, run_dir)
        status = "failed"  # The actual expected-state assertions run after HTTP/UI execution.
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        (run_dir / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    after = read_records(db_path)
    expected = [{"id": PUZZLE_ID, "name": expected_name, "state": "pending"}]
    checks = {
        "initial_empty": before == [],
        "registration_response": ui_result,
        "db_expected_state": after == expected,
    }
    if error is None:
        status = "passed" if all(checks.values()) else "failed"
    save_json(run_dir / "after.json", after)
    save_json(run_dir / "diff.json", {
        "added": [row for row in after if row not in before],
        "removed": [row for row in before if row not in after],
    })
    evidence = sorted(str(path.relative_to(run_dir)) for path in run_dir.rglob("*")
                      if path.is_file() and path.name not in {"fixture.sqlite3", "result.json"})
    result = {
        "schemaVersion": 1,
        "runId": "RUN-" + uuid.uuid4().hex[:12],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "featureMap": FEATURE_MAP,
        "useCaseId": "UC-REGISTER",
        "verifyCaseId": "TEST-REGISTER",
        "testRef": TEST_REF,
        "runner": "playwright-python" if engine == "browser" else "python-http-smoke",
        "sourceRevision": revision(),
        "environment": "synthetic-loopback-sqlite",
        "fixtureRef": "examples/ai-assisted-testing/app.py:setup_database",
        "status": status,
        "checks": checks,
        "expected": expected,
        "observed": after,
        "error": error,
        "evidence": evidence,
        "limitations": (["HTTP transport only; browser clicks and screenshots not verified"]
                        if engine == "http" else ["Synthetic app/SQLite only; no external integration"]),
    }
    save_json(run_dir / "result.json", result)
    return status, run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic Feature Map E2E evidence example")
    parser.add_argument("--engine", choices=("http", "browser"), default="http")
    parser.add_argument("--output", type=Path, help="Parent directory for a new isolated run directory")
    parser.add_argument("--expected-name", default=PUZZLE_NAME,
                        help="Override expected result to demonstrate a failing assertion")
    args = parser.parse_args()
    status, run_dir = run_scenario(args.engine, args.output, args.expected_name)
    print(f"{status}: {run_dir / 'result.json'}")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
