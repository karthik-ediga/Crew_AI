# Financial Research & Investment-Memo Crew

An autonomous multi-agent CrewAI research pipeline that converts any stock ticker into a structured, source-grounded investment memo — featuring a built-in verification and critique step instead of blindly trusting the final LLM output.

Includes both a **CLI pipeline** and a **Modern Fintech Terminal Web Dashboard** built with Streamlit.

---

## Key Design Principles

Based on the MAST multi-agent failure-mode research (41.8% of multi-agent failures trace to bad specs, 36.9% to inter-agent misalignment, 21.3% to weak verification):

1. **Explicit Pydantic Contracts**: Every agent's input and output schema is strictly enforced with Pydantic models — never left to unconstrained LLM parsing.
2. **Dedicated Verification Agent**: A built-in Critic / Devil's Advocate audits claims against gathered evidence before any memo is finalized.
3. **Traceable Handoffs**: Every inter-agent task handoff is logged to `logs/handoffs.jsonl` for full auditability and debugging.
4. **Deterministic Sequential Pipeline**: A linear 5-stage pipeline ensuring predictability and clean state transitions before introducing complex loops.

---

## Multi-Agent Pipeline & Architecture

```
[User Ticker]
      │
      ▼
1. Data Gatherer  ───────►  Market Data (yfinance) + News Search (Serper API)
      │                     └─► Outputs: CompanyData
      ▼
2. Quant Analyst  ───────►  Valuation Multiples, Margins, Growth & Sector Benchmarks
      │                     └─► Outputs: QuantAnalysis
      ▼
3. Risk Analyst   ───────►  Categorized Risk Factors (Financial, Competitive, Regulatory, Macro, Gov)
      │                     └─► Outputs: RiskAssessment
      ▼
4. Memo Writer    ───────►  Comprehensive Investment Memo (Exec Summary, Bull/Bear Cases)
      │                     └─► Outputs: investment_memo_draft.md
      ▼
5. Critic Analyst ───────►  Groundedness Audit & Discrepancy Flagging
                            └─► Outputs: critique_report.json
```

### Agent Roster & I/O Contract

| # | Agent | Role | Input (reads) | Output (produces) | Consumed by |
|---|---|---|---|---|---|
| 1 | `data_gatherer` | Financial Data Gatherer | `ticker` (string, from user) | `CompanyData` — price, fundamentals, recent news | quant_analyst, risk_analyst, memo_writer, critic |
| 2 | `quant_analyst` | Quantitative Analyst | `CompanyData` | `QuantAnalysis` — valuation ratios, growth/margin trends, sector comparison, valuation verdict | memo_writer, critic |
| 3 | `risk_analyst` | Risk Analyst | `CompanyData` | `RiskAssessment` — list of `RiskFlag` (category, description, severity, evidence), overall risk level | memo_writer, critic |
| 4 | `memo_writer` | Investment Memo Writer | `CompanyData` + `QuantAnalysis` + `RiskAssessment` | Markdown memo (exec summary, overview, financial analysis, risk factors, bull case, bear case, disclaimer — **no directive buy/sell call**) | critic |
| 5 | `critic` | Verification / Devil's Advocate | All agent outputs + draft memo | `CritiqueReport` — unsupported claims, missing considerations, logical issues, `verification_passed: bool` | Human reviewer & UI |

---

## Project Structure

```
finmemo_crew/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py                       # Modern Streamlit fintech dashboard
├── logs/                        # Handoff logs written here at runtime
│   └── handoffs.jsonl
├── output/                      # Memo and critique outputs
│   ├── investment_memo_draft.md
│   └── critique_report.json
├── src/finmemo_crew/
│   ├── __init__.py
│   ├── crew.py                  # CrewAI agents, tasks, and sequential pipeline
│   ├── main.py                  # CLI entry point and execution wrapper
│   ├── models.py                # Pydantic schemas (CompanyData, QuantAnalysis, etc.)
│   ├── logging_utils.py         # Task handoff logging callback
│   ├── ui_service.py            # Dashboard parsing and data service helpers
│   ├── tools/
│   │   ├── market_data_tool.py  # yfinance market fundamentals and price history
│   │   └── news_search_tool.py  # Serper API web search integration
│   └── config/
│       ├── agents.yaml          # Agent personas, goals, and backstories
│       └── tasks.yaml           # Task definitions, inputs, and output expectations
└── tests/
    ├── test_project.py          # Core pipeline and schema tests
    └── test_ui.py               # Dashboard and UI service unit tests
```

---

## Getting Started

### 1. Installation

```bash
# Clone the repository and navigate into the folder
cd finmemo_crew

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Keys

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Set the required environment variables:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

* Optional: specify model selection via `MODEL=gemini/gemini-2.5-flash` (default).

---

## Running the Application

### Option A: Modern Fintech Web Dashboard (Streamlit)

Launch the interactive UI:
```bash
streamlit run app.py
```
* **Local URL**: `http://localhost:8501`
* **Features**:
  * **1-Click Ticker Presets**: Fast testing chips (`AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `TSLA`).
  * **Live Company KPI Ribbon**: Price, Market Cap, Valuation Verdict, Risk Profile, and Audit Badge.
  * **5-Tab Analytical Workstation**:
    * 📑 **Investment Memo** (with 1-click `.md` export)
    * 📊 **Quantitative Deep-Dive** (Valuation, margins, ROE, growth, sector comparison)
    * ⚠️ **Risk Matrix** (Categorized flags with High/Med/Low severity pills and evidence)
    * 🛡️ **Verification Audit** (Passed/Flagged certificate, auditor notes, and claim checks)
    * ⚡ **Multi-Agent Trace** (Live trace of data flow across all 5 agents)

### Option B: CLI Mode

Run analysis directly from your terminal:
```bash
python -m src.finmemo_crew.main AAPL
```

---

## Deployment on Render

This application is fully compatible with [Render](https://render.com/) as a Python Web Service.

### Configuration Settings

1. Create a **New Web Service** connected to your GitHub repository.
2. Enter the following parameters:

| Field | Configuration Value |
| :--- | :--- |
| **Language** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
| **Instance Type** | `Free` |

3. Add your Environment Variables in the Render dashboard:
   - `GEMINI_API_KEY` = `<your-api-key>`
   - `SERPER_API_KEY` = `<your-serper-key>`
   - `PYTHON_VERSION` = `3.11.9`

> [!NOTE]
> Render dynamically sets the `$PORT` environment variable. The start command above ensures Streamlit binds properly to Render's allocated port.

---

## Running Tests

Run the complete test suite:
```bash
python -m unittest discover tests
```

---

## Disclaimer

This system produces research-support content for educational and portfolio purposes, not financial or investment advice. The output is intentionally structured to present a balanced, evidence-grounded bull and bear case rather than a directive buy/sell recommendation.
