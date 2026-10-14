#!/usr/bin/env python3
"""Check business-first and disclosure-based XSLT rendering with a synthetic map."""

from __future__ import annotations

import unittest
from pathlib import Path

from lxml import etree

STYLESHEET = (
    Path(__file__).resolve().parents[1] / "skills" / "feature-map-workflow"
    / "assets" / "feature-map.xsl"
)


class FeatureMapViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.transform = etree.XSLT(etree.parse(str(STYLESHEET)))

    def render(self, cases=4, rules=6, diagrams=True):
        use_cases = "".join(
            f'<useCase id="U{i}"><scenario>Scenario {i}</scenario>'
            f'<input>Input {i}</input><outcome>Outcome {i}</outcome>'
            f'<sample>Sample {i}</sample></useCase>' for i in range(cases)
        )
        knowledge = "".join(
            f'<rule id="R{i}">Rule {i}</rule>' for i in range(rules)
        )
        diagrams_xml = (
            '<diagrams><diagram id="D1" kind="sequence">'
            'sequenceDiagram&#10;A-&gt;&gt;B: hi'
            '</diagram></diagrams>' if diagrams else ""
        )
        source = f'''<featureMap version="1.3" mode="change" state="ready">
<meta><system>Example</system><feature>Feature</feature></meta>
<goal><purpose>Purpose</purpose><scope>Only target slice</scope></goal>
{use_cases}
<sourceMap><ref kind="entry" target="example:Entry"/></sourceMap>
{diagrams_xml}
<knowledge>{knowledge}</knowledge>
<verify><case id="V1" status="passed" type="normal">
<condition>Scenario</condition><expect>Result</expect>
<observe>Observed result</observe><evidence ref="tests/fixture.log"/>
</case></verify>
<open><item id="O1" impact="high" type="business-rule" next="Ask domain owner">Unconfirmed</item></open>
</featureMap>'''
        document = etree.fromstring(source.encode("utf-8"))
        return etree.HTML(str(self.transform(document)))

    def test_business_first_and_progressive_details(self) -> None:
        doc = self.render()
        body = doc.xpath("//body")[0]
        top_tags = [node.tag for node in body if isinstance(node.tag, str)]
        self.assertIn("header", top_tags)
        self.assertLess(top_tags.index("h2"), top_tags.index("details"))
        body_html = etree.tostring(body, encoding="unicode", method="html")
        self.assertLess(body_html.index("Knowledge"), body_html.index("Source Map"))
        self.assertLess(body_html.index("Unconfirmed"), body_html.index("Source Map"))
        self.assertEqual(1, len(doc.xpath("//details[summary[contains(., 'Source Map')]]")))
        self.assertEqual(1, len(doc.xpath("//details[summary[contains(., 'Verify')]]")))
        self.assertEqual(1, len(doc.xpath("//details[summary[contains(., 'Diagrams')]]")))
        self.assertFalse(doc.xpath("//details[@open]"), "heavy details should start collapsed")
        self.assertEqual(3, len(doc.xpath("//body/h2[contains(., 'Use Cases')]/following-sibling::div[contains(@class,'use-case')]")))
        self.assertEqual(1, len(doc.xpath("//details[@class='more']/summary[contains(., 'More use cases')]")))
        self.assertEqual(1, len(doc.xpath("//details[@class='more']/summary[contains(., 'More knowledge')]")))
        self.assertIn("Input 0", body_html)
        self.assertIn("Outcome 0", body_html)
        self.assertIn("tests/fixture.log", body_html)

    def test_mermaid_loads_only_when_opened(self) -> None:
        html = etree.tostring(self.render(), encoding="unicode", method="html")
        self.assertIn("addEventListener('toggle', startWhenOpened)", html)
        self.assertIn("if (!diagramPanel || !diagramPanel.open || started) return;", html)
        self.assertIn("feature-map.mermaid.min.js", html)
        self.assertIn("mermaid@12.0.0", html)
        self.assertIn("securityLevel: 'strict'", html)

    def test_sections_omitted_when_no_data(self) -> None:
        doc = self.render(cases=0, rules=0, diagrams=False)
        self.assertFalse(doc.xpath("//details[summary[contains(., 'Diagrams')]]"))
        self.assertFalse(doc.xpath("//details[@class='more']"))
        self.assertFalse(doc.xpath("//script"))
        self.assertTrue(doc.xpath("//details[summary[contains(., 'Source Map')]]"))


if __name__ == "__main__":
    unittest.main()
