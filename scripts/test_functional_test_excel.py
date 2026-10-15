#!/usr/bin/env python3
"""Synthetic tests for the user-supplied fixed Excel functional-test layout."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_functional_test_excel.py"

class WorkbookTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.template = self.root / "template.xlsx"
        w = Workbook()
        cover = w.active
        cover.title = "表紙"
        listing = w.create_sheet("検証リスト")
        detail = w.create_sheet("FT-01")
        detail["H30"] = '=IF(F6="対象","未実施","未判定")'
        detail["B31"] = '=IF(B16="","未設計","設計済")'
        detail["B5"] = "FT-01"
        detail["A40"] = "E-01"
        listing["A7"] = "='FT-01'!B5"
        w.save(self.template)
        self.xml = self.root / "feature-map.xml"
        self.xml.write_text("""<featureMap version="1.3" mode="change" state="draft">
<meta><system>架空システム</system><feature>受付</feature></meta>
<goal><purpose>依頼受付</purpose></goal>
<useCase id="UC-ONE"><scenario>依頼する</scenario><input>商品ID</input></useCase>
<verify><case id="V-ONE" type="normal" status="not-run">
<condition>通常入力</condition><expect>受付番号を表示</expect>
</case></verify></featureMap>""", encoding="utf-8")

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str,args)],
                              capture_output=True,text=True,timeout=25)

    def plan(self):
        target = self.root / "plan.xlsx"
        proc = self.cli("plan","--template",self.template,"--feature-map",self.xml,
                        "--revision","sha-test","--output",target)
        self.assertEqual(0,proc.returncode,proc.stderr)
        return target

    def test_plan_preserves_formula_and_pending_decision(self):
        target=self.plan()
        w=load_workbook(target)
        self.assertEqual("f",w["FT-01"]["H30"].data_type)
        self.assertEqual("f",w["FT-01"]["B31"].data_type)
        self.assertEqual("未判定",w["FT-01"]["F6"].value)
        self.assertEqual("通常入力",w["FT-01"]["B16"].value)
        self.assertIsNone(w["FT-01"]["H16"].value)
        self.assertIn("VERIFY:V-ONE",w["FT-01"]["B7"].value)
        self.assertEqual("sha-test",w["表紙"]["K19"].value)

    def test_case_count_above_ten_preserves_footer(self):
        tree=ET.parse(self.xml)
        node=tree.getroot().find("verify")
        node.clear()
        for idx in range(12):
            c=ET.SubElement(node,"case",id=f"V-{idx}",type="normal",status="not-run")
            ET.SubElement(c,"condition").text=f"case {idx}"
            ET.SubElement(c,"expect").text="returns OK"
        tree.write(self.xml,encoding="utf-8")
        plan=self.plan()
        w=load_workbook(plan)
        self.assertIn("FT-21",w.sheetnames)
        self.assertEqual("='FT-21'!B5",w["検証リスト"]["A27"].value)

    def test_result_requires_matching_revision_and_step_evidence(self):
        target=self.plan()
        p=self.root/"result.json"
        base=dict(schemaVersion=1,runId="R-1",verifyCaseId="V-ONE",
                  sourceRevision="different",status="passed",checks=[],evidence=[])
        p.write_text(json.dumps(base),encoding="utf-8")
        output=self.root/"resulted.xlsx"
        bad=self.cli("results","--workbook",target,"--result",p,"--output",output)
        self.assertNotEqual(0,bad.returncode)
        self.assertFalse(output.exists())
        base["sourceRevision"]="sha-test"
        p.write_text(json.dumps(base),encoding="utf-8")
        good=self.cli("results","--workbook",target,"--result",p,"--output",output)
        self.assertEqual(0,good.returncode,good.stderr)
        w=load_workbook(output)
        self.assertIsNone(w["FT-01"]["H16"].value)
        self.assertIn("R-1",w["FT-01"]["B26"].value)

    def test_formula_injection_and_dtd_are_refused(self):
        tree=ET.parse(self.xml)
        tree.getroot().find("./verify/case/condition").text="=HYPERLINK(1)"
        tree.write(self.xml,encoding="utf-8")
        w=load_workbook(self.plan())
        self.assertTrue(w["FT-01"]["B16"].value.startswith("'="))
        self.xml.write_text("<!DOCTYPE featureMap><featureMap/>",encoding="utf-8")
        failed=self.cli("plan","--template",self.template,"--feature-map",self.xml,
                        "--revision","sha-test","--output",self.root/"other.xlsx")
        self.assertNotEqual(0,failed.returncode)

if __name__=="__main__":
    unittest.main()
