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
    key_players: list = Field(default_factory=list, description="Key market players")
    technology_trends: str = Field(..., description="Technology trends and innovations")
    competitive_landscape: str = Field(..., description="Competitive analysis")
    market_opportunities: str = Field(..., description="Market opportunities")
    regional_analysis: str = Field(..., description="Regional market analysis")
    references: list = Field(default_factory=list, description="Source references")


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
        """Use LLM to analyze market information using BaseAgent's helper method"""
        self.logger.info("Acting: Analyzing market data with LLM...")
        
        # Use BaseAgent's helper method to format search results
        search_context = self.format_search_results(thought.get("search_results", {}))
        
        system_prompt = """당신은 배터리 산업 전문가이고 국제적 시장 분석 경험이 풍부합니다.
당신의 역할:
1. 배터리 시장의 규모와 성장 추이를 분석
2. 주요 플레이어와 시장 점유율 파악
3. 기술 트렌드와 혁신 사항 식별
4. 경쟁 구도 분석
5. 시장 기회 포인트 발굴
6. 지역별 시장 특성 파악"""

        user_prompt = f"""다음 검색 결과들을 종합하여 배터리 시장을 분석해주세요.
검색 결과가 제한적이더라도, 전문 지식과 함께 최선의 분석을 제공해주세요:

[검색 결과]
{search_context}

[분석 요청]
다음 각 항목에 대해 구체적으로 분석하세요:

1. **시장 규모와 성장률**: 현재 규모와 예상 성장률
2. **주요 시장 참여자**: 주요 배터리 제조사 목록 (쉼표 구분)
3. **기술 트렌드**: 혁신 기술과 최신 동향
4. **경쟁 구도**: 시장 경쟁 상황과 기업 전략
5. **시장 기회**: 성장 기회와 새로운 수요
6. **지역별 분석**: 중국, 한국, 유럽, 북미의 특성

각 항목은 2-3문장으로 명확하고 전문적인 분석 부탁합니다."""

        if not self.llm:
            # Fallback: placeholder response
            self.logger.warning("LLM not available, using placeholder")
            return self._get_placeholder_response()
        
        try:
            # Use BaseAgent's helper method to call LLM
            response = self.call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000,
                use_json_mode=False  # GPT-4는 JSON mode 미지원이므로 text mode 사용
            )
            
            # If response is already a dict (JSON parsed), return it
            if isinstance(response, dict):
                return response
            
            # Otherwise parse the text response
            return self.parse_llm_response(response)
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}, using placeholder")
            return self._get_placeholder_response()
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output"""
        self.logger.info("Output: Structuring market research results...")
        
        try:
            # Create structured output using MarketResearchOutput schema
            output = MarketResearchOutput(
                market_size=action_result.get("market_size", ""),
                key_players=self._parse_key_players(action_result.get("key_players", [])),
                technology_trends=action_result.get("technology_trends", ""),
                competitive_landscape=action_result.get("competitive_landscape", ""),
                market_opportunities=action_result.get("market_opportunities", ""),
                regional_analysis=action_result.get("regional_analysis", ""),
                references=action_result.get("references", [])
            )
            self.logger.info("Output validation successful")
            return output.dict()
        except Exception as e:
            self.logger.error(f"Output validation failed: {str(e)}, returning raw result")
            return action_result
    
    # ========== Helper Methods ==========
    
    def _parse_key_players(self, key_players: Any) -> list:
        """Parse key players from various formats"""
        if isinstance(key_players, list):
            return key_players
        elif isinstance(key_players, str):
            # Split comma-separated string
            return [p.strip() for p in key_players.split(',') if p.strip()]
        else:
            return []
    
    def _get_placeholder_response(self) -> Dict[str, Any]:
        """Return placeholder response when LLM unavailable"""
        return {
            "market_size": "2023년 기준 약 100조 원 규모로 추정되며, 연평균 15-20% 성장률 기록",
            "key_players": ["LG에너지솔루션", "CATL", "BYD", "Panasonic", "Samsung SDI"],
            "technology_trends": "고에너지 밀도, 빠른 충전, 안전성 향상 방향으로 진화. 고체배터리, 나트륨이온 배터리 등 차세대 기술 개발 활발",
            "competitive_landscape": "중국 기업의 수직 통합 전략과 한국/일본 기업의 기술 고도화로 양극화",
            "market_opportunities": "전기차 시장 확대, ESS 수요 증가, 차세대 배터리 기술 개발",
            "regional_analysis": "중국: 생산 능력 위주 / 한국: 기술 고도화 / 유럽: 환경 규제 강화",
            "references": []
        }
    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze market information"""
        self.logger.info("Acting phase: analyzing market data with LLM...")
        
        # Format search results for better readability
        search_context = self._format_search_results(thought.get("search_results", {}))
        
        system_prompt = """당신은 배터리 산업 전문가이고 국제적 시장 분석 경험이 풍부합니다.
당신의 역할:
1. 배터리 시장의 규모와 성장 추이를 분석
2. 주요 플레이어와 시장 점유율 파악
3. 기술 트렌드와 혁신 사항 식별
4. 경쟁 구도 분석
5. 시장 기회 포인트 발굴
6. 지역별 시장 특성 파악

분석은 데이터 기반의 정성적이고 전략적이어야 합니다.

반드시 다음의 JSON 형식으로 응답하세요:
{
  "market_size": "시장 규모와 성장률 정보",
  "key_players": ["회사1", "회사2", "회사3"],
  "technology_trends": "기술 트렌드 설명",
  "competitive_landscape": "경쟁 구도 분석",
  "market_opportunities": "시장 기회",
  "regional_analysis": "지역별 분석"
}"""

        user_prompt = f"""다음 검색 결과들을 종합하여 배터리 시장을 분석해주세요.
검색 결과가 제한적이더라도, 귀사의 전문 지식과 함께 최선의 분석을 제공해주세요:

[검색 결과]
{search_context}

[분석 요청]
다음 각 항목에 대해 상세히 분석하고, 각 항목마다 명확한 제목으로 구분하여 응답하세요:

1. **시장 규모와 성장률**: 배터리 시장의 현재 규모와 예상 성장률은?
2. **주요 시장 참여자**: 주요 배터리 제조사와 기업들은? (쉼표로 구분하여 나열)
3. **기술 트렌드**: 현재 진행 중인 기술 혁신과 트렌드는?
4. **경쟁 구도**: 시장의 경쟁 상황과 기업들의 전략은?
5. **시장 기회**: 배터리 시장에서 주목할만한 성장 기회는?
6. **지역별 분석**: 주요 시장(중국, 한국, 유럽, 북미)의 특성과 차이점은?

각 항목은 3-5문장이면 충분합니다. 구체적이고 전문적인 분석 부탁드립니다."""

        if not self.llm:
            # Placeholder response for testing
            return {
                "market_size": "2023년 기준 약 100조 원 규모로 추정되며, 연평균 15-20% 성장률 기록",
                "key_players": ["LG에너지솔루션", "CATL", "BYD", "Panasonic", "Samsung SDI"],
                "technology_trends": "고에너지 밀도, 빠른 충전, 안전성 향상 방향으로 진화. 고체배터리, 나트륨이온 배터리 등 차세대 기술 개발 활발",
                "competitive_landscape": "중국 기업의 수직 통합 전략과 한국/일본 기업의 기술 고도화로 양극화. CATL과 BYD의 중국 시장 장악력 증가",
                "market_opportunities": "전기차 시장 확대, 에너지 저장 시스템(ESS) 수요 증가, 차세대 배터리 기술 개발",
                "regional_analysis": "중국: 생산 능력 위주의 시장 확장 / 한국: 기술 고도화와 프리미엄 전략 / 유럽: 환경 규제 강화에 따른 니즈 증가",
                "references": ["검색 결과 1", "검색 결과 2"]
            }
        
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
        """Return placeholder analysis when LLM fails"""
        return {
            "market_size": "2023년 기준 약 100조 원 규모로 추정되며, 연평균 15-20% 성장률 기록",
            "key_players": ["LG에너지솔루션", "CATL", "BYD", "Panasonic", "Samsung SDI"],
            "technology_trends": "고에너지 밀도, 빠른 충전, 안전성 향상 방향으로 진화. 고체배터리, 나트륨이온 배터리 등 차세대 기술 개발 활발",
            "competitive_landscape": "중국 기업의 수직 통합 전략과 한국/일본 기업의 기술 고도화로 양극화",
            "market_opportunities": "전기차 시장 확대, ESS 수요 증가, 차세대 배터리 기술 개발",
            "regional_analysis": "중국: 생산 능력 위주 / 한국: 기술 고도화 / 유럽: 환경 규제 강화",
            "references": []
        }
