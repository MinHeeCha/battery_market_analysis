"""
Company Research Agent - analyzes LG Energy Solution and CATL strategies
"""
from typing import Dict, Any
from agents.base import BaseAgent


class CompanyResearchAgent(BaseAgent):
    """Agent for analyzing company strategies (LG vs CATL)"""
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="CompanyResearchAgent", llm_client=llm_client, retriever=retriever)
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search and gather company information"""
        self.logger.info("Thinking phase: searching company documents...")
        
        lg_queries = [
            "LG에너지솔루션 전략",
            "LG에너지솔루션 기술",
            "LG배터리 경쟁력"
        ]
        
        catl_queries = [
            "CATL 전략",
            "CATL 기술",
            "CATL 시장 점유율"
        ]
        
        search_results = {"lg": {}, "catl": {}}
        
        if self.retriever:
            for query in lg_queries:
                search_results["lg"][query] = self.retriever.search(query, top_k=3)
            for query in catl_queries:
                search_results["catl"][query] = self.retriever.search(query, top_k=3)
        
        return {
            "lg_search_results": search_results["lg"],
            "catl_search_results": search_results["catl"],
            "context": context
        }
    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze company information"""
        self.logger.info("Acting phase: analyzing company data with LLM...")
        
        # Placeholder for testing
        lg_analysis = """
        LG에너지솔루션은 한국의 배터리 제조 선도 기업으로서:
        - 고에너지 밀도 기술 개발에 집중
        - 자동차 제조사와의 장기 공급 계약 확대
        - 프리미엄 시장 세그먼트 타겟
        """
        
        catl_analysis = """
        CATL은 중국의 배터리 시장 지배자로서:
        - 비용 경쟁력과 규모의 경제 추구
        - 수직 통합으로 생산 비용 최소화
        - 전 세계 시장에서 가장 큰 시장 점유율 보유
        """
        
        if not self.llm:
            return {
                "lg_result": lg_analysis,
                "catl_result": catl_analysis
            }
        
        # In real implementation, call LLM for each company
        lg_response = self.llm.invoke(
            system_prompt="LG에너지솔루션 전문 분석가",
            user_prompt=f"LG에너지솔루션의 전략과 경쟁력을 분석하시오: {thought['lg_search_results']}"
        )
        
        catl_response = self.llm.invoke(
            system_prompt="CATL 전문 분석가",
            user_prompt=f"CATL의 전략과 경쟁력을 분석하시오: {thought['catl_search_results']}"
        )
        
        return {
            "lg_result": lg_response,
            "catl_result": catl_response
        }
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output"""
        self.logger.info("Output phase: formatting company research results...")
        
        return {
            "lg_result": action_result.get("lg_result", ""),
            "catl_result": action_result.get("catl_result", ""),
            "agent": "company_research",
            "status": "completed"
        }
