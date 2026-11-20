# 新規参加者のキャッチアップ（New Member Catch-up）

## 目的と責務

初参加の人間やAIが、**既存の正本と実行可能な根拠**を使って、未知の業務機能を安全に理解し、小さな承認済み作業をレビューに出せる状態にするための任意ガイド。

FMWは業務機能単位の永続的知識と参照先を管理する。人事的な研修進捗、アクセス許可、実行キュー、全体アーキテクチャ、テストの実行・原証跡、マージ承認の正本は持たない。全体理解と人向けオンボーディングの標準は [system-understanding-architecture](https://github.com/nakashima-yoshua/system-understanding-architecture) を参照し、実システムの情報は導入先のリポジトリを正本とする。

## 実施前に必要な情報

- 対象の既存リポジトリとGitコミット、対象業務機能1件（`UC-...`）、担当者・相談先。
- 承認済みの検証環境と操作範囲。読み取り以外の操作は別途明示的な許可が必要。
- 既存の要求/設計/Runbook/テストとFeature Mapの所在。不足は不足として記録する。
- 最初の作業のIssue/Change Contract、対象外、受入条件。学習のために未承認の実装や本番操作を行わない。

## 進め方（小さな1機能で完結）

1. **俯瞰（人が説明できる状態）**: 導入先の業務概要、アーキテクチャ、重要な不変条件、運用上の責務を確認する。目的の機能を1件選び、既存のFeature Mapとソース・テストを読む。READMEやガイドを再帰的に全部読み込まない。
2. **処理経路の追跡**: UI/API/ジョブなどの実際の入口から、コード、SQL/ストアド、DB更新、外部IF、後続処理を追う。[Legacy Analysis](legacy-analysis.md) を必要な範囲で使用。静的な**可能経路**と実行で確認した**観測経路**を区別する。
3. **代表的な図と根拠**: 説明に必要な場合のみ、[Three Complementary Views](three-view-understanding.md)から業務・データ・ERの図を選ぶ。出典のない関連や、JOINから推測した物理FKを確定しない。
4. **安全な動作確認**: 許可済みの隔離/検証環境で既存スモークテスト、代表正常系、重要な異常系を確認する。実行コマンド、環境、Git SHA、ネイティブの証跡位置を記録する。未実行なら `NOT_RUN`、実行不能なら `BLOCKED`。実行結果を推測で補わない。
5. **知識更新**: 既存Feature Mapに継続価値のある確定差分だけ反映する。確認済み業務ルール、未解決事項、ソース・ケース・証跡のID/版付き参照を保持。初作成なら既存 `init_feature_map.py --mode catchup` を使い、[Feature Map Contract](feature-map-contract.md)に従いXSD検証を行う。重複や再構築容易な情報を複写しない。差分がなければ `NO FEATURE MAP CHANGE`。
6. **最初の小作業**: 明示的に合意されたIssue/変更契約の範囲で、テスト追加か軽微な修正を1件だけ行う。影響・不変条件・回帰と戻し方を説明し、コード・テスト・証跡を同じGit版に結びつける。品質判定と人間レビューは外部で実施し、ここではマージ・デプロイをしない。
7. **フィードバック**: 見つけにくい情報、古い入口、再現不能な手順を導入先のオンボーディング文書・Issueへ返す。業務上の確定知識だけFMWへ記録する。新しい学習進捗台帳を作らない。

## 完了を判定する実物

| 観点 | 第三者が確認できる成果 |
| --- | --- |
| 全体像 | 対象機能の目的、責務、重大な不変条件を説明 |
| 入口から結果 | `UC` → 実装/SQL/DB/外部効果 → 代表テストを出典で追跡 |
| 検証 | 実行結果または未実行/障害をGit版とともに説明 |
| 小さな仕事 | 承認済みの変更についてレビュー可能なPRや差分と検証根拠 |
| 引継ぎ | 未解決項目と最安の次の確認、Runbook・相談先を提示 |

期間は目安であり、日数経過だけで完了としない。危険なDB更新、無権限のログ/秘密情報の参照、復旧実行、権限拡大は研修の対象外。必要なら権限者の確認に切り替える。

## 既存資産をどう再利用するか

- キャッチアップの形式と知識状態: [Feature Map Contract](feature-map-contract.md)
- 既存システムの隠れた依存・復旧経路: [Legacy Analysis](legacy-analysis.md)
- テストと検証根拠: [Test Strategy](test-strategy.md) / [Evidence Storage](evidence-storage.md)
- **新規参加者**と**長期AIセッションの再開**は別物。後者は [Long-running Sessions](long-running-sessions.md) の任意・読み取り専用 `build_session_brief.py` を利用できるが、同スクリプトは環境構築や技能評価を実施しない。

English summary: Newcomers first study the project's system-level context, then trace one verified feature end-to-end, run only authorized tests, persist only durable deltas in the existing Feature Map and submit a bounded first change for human review. This guide adds no new schema, runner, gate, or approval authority.
