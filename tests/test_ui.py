import unittest

from src.finmemo_crew.ui_service import (
    build_agent_status,
    extract_pipeline_details,
    load_handoff_traces,
    parse_memo_metadata,
)


class TestUiService(unittest.TestCase):
    def test_build_agent_status_returns_expected_agents(self):
        statuses = build_agent_status()
        self.assertEqual(
            [item["name"] for item in statuses],
            [
                "Data Gatherer",
                "Quant Analyst",
                "Risk Analyst",
                "Memo Writer",
                "Critic",
            ],
        )
        self.assertTrue(all(item["avatar"] for item in statuses))

    def test_parse_memo_metadata(self):
        sample_memo = """
# Investment Research Memo: Apple Inc. (AAPL)

**Date:** [Current Date]
**Ticker:** AAPL
**Company Name:** Apple Inc.
**Sector:** Technology
**Industry:** Consumer Electronics
**Current Price:** $331.34
**Market Capitalization:** $4,835,635,625,984
"""
        data = parse_memo_metadata(sample_memo)
        self.assertEqual(data["ticker"], "AAPL")
        self.assertEqual(data["company_name"], "Apple Inc.")
        self.assertEqual(data["sector"], "Technology")
        self.assertEqual(data["industry"], "Consumer Electronics")
        self.assertEqual(data["current_price"], "$331.34")
        self.assertIn("$4,835,635,625,984", data["market_cap"])

    def test_extract_pipeline_details(self):
        records = [
            {
                "agent": "Quantitative Analyst",
                "output_preview": '{"valuation_verdict": "Fairly valued", "valuation_ratios_summary": "P/E 30"}',
            },
            {
                "agent": "Risk Analyst",
                "output_preview": '{"flags": [{"category": "financial", "severity": "medium", "description": "High P/E"}], "overall_risk_level": "medium"}',
            },
        ]
        details = extract_pipeline_details(records)
        self.assertEqual(details["quant_analysis"]["valuation_verdict"], "Fairly valued")
        self.assertEqual(len(details["risk_assessment"]["flags"]), 1)
        self.assertEqual(details["risk_assessment"]["overall_risk_level"], "medium")


if __name__ == "__main__":
    unittest.main()
