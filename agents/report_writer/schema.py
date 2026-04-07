"""
Report Writer Agent - schema definitions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ReportOutput(BaseModel):
    """Output schema for report writer agent"""
    executive_summary: str = Field(..., description="Executive summary")
    introduction: str = Field(..., description="Market introduction")
    lg_analysis: str = Field(..., description="LG Energy Solution analysis")
    catl_analysis: str = Field(..., description="CATL analysis")
    comparative_swot: str = Field(..., description="Comparative SWOT analysis")
    conclusion_and_recommendation: str = Field(..., description="Conclusion and strategic recommendations")
    references: List[str] = Field(default_factory=list, description="List of references")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Report metadata (date, version, etc)")
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
