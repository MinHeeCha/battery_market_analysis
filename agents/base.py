"""
Base agent class - defines common interface for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from config.schema import ProjectState
from shared.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Implements common interface: think → act → output
    """
    
    def __init__(self, name: str, llm_client=None, retriever=None):
        self.name = name
        self.llm = llm_client
        self.retriever = retriever
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather information and prepare for reasoning.
        This is where you search documents, collect data, etc.
        
        Args:
            context: Input context dictionary
            
        Returns:
            Dictionary with prepared information
        """
        pass
    
    @abstractmethod
    def act(self, thought: Dict[str, Any]) -> str:
        """
        Perform main reasoning/action through LLM.
        This is where you call the LLM.
        
        Args:
            thought: Output from think()
            
        Returns:
            Raw LLM response (text)
        """
        pass
    
    @abstractmethod
    def output(self, action_result: str) -> Dict[str, Any]:
        """
        Format and validate the output.
        Convert raw LLM response to structured output.
        
        Args:
            action_result: Output from act()
            
        Returns:
            Structured output dictionary
        """
        pass
    
    def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the agent pipeline: think → act → output
        
        Args:
            context: Input context (can be ProjectState or dict)
            
        Returns:
            Final structured output
        """
        try:
            self.logger.info(f"Agent {self.name} starting...")
            
            # Convert ProjectState to dict if needed
            if isinstance(context, ProjectState):
                context = context.to_dict()
            elif context is None:
                context = {}
            
            # Pipeline execution
            thought = self.think(context)
            action_result = self.act(thought)
            output = self.output(action_result)
            
            self.logger.info(f"Agent {self.name} completed successfully")
            return output
            
        except Exception as e:
            self.logger.error(f"Agent {self.name} failed: {str(e)}")
            raise
