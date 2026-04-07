"""
Integration tests for CATL strategy retrieval queries.

These tests validate that vector DB search returns top_k results for
predefined CATL strategy sub-questions.
"""
import sys
import unittest
from pathlib import Path

from retrieval.retriever import Retriever


class TestRetrieverCATLQueries(unittest.TestCase):
    """CATL query coverage tests against Chroma vector DB."""

    CATL_QUERIES = [
        "CATL 현재 사업 포트폴리오 현황 제품 고객 지역",
        "CATL 시장 환경 변화 대응 전략 EV 캐즘 대응",
        "CATL 다각화 전략 방향",
        "CATL 핵심 경쟁력",
        "CATL 수익성 구조 및 전략",
        "CATL 주요 리스크 및 과제",
    ]

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

    def test_catl_queries_return_top5_results(self):
        """Each CATL query should return exactly top_k=5 results."""
        for query in self.CATL_QUERIES:
            with self.subTest(query=query):
                results = self.retriever.search(query, top_k=5)

                self.assertEqual(len(results), 5)

                for item in results:
                    self.assertIn("content", item)
                    self.assertIn("source", item)
                    self.assertIn("score", item)
                    self.assertTrue(isinstance(item["content"], str))
                    self.assertTrue(isinstance(item["source"], str))
                    self.assertTrue(isinstance(item["score"], float))

    def test_print_catl_query_source_table(self):
        """Print source table with snippets so retrieved text is visible."""
        out = sys.__stdout__
        out.write("\nCATL Retrieval Source Table\n")
        out.write("| Query | Rank | Score | Source | Snippet |\n")
        out.write("|---|---:|---:|---|---|\n")

        total_rows = 0
        for query in self.CATL_QUERIES:
            results = self.retriever.search(query, top_k=5)
            for rank, item in enumerate(results, start=1):
                score = item.get("score", 0.0)
                source = item.get("source", "")
                content = item.get("content", "")
                snippet = " ".join(content.split())[:120]
                safe_query = query.replace("|", "\\|")
                safe_source = source.replace("|", "\\|")
                safe_snippet = snippet.replace("|", "\\|")
                out.write(
                    f"| {safe_query} | {rank} | {score:.4f} | {safe_source} | {safe_snippet} |\n"
                )
                total_rows += 1

        out.flush()
        self.assertGreater(total_rows, 0)


if __name__ == "__main__":
    unittest.main()
