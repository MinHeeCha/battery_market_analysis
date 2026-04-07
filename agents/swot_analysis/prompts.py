"""
SWOT Analysis Agent - prompt templates
"""

SWOT_ANALYSIS_SYSTEM_PROMPT = """
당신은 배터리 업계 전략 분석 전문가입니다.

역할:
- LG에너지솔루션과 CATL의 강점, 약점, 기회, 위협을 분석한다
- 시장 환경과 기업 전략을 종합적으로 평가한다
- 두 기업의 상대적 위치를 비교 분석한다
- 전략적 시사점을 도출한다

출력 요구사항:
- 각 기업의 SWOT 분석 (각 2-3개 항목)
- 비교 분석: 약 2페이지
- 정성적이고 인사이트 있는 내용
- 한국어로 작성
"""

SWOT_ANALYSIS_USER_PROMPT_TEMPLATE = """
다음 정보를 바탕으로 배터리 시장에서 LG에너지솔루션과 CATL의 SWOT 분석을 수행하시오:

### 시장 배경
{market_background}

### LG에너지솔루션 전략
{lg_strategy}

### CATL 전략
{catl_strategy}

분석 내용:
1. 각 기업의 강점 (S)
2. 각 기업의 약점 (W)
3. 시장 기회 (O)
4. 시장 위협 (T)
5. 상대적 경쟁 우위
6. 전략적 시사점

구조화된 SWOT 분석을 제공하시오.
"""

SWOT_VALIDATION_PROMPT = """
다음 SWOT 분석의 품질을 평가하시오:

{swot_analysis}

평가 기준:
1. SWOT 구성의 완전성
2. 논리적 일관성
3. 비교 분석의 명확성
4. 전략적 인사이트
5. 시장 현실과의 부합성

평가 결과: 통과/불통과
피드백: [구체적인 개선 사항]
"""
