import json
import os
import sys

from dotenv import load_dotenv

from .crew import FinMemoCrew


def validate_environment() -> None:
    missing_keys = [
        name for name in ("GEMINI_API_KEY", "SERPER_API_KEY") if not os.getenv(name)
    ]
    if missing_keys:
        names = ", ".join(missing_keys)
        raise RuntimeError(
            f"Missing required environment variable(s): {names}. "
            "Add them to the project's .env file before running."
        )


def run_for_ticker(ticker: str) -> dict:
    load_dotenv()
    validate_environment()

    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print(f"\nRunning FinMemoCrew for {ticker}\n")
    FinMemoCrew().crew().kickoff(inputs={"ticker": ticker})

    critique_path = "output/critique_report.json"
    critique = {}
    if os.path.exists(critique_path):
        with open(critique_path, "r", encoding="utf-8") as f:
            critique = json.load(f)

    result = {
        "ticker": ticker.upper(),
        "memo_path": "output/investment_memo_draft.md",
        "critique_path": critique_path,
        "handoffs_path": "logs/handoffs.jsonl",
        "verification_passed": critique.get("verification_passed"),
        "critique": critique,
    }

    print("\n" + "=" * 60)
    print("RUN COMPLETE")
    print("=" * 60)
    print(f"Memo:      {result['memo_path']}")
    print(f"Critique:  {result['critique_path']}")
    print(f"Handoffs:  {result['handoffs_path']}")
    print(f"\nVerification passed: {result['verification_passed']}")

    if not result["verification_passed"]:
        print("\nThe critic flagged issues — review before trusting the memo:")
        for claim in critique.get("unsupported_claims", []):
            print(f"  - [unsupported claim] {claim}")
        for gap in critique.get("missing_considerations", []):
            print(f"  - [missing] {gap}")
        for issue in critique.get("logical_issues", []):
            print(f"  - [contradiction] {issue}")

    return result


def run() -> None:
    ticker = sys.argv[1].strip().upper() if len(sys.argv) > 1 else input(
        "Enter a stock ticker (e.g. AAPL): "
    ).strip().upper()
    run_for_ticker(ticker)


if __name__ == "__main__":
    run()
