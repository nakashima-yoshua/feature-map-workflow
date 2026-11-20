# 関連リポジトリ / Related repositories

**FMWの責務**は業務機能単位の永続的知識と根拠への参照です。以下のリンクは責務の案内であり、実行時依存や統合済みのAPIを意味しません。

| 他のリポジトリ | FMWとの関係 | 現状・責務境界 |
| --- | --- | --- |
| [system-understanding-architecture](https://github.com/nakashima-yoshua/system-understanding-architecture) | 全体理解の参照設計と新規参加者向け学習順序 | FMWは機能詳細、全体の正本は導入先に置く。ドキュメント参照 |
| [cli-test-mcp](https://github.com/nakashima-yoshua/cli-test-mcp) | テスト定義・実行と原証跡。FMWからケースID・証跡を参照 | 任意の外部ツール。FMWは実行やテストPASSを保証しない |
| [quality-gate](https://github.com/nakashima-yoshua/quality-gate) | 実際の変更・レビュー・証跡の版付き準備度判定 | 独立した評価器。ホスト側の接続が必要、人間の承認は別 |
| [architecture-decision-system](https://github.com/nakashima-yoshua/architecture-decision-system) | 設計規則・Decision ID・制約の参照、選択的なContext連携 | 任意アダプターは設計記載。FMWのCore必須依存にはしない |

## 正本と現実の区別

- 導入先リポジトリは合意済み要求、実装、DB資産、環境設定、運用Runbookの正本を持つ。FMWのXMLは重複した第二のソースコード集ではない。
- cli-test-mcpやCIの実行結果を確認せず、Feature Mapの `verify/case` の状態を単独で合格証拠としない。
- quality-gateの準備完了は権限ある人間によるPR・リリース承認ではない。
- ADSがパターンを選択しても、業務上の正解や承認とはみなさない。
- 実装済み、任意、構想段階を混同しない。現状は各リポジトリのREADME・コード・テストを確認する。相互リンクのためだけに新しい強制依存を作らない。
