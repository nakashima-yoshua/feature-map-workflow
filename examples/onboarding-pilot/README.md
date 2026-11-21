# オンボーディング・パイロット：架空の補充依頼

**対象：** FMWリポジトリの新規参加者による、既存情報の読解・検証手順の練習。題材は[fictional-stock-request](../fictional-stock-request/README.md)の架空ユースケース `UC-SUBMIT`。本番業務・実在する顧客・DB・ソース実装は存在しません。実際の参加者・所要時間・効果はまだ計測していません。

## 前提
- Gitの作業コピーとPython 3.10以降。仮想環境で `lxml` を用意する。
- 既存のREADMEと[責務定義](../../docs/scope-and-boundaries.md)を確認する。
- 本演習に本番アクセス権・外部API・認証情報・実DBは不要。

## 手順
1. `git rev-parse HEAD` と `git status --short` を読み、基準Git SHAと作業ツリーの状態を記録する。汚れている場合は勝手にresetしない。
2. [Feature Map XML](../fictional-stock-request/feature-map.xml)を開く。`meta`, `goal`, `useCase id="UC-SUBMIT"`, `sourceMap`, `diagrams`, `knowledge`, `verify`, `open` を確認する。
3. `DG-FLOW` で受付・拒否分岐、`DG-DFD` で読み書き、`DG-ER` で**架空の**表関係を説明する。`sourceMap/ref` の `fictional:` は実ファイルパスではないと確認する。
4. 作業コピーのリポジトリルートから、以下の既存の静的検証を実行する（実業務の正常系・異常系を実行するコマンドではない）。

```sh
python skills/feature-map-workflow/scripts/validate_feature_map.py examples/fictional-stock-request/feature-map.xml --xsd skills/feature-map-workflow/assets/feature-map.xsd
python scripts/test_three_view_understanding.py
```

5. 実際の終了コード、画面出力、Git SHA、環境を記録する。実行できない場合は `BLOCKED`、実行していなければ `NOT_RUN`。XML上の検証ケース `V-SUBMIT` / `V-REJECT` は実業務テスト未実行のまま。
6. [Feature Map Contract](../../skills/feature-map-workflow/references/feature-map-contract.md)に従い、何をFMWの永続知識に保存し、どのログ/結果をテスト側に残すか説明する。推測を確認済みと記載しない。
7. 担当者が認めたIssueがある場合だけ、ドキュメントのリンク修正や既存テストの改善など小さなPRを別途作成する。PRはレビュー依頼までとし、マージしない。

## 参加者の到達基準
- システム全体に対するFMWの役割と、テスト実行・Quality Gate・承認の境界を説明できる。
- `UC-SUBMIT` から3図・データ参照・`verify`へたどり着ける。
- XMLの形式検証と現実の業務動作の実証が違うことを説明できる。
- 未検証事項、環境制限、次の安全な確認を第三者へ伝えられる。

## 実パイロット測定欄（未測定）
実施者・日時、初回起動までの時間、構造理解までの時間、初回PRまでの時間、質問・手戻り件数は、参加者の同意と実際の観測に基づき既存Issue/PRへ記録する。合格率や工数削減を推測で記載しない。

**導入先への移行条件：** 実案件のリポジトリ・作業権限・機能1件・現実の検証環境・Runbook・合意済みIssueが具体化した段階で、その導入先に独自の`ONBOARDING.md`を設けて評価する。この架空演習はその代替ではない。
