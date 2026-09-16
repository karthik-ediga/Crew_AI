"""
Market data tool backed by yfinance. No API key required.

Returns a compact JSON string so the LLM gets structured numbers instead of
having to eyeball a table — this feeds the `fundamentals_raw` and
`price_trend_summary` fields of CompanyData.
"""

import json

import yfinance as yf
from crewai.tools import tool


@tool("Market Data Lookup")
def market_data_tool(ticker: str) -> str:
    """
    Fetch current price, key fundamentals, and a 1-year price trend for a
    stock ticker symbol (e.g. 'AAPL', 'MSFT') using Yahoo Finance data.

    Args:
        ticker: The stock ticker symbol to look up.

    Returns:
        A JSON string with company name, sector, current price, market cap,
        P/E ratio, selected fundamentals, and a 1-year high/low/change summary.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="1y")

        if hist.empty:
            price_trend = "No price history available."
        else:
            start_price = float(hist["Close"].iloc[0])
            end_price = float(hist["Close"].iloc[-1])
            high = float(hist["Close"].max())
            low = float(hist["Close"].min())
            pct_change = ((end_price - start_price) / start_price) * 100 if start_price else 0
            price_trend = (
                f"1-year change: {pct_change:.1f}% "
                f"(from {start_price:.2f} to {end_price:.2f}); "
                f"52-week range approx {low:.2f}-{high:.2f}."
            )

        result = {
            "ticker": ticker.upper(),
            "company_name": info.get("longName") or info.get("shortName") or ticker.upper(),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "profit_margins": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "return_on_equity": info.get("returnOnEquity"),
            "free_cashflow": info.get("freeCashflow"),
            "price_trend_summary": price_trend,
        }
        return json.dumps(result, default=str)

    except Exception as e:  # noqa: BLE001
        return json.dumps({"error": f"Failed to fetch market data for {ticker}: {e}"})
