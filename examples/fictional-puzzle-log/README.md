# 完全に仮想のFeature Map例

「パズル記録帳」を題材にした公開用の例です。個人・顧客・組織の業務情報は使っていません。名前、ID、ルール、参照先はすべて創作です。実装は同梱せず、テストも未実行のため、XMLの状態は `draft`、検証項目は `planned` としています。

`feature-map.xml` は Feature Map 1.3のXSDに沿い、登録の条件分岐、完成操作のシーケンス、状態遷移のMermaid図を含みます。実際のプロジェクトで使う際は、仮想の参照先を実在するソース・テストに置き換えます。

別の[AI支援テスト例](../ai-assisted-testing/README.md)には、このXMLのIDを参照する実行可能なアダプターがあります。その実行結果で、本XMLの `draft` / `planned` が自動更新されることはありません。

## HTMLを生成して表示する

リポジトリのルートでPowerShellから実行します。PowerShell標準の.NET機能でXSD検証とXSLT変換を行うため、追加パッケージは不要です。

```powershell
./examples/fictional-puzzle-log/render.ps1
Start-Process ./examples/fictional-puzzle-log/feature-map.html
```

生成した `feature-map.html` をブラウザで開いて閲覧します。XMLを編集したら、再度 `render.ps1` を実行してください。XMLを直接開く方法はブラウザのXSLT対応に依存するため、この例ではHTMLへ変換します。

Mermaidは既存XSLTのローダーが読み込みます。同じフォルダの `feature-map.mermaid.min.js` を優先し、なければjsDelivrのMermaid 12.0.0を使います。CDN利用にはインターネット接続が必要です。読み込めない場合も図のソースは表示されます。

オフラインで図を表示するには、オンライン環境で次のコマンドを事前に一度だけ実行し、Mermaid本体とライセンスをダウンロードしておきます。ダウンロード後、HTMLを開き直してください。

```powershell
./scripts/setup-mermaid.ps1 -Destination ./examples/fictional-puzzle-log
```

図がソースのままの場合は、Diagrams欄のステータス表示と、ブラウザの開発者ツールで読み込みエラーを確認してください。

