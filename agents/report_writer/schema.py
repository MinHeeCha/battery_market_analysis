"""
Report Writer Agent - schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class SummarySection(BaseModel):
    key_conclusions: str = Field(..., description="핵심 결론")
    market_summary: str = Field(..., description="시장 상황 요약")
    company_strategy_summary: str = Field(..., description="기업별 전략 핵심")
    comparison_result: str = Field(..., description="비교 결과")
    insights: str = Field(..., description="인사이트 & 시사점")


class MarketBackgroundSection(BaseModel):
    market_size_trend: str = Field(..., description="2.1 배터리 시장 규모 변화")
    market_demand_change: str = Field(..., description="2.2 배터리 시장 수요 변화")
    policy_changes: str = Field(..., description="2.3 정책 변화")


class CompanyAnalysisSection(BaseModel):
    portfolio: str = Field(..., description="현재 사업 포트폴리오 현황 (제품·고객·지역)")
    market_response: str = Field(..., description="시장 환경 변화 대응 전략 (EV 캐즘 대응 포함)")
    diversification: str = Field(..., description="다각화 전략 방향")
    core_competency: str = Field(..., description="핵심 경쟁력")
    profitability: str = Field(..., description="수익성 구조 및 전략")
    risks: str = Field(..., description="주요 리스크 및 과제")


class StrategyComparisonSection(BaseModel):
    core_strategy_comparison: str = Field(..., description="5.1 핵심 전략 비교 (기술/시장/원가/파트너십)")
    lges_swot: str = Field(..., description="5.2 LG에너지솔루션 SWOT 분석")
    catl_swot: str = Field(..., description="5.3 CATL SWOT 분석")
    comparative_swot: str = Field(..., description="5.4 Comparative SWOT (S/W/O/T × 두 기업 × 전략적 시사점)")


class ReportOutput(BaseModel):
    """Output schema for report writer agent"""
    summary: SummarySection = Field(..., description="1. SUMMARY")
    market_background: MarketBackgroundSection = Field(..., description="2. 시장 배경")
    lges_analysis: CompanyAnalysisSection = Field(..., description="3. LG에너지솔루션 전략 분석")
    catl_analysis: CompanyAnalysisSection = Field(..., description="4. CATL 전략 분석")
    strategy_comparison: StrategyComparisonSection = Field(..., description="5. 전략 비교 및 Comparative SWOT")
    overall_implications: str = Field(..., description="6. 종합 시사점")
    references: List[str] = Field(default_factory=list, description="7. REFERENCE")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="보고서 메타데이터")

    class Config:
        arbitrary_types_allowed = True
