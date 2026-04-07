"""
Supervisor Agent – LangGraph-based orchestrator.

Flow:
    START
      └─► parallel_research (market ∥ company)
            └─► supervisor_eval_research
                  ├─► retry_market / retry_company  (loop until approved or max retries)
                  └─► swot
                        └─► supervisor_eval_swot
                              ├─► retry_swot          (loop)
                              └─► report
                                    └─► supervisor_eval_report
                                          ├─► retry_report  (loop)
                                          └─► END
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from config.graph_state import BatteryAnalysisState
from shared.logger import get_logger

logger = get_logger(__name__)

# ── Supervisor thresholds (확장 예정) ──────────────────────────────────────
MAX_RETRIES = 2
MIN_RESULT_CHARS = 300  # 최소 유효 응답 길이


# ══════════════════════════════════════════════════════════════════════════════
# Graph builder
# ══════════════════════════════════════════════════════════════════════════════

def build_graph(retriever=None):
    """Compile and return the LangGraph workflow."""

    # ── Worker functions (closures capture `retriever`) ───────────────────

    def _run_market() -> Dict[str, Any]:
        from agents.market_research.agent import MarketResearchAgent
        agent = MarketResearchAgent(retriever=retriever)
        result = agent.run({})
        logger.info("[market_research] done (len=%d)", len(result.get("result", "")))
        return {"market_result": result.get("result", "")}

    def _run_company() -> Dict[str, Any]:
        from agents.company_research.agent import CompanyResearchAgent
        agent = CompanyResearchAgent(retriever=retriever)
        result = agent.run({})
        logger.info(
            "[company_research] done (lg=%d, catl=%d)",
            len(result.get("lg_result", "")),
            len(result.get("catl_result", "")),
        )
        return {
            "lg_result": result.get("lg_result", ""),
            "catl_result": result.get("catl_result", ""),
        }

    # ── Nodes ─────────────────────────────────────────────────────────────

    def parallel_research(state: BatteryAnalysisState) -> Dict[str, Any]:
        """Run market and company research concurrently."""
        logger.info("[supervisor] parallel_research START")
        with ThreadPoolExecutor(max_workers=2) as pool:
            mf = pool.submit(_run_market)
            cf = pool.submit(_run_company)
            market = mf.result()
            company = cf.result()
        logger.info("[supervisor] parallel_research DONE")
        return {
            **market,
            **company,
            "market_retries": state.get("market_retries", 0),
            "company_retries": state.get("company_retries", 0),
        }

    def supervisor_eval_research(state: BatteryAnalysisState) -> Dict[str, Any]:
        market_ok = len(state.get("market_result", "")) >= MIN_RESULT_CHARS
        company_ok = (
            len(state.get("lg_result", "")) >= MIN_RESULT_CHARS
            and len(state.get("catl_result", "")) >= MIN_RESULT_CHARS
        )
        logger.info(
            "[supervisor] eval_research market=%s company=%s (retries m=%d c=%d)",
            market_ok, company_ok,
            state.get("market_retries", 0),
            state.get("company_retries", 0),
        )
        return {"market_approved": market_ok, "company_approved": company_ok}

    def retry_market(state: BatteryAnalysisState) -> Dict[str, Any]:
        logger.info("[supervisor] retry_market (attempt %d)", state.get("market_retries", 0) + 1)
        result = _run_market(state)
        return {**result, "market_retries": state.get("market_retries", 0) + 1}

    def retry_company(state: BatteryAnalysisState) -> Dict[str, Any]:
        logger.info("[supervisor] retry_company (attempt %d)", state.get("company_retries", 0) + 1)
        result = _run_company(state)
        return {**result, "company_retries": state.get("company_retries", 0) + 1}

    def run_swot(state: BatteryAnalysisState) -> Dict[str, Any]:
        from agents.swot_analysis.agent import SWOTAnalysisAgent
        logger.info("[supervisor] run_swot START")
        agent = SWOTAnalysisAgent()
        result = agent.run({
            "market_background": state.get("market_result", ""),
            "lg_strategy": state.get("lg_result", ""),
            "catl_strategy": state.get("catl_result", ""),
        })
        logger.info("[supervisor] run_swot DONE (len=%d)", len(result.get("result", "")))
        return {
            "swot_result": result.get("result", ""),
            "swot_retries": state.get("swot_retries", 0),
        }

    def supervisor_eval_swot(state: BatteryAnalysisState) -> Dict[str, Any]:
        swot_ok = len(state.get("swot_result", "")) >= MIN_RESULT_CHARS
        logger.info(
            "[supervisor] eval_swot approved=%s (retries=%d)",
            swot_ok, state.get("swot_retries", 0),
        )
        return {"swot_approved": swot_ok}

    def retry_swot(state: BatteryAnalysisState) -> Dict[str, Any]:
        logger.info("[supervisor] retry_swot (attempt %d)", state.get("swot_retries", 0) + 1)
        result = run_swot(state)
        return {**result, "swot_retries": state.get("swot_retries", 0) + 1}

    def run_report(state: BatteryAnalysisState) -> Dict[str, Any]:
        from agents.report_writer.agent import ReportWriterAgent
        logger.info("[supervisor] run_report START")
        agent = ReportWriterAgent()
        result = agent.run({
            "market_background": state.get("market_result", ""),
            "lg_strategy": state.get("lg_result", ""),
            "catl_strategy": state.get("catl_result", ""),
            "comparative_swot": state.get("swot_result", ""),
        })
        logger.info("[supervisor] run_report DONE (len=%d)", len(result.get("result", "")))
        return {
            "final_report": result.get("result", ""),
            "report_retries": state.get("report_retries", 0),
        }

    def supervisor_eval_report(state: BatteryAnalysisState) -> Dict[str, Any]:
        report_ok = len(state.get("final_report", "")) >= MIN_RESULT_CHARS
        logger.info(
            "[supervisor] eval_report approved=%s (retries=%d)",
            report_ok, state.get("report_retries", 0),
        )
        return {"report_approved": report_ok}

    def retry_report(state: BatteryAnalysisState) -> Dict[str, Any]:
        logger.info("[supervisor] retry_report (attempt %d)", state.get("report_retries", 0) + 1)
        result = run_report(state)
        return {**result, "report_retries": state.get("report_retries", 0) + 1}

    # ── Routing functions ─────────────────────────────────────────────────

    def route_research(state: BatteryAnalysisState) -> str:
        market_ok = state.get("market_approved", False)
        company_ok = state.get("company_approved", False)
        if market_ok and company_ok:
            return "swot"
        if not market_ok and state.get("market_retries", 0) < MAX_RETRIES:
            return "retry_market"
        if not company_ok and state.get("company_retries", 0) < MAX_RETRIES:
            return "retry_company"
        return "swot"  # max retries 소진 → 강제 진행

    def route_swot(state: BatteryAnalysisState) -> str:
        if state.get("swot_approved", False):
            return "report"
        if state.get("swot_retries", 0) < MAX_RETRIES:
            return "retry_swot"
        return "report"

    def route_report(state: BatteryAnalysisState) -> str:
        if state.get("report_approved", False):
            return END
        if state.get("report_retries", 0) < MAX_RETRIES:
            return "retry_report"
        return END

    # ── Graph assembly ────────────────────────────────────────────────────

    wf = StateGraph(BatteryAnalysisState)

    wf.add_node("parallel_research", parallel_research)
    wf.add_node("supervisor_eval_research", supervisor_eval_research)
    wf.add_node("retry_market", retry_market)
    wf.add_node("retry_company", retry_company)
    wf.add_node("swot", run_swot)
    wf.add_node("supervisor_eval_swot", supervisor_eval_swot)
    wf.add_node("retry_swot", retry_swot)
    wf.add_node("report", run_report)
    wf.add_node("supervisor_eval_report", supervisor_eval_report)
    wf.add_node("retry_report", retry_report)

    wf.add_edge(START, "parallel_research")
    wf.add_edge("parallel_research", "supervisor_eval_research")
    wf.add_conditional_edges(
        "supervisor_eval_research", route_research,
        {"swot": "swot", "retry_market": "retry_market", "retry_company": "retry_company"},
    )
    wf.add_edge("retry_market", "supervisor_eval_research")
    wf.add_edge("retry_company", "supervisor_eval_research")

    wf.add_edge("swot", "supervisor_eval_swot")
    wf.add_conditional_edges(
        "supervisor_eval_swot", route_swot,
        {"report": "report", "retry_swot": "retry_swot"},
    )
    wf.add_edge("retry_swot", "supervisor_eval_swot")

    wf.add_edge("report", "supervisor_eval_report")
    wf.add_conditional_edges(
        "supervisor_eval_report", route_report,
        {END: END, "retry_report": "retry_report"},
    )
    wf.add_edge("retry_report", "supervisor_eval_report")

    return wf.compile()


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

class SupervisorAgent:
    """Thin wrapper that runs the LangGraph workflow and returns the final report."""

    def __init__(self, retriever=None):
        self.retriever = retriever
        self.graph = build_graph(retriever=retriever)

    def run(self, save: bool = True) -> str:
        """Execute the full workflow and return the final markdown report.

        Args:
            save: If True, save the report to outputs/reports_md/ automatically.
        Returns:
            Final report as a markdown string.
        """
        logger.info("[SupervisorAgent] workflow START")
        final_state: BatteryAnalysisState = self.graph.invoke({})
        report = final_state.get("final_report", "")
        logger.info("[SupervisorAgent] workflow DONE (report len=%d)", len(report))

        if save and report:
            self._save(report)

        return report

    def _save(self, report: str) -> Path:
        """Save report to outputs/reports_md/ and return the file path."""
        out_dir = Path(__file__).resolve().parents[2] / "outputs" / "reports_md"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"battery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = out_dir / filename
        path.write_text(report, encoding="utf-8")
        logger.info("[SupervisorAgent] report saved → %s", path)
        return path
