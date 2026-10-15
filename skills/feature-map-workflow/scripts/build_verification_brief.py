#!/usr/bin/env python3
"""Create a focused, human-reviewable verification brief from an existing Feature Map.

No tests or user actions are executed. The optional work plan is a disposable
session plan, not a new source of expected business behavior.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import tempfile
import os
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

MAX_INPUT = 2 * 1024 * 1024
MAX_PLAN = 128 * 1024
CDN = "https://cdn.jsdelivr.net/npm/mermaid@12.0.0/dist/mermaid.min.js"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def text(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    return " ".join((node.findtext(path) or "").split())


def read_xml(path: Path) -> ET.Element:
    if not path.is_file() or path.stat().st_size > MAX_INPUT:
        raise ValueError("Feature Map is missing or exceeds 2 MiB")
    raw = path.read_bytes()
    if re.search(br"<!DOCTYPE\b|<!ENTITY\b", raw, flags=re.I):
        raise ValueError("DOCTYPE and ENTITY declarations are forbidden")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid Feature Map XML: {exc}") from exc
    if root.tag != "featureMap":
        raise ValueError("Expected a featureMap root")
    if not text(root, "./meta/feature") or not text(root, "./meta/system"):
        raise ValueError("Feature Map system and feature must be present")
    return root


def choose_focus(root: ET.Element, focus: str | None) -> ET.Element | None:
    cases = root.findall("./useCase")
    if focus:
        match = [x for x in cases if x.get("id") == focus]
        if len(match) != 1:
            raise ValueError(f"Unknown or duplicated use case ID: {focus}")
        return match[0]
    if len(cases) > 1:
        raise ValueError("Specify --use-case for a multi-use-case Feature Map")
    return cases[0] if cases else None


def choose_cases(root: ET.Element, selected: list[str], multi_uc: bool) -> list[ET.Element]:
    catalog = root.findall("./verify/case")
    ids = [x.get("id", "") for x in catalog]
    if len(ids) != len(set(ids)) or any(not i for i in ids):
        raise ValueError("Verification cases require distinct nonempty IDs")
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate --case ID")
    if multi_uc and not selected:
        raise ValueError("Specify --case IDs when the map contains multiple use cases")
    names = selected or ids
    if not names:
        raise ValueError("Feature Map has no verification cases")
    lookup = dict(zip(ids, catalog))
    missing = set(names) - set(lookup)
    if missing:
        raise ValueError(f"Unknown verification case ID: {', '.join(sorted(missing))}")
    return [lookup[i] for i in names]


@dataclass(frozen=True)
class Diagram:
    id: str
    title: str
    role: str
    source: str
    reason: str


ROLE_INFO = {
    "business": ("業務フロー", "担当者の操作・判断・例外を把握する"),
    "data": ("データフロー", "入力、参照・更新先、外部への影響を確認する"),
    "er": ("ER図", "テーブル、キー、保存データ間の関連を確認する"),
    "state": ("状態遷移図", "状態と操作の可否、遷移条件を確認する"),
    "sequence": ("シーケンス図", "モジュール間の順序と連携を確認する"),
    "class": ("クラス図", "責務とオブジェクト構造を確認する"),
    "other": ("補足図", "関連する構造・処理を補足する"),
}


def classify_diagram(element: ET.Element) -> str:
    kind = element.get("kind", "").lower()
    title = (element.get("title") or "").lower()
    source = (element.text or "").lstrip()
    if kind == "er" or source.startswith("erDiagram"):
        return "er"
    if kind == "state" or source.startswith("stateDiagram"):
        return "state"
    if kind == "sequence" or source.startswith("sequenceDiagram"):
        return "sequence"
    if kind == "class" or source.startswith("classDiagram"):
        return "class"
    if "データフロー" in title or "data flow" in title or "dfd" in title:
        return "data"
    if kind in ("flowchart", "activity") or source.startswith("flowchart"):
        return "business"
    return "other"


def choose_diagrams(root: ET.Element, focus: ET.Element | None,
                    selected: list[str]) -> list[Diagram]:
    available = root.findall("./diagrams/diagram")
    ids = [d.get("id", "") for d in available]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise ValueError("Diagram IDs must be distinct and nonempty for a brief")
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate --diagram ID")
    if len(selected) > 3:
        raise ValueError("Select at most 3 diagrams")
    focus_id = focus.get("id", "") if focus is not None else ""
    eligible = []
    for d in available:
        title = d.get("title", d.get("id", ""))
        mentioned = re.findall(r"\bUC[-_][A-Za-z0-9_-]+\b", title, flags=re.I)
        if focus_id and mentioned and focus_id not in mentioned:
            continue
        role = classify_diagram(d)
        label, reason = ROLE_INFO[role]
        eligible.append(Diagram(d.get("id", ""), title or label, role,
                                (d.text or "").strip(), reason))
    mapping = {d.id: d for d in eligible}
    if selected:
        missing = set(selected) - set(mapping)
        if missing:
            raise ValueError("Unknown or out-of-focus diagram ID: " + ", ".join(sorted(missing)))
        return [mapping[i] for i in selected]
    # Distinct purposes, not a diagram dump. Priority follows what testers ask first.
    priority = ("business", "data", "er", "state", "sequence", "class", "other")
    picked = []
    for role in priority:
        if len(picked) == 3:
            break
        match = next((d for d in eligible if d.role == role), None)
        if match is not None:
            picked.append(match)
    return picked


def required_string(item: dict, key: str, location: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}.{key} must be a nonempty string")
    return value.strip()


def required_list(item: dict, key: str, location: str) -> list[str]:
    value = item.get(key)
    if (not isinstance(value, list) or not value or
            any(not isinstance(s, str) or not s.strip() for s in value)):
        raise ValueError(f"{location}.{key} must be a nonempty list of strings")
    return [s.strip() for s in value]


def read_plan(path: Path | None, case_ids: list[str]) -> dict | None:
    if path is None:
        return None
    if not path.is_file() or path.stat().st_size > MAX_PLAN:
        raise ValueError("Plan is missing or exceeds 128 KiB")
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Invalid plan JSON: {exc}") from exc
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("Plan must use version 1")
    required_string(plan, "environment", "plan")
    required_string(plan, "sourceRevision", "plan")
    required_list(plan, "preflight", "plan")
    sessions = plan.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        raise ValueError("Plan requires at least one human session")
    seen_steps = []
    seen_sessions = set()
    for index, session in enumerate(sessions):
        label = f"sessions[{index}]"
        if not isinstance(session, dict):
            raise ValueError(f"{label} must be an object")
        sid = required_string(session, "id", label)
        if sid in seen_sessions:
            raise ValueError(f"Repeated session ID: {sid}")
        seen_sessions.add(sid)
        for key in ("title", "actor"):
            required_string(session, key, label)
        for key in ("sharedSetup", "stopOn", "cleanup"):
            required_list(session, key, label)
        steps = session.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"{label}.steps must be nonempty")
        for i, step in enumerate(steps):
            where = f"{label}.steps[{i}]"
            if not isinstance(step, dict):
                raise ValueError(f"{where} must be an object")
            cid = required_string(step, "caseId", where)
            for field in ("resetBefore", "action", "capture"):
                required_string(step, field, where)
            seen_steps.append(cid)
    if len(seen_steps) != len(set(seen_steps)):
        raise ValueError("Each verification case may appear only once in the plan")
    if set(seen_steps) != set(case_ids):
        raise ValueError("Plan steps must cover exactly the selected case IDs")
    return plan


def li(lines: list[str]) -> str:
    return "<ol>" + "".join(f"<li>{esc(x)}</li>" for x in lines) + "</ol>"


def render(root: ET.Element, focus: ET.Element | None,
           cases: list[ET.Element], diagrams: list[Diagram],
           plan: dict | None, allow_cdn: bool) -> str:
    title = text(root, "./meta/feature")
    uc_id = focus.get("id", "") if focus is not None else ""
    header = f"""<header><p class="eyebrow">機能理解・検証ブリーフ / 作業ディレクション</p>
<h1>{esc(title)}</h1><p>{esc(text(root, "./meta/system"))} · Feature Map {esc(root.get("state", ""))} · {esc(uc_id)}</p>
<p class="notice">この資料は作業の準備計画であり、検証実施・承認・合格の証明ではありません。</p></header>"""
    uc = ""
    if focus is not None:
        uc = (f"<p><strong>対象シナリオ：</strong>{esc(text(focus, 'scenario'))}</p>"
              f"<p><strong>入力：</strong>{esc(text(focus, 'input'))}　"
              f"<strong>結果：</strong>{esc(text(focus, 'outcome'))}</p>")
    overview = (f'<section><h2>1. この機能で理解すること</h2>'
                f'<p><strong>目的：</strong>{esc(text(root, "./goal/purpose"))}</p>{uc}'
                f'<p><strong>対象：</strong>{esc(text(root, "./goal/scope"))}　'
                f'<strong>対象外：</strong>{esc(text(root, "./goal/exclude"))}</p></section>')

    diagram_items = []
    for d in diagrams:
        diagram_items.append(
            f'<details class="diagram"><summary>{esc(ROLE_INFO[d.role][0])}：{esc(d.title)}</summary>'
            f'<p class="muted">{esc(d.reason)} · {esc(d.id)}</p>'
            f'<pre class="mermaid">{esc(d.source)}</pre></details>'
        )
    diagram_section = (f'<section><h2>2. 今回読む図 <small>({len(diagrams)}件)</small></h2>'
                       '<p>対象機能と検証目的に関係する図を優先表示します。'
                       '図は既存Feature Mapの記述であり、未検証の関連を自動的に確定するものではありません。</p>'
                       + (''.join(diagram_items) +
                          '<p id="mermaid-status" class="muted">図を展開するとローカルのMermaidを読み込みます。</p>'
                          if diagrams else '<p class="notice">該当する図がありません。推測による図は生成しません。</p>')
                       + '</section>')

    case_rows = []
    case_by_id = {}
    for c in cases:
        cid = c.get("id", "")
        case_by_id[cid] = c
        evidence = ", ".join(x.get("ref", "") for x in c.findall("evidence"))
        case_rows.append(
            f"<tr><th scope='row'>{esc(cid)}</th><td>{esc(text(c, 'condition'))}</td>"
            f"<td>{esc(text(c, 'expect'))}</td><td>{esc(c.get('status', ''))}"
            f"<br><small>Feature Map記録（今回の判定ではない）</small></td>"
            f"<td>{esc(evidence) if evidence else '—'}</td></tr>"
        )
    table = ("<section><h2>3. ケース別の検証観点</h2>"
             "<div class='scroll'><table><thead><tr><th>ID</th><th>条件</th><th>期待結果</th>"
             "<th>既存記録</th><th>証跡参照</th></tr></thead><tbody>"
             + "".join(case_rows) + "</tbody></table></div></section>")

    if plan is None:
        sessions = ('<section><h2>4. 人の作業ディレクション</h2><p class="blocker">'
                    'HALT：作業計画が未指定です。共通環境・操作・ケース間の初期化を'
                    '確認するまで、人に実行依頼を出さないでください。</p>'
                    '<p>--plan で承認前の作業手順案を渡すと、検証IDを維持したまま'
                    '複数ケースを1回の作業セッションへまとめられます。</p></section>')
    else:
        session_parts = []
        for session in plan["sessions"]:
            rows = []
            for number, step in enumerate(session["steps"], 1):
                c = case_by_id[step["caseId"]]
                rows.append(
                    f"<li><strong>{esc(step['caseId'])}</strong>：{esc(step['action'])}"
                    f"<p><b>ケースの初期化：</b>{esc(step['resetBefore'])}</p>"
                    f"<p><b>期待結果：</b>{esc(text(c, 'expect'))}</p>"
                    f"<p><b>証跡取得：</b>{esc(step['capture'])}</p>"
                    "<p class='muted'>実測・判定は検証ID別に外部の記録へ残す"
                    "（このHTMLには実行結果を保存しない）。</p></li>"
                )
            session_parts.append(
                f'<article><h3>{esc(session["id"])}：{esc(session["title"])}'
                f' <small>（担当：{esc(session["actor"])}）</small></h3>'
                '<h4>共通準備（1回）</h4>' + li(session["sharedSetup"])
                + '<h4>人が実施する順序・ケース別リセット</h4><ol>'
                + "".join(rows) + "</ol><h4>中止条件</h4>" + li(session["stopOn"])
                + "<h4>終了時の復旧・片付け</h4>" + li(session["cleanup"])
                + "</article>"
            )
        sessions = (
            '<section><h2>4. 人の作業ディレクション</h2>'
            f'<p><strong>環境：</strong>{esc(plan["environment"])}　'
            f'<strong>対象リビジョン：</strong>{esc(plan["sourceRevision"])}　'
            f'<strong>まとめる作業機会：</strong>{len(plan["sessions"])}回</p>'
            '<p class="notice">事前準備・承認・データ隔離は、この資料を出力しただけでは完了しません。'
            '担当者が実環境とリビジョンを確認してください。</p>'
            '<h3>事前チェック（人を呼ぶ前）</h3>' + li(plan["preflight"])
            + "".join(session_parts) + "</section>"
        )

    issues = root.findall("./open/item")
    issue_rows = []
    for issue in issues:
        issue_rows.append(
            f"<li><strong>{esc(issue.get('id', ''))}"
            f" [{esc(issue.get('impact', ''))}]：</strong>{esc(' '.join((issue.text or '').split()))}"
            f"<br><small>次の確認：{esc(issue.get('next', ''))}</small></li>"
        )
    open_section = ("<section><h2>5. 不明点・安全な終了条件</h2>"
                    + ("<ul>" + "".join(issue_rows) + "</ul>" if issue_rows else
                       "<p>Feature Mapの未解決事項はありません（実環境の安全性は別途確認）。</p>")
                    + "<p>ケースの合否は既存の結果契約・証跡により個別に管理し、"
                    "一括操作を理由に独立検証を省略しません。"
                    "未知の期待結果、初期化失敗、環境違い、予期しないDB更新では作業を中止します。</p>"
                    "</section>")

    loader = ""
    if diagrams:
        fallback = "true" if allow_cdn else "false"
        loader = """<script>
(function () {
  const fallback = """ + fallback + """;
  const status = document.getElementById('mermaid-status');
  let started = false;
  function fail() {
    if (status) status.textContent = 'Mermaid未描画：図のソースを表示しています。ローカルのfeature-map.mermaid.min.jsを配置してください。';
  }
  async function run() {
    try {
      window.mermaid.initialize({startOnLoad:false,securityLevel:'strict',
                                 layout:'dagre',theme:'default',look:'classic'});
      await window.mermaid.run({querySelector:'.mermaid'});
      if (status) status.textContent = 'Mermaid描画済み';
    } catch (_) { fail(); }
  }
  function load(url, next) {
    const tag = document.createElement('script');
    tag.src = url;
    tag.onload = run;
    tag.onerror = () => next ? load(next, null) : fail();
    document.head.appendChild(tag);
  }
  document.querySelectorAll('details.diagram').forEach(function (node) {
    node.addEventListener('toggle', function () {
      if (!node.open || started) return;
      started = true;
      if (window.mermaid) run();
      else load('feature-map.mermaid.min.js', fallback ?
                'https://cdn.jsdelivr.net/npm/mermaid@12.0.0/dist/mermaid.min.js' : null);
    });
  });
})();
</script>"""

    return ("""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + esc(title) + """ - 機能理解・検証ブリーフ</title>
<style>
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:1100px;
     padding:1.1rem;margin:1rem auto;color:#202124;line-height:1.55}
h1{font-size:1.65rem}h2{font-size:1.15rem;margin:0 0 .65rem}
h3{font-size:1.05rem}h4{margin:.7rem 0 .2rem}
section,article{border:1px solid #dedfe2;border-radius:.6rem;padding:1rem;margin:1rem 0}
header{border-bottom:2px solid #ddd}.eyebrow,.muted,small{color:#626a73}
.notice,.blocker{padding:.6rem .85rem;background:#f4f5f7;border-radius:.4rem}
.blocker{border-left:3px solid #a43f36}p{margin:.5rem 0}
summary{cursor:pointer;font-weight:600}details.diagram{border-top:1px solid #eee;padding:.55rem 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f8f8f8;padding:.8rem}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:600px}
th,td{border-bottom:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}
li{margin:.45rem 0}li p{margin:.2rem 0 0 .4rem}
@media print{body{max-width:none}section,article{break-inside:avoid}}
</style></head><body>"""
            + header + overview + diagram_section + table + sessions + open_section
            + '<footer class="muted">元データ：Feature Map XML / 作業計画は非正本。出力時に検証・承認・データ操作は行っていません。</footer>'
            + loader + '</body></html>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-map", required=True, type=Path)
    parser.add_argument("--use-case", help="Focus on a specific use case ID")
    parser.add_argument("--case", action="append", default=[], help="Include one verification ID; repeat as needed")
    parser.add_argument("--diagram", action="append", default=[], help="Explicit diagram ID; max three")
    parser.add_argument("--plan", type=Path, help="Optional, reviewable human-work session JSON")
    parser.add_argument("--output", type=Path, default=Path("verification-brief.html"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-cdn", action="store_true",
                        help="Allow fallback to external Mermaid CDN (default: local only)")
    args = parser.parse_args()
    source = args.feature_map.resolve()
    base = source.parent
    raw_out = base / args.output if not args.output.is_absolute() else args.output
    if raw_out.is_symlink():
        parser.error("Refusing symlink output")
    output = raw_out.resolve()
    if not output.is_relative_to(base) or output.suffix.lower() != ".html":
        parser.error("Output must be an HTML file inside the Feature Map directory")
    if output.exists() and (not output.is_file() or not args.force):
        parser.error("Output exists; pass --force to replace a regular HTML file")
    try:
        root = read_xml(source)
        focus = choose_focus(root, args.use_case)
        cases = choose_cases(root, args.case, len(root.findall("./useCase")) > 1)
        diagrams = choose_diagrams(root, focus, args.diagram)
        plan = read_plan(args.plan, [c.get("id", "") for c in cases])
        markup = render(root, focus, cases, diagrams, plan, args.allow_cdn)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         prefix=".verification-brief-", suffix=".tmp",
                                         dir=output.parent, delete=False) as out:
            temp_path = Path(out.name)
            out.write(markup)
        os.replace(temp_path, output)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    print(f"{output}: {len(cases)} cases, {len(diagrams)} diagrams, "
          f"{len(plan['sessions']) if plan else 0} directed sessions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
