#!/usr/bin/env python3
"""Install only the optional test tools selected by the operator.

No elevation, global pip packages, implicit project edits, or destructive cleanup.
"""

from __future__ import annotations

import argparse
import os
import shlex
import platform
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv-ai-testing"
REQUIREMENTS = ROOT / "scripts" / "requirements-ai-testing.txt"
FLAUI_VERSION = "5.0.0"


class SetupError(Exception):
    """A prerequisite or tool operation failed safely."""


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def playwright_version(requirements: Path | None = None) -> str:
    requirements = requirements or REQUIREMENTS
    lines = [line.strip() for line in requirements.read_text(encoding="utf-8").splitlines()]
    pins = [line.split("==", 1)[1] for line in lines if line.startswith("playwright==")]
    if len(pins) != 1 or not pins[0] or any(" " in pin for pin in pins):
        raise SetupError("Expected exactly one pinned playwright==VERSION in requirements")
    return pins[0]


def run(command: list[str], *, capture: bool = False) -> str:
    # Do not invoke a shell or interpolate operator-controlled paths as commands.
    try:
        result = subprocess.run(command, cwd=ROOT, check=True, text=True,
                                stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None,
                                timeout=30 if capture else None)
    except FileNotFoundError as exc:
        raise SetupError(f"Command not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise SetupError(f"Timed out checking command: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip() if capture else "See command output above."
        raise SetupError(f"Command failed ({exc.returncode}): {command[0]}\n{detail}") from exc
    return (result.stdout or "").strip()


def dotnet_check(*, minimum_major: int | None = None) -> None:
    value = run(["dotnet", "--version"], capture=True)
    try:
        major = int(value.split(".", 1)[0])
    except (ValueError, IndexError) as exc:
        raise SetupError(f"Unrecognized .NET SDK version: {value}") from exc
    if minimum_major is not None and major < minimum_major:
        raise SetupError(f".NET SDK {minimum_major}+ required; detected {value}")


def validate_windows_project(project: Path | None) -> Path | None:
    if project is None:
        return None
    if platform.system() != "Windows":
        raise SetupError("FlaUI installation is only supported on Windows")
    project = project.expanduser().resolve()
    if not project.is_file() or project.suffix.lower() != ".csproj":
        raise SetupError("--windows-ui-project must name an existing .csproj file")
    # NuGet central package management can edit a shared Directory.Packages.props.
    # Do not implicitly mutate a second project-wide package manifest.
    for directory in project.parents:
        if (directory / "Directory.Packages.props").is_file():
            raise SetupError("Central NuGet package management detected; add FlaUI manually after review")
    if "<ManagePackageVersionsCentrally>true" in project.read_text(encoding="utf-8"):
        raise SetupError("Central NuGet package management detected; add FlaUI manually after review")
    return project


def install_plan(venv: Path, *, install_web: bool = True, with_xquery: bool = False,
                 windows_project: Path | None = None) -> list[list[str]]:
    python = str(venv_python(venv))
    commands = []
    if install_web:
        if not venv_python(venv).is_file():
            commands.append([sys.executable, "-m", "venv", str(venv)])
        commands.extend([
            [python, "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
             "-r", str(REQUIREMENTS)],
            [python, "-m", "playwright", "install", "chromium"],
        ])
    if with_xquery:
        commands.append(["dotnet", "tool", "restore", "--tool-manifest",
                         str(ROOT / ".config" / "dotnet-tools.json")])
    if windows_project is not None:
        commands.append(["dotnet", "add", str(windows_project), "package",
                         "FlaUI.UIA3", "--version", FLAUI_VERSION])
    return commands


def check_web_tools(venv: Path) -> None:
    python = venv_python(venv)
    if not python.is_file():
        raise SetupError(f"Missing test environment: {python}. Run installer without --check")
    version = playwright_version()
    verification = (
        "from importlib.metadata import version; "
        f"assert version('playwright') == {version!r}, 'Playwright version differs'; "
        "from pathlib import Path; from playwright.sync_api import sync_playwright; "
        "p = sync_playwright().start(); "
        "executable = Path(p.chromium.executable_path); "
        "p.stop(); "
        "assert executable.is_file(), f'Chromium missing: {executable}'; "
        "print(f'Playwright OK; Chromium: {executable}')"
    )
    run([str(python), "-c", verification])
    print("Package and browser binary found (GUI operation not yet verified).")


def check_flaui_reference(project: Path) -> None:
    try:
        root = ElementTree.parse(project).getroot()
    except ElementTree.ParseError as exc:
        raise SetupError(f"Invalid .csproj XML: {project}") from exc
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "PackageReference":
            continue
        if element.attrib.get("Include", element.attrib.get("Update")) != "FlaUI.UIA3":
            continue
        declared = element.attrib.get("Version")
        if not declared:
            declared = next((child.text for child in element
                             if child.tag.rsplit("}", 1)[-1] == "Version"), None)
        if not declared or not declared.strip():
            raise SetupError("FlaUI.UIA3 version is managed elsewhere; verify the central version explicitly")
        if declared.strip() != FLAUI_VERSION:
            raise SetupError(f"FlaUI.UIA3 version differs: {declared.strip()}")
        print("Pinned FlaUI.UIA3 reference found (NuGet restore/build not verified).")
        return
    raise SetupError("No FlaUI.UIA3 PackageReference in the selected project")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install isolated Playwright/Chromium and optional Feature Map test tools")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print planned commands without changes")
    mode.add_argument("--check", action="store_true", help="Check installed tools without changes")
    parser.add_argument("--skip-web", action="store_true",
                        help="Skip Playwright/Chromium (for Windows-only or xquery-only setup)")
    parser.add_argument("--with-xquery", action="store_true",
                        help="Also restore existing pinned xquery-mcp local .NET tool")
    parser.add_argument("--windows-ui-project", type=Path, metavar="TESTS.csproj",
                        help="Windows only: explicitly add pinned FlaUI.UIA3 to this test project")
    parser.add_argument("--smoke", action="store_true",
                        help="After installation, run real browser+SQLite fictional smoke test")
    args = parser.parse_args(argv)
    if args.smoke and (args.dry_run or args.check or args.skip_web):
        parser.error("--smoke requires web setup and cannot be combined with --dry-run or --check")
    if args.skip_web and not (args.with_xquery or args.windows_ui_project):
        parser.error("--skip-web requires --with-xquery or --windows-ui-project")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if sys.version_info < (3, 10):
            raise SetupError("Python 3.10 or newer is required")
        playwright_version()
        project = validate_windows_project(args.windows_ui_project)
        if args.dry_run:
            print("DRY RUN: no commands will be executed or files changed")
            for command in install_plan(VENV, install_web=not args.skip_web,
                                        with_xquery=args.with_xquery, windows_project=project):
                print(subprocess.list2cmdline(command) if os.name == "nt"
                      else shlex.join(command))
            print("The installer does not install OS browser libraries or change global pip packages.")
            return 0
        if args.with_xquery:
            dotnet_check(minimum_major=10)
        if project is not None:
            dotnet_check()
        if args.check:
            if not args.skip_web:
                check_web_tools(VENV)
            if args.with_xquery:
                listing = run(["dotnet", "tool", "list", "--local", "--tool-manifest",
                               str(ROOT / ".config" / "dotnet-tools.json")], capture=True)
                if "xquery-mcp" not in listing:
                    raise SetupError("xquery-mcp is not restored")
                print("xquery-mcp declared in the local .NET manifest (tool launch not verified)")
            if project is not None:
                check_flaui_reference(project)
            return 0
        for command in install_plan(VENV, install_web=not args.skip_web,
                                    with_xquery=args.with_xquery, windows_project=project):
            print(f"Running: {command[0]} ...", flush=True)
            run(command)
        if not args.skip_web:
            check_web_tools(VENV)
        if args.smoke:
            run([str(venv_python(VENV)), str(ROOT / "examples" / "ai-assisted-testing" /
                                          "run_demo.py"), "--engine", "browser"])
        print("Setup finished.")
        if not args.skip_web:
            print("To run the browser example:")
            print(f"  {venv_python(VENV)} examples/ai-assisted-testing/run_demo.py --engine browser")
        return 0
    except SetupError as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
