"""
Market Research Agent - investigates battery market trends, size, and competitive landscape
Uses BaseAgent's LLM integration helper methods and prompts from prompts.py
"""
from typing import Dict, Any
from agents.base import BaseAgent
from pydantic import BaseModel, Field
from agents.market_research.prompts import (
    MARKET_RESEARCH_SYSTEM_PROMPT,
    MARKET_RESEARCH_USER_PROMPT_TEMPLATE
)


class MarketResearchOutput(BaseModel):
    """Output schema for market research"""
    market_size: str = Field(..., description="Market size and growth")
    key_players: list[str] = Field(default_factory=list, description="Key market players")
    technology_trends: str = Field(..., description="Technology trends and innovations")
    competitive_landscape: str = Field(..., description="Competitive analysis")
    market_opportunities: str = Field(..., description="Market opportunities")
    regional_analysis: str = Field(..., description="Regional market analysis")
    references: list[str] = Field(default_factory=list, description="Source references")


class MarketResearchAgent(BaseAgent):
    """
    Agent for market research analysis
    
    Pipeline:
    1. Think: Search for relevant market documents
    2. Act: Use LLM to analyze market information
    3. Output: Structure and validate results
    """
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="MarketResearchAgent", llm_client=llm_client, retriever=retriever)
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search and gather market information"""
        self.logger.info("Thinking: Searching market documents...")
        
        queries = [
            "배터리 시장 규모 성장률",
            "전기차 배터리 시장 트렌드",
            "배터리 기술 혁신",
            "배터리 시장 경쟁사 분석",
            "전 세계 배터리 시장 동향"
        ]
        
        search_results = {}
        if self.retriever:
            for query in queries:
                results = self.retriever.search(query, top_k=3)
                search_results[query] = results
        
        return {
            "queries": queries,
            "search_results": search_results,
            "context": context
        }
    

    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze market information with prompts from prompts.py"""
        self.logger.info("Acting phase: analyzing market data with LLM...")
        
        # Extract and format context from thinking phase
        context = thought.get("context", {})
        context_str = self._format_context(context)
        
        # Format search results for better readability
        search_context = self._format_search_results(thought.get("search_results", {}))
        
        # Use prompts from prompts.py for better maintenance
        system_prompt = MARKET_RESEARCH_SYSTEM_PROMPT
        user_prompt = MARKET_RESEARCH_USER_PROMPT_TEMPLATE.format(
            context=context_str,
            search_results=search_context
        )

        if not self.llm:
            return self._get_placeholder_analysis()
        
        try:
            # Call LLM with structured prompt - try JSON first
            self.logger.info("Calling LLM for market analysis (JSON mode)...")
            try:
                response = self.llm.invoke_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    max_tokens=2000
                )
                self.logger.info(f"LLM JSON response received")
                return response
            except Exception as json_error:
                # Fallback to text mode if JSON fails
                self.logger.warning(f"JSON mode failed: {str(json_error)}, falling back to text mode")
                response = self.llm.invoke(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    max_tokens=2000
                )
                self.logger.info(f"LLM text response received, parsing results...")
                result = self._parse_market_analysis(response)
                return result
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {str(e)}, returning placeholder")
            return self._get_placeholder_analysis()
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output"""
        self.logger.info("Output phase: formatting market research results...")
        
        # Create structured output using MarketResearchOutput schema
        try:
            output = MarketResearchOutput(
                market_size=action_result.get("market_size", ""),
                key_players=action_result.get("key_players", []),
                technology_trends=action_result.get("technology_trends", ""),
                competitive_landscape=action_result.get("competitive_landscape", ""),
                market_opportunities=action_result.get("market_opportunities", ""),
                regional_analysis=action_result.get("regional_analysis", ""),
                references=action_result.get("references", [])
            )
            self.logger.info("Market research output validated successfully")
            return output.dict()
        except Exception as e:
            self.logger.error(f"Output validation failed: {str(e)}, returning raw result")
            return action_result
    
    def _format_search_results(self, search_results: Dict[str, list]) -> str:
        """Format search results for LLM context"""
        if not search_results:
            return "(검색 결과 없음)"
        
        formatted = []
        for query, results in search_results.items():
            formatted.append(f"🔍 [{query}]")
            if results:
                for i, result in enumerate(results, 1):
                    content = result.get("content", "")[:300] if isinstance(result, dict) else str(result)[:300]
                    score = result.get("score", 0) if isinstance(result, dict) else 0
                    formatted.append(f"  {i}. {content} (관련도: {score:.2f})")
            else:
                formatted.append("  (결과 없음)")
        
        return "\n".join(formatted)
    
    def _format_context(self, context: Any) -> str:
        """
        Safely format context for LLM prompt.
        Converts dict/list to human-readable string format.
        """
        if not context:
            return "(요청 배경 정보 없음)"
        
        if isinstance(context, str):
            return context
        
        if isinstance(context, dict):
            # Format dict as key-value pairs
            lines = []
            for key, value in context.items():
                # Handle various value types
                if isinstance(value, (list, dict)):
                    # Convert nested structures to simple repr
                    lines.append(f"• {key}: {str(value)[:200]}")
                else:
                    lines.append(f"• {key}: {value}")
            return "\n".join(lines) if lines else "(요청 배경 정보 없음)"
        
        if isinstance(context, list):
            # Format list as bullet points
            lines = [f"• {str(item)[:200]}" for item in context]
            return "\n".join(lines) if lines else "(요청 배경 정보 없음)"
        
        # For other types, try to convert to string safely
        try:
            return str(context)[:500]
        except Exception as e:
            self.logger.warning(f"Failed to format context: {str(e)}")
            return "(요청 배경 정보 포맷팅 실패)"
    
    
    def _parse_market_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured market analysis"""
        import json
        import re
        
        # Try to extract JSON from response
        json_pattern = r'\{[\s\S]*\}'
        json_matches = re.findall(json_pattern, llm_response)
        
        # Try to parse JSON if found
        if json_matches:
            for match in json_matches:
                try:
                    result = json.loads(match)
                    # Validate it has expected keys
                    expected_keys = ["market_size", "key_players", "technology_trends", 
                                    "competitive_landscape", "market_opportunities", "regional_analysis"]
                    if any(key in result for key in expected_keys):
                        # Ensure all fields exist
                        for key in expected_keys:
                            if key not in result:
                                result[key] = "" if key != "key_players" else []
                        return result
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, do simple text parsing
        result = {
            "market_size": "",
            "key_players": [],
            "technology_trends": "",
            "competitive_landscape": "",
            "market_opportunities": "",
            "regional_analysis": "",
            "references": []
        }
        
        # Split by common section headers
        lines = llm_response.split('\n')
        current_section = None
        buffer = []
        
        section_keywords = {
            "market_size": ["시장 규모", "market size", "규모", "성장률"],
            "key_players": ["주요", "플레이어", "참여자", "회사", "기업", "players", "companies"],
            "technology_trends": ["기술", "트렌드", "혁신", "technology", "trends", "innovation"],
            "competitive_landscape": ["경쟁", "competitive", "경쟁 구도", "landscape"],
            "market_opportunities": ["기회", "기회", "opportunity", "opportunities"],
            "regional_analysis": ["지역", "regional", "지역별", "분석"]
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new section
            new_section = None
            for section, keywords in section_keywords.items():
                if any(keyword in line.lower() for keyword in keywords):
                    new_section = section
                    break
            
            if new_section and new_section != current_section:
                # Save previous section
                if current_section and buffer:
                    content = '\n'.join(buffer).strip()
                    if current_section == "key_players":
                        # Parse as list
                        result[current_section] = [p.strip() for p in content.split(',') if p.strip()]
                    else:
                        result[current_section] = content
                
                current_section = new_section
                buffer = [line]
            else:
                buffer.append(line)
        
        # Save last section
        if current_section and buffer:
            content = '\n'.join(buffer).strip()
            if current_section == "key_players":
                result[current_section] = [p.strip() for p in content.split(',') if p.strip()]
            else:
                result[current_section] = content
        
        return result
    
    def _get_placeholder_analysis(self) -> Dict[str, Any]:
        return {
            "market_size": "LLM unavailable",
            "key_players": [],
            "technology_trends": "LLM unavailable",
            "competitive_landscape": "LLM unavailable",
            "market_opportunities": "LLM unavailable",
            "regional_analysis": "LLM unavailable",
            "references": []
        }
