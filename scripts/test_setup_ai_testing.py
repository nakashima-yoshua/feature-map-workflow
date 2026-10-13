#!/usr/bin/env python3
"""No-network installer tests (no actual packages installed)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).with_name("setup-ai-testing.py")
SPEC = importlib.util.spec_from_file_location("feature_map_setup_ai_testing", MODULE)
assert SPEC and SPEC.loader
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "requirements-ai-testing.txt").write_text(
            "playwright==1.63.0\n", encoding="utf-8")
        self.venv = self.root / ".venv-ai-testing"
        patch_root = patch.object(setup, "ROOT", self.root)
        patch_venv = patch.object(setup, "VENV", self.venv)
        patch_req = patch.object(setup, "REQUIREMENTS", self.root / "scripts" / "requirements-ai-testing.txt")
        patch_root.start()
        patch_venv.start()
        patch_req.start()
        self.addCleanup(patch_root.stop)
        self.addCleanup(patch_venv.stop)
        self.addCleanup(patch_req.stop)

    def test_plugin_packager_excludes_local_virtualenv(self) -> None:
        # Installing the optional web tools must not inflate the plugin ZIP.
        packager = Path(__file__).with_name("package_plugin.py")
        if packager.exists():
            text = packager.read_text(encoding="utf-8")
            self.assertIn('".venv-ai-testing"', text)

    def test_default_plan_is_isolated_and_pinned(self) -> None:
        plan = setup.install_plan(self.venv)
        self.assertEqual(["-m", "venv"], plan[0][1:3])
        self.assertEqual("-r", plan[1][-2])
        self.assertIn(".venv-ai-testing", plan[1][0])
        self.assertEqual(["-m", "playwright", "install", "chromium"], plan[2][1:])
        self.assertEqual(3, len(plan))
        self.assertEqual("1.63.0", setup.playwright_version())

    def test_existing_virtualenv_is_reused(self) -> None:
        python = setup.venv_python(self.venv)
        python.parent.mkdir(parents=True)
        python.touch()
        plan = setup.install_plan(self.venv)
        self.assertEqual(2, len(plan))
        self.assertNotIn("venv", plan[0])

    def test_dry_run_never_runs_commands_or_creates_venv(self) -> None:
        output = io.StringIO()
        with patch.object(setup, "run") as called, contextlib.redirect_stdout(output):
            self.assertEqual(0, setup.main(["--dry-run", "--with-xquery"]))
        called.assert_not_called()
        self.assertFalse(self.venv.exists())
        self.assertIn("dotnet tool restore", output.getvalue())
        self.assertIn("playwright install chromium", output.getvalue())

    def test_check_missing_tools_does_not_install(self) -> None:
        errors = io.StringIO()
        with patch.object(setup, "run") as called, contextlib.redirect_stderr(errors):
            self.assertEqual(2, setup.main(["--check"]))
        called.assert_not_called()
        self.assertIn("Missing test environment", errors.getvalue())

    def test_linux_rejects_windows_install_before_write(self) -> None:
        project = self.root / "ui-tests.csproj"
        project.touch()
        with patch.object(setup.platform, "system", return_value="Linux"):
            with patch.object(setup, "run") as called:
                self.assertEqual(2, setup.main(["--windows-ui-project", str(project)]))
        called.assert_not_called()
        self.assertFalse(self.venv.exists())

    def test_windows_ui_blocks_central_package_management(self) -> None:
        project = self.root / "ui-tests.csproj"
        project.write_text("<Project/>", encoding="utf-8")
        (self.root / "Directory.Packages.props").write_text("<Project/>", encoding="utf-8")
        with patch.object(setup.platform, "system", return_value="Windows"):
            with self.assertRaisesRegex(setup.SetupError, "Central NuGet"):
                setup.validate_windows_project(project)

    def test_windows_project_opt_in_uses_pinned_flaui(self) -> None:
        project = self.root / "ui-tests.csproj"
        project.write_text("<Project/>", encoding="utf-8")
        with patch.object(setup.platform, "system", return_value="Windows"):
            commands = setup.install_plan(self.venv, with_xquery=True,
                                          windows_project=setup.validate_windows_project(project))
        self.assertEqual(["dotnet", "add"], commands[-1][:2])
        self.assertTrue(Path(commands[-1][2]).samefile(project))
        self.assertEqual(["package", "FlaUI.UIA3", "--version", "5.0.0"], commands[-1][3:])
        self.assertEqual("dotnet", commands[-2][0])
        self.assertNotIn("FlaUI.Core", str(commands))  # UIA3 supplies it transitively.

    def test_old_dotnet_blocks_xquery_before_install(self) -> None:
        with patch.object(setup, "run", return_value="9.0.300") as called:
            self.assertEqual(2, setup.main(["--with-xquery"]))
        self.assertEqual(1, called.call_count)
        self.assertFalse(self.venv.exists())

    def test_command_failure_stops_plan(self) -> None:
        with patch.object(setup, "run", side_effect=setup.SetupError("pip failed")) as called:
            self.assertEqual(2, setup.main([]))
        self.assertEqual(1, called.call_count)

    def test_check_runs_version_and_browser_binary_probe(self) -> None:
        python = setup.venv_python(self.venv)
        python.parent.mkdir(parents=True)
        python.touch()
        with patch.object(setup, "run", return_value="Playwright OK") as called:
            self.assertEqual(0, setup.main(["--check"]))
        called.assert_called_once()
        self.assertEqual(str(python), called.call_args.args[0][0])
        self.assertIn("chromium.executable_path", called.call_args.args[0][2])

    def test_windows_only_setup_skips_all_web_dependencies(self) -> None:
        project = self.root / "ui-tests.csproj"
        project.touch()
        plan = setup.install_plan(self.venv, install_web=False, windows_project=project)
        self.assertEqual(1, len(plan))
        self.assertEqual("FlaUI.UIA3", plan[0][4])

    def test_xquery_only_skips_all_web_dependencies(self) -> None:
        plan = setup.install_plan(self.venv, install_web=False, with_xquery=True)
        self.assertEqual(["dotnet", "tool", "restore"], plan[0][:3])
        self.assertEqual(1, len(plan))

    def test_flaui_check_rejects_missing_reference(self) -> None:
        project = self.root / "tests.csproj"
        project.write_text("<Project/>", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "No FlaUI"):
            setup.check_flaui_reference(project)

    def test_flaui_check_accepts_explicit_pinned_reference(self) -> None:
        project = self.root / "tests.csproj"
        project.write_text('<Project><ItemGroup><PackageReference Include="FlaUI.UIA3" '
                           'Version="5.0.0"/></ItemGroup></Project>', encoding="utf-8")
        setup.check_flaui_reference(project)

    def test_flaui_check_does_not_accept_unchecked_central_version(self) -> None:
        project = self.root / "tests.csproj"
        project.write_text('<Project><ItemGroup><PackageReference Include="FlaUI.UIA3"/>'
                           '</ItemGroup></Project>', encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "managed elsewhere"):
            setup.check_flaui_reference(project)

    def test_flaui_check_rejects_version_mismatch(self) -> None:
        project = self.root / "tests.csproj"
        project.write_text('<Project><ItemGroup><PackageReference Include="FlaUI.UIA3" '
                           'Version="4.0.0"/></ItemGroup></Project>', encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "version differs"):
            setup.check_flaui_reference(project)

    def test_wrapper_modes_are_mutually_exclusive(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                setup.parse_args(["--smoke", "--check"])


if __name__ == "__main__":
    unittest.main()
