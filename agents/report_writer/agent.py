"""
Report Writer Agent - compiles final report from all agent outputs
"""
from typing import Dict, Any
from datetime import datetime
from agents.base import BaseAgent
from agents.report_writer.schema import ReportOutput


class ReportWriterAgent(BaseAgent):
    """Agent for composing the final comprehensive report"""
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="ReportWriterAgent", llm_client=llm_client, retriever=retriever)
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare all agent outputs for report compilation"""
        self.logger.info("Thinking phase: preparing report components...")
        
        return {
            "market_background": context.get("market_background", ""),
            "lg_strategy": context.get("lg_strategy", ""),
            "catl_strategy": context.get("catl_strategy", ""),
            "comparative_swot": context.get("comparative_swot", ""),
            "execution_id": context.get("execution_id", ""),
            "context": context
        }
    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to compose the final report components"""
        self.logger.info("Acting phase: composing final report sections...")
        
        # Placeholder components (in production, LLM would generate these)
        components = {
            "executive_summary": "본 보고서는 배터리 시장의 현황을 분석하고 LG에너지솔루션과 CATL의 경쟁 전략을 비교 분석한 결과물입니다.",
            "introduction": thought.get("market_background", ""),
            "lg_analysis": thought.get("lg_strategy", ""),
            "catl_analysis": thought.get("catl_strategy", ""),
            "comparative_swot": thought.get("comparative_swot", ""),
            "conclusion_and_recommendation": "배터리 시장에서 성공하기 위해서는 기술 혁신과 비용 경쟁력의 균형을 이루어야 합니다."
        }
        
        if not self.llm:
            return components
        
        # In real implementation, call LLM for report composition
        response = self.llm.invoke(
            system_prompt="전문 리포터로서 모든 분석 내용을 통합하여 체계적인 보고서를 작성하라",
            user_prompt=f"""
            다음 분석 결과들을 통합하여 종합적인 배터리 시장 전략 보고서의 각 섹션을 작성하시오:
            
            시장 분석: {thought['market_background']}
            LG 분석: {thought['lg_strategy']}
            CATL 분석: {thought['catl_strategy']}
            SWOT 분석: {thought['comparative_swot']}
            """
        )
        return response
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate the output as structured JSON"""
        self.logger.info("Output phase: formatting final report as JSON...")
        
        # Create ReportOutput schema object
        report_output = ReportOutput(
            executive_summary=action_result.get("executive_summary", ""),
            introduction=action_result.get("introduction", ""),
            lg_analysis=action_result.get("lg_analysis", ""),
            catl_analysis=action_result.get("catl_analysis", ""),
            comparative_swot=action_result.get("comparative_swot", ""),
            conclusion_and_recommendation=action_result.get("conclusion_and_recommendation", ""),
            references=[],
            metadata={
                "generated_at": datetime.now().isoformat(),
                "agent": "report_writer",
                "format": "json"
            }
        )
        
        return {
            "result": report_output.dict(),  # Convert to dict for JSON serialization
            "agent": "report_writer",
            "status": "completed",
            "format": "json"
        }
