import json
import os
import unittest
from unittest.mock import patch

from src.finmemo_crew.crew import FinMemoCrew
from src.finmemo_crew.models import CompanyData, CritiqueReport, QuantAnalysis, RiskAssessment
from src.finmemo_crew.tools.news_search_tool import news_search_tool


class ProjectTests(unittest.TestCase):
    def test_models_accept_expected_contracts(self):
        company = CompanyData(
            ticker="TEST",
            company_name="Test Company",
            fundamentals_raw="{}",
            price_trend_summary="No price history available.",
        )
        self.assertEqual(company.recent_news, [])

        self.assertIsInstance(QuantAnalysis(
            valuation_ratios_summary="Unavailable",
            growth_trend_analysis="Unavailable",
            margin_analysis="Unavailable",
            sector_comparison="Unavailable",
            valuation_verdict="Unavailable",
        ), QuantAnalysis)
        self.assertIsInstance(RiskAssessment(flags=[], overall_risk_level="low"), RiskAssessment)
        self.assertIsInstance(CritiqueReport(verification_passed=True, notes="No issues"), CritiqueReport)

    def test_crew_has_expected_sequential_pipeline(self):
        crew = FinMemoCrew().crew()

        self.assertEqual(len(crew.agents), 5)
        self.assertEqual(len(crew.tasks), 5)
        self.assertEqual([task.name for task in crew.tasks], [
            "gather_data_task",
            "quant_analysis_task",
            "risk_assessment_task",
            "write_memo_task",
            "verify_memo_task",
        ])
        self.assertEqual(str(crew.process), "Process.sequential")

    def test_news_search_reports_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = json.loads(news_search_tool.run("TEST recent news"))

        self.assertIn("error", result)
        self.assertIn("SERPER_API_KEY not set", result["error"])


if __name__ == "__main__":
    unittest.main()