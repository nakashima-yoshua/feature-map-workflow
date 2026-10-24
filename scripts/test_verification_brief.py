#!/usr/bin/env python3
"""Regression checks for focused UML selection and consolidated human work briefs."""

from __future__ import annotations

import json
import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "fictional-stock-request"
SCRIPT = ROOT / "skills" / "feature-map-workflow" / "scripts" / "build_verification_brief.py"


class VerificationBriefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.xml = self.dir / "feature-map.xml"
        self.plan = self.dir / "plan.json"
        shutil.copyfile(EXAMPLE / "feature-map.xml", self.xml)
        shutil.copyfile(EXAMPLE / "human-work-plan.example.json", self.plan)

    def run_brief(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--feature-map", str(self.xml),
             "--use-case", "UC-SUBMIT", *args],
            capture_output=True, text=True, timeout=15,
        )

    def document(self, name="verification-brief.html"):
        return etree.HTML((self.dir / name).read_text(encoding="utf-8"))

    def test_focused_fictional_brief_retains_cases_and_session(self) -> None:
        run = self.run_brief("--plan", str(self.plan))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("2 cases, 3 diagrams, 1 directed sessions", run.stdout)
        page = self.document()
        text = etree.tostring(page, encoding="unicode", method="html")
        self.assertIn("DG-FLOW", text)
        self.assertIn("DG-DFD", text)
        self.assertIn("DG-ER", text)
        self.assertIn("H-RECEPTION", text)
        self.assertIn("V-SUBMIT", text)
        self.assertIn("V-REJECT", text)
        self.assertIn("ケースの初期化", text)
        self.assertIn("実測・判定は検証ID別", text)
        self.assertIn("sourceRevision", self.plan.read_text(encoding="utf-8"))
        self.assertIn("const fallback = false", text)
        self.assertEqual(3, len(page.xpath("//details[@class='diagram']")))
        self.assertEqual(1, len(page.xpath("//details[@class='diagram'][@open]")))
        self.assertEqual(2, len(page.xpath("//article//ol/li[strong]")))
        self.assertNotIn("<script>alert(", text)

    def test_without_plan_is_explicitly_non_executable(self) -> None:
        run = self.run_brief()
        self.assertEqual(run.returncode, 0, run.stderr)
        text = etree.tostring(self.document(), encoding="unicode", method="html")
        self.assertIn("HALT：作業計画が未指定", text)
        self.assertNotIn("H-RECEPTION", text)
        self.assertIn("2 cases, 3 diagrams, 0 directed sessions", run.stdout)

    def v2_plan(self):
        return json.loads((EXAMPLE / "human-work-plan.v2.example.json").read_text(encoding="utf-8"))

    def save_plan(self, plan):
        self.plan.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    def test_v2_shared_operation_keeps_individual_checkpoints_and_trial_state(self):
        self.save_plan(self.v2_plan())
        run = self.run_brief("--plan", str(self.plan))
        self.assertEqual(0, run.returncode, run.stderr)
        page = self.document()
        self.assertEqual(1, len(page.xpath("//*[@data-operation-id='OP-OPEN']")))
        self.assertEqual(4, len(page.xpath("//*[@data-condition-id]")))
        rendered = " ".join(page.itertext())
        for expected in ("NORMAL-READY", "ERROR-READY", "NORMAL-RESULT", "ERROR-RESULT",
                         "fictional:REQ-SUBMIT@1", "OP-OPEN", "P-SUBMIT@1", "required", "delta"):
            self.assertIn(expected, rendered)
        self.assertIn("正式合格", rendered)
        self.assertIn("未測定", rendered)

    def test_v2_rejects_broken_bindings_without_replacing_output(self):
        self.assertEqual(0, self.run_brief().returncode)
        original = (self.dir / "verification-brief.html").read_bytes()
        mutations = [
            lambda p: p["sessions"][0]["steps"][0]["checks"][0].pop("capture"),
            lambda p: p["sessions"][0]["steps"][0]["checks"][0].update(caseId="UNKNOWN"),
            lambda p: p["sessions"][0]["steps"][1]["checks"][0].update(stepNo=1),
            lambda p: p["sessions"][0]["steps"].pop(),
            lambda p: p["sessions"][0]["steps"][0]["checks"][0].update(status="passed"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                p = self.v2_plan(); mutate(p); self.save_plan(p)
                self.assertNotEqual(0, self.run_brief("--plan", str(self.plan), "--force").returncode)
                self.assertEqual(original, (self.dir / "verification-brief.html").read_bytes())

    def test_v2_refuses_stale_procedure_or_incompatible_context(self):
        mutations = [
            lambda p: p["procedures"][0].update(status="retired"),
            lambda p: p["procedures"][0]["appliesTo"].update(actor="admin"),
            lambda p: p["procedures"][0]["appliesTo"].update(data="live-data"),
            lambda p: p["procedures"][0]["appliesTo"].update(sourceRevision="other"),
            lambda p: p["sessions"][0]["steps"][0].update(procedureRevision="2"),
            lambda p: p["procedures"][0].pop("verifiedAt"),
            lambda p: p["sessions"][0]["steps"][0]["trial"].pop("recordRef"),
            lambda p: p["procedures"][0].update(destructive=True, parallelSafe=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                p = self.v2_plan(); mutate(p); self.save_plan(p)
                self.assertNotEqual(0, self.run_brief("--plan", str(self.plan)).returncode)
                self.assertFalse((self.dir / "verification-brief.html").exists())

    def test_v2_requires_dependencies_and_restart_within_prior_session_steps(self):
        for field, value in (("dependsOn", ["OP-REJECT"]), ("dependsOn", ["UNKNOWN"]),
                             ("restartFrom", "OP-REJECT")):
            with self.subTest(field=field, value=value):
                p = self.v2_plan(); p["sessions"][0]["steps"][0][field] = value
                self.save_plan(p)
                self.assertNotEqual(0, self.run_brief("--plan", str(self.plan)).returncode)

    def test_v2_measurements_require_finite_nonnegative_observations_and_reference(self):
        p = self.v2_plan()
        p["measurements"] = {"reference": "fictional:timing/1", "minutes": {"setup": 3, "waiting": 2}}
        self.save_plan(p)
        self.assertEqual(0, self.run_brief("--plan", str(self.plan)).returncode)
        self.assertIn("fictional:timing/1", (self.dir / "verification-brief.html").read_text(encoding="utf-8"))
        for value in (-1, float("inf"), True):
            q = copy.deepcopy(p); q["measurements"]["minutes"]["setup"] = value
            self.save_plan(q)
            self.assertNotEqual(0, self.run_brief("--plan", str(self.plan), "--force").returncode)

    def extend_with_all_relevant_uml(self) -> list[str]:
        tree = ET.parse(self.xml)
        root = tree.getroot()
        diagrams = root.find("./diagrams")
        extra = [
            ("DG-STATE", "state", "状態遷移 / UC-SUBMIT", "stateDiagram-v2\n  [*] --> Pending\n"),
            ("DG-SEQUENCE", "sequence", "呼出順序 / UC-SUBMIT", "sequenceDiagram\n  A->>B: retry\n"),
            ("DG-USECASE", "usecase", "権限 / UC-SUBMIT", "flowchart LR\n  Actor --> Action\n"),
            ("DG-CLASS", "class", "クラス構造 / UC-SUBMIT", "classDiagram\n  class Request\n"),
            ("DG-ARCH", "architecture", "システム構成 / UC-SUBMIT", "flowchart LR\n  A --> B\n"),
        ]
        for ident, kind, title, source in extra:
            ET.SubElement(diagrams, "diagram", id=ident, kind=kind, title=title).text = source
        ver = root.find("./verify")
        for ident, kind, message in (
            ("V-STATE", "state", "状態遷移を検証"),
            ("V-RETRY", "retry", "リトライ後の到達結果"),
            ("V-ROLE", "permission", "権限なしの動作"),
            ("V-CLASS", "other", "クラスの責務を確認"),
        ):
            case = ET.SubElement(ver, "case", id=ident, type=kind, status="not-run")
            ET.SubElement(case, "condition").text = message
            ET.SubElement(case, "expect").text = "Expected fictional behavior"
        source_map = root.find("./sourceMap")
        ET.SubElement(source_map, "ref", kind="api", target="fictional:external-api", access="call")
        ET.SubElement(source_map, "ref", kind="external", target="fictional:external-service", access="call")
        tree.write(self.xml, encoding="utf-8", xml_declaration=True)
        return ["DG-FLOW", "DG-DFD", "DG-ER"] + [a[0] for a in extra]

    def test_unlimited_relevant_diagrams_auto_and_explicit(self) -> None:
        ids = self.extend_with_all_relevant_uml()
        run = self.run_brief()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8 diagrams", run.stdout)
        text = (self.dir / "verification-brief.html").read_text(encoding="utf-8")
        self.assertTrue(all(x in text for x in ids))
        self.assertEqual(8, len(self.document().xpath("//details[@class='diagram']")))
        # More than three selected diagram IDs are now supported.
        run = self.run_brief("--force", *[arg for ident in reversed(ids)
                                        for arg in ("--diagram", ident)])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("8 diagrams", run.stdout)

    def test_out_of_focus_diagram_is_not_guessed_or_included(self) -> None:
        tree = ET.parse(self.xml)
        ET.SubElement(tree.getroot().find("./diagrams"), "diagram",
                      id="DG-OTHER", kind="state", title="別機能 / UC-OTHER").text = (
                          "stateDiagram-v2\n  [*] --> Done"
                      )
        tree.write(self.xml, encoding="utf-8", xml_declaration=True)
        run = self.run_brief()
        self.assertEqual(run.returncode, 0, run.stderr)
        text = (self.dir / "verification-brief.html").read_text(encoding="utf-8")
        self.assertNotIn("DG-OTHER", text)
        self.assertNotEqual(0, self.run_brief("--diagram", "DG-OTHER", "--force").returncode)

    def test_plan_must_cover_cases_once_and_preserve_previous_output(self) -> None:
        self.assertEqual(0, self.run_brief("--plan", str(self.plan)).returncode)
        orig = (self.dir / "verification-brief.html").read_bytes()
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        plan["sessions"][0]["steps"].pop()
        self.plan.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        failed = self.run_brief("--plan", str(self.plan), "--force")
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("cover exactly", failed.stderr)
        self.assertEqual(orig, (self.dir / "verification-brief.html").read_bytes())

    def test_escaping_dtd_and_output_path_restriction(self) -> None:
        tree = ET.parse(self.xml)
        tree.getroot().find("./meta/feature").text = "<script>alert('secret')</script>"
        tree.write(self.xml, encoding="utf-8", xml_declaration=True)
        self.assertEqual(0, self.run_brief().returncode)
        html = (self.dir / "verification-brief.html").read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;alert(", html)
        self.assertNotIn("<script>alert('secret')</script>", html)
        self.assertNotEqual(0, self.run_brief("--output", "../escaped.html").returncode)
        self.xml.write_text("<!DOCTYPE a><featureMap/>", encoding="utf-8")
        self.assertNotEqual(0, self.run_brief("--force").returncode)

    def test_reject_output_symlink(self) -> None:
        dest = self.dir / "target.html"
        dest.write_text("safe", encoding="utf-8")
        link = self.dir / "verification-brief.html"
        try:
            link.symlink_to(dest)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported")
        self.assertNotEqual(0, self.run_brief("--force").returncode)
        self.assertEqual("safe", dest.read_text(encoding="utf-8"))

    def test_cdn_requires_explicit_opt_in(self) -> None:
        self.assertEqual(0, self.run_brief("--allow-cdn").returncode)
        text = (self.dir / "verification-brief.html").read_text(encoding="utf-8")
        self.assertIn("const fallback = true", text)


if __name__ == "__main__":
    unittest.main()
