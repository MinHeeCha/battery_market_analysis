"""
Report Writer Agent - prompt templates
"""

REVISION_PROMPT = """
아래 보고서에서 다음 항목들이 기준을 충족하지 못했습니다. 해당 부분을 수정하여 보고서 전체를 다시 작성하시오.

=== 수정 필요 항목 ===
{failures}

=== 현재 보고서 ===
{report_json}

=== 출력 형식 ==={output_format}
"""

REPORT_WRITER_SYSTEM_PROMPT = """
당신은 배터리 산업 전문 전략 애널리스트입니다.

역할:
- 시장 조사, 기업 분석, SWOT 분석 결과를 통합하여 경영진 보고서를 작성한다
- 각 섹션이 논리적으로 연결되도록 구성한다
- 데이터 기반의 객관적 분석과 전략적 시사점을 명확히 제시한다
- 전문적이고 일관된 한국어로 작성한다

출력 요구사항:
- 반드시 지정된 JSON 형식으로만 응답한다
- 각 섹션은 충분한 분량으로 작성한다 (섹션당 최소 3문장 이상)
- 요약(SUMMARY)은 전체 보고서를 읽지 않아도 핵심을 파악할 수 있도록 작성한다
"""

REPORT_COMPOSITION_PROMPT = """
아래 분석 자료를 바탕으로 배터리 시장 전략 비교 보고서를 작성하시오.

=== 입력 자료 ===

[시장 조사 결과]
{market_background}

[LG에너지솔루션 분석]
{lg_strategy}

[CATL 분석]
{catl_strategy}

[SWOT 비교 분석]
{comparative_swot}

=== 출력 형식 ===

반드시 아래 JSON 구조로만 응답하시오. 모든 필드를 빠짐없이 채워야 한다.

{{
  "summary": {{
    "key_conclusions": "핵심 결론 (3~5문장, 보고서 전체를 아우르는 핵심 메시지)",
    "market_summary": "시장 상황 요약 (시장 규모, 성장률, 수요 변화, 정책 동향)",
    "company_strategy_summary": "기업별 전략 핵심 (LGES와 CATL 각각의 핵심 전략 방향)",
    "comparison_result": "비교 결과 (두 기업의 전략적 포지셔닝 차이)",
    "insights": "인사이트 & 시사점 (향후 시장 전망 및 전략적 함의)"
  }},
  "market_background": {{
    "market_size_trend": "2.1 배터리 시장 규모 변화: EV 배터리 시장 장기 성장 여부, 글로벌 EV 배터리 수요 추이",
    "market_demand_change": "2.2 배터리 시장 수요 변화: EV/HEV·PHEV/ESS 수요처별 비중 변화, EV 캐즘과 HEV·ESS·신시장 전환",
    "policy_changes": "2.3 정책 변화: 현지 생산 및 산업 육성 정책, 무역·관세 정책, 배터리 규제 변화"
  }},
  "lges_analysis": {{
    "portfolio": "3.1 현재 사업 포트폴리오 현황: 주요 제품군, 핵심 고객사, 주요 진출 지역",
    "market_response": "3.2 시장 환경 변화 대응 전략: EV 캐즘 대응 방안, 수요 변화 대응",
    "diversification": "3.3 다각화 전략 방향: ESS, 신규 고객·시장 확장 전략",
    "core_competency": "3.4 핵심 경쟁력: 기술력, 파트너십, 생산 능력 등",
    "profitability": "3.5 수익성 구조 및 전략: 원가 구조, 수익성 확보 전략",
    "risks": "3.6 주요 리스크 및 과제: 지정학적 리스크, 경쟁 리스크, 내부 과제"
  }},
  "catl_analysis": {{
    "portfolio": "4.1 현재 사업 포트폴리오 현황: 주요 제품군, 핵심 고객사, 주요 진출 지역",
    "market_response": "4.2 시장 환경 변화 대응 전략: EV 캐즘 대응 방안, 수요 변화 대응",
    "diversification": "4.3 다각화 전략 방향: ESS, 신규 고객·시장 확장 전략",
    "core_competency": "4.4 핵심 경쟁력: 기술력, 파트너십, 생산 능력 등",
    "profitability": "4.5 수익성 구조 및 전략: 원가 구조, 수익성 확보 전략",
    "risks": "4.6 주요 리스크 및 과제: 지정학적 리스크, 경쟁 리스크, 내부 과제"
  }},
  "strategy_comparison": {{
    "core_strategy_comparison": "5.1 핵심 전략 비교: 기술 / 시장 / 원가 / 파트너십 4개 축에서 두 기업 비교",
    "lges_swot": "5.2 LG에너지솔루션 SWOT: 강점(S) / 약점(W) / 기회(O) / 위협(T) 각 항목별 서술",
    "catl_swot": "5.3 CATL SWOT: 강점(S) / 약점(W) / 기회(O) / 위협(T) 각 항목별 서술",
    "comparative_swot": "5.4 Comparative SWOT: S/W/O/T 각 항목에서 두 기업 비교 및 전략적 시사점"
  }},
  "overall_implications": "6. 종합 시사점: 시장 전망, 두 기업의 전략적 방향성, 업계 전반의 시사점 (5문장 이상)",
  "references": []
}}
"""
