日本語 | [English](README.md)

# Feature Map Workflow Plugin

業務上まとまりのある機能ごとに、小さなFeature Map XMLを1つ持ちます。
ソース・テストは実装と実行可能な証拠の正本、Feature Mapは再構築しにくい
業務ルール・判断・参照先・未解決事項の索引です。
既存ツールから始め、Hooks・外部の判断補助・テスト支援・Runnerは必要時だけ使います。

## FMWの責務と他リポジトリとの境界

FMWは**機能単位の知識と根拠への参照**を管理します。汎用のワークフロー実行、
テスト実行、総合品質判定、リリース承認は正本も責任主体も分けます。
既存の任意Runner・連携機能は今回変更せず、移行は別途判断します。
[責務定義・既存機能の棚卸し・分離判断基準](docs/scope-and-boundaries.md)を参照してください。

## 利用構成を選ぶ

[Core／AI Assist／Automation](docs/deployment-profiles.md)は独立した利用構成です。CoreはPython 3.10以降と、ローカルXSD検証用の`lxml`だけで動作します。Docker、Jev、有料AI、.NET、MCPは不要です。AI支援と自動化は明示的に選んだときだけ使い、Docker必須なのはComposeモジュール実行経路です。CoreのCIはLinux、Windows、macOSで独立して実行します。

## 1機能から始める

Python 3.10以降を使い、リポジトリのルートで実行します。保存先は許可された場所へ変えます。

```sh
python skills/feature-map-workflow/scripts/init_feature_map.py --system Demo --feature Sample --mode catchup --purpose "Understand one business scenario" --output path/to/feature/feature-map.xml
```

初期化スクリプトはXMLを作成し、XSD/XSLTを同じ場所へコピーします。既存XMLの上書きには明示的な `--force` が必要です。
現行理解は catchup、合意した変更は change。実際の起動点・ソース・テスト・データを調べ、
必要な知識だけ更新し、IDを保って現在のXMLをXSDで検証します。
テストは別途実行し、実際の実行記録・証跡へリンクします。知識が現状と一致するならXMLは変更不要です。

形式の例が必要なときだけ、[架空のパズル記録帳](examples/fictional-puzzle-log/README.md)、
[架空の補充依頼](examples/fictional-stock-request/README.md)を参照します。
創作のルールやDB関係を実システムの根拠には使いません。

## 目的に合う手順を選ぶ

入口は[SKILL.mdの選択表](skills/feature-map-workflow/SKILL.md#choose-the-relevant-guide)に統一しています。
READMEは日本語版・英語版のどちらか一方を読み、ガイドは現在の問いに必要な節だけ参照します。
リンク先を再帰的に全部読む必要はありません。
過去経緯はGitと[CHANGELOG](CHANGELOG.md)に残し、版の調査時だけ参照します。

主な入口は、[XMLの契約](skills/feature-map-workflow/references/feature-map-contract.md)、
[工程の全体像](skills/feature-map-workflow/references/development-lifecycle.md)、
[変更・影響範囲に応じた条件選定とテスト戦略](skills/feature-map-workflow/references/test-strategy.md)、
[人の作業手順](skills/feature-map-workflow/references/human-work-direction.md)、
[証跡保存](skills/feature-map-workflow/references/evidence-storage.md)、
[監査証跡の追跡](skills/feature-map-workflow/references/audit-evidence-traceability.md)です。

## 完成状態から逆算する

要求では納品後の目標状態と完成条件を定義し、仕様では振る舞い、設計では責務と必要なファイル配置を具体化します。実装・検証では現在状態との差分だけを埋め、完了時にはGit・証跡・保守情報・次案件の再開経路も確認します。ファイル構造の一律変更や新しい管理台帳は必須ではありません。[目標状態と引き継ぎ](skills/feature-map-workflow/references/target-state-and-handoff.md)を参照してください。

## 情報の保存先を分ける

業務の期待結果は合意済み仕様、実装はソース・テスト、永続的な知識と重要な未決事項は
Feature Mapが持ちます。詳細データ・計画・ログ・画像・実行結果・リリース成果物は
既存の保存先に置き、XMLからID・版で参照します。コード一覧や実行履歴を転記しません。

現行のXSDはFeature Map形式1.3に対応し、1.1/1.2形式のXMLも検証できます。AIは必要なXMLノードを取得し、
検証はXSDツールで行います。スキーマ全文や例は、関係する契約変更・エラーの確認時だけ読みます。

**FMWのHTMLは人向けの出力に限定します。** AI・ツールはXML、構造化計画、
実行結果と証跡の正本から必要情報を取得します。
FMWのHTMLを再解析したりモデルへ渡したりして、ケース・操作・状態・証跡を取り出しません。
通常のWeb UIテストや、人向け出力のマークアップ検証を禁止する方針ではありません。
図は根拠のある関係だけを示し、JOINだけで物理FKを確定しません。
機能索引は個別XMLへのメタデータとリンクだけです。XML・索引・証跡の機密性も保護します。

## 任意ツールと実装状態

| 必要な場面 | 参照先 |
| --- | --- |
| XML問い合わせ・XSD検証 | [xquery-mcp](skills/feature-map-workflow/references/xquery-mcp.md) |
| 信頼したローカルファイルによるHooks | [イベント・制約](skills/feature-map-workflow/references/codex-hooks.md) |
| 外部の限定判断補助。既定off、既存Jev設定は維持 | [Decision Providers](skills/feature-map-workflow/references/decision-providers.md) |
| テストツール導入・合成データの実行例 | [導入ガイド](examples/ai-assisted-testing/README.md) |
| Linux bubblewrapでの単一タスク試行 | [Runner契約](skills/feature-map-workflow/references/autonomous-task-runner.md)、[信頼境界](skills/feature-map-workflow/references/ai-trust-controls.md) |
| 選択式49候補・Linuxコンテナでの直列実行 | [モジュール実行基盤](skills/feature-map-workflow/references/module-workflow.md)、[オフライン合成例](examples/module-workflow/README.md)。DB・Windows実行は未対応 |
| 任意のself-hosted PoC | [Agents API](skills/feature-map-workflow/references/agents-api.md) |
| API・キュー・Projectionの設計案。実行サービスは未同梱 | [Repository Coordination](skills/feature-map-workflow/references/repository-coordination.md) |

合成テストの成功だけで本番適合や費用削減を証明しません。
PTCは予測可能な読み取り・問い合わせ・集約に使い、書き込み・承認・外部作用には各操作の権限が必要です。

### XML問い合わせ・検証の準備

xquery-mcp **2.5.1** を固定し、.NET 10 SDKを使います。
必要時だけ ./scripts/setup-xquery-mcp.ps1 または bash ./scripts/setup-xquery-mcp.sh で復元します。
QueryResultの正規化、空と失敗の区別、xml_validate_schemaの成功契約は連携ガイドを正本とします。

### テストツールと生成物

./scripts/setup-ai-testing.ps1 -DryRun または bash ./scripts/setup-ai-testing.sh --dry-run で
導入予定を確認します。専用 .venv-ai-testing を使い、FlaUIは明示したプロジェクトだけへ追加できます。
SDKやLinuxブラウザ用OSライブラリは自動導入しません。ドライランと実UIテストは別の確認です。

[人の作業手順](skills/feature-map-workflow/references/human-work-direction.md)が
HTML表示と正本からのJSON取得を扱います。
[Plan v2](skills/feature-map-workflow/references/human-work-plan-v2.md)は手順部品・個別確認点が必要なときだけ読みます。
[Excel生成](skills/feature-map-workflow/references/functional-test-excel.md)には
対応する test_template.xlsx をローカルで用意します。顧客原本は同梱しません。
生成処理はテストを実行せず、業務の期待結果や合否も承認しません。

### Hooksの信頼と外部への判断問い合わせ

有効化前に[設定](hooks/hooks.json)と[実装](hooks/feature_map_hook.py)を確認します。
Web上でPluginを追加しただけではローカルスクリプトは動きません。
反復プロンプトにも短い安全方針を毎回渡し、セッション再開・圧縮・状態不明・対象や方針の変更後には
全文を再挿入します。キャッシュは送出履歴であり、モデルが情報を覚えている証明ではありません。
Stop/XSDの判定は現在のXMLハッシュに対応します。

外部送信には権限を確認し、助言で事実・権限・承認・検証合格を確定しません。
API失敗時もローカルのゲートを維持します。

## 検証、レビュー、人の権限

必要なチェックは[CONTRIBUTING](CONTRIBUTING.md)、独立した読み取り専用レビューは
[REVIEW.md](REVIEW.md)に従います。対象コミットに結び付いた実証跡を残し、
重要な指摘を解消します。AIの修正・再レビューは原則3回まで、未実行は NOT_RUN。
人の承認は現在の版に対して必要です。テスト・AIレビューの合格だけでmerge・deployやデータ操作は許可されません。
HIGH/CRITICALは人主導で、Runnerの候補は HUMAN_REVIEW_REQUIRED です。
ホストの保護設定は管理者が実際の有効性を確認します。

## リポジトリ構成と参加方法

skills/feature-map-workflowにガイド・資材・支援ツール、hooksにローカル連携、
scriptsにテスト・導入・梱包・Runner、examplesに架空例、docsに設定ガイドがあります。
[月次保守](skills/feature-map-workflow/references/cross-task-harness-maintenance.md)は
読み取り専用で候補を提示し、Skillを自動修正しません。

必要に応じて[SECURITY](SECURITY.md)、[保護設定](docs/github-repository-settings.md)、
[LICENSE](LICENSE)、[依存関係の表記](THIRD_PARTY_NOTICES.md)を参照してください。
