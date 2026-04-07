"""
Company Research Agent - schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class CompanyProfile(BaseModel):
    """Profile of a single company"""
    company_name: str = Field(..., description="Company name")
    core_competencies: List[str] = Field(default_factory=list, description="Core competencies")
    strategic_initiatives: str = Field(..., description="Strategic initiatives and plans")
    market_position: str = Field(..., description="Market position and ranking")
    production_capacity: str = Field(default="", description="Production capacity")
    technology_roadmap: str = Field(default="", description="Technology roadmap")
    partnerships: List[str] = Field(default_factory=list, description="Key partnerships")
    references: List[str] = Field(default_factory=list, description="Source references")


class CompanyResearchOutput(BaseModel):
    """Output schema for company research agent"""
    lg_strategy: CompanyProfile = Field(..., description="LG Energy Solution profile")
    catl_strategy: CompanyProfile = Field(..., description="CATL profile")
    comparative_strengths: str = Field(default="", description="Comparative strengths")
    comparative_weaknesses: str = Field(default="", description="Comparative weaknesses")
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
