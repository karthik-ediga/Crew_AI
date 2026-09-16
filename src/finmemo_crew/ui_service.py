import json
import re
from pathlib import Path


def build_agent_status():
    return [
        {
            "name": "Data Gatherer",
            "role": "Collects price, fundamentals, and market headlines",
            "status": "ready",
            "avatar": "📊",
        },
        {
            "name": "Quant Analyst",
            "role": "Evaluates valuation, growth, and margin trends",
            "status": "ready",
            "avatar": "📈",
        },
        {
            "name": "Risk Analyst",
            "role": "Flags operational, financial, and macro risks",
            "status": "ready",
            "avatar": "⚠️",
        },
        {
            "name": "Memo Writer",
            "role": "Produces the balanced investment memo",
            "status": "ready",
            "avatar": "✍️",
        },
        {
            "name": "Critic",
            "role": "Verifies claims against the evidence and catches gaps",
            "status": "ready",
            "avatar": "🧠",
        },
    ]


def parse_memo_metadata(memo_text: str) -> dict:
    """Extracts top-line company metadata from the generated markdown memo."""
    data = {}
    patterns = {
        "ticker": r"\*\*Ticker:\*\*\s*(.+)",
        "company_name": r"\*\*Company Name:\*\*\s*(.+)",
        "sector": r"\*\*Sector:\*\*\s*(.+)",
        "industry": r"\*\*Industry:\*\*\s*(.+)",
        "current_price": r"\*\*Current Price:\*\*\s*(.+)",
        "market_cap": r"\*\*Market Capitalization:\*\*\s*(.+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, memo_text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
    return data


def load_handoff_traces(log_file: str = "logs/handoffs.jsonl", limit: int = 15) -> list:
    """Loads recent handoff records from the handoffs log."""
    path = Path(log_file)
    if not path.exists():
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []
    return records[-limit:]


def extract_pipeline_details(records: list) -> dict:
    """Extracts quant analysis, risk flags, and company data from recent handoff records."""
    details = {
        "company_data": {},
        "quant_analysis": {},
        "risk_assessment": {"flags": [], "overall_risk_level": "medium"},
    }

    for record in reversed(records):
        agent_name = record.get("agent", "").lower()
        preview = record.get("output_preview", "")

        # Try to parse preview if it contains JSON
        clean_preview = preview.strip()
        if clean_preview.startswith("```json"):
            clean_preview = clean_preview[7:]
        if clean_preview.startswith("```"):
            clean_preview = clean_preview[3:]
        if clean_preview.endswith("```"):
            clean_preview = clean_preview[:-3]
        clean_preview = clean_preview.strip()

        parsed = {}
        try:
            parsed = json.loads(clean_preview)
        except Exception:
            pass

        if "quant" in agent_name and not details["quant_analysis"] and isinstance(parsed, dict):
            details["quant_analysis"] = parsed

        if "risk" in agent_name and not details["risk_assessment"]["flags"] and isinstance(parsed, dict):
            if "flags" in parsed:
                details["risk_assessment"] = parsed

        if "data gatherer" in agent_name and not details["company_data"] and isinstance(parsed, dict):
            details["company_data"] = parsed

    return details
