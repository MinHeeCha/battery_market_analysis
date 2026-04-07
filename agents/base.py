"""
Base agent class - defines common interface for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import json
import re
from config.schema import ProjectState
from shared.logger import get_logger
from shared.llm_client import LLMClient


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Implements common interface: think → act → output
    
    모든 agent는 이 클래스를 상속하며, think → act → output 파이프라인을 구현합니다.
    
    Attributes:
        name: Agent의 이름
        llm: LLMClient 인스턴스 (자동 초기화)
        retriever: 검색 엔진 (선택사항)
        logger: 로거 인스턴스
    """
    
    def __init__(self, name: str, llm_client: Optional[LLMClient] = None, retriever: Optional[Any] = None):
        """
        Initialize base agent
        
        Args:
            name: Agent의 이름
            llm_client: LLMClient 인스턴스 (None이면 자동 생성)
            retriever: 검색 엔진 (선택사항)
        """
        self.name = name
        self.retriever = retriever
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize LLM client if not provided
        if llm_client is None:
            try:
                self.llm = LLMClient()
                self.logger.info(f"LLM client auto-initialized for {self.name}")
            except ValueError as e:
                self.logger.warning(f"LLM not initialized for {self.name}: {str(e)}")
                self.llm = None
        else:
            self.llm = llm_client
            self.logger.info(f"LLM client provided for {self.name}")
    
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
    def act(self, thought: Dict[str, Any]) -> Any:
        """
        Perform main reasoning/action through LLM.
        This is where you call the LLM.
        
        Args:
            thought: Output from think()
            
        Returns:
            LLM response (dict or str)
        """
        pass
    
    @abstractmethod
    def output(self, action_result: Any) -> Dict[str, Any]:
        """
        Format and validate the output.
        Convert raw LLM response to structured output.
        
        Args:
            action_result: Output from act()
            
        Returns:
            Structured output dictionary
        """
        pass
    
    # ========== Helper Methods for LLM Integration ==========
    
    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_json_mode: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Call LLM with structured prompts.
        
        Args:
            system_prompt: System role message
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            use_json_mode: Whether to request JSON output
            
        Returns:
            LLM response (dict if use_json_mode else str)
        """
        if not self.llm:
            self.logger.error(f"{self.name}: LLM not initialized")
            raise RuntimeError("LLM client not available")
        
        try:
            if use_json_mode:
                self.logger.debug(f"{self.name}: Calling LLM with JSON mode...")
                try:
                    return self.llm.invoke_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                except Exception as e:
                    # Fallback to text mode
                    self.logger.warning(f"{self.name}: JSON mode failed, falling back to text mode")
                    response = self.llm.invoke(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    # Try to parse JSON from text
                    return self._extract_json_from_text(response)
            else:
                self.logger.debug(f"{self.name}: Calling LLM in text mode...")
                return self.llm.invoke(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
        except Exception as e:
            self.logger.error(f"{self.name}: LLM call failed: {str(e)}")
            raise
    
    def parse_llm_response(
        self,
        response: str,
        expected_fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Parse LLM text response into structured format.
        
        Args:
            response: Raw LLM response text
            expected_fields: List of expected field names for parsing
            
        Returns:
            Parsed response as dictionary
        """
        # Try to extract JSON first
        try:
            json_response = self._extract_json_from_text(response)
            if isinstance(json_response, dict):
                return json_response
        except:
            pass
        
        # If no JSON, return as-is
        return {"content": response, "raw": True}
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from text containing other content.
        
        Args:
            text: Text possibly containing JSON
            
        Returns:
            Parsed JSON dictionary
        """
        # Find JSON pattern
        json_pattern = r'\{[\s\S]*\}'
        json_matches = re.findall(json_pattern, text)
        
        if json_matches:
            for match in json_matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid JSON found in response")
    
    def format_search_results(self, search_results: Dict[str, list]) -> str:
        """
        Format search results for LLM context.
        
        Args:
            search_results: Dictionary mapping queries to result lists
            
        Returns:
            Formatted search results string
        """
        if not search_results:
            return "(검색 결과 없음)"
        
        formatted = []
        for query, results in search_results.items():
            formatted.append(f"🔍 [{query}]")
            if results:
                for i, result in enumerate(results, 1):
                    if isinstance(result, dict):
                        content = result.get("content", "")[:300]
                        score = result.get("score", 0)
                        formatted.append(f"  {i}. {content} (관련도: {score:.2f})")
                    else:
                        formatted.append(f"  {i}. {str(result)[:300]}")
            else:
                formatted.append("  (결과 없음)")
        
        return "\n".join(formatted)
    
    def run(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the agent pipeline: think → act → output
        
        Args:
            context: Input context (can be ProjectState or dict)
            
        Returns:
            Final structured output
        """
        try:
            self.logger.info(f"=[{self.name}]= Agent starting...")
            
            # Convert ProjectState to dict if needed
            if isinstance(context, ProjectState):
                context = context.to_dict() if hasattr(context, 'to_dict') else context.__dict__
            elif context is None:
                context = {}
            
            # Pipeline execution with logging
            self.logger.info(f"  → Think phase...")
            thought = self.think(context)
            
            self.logger.info(f"  → Act phase...")
            action_result = self.act(thought)
            
            self.logger.info(f"  → Output phase...")
            output = self.output(action_result)
            
            self.logger.info(f"=[{self.name}]= Agent completed successfully ✓")
            return output
            
        except Exception as e:
            self.logger.error(f"=[{self.name}]= Agent failed: {str(e)}")
            raise
