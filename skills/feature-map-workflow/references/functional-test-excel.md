# 機能テストExcelテンプレート統合

機能テストの対外共有・実施記録を既存Excelへまとめる場合に使います。対応する `test_template.xlsx` をローカルで用意し、`--template` で指定してください。公開リポジトリに原本は同梱していません。生成CLIは **表紙 / 検証リスト / FT-01～FT-10** の対応レイアウト・数式・入力規則を維持します。

顧客提出が目的なら、先に [顧客提出資料の作成](customer-deliverables.md) で読者・用途・提出項目を決めます。以下のCLIは内部の技術用帳票を作る手段です。顧客版の別生成・全パッケージ検査・数式/表示確認・提出候補のhash固定までを同ガイドに従って行います。

## 計画の作成

先に [Test Strategy](test-strategy.md#select-changed-behavior-before-selecting-cases) で、変更箇所と影響経路、プログラムが保証すべき動作、条件ごとの優先度を決めます。シート単位だけでなく、入力条件も同値クラス・重要境界・状態変化の代表へ絞ります。既存機能の全回帰、環境構築・接続・OS設定を顧客用の機能試験へ混ぜません。既存の内部試験で証明する重要な保証は参照で結び、画面Excelだけで全保証が揃ったとしません。

既存帳票の棚卸しでは原本と旧結果を残し、条件ごとの採否・理由・代替条件・保証範囲を内部で追跡します。期待結果や観測方法を改める場合は差分と既存の権限を明示し、旧条件を合格へ上書きしません。不合格を削減理由にせず、既知の不合格と未確認の重要保証を改訂後も見える状態にします。承認済みの今回対象条件を新しい顧客版へ出力します。契約・受入上必須の条件は優先度だけで除外しません。未変更の条件番号は維持し、期待結果・観測方法を改めた条件には新しい番号を付けて旧条件へ対応づけます。顧客用の表現と漏えい検査は [Customer Deliverables](customer-deliverables.md) に従います。

```sh
python -m pip install openpyxl
python scripts/build_functional_test_excel.py plan \
  --template /path/to/test_template.xlsx \
  --feature-map examples/fictional-stock-request/feature-map.xml \
  --use-case UC-SUBMIT \
  --revision <actual-source-commit> \
  --project "機能テスト" --environment "隔離検証環境" \
  --output /private/output/functional-test-plan.xlsx
```

対象を絞る場合は `--case V-SUBMIT --case V-REJECT` のように指定します。`--human-plan <path>` で、人向けの共通準備とケース間の初期化・操作を取り込めます。検証観点は `verify/case/@type` に従って配置します。

**採否はすべて未判定**です。期待結果の出所が承認されていなければ、Excelを生成しただけでは実行可能とみなしません。複数のユースケースを含むXMLでは、対象の `useCase` と検証IDを明示してください。

任意の [Human Work Plan v2](human-work-direction.md#procedure-based-plan-version-2) も
同じ `--human-plan` で指定できます。共有操作をケース別の確認行へ展開し、操作 ID、
手順 ID と版、条件 ID、要件参照、前提・終了状態、初期化・復旧・再開位置と証跡取得方法を
保持します。対象リビジョンや必要条件との不一致、欠落・重複、1ケース6手順を超える計画は
出力前に拒否します。手順や確認条件を黙って省略せず、ケースの分割を明示してください。

Excelは `FT-xx!B7` に `VERIFY:<検証ID>` を保持し、`表紙!K19` にソースリビジョンを記録します。検証リストの数式、個別ケースの `B31`（設計状態）と `H30`（総合判定）は保全します。10件超ではシートと一覧行を追加します。各ケース6手順を超える場合は、手順を無理に省略せず、ケース設計を見直して分割します。

## 結果・証跡の反映

```sh
python scripts/build_functional_test_excel.py results \
  --workbook /private/output/functional-test-plan.xlsx \
  --result /private/runs/run001/result.json \
  --output /private/output/functional-test-results.xlsx
```

標準 `ai-assisted-testing.md` の `result.json` を読み、**sourceRevision・verifyCaseId・runId** を必須照合します。実行全体がPASSでも各手順の合格にはしません。各 `checks[]` に `stepNo`（1～6）、`status` と `evidence[]` があり、同一result内の実在する相対証跡パスに対応する場合のみ個別行へ結果を反映します。

v2 から作った行では、`checks[].conditionId` も行頭の `CONDITION:` と照合します。
別条件の結果を同じ手順番号へ流用しません。v1 の帳票・結果の取込条件は維持します。
実行不能は `blocked`（保留）、未着手は `not-run`、期待結果との差を観測した場合は
`failed` とし、前の操作の失敗だけで後続を不合格にしません。試行記録や作業計画から
結果セルを自動的に合格へ変更しません。

```json
{
  "schemaVersion": 1, "runId": "R-001", "verifyCaseId": "V-SUBMIT",
  "sourceRevision": "actual-commit-sha", "status": "passed",
  "checks": [{"stepNo": 1, "status": "passed", "observedUI": "受付番号を表示",
              "evidence": ["screenshots/001.png"]}],
  "evidence": [{"path": "screenshots/001.png", "type": "画像", "description": "画面確認"}]
}
```

証跡は `result.json` と同じフォルダを起点とした実ファイルのみ参照し、絶対パス、親ディレクトリ遡り、シンボリックリンクは拒否します。入力済みの人手判定は上書きしません。出力先は常に別ファイルとし、更新や再実行時は新しい出力名を指定します。画面画像のExcel埋め込みは行わず、証跡一覧にID/ファイル参照を記録します。必要に応じて人が最小枚数の画像を貼付できます。

**重要:** 添付テンプレートの総合判定式は証跡の存在・妥当性まで検査しません。納品・アーカイブ前に証跡の存在、実行版数、要求ID、採否、未実施・保留を別途確認し、人が受入判断を行います。Feature Map XMLは業務知識の正本、Excelは作業・顧客共有用の実行記録です。

## v2計画と結果の整合性

- ケース全体の正本期待値は先頭手順の元の期待値欄に「ケース全体の期待結果」として残し、
  手順の確認点と区別します。計画の期待値が矛盾しても正本を消しません。
  生成は採用・合否の承認ではなく、F6は引き続き未判定です。
- v2で全体結果を passed とするには、計画済みの全stepNo・conditionIdに対応する
  passedのcheckと個別証跡が必要です。空・一部だけのchecks、異なるconditionId、
  failed/blockedを含むPASSは拒否し、出力しません。未完了の実行を自動で合格にしません。
  failed/blockedの部分結果とchecksのないnot-runは保持できます。
- v1のchecksが空のrun-level結果は従来どおり扱い、未確認の手順セルを合格にしません。
  stepNoのない従来の補足記録にも新しい必須項目は追加しませんが、明示的な
  failed/blocked/not-runを含む記録とoverall PASSの矛盾は拒否します。
  v2の旧不完全PASS入力はエラーとなるため、実際の全結果・証跡を揃えるか、
  事実に合う未実施・保留・失敗として記録します。旧結果や失敗履歴を上書きしません。
- 共通v2検査はcaseIdの前後空白を正規化して返します。元JSONは変更せず、Excelと
  JSON等の派生取得が同じIDを使います。active手順のverifiedAtは検証ホストの当日以前
  でなければ拒否します。日付やactive状態だけで実環境への適合・再利用を承認しません。
- Excelは1ケースを複数sessionへまたがって表現できないため、その計画を明示拒否します。
  必要な確認条件を失わずケースを明示的に分けてください。共通計画の複数session自体は
  引き続き使えます。1session内のケースはB8にsession ID・actor・共通準備・停止条件・
  終了/片付けを残し、操作ごとの初期化・復旧・再開と区別します。

結合した期待値やsession説明が既存のセル容量を超える場合も、黙って切り捨てず
短縮・分割を求めるエラーにします。必須フィールドや実行基盤は追加しません。

## Excelを入口にした監査

監査対象が検証リストまたは `FT-xx` シートから指定された場合は、[Audit Evidence Traceability](audit-evidence-traceability.md#excel起点の監査検証リスト個別シートからの逆方向追跡) の逆方向追跡手順を使います。個別シートの `B7` にある `VERIFY:<検証ID>` と表紙 `K19` のソースリビジョンを起点として、Feature Map、元の `result.json`（`verifyCaseId` / `sourceRevision` / `runId`）、画像・ログ、PR/CI/人の承認、必要ならリリースまでを照合します。

Excelの総合判定セルや数式だけを監査証拠として扱わず、原証跡の有無・実行対象リビジョン・権限・未確認事項を区別します。Excel原本の書換えや新たな必須列は必要ありません。

## 境界

監査用の保存・追跡は [Evidence Storage](evidence-storage.md) に従います。外向けの
試験番号・条件番号から、内部索引、実行原本、証跡ファイルへ辿れるようにします。
顧客提出版には開発環境・接続・内部Issue/PR・ローカルパス・内部識別子を出さず、
対応表と実行版数は内部索引に保持します。上記CLIの技術用出力には環境/版数/内部IDが
含まれるため、そのまま顧客提出版とみなしません。顧客向けの派生版は別に生成・全体検査し、
そのhashも索引へ記録します。原本、内部帳票、顧客帳票のどれかを変更して他を装わないでください。

- 対応レイアウトの原本は利用者がローカルで指定します。顧客原本の取得・公開・外部への移送は生成CLIの役割に含めません。
- `openpyxl` はExcel式のキャッシュ再計算を行わないため、Excelで開いて再計算します。数式を固定値に置換しません。
- 機能テストの対象に関係のないFTシートは既存帳票の枠として残ります。未判定のため合否集計へ混入しません。
- 顧客の証跡・帳票は公開GitHubへコミットしないでください。
