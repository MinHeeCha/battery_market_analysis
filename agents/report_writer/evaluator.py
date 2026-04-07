"""
Report Writer Agent - 자기평가 모듈
Layer 1: 수치 기반 Gate 조건 (Python 코드)
Layer 2: 구조 체크리스트 (LLM 평가)
"""
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class EvaluationResult:
    layer: int
    passed: bool
    failures: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        if self.passed:
            return f"[Layer {self.layer}] 통과"
        return f"[Layer {self.layer}] 실패 - {len(self.failures)}개 항목:\n" + "\n".join(
            f"  - {f}" for f in self.failures
        )


LAYER2_EVAL_PROMPT = """
아래 배터리 시장 전략 보고서를 검토하고 각 항목을 평가하시오.

=== 보고서 ===
{report_json}

=== 평가 항목 ===
1. SUMMARY의 핵심 결론이 6장 종합 시사점과 논리적으로 모순되지 않는가?
2. 3장(LGES)과 4장(CATL)이 동일한 소목차 구조(포트폴리오/시장대응/다각화/핵심경쟁력/수익성/리스크)를 유지하고 있는가?
3. 5장 비교 분석이 3장·4장의 내용을 실제로 참조하고 있는가?
4. Comparative SWOT(5.4)에 두 기업 각각의 S/W/O/T 항목이 명확히 구분되어 있는가?
5. SUMMARY가 보고서 전체 내용을 균형 있게 반영하고 있는가?

반드시 아래 JSON 형식으로만 응답하시오:
{{
  "check_1": true/false,
  "reason_1": "판단 근거 (1~2문장)",
  "check_2": true/false,
  "reason_2": "판단 근거 (1~2문장)",
  "check_3": true/false,
  "reason_3": "판단 근거 (1~2문장)",
  "check_4": true/false,
  "reason_4": "판단 근거 (1~2문장)",
  "check_5": true/false,
  "reason_5": "판단 근거 (1~2문장)"
}}
"""

LAYER2_CHECK_LABELS = {
    "check_1": "SUMMARY 결론 ↔ 종합 시사점 일관성",
    "check_2": "3장·4장 동일 소목차 구조 유지",
    "check_3": "5장 비교가 3·4장 내용 실제 참조",
    "check_4": "Comparative SWOT S/W/O/T 항목 구분",
    "check_5": "SUMMARY가 전체 내용 균형 반영",
}


class ReportEvaluator:
    """보고서 품질 평가기 (Layer 1 + Layer 2)"""

    def evaluate_layer1(self, report_data: Dict[str, Any]) -> EvaluationResult:
        """Layer 1: 수치 기반 Gate 조건 체크"""
        failures = []
        details = {}
        full_text = json.dumps(report_data, ensure_ascii=False)

        # 1. SUMMARY 분량 (600~900자)
        summary = report_data.get("summary", {})
        summary_text = " ".join(str(v) for v in summary.values() if isinstance(v, str))
        summary_len = len(summary_text)
        details["summary_length"] = summary_len
        if not (600 <= summary_len <= 900):
            failures.append(
                f"SUMMARY 분량 오류: {summary_len}자 (기준: 600~900자) "
                f"{'→ 줄여주세요' if summary_len > 900 else '→ 늘려주세요'}"
            )

        # 2. 본문 5개 챕터 존재 여부 (2~6장)
        required_sections = {
            "market_background": "2장 시장 배경",
            "lges_analysis": "3장 LG에너지솔루션 분석",
            "catl_analysis": "4장 CATL 분석",
            "strategy_comparison": "5장 전략 비교",
            "overall_implications": "6장 종합 시사점",
        }
        missing = [label for key, label in required_sections.items() if not report_data.get(key)]
        if missing:
            failures.append(f"섹션 누락: {', '.join(missing)}")
        details["missing_sections"] = missing

        # 3. REFERENCE 10건 이상
        refs = report_data.get("references", [])
        ref_count = len(refs)
        details["reference_count"] = ref_count
        if ref_count < 10:
            failures.append(f"REFERENCE 부족: {ref_count}건 (최소 10건 필요)")

        # 4. 기업명 언급 균형 (LGES:CATL = 4:6 ~ 6:4)
        lges_count = full_text.count("LG에너지솔루션") + full_text.count("LGES")
        catl_count = full_text.count("CATL")
        total_mentions = lges_count + catl_count
        details["lges_mentions"] = lges_count
        details["catl_mentions"] = catl_count
        if total_mentions > 0:
            lges_ratio = lges_count / total_mentions
            if not (0.4 <= lges_ratio <= 0.6):
                dominant = "LGES" if lges_ratio > 0.6 else "CATL"
                failures.append(
                    f"기업명 언급 불균형: LGES {lges_count}회 / CATL {catl_count}회 "
                    f"(비율 {lges_ratio:.0%}:{1-lges_ratio:.0%}) → {dominant} 편향"
                )

        # 5. Comparative SWOT 최소 8개 항목 (S/W/O/T × 2개사)
        swot_text = json.dumps(
            report_data.get("strategy_comparison", {}).get("comparative_swot", ""),
            ensure_ascii=False
        )
        # 한국어/영어 모두 허용: 4개 카테고리 각각 하나라도 매칭되면 통과
        swot_categories = [
            ["강점", "Strengths", "S:"],
            ["약점", "Weaknesses", "W:"],
            ["기회", "Opportunities", "O:"],
            ["위협", "Threats", "T:"],
        ]
        company_keywords = ["LG에너지솔루션", "LGES", "CATL"]
        swot_hit = sum(1 for cat in swot_categories if any(kw in swot_text for kw in cat))
        company_hit = sum(1 for kw in company_keywords if kw in swot_text)
        details["swot_keywords"] = swot_hit
        details["swot_companies"] = company_hit
        if swot_hit < 4 or company_hit < 2:
            failures.append(
                f"Comparative SWOT 항목 부족: "
                f"S/W/O/T 키워드 {swot_hit}/4개, 기업 언급 {company_hit}/2개 "
                f"(S/W/O/T × 2개사 = 최소 8항목 필요)"
            )

        return EvaluationResult(
            layer=1,
            passed=len(failures) == 0,
            failures=failures,
            details=details,
        )

    def evaluate_layer2(self, report_data: Dict[str, Any], llm) -> EvaluationResult:
        """Layer 2: LLM 기반 구조 체크리스트"""
        failures = []
        details = {}

        report_json = json.dumps(report_data, ensure_ascii=False, separators=(",", ":"))
        if len(report_json) > 4000:
            report_json = report_json[:4000] + "...(이하 생략)"

        prompt = LAYER2_EVAL_PROMPT.format(report_json=report_json)

        try:
            result = llm.invoke_json(
                system_prompt="당신은 보고서 품질 검토 전문가입니다. 주어진 항목을 객관적으로 평가하시오.",
                user_prompt=prompt,
            )
            for i in range(1, 6):
                check_key = f"check_{i}"
                reason_key = f"reason_{i}"
                passed = result.get(check_key, False)
                reason = result.get(reason_key, "")
                label = LAYER2_CHECK_LABELS.get(check_key, f"체크 {i}")
                details[check_key] = {"passed": passed, "reason": reason}
                if not passed:
                    failures.append(f"{label}: {reason}")
        except Exception as e:
            # Layer 2는 Gate가 아니므로 실패해도 경고만 기록하고 통과 처리
            # (LLM 오류로 인한 평가 불가를 보고서 실패로 처리하지 않음)
            details["error"] = str(e)
            details["skipped"] = True

        return EvaluationResult(
            layer=2,
            passed=len(failures) == 0,
            failures=failures,
            details=details,
        )
