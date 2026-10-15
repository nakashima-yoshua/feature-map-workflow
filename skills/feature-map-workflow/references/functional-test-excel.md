# 機能テストExcelテンプレート統合

機能テストの対外共有・実施記録には、依頼者が提供した `test_template.xlsx` を標準帳票として使います。帳票は **表紙 / 検証リスト / FT-01～FT-10** の既存レイアウト・数式・入力規則を維持します。GitHub上の公開リポジトリには元の添付ファイルを格納していないため、実行時に **--template** で安全なローカル原本を指定します。

## 計画の作成

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

任意で `--case V-SUBMIT --case V-REJECT` を繰り返して対象ケースを限定し、`--human-plan <path>` で人向け共通準備とケース間の初期化・操作を取り込みます。検証観点は `verify/case/@type` に従い配置されますが、**採否はすべて未判定**です。期待結果の出所が承認されていなければ、Excelを生成しただけでは実行可能とみなしません。多ユースケースのXMLでは対象useCaseと検証IDを明示指定してください。

Excelは `FT-xx!B7` に `VERIFY:<検証ID>` を保持し、`表紙!K19` にソースリビジョンを記録します。検証リストの数式、個別ケースの `B31`（設計状態）と `H30`（総合判定）は保全します。10件超ではシートと一覧行を追加します。各ケース6手順を超える場合は、手順を無理に省略せず、ケース設計を見直して分割します。

## 結果・証跡の反映

```sh
python scripts/build_functional_test_excel.py results \
  --workbook /private/output/functional-test-plan.xlsx \
  --result /private/runs/run001/result.json \
  --output /private/output/functional-test-results.xlsx
```

標準 `ai-assisted-testing.md` の `result.json` を読み、**sourceRevision・verifyCaseId・runId** を必須照合します。実行全体がPASSでも各手順の合格にはしません。各 `checks[]` に `stepNo`（1～6）、`status` と `evidence[]` があり、同一result内の実在する相対証跡パスに対応する場合のみ個別行へ結果を反映します。

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

## 境界

- 原本の添付xlsxはユーザーから提供済みであり、元ファイルのGitHubへの自動移送はこのツール接続では扱っていません。生成CLIは原本をローカルに置いて実行します。
- `openpyxl` はExcel式のキャッシュ再計算を行わないため、Excelで開いて再計算します。数式を固定値に置換しません。
- 機能テストの対象に関係のないFTシートは既存帳票の枠として残ります。未判定のため合否集計へ混入しません。
- 顧客の証跡・帳票は公開GitHubへコミットしないでください。
