"""
Company Research Agent - schema definitions
기업별 6개 섹션 결과를 각각 담기 위한 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class SourceItem(BaseModel):
    """최종 채택 출처"""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    source_type: Literal[
        "official_report",
        "company_report",
        "policy_document",
        "research_report",
        "news",
        "other",
    ] = Field(..., description="Type of source")
    author: Optional[str] = Field(None, description="Author or organization name")
    year: Optional[str] = Field(None, description="Publication year")
    journal: Optional[str] = Field(None, description="Journal or publication name")
    volume: Optional[str] = Field(None, description="Volume number")
    issue: Optional[str] = Field(None, description="Issue number")
    pages: Optional[str] = Field(None, description="Page range")
    site_name: Optional[str] = Field(None, description="Website name for web sources")


class CompanySectionResult(BaseModel):
    """회사 1개의 6개 섹션 분석 결과"""
    portfolio_status: str = Field(
        default="",
        description="현재 사업 포트폴리오 현황 제품 고객 지역"
    )
    market_response_strategy: str = Field(
        default="",
        description="시장 환경 변화 대응 전략 EV 캐즘 대응 포함"
    )
    diversification_strategy: str = Field(
        default="",
        description="다각화 전략 방향"
    )
    core_competency: str = Field(
        default="",
        description="핵심 경쟁력"
    )
    profitability_strategy: str = Field(
        default="",
        description="수익성 구조 및 전략"
    )
    risks_and_challenges: str = Field(
        default="",
        description="주요 리스크 및 과제"
    )


class CompanyResearchResult(BaseModel):
    """회사 1개의 최종 조사 결과"""
    company_name: str = Field(..., description="Company name")
    response: CompanySectionResult = Field(
        ...,
        description="6개 섹션 기준 조사 결과"
    )
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="최종 채택 출처 목록"
    )


class CompanyResearchOutput(BaseModel):
    """기업조사 agent 최종 출력"""
    lg_strategy: CompanyResearchResult = Field(
        ...,
        description="LG Energy Solution analysis result"
    )
    catl_strategy: CompanyResearchResult = Field(
        ...,
        description="CATL analysis result"
    )