"""
Market Research Agent - schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class MarketResearchOutput(BaseModel):
    """Output schema for market research agent"""
    market_size: str = Field(..., description="Current market size and growth rate")
    key_players: List[str] = Field(default_factory=list, description="Key market players")
    technology_trends: str = Field(..., description="Current and emerging technology trends")
    competitive_landscape: str = Field(..., description="Competitive analysis and market structure")
    market_opportunities: str = Field(..., description="Growth opportunities and market gaps")
    regional_analysis: str = Field(..., description="Regional market breakdown and analysis")
    supply_chain_analysis: str = Field(default="", description="Supply chain insights")
    references: List[str] = Field(default_factory=list, description="Source references URL/names")
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
