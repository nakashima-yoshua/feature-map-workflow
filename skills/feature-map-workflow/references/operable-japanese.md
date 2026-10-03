# Operable Japanese

## Goal

Write Japanese that a human can read naturally and an AI or developer can act on without guessing. Do not turn Japanese into a rigid controlled language. Fix meaning first, then improve the surface expression.

Priority:

`meaning preservation > operability > naturalness > brevity`

## Internal meaning contract

Before rendering an instruction or clarification, identify only the slots that affect the current action:

- `goal`: intended outcome.
- `actor`: who acts, only when responsibility is ambiguous.
- `action`: concrete operation.
- `target`: object being read, changed, sent, deleted, etc.
- `condition`: condition under which the action applies.
- `scope`: included boundary.
- `exclude`: explicitly unchanged boundary.
- `authority`: whether the user authorized the action.
- `doneWhen`: acceptance/completion condition.
- `certainty`: confirmed, assumed, inferred, or unknown.

Do not expose this structure to the user unless structured output is useful. It is a reasoning contract, not a writing template.

## Natural rendering rules

Use the following principles, aligned with the `natural-japanese` skill:

1. Put the conclusion or current interpretation first. Remove ceremonial preambles.
2. Prefer one semantic claim per sentence. Do not split a natural condition-action relation merely to shorten the text.
3. State the subject or actor only when omission creates ambiguity. Japanese does not need an explicit subject in every sentence.
4. Keep a condition close to the action it controls. Keep a modifier close to the word it modifies.
5. Preserve modality and certainty. Do not convert `可能`, `推奨`, `必要`, `未確認`, or `推定` into stronger/weaker claims.
6. Preserve identifiers exactly: file names, symbols, SQL objects, APIs, config keys, issue IDs, numeric limits, and dates.
7. Avoid undefined execution words such as `適宜`, `必要に応じて`, `関連箇所`, `全部`, `可能な限り`, `問題があれば`, `適切に`, and `いい感じに`. Define their condition or boundary when they affect execution.
8. Avoid vague demonstratives (`これ`, `それ`, `こちら`, `該当`) when more than one referent is plausible.
9. Use lists only for genuinely parallel items. Express causality and sequence in ordinary prose when that reads more naturally.
10. Do not repeat the same confirmation template mechanically. Keep the semantic structure stable but vary ordinary Japanese wording when there is no loss of precision.
11. Do not add facts for fluency. A smoother sentence with invented cause, scope, or confidence is wrong.
12. Shortness is a tiebreaker, not the objective. Longer wording is correct when it removes a genuine ambiguity.

## Clarification pattern

Ask one question at a time. State the current interpretation before asking.

Preferred shape:

```text
【確認】<current interpretation>。<important scope/exclusion if needed>。
この理解で進めてよいですか？
```

Use a more specific final question when a yes/no answer is not possible, but still present the current interpretation first.

### Example

Input:

`関連するDBも全部直して。`

Internal gap:

- target: DB objects are not identified.
- scope: `関連する` and `全部` are undefined.
- authority: schema/data migration may be broader than the feature change.

Natural clarification:

`【確認】注文機能が直接更新する3テーブルまでを変更対象とし、他機能と共用するテーブルは変更しない理解です。この範囲で進めてよいですか？`

## Assumption pattern

Do not ask when the ambiguity is low-risk and reversible.

Example:

`表示文言を少し整えて。`

If the repository clearly identifies one changed screen and no public contract changes:

`対象画面の既存文言だけを整え、画面遷移やAPI仕様は変更しない前提で進めます。`

Then proceed.
