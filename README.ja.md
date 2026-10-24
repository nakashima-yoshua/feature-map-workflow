日本語 | [English](README.md)

# Feature Map Workflow Plugin

業務上まとまりのある機能ごとに、小さなFeature Map XMLを1つ持ちます。調査、設計、実装、検証、納品を通じて、ソースやテストだけでは再構築しにくい業務ルール、判断、参照先、未解決事項を残すための開発ワークフローです。

まずは既存のソース・テストとFeature Mapから始めます。Hooks、外部の判断補助、テスト支援、Task Runnerは任意です。複数人・AI向けのRepository Coordinationは設計案であり、実行サービスは同梱していません。

## 1機能から始める

Python 3.10以降を使い、リポジトリのルートで実行します。名前と出力先は、対象機能と許可された保存場所に置き換えてください。

```sh
python skills/feature-map-workflow/scripts/init_feature_map.py --system Demo --feature Sample --mode catchup --purpose "Understand one business scenario" --output path/to/feature/feature-map.xml
```

初期化スクリプトはXMLと表示・検証用のXSLT/XSDを配置します。既存XMLは `--force` を指定した場合だけ上書きします。現行機能の理解には `catchup`、合意した変更には `change` を使い、更新時は既存IDを保ちます。

1. 実際の起動点、ソース、テスト、関係するデータ・設定を確認する。
2. 再利用する知識と参照先をXMLへ残し、未確認事項は `open` で管理する。
3. 必要なノードだけ変更し、現在のXMLをXSDで検証する。
4. 必要なテストを別途実行し、実際の証跡を参照する。
5. 完了前にFeature Mapを確認する。永続的な知識に差分がなければ、変更不要と報告する。

[架空のパズル記録帳](examples/fictional-puzzle-log/README.md)と[架空の補充依頼](examples/fictional-stock-request/README.md)に一式の例があります。業務ルールやDBの関係は創作であり、実システムの根拠には使いません。パズル記録帳には、PowerShellでXMLをHTMLへ変換する手順もあります。

## 目的に合う手順を選ぶ

今の作業に関係するガイドから読み始めます。

| 目的 | ガイド |
| --- | --- |
| XMLに残す知識、機能の分割、HTML索引を決める | [Feature Map Contract](skills/feature-map-workflow/references/feature-map-contract.md) |
| 要件、設計、テスト、実装、納品をつなぐ | [Development Lifecycle](skills/feature-map-workflow/references/development-lifecycle.md) |
| 初見コード、動的呼出し、SQL、実行時依存を調べる | [Legacy Analysis](skills/feature-map-workflow/references/legacy-analysis.md) |
| EXE・ジョブ・画面から対象BLへ到達する条件と最小データを探す | [Target Reachability](skills/feature-map-workflow/references/target-reachability.md) |
| レガシー機能追加で局所改修・最小限の責務分離・段階的置換を比較する | [Incremental Modernization](skills/feature-map-workflow/references/incremental-modernization.md) |
| 業務フロー、データフロー、根拠のあるER関係をつなぐ | [Three Complementary Views](skills/feature-map-workflow/references/three-view-understanding.md) |
| 変更箇所と影響経路から検証項目・入力条件を優先度で絞り、必要十分なテスト層を決める | [Test Strategy](skills/feature-map-workflow/references/test-strategy.md)、[Coverage Model](skills/feature-map-workflow/references/coverage-model.md) |
| UI・CLI・DBテストを繰り返し実行して証跡を残す | [AI-assisted Testing](skills/feature-map-workflow/references/ai-assisted-testing.md) |
| ケースごとの合否を保ち、人の準備・切替回数を減らす | [Human Work Direction](skills/feature-map-workflow/references/human-work-direction.md) |
| 提供されたExcelへ計画と手順単位の実行結果を反映する | [機能テストExcel](skills/feature-map-workflow/references/functional-test-excel.md) |
| 顧客提出資料を作成・検査し、証跡の揃った資材だけを整理する | [顧客提出資料の作成](skills/feature-map-workflow/references/customer-deliverables.md) |
| 監査時に試験番号・条件番号から実行原本へ辿る | [証跡の保存と監査索引](skills/feature-map-workflow/references/evidence-storage.md) |
| 検証済みの変更をレビューし、人の承認へつなぐ | [Code Review](skills/feature-map-workflow/references/code-review.md)、[REVIEW.md](REVIEW.md) |
| 明示的に依頼された保守負荷・工程効率の調査を行う | [保守改善トリアージ](skills/feature-map-workflow/references/maintenance-triage.md)、[YAGNIと全体最適](skills/feature-map-workflow/references/yagni-whole-system-optimization.md) |
| 新しいタスクから共通手順を学習し、Harnessを棚卸し・校正する | [タスク横断型Harness保守](skills/feature-map-workflow/references/cross-task-harness-maintenance.md) |

GitHub Actionsで月次の読み取り専用構造監査を行います。意味の校正・統合・変更の採否は人間のレビューに委ね、Skillの自動書き換えは行いません。

各ガイドは既存の開発工程で使います。毎回、新しい工程・報告書・ツールを増やす必要はありません。関係する業務全体を理解したうえで、変更は合意した範囲に絞ります。実装・検証・運用の負担に見合う価値がなければ、変更しない判断も選べます。

## 情報の保存先を分ける

| 情報 | 正本・保存先 |
| --- | --- |
| 実装と実行可能な振る舞いの証拠 | ソース、テスト |
| 業務上の期待結果と受入権限 | 承認済みの要求、不変条件、人の判断 |
| 再利用する機能知識と重要な未確認事項 | Feature Map XML |
| テストデータ、詳細手順、画像、ログ、DB観測、リリース成果物 | 既存のテスト・証跡・成果物の保存先。XMLからは参照する |
| 変更履歴 | Git |
| XML構造と人向け表示 | XSD、XSLT |

現在のFeature Map形式は1.3で、XSDは1.1と1.2も受け付けます。変更履歴、クラス一覧、SQLの写し、実行トレース全文はXMLへ重複保存しません。既存コードから観測した動作と、業務として承認された期待結果を区別します。

Mermaid図は、既存の `diagrams/diagram` にCDATAで記録します。順序、境界、状態、データの関係を理解する助けになる図を選びます。JOINだけで物理FKを確定せず、図を生成しただけで動作検証済みともしません。人向けブリーフでは、必要なUML・DFD・ER等を件数の上限なく選択できます。

XSLT表示は技術的な詳細と図を折りたたみます。複数機能の索引には、個別XMLへリンクするメタデータだけのHTMLを任意で生成できます。詳しくは[Feature Map Contract](skills/feature-map-workflow/references/feature-map-contract.md)を参照してください。顧客のXML、証跡、索引にも機密情報が含まれ得るため、許可された場所で保管します。

## 任意ツールと実装状態

| 構成要素 | 利用できる範囲 | 詳細 |
| --- | --- | --- |
| xquery-mcp | 固定版のXML問い合わせ・整形・XSD検証との連携 | [ツールと結果の契約](skills/feature-map-workflow/references/xquery-mcp.md) |
| Codex Hooks | コンテキスト確認、編集追跡、完了時検証。信頼したファイルを実行するホストが必要 | [イベントと制約](skills/feature-map-workflow/references/codex-hooks.md) |
| Decision Providers | 限定した判断補助を実装済み。外部呼出しは既定off | [選択と送信条件](skills/feature-map-workflow/references/decision-providers.md)、[既存Jev設定](skills/feature-map-workflow/references/jev.md) |
| テスト支援 | 任意インストーラー、合成データの実行例、HTMLブリーフ・Excel生成 | [導入と実行例](examples/ai-assisted-testing/README.md) |
| Task Runner | 単一タスクの上限付き試行を任意で実行。評価にはLinuxのbubblewrapが必要 | [実行・再開の契約](skills/feature-map-workflow/references/autonomous-task-runner.md)、[オフライン例](examples/task-runner/README.md) |
| Agents API | 読み取り担当と単一更新担当を分ける、任意のself-hosted PoC | [連携契約](skills/feature-map-workflow/references/agents-api.md)、[実行例](examples/agents-api/README.md) |
| Repository Coordination | API・キュー・Projectionを扱う設計契約。実行サービスは未同梱 | [設計案とMVP境界](skills/feature-map-workflow/references/repository-coordination.md) |

実装や合成テストの存在だけでは、本番運用への適合や納品までの時間短縮を証明できません。導入を検討する際は、[Runnerの未解決事項とAI信頼境界](skills/feature-map-workflow/references/ai-trust-controls.md)を確認します。Programmatic Tool Callingは、予測可能な読み取り・問い合わせ・集約に使います。書き込み、承認、外部への副作用は、それぞれの実行権限に従います。[呼出し方針](skills/feature-map-workflow/references/programmatic-tool-calling.md)に詳細があります。

### XML問い合わせ・検証の準備

ローカル.NET Toolとして `xquery-mcp` **2.5.1** を固定しています。連携を使う場合は、.NET 10 SDKを用意して復元します。

```powershell
./scripts/setup-xquery-mcp.ps1
```

```sh
bash ./scripts/setup-xquery-mcp.sh
```

XPath/XQueryの実行結果は、構造化された `QueryResult` として返ります。同梱アダプターで正規化し、正常な空シーケンスと失敗を区別してから値を使います。`xml_validate_schema` は別のプレーンテキスト成功契約を維持しています。詳しくは[xquery-mcp Integration](skills/feature-map-workflow/references/xquery-mcp.md)を参照してください。

### テストツールと生成物

任意のインストーラーは専用の `.venv-ai-testing` を作り、固定版PlaywrightとChromiumを導入します。xquery-mcpの復元や、明示したテストプロジェクトへのFlaUI追加も選べます。最初に導入予定を確認してください。

```powershell
./scripts/setup-ai-testing.ps1 -DryRun
```

```sh
bash ./scripts/setup-ai-testing.sh --dry-run
```

実際の導入、`--check` / `-Check`、smoke test、OSごとの前提は[導入ガイド](examples/ai-assisted-testing/README.md)に従います。Python・.NET SDKやLinuxのブラウザ用OSライブラリは自動導入しません。ドライランの成功と、ブラウザ・デスクトップの実操作は別の検証です。

[人向け検証ブリーフ](skills/feature-map-workflow/references/human-work-direction.md)は、既存の図・期待結果とレビュー済み作業計画を表示します。[Excel生成](skills/feature-map-workflow/references/functional-test-excel.md)には、対応レイアウトの `test_template.xlsx` をローカルで指定します。顧客原本は同梱していません。どちらも既存情報から作る成果物であり、テスト実行や業務期待値の承認は行いません。未実行ケースを合格にせず、実行全体のPASSを根拠のない手順別PASSへ転記しません。

### Hooksの信頼と外部への判断問い合わせ

有効化前に[hooks/hooks.json](hooks/hooks.json)と[実装](hooks/feature_map_hook.py)を確認します。スクリプトはPluginファイルを持つホストで動作します。Web上でPluginを追加しただけでは、スクリプトはローカルに配置されません。プロンプト中の曖昧な語は調査の手掛かりとして使い、利用可能な情報を確認しても結果を左右する不足が残る場合だけ質問します。Stop時の検証は現在のXMLハッシュに結び付き、継続回数には上限があります。

判断補助は `FEATURE_MAP_DECISION_PROVIDER=off|jev|openai` で選び、OpenAIには任意の作業フェーズ判定と、結果を記録するだけの観測モードがあります。既存の `FEATURE_MAP_JEV_*` 設定も維持します。metadataや本文送信モードで送る内容はProviderごとに異なります。有効化前に[Decision Providers](skills/feature-map-workflow/references/decision-providers.md)と[Jev](skills/feature-map-workflow/references/jev.md)の送信条件を確認してください。判断補助で事実や権限を確定せず、必須検証を解除しません。APIの失敗は未判断とし、ローカルのゲートは維持します。

## 検証、レビュー、人の権限

対象コミットに必要な決定的検証を実行し、[REVIEW.md](REVIEW.md)に沿って別コンテキストの読み取り専用差分レビューを依頼します。指摘は根拠と照合して処理し、AIによる修正・再レビューは原則3回までとします。人のレビューは現在のコミットに結び付けます。実行できなかった検証は `NOT_RUN` とし、ソース確認、モック、実行結果、業務受入を区別して報告します。

Task RunnerはLOWと、事前承認の条件を満たすMEDIUMを扱います。HIGH/CRITICALは人主導です。検証に合格した候補は `HUMAN_REVIEW_REQUIRED` となり、自動承認・公開には進みません。AIの指摘が0件でも、PRテンプレートや方針文書があっても、GitHubの保護設定が有効である証明にはなりません。必要な人の承認、ホスト権限、復旧手段、実際のCIをそれぞれ確認します。

日本語は、短くする前に意味・範囲・確信度・識別子を保ちます。[Context Gate](skills/feature-map-workflow/references/context-gate.md)と[Operable Japanese](skills/feature-map-workflow/references/operable-japanese.md)に従い、既存情報で解決できることは再質問しません。

## リポジトリ構成と参加方法

| 場所 | 内容 |
| --- | --- |
| [skills/feature-map-workflow/](skills/feature-map-workflow/) | Skill入口、作業別ガイド、XML/XSD/XSLT、機能単位の支援ツール |
| [hooks/](hooks/) | ライフサイクルHooksと任意のDecision Provider実装 |
| [scripts/](scripts/) | セットアップ、テスト、検証、梱包、Task Runner |
| [examples/](examples/) | 架空のFeature Map、合成テスト、任意の実行基盤の例 |
| [docs/](docs/) | リポジトリ設定ガイドと既存のRunner Feature Map |
| [.github/](.github/) | CI・リリース定義と共同作業用テンプレート |

変更時の検証とPRの書き方は[CONTRIBUTING.md](CONTRIBUTING.md)、非公開での脆弱性報告は[SECURITY.md](SECURITY.md)、管理者が行う保護設定は[GitHub repository settings](docs/github-repository-settings.md)を参照してください。ライセンスと依存関係の表記は[LICENSE](LICENSE)と[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)にあります。
