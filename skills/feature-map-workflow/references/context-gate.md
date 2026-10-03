# Context Sufficiency Gate

## Purpose

Ask the user only when missing context can materially change the result, authority, or major risk. Do not use clarification as a substitute for repository investigation.

## Decision order

1. Read the user's request literally.
2. Reuse current conversation and Feature Map context.
3. Inspect cheap local evidence when it can resolve the ambiguity: source, tests, config, schema, logs, or similar implementation.
4. Identify the narrowest reasonable interpretation.
5. Ask only when the remaining gap materially changes the action.

## Material missing-context categories

- `scope`: target boundary is ambiguous.
- `authority`: requested action may exceed explicit execution permission or become irreversible/external.
- `business_rule`: correct behavior depends on an unstated domain rule.
- `expected_behavior`: more than one externally visible result is plausible.
- `acceptance`: completion cannot be tested without a success condition.
- `external_dependency`: behavior depends on another system, contract, service, or party.
- `data`: required data semantics or destructive data handling are uncertain.
- `environment`: target environment or deployment boundary changes the action materially.
- `other`: rare cases that do not fit above.

## Ask

Ask when one of the following remains unresolved after cheap investigation:

- different interpretations cause materially different code/data changes;
- the request could cross a stated or likely permission boundary;
- deletion, migration, production modification, publication, external sending, payment, authentication/authorization, public interface, schema, or contractual behavior could be affected;
- acceptance criteria differ depending on the missing fact;
- proceeding would create significant rollback or data-correction cost.

Ask exactly one question. Prefer a question that resolves the largest branch in the decision tree.

## Do not ask

Proceed with an explicit minimal assumption when all of these are true:

- the action is low-risk and reversible;
- the repository or Feature Map strongly implies one interpretation;
- the assumption does not broaden scope or authority;
- correcting the assumption later has low cost.

Do not ask the user to repeat information already available in the conversation, Feature Map, source, tests, config, logs, or attached material.

## Feature Map interaction

A transient prompt ambiguity does not automatically belong in XML.

Add an `open/item` only when the unresolved question is durable feature knowledge that affects later understanding, implementation, or acceptance. Use `type` to classify it. Remove the item or convert the resolved fact into the appropriate durable section when the answer becomes known.
