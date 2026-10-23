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
