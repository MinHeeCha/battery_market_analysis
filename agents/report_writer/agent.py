"""
Report Writer Agent - compiles final report from all agent outputs
"""
import re
from typing import Any, Dict, List
from datetime import datetime
from agents.base import BaseAgent
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
                result["references"] = self._collect_sources(
                    thought.get("lg_strategy", ""),
                    thought.get("catl_strategy", ""),
                )
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

    def _collect_sources(self, *markdowns: str) -> List[str]:
        """각 기업조사 마크다운의 ## Sources 섹션에서 인용 항목을 추출한다."""
        seen: dict = {}
        for md in markdowns:
            # ## Sources 이후 섹션만 추출
            match = re.search(r"## Sources\n([\s\S]*?)(?=\n## |\Z)", md)
            if not match:
                continue
            for line in match.group(1).splitlines():
                # 4-space 들여쓰기로 시작하는 실제 인용 라인만 수집
                stripped = line.strip()
                if stripped.startswith("- ") and line.startswith("    "):
                    citation = stripped[2:].strip()
                    if citation and citation not in seen:
                        seen[citation] = True
        return list(seen.keys())

    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format final report as a markdown string for the supervisor."""
        self.logger.info("Output phase: converting report to markdown...")
        markdown = self._to_markdown(action_result)
        return {
            "result": markdown,
            "agent": "report_writer",
            "status": "completed",
        }

    def _to_markdown(self, d: Dict[str, Any]) -> str:
        """Convert the structured report dict to a markdown document."""
        def s(obj: Any, key: str, fallback: str = "(없음)") -> str:
            if isinstance(obj, dict):
                return str(obj.get(key, fallback)).strip() or fallback
            return fallback

        summary = d.get("summary", {})
        mkt = d.get("market_background", {})
        lges = d.get("lges_analysis", {})
        catl = d.get("catl_analysis", {})
        cmp = d.get("strategy_comparison", {})
        implications = str(d.get("overall_implications", "(없음)")).strip()
        refs = d.get("references", [])
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            "# 배터리 시장 전략 비교 보고서",
            f"> 생성일시: {generated_at}",
            "",
            "---",
            "",
            "## 1. SUMMARY",
            "",
            f"**핵심 결론**  \n{s(summary, 'key_conclusions')}",
            "",
            f"**시장 상황 요약**  \n{s(summary, 'market_summary')}",
            "",
            f"**기업별 전략 핵심**  \n{s(summary, 'company_strategy_summary')}",
            "",
            f"**비교 결과**  \n{s(summary, 'comparison_result')}",
            "",
            f"**인사이트 & 시사점**  \n{s(summary, 'insights')}",
            "",
            "---",
            "",
            "## 2. 시장 배경",
            "",
            f"### 2.1 배터리 시장 규모 변화\n{s(mkt, 'market_size_trend')}",
            "",
            f"### 2.2 배터리 시장 수요 변화\n{s(mkt, 'market_demand_change')}",
            "",
            f"### 2.3 정책 변화\n{s(mkt, 'policy_changes')}",
            "",
            "---",
            "",
            "## 3. LG에너지솔루션 전략 분석",
            "",
            f"### 3.1 현재 사업 포트폴리오 현황\n{s(lges, 'portfolio')}",
            "",
            f"### 3.2 시장 환경 변화 대응 전략\n{s(lges, 'market_response')}",
            "",
            f"### 3.3 다각화 전략 방향\n{s(lges, 'diversification')}",
            "",
            f"### 3.4 핵심 경쟁력\n{s(lges, 'core_competency')}",
            "",
            f"### 3.5 수익성 구조 및 전략\n{s(lges, 'profitability')}",
            "",
            f"### 3.6 주요 리스크 및 과제\n{s(lges, 'risks')}",
            "",
            "---",
            "",
            "## 4. CATL 전략 분석",
            "",
            f"### 4.1 현재 사업 포트폴리오 현황\n{s(catl, 'portfolio')}",
            "",
            f"### 4.2 시장 환경 변화 대응 전략\n{s(catl, 'market_response')}",
            "",
            f"### 4.3 다각화 전략 방향\n{s(catl, 'diversification')}",
            "",
            f"### 4.4 핵심 경쟁력\n{s(catl, 'core_competency')}",
            "",
            f"### 4.5 수익성 구조 및 전략\n{s(catl, 'profitability')}",
            "",
            f"### 4.6 주요 리스크 및 과제\n{s(catl, 'risks')}",
            "",
            "---",
            "",
            "## 5. 전략 비교 및 Comparative SWOT",
            "",
            f"### 5.1 핵심 전략 비교\n{s(cmp, 'core_strategy_comparison')}",
            "",
            f"### 5.2 LG에너지솔루션 SWOT\n{s(cmp, 'lges_swot')}",
            "",
            f"### 5.3 CATL SWOT\n{s(cmp, 'catl_swot')}",
            "",
            f"### 5.4 Comparative SWOT\n{s(cmp, 'comparative_swot')}",
            "",
            "---",
            "",
            "## 6. 종합 시사점",
            "",
            implications,
        ]

        if refs:
            lines += ["", "---", "", "## 7. References", ""]
            for ref in refs:
                lines.append(f"- {ref}")

        return "\n".join(lines).strip()
