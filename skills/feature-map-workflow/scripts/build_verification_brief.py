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
    "activity": ("アクティビティ図・業務フロー", "担当者の判断、分岐、正常・異常結果を確認する"),
    "usecase": ("ユースケース図", "利用者・権限と機能の対象範囲を確認する"),
    "data": ("データフロー図", "入力からDB・ファイル・外部システムまでの流れを追う"),
    "er": ("ER図", "テーブル間の関係と更新対象、キーを確認する"),
    "state": ("状態遷移図", "操作前後の状態と遷移条件を確認する"),
    "sequence": ("シーケンス図", "モジュールや外部連携の呼出順序を確認する"),
    "class": ("クラス図", "責務、型・オブジェクト間の構造を確認する"),
    "architecture": ("構成図", "サービス・プロセスなどの境界を確認する"),
    "context": ("システムコンテキスト図", "利用者と外部システムの境界を確認する"),
    "component": ("コンポーネント図", "機能とモジュールの責務・依存を確認する"),
    "dependency": ("依存関係図", "変更の影響を受ける参照元と参照先を確認する"),
    "lineage": ("データリネージ図", "データの由来・変換と伝播先を確認する"),
    "crud": ("CRUDマトリクス", "機能ごとのデータ参照・更新範囲を確認する"),
    "decision": ("決定表", "条件の組合せと期待結果を確認する"),
    "traceability": ("トレーサビリティ図", "要件・実装・検証・証跡の対応を確認する"),
    "deployment": ("配置図", "実行環境と通信経路を確認する"),
    "timing": ("タイミング図", "待機時間とイベント順序を確認する"),
    "batch": ("ジョブ依存図", "ジョブの先行後続と失敗波及を確認する"),
    "other": ("補足図", "検証上重要な他の構造を確認する"),
}


def classify_diagram(element: ET.Element) -> str:
    kind = element.get("kind", "").lower()
    title = (element.get("title") or "").lower()
    source = (element.text or "").lstrip()
    # Intent labels are encoded in diagram titles; the XSD has no extra kinds.
    # Check specific categories first so a generic flowchart stays a flowchart.
    named = (
        ("lineage", r"データリネージ|data lineage|lineage"),
        ("crud", r"crud|更新マトリクス"),
        ("decision", r"決定表|decision table"),
        ("traceability", r"トレーサビリティ|traceability"),
        ("context", r"システムコンテキスト|system context|c4 level 1"),
        ("component", r"コンポーネント|component"),
        ("dependency", r"依存関係|dependency|call graph"),
        ("deployment", r"配置図|deployment"),
        ("timing", r"タイミング図|timing diagram"),
        ("batch", r"ジョブ依存|バッチ依存|job dependency"),
    )
    for role, pattern in named:
        if re.search(pattern, title):
            return role
    if kind == "er" or source.startswith("erDiagram"):
        return "er"
    if kind == "state" or source.startswith("stateDiagram"):
        return "state"
    if kind == "sequence" or source.startswith("sequenceDiagram"):
        return "sequence"
    if kind == "class" or source.startswith("classDiagram"):
        return "class"
    if "データフロー" in title or "data flow" in title or re.search(r"\bdfd\b", title):
        return "data"
    if kind == "usecase":
        return "usecase"
    if kind == "architecture":
        return "architecture"
    if kind in ("activity", "flowchart") or source.startswith(("flowchart", "graph ")):
        return "activity"
    return "other"


def need_roles(root: ET.Element, cases: list[ET.Element]) -> set[str]:
    """Recommend diagram roles from declared test purposes, never inferred guarantees."""
    types = {c.get("type", "") for c in cases}
    words = " ".join(
        text(c, "condition") + " " + text(c, "expect") for c in cases
    ).lower()
    refs = root.findall("./sourceMap/ref")
    kinds = {ref.get("kind", "") for ref in refs}
    touched_tables = {
        ref.get("target", "") for ref in refs if ref.get("kind") in ("table", "view")
    }
    writes = any(ref.get("access") in ("write", "read-write") for ref in refs)
    has_external = bool(kinds.intersection({"api", "external", "batch"}))
    roles = {"activity"}  # Focused scenario/decision comes first.
    if writes or has_external or kinds.intersection({"table", "view", "query"}):
        roles.add("data")
    if len(touched_tables) >= 2:
        roles.update({"er", "crud"})
    if writes or has_external:
        roles.add("lineage")
    if has_external:
        roles.add("context")
    if "batch" in kinds:
        roles.add("batch")
    if re.search(r"境界|boundary|サービス|service|構成", words):
        roles.update({"context", "component"})
    if re.search(r"変更影響|impact|依存|dependency", words):
        roles.update({"dependency", "traceability"})
    if re.search(r"条件組合せ|組み合わせ|matrix|decision table|決定表", words):
        roles.add("decision")
    if re.search(r"証跡|traceability|トレーサビリティ|要件.*テスト", words):
        roles.add("traceability")
    if re.search(r"配置|deployment|ネットワーク|network", words):
        roles.add("deployment")
    if re.search(r"遅延|待機|latency|timing|時間制約", words):
        roles.add("timing")
    if types.intersection({"state", "duplicate"}) or re.search(
        r"状態|遷移|status|state|有効|無効|完了済", words
    ):
        roles.add("state")
    if types.intersection({"retry", "duplicate"}) or has_external or re.search(
        r"再試行|リトライ|タイムアウト|timeout|retry|非同期|queue|連携|call order", words
    ):
        roles.add("sequence")
    if "permission" in types or re.search(r"権限|ロール|actor|role|permission", words):
        roles.add("usecase")
    if re.search(r"クラス|継承|interface|class|object|オブジェクト|責務", words):
        roles.add("class")
    if len(kinds.intersection({"api", "external", "batch", "procedure"})) >= 2:
        roles.add("architecture")
    return roles


def choose_diagrams(root: ET.Element, focus: ET.Element | None,
                    selected: list[str], cases: list[ET.Element]) -> list[Diagram]:
    available = root.findall("./diagrams/diagram")
    ids = [d.get("id", "") for d in available]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise ValueError("Diagram IDs must be distinct and nonempty for a brief")
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate --diagram ID")
    focus_id = focus.get("id", "") if focus is not None else ""
    eligible = []
    for d in available:
        title = d.get("title", d.get("id", ""))
        mentioned = re.findall(r"\bUC[-_][A-Za-z0-9_-]+\b", title, flags=re.I)
        if focus_id and mentioned and focus_id not in mentioned:
            continue
        role = classify_diagram(d)
        if not (d.text or "").strip():
            continue
        label, reason = ROLE_INFO[role]
        eligible.append(Diagram(d.get("id", ""), title or label, role,
                                (d.text or "").strip(), reason))
    mapping = {d.id: d for d in eligible}
    if selected:
        missing = set(selected) - set(mapping)
        if missing:
            raise ValueError("Unknown or out-of-focus diagram ID: " + ", ".join(sorted(missing)))
        return [mapping[i] for i in selected]
    needed = need_roles(root, cases)
    # Use every relevant documented view, regardless of count; do not fabricate diagrams.
    # Avoid rendering identical Mermaid bodies several times.
    used_sources: set[str] = set()
    picked: list[Diagram] = []
    for d in eligible:
        if d.role in needed and d.source not in used_sources:
            picked.append(d)
            used_sources.add(d.source)
    # A non-data feature may only supply a use-case diagram; retain a useful fallback.
    if not picked and eligible:
        picked.append(eligible[0])
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
    for number, d in enumerate(diagrams):
        # First selected diagram is visible; others are available without overwhelming the page.
        opened = " open" if number == 0 else ""
        diagram_items.append(
            f'<details class="diagram"{opened}><summary>{esc(ROLE_INFO[d.role][0])}：{esc(d.title)}</summary>'
            f'<p class="muted">選定理由：{esc(d.reason)} · {esc(d.id)}</p>'
            f'<pre class="mermaid">{esc(d.source)}</pre></details>'
        )
    diagram_section = (f'<section><h2>2. 今回読む図 <small>({len(diagrams)}件)</small></h2>'
                       '<p>件数の固定上限はありません。検証目的に関係する既存図を選定し、'
                       '先頭の図を表示します。未確認の関係を自動確定・創作しません。</p>'
                       + (''.join(diagram_items) +
                          '<p id="mermaid-status" class="muted">図を開くとMermaidを読み込みます。'
                          'ライブラリを利用できない場合はソースを表示します。</p>'
                          if diagrams else '<p class="notice">根拠のある関連図がありません。'
                          '図の作成に必要なソース・DB情報の確認を検討してください。</p>')
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
            for step in session["steps"]:
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
  let ready = null;
  let initialized = false;
  function fail() {
    if (status) status.textContent = 'Mermaid未描画：図のソースを表示しています。必要なら同じフォルダにfeature-map.mermaid.min.jsを配置してください。';
  }
  function library(url, next, resolve, reject) {
    const tag = document.createElement('script');
    tag.src = url;
    tag.onload = resolve;
    tag.onerror = function () {
      if (next) library(next, null, resolve, reject);
      else reject(new Error('Mermaid unavailable'));
    };
    document.head.appendChild(tag);
  }
  function ensure() {
    if (ready) return ready;
    ready = new Promise(function (resolve, reject) {
      if (window.mermaid) { resolve(); return; }
      library('feature-map.mermaid.min.js', fallback ?
              'https://cdn.jsdelivr.net/npm/mermaid@12.0.0/dist/mermaid.min.js' : null,
              resolve, reject);
    });
    return ready;
  }
  async function renderPanel(panel) {
    if (!panel.open) return;
    const target = panel.querySelector('pre.mermaid');
    if (!target || target.dataset.done) return;
    try {
      await ensure();
      if (!initialized) {
        window.mermaid.initialize({startOnLoad:false,securityLevel:'strict',
                                   layout:'dagre',theme:'default',look:'classic'});
        initialized = true;
      }
      await window.mermaid.run({nodes:[target]});
      target.dataset.done = 'true';
      if (status) status.textContent = '選択した図を描画しました。';
    } catch (_) { fail(); }
  }
  document.querySelectorAll('details.diagram').forEach(function (panel) {
    panel.addEventListener('toggle', function () { renderPanel(panel); });
    if (panel.open) renderPanel(panel);
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
    parser.add_argument("--diagram", action="append", default=[], help="Select diagram IDs explicitly, repeat without count limit")
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
        diagrams = choose_diagrams(root, focus, args.diagram, cases)
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
