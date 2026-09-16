"""
Logs every inter-agent handoff to logs/handoffs.jsonl.

Per MAST (Cemri et al., 2025), a large share of multi-agent failures are
coordination breakdowns between agents — one agent silently ignoring or
misreading what a previous agent produced. That class of bug is very hard
to catch by staring at final output; it's much easier to catch by reading
a chronological log of exactly what each agent handed to the next one.

This is wired in as the `callback` on every Task in crew.py.
"""

import json
import os
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
LOG_PATH = os.path.join(LOG_DIR, "handoffs.jsonl")


def log_handoff(task_output) -> None:
    """CrewAI task callback. Receives a TaskOutput after each task finishes."""
    os.makedirs(LOG_DIR, exist_ok=True)

    agent_name = getattr(task_output, "agent", "unknown_agent")
    description = getattr(task_output, "description", "") or ""
    raw = getattr(task_output, "raw", str(task_output))

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent_name,
        "task_description": description[:200],
        "output_preview": str(raw)[:1500],
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"[handoff] {agent_name} -> next agent | {description[:60]!r}...")
