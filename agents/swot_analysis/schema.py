"""
SWOT Analysis Agent - schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SWOTMatrix(BaseModel):
    """SWOT matrix for a single company"""
    company: str = Field(..., description="Company name")
    strengths: List[str] = Field(default_factory=list, description="Strengths (S)")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses (W)")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities (O)")
    threats: List[str] = Field(default_factory=list, description="Threats (T)")


class SWOTAnalysisOutput(BaseModel):
    """Output schema for SWOT analysis agent"""
    lg_swot: SWOTMatrix = Field(..., description="LG Energy Solution SWOT")
    catl_swot: SWOTMatrix = Field(..., description="CATL SWOT")
    comparative_analysis: str = Field(..., description="Comparative analysis between two companies")
    strategic_recommendation: str = Field(default="", description="Strategic recommendations")
    references: List[str] = Field(default_factory=list, description="Source references")
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
