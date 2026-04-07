"""
Tests for Market Research Agent
"""
import unittest
from agents.market_research.agent import MarketResearchAgent


class TestMarketResearchAgent(unittest.TestCase):
    """Test cases for market research agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = MarketResearchAgent()
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.name, "MarketResearchAgent")
    
    def test_think_phase(self):
        """Test think phase"""
        context = {}
        result = self.agent.think(context)
        self.assertIn("queries", result)
        self.assertIn("search_results", result)
    
    def test_act_phase(self):
        """Test act phase"""
        thought = {"search_results": {}}
        result = self.agent.act(thought)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_output_phase(self):
        """Test output phase"""
        action_result = "Test output"
        result = self.agent.output(action_result)
        self.assertEqual(result["agent"], "market_research")
        self.assertEqual(result["status"], "completed")


if __name__ == "__main__":
    unittest.main()
