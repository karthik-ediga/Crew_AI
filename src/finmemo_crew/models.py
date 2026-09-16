"""
Pydantic schemas that define the exact input/output contract between agents.

Every task in crew.py declares one of these as its `output_pydantic`, so the
LLM's output is validated into a structured object instead of trusting free
text to be well-formed. If an agent's output doesn't fit the schema, CrewAI
will raise instead of silently passing malformed data to the next agent.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    headline: str
    source: str
    date: str
    summary: str = Field(description="1-2 sentence summary of the article")


class CompanyData(BaseModel):
    """Output of data_gatherer. Input to every downstream agent."""

    ticker: str
    company_name: str
    sector: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    fundamentals_raw: str = Field(
        description="Raw key fundamentals as a compact text/JSON blob "
        "(revenue, margins, debt, cash, growth rates, etc.)"
    )
    price_trend_summary: str = Field(
        description="Plain-language summary of the 1-year price trend"
    )
    recent_news: List[NewsItem] = Field(default_factory=list)


class QuantAnalysis(BaseModel):
    """Output of quant_analyst. Input to memo_writer and critic."""

    valuation_ratios_summary: str = Field(
        description="Key ratios (P/E, P/B, EV/EBITDA, etc.) and what they indicate"
    )
    growth_trend_analysis: str
    margin_analysis: str
    sector_comparison: str = Field(
        description="How this company's multiples/margins compare to sector peers"
    )
    valuation_verdict: str = Field(
        description="undervalued / fairly valued / overvalued, with the reasoning — "
        "not a buy/sell instruction, a valuation observation"
    )


class RiskFlag(BaseModel):
    category: str = Field(
        description="e.g. financial, competitive, regulatory, macro, governance"
    )
    description: str
    severity: str = Field(description="low, medium, or high")
    evidence: str = Field(description="what in the gathered data supports this flag")


class RiskAssessment(BaseModel):
    """Output of risk_analyst. Input to memo_writer and critic."""

    flags: List[RiskFlag]
    overall_risk_level: str = Field(description="low, medium, or high")


class CritiqueReport(BaseModel):
    """Output of critic. The v1 verification gate."""

    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims in the memo that don't trace back to CompanyData, "
        "QuantAnalysis, or RiskAssessment",
    )
    missing_considerations: List[str] = Field(
        default_factory=list,
        description="Material risks or facts the memo should have covered but didn't",
    )
    logical_issues: List[str] = Field(
        default_factory=list,
        description="Internal contradictions, e.g. bull case ignoring a high-severity risk flag",
    )
    verification_passed: bool = Field(
        description="True only if there are no unsupported claims and no major "
        "missing considerations"
    )
    notes: str = Field(description="Short free-text summary of the review")
