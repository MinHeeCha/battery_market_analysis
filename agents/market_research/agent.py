"""
Market Research Agent - External Environment Analysis Engine

역할: 글로벌 EV 시장 캐즘, 배터리 수요 구조 변화, 정책/관세, 공급망, 기술/경쟁 구도 분석
LG에너지솔루션과 CATL의 공통 외부 환경 분석으로 SWOT 도출용 근거 제공

Architecture: think()→검색(RAG+Web) → act()→생성+평가+개선 → output()→메타데이터 포함
"""

import json
import re
import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from agents.base import BaseAgent
from pydantic import BaseModel, Field
from config.settings import config
from agents.market_research.prompts import (
    MARKET_RESEARCH_SYSTEM_PROMPT,
    MARKET_RESEARCH_USER_PROMPT_TEMPLATE,
    MARKET_RESEARCH_EVALUATION_PROMPT_TEMPLATE,
    MARKET_RESEARCH_REVISION_PROMPT_TEMPLATE
)


class MarketResearchEvaluation(BaseModel):
    """평가 결과"""
    external_relevance_score: int
    environment_centrality_score: int
    key_topics_score: int
    pass_evaluation: bool
    included_topics: List[str] = Field(default_factory=list)
    missing_topics: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    feedback: str = ""


class MarketResearchOutput(BaseModel):
    """최종 출력"""
    final_answer: str
    external_relevance_score: int = 0
    pass_evaluation: bool = False
    revision_count: int = 0
    included_topics: List[str] = Field(default_factory=list)
    missing_topics: List[str] = Field(default_factory=list)
    evaluation_details: Optional[Dict[str, Any]] = None


class MarketResearchAgent(BaseAgent):
    """외부 환경 분석 에이전트 (RAG + Web Search)"""
    
    EVALUATION_SCORE_THRESHOLD = 80
    MAX_REVISIONS = 2
    
    def __init__(self, llm_client=None, retriever=None):
        super().__init__(name="MarketResearchAgent", llm_client=llm_client, retriever=retriever)
        self.revision_count = 0
        self.vector_top_k = config.max_search_results
        self.web_top_k = 5
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """검색 (Vector DB + Web 통합)"""
        self.logger.info("Thinking: Searching market documents (RAG + Web)...")
        
        queries = [
            "글로벌 EV 시장 캐즘 보조금 감소",
            "배터리 수요 구조 변화 가격 압력",
            "배터리 관세 정책 규제",
            "배터리 공급망 원자재 물류",
            "차세대 배터리 기술 경쟁"
        ]
        
        all_combined_results = []
        
        for query in queries:
            combined_results = []
            
            vector_results = self._search_vector(query)
            combined_results.extend(vector_results)
            self.logger.info("Vector search - {}: {} results".format(query, len(vector_results)))
            
            web_results = self._search_web(query)
            combined_results.extend(web_results)
            self.logger.info("Web search - {}: {} results".format(query, len(web_results)))
            
            deduped = self._dedupe_results(combined_results)
            all_combined_results.extend(deduped)
            self.logger.info("Combined - {}: {} unique results".format(query, len(deduped)))
        
        final_results = self._dedupe_results(all_combined_results)[:15]
        self.logger.info("Final results: {} items from all searches".format(len(final_results)))
        
        return {
            "queries": queries,
            "search_results": final_results,
            "context": context
        }
    
    def _search_vector(self, query: str) -> List[Dict[str, Any]]:
        """Vector DB 검색"""
        if not self.retriever:
            return []
        try:
            results = self.retriever.search(query, top_k=self.vector_top_k)
        except Exception as e:
            self.logger.error("Vector search error: {}".format(e))
            return []
        
        normalized = []
        for item in results:
            normalized.append({
                "title": item.get("metadata", {}).get("file_name", item.get("source", "vector_result")),
                "url": item.get("source", ""),
                "content": item.get("content", ""),
                "score": float(item.get("score", 0.0)),
                "source_type": "vector_db"
            })
        return normalized
    
    def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Web 검색 (Tavily API)"""
        if not self.tavily_api_key:
            return []
        
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": self.web_top_k,
        }
        
        try:
            response = requests.post("https://api.tavily.com/search", json=payload, timeout=20)
            response.raise_for_status()
            results = response.json().get("results", [])
        except Exception as e:
            self.logger.debug("Web search error: {}".format(e))
            return []
        
        normalized = []
        for item in results:
            normalized.append({
                "title": item.get("title", "web_result"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": float(item.get("score", 0.0)),
                "source_type": "web"
            })
        return normalized
    
    def _dedupe_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """결과 중복 제거 및 점수로 정렬"""
        deduped = {}
        for item in results:
            key = (item.get("url", ""), item.get("title", ""))
            if key not in deduped or item.get("score", 0.0) > deduped[key].get("score", 0.0):
                deduped[key] = item
        
        ranked = sorted(deduped.values(), key=lambda x: x.get("score", 0.0), reverse=True)
        return ranked
    
    def act(self, thought: Dict[str, Any]) -> Dict[str, Any]:
        """생성→평가→개선 사이클"""
        self.logger.info("Acting: Generating market analysis with evaluation cycle...")
        
        context = thought.get("context", {})
        context_str = self._format_context(context)
        search_context = self._format_search_results(thought.get("search_results", {}))
        
        # 1. Draft
        draft = self._generate_initial_draft(context_str, search_context)
        self.logger.info("Generated initial draft")
        
        # 2. Evaluate
        evaluation = self._evaluate_analysis(draft)
        self.logger.info(f"Evaluation: {evaluation.external_relevance_score}/100 (Pass: {evaluation.pass_evaluation})")
        
        # 3. Revise if needed
        final_result = draft
        self.revision_count = 0
        
        while not evaluation.pass_evaluation and self.revision_count < self.MAX_REVISIONS:
            self.logger.info(f"Revision cycle {self.revision_count + 1}")
            final_result = self._revise_analysis(original=final_result, evaluation=evaluation)
            evaluation = self._evaluate_analysis(final_result)
            self.revision_count += 1
            self.logger.info(f"After revision {self.revision_count}: {evaluation.external_relevance_score}/100")
        
        return {
            "analysis": final_result,
            "evaluation": evaluation,
            "revision_count": self.revision_count
        }
    
    def output(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 구조화"""
        self.logger.info("Output: Preparing final result with metadata...")
        
        analysis = action_result.get("analysis", "")
        evaluation = action_result.get("evaluation")
        revision_count = action_result.get("revision_count", 0)
        
        output = MarketResearchOutput(
            final_answer=analysis,
            external_relevance_score=evaluation.external_relevance_score if evaluation else 0,
            pass_evaluation=evaluation.pass_evaluation if evaluation else False,
            revision_count=revision_count,
            included_topics=evaluation.included_topics if evaluation else [],
            missing_topics=evaluation.missing_topics if evaluation else [],
            evaluation_details={
                "environment_centrality_score": evaluation.environment_centrality_score if evaluation else 0,
                "key_topics_score": evaluation.key_topics_score if evaluation else 0,
                "improvements": evaluation.improvements if evaluation else [],
                "feedback": evaluation.feedback if evaluation else ""
            }
        )
        
        self.logger.info(f"Output prepared: Score {output.external_relevance_score}/100, Pass: {output.pass_evaluation}")
        return output.dict()
    
    def _generate_initial_draft(self, context_str: str, search_context: str) -> str:
        """초안 생성"""
        if not self.llm:
            return self._get_placeholder_analysis()
        
        system_prompt = MARKET_RESEARCH_SYSTEM_PROMPT
        user_prompt = MARKET_RESEARCH_USER_PROMPT_TEMPLATE.format(
            context=context_str,
            search_results=search_context
        )
        
        try:
            response = self.llm.invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2500
            )
            return response
        except Exception as e:
            self.logger.error(f"Draft generation failed: {e}")
            return self._get_placeholder_analysis()
    
    def _revise_analysis(self, original: str, evaluation: MarketResearchEvaluation) -> str:
        """개선"""
        if not self.llm:
            return original
        
        improvements_str = "\n".join(f"- {imp}" for imp in evaluation.improvements) if evaluation.improvements else "없음"
        missing_str = ", ".join(evaluation.missing_topics) if evaluation.missing_topics else "없음"
        
        # 중괄호 이스케이프
        safe_original = original.replace("{", "{{").replace("}", "}}")
        
        revision_prompt = MARKET_RESEARCH_REVISION_PROMPT_TEMPLATE.format(
            original_analysis=safe_original,
            score=evaluation.external_relevance_score,
            env_score=evaluation.environment_centrality_score,
            topics_score=evaluation.key_topics_score,
            missing_topics=missing_str,
            improvements=improvements_str
        )
        
        try:
            response = self.llm.invoke(
                system_prompt=MARKET_RESEARCH_SYSTEM_PROMPT,
                user_prompt=revision_prompt,
                temperature=0.7,
                max_tokens=2500
            )
            return response
        except Exception as e:
            self.logger.error(f"Revision failed: {e}")
            return original
    
    def _evaluate_analysis(self, analysis: str) -> MarketResearchEvaluation:
        """평가"""
        if not self.llm:
            return self._get_placeholder_evaluation()
        
        eval_prompt = MARKET_RESEARCH_EVALUATION_PROMPT_TEMPLATE.replace("{analysis}", analysis)
        
        try:
            response = self.llm.invoke(
                system_prompt="당신은 공정한 평가자입니다.",
                user_prompt=eval_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            return self._parse_evaluation_text(response)
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return self._get_placeholder_evaluation()
    
    def _parse_evaluation_json(self, response: Any) -> MarketResearchEvaluation:
        """JSON 파싱"""
        try:
            if isinstance(response, dict):
                data = response
            else:
                data = json.loads(str(response))
            
            score = int(data.get("external_relevance_score", 0))
            env_score = int(data.get("environment_centrality_score", 0))
            topics_score = int(data.get("key_topics_score", 0))
            
            topic_details = data.get("topic_details", {})
            included = [k.replace("_", " ") for k, v in topic_details.items() if v.get("included", False)]
            missing = [k.replace("_", " ") for k, v in topic_details.items() if not v.get("included", False)]
            
            improvements = data.get("improvements", [])[:3]
            feedback = data.get("environment_feedback", "")
            
            return MarketResearchEvaluation(
                external_relevance_score=min(max(score, 0), 100),
                environment_centrality_score=min(max(env_score, 0), 50),
                key_topics_score=min(max(topics_score, 0), 50),
                pass_evaluation=score >= self.EVALUATION_SCORE_THRESHOLD,
                included_topics=included,
                missing_topics=missing,
                improvements=improvements,
                feedback=feedback
            )
        except Exception as e:
            self.logger.warning(f"JSON parsing failed: {e}")
            return self._get_placeholder_evaluation()
    
    def _parse_evaluation_text(self, response: str) -> MarketResearchEvaluation:
        """텍스트 파싱 (새로운 형식)"""
        try:
            # 1. JSON이 포함되어 있으면 먼저 시도
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    return self._parse_evaluation_json(data)
                except:
                    pass
            
            # 2. 새로운 텍스트 형식 파싱
            response_lower = response.lower()
            
            # 총점 추출
            score_match = re.search(r'총점:\s*(\d+)', response)
            score = int(score_match.group(1)) if score_match else 0
            
            # 환경점수, 항목점수 추출
            env_score_match = re.search(r'외부환경점수:\s*(\d+)', response)
            env_score = int(env_score_match.group(1)) if env_score_match else score // 2
            
            topics_score_match = re.search(r'항목점수:\s*(\d+)', response)
            topics_score = int(topics_score_match.group(1)) if topics_score_match else score // 2
            
            # 항목별 포함 여부 확인
            included_topics = []
            all_topics = [
                ("EV 시장 캐즘", ["EV캐즘", "ev_chasm", "캐즘"]),
                ("배터리 수요 구조 변화", ["배터리수요", "demand_change", "배터리 수요"]),
                ("정책 및 관세", ["정책관세", "policy_tariff", "정책", "관세"]),
                ("공급망 이슈", ["공급망", "supply", "공급"]),
                ("기술 및 경쟁 구도", ["기술경쟁", "tech_competition", "기술", "경쟁"])
            ]
            
            for topic_name, keywords in all_topics:
                # 먼저 "항목: yes" 형식으로 확인
                for keyword in keywords:
                    if re.search(rf'{keyword}:.*yes', response_lower):
                        included_topics.append(topic_name)
                        break
                else:
                    # "yes" 형식이 없으면 단순 존재 여부로 확인
                    for keyword in keywords:
                        if keyword in response_lower:
                            included_topics.append(topic_name)
                            break
            
            # 누락된 항목
            all_topic_names = [t[0] for t in all_topics]
            missing_topics = [t for t in all_topic_names if t not in included_topics]
            
            # 개선사항 추출
            improvements = []
            improvement_lines = response.split('\n')
            for line in improvement_lines:
                if '개선' in line or '피드백' in line:
                    clean_line = line.replace('개선', '').replace('피드백', '').replace(':', '').strip()
                    if clean_line and len(clean_line) > 5:
                        improvements.append(clean_line[:100])
                if len(improvements) >= 3:
                    break
            
            return MarketResearchEvaluation(
                external_relevance_score=min(score, 100),
                environment_centrality_score=min(env_score, 50),
                key_topics_score=min(topics_score, 50),
                pass_evaluation=score >= self.EVALUATION_SCORE_THRESHOLD,
                included_topics=included_topics,
                missing_topics=missing_topics,
                improvements=improvements,
                feedback=response[:300]
            )
        except Exception as e:
            self.logger.warning(f"Text parsing failed: {e}")
            return self._get_placeholder_evaluation()
    
    def _format_context(self, context: Any) -> str:
        """Context 포맷팅"""
        if not context:
            return "(요청 배경 정보 없음)"
        
        if isinstance(context, str):
            return context
        
        if isinstance(context, dict):
            lines = []
            for key, value in context.items():
                if isinstance(value, (list, dict)):
                    lines.append(f"• {key}: {str(value)[:200]}")
                else:
                    lines.append(f"• {key}: {value}")
            return "\n".join(lines) if lines else "(요청 배경 정보 없음)"
        
        if isinstance(context, list):
            lines = [f"• {str(item)[:200]}" for item in context]
            return "\n".join(lines) if lines else "(요청 배경 정보 없음)"
        
        try:
            return str(context)[:500]
        except Exception as e:
            self.logger.warning(f"Context formatting failed: {e}")
            return "(요청 배경 정보 포맷팅 실패)"
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과 포맷팅 (Vector DB + Web)"""
        if not search_results:
            return "(검색 결과 없음)"
        
        formatted = []
        for idx, item in enumerate(search_results[:5], start=1):
            title = item.get("title", "No title")
            content = item.get("content", "")[:300]
            source_type = item.get("source_type", "unknown")
            score = item.get("score", 0.0)
            formatted.append("[{}] {}\\n   {} (점수: {:.2f})".format(source_type, title, content, score))
        
        return "\\n\\n".join(formatted)
    
    def _get_placeholder_analysis(self) -> str:
        """Placeholder 분석"""
        return """This is the placeholder..."""
    
    def _get_placeholder_evaluation(self) -> MarketResearchEvaluation:
        """Placeholder 평가"""
        return MarketResearchEvaluation(
            external_relevance_score=70,
            environment_centrality_score=35,
            key_topics_score=35,
            pass_evaluation=False,
            included_topics=["EV 시장 캐즘", "배터리 수요 구조 변화", "정책 및 관세", "공supply망 이슈", "기술 및 경쟁 구도"],
            missing_topics=[],
            improvements=[],
            feedback="기본 외부 환경 요소를 포함하고 있으나, 더 심층적인 분석이 필요합니다."
        )
    

