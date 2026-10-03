#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from openai import OpenAI


def build_instructions(allow_write: bool) -> str:
    write_policy = (
        "You are the single canonical writer for this session. Reader subagents are read-only. "
        "You may edit only when the user's scope and authority are sufficient."
        if allow_write
        else
        "This is a read-only investigation. Do not edit files, commit, push, or mutate external systems."
    )
    return (
        "Use the repository's skills/feature-map-workflow/SKILL.md as the workflow contract. "
        "Read only the reference files needed for the task. "
        "For bounded XPath/XQuery/filter/aggregate stages, use Programmatic Tool Calling and reduce intermediate results before reasoning. "
        "Do not use programmatic calls for repository writes, Git publication, approvals, or external side effects. "
        "Delegate independent source/test/data investigation to subagents when useful, but keep all subagents read-only. "
        + write_policy
        + " Keep source and tests canonical, keep Feature Map XML compact, and distinguish confirmed evidence from inference."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Feature Map Workflow in an OpenAI Agents API self-hosted session."
    )
    parser.add_argument("task", help="Bounded feature-analysis or change task")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Repository worktree used by the self-hosted environment",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_AGENT_MODEL", "gpt-6-astra"),
    )
    parser.add_argument(
        "--readers",
        type=int,
        default=3,
        help="Maximum concurrent read-only subagents",
    )
    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="Allow the parent agent to make repository changes. Subagents remain read-only.",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    skill_dir = workspace / "skills"
    if not (workspace / "skills" / "feature-map-workflow" / "SKILL.md").is_file():
        raise SystemExit(f"Feature Map Workflow skill not found under {workspace}")

    tools = [
        {"type": "programmatic_tool_calling"},
        {
            "type": "mcp",
            "server_label": "xquery",
            "transport": {
                "type": "stdio",
                "command": "dotnet",
                "args": ["tool", "run", "xquery-mcp"],
                "cwd": str(workspace),
            },
            "allowed_tools": [
                "xpath_evaluate",
                "xquery_evaluate",
                "xquery_validate",
                "xml_validate_schema",
                "xml_format",
            ],
            "required": False,
        },
    ]
    agent = {
        "model": args.model,
        "instructions": build_instructions(args.allow_write),
        "tools": tools,
        "multi_agent": {
            "enabled": True,
            "max_concurrent_subagents": max(1, args.readers),
        },
    }
    environment = {
        "type": "self_hosted",
        "workspace_directory": str(workspace),
        "capability_directories": [str(skill_dir)],
    }

    with OpenAI() as client:
        with client.beta.agents.sessions.create(
            agent=agent,
            environment=environment,
            input=args.task,
            stream=True,
        ) as events:
            for event in events:
                print(event.to_json(indent=None), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
