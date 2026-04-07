#!/usr/bin/env python3
"""
Main workflow execution script - runs the complete agent pipeline
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config
from config.schema import ProjectState
from shared.logger import get_logger
from shared.utils import generate_execution_id
from agents.supervisor.agent import SupervisorAgent
from agents.market_research.agent import MarketResearchAgent
from agents.company_research.agent import CompanyResearchAgent
from agents.swot_analysis.agent import SWOTAnalysisAgent
from agents.report_writer.agent import ReportWriterAgent
from retrieval.retriever import Retriever
from validators.content_validators import (
    MarketValidator, CompanyValidator, SWOTValidator, ReportValidator
)
from state.state_manager import StateManager
from report.json_builder import JSONBuilder
from report.markdown_builder import MarkdownBuilder
logger = get_logger(__name__)


def main():
    """Main execution entry point"""
    logger.info("=" * 60)
    logger.info("Battery Analysis System - Complete Workflow")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        execution_id = generate_execution_id()
        logger.info(f"Execution ID: {execution_id}")
        
        retriever = Retriever(
            vector_store_path=config.rag.vector_store_path,
            use_web_search=config.use_web_search
        )
        
        # Create agent instances
        market_agent = MarketResearchAgent(retriever=retriever)
        company_agent = CompanyResearchAgent(retriever=retriever)
        swot_agent = SWOTAnalysisAgent()
        report_agent = ReportWriterAgent()
        
        # Create supervisor with all agents
        agents_dict = {
            "market_research": market_agent,
            "company_research": company_agent,
            "swot_analysis": swot_agent,
            "report_writer": report_agent
        }
        
        supervisor = SupervisorAgent(agents_dict=agents_dict)
        
        # Run workflow
        logger.info("Starting workflow execution...")
        result = supervisor.run({"execution_id": execution_id})
        
        final_state = supervisor.get_state()
        
        if final_state and final_state.final_report:
            logger.info("Workflow completed successfully!")
            
            # Save JSON report (PRIMARY OUTPUT)
            logger.info("Generating JSON report...")
            json_builder = JSONBuilder(output_dir=f"{config.output_dir}/reports_json")
            
            # Get report output from final_state
            report_output = final_state.final_report
            if isinstance(report_output, str):
                # If it's a string, convert to dict
                report_data = {
                    "executive_summary": "AI Agent 기반 분석 결과",
                    "introduction": report_output,
                    "lg_analysis": final_state.lg_strategy or "",
                    "catl_analysis": final_state.catl_strategy or "",
                    "comparative_swot": final_state.comparative_swot or "",
                    "conclusion_and_recommendation": "분석 결과 참고",
                    "references": []
                }
            else:
                report_data = report_output
            
            json_report = json_builder.build_from_report_output(report_data)
            json_path = json_builder.save_report(json_report)
            logger.info(f"JSON report saved to: {json_path}")
            
            # Save markdown report (OPTIONAL)
            logger.info("Generating markdown report...")
            md_builder = MarkdownBuilder(output_dir=f"{config.output_dir}/reports_md")
            md_content = md_builder.build_from_state(final_state)
            md_path = md_builder.save_report(md_content)
            logger.info(f"Markdown report saved to: {md_path}")
            
            # Save final state
            state_manager = StateManager(output_dir=config.output_dir)
            state_manager.save_state(final_state, "final")
            
            logger.info("=" * 60)
            logger.info("All outputs saved to:")
            logger.info(f"  - JSON (PRIMARY): {json_path}")
            logger.info(f"  - Markdown: {md_path}")
            logger.info("=" * 60)
            
            return 0
        else:
            logger.error("Workflow failed or no final report generated")
            return 1
    
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
