"""
Supervisor Agent - orchestrates all agents and manages workflow
"""
from typing import Dict, Any, Optional
from agents.base import BaseAgent
from config.schema import ProjectState
from shared.logger import get_logger
from shared.utils import generate_execution_id

logger = get_logger(__name__)


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent - implements Supervisor Pattern.
    Responsible for orchestrating all agents and managing state handoff.
    """
    
    def __init__(self, llm_client=None, retriever=None, agents_dict: Dict[str, BaseAgent] = None):
        super().__init__(name="SupervisorAgent", llm_client=llm_client, retriever=retriever)
        self.agents = agents_dict or {}
        self.state: Optional[ProjectState] = None
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize state and prepare workflow"""
        self.logger.info("Supervisor: Thinking phase - initializing workflow...")
        
        # Create initial state
        execution_id = context.get("execution_id", generate_execution_id())
        self.state = ProjectState(execution_id=execution_id)
        
        return {
            "state": self.state,
            "execution_id": execution_id
        }
    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete workflow:
        1. Market Research → 2. Company Research → 3. SWOT Analysis → 4. Report Writing
        """
        self.logger.info(f"Supervisor: Acting phase - executing workflow for {thought['execution_id']}")
        
        self.state = thought["state"]
        workflow_results = {}
        
        try:
            # Phase 1: Market Research
            self.logger.info("Supervisor: Initiating Market Research Agent...")
            self.state.current_phase = "market_research"
            market_agent = self.agents.get("market_research")
            if market_agent:
                market_result = market_agent.run(self.state.to_dict())
                self.state.market_background = market_result.get("result", "")
                workflow_results["market_research"] = market_result
                self.logger.info("Market Research completed")
            
            # Phase 2: Company Research
            self.logger.info("Supervisor: Initiating Company Research Agent...")
            self.state.current_phase = "company_research"
            company_agent = self.agents.get("company_research")
            if company_agent:
                company_result = company_agent.run(self.state.to_dict())
                self.state.lg_strategy = company_result.get("lg_result", "")
                self.state.catl_strategy = company_result.get("catl_result", "")
                workflow_results["company_research"] = company_result
                self.logger.info("Company Research completed")
            
            # Phase 3: SWOT Analysis
            self.logger.info("Supervisor: Initiating SWOT Analysis Agent...")
            self.state.current_phase = "swot_analysis"
            swot_agent = self.agents.get("swot_analysis")
            if swot_agent:
                swot_result = swot_agent.run(self.state.to_dict())
                self.state.comparative_swot = swot_result.get("result", "")
                workflow_results["swot_analysis"] = swot_result
                self.logger.info("SWOT Analysis completed")
            
            # Phase 4: Report Writing
            self.logger.info("Supervisor: Initiating Report Writer Agent...")
            self.state.current_phase = "report_writing"
            report_agent = self.agents.get("report_writer")
            if report_agent:
                report_result = report_agent.run(self.state.to_dict())
                self.state.final_report = report_result.get("result", "")
                workflow_results["report_writer"] = report_result
                self.logger.info("Report Writing completed")
            
            return {
                "state": self.state,
                "workflow_results": workflow_results,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Supervisor: Workflow failed - {str(e)}")
            self.state.errors["workflow"] = str(e)
            return {
                "state": self.state,
                "status": "failed",
                "error": str(e)
            }
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format supervisor output"""
        self.logger.info("Supervisor: Output phase - formatting results...")
        
        return {
            "state": action_result["state"],
            "workflow_results": action_result.get("workflow_results", {}),
            "status": action_result.get("status", "unknown"),
            "execution_id": self.state.execution_id if self.state else None
        }
    
    def get_state(self) -> Optional[ProjectState]:
        """Get current state"""
        return self.state
