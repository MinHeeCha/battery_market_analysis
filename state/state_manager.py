"""
State manager for handling workflow state handoff
"""
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """
    Manages state persistence and handoff between agents.
    Responsible for state serialization, validation, and history tracking.
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_history_dir = self.output_dir / "state_history"
        self.state_history_dir.mkdir(exist_ok=True)
    
    def create_initial_state(self, execution_id: str) -> ProjectState:
        """Create initial empty state"""
        return ProjectState(
            execution_id=execution_id,
            current_phase="init",
            created_at=datetime.now()
        )
    
    def update_state(self, state: ProjectState, phase: str, data: Dict[str, Any]) -> ProjectState:
        """Update state with new phase data"""
        state.current_phase = phase
        
        if phase == "market_research":
            state.market_background = data.get("result")
        elif phase == "company_research":
            state.lg_strategy = data.get("lg_result")
            state.catl_strategy = data.get("catl_result")
        elif phase == "swot_analysis":
            swot_result = data.get("result")
            if isinstance(swot_result, dict):
                state.comparative_swot = swot_result.get("comparative_swot", "")
            else:
                state.comparative_swot = swot_result
        elif phase == "report_writing":
            state.final_report = data.get("result")
        
        # Update validation and retry status
        if "validation_passed" in data:
            state.validation_status[phase] = data["validation_passed"]
        if "retry_count" in data:
            state.retry_count[phase] = data["retry_count"]
        
        logger.info(f"State updated at phase: {phase}")
        self.save_state(state, phase)
        return state
    
    def save_state(self, state: ProjectState, phase: str = "checkpoint"):
        """Save state to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.state_history_dir / f"state_{phase}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, indent=2, default=str, ensure_ascii=False)
        
        logger.debug(f"State saved to {filename}")
    
    def load_state(self, execution_id: str, phase: Optional[str] = None) -> Optional[ProjectState]:
        """Load state from file"""
        try:
            if phase:
                pattern = f"state_{phase}_*.json"
            else:
                pattern = f"state_*_{execution_id}.json"
            
            files = sorted(self.state_history_dir.glob(pattern))
            if not files:
                return None
            
            latest_file = files[-1]
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ProjectState(**data)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def get_state_config_hash(self, state: ProjectState) -> str:
        """Get hash of the state configuration"""
        config_str = json.dumps(state.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()
