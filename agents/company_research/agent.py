"""Company Research Agent implementation."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import requests

from agents.base import BaseAgent
from agents.company_research.prompts import (
	SECTION_QUERIES,
	RETRY_HINT,
	COMPANY_SYSTEM_PROMPT,
	build_company_user_prompt,
)
from agents.company_research.schema import (
	CompanyResearchOutput,
	CompanyResearchResult,
	CompanySectionResult,
	SourceItem,
)
from config.settings import config


class CompanyResearchAgent(BaseAgent):
	"""Research LGES and CATL using vector DB + Tavily web search."""

	COMPANIES = {
		"lg_strategy": "LG에너지솔루션",
		"catl_strategy": "CATL",
	}
	COMPANY_ALIASES = {
		"LG에너지솔루션": ["LG에너지솔루션", "LG엔솔", "LG Energy Solution", "LGES"],
		"CATL": ["CATL", "닝더스다이", "Contemporary Amperex"],
	}

	def __init__(self, llm_client=None, retriever=None):
		super().__init__(name="CompanyResearchAgent", llm_client=llm_client, retriever=retriever)
		self.vector_top_k = config.max_search_results
		self.web_top_k = 5
		self.max_search_rounds = 2
		self.min_section_score = 0.45
		self.min_evidence_count = 2
		self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")

	def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
		"""Search evidence for each company/section and retry weak sections."""
		company_evidence: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

		for company_key, company_name in self.COMPANIES.items():
			section_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

			for section, template in SECTION_QUERIES.items():
				base_query = template.format(company=company_name)
				combined_results: List[Dict[str, Any]] = []

				for round_idx in range(self.max_search_rounds):
					query = self._build_round_query(base_query, round_idx)
					combined_results.extend(self._search_vector(query))
					combined_results.extend(self._search_web(query))

					deduped = self._dedupe_results(combined_results)
					deduped = self._filter_evidence_for_company(company_name, deduped)
					score = self._evaluate_evidence(deduped)

					if score >= self.min_section_score and len(deduped) >= self.min_evidence_count:
						section_results[section] = deduped
						break

					if round_idx == self.max_search_rounds - 1:
						section_results[section] = deduped

			company_evidence[company_key] = section_results

		return {
			"company_evidence": company_evidence,
			"context": context,
		}

	def act(self, thought: Dict[str, Any]) -> CompanyResearchOutput:
		"""Summarize evidence into schema-aligned structured output via LLM."""
		company_results: Dict[str, CompanyResearchResult] = {}

		for company_key, company_name in self.COMPANIES.items():
			section_evidence = thought["company_evidence"][company_key]
			evidence_text = self._format_evidence_for_llm(section_evidence)

			llm_json = self.call_llm(
				system_prompt=COMPANY_SYSTEM_PROMPT,
				user_prompt=build_company_user_prompt(company_name, evidence_text),
				temperature=0.2,
				max_tokens=1500,
				use_json_mode=True,
			)

			section_result = CompanySectionResult(**llm_json)
			section_result = self._enforce_minimum_detail(company_name, section_result, section_evidence)
			sources = self._build_sources(section_evidence)
			company_results[company_key] = CompanyResearchResult(
				company_name=company_name,
				response=section_result,
				sources=sources,
			)

		return CompanyResearchOutput(
			lg_strategy=company_results["lg_strategy"],
			catl_strategy=company_results["catl_strategy"],
		)

	def output(self, action_result: CompanyResearchOutput) -> Dict[str, Any]:
		"""Return markdown strings for supervisor handoff with source list."""
		lg_md = self._to_markdown(action_result.lg_strategy)
		catl_md = self._to_markdown(action_result.catl_strategy)

		return {
			"lg_result": lg_md,
			"catl_result": catl_md,
			"agent": "company_research",
			"status": "completed",
		}

	def run_single_company(self, company_name: str) -> str:
		"""Run full pipeline for one company and return markdown only."""
		normalized = self._normalize_company_name(company_name)
		if normalized is None:
			raise ValueError("Unsupported company. Use 'LG에너지솔루션' or 'CATL'.")

		section_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
		for section, template in SECTION_QUERIES.items():
			base_query = template.format(company=normalized)
			combined_results: List[Dict[str, Any]] = []

			for round_idx in range(self.max_search_rounds):
				query = self._build_round_query(base_query, round_idx)
				combined_results.extend(self._search_vector(query))
				combined_results.extend(self._search_web(query))

				deduped = self._dedupe_results(combined_results)
				deduped = self._filter_evidence_for_company(normalized, deduped)
				score = self._evaluate_evidence(deduped)

				if score >= self.min_section_score and len(deduped) >= self.min_evidence_count:
					section_results[section] = deduped
					break

				if round_idx == self.max_search_rounds - 1:
					section_results[section] = deduped

		evidence_text = self._format_evidence_for_llm(section_results)
		llm_json = self.call_llm(
			system_prompt=COMPANY_SYSTEM_PROMPT,
			user_prompt=build_company_user_prompt(normalized, evidence_text),
			temperature=0.2,
			max_tokens=1500,
			use_json_mode=True,
		)

		section_result = CompanySectionResult(**llm_json)
		section_result = self._enforce_minimum_detail(normalized, section_result, section_results)
		result = CompanyResearchResult(
			company_name=normalized,
			response=section_result,
			sources=self._build_sources(section_results),
		)
		return self._to_markdown(result)

	def _normalize_company_name(self, company_name: str) -> str | None:
		"""Normalize user-provided company string to supported canonical name."""
		name = (company_name or "").strip()
		for canonical, aliases in self.COMPANY_ALIASES.items():
			if name == canonical:
				return canonical
			if any(name.lower() == a.lower() for a in aliases):
				return canonical
		return None

	def _build_round_query(self, base_query: str, round_idx: int) -> str:
		if round_idx == 0:
			return base_query
		return f"{base_query} {RETRY_HINT}"

	def _search_vector(self, query: str) -> List[Dict[str, Any]]:
		if not self.retriever:
			return []
		try:
			results = self.retriever.search(query, top_k=self.vector_top_k)
		except Exception:
			return []

		normalized = []
		for item in results:
			normalized.append(
				{
					"title": item.get("metadata", {}).get("file_name", item.get("source", "vector_result")),
					"url": item.get("source", ""),
					"content": item.get("content", ""),
					"score": float(item.get("score", 0.0)),
					"source_type": self._infer_source_type(item.get("source", "")),
				}
			)
		return normalized

	def _search_web(self, query: str) -> List[Dict[str, Any]]:
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
		except Exception:
			return []

		normalized = []
		for item in results:
			normalized.append(
				{
					"title": item.get("title", "web_result"),
					"url": item.get("url", ""),
					"content": item.get("content", ""),
					"score": float(item.get("score", 0.0)),
					"source_type": self._infer_source_type(item.get("url", "")),
				}
			)
		return normalized

	def _dedupe_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		deduped: Dict[Tuple[str, str], Dict[str, Any]] = {}
		for item in results:
			key = (item.get("url", ""), item.get("title", ""))
			if key not in deduped or item.get("score", 0.0) > deduped[key].get("score", 0.0):
				deduped[key] = item
		ranked = sorted(deduped.values(), key=lambda x: x.get("score", 0.0), reverse=True)
		return ranked[:8]

	def _filter_evidence_for_company(self, company_name: str, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		"""Exclude evidence clearly centered on the other company."""
		target_aliases = [a.lower() for a in self.COMPANY_ALIASES.get(company_name, [company_name])]
		other_aliases = []
		for name, aliases in self.COMPANY_ALIASES.items():
			if name != company_name:
				other_aliases.extend([a.lower() for a in aliases])

		filtered: List[Dict[str, Any]] = []
		for item in evidence:
			blob = " ".join(
				[
					str(item.get("title", "")),
					str(item.get("content", "")),
					str(item.get("url", "")),
				]
			).lower()

			has_target = any(alias in blob for alias in target_aliases)
			has_other = any(alias in blob for alias in other_aliases)

			# Keep evidence if target is present, or if it is neutral (no explicit other-company signal).
			if has_target or not has_other:
				filtered.append(item)

		return filtered

	def _evaluate_evidence(self, evidence: List[Dict[str, Any]]) -> float:
		if not evidence:
			return 0.0
		top_scores = [item.get("score", 0.0) for item in evidence[:3]]
		avg_score = sum(top_scores) / max(len(top_scores), 1)
		diversity_bonus = min(len({item.get("url", "") for item in evidence if item.get("url")}) / 5.0, 0.2)
		return avg_score + diversity_bonus

	def _infer_source_type(self, source: str) -> str:
		lowered = source.lower()
		if "sustainability" in lowered or "esg" in lowered or "annual" in lowered:
			return "company_report"
		if "gov" in lowered or "policy" in lowered:
			return "policy_document"
		if "research" in lowered or "report" in lowered or source.endswith(".pdf"):
			return "research_report"
		if lowered.startswith("http"):
			return "news"
		return "other"

	def _format_evidence_for_llm(self, section_evidence: Dict[str, List[Dict[str, Any]]]) -> str:
		lines: List[str] = []
		for section, query_template in SECTION_QUERIES.items():
			section_title = query_template.replace("{company}", "").strip()
			lines.append(f"\n## {section_title}")
			for idx, item in enumerate(section_evidence.get(section, [])[:5], start=1):
				snippet = " ".join(item.get("content", "").split())[:300]
				lines.append(
					f"{idx}. ({item.get('score', 0.0):.2f}) {snippet} [source={item.get('url', '')}]"
				)
		return "\n".join(lines) if lines else "(근거 없음)"

	def _build_sources(self, section_evidence: Dict[str, List[Dict[str, Any]]]) -> List[SourceItem]:
		source_map: Dict[str, SourceItem] = {}
		for items in section_evidence.values():
			for item in items:
				url = item.get("url", "")
				if not url:
					continue
				if url not in source_map:
					source_map[url] = SourceItem(
						title=item.get("title", "source"),
						url=url,
						source_type=item.get("source_type", "other"),
					)
		return list(source_map.values())[:10]

	def _enforce_minimum_detail(
		self,
		company_name: str,
		section_result: CompanySectionResult,
		section_evidence: Dict[str, List[Dict[str, Any]]],
	) -> CompanySectionResult:
		"""Ensure each section has at least 3 sentences and mentions the target company."""
		return CompanySectionResult(
			portfolio_status=self._ensure_min_sentences(
				company_name,
				section_result.portfolio_status,
				section_evidence.get("portfolio_status", []),
			),
			market_response_strategy=self._ensure_min_sentences(
				company_name,
				section_result.market_response_strategy,
				section_evidence.get("market_response_strategy", []),
			),
			diversification_strategy=self._ensure_min_sentences(
				company_name,
				section_result.diversification_strategy,
				section_evidence.get("diversification_strategy", []),
			),
			core_competency=self._ensure_min_sentences(
				company_name,
				section_result.core_competency,
				section_evidence.get("core_competency", []),
			),
			profitability_strategy=self._ensure_min_sentences(
				company_name,
				section_result.profitability_strategy,
				section_evidence.get("profitability_strategy", []),
			),
			risks_and_challenges=self._ensure_min_sentences(
				company_name,
				section_result.risks_and_challenges,
				section_evidence.get("risks_and_challenges", []),
			),
		)

	def _ensure_min_sentences(
		self,
		company_name: str,
		text: str,
		evidence: List[Dict[str, Any]],
		min_sentences: int = 3,
	) -> str:
		"""Normalize section text to contain at least min_sentences and target company mention."""
		sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]

		if not sentences:
			sentences = [f"{company_name}의 전략 관점에서 핵심 쟁점을 요약합니다."]

		# Force company-name consistency in the lead sentence.
		if not self._contains_company_alias(company_name, sentences[0]):
			sentences[0] = f"{company_name}은 {sentences[0]}"

		idx = 0
		while len(sentences) < min_sentences and idx < len(evidence):
			snippet = " ".join(evidence[idx].get("content", "").split())[:140]
			if snippet:
				sentences.append(f"근거 기준으로 보면 {company_name} 관련 포인트는 다음과 같습니다: {snippet}.")
			idx += 1

		while len(sentences) < min_sentences:
			sentences.append(f"추가 데이터 확보 시 {company_name} 관점에서 정밀 보완이 필요합니다.")

		return "\n".join(sentences[: max(min_sentences, len(sentences))])

	def _contains_company_alias(self, company_name: str, text: str) -> bool:
		lowered = text.lower()
		for alias in self.COMPANY_ALIASES.get(company_name, [company_name]):
			if alias.lower() in lowered:
				return True
		return False

	def _to_markdown(self, result: CompanyResearchResult) -> str:
		r = result.response
		lines = [
			f"# {result.company_name} 전략 분석",
			"",
			"## 1) 현재 사업 포트폴리오 현황 (제품·고객·지역)",
			r.portfolio_status,
			"",
			"## 2) 시장 환경 변화 대응 전략 (EV 캐즘 대응 포함)",
			r.market_response_strategy,
			"",
			"## 3) 다각화 전략 방향",
			r.diversification_strategy,
			"",
			"## 4) 핵심 경쟁력",
			r.core_competency,
			"",
			"## 5) 수익성 구조 및 전략",
			r.profitability_strategy,
			"",
			"## 6) 주요 리스크 및 과제",
			r.risks_and_challenges,
			"",
			"## Sources",
		]

		if result.sources:
			for src in result.sources:
				lines.append(f"- {src.title} ({src.source_type}): {src.url}")
		else:
			lines.append("- 출처 없음")

		return "\n".join(lines).strip()

