"""
SWOT Analysis Agent - performs comparative SWOT analysis between LG and CATL
"""
import json
from typing import Dict, Any, Optional
from agents.base import BaseAgent
from agents.swot_analysis.prompts import (
    SWOT_ANALYSIS_SYSTEM_PROMPT,
    SWOT_ANALYSIS_USER_PROMPT_TEMPLATE,
)


class SWOTAnalysisAgent(BaseAgent):
    """Agent for SWOT analysis and strategic comparison"""
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="SWOTAnalysisAgent", llm_client=llm_client, retriever=retriever)
        self.max_retry_count = 2
        self.threshold_task_success_rate = 0.8
        self.threshold_fact_accuracy = 0.7
        self.threshold_specificity = 0.6
        self._last_evaluation: Dict[str, Any] = {}
        self._last_retry_count: int = 0
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare market and company context for SWOT analysis"""
        self.logger.info("Thinking phase: preparing SWOT context...")
        
        return {
            "market_background": context.get("market_background", ""),
            "lg_strategy": context.get("lg_strategy", ""),
            "catl_strategy": context.get("catl_strategy", ""),
            "context": context
        }
    
    def _build_user_prompt(self, thought: Dict[str, Any], feedback: str = "") -> str:
        """Build user prompt with optional feedback for retry."""
        base_prompt = SWOT_ANALYSIS_USER_PROMPT_TEMPLATE.format(
            market_background=thought.get("market_background", ""),
            lg_strategy=thought.get("lg_strategy", ""),
            catl_strategy=thought.get("catl_strategy", ""),
        )
        json_schema_guide = """
출력 형식: 반드시 아래 JSON 객체만 반환하시오. 마크다운/설명문 금지.
{
  "lg_swot": {
    "company": "LG에너지솔루션",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  },
  "catl_swot": {
    "company": "CATL",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "opportunities": ["..."],
    "threats": ["..."]
  },
  "comparative_swot": "두 기업의 상대적 경쟁우위/열위, 시사점을 포함한 비교 분석"
}
"""
        prompt = f"{base_prompt}\n\n{json_schema_guide}"
        if not feedback:
            return prompt
        return f"{prompt}\n\n이전 결과 개선 요청:\n{feedback}"

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from raw response text."""
        try:
            return json.loads(text)
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return None
        return None

    def _default_swot_output(self) -> Dict[str, Any]:
        """Default SWOT output used when LLM is unavailable."""
        return {
            "lg_swot": {
                "company": "LG에너지솔루션",
                "strengths": ["프리미엄 기술 포지셔닝", "글로벌 브랜드 신뢰도", "자동차 제조사와의 강한 파트너십"],
                "weaknesses": ["상대적으로 높은 생산 비용", "아시아 시장에서의 제한된 점유율"],
                "opportunities": ["전기차 시장의 지속적 성장", "고성능 배터리 수요 증가"],
                "threats": ["CATL의 공격적 시장 진출", "비용 경쟁 심화"],
            },
            "catl_swot": {
                "company": "CATL",
                "strengths": ["비용 경쟁력", "광대한 생산 능력", "중국 시장의 절대 우위"],
                "weaknesses": ["기술 차별성 부족", "지정학적 위험"],
                "opportunities": ["신흥 시장 진출", "나트륨이온 배터리 시장"],
                "threats": ["글로벌 공급망 재편", "선진 기업의 기술 경쟁"],
            },
            "comparative_swot": (
                "LG에너지솔루션은 기술/품질/글로벌 OEM 파트너십에서 우위를 보이지만 원가 부담이 상대적으로 높습니다. "
                "반면 CATL은 비용 경쟁력과 대규모 생산능력에서 강점을 가지며 중저가 대중 시장 침투가 빠릅니다. "
                "향후 경쟁은 고성능 세그먼트의 기술 리더십과 대중형 세그먼트의 원가 효율 경쟁으로 양분될 가능성이 큽니다."
            ),
        }

    def _normalize_swot_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and sanitize SWOT output structure."""
        def ensure_list(value: Any) -> list:
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if isinstance(value, str) and value.strip():
                return [value.strip()]
            return []

        lg = parsed.get("lg_swot", {}) if isinstance(parsed.get("lg_swot", {}), dict) else {}
        catl = parsed.get("catl_swot", {}) if isinstance(parsed.get("catl_swot", {}), dict) else {}

        return {
            "lg_swot": {
                "company": str(lg.get("company", "LG에너지솔루션")),
                "strengths": ensure_list(lg.get("strengths")),
                "weaknesses": ensure_list(lg.get("weaknesses")),
                "opportunities": ensure_list(lg.get("opportunities")),
                "threats": ensure_list(lg.get("threats")),
            },
            "catl_swot": {
                "company": str(catl.get("company", "CATL")),
                "strengths": ensure_list(catl.get("strengths")),
                "weaknesses": ensure_list(catl.get("weaknesses")),
                "opportunities": ensure_list(catl.get("opportunities")),
                "threats": ensure_list(catl.get("threats")),
            },
            "comparative_swot": str(parsed.get("comparative_swot", "")).strip(),
        }

    def _parse_swot_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into required structured SWOT output."""
        parsed = self._extract_json(response)
        if parsed:
            return self._normalize_swot_result(parsed)

        # Fallback: keep raw response as comparative text while preserving schema.
        fallback = self._default_swot_output()
        fallback["comparative_swot"] = response.strip()
        return fallback

    def _evaluate_swot(self, swot_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate SWOT quality:
        - Structure score (quadrant existence)
        - Fact accuracy
        - Specificity
        """
        required_fields = ["strengths", "weaknesses", "opportunities", "threats"]
        lg_swot = swot_result.get("lg_swot", {})
        catl_swot = swot_result.get("catl_swot", {})

        valid_quadrants = 0
        for field in required_fields:
            if isinstance(lg_swot.get(field), list) and len(lg_swot.get(field, [])) > 0:
                valid_quadrants += 1
            if isinstance(catl_swot.get(field), list) and len(catl_swot.get(field, [])) > 0:
                valid_quadrants += 1

        has_comparative_swot = bool(str(swot_result.get("comparative_swot", "")).strip())
        structure_score = valid_quadrants / 8.0
        has_required_structure = (valid_quadrants == 8) and has_comparative_swot

        # Default heuristic values (used when evaluator LLM is unavailable)
        swot_text = json.dumps(swot_result, ensure_ascii=False)
        fact_accuracy = 0.7 if len(swot_text) >= 600 else 0.5
        specificity = 0.6 if len(swot_result.get("comparative_swot", "")) >= 200 else 0.5
        fact_check_pass = fact_accuracy >= self.threshold_fact_accuracy
        feedback = ""

        if self.llm:
            evaluator_prompt = f"""
다음 SWOT 결과물을 아래 기준으로 평가하고 JSON만 반환하시오.

평가 방식:
- 구조 점수 + 사실 정확도 + 구체성 점수

판단 단위:
- 4분면 존재 여부 (강점/약점/기회/위협)
- 사실 판정 결과
- 구체성 점수

반환 JSON 스키마:
{{
  "fact_accuracy": 0.0~1.0,
  "specificity": 0.0~1.0,
  "fact_check_pass": true/false,
  "feedback": "개선사항"
}}

SWOT 결과물:
{json.dumps(swot_result, ensure_ascii=False, indent=2)}
"""
            try:
                eval_response = self.llm.invoke(
                    system_prompt="당신은 엄격한 품질평가자다. 반드시 JSON만 출력한다.",
                    user_prompt=evaluator_prompt
                )
                parsed = self._extract_json(eval_response) or {}
                fact_accuracy = float(parsed.get("fact_accuracy", fact_accuracy))
                specificity = float(parsed.get("specificity", specificity))
                fact_check_pass = bool(parsed.get("fact_check_pass", fact_check_pass))
                feedback = str(parsed.get("feedback", "")).strip()
            except Exception as e:
                self.logger.warning("SWOT 평가 중 오류 발생, 휴리스틱 점수 사용: %s", str(e))

        # Normalize score boundaries
        fact_accuracy = max(0.0, min(1.0, fact_accuracy))
        specificity = max(0.0, min(1.0, specificity))

        task_success_rate = round((structure_score + fact_accuracy + specificity) / 3, 4)
        passed = (
            task_success_rate >= self.threshold_task_success_rate
            and fact_accuracy >= self.threshold_fact_accuracy
            and specificity >= self.threshold_specificity
            and has_required_structure
            and fact_check_pass
        )
        return {
            "structure_score": structure_score,
            "valid_quadrants": valid_quadrants,
            "has_comparative_swot": has_comparative_swot,
            "has_required_structure": has_required_structure,
            "fact_accuracy": fact_accuracy,
            "fact_check_pass": fact_check_pass,
            "specificity": specificity,
            "task_success_rate": task_success_rate,
            "passed": passed,
            "feedback": feedback,
        }

    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SWOT and retry up to 2 times when quality thresholds are not met."""
       # self.logger.info("Acting phase: conducting SWOT analysis...")
       # self.logger.info("SWOT 입력값 - 시장 배경:\n%s", thought.get("market_background", ""))
       # self.logger.info("SWOT 입력값 - LG 전략:\n%s", thought.get("lg_strategy", ""))
       # self.logger.info("SWOT 입력값 - CATL 전략:\n%s", thought.get("catl_strategy", ""))

        if not self.llm:
            default_result = self._default_swot_output()
            self._last_evaluation = self._evaluate_swot(default_result)
            self._last_retry_count = 0
            self.logger.warning("LLM 미연결 상태로 고정 샘플 SWOT 반환")
            return default_result

        best_result: Dict[str, Any] = self._default_swot_output()
        best_eval: Dict[str, Any] = {}
        feedback = ""

        for attempt in range(self.max_retry_count + 1):
            response = self.llm.invoke(
                system_prompt=SWOT_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=self._build_user_prompt(thought, feedback=feedback)
            )
            parsed_result = self._parse_swot_response(response)
            evaluation = self._evaluate_swot(parsed_result)
            self.logger.info(
                "SWOT 평가 attempt=%d | TSR=%.3f | Fact=%.3f | Specificity=%.3f | Pass=%s",
                attempt + 1,
                evaluation["task_success_rate"],
                evaluation["fact_accuracy"],
                evaluation["specificity"],
                evaluation["passed"],
            )

            if (not best_eval) or (evaluation["task_success_rate"] > best_eval.get("task_success_rate", -1)):
                best_result = parsed_result
                best_eval = evaluation
                self._last_retry_count = attempt

            if evaluation["passed"]:
                self._last_evaluation = evaluation
                self._last_retry_count = attempt
                return parsed_result

            feedback = evaluation.get("feedback", "")
            if not feedback:
                feedback = (
                    "점수 미달입니다. lg_swot/catl_swot/comparative_swot 구조를 유지하고, "
                    "각 4분면 항목을 구체적으로 보강하세요."
                )

        self._last_evaluation = best_eval
        return best_result

    def _build_company_swot_markdown_table(self, company_swot: Dict[str, Any]) -> str:
        """Build markdown table for one company's SWOT."""
        def format_items(items: Any) -> str:
            if not isinstance(items, list):
                return "-"
            clean_items = [str(item).strip() for item in items if str(item).strip()]
            return "<br>".join(clean_items) if clean_items else "-"

        return "\n".join(
            [
                "| 구분 | 내용 |",
                "| --- | --- |",
                f"| 강점 (S) | {format_items(company_swot.get('strengths', []))} |",
                f"| 약점 (W) | {format_items(company_swot.get('weaknesses', []))} |",
                f"| 기회 (O) | {format_items(company_swot.get('opportunities', []))} |",
                f"| 위협 (T) | {format_items(company_swot.get('threats', []))} |",
            ]
        )

    def _build_swot_markdown_output(self, swot_result: Dict[str, Any]) -> Dict[str, str]:
        """Build markdown outputs for LG/CATL/comparative SWOT."""
        lg_swot = swot_result.get("lg_swot", {})
        catl_swot = swot_result.get("catl_swot", {})
        comparative_text = str(swot_result.get("comparative_swot", "")).strip()
        comparative_cell = comparative_text.replace("\n", "<br>") if comparative_text else "-"

        lg_table = self._build_company_swot_markdown_table(lg_swot)
        catl_table = self._build_company_swot_markdown_table(catl_swot)
        comparative_table = "\n".join(
            [
                "| 항목 | 내용 |",
                "| --- | --- |",
                f"| Comparative SWOT | {comparative_cell} |",
            ]
        )

        full_markdown = "\n\n".join(
            [
                "## LG에너지솔루션 SWOT",
                lg_table,
                "## CATL SWOT",
                catl_table,
                "## 두 기업 Comparative SWOT",
                comparative_table,
            ]
        )

        return {
            "lg_swot": lg_table,
            "catl_swot": catl_table,
            "comparative_swot": comparative_table,
            "full": full_markdown,
        }
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output"""
        self.logger.info("Output phase: formatting SWOT analysis results...")
        passed = bool(self._last_evaluation.get("passed", False))
        markdown_tables = self._build_swot_markdown_output(action_result)

        return {
            "result": markdown_tables["full"],   # supervisor에 넘길 마크다운 문자열
            "agent": "swot_analysis",
            "status": "completed" if passed else "failed_quality_check",
            "quality_evaluation": self._last_evaluation,
            "retry_count": self._last_retry_count,
        }
