"""
Report Writer Agent - compiles final report from all agent outputs
"""
import re
import json
from typing import Any, Dict, List
from datetime import datetime
from agents.base import BaseAgent
from agents.report_writer.prompts import (
    REPORT_WRITER_SYSTEM_PROMPT,
    MARKET_BACKGROUND_PROMPT,
    LGES_ANALYSIS_PROMPT,
    CATL_ANALYSIS_PROMPT,
    STRATEGY_COMPARISON_PROMPT,
    SUMMARY_PROMPT,
)
from agents.report_writer.evaluator import ReportEvaluator

MAX_EVAL_RETRIES = 2


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
        """섹션별 독립 LLM 호출로 보고서를 작성한다 (5회 호출)"""
        self.logger.info("Acting phase: composing final report sections...")

        if not self.llm:
            self.logger.warning("LLM not available, using placeholder report")
            return self._placeholder(thought)

        def _call(prompt: str, label: str) -> Dict[str, Any]:
            try:
                res = self.call_llm(
                    system_prompt=REPORT_WRITER_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    use_json_mode=True,
                    max_tokens=2000,
                )
                if isinstance(res, dict):
                    return res
                self.logger.warning(f"{label}: dict 아님, 빈 dict 반환")
                return {}
            except Exception as e:
                self.logger.error(f"{label} LLM 호출 실패: {e}")
                return {}

        # ── Call 1~4: 섹션별 생성 ──────────────────────────────────────
        self.logger.info("섹션 생성 1/5: 시장 배경")
        market_background = _call(
            MARKET_BACKGROUND_PROMPT.format(market_research=thought.get("market_background", "(없음)")),
            "시장 배경",
        )

        self.logger.info("섹션 생성 2/5: LG에너지솔루션 분석")
        lges_analysis = _call(
            LGES_ANALYSIS_PROMPT.format(lg_strategy=thought.get("lg_strategy", "(없음)")),
            "LGES 분석",
        )

        self.logger.info("섹션 생성 3/5: CATL 분석")
        catl_analysis = _call(
            CATL_ANALYSIS_PROMPT.format(catl_strategy=thought.get("catl_strategy", "(없음)")),
            "CATL 분석",
        )

        self.logger.info("섹션 생성 4/5: 전략 비교")
        strategy_comparison = _call(
            STRATEGY_COMPARISON_PROMPT.format(
                lges_summary=json.dumps(lges_analysis, ensure_ascii=False)[:1500],
                catl_summary=json.dumps(catl_analysis, ensure_ascii=False)[:1500],
                comparative_swot=thought.get("comparative_swot", "(없음)"),
            ),
            "전략 비교",
        )

        # ── Call 5: SUMMARY + 종합 시사점 ─────────────────────────────
        self.logger.info("섹션 생성 5/5: SUMMARY + 종합 시사점")
        summary_result = _call(
            SUMMARY_PROMPT.format(
                market_background=json.dumps(market_background, ensure_ascii=False)[:800],
                lges_analysis=json.dumps(lges_analysis, ensure_ascii=False)[:800],
                catl_analysis=json.dumps(catl_analysis, ensure_ascii=False)[:800],
                strategy_comparison=json.dumps(strategy_comparison, ensure_ascii=False)[:800],
            ),
            "SUMMARY",
        )

        result: Dict[str, Any] = {
            "summary": summary_result.get("summary", {}),
            "market_background": market_background,
            "lges_analysis": lges_analysis,
            "catl_analysis": catl_analysis,
            "strategy_comparison": strategy_comparison,
            "overall_implications": summary_result.get("overall_implications", ""),
            "references": self._collect_sources(
                thought.get("lg_strategy", ""),
                thought.get("catl_strategy", ""),
            ),
        }

        # ── 평가 ──────────────────────────────────────────────────────
        evaluator = ReportEvaluator()
        eval_metadata: Dict[str, Any] = {}

        l1 = evaluator.evaluate_layer1(result)
        eval_metadata["layer1"] = {"passed": l1.passed, "details": l1.details, "failures": l1.failures}
        self.logger.info(l1.summary())

        l2 = evaluator.evaluate_layer2(result, self.llm)
        eval_metadata["layer2"] = {"passed": l2.passed, "details": l2.details, "failures": l2.failures}
        self.logger.info(l2.summary())

        result["_evaluation"] = eval_metadata
        return result

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
            match = re.search(r"## Sources\n([\s\S]*?)(?=\n## |\Z)", md)
            if not match:
                continue
            for line in match.group(1).splitlines():
                stripped = line.strip()
                if stripped.startswith("- ") and line.startswith("    "):
                    citation = stripped[2:].strip()
                    if citation and citation not in seen:
                        seen[citation] = True
        return list(seen.keys())

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

    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert report dict to markdown and return for supervisor"""
        self.logger.info("Output phase: converting report to markdown...")

        evaluation = action_result.pop("_evaluation", {})
        markdown = self._to_markdown(action_result)

        l1_passed = evaluation.get("layer1", {}).get("passed", None)
        l2_passed = evaluation.get("layer2", {}).get("passed", None)

        return {
            "result": markdown,
            "agent": "report_writer",
            "status": "completed",
            "format": "json",
            "evaluation": {
                "layer1_passed": l1_passed,
                "layer2_passed": l2_passed,
                "details": evaluation,
            },
        }