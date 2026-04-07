"""Prompt templates and query definitions for CompanyResearchAgent."""

from typing import Dict


SECTION_QUERIES: Dict[str, str] = {
	"portfolio_status": "{company} 현재 사업 포트폴리오 현황 제품 고객 지역",
	"market_response_strategy": "{company} 시장 환경 변화 대응 전략 EV 캐즘 대응",
	"diversification_strategy": "{company} 다각화 전략 방향",
	"core_competency": "{company} 핵심 경쟁력",
	"profitability_strategy": "{company} 수익성 구조 및 전략",
	"risks_and_challenges": "{company} 주요 리스크 및 과제",
}


RETRY_HINT = "최신 실적 전략 리스크 공시 발표 투자자자료"


COMPANY_SYSTEM_PROMPT = """
You are a senior battery industry strategy analyst.
You must produce concise, evidence-grounded output in Korean.
Return a JSON object with exactly these keys:
- portfolio_status
- market_response_strategy
- diversification_strategy
- core_competency
- profitability_strategy
- risks_and_challenges

Rules:
1) Do not fabricate facts.
2) Reflect uncertainty where evidence is weak.
3) Use business-focused wording suitable for executive reporting.
4) Each section should be 3-6 sentences.
""".strip()


def build_company_user_prompt(company_name: str, evidence_text: str) -> str:
	"""Build user prompt for one company using aggregated evidence."""
	return f"""
대상 기업: {company_name}

아래 근거를 바탕으로 6개 항목을 분석하라.

[근거]
{evidence_text}

반드시 JSON 객체로만 답하라.
""".strip()

