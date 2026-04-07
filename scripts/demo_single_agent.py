#!/usr/bin/env python3
"""
Test single agent execution - useful for development and debugging
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.logger import get_logger
from agents.market_research.agent import MarketResearchAgent
from agents.company_research.agent import CompanyResearchAgent
from agents.swot_analysis.agent import SWOTAnalysisAgent
from agents.report_writer.agent import ReportWriterAgent
from retrieval.retriever import Retriever

logger = get_logger(__name__)


def test_agent(agent_name: str):
    """Test single agent"""
    logger.info(f"Testing {agent_name} agent...")
    
    retriever = Retriever()
    
    if agent_name == "market":
        agent = MarketResearchAgent(retriever=retriever)
        result = agent.run()
    elif agent_name == "company":
        agent = CompanyResearchAgent(retriever=retriever)
        result = agent.run()
    elif agent_name == "swot":
        agent = SWOTAnalysisAgent()
        result = agent.run()
    elif agent_name == "report":
        agent = ReportWriterAgent()
        result = agent.run()
    else:
        logger.error(f"Unknown agent: {agent_name}")
        return 1
    
    logger.info(f"Result: {result}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test single agent")
    parser.add_argument(
        "--agent",
        choices=["market", "company", "swot", "report"],
        default="market",
        help="Agent to test"
    )
    
    args = parser.parse_args()
    sys.exit(test_agent(args.agent))
