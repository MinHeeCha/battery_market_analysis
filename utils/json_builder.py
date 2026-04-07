"""
JSON report builder - outputs structured report as JSON
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class JSONBuilder:
    """Builds JSON format reports from agent outputs"""

    def __init__(self, output_dir: str = "./outputs/reports_json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_from_state(self, state: ProjectState) -> Dict[str, Any]:
        """Build structured JSON report from ProjectState"""
        logger.info("Building JSON report from state...")

        report = {
            "metadata": {
                "title": "AI Agent 기반 배터리 시장 전략 보고서",
                "generated_at": datetime.now().isoformat(),
                "execution_id": state.execution_id,
                "format": "json",
                "version": "1.0"
            },
            "1_summary": {
                "title": "SUMMARY",
                "content": "(state에서 직접 생성된 요약)"
            },
            "2_market_background": {
                "title": "시장 배경",
                "content": state.market_background or "(시장 조사 결과 없음)"
            },
            "3_lges_analysis": {
                "title": "LG에너지솔루션 전략 분석",
                "content": state.lg_strategy or "(LG 분석 결과 없음)"
            },
            "4_catl_analysis": {
                "title": "CATL 전략 분석",
                "content": state.catl_strategy or "(CATL 분석 결과 없음)"
            },
            "5_strategy_comparison": {
                "title": "전략 비교 및 Comparative SWOT",
                "content": state.comparative_swot or "(SWOT 분석 결과 없음)"
            },
            "6_overall_implications": "(종합 시사점 없음)",
            "7_references": [],
            "workflow_status": {
                "phases": {
                    "market_research": state.validation_status.get("market_research", False),
                    "company_research": state.validation_status.get("company_research", False),
                    "swot_analysis": state.validation_status.get("swot_analysis", False),
                    "report_writing": state.validation_status.get("report_writing", False)
                },
                "retry_counts": state.retry_count,
                "errors": state.errors
            }
        }

        return report

    def build_from_report_output(self, report_output: Dict[str, Any]) -> Dict[str, Any]:
        """Build JSON report from structured report output"""
        logger.info("Building JSON report from report output...")

        summary = report_output.get("summary", {})
        market = report_output.get("market_background", {})
        lges = report_output.get("lges_analysis", {})
        catl = report_output.get("catl_analysis", {})
        comparison = report_output.get("strategy_comparison", {})

        report = {
            "metadata": {
                "title": "AI Agent 기반 배터리 시장 전략 보고서",
                "generated_at": datetime.now().isoformat(),
                "format": "json",
                "version": "1.0"
            },
            "1_summary": {
                "title": "SUMMARY",
                "key_conclusions": summary.get("key_conclusions", ""),
                "market_summary": summary.get("market_summary", ""),
                "company_strategy_summary": summary.get("company_strategy_summary", ""),
                "comparison_result": summary.get("comparison_result", ""),
                "insights": summary.get("insights", "")
            },
            "2_market_background": {
                "title": "시장 배경",
                "2_1_market_size_trend": market.get("market_size_trend", ""),
                "2_2_market_demand_change": market.get("market_demand_change", ""),
                "2_3_policy_changes": market.get("policy_changes", "")
            },
            "3_lges_analysis": {
                "title": "LG에너지솔루션 전략 분석",
                "3_1_portfolio": lges.get("portfolio", ""),
                "3_2_market_response": lges.get("market_response", ""),
                "3_3_diversification": lges.get("diversification", ""),
                "3_4_core_competency": lges.get("core_competency", ""),
                "3_5_profitability": lges.get("profitability", ""),
                "3_6_risks": lges.get("risks", "")
            },
            "4_catl_analysis": {
                "title": "CATL 전략 분석",
                "4_1_portfolio": catl.get("portfolio", ""),
                "4_2_market_response": catl.get("market_response", ""),
                "4_3_diversification": catl.get("diversification", ""),
                "4_4_core_competency": catl.get("core_competency", ""),
                "4_5_profitability": catl.get("profitability", ""),
                "4_6_risks": catl.get("risks", "")
            },
            "5_strategy_comparison": {
                "title": "전략 비교 및 Comparative SWOT",
                "5_1_core_strategy_comparison": comparison.get("core_strategy_comparison", ""),
                "5_2_lges_swot": comparison.get("lges_swot", ""),
                "5_3_catl_swot": comparison.get("catl_swot", ""),
                "5_4_comparative_swot": comparison.get("comparative_swot", "")
            },
            "6_overall_implications": report_output.get("overall_implications", ""),
            "7_references": report_output.get("references", []),
            "report_metadata": report_output.get("metadata", {})
        }

        return report

    def save_report(self, report_data: Dict[str, Any], filename: Optional[str] = None, indent: int = 2) -> Path:
        """Save JSON report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"battery_strategy_report_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=indent, ensure_ascii=False, default=str)

        logger.info(f"JSON report saved to {filepath}")
        return filepath

    def load_report(self, filepath: Path) -> Dict[str, Any]:
        """Load JSON report from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON report loaded from {filepath}")
        return data
