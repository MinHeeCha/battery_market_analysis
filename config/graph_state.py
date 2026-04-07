"""LangGraph state definition for the battery analysis workflow."""
from typing import TypedDict


class BatteryAnalysisState(TypedDict, total=False):
    # ── Agent results (markdown strings) ──────────────────────────────────
    market_result: str      # MarketResearchAgent output
    lg_result: str          # CompanyResearchAgent – LG
    catl_result: str        # CompanyResearchAgent – CATL
    swot_result: str        # SWOTAnalysisAgent output
    final_report: str       # ReportWriterAgent output

    # ── Supervisor approvals ───────────────────────────────────────────────
    market_approved: bool
    company_approved: bool
    swot_approved: bool
    report_approved: bool

    # ── Retry counters ─────────────────────────────────────────────────────
    market_retries: int
    company_retries: int
    swot_retries: int
    report_retries: int
