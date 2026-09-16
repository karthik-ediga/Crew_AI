import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .logging_utils import log_handoff
from .models import CompanyData, CritiqueReport, QuantAnalysis, RiskAssessment
from .tools.market_data_tool import market_data_tool
from .tools.news_search_tool import news_search_tool


def _gemini_llm() -> LLM:
    model = os.getenv("MODEL", "gemini/gemini-2.5-flash")
    if not model.startswith("gemini/"):
        model = f"gemini/{model}"
    return LLM(model=model, api_key=os.getenv("GEMINI_API_KEY"))


@CrewBase
class FinMemoCrew:
    """Financial research & investment-memo crew.

    v1: strictly sequential. gather -> quant + risk (both read gather's
    output) -> memo (reads all three) -> critic (reads everything,
    including the memo). Every task's output is a validated Pydantic model
    except the memo itself, which is left as Markdown since its job is to
    read well as a document, not to be machine-parsed further.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ---- Agents ----------------------------------------------------

    @agent
    def data_gatherer(self) -> Agent:
        return Agent(
            config=self.agents_config["data_gatherer"],
            tools=[market_data_tool, news_search_tool],
            llm=_gemini_llm(),
            verbose=True,
        )

    @agent
    def quant_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["quant_analyst"],
            llm=_gemini_llm(),
            verbose=True,
        )

    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_analyst"],
            tools=[news_search_tool],
            llm=_gemini_llm(),
            verbose=True,
        )

    @agent
    def memo_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["memo_writer"],
            llm=_gemini_llm(),
            verbose=True,
        )

    @agent
    def critic(self) -> Agent:
        return Agent(
            config=self.agents_config["critic"],
            llm=_gemini_llm(),
            verbose=True,
        )

    # ---- Tasks -------------------------------------------------------
    # Every task gets `callback=log_handoff` so each handoff is written to
    # logs/handoffs.jsonl as it happens, not reconstructed after the fact.

    @task
    def gather_data_task(self) -> Task:
        return Task(
            config=self.tasks_config["gather_data_task"],
            agent=self.data_gatherer(),
            output_pydantic=CompanyData,
            callback=log_handoff,
        )

    @task
    def quant_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["quant_analysis_task"],
            agent=self.quant_analyst(),
            context=[self.gather_data_task()],
            output_pydantic=QuantAnalysis,
            callback=log_handoff,
        )

    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            agent=self.risk_analyst(),
            context=[self.gather_data_task()],
            output_pydantic=RiskAssessment,
            callback=log_handoff,
        )

    @task
    def write_memo_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_memo_task"],
            agent=self.memo_writer(),
            context=[
                self.gather_data_task(),
                self.quant_analysis_task(),
                self.risk_assessment_task(),
            ],
            callback=log_handoff,
            output_file="output/investment_memo_draft.md",
        )

    @task
    def verify_memo_task(self) -> Task:
        return Task(
            config=self.tasks_config["verify_memo_task"],
            agent=self.critic(),
            context=[
                self.gather_data_task(),
                self.quant_analysis_task(),
                self.risk_assessment_task(),
                self.write_memo_task(),
            ],
            output_pydantic=CritiqueReport,
            callback=log_handoff,
            output_file="output/critique_report.json",
        )

    # ---- Crew ----------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # populated by the @agent decorators above
            tasks=self.tasks,  # populated by the @task decorators above, in order
            process=Process.sequential,
            verbose=True,
            tracing=True,
        )
