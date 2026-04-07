"""
Markdown report builder - outputs structured report as Markdown
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class MarkdownBuilder:
    """Builds Markdown format reports from agent outputs"""

    def __init__(self, output_dir: str = "./outputs/reports_md"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_from_state(self, state: ProjectState) -> str:
        """Build Markdown report string from ProjectState"""
        logger.info("Building Markdown report from state...")

        now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

        sections = [
            "# AI Agent 기반 배터리 시장 전략 비교 보고서",
            f"\n> 생성일시: {now}  \n> 실행 ID: {state.execution_id}\n",
            "---",
            "## 1. Executive Summary",
            self._get_executive_summary(state),
            "## 2. 시장 개요",
            state.market_background or "_시장 조사 결과 없음_",
            "## 3. LG에너지솔루션 전략 분석",
            state.lg_strategy or "_LG 분석 결과 없음_",
            "## 4. CATL 전략 분석",
            state.catl_strategy or "_CATL 분석 결과 없음_",
            "## 5. SWOT 비교 분석",
            state.comparative_swot or "_SWOT 분석 결과 없음_",
            "## 6. 결론 및 전략 제안",
            self._get_conclusion(state),
            "---",
            self._get_workflow_status(state),
        ]

        return "\n\n".join(sections)

    def _get_executive_summary(self, state: ProjectState) -> str:
        if state.final_report:
            if isinstance(state.final_report, dict):
                return state.final_report.get("executive_summary", "")
            if isinstance(state.final_report, str):
                return state.final_report
        return (
            "본 보고서는 배터리 시장의 현황을 분석하고 "
            "LG에너지솔루션과 CATL의 경쟁 전략을 비교 분석한 결과물입니다."
        )

    def _get_conclusion(self, state: ProjectState) -> str:
        if state.final_report and isinstance(state.final_report, dict):
            return state.final_report.get(
                "conclusion_and_recommendation",
                "배터리 시장에서 성공하기 위해서는 기술 혁신과 비용 경쟁력의 균형이 필요합니다.",
            )
        return "배터리 시장에서 성공하기 위해서는 기술 혁신과 비용 경쟁력의 균형이 필요합니다."

    def _get_workflow_status(self, state: ProjectState) -> str:
        statuses = state.validation_status or {}
        lines = ["### 워크플로우 실행 상태", ""]
        phase_labels = {
            "market_research": "시장 조사",
            "company_research": "기업 조사",
            "swot_analysis": "SWOT 분석",
            "report_writing": "보고서 작성",
        }
        for key, label in phase_labels.items():
            icon = "✅" if statuses.get(key) else "⬜"
            lines.append(f"- {icon} {label}")
        if state.errors:
            lines.append("\n**오류 내역:**")
            for err in state.errors:
                lines.append(f"- {err}")
        return "\n".join(lines)

    def save_report(self, content: str, filename: Optional[str] = None) -> Path:
        """Save Markdown report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"battery_strategy_report_{timestamp}.md"

        filepath = self.output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Markdown report saved to {filepath}")
        return filepath
