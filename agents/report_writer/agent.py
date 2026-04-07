"""
Report Writer Agent - compiles final report from all agent outputs
"""
from typing import Dict, Any
from datetime import datetime
from agents.base import BaseAgent
from agents.report_writer.schema import ReportOutput
from agents.report_writer.prompts import REPORT_WRITER_SYSTEM_PROMPT, REPORT_COMPOSITION_PROMPT


class ReportWriterAgent(BaseAgent):
    """Agent for composing the final comprehensive report"""

    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="ReportWriterAgent", llm_client=llm_client, retriever=retriever)

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare all agent outputs for report compilation"""
        self.logger.info("Thinking phase: preparing report components...")
        return {
            "market_background": context.get("market_background", ""),
            "lg_strategy": context.get("lg_strategy", ""),
            "catl_strategy": context.get("catl_strategy", ""),
            "comparative_swot": context.get("comparative_swot", ""),
            "execution_id": context.get("execution_id", ""),
        }

    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to compose the final report sections as structured JSON"""
        self.logger.info("Acting phase: composing final report sections...")

        # Fallback when LLM is not available
        if not self.llm:
            self.logger.warning("LLM not available, using placeholder report")
            return self._placeholder(thought)

        user_prompt = REPORT_COMPOSITION_PROMPT.format(
            market_background=thought.get("market_background", "(없음)"),
            lg_strategy=thought.get("lg_strategy", "(없음)"),
            catl_strategy=thought.get("catl_strategy", "(없음)"),
            comparative_swot=thought.get("comparative_swot", "(없음)"),
        )

        try:
            result = self.call_llm(
                system_prompt=REPORT_WRITER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                use_json_mode=True,
                max_tokens=4000,
            )
            if isinstance(result, dict):
                return result
            return self._placeholder(thought)
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}. Using placeholder.")
            return self._placeholder(thought)

    def _placeholder(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 미연결 또는 오류 시 반환하는 플레이스홀더"""
        empty_company = {
            "portfolio": "(분석 결과 없음)",
            "market_response": "(분석 결과 없음)",
            "diversification": "(분석 결과 없음)",
            "core_competency": "(분석 결과 없음)",
            "profitability": "(분석 결과 없음)",
            "risks": "(분석 결과 없음)",
        }
        return {
            "summary": {
                "key_conclusions": "(핵심 결론 없음)",
                "market_summary": thought.get("market_background", "(없음)"),
                "company_strategy_summary": "(기업 전략 요약 없음)",
                "comparison_result": "(비교 결과 없음)",
                "insights": "(인사이트 없음)",
            },
            "market_background": {
                "market_size_trend": "(시장 규모 분석 없음)",
                "market_demand_change": "(수요 변화 분석 없음)",
                "policy_changes": "(정책 변화 분석 없음)",
            },
            "lges_analysis": empty_company,
            "catl_analysis": empty_company,
            "strategy_comparison": {
                "core_strategy_comparison": "(전략 비교 없음)",
                "lges_swot": "(LGES SWOT 없음)",
                "catl_swot": "(CATL SWOT 없음)",
                "comparative_swot": thought.get("comparative_swot", "(없음)"),
            },
            "overall_implications": "(종합 시사점 없음)",
            "references": [],
        }

    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output as structured JSON"""
        self.logger.info("Output phase: formatting final report as JSON...")

        report_output = ReportOutput(
            summary=action_result.get("summary", {}),
            market_background=action_result.get("market_background", {}),
            lges_analysis=action_result.get("lges_analysis", {}),
            catl_analysis=action_result.get("catl_analysis", {}),
            strategy_comparison=action_result.get("strategy_comparison", {}),
            overall_implications=action_result.get("overall_implications", ""),
            references=action_result.get("references", []),
            metadata={
                "generated_at": datetime.now().isoformat(),
                "agent": "report_writer",
                "format": "json",
            },
        )

        return {
            "result": report_output.dict(),
            "agent": "report_writer",
            "status": "completed",
            "format": "json",
        }
