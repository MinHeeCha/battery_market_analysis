#!/usr/bin/env python3
"""
Market Research Agent Test
Tests the MarketResearchAgent with LLM integration
"""
import sys
import os
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from shared.logger import get_logger
from agents.market_research.agent import MarketResearchAgent
from retrieval.retriever import Retriever

logger = get_logger(__name__)


def test_market_research_agent():
    """Test MarketResearchAgent with full pipeline"""
    print("=" * 70)
    print("Market Research Agent Test")
    print("=" * 70)
    
    try:
        # Initialize components
        print("\n[1] Initializing components...")
        retriever = Retriever()
        agent = MarketResearchAgent(retriever=retriever)
        print("  ✓ Agent initialized")
        
        # Test context
        context = {
            "execution_id": "test-market-001",
            "target_companies": ["LG에너지솔루션", "CATL"]
        }
        
        # Think phase
        print("\n[2] Thinking phase: Searching for market documents...")
        thought = agent.think(context)
        print(f"  ✓ Queries executed: {len(thought.get('queries', []))} queries")
        print(f"    Queries: {thought.get('queries', [])}")
        
        search_results_count = sum(
            len(results) for results in thought.get('search_results', {}).values()
        )
        print(f"  ✓ Search results: {search_results_count} results found")
        
        # Act phase
        print("\n[3] Acting phase: LLM analysis...")
        action_result = agent.act(thought)
        print("  ✓ LLM analysis completed")
        
        # Display LLM response structure
        if isinstance(action_result, dict):
            print("\n  📊 Analysis Results:")
            for key, value in action_result.items():
                if isinstance(value, list):
                    print(f"    - {key}: {len(value)} items")
                    if value:
                        for item in value[:3]:
                            print(f"      • {item}")
                        if len(value) > 3:
                            print(f"      ... and {len(value) - 3} more")
                elif isinstance(value, str):
                    preview = value[:100] + "..." if len(value) > 100 else value
                    print(f"    - {key}: {preview}")
                else:
                    print(f"    - {key}: {value}")
        
        # Output phase
        print("\n[4] Output phase: Structuring results...")
        output = agent.output(action_result)
        print("  ✓ Results structured and validated")
        
        # Display final output
        print("\n" + "=" * 70)
        print("📋 FINAL OUTPUT")
        print("=" * 70)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 70)
        print("✓ TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_market_research_agent()
    sys.exit(0 if success else 1)
