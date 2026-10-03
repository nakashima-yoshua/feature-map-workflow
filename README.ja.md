日本語 | [English](README.md)

# Feature Map Workflow Plugin

Feature Map Workflow は、**ソースコードを正本にしたまま、1枚のFeature Map XMLを開発中ずっと持ち回る**ための開発ワークフローです。初見システムのキャッチアップ、要件確認、設計、実装、検証まで、必要な情報だけをXMLに残します。

## 構成

- ソースコード: 実装の正本
- テスト: 実行可能な振る舞いの根拠
- Feature Map XML: 人間とAIが共有するナビゲーション、永続的なルール、不変条件、設計判断、検証証跡、スコープ境界、未解決事項
- XSD: XML構造の契約
- XSLT: 人間向けの1ページHTML表示
- Git: 変更履歴
- xquery-mcp: XPath/XQueryによる部分参照、XML整形、XSD検証
- Codex Hooks: コンテキスト不足の確認、ライフサイクル制御、編集追跡、完了ゲート
- Jev: コンテキスト充足度やFeature Map更新要否を扱う任意の閉じた判断層
- Operable Japanese: `natural-japanese` の考え方を取り入れた、意味を保ったまま操作可能で自然な日本語

## 設計方針

内部で扱う意味と、人間に見せる文章を分離します。

```text
ユーザーの依頼
  -> Context Sufficiency Gate
  -> 意味契約（必要な項目だけ）
  -> source / tests / Feature Map を調査
  -> 実行、または確認を1問だけ返す
  -> 自然な業務日本語として表示
```

優先順位は次の通りです。

```text
意味の保持 > 操作可能性 > 自然さ > 短さ
```

内部の意味契約では、必要に応じて `goal / actor / action / target / condition / scope / exclude / authority / doneWhen / certainty` を整理します。ただし、これを第2の仕様書として保存しません。Feature Map XMLに残すのは、後から再利用する価値がある永続的な知識だけです。

## 初回セットアップ

`xquery-mcp` 2.5.1 をローカル.NET Toolとして固定しています。最初に1回だけNuGetから復元してください。

Windows PowerShell:

```powershell
./scripts/setup-xquery-mcp.ps1
```

macOS/Linux:

```sh
./scripts/setup-xquery-mcp.sh
```

.NET 10 SDKが必要です。

Codex PluginのHookはnon-managed hookです。有効化する前に `hooks/hooks.json` と `hooks/feature_map_hook.py` を確認し、信頼できる内容か判断してください。HookスクリプトはPluginファイルが実行環境に存在する場合だけ動作します。Web上でPluginを追加しただけでは、ローカル環境へスクリプトは配置されません。

## Hookの動作

同梱するHookは、役割を必要最小限に絞っています。

1. `UserPromptSubmit`: 曖昧さの兆候を検出し、Feature Mapの必要部分だけを読み、コンテキスト充足度を確認する方針をCodexへ渡します。曖昧な単語があるだけでは止めません。ソースやテストなどを確認しても実行結果が変わる情報不足が残る場合だけ、対象操作の前に自然な日本語で1問確認します。
2. `SessionStart`: Feature Mapを1つ特定し、XML全体ではなく必要な要約だけをコンテキストへ追加します。
3. `PostToolUse`（`Edit|Write`）: 変更ファイルを追跡し、Feature Map XMLが壊れた場合だけ検出します。
4. `PostToolUse`（`mcp__xquery__xml_validate_schema`）: xquery-mcpでXSD検証に成功したXMLのcanonical hashを記録します。
5. `Stop`: XML状態の矛盾を確認し、Feature Map変更後のXSD検証を必須にします。必要に応じてJevへ、コードやテストの変更をFeature Mapへ残すべきか問い合わせます。

プロンプト受信時のHookは、強制停止ではなく `additionalContext` を使います。コンテキスト不足は意味上の問題なので、regexの一致だけでは判断しません。Codexがsource / tests / config / Feature Mapを先に確認し、それでも不足が残る場合だけ質問します。

Stopの再実行回数は `FEATURE_MAP_MAX_STOP_BLOCKS` で制限し、既定値は `2` です。

## 操作可能で自然な日本語

ユーザー向けの指示や確認文は、次の原則で作ります。

- 文章を整える前に意味を確定する
- 実行結果を変える情報不足だけ質問する
- 確認するときは、現在の理解を先に示す
- 可能なら `はい` または短い訂正だけで答えられる形にする
- スコープ、対象外、確信度、数値、コード上の識別子を変えない
- 条件が定義されていない `適宜`、`必要に応じて`、`関連箇所`、`全部` などを、そのまま実行条件として使わない
- 明確さのために不自然な短文を並べず、普通の日本語で同じ意味を安全に表現する
- 一文一義を意識しつつ、自然な「条件→操作」の関係まで機械的に分割しない

実行環境で `natural-japanese` Skillを利用できる場合は、意味を確定した後の最終表現にクイックモードの考え方を使います。単独利用できる最小ルールも `references/operable-japanese.md` に同梱しています。

## Mermaid図

Feature Map 1.3では、MermaidソースをXML内へ直接保持できます。記号や改行を読みやすく保つため、CDATAで記述します。

```xml
<diagrams>
  <diagram id="DG1" kind="sequence" title="Receiving flow"><![CDATA[
sequenceDiagram
    User->>ReceivingService: Import
    ReceivingService->>InventoryService: GetStock
    InventoryService-->>ReceivingService: Stock
  ]]></diagram>
</diagrams>
```

`feature-map.xsl` はこのブロックを自動描画します。生成HTMLは、まず同じフォルダの `feature-map.mermaid.min.js` を読み込みます。存在しない場合は、jsDelivr上のMermaid 12.0.0へフォールバックします。描画時の `securityLevel` は `strict` です。

Mermaid 12はモダンブラウザ向けです。描画結果の変化を抑えるため、`layout: dagre`、`theme: default`、`look: classic` を固定しています。

オフラインまたはローカルのMermaid runtimeを使う場合は、Feature Mapと同じ場所へ配置します。

```sh
./scripts/setup-mermaid.sh .
```

```powershell
./scripts/setup-mermaid.ps1 -Destination .
```

全クラスから機械的に図を作ることは想定していません。境界、システム間連携、状態遷移、データ関係など、**ソースコードを追うより図で見た方が理解コストが下がる場合だけ**残します。

## OSS公開用ファイル

リポジトリのルートとしてそのまま使えるよう、以下を同梱しています。

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.github/CODEOWNERS`
- Issue / PRテンプレート
- Dependabot設定
- CI / Release workflow
- `docs/github-repository-settings.md`

GitHub側で設定する推奨値は `docs/github-repository-settings.md` にまとめています。

## Jev連携（任意）

Jevは既定では無効です。用途を2つに分けています。

### 完了時のJev判定

`FEATURE_MAP_JEV_MODE` を設定します。

- `off`: TypeSafeへ送信しない（既定）
- `metadata`: Feature Mapの状態、変更ファイル名、git diff統計のみ
- `summary`: metadataに加え、現在のCodex応答を最大3000文字送信
- `diff`: summaryに加え、git diffを最大8000文字送信

`update_required`、`update_section`、`human_review_required` のような閉じた判断だけを返します。

### プロンプト受信時のJev判定

`FEATURE_MAP_CONTEXT_JEV_MODE` を設定します。

- `off`: TypeSafeへ送信しない（既定）
- `metadata`: Feature Mapメタデータ、プロンプト長、ローカルで検出したカテゴリ、高影響Open件数を送信。プロンプト本文は送信しません
- `prompt`: metadataに加え、プロンプト本文を最大3000文字送信

`context_sufficient`、`question_required`、`missing_context_type` を参考値として返します。最終的に質問するかどうかは、Codexがローカル情報を確認して判断します。

どちらも `TYPESAFE_API_KEY` が必要です。TypeSafe APIが利用できない場合はfail-openで処理を継続します。

例:

```sh
export TYPESAFE_API_KEY='...'
export FEATURE_MAP_JEV_MODE='summary'
export FEATURE_MAP_CONTEXT_JEV_MODE='metadata'
```

PowerShell:

```powershell
$env:TYPESAFE_API_KEY = '...'
$env:FEATURE_MAP_JEV_MODE = 'summary'
$env:FEATURE_MAP_CONTEXT_JEV_MODE = 'metadata'
```

調整可能な環境変数:

- `FEATURE_MAP_JEV_MODEL`（既定: `jev-latest`）
- `FEATURE_MAP_JEV_UPDATE_THRESHOLD`（既定: `0.70`）
- `FEATURE_MAP_JEV_REVIEW_THRESHOLD`（既定: `0.85`）
- `FEATURE_MAP_CONTEXT_QUESTION_THRESHOLD`（既定: `0.75`）
- `FEATURE_MAP_MAX_STOP_BLOCKS`（既定: `2`）
- `FEATURE_MAP_PATH`（Feature Mapが複数ある場合に対象XMLを明示）

JevはTypeSafeの外部APIです。ソースコードやプロンプトを外部サービスへ送信できない契約・ポリシーのプロジェクトでは、本文を送信するモードを有効にしないでください。両方のJevモードが `off` の場合、PluginからTypeSafeへリポジトリ内容やプロンプト本文は送信しません。

## Feature Map 1.3

1.3では、1.2のコンテキスト項目を維持したまま、Mermaid図を追加しました。

- `goal/exclude`: 明示した方がスコープ誤認を防げる対象外境界
- `open/item@type`: `scope`、`authority`、`business-rule`、`expected-behavior`、`acceptance`、`external-dependency`、`data`、`environment` など、永続的な不足情報の分類
- `diagrams/diagram`: class、sequence、use-case、state、ER、flow、architectureなどのMermaidソース

同梱XSDは、後方互換のためFeature Map `1.1` と `1.2` も受け付けます。

## 通常の開発フロー

1. ユーザーの依頼を受け取る。
2. Context Sufficiency Gateで、会話やローカル情報を再利用してから質問要否を判断する。
3. 実行結果を変える重大な不足が残る場合だけ、自然な日本語で1問確認する。解決するまで、曖昧さに依存する範囲は編集しない。
4. 対象Featureの `feature-map.xml` を作成、または既存ファイルを特定する。
5. XPathで必要なノードだけ読む。
6. ソースコードとテストを直接確認する。
7. 永続的な知識の差分だけXMLへ反映する。
8. xquery-mcpで現在のXMLを `feature-map.xsd` に対して検証する。
9. Stop Hookで、XSD検証漏れやFeature Mapへの反映漏れを検出する。
10. 履歴はGitに任せ、XML内へ変更履歴セクションを作らない。

再利用可能なワークフロー本体は `skills/feature-map-workflow/` にあります。
