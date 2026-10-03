# Agents API PoC

This example starts one Feature Map Workflow session with an OpenAI Agents API self-hosted environment.

It defaults to read-only investigation. Use `--allow-write` only when the parent agent is authorized to change the selected worktree.

## Prerequisites

- current OpenAI Python SDK;
- `OPENAI_API_KEY` with Agents API permissions;
- a self-hosted Agents API environment capable of using the selected workspace;
- this repository checked out as the workspace.

Install/update the SDK:

```sh
python -m pip install --upgrade openai
```

Read-only catch-up:

```sh
python examples/agents-api/run_feature_map.py \
  --workspace /path/to/repository \
  "Trace the receiving feature, identify the business scenarios and important data effects, and report unresolved evidence gaps."
```

Authorized change:

```sh
python examples/agents-api/run_feature_map.py \
  --workspace /path/to/worktree \
  --allow-write \
  "Implement the approved change and update only durable Feature Map deltas."
```

The parent agent is the only canonical writer. Subagents are for parallel read-only investigation.
