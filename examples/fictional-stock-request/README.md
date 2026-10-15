# 架空の補充依頼：業務フロー × データフロー × ER図

完全に創作した「補充依頼の受付（UC-SUBMIT）」を題材に、3つの視点を同じFeature Map XMLへ保存する最小例です。**実在する顧客・業務・DB・コード・テストは含まれません。** PK/FK、多重度、業務ルールは仮想仕様であり、DB解析結果ではありません。

| 図 | Mermaidの開始宣言 | ID | 見るもの |
| --- | --- | --- | --- |
| 業務フロー | `flowchart TD` | `DG-FLOW` | 入力、業務判断、正常・エラー結果 |
| データフロー | `flowchart LR` | `DG-DFD` | 同じ業務の入力、マスタ参照、2つの書込先 |
| ER図 | `erDiagram` | `DG-ER` | `REQUEST`、`REQUEST_LINE`、`ITEM` のキーと関係 |

3つの図を `UC-SUBMIT` に結び、同じテーブル名を `sourceMap/ref` に記録しています。検証は `not-run`、Feature Mapの状態は `draft` とし、実データがないため実DBの関係を確認したと誤認させないようにしています。

## 検証・HTML表示

リポジトリルートで次を実行してください（HTML変換には `lxml` が必要です。CI環境では既に利用しています）。

```sh
python -m pip install lxml
python scripts/validate_repository.py
python -c "from lxml import etree; from pathlib import Path; p=Path('examples/fictional-stock-request'); x=etree.XSLT(etree.parse('skills/feature-map-workflow/assets/feature-map.xsl')); (p/'feature-map.html').write_bytes(bytes(x(etree.parse(str(p/'feature-map.xml')))))"
```

生成された `examples/fictional-stock-request/feature-map.html` をブラウザで開き、折りたたまれた **Diagrams** を展開します。既存XSLTがMermaid 12.0.0を読み込み、3つの図を表示します。ローカル版 `feature-map.mermaid.min.js` をHTMLの横に置くか、CDNに接続できる必要があります。読み込めないときは図のソースを確認できます。HTML生成と実ブラウザでの図の描画は別の検証です。

実プロジェクトへ適用する際は、[Three Complementary Views](../../skills/feature-map-workflow/references/three-view-understanding.md)に従い、読み取り専用のDBカタログ・コード・実行根拠から関係を確定して、必要な機能範囲の図だけを保存します。
