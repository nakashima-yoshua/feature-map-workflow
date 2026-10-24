# Audit Evidence Traceability（監査向け証跡追跡）

## 目的と適用範囲

監査の質問から、要求・意思決定・変更・テスト・レビュー・承認・リリースまでを短時間で追跡するための**参照構成**。既存の開発工程と正本を再利用し、新しい必須工程・中央証跡DB・Feature Mapスキーマを追加しない。顧客監査、内部品質監査、変更影響調査に必要な範囲で使用する。

監査で保証するのは「証跡の存在・対象・来歴・不足を検証できること」であり、証跡が存在するだけで品質、統制の有効性、業務承認を保証するものではない。

## 原則：正本は分散、索引は一箇所

| 質問 | 正本 | 推奨する参照キー |
| --- | --- | --- |
| なぜ変更したか | 承認済み要求、Issue、変更契約、ADR | requirement ID / issue URL / decision ID |
| 何を変更したか | Git commit、PR、対象コードと設定 | repository / base SHA / head SHA / path |
| 何を検証したか | テスト定義、実行結果、CIログ、検証Excel | case ID / run ID / commit SHA / environment |
| どう判定したか | 期待結果の出典、結果、例外記録 | oracle reference / observed result / status |
| 誰がいつ承認したか | GitHubレビュー、承認記録、受入記録 | reviewer/authority / timestamp / exact revision |
| 何を納品・適用したか | ビルド成果物、リリースmanifest、配備記録 | artifact digest / release ID / environment |

Feature Map XMLは耐久性のある業務知識・source/test/evidence参照の索引であり、生ログ、スクリーンショット、個人情報、認証情報や実行履歴全体を複製しない。成果物やGit履歴は元の保存先を正本とする。

## 推奨構成：Audit Index（派生・再生成可能）

変更・リリース単位で、必要時に**監査用目次（Audit Index）**を作る。最初はMarkdownで十分。専用サービスやXML/XSD変更は不要。

```text
Audit question / change ID
    -> requirement + accepted intent
    -> affected feature / rule / invariant / interface
    -> implementation PR + exact commit SHA
    -> test case + execution run + observed result
    -> review finding + disposition + human approval
    -> released artifact digest + deployment/acceptance
```

最小の記載項目：

- 対象：feature ID、change/issue/PR ID、監査範囲、対象外、リスク区分
- リビジョン：repo URL、base SHA、検証・レビュー対象 head SHA、リリース時のSHA
- 判断：要求・業務ルール・ADR/例外承認へのリンク（不明は `UNVERIFIED`）
- 検証：case ID、期待結果の根拠、実行ID、実行日時、環境識別子、結果と証跡URI、検証対象SHA
- 承認：レビュー対象SHA、判断者と権限、判断日時、承認/保留/不承認の原記録へのリンク
- 配布：artifact ID/digest、デプロイ記録、受入記録、差分/切戻し・補償手順の参照
- 不足：`NOT_RUN`、`UNVERIFIED`、`MISSING`、`STALE` の区別と担当・次の確認方法

相対パスだけに依存せず、GitHubのpermalink（コミット固定URL）、CI run URL、artifact digestなど**時点を固定できる参照**を優先する。CIの短期保存ログや期限付きartifact URLは、保持期限を確認して必要な証跡のみ権限管理された保存先へ退避し、正本URIとハッシュ・保管者・保管期限を索引に記録する。退避は保存方針・契約・法令に従い、無許可で実データを外部公開しない。

## 既存フェーズへの差し込み（別工程を増やさない）

- **1–3 要件・基本設計：** 要求/変更IDとFeature Mapのルール・不変条件・関係箇所を結ぶ。レガシー機能追加ではA/B/Cの選定根拠、維持する外部契約、未解析経路を参照する。
- **4–8 検証設計：** 重要な要求→シナリオ→ルール/状態/副作用→case IDを結ぶ。期待結果の根拠と未検証範囲を区別する。不要なテストカタログはFeature Map XMLに転記しない。
- **9 実装・CI：** 実行run、commit SHA、環境、テストケース、結果の対応を証跡の所有元で保持する。レビューの指摘・対応はPRの実記録に結ぶ。
- **10 リリース：** artifact digestと実際に検証・承認されたSHAの対応を確認する。変更後の再ビルド/差し替えは追跡し直す。
- **11–12 As-Built・受入：** 必要時にAudit Indexを組み立て、リンク到達性・対象一致・不足を確認して人に渡す。Audit Indexの生成やAI要約は承認にはならない。

## 監査照会の手順（最短経路）

1. 監査質問を具体的な変更ID、機能ID、期間、環境へ絞る。範囲が不明なら推測で「証拠あり」としない。
2. 既存Feature Map/Issue/PRから最短の索引を組み立て、各リンクを**正本まで辿る**。巨大なログ全文は先に取得しない。
3. `requirement -> case -> run -> revision -> approval -> release` の主要チェーンをたどり、要所でIDとSHA・時刻・環境を突合する。監査質問によっては逆方向（本番artifact→変更→要件）も使う。
4. 不足を `MISSING`（証跡なし）、`NOT_RUN`（未実施）、`UNVERIFIED`（未確認）、`STALE`（対象リビジョン違い/古い）のように区別する。リンク切れはPASSではない。
5. 監査者のアクセス権に応じてリンクと限定的な抜粋を提示し、機微情報や顧客データはマスク/別保管。承認や検査のない工程は推測で埋めない。

## Excel起点の監査（検証リスト・個別シートからの逆方向追跡）

既存の[機能テストExcel](functional-test-excel.md)は顧客共有・人の実施記録であり、**監査の入口**として利用する。Excelを監査上の唯一の正本に格上げしない。元テンプレートの列追加・式変更、Excelからの外部通信、VBA追加は不要。

```text
Excel 検証リスト（対象ケースを選択）
  -> 個別 FT-xx シート B7: VERIFY:<verifyCaseId>
  -> Feature Map verify/case（要求・ルール・期待結果の出典）
  -> 表紙 K19: sourceRevision
  -> results の result.json（verifyCaseId + sourceRevision + runId の一致）
  -> checks[].evidence[] + 実在する証跡ファイル（画像・ログ）
  -> PR / CI / コミット / 人の承認（対象SHA・権限・日時を照合）
  -> release manifest / artifact digest / 受入記録（必要な場合）
  -> Audit Index（参照先・照合結果・欠落と未確認）
```

### 手順

1. **ケース選択：** 検証リストで対象行・結果・対象ケースを選び、対応する `FT-xx` シートの `B7` にある `VERIFY:<検証ID>` を抽出する。シート名・行番号だけを永続IDにしない。複数の検証IDが混在するときは対象を限定する。
2. **対象特定：** 表紙 `K19` のソースリビジョンとFeature Mapの `verify/case`、関連 `useCase`・ルール・期待結果の出典を照合する。Excelに書かれた期待値が業務承認されたオラクルであるとは推定しない。
3. **結果照合：** 実行記録の `result.json` を探し、`verifyCaseId`、`sourceRevision`、`runId` の組を照合する。候補が複数なら実行日時・環境・対象範囲で選択し、取り違えを避ける。Excel `H30`（総合判定）、`B31`（設計状態）と個別 `checks[]` の実績を区別する。Excelの数式値のみで証拠の存在やPASSを保証しない。
4. **原物確認：** 各 `checks[].evidence[]` が該当run内の実在する画像/ログを指すこと、記録の出所・実行条件・アクセス権を確認する。Excel内の説明文や貼付画像だけしか残っていない場合は原証跡の欠落を明記する。既存の結果取込処理は相対パス・存在確認・シンボリックリンク制約を維持する。
5. **変更・承認・配布への接続：** 検証したSHAに対応するPR・CI・独立レビュー・人の承認を原記録で辿る。リリースを問う場合のみ配布artifact digestとの対応も検証する。PRリンクだけでは対象SHAの一致は保証しない。
6. **回答：** Audit Indexに `workbook reference + sheet + verifyCaseId + sourceRevision + runId` を起点キーとして、確認済みリンクと `MISSING` / `NOT_RUN` / `UNVERIFIED` / `STALE` を記録。監査用の抜粋は必要最小限とし、元Excelや顧客証跡を公開GitHubへ転記しない。

任意の手順計画 v2 を使う場合は、個別行の条件 ID・操作 ID・手順 ID/版から、
封印した計画（`planSHA256`）と `checks[].conditionId`・`stepNo` へ対応をたどります。
共通操作でもケース別の観測・合否・証跡を照合し、試行の採用条件や実行不能の理由を確認します。
作業時間の短縮は QA 作業効率の情報として扱い、製品品質や人の納品承認の代用にしません。

### Excel起点Audit Indexの最小レコード（架空例）

```yaml
entry:
  workbook_ref: private://audits/functional-test-results.xlsx
  sheet: FT-04
  verify_case_id: V-SUBMIT
  workbook_revision: 0123456789abcdef0123456789abcdef01234567
  expected_ref: REQ-04
  run_id: null
  result_ref: null
  evidence_refs: []
  review_ref: null
  release_digest: null
  audit_status: UNVERIFIED
```

`workbook_ref` は実際のアクセス権がある保管先の識別子を使用し、上の架空URIを正本とみなさない。参照できない・一致しない場合、監査側で無理にPASSへ補正しない。

### 段階導入と自動化境界

**まずは読み取り専用の照会手順を1ケースで実証する。** 既存Excelの `B7`・`K19` から索引の照会キーを抽出し、`result.json` とFeature Mapに突合する小さなスクリプトは、手動試行で追跡時間短縮を確認した場合のみ追加を検討する。自動化時も原本Excelの保存・式再計算・結果判定・承認操作は行わない。旧テンプレート・未知のレイアウト・不整合はエラー/未確認として報告し、推測で補完しない。

## 例（架空データ・実行証跡ではない）

```yaml
change: CHG-017
feature: STOCK-REQUEST
requirement: REQ-04
pr: https://github.com/example/project/pull/123
verified_revision: 0123456789abcdef0123456789abcdef01234567
cases:
  - id: FT-04
    result: NOT_RUN
    run_url: null
    oracle_ref: REQ-04
human_approval: UNVERIFIED
release_digest: null
status: INCOMPLETE
```

上記は参照関係の例であり、実際の実行・承認・配布を示さない。

## 最小受入・検証

- [ ] 一件の変更から要求→影響範囲→テストケース→実行証跡→PR/承認→配布へ辿れる。未実施の項目は不足として表示する。
- [ ] 同じテスト結果を別SHA/別環境の証拠として再利用しない。タイムスタンプだけでなくrevision・runを確認する。
- [ ] ソース、テスト、ログ、Excel、PR、CIを一箇所へ無駄に複製していない。
- [ ] アクセス制御、秘密/個人情報の除去、保管期間、リンク失効の取り扱いが明記される。
- [ ] 監査者がサンプルの質問3件（要求起点、テスト起点、リリース起点）を索引から辿り、不足を正しく指摘できる。
- [ ] 追加によって既存のXSD・ゲート・承認権限・Task Runnerの実行上限が変わらない。

**段階導入：** まず1件の実際のPRに対してMarkdownの目次を手動で組み立て、所在確認時間・欠落リンク・保守工数を記録。効果が確認できた場合のみ、既存メタデータから索引を生成するread-onlyスクリプトを検討する。網羅的収集・別DB・新しい統制エンジンは導入しない。
