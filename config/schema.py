"""
Shared Pydantic schemas for state management
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ProjectState(BaseModel):
    """
    Central state object shared across all agents.
    Implements state handoff pattern.
    """
    # Execution metadata
    execution_id: str = Field(..., description="Unique execution ID")
    created_at: datetime = Field(default_factory=datetime.now)
    current_phase: str = Field(default="init", description="Current workflow phase")
    
    # Phase outputs (Agent outputs)
    market_background: Optional[str] = Field(None, description="Market research results (~2 pages)")
    lg_strategy: Optional[str] = Field(None, description="LG Energy strategy analysis (~1 page)")
    catl_strategy: Optional[str] = Field(None, description="CATL strategy analysis (~1 page)")
    comparative_swot: Optional[str] = Field(None, description="Comparative SWOT analysis (~2 pages)")
    final_report: Optional[str] = Field(None, description="Final compiled report content")
    
    # Metadata
    retry_count: Dict[str, int] = Field(default_factory=dict, description="Retry count per agent")
    validation_status: Dict[str, bool] = Field(default_factory=dict, description="Validation status per phase")
    errors: Dict[str, str] = Field(default_factory=dict, description="Error messages per phase")
    
    # Config for tracking
    config_hash: str = Field(default="", description="Hash of configuration used")
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "execution_id": "exec_20240407_120000",
                "current_phase": "market_research",
                "market_background": "...",
                "retry_count": {"market": 0},
                "validation_status": {"market": True}
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=False)
