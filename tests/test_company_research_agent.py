"""Integration tests for CompanyResearchAgent with real vector DB / web search."""

import os
import sys
import unittest
from pathlib import Path

from agents.company_research.agent import CompanyResearchAgent
from retrieval.retriever import Retriever


class TestCompanyResearchAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parent.parent
        vector_store_path = project_root / "data" / "vector_store"

        cls.retriever = Retriever(vector_store_path=str(vector_store_path))
        info = cls.retriever.get_embedder_info()

        if not info.get("vector_store_ready", False):
            raise unittest.SkipTest("Vector store is not ready. Run ingestion first.")

        if info.get("collection_count", 0) == 0:
            raise unittest.SkipTest("Vector store is empty. Run scripts/ingest_documents.py first.")

        cls.agent = CompanyResearchAgent(retriever=cls.retriever)

    def test_think_uses_real_vectordb(self):
        thought = self.agent.think({})
        evidence = thought.get("company_evidence", {})

        self.assertIn("lg_strategy", evidence)
        self.assertIn("catl_strategy", evidence)

        vector_sources = []
        for company_sections in evidence.values():
            for items in company_sections.values():
                for item in items:
                    src = item.get("url", "")
                    if src.startswith("data/") or src.endswith(".pdf"):
                        vector_sources.append(src)

        self.assertGreater(len(vector_sources), 0)

    def test_think_uses_web_search_when_tavily_key_exists(self):
        if not os.getenv("TAVILY_API_KEY"):
            raise unittest.SkipTest("TAVILY_API_KEY is not set")

        thought = self.agent.think({})
        evidence = thought.get("company_evidence", {})

        web_sources = []
        for company_sections in evidence.values():
            for items in company_sections.values():
                for item in items:
                    src = item.get("url", "")
                    if src.startswith("http"):
                        web_sources.append(src)

        self.assertGreater(len(web_sources), 0)

    def test_run_single_company_end_to_end(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise unittest.SkipTest("OPENAI_API_KEY is not set")

        md = self.agent.run_single_company("CATL")
        out = sys.__stdout__
        out.write("\n===== FINAL RESPONSE: CATL (REAL) =====\n")
        out.write(md + "\n")
        out.flush()

        self.assertIn("# CATL 전략 분석", md)
        self.assertIn("## Sources", md)


if __name__ == "__main__":
    unittest.main()
