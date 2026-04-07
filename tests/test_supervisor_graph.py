"""
Integration tests for the LangGraph-based SupervisorAgent.

실행 명령어:
    cd /Users/yubin/playground/battery_market_analysis
    python -m pytest tests/test_supervisor_graph.py -v
"""

import os
import sys
import unittest
from pathlib import Path

# ── 프로젝트 루트를 sys.path에 추가 ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class TestSupervisorGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from retrieval.retriever import Retriever
        vector_store_path = ROOT / "data" / "vector_store"
        cls.retriever = Retriever(vector_store_path=str(vector_store_path))

        info = cls.retriever.get_embedder_info()
        if not info.get("vector_store_ready", False):
            raise unittest.SkipTest("Vector store not ready. Run ingestion first.")
        if info.get("collection_count", 0) == 0:
            raise unittest.SkipTest("Vector store empty. Run scripts/ingest_documents.py first.")

        if not os.getenv("OPENAI_API_KEY"):
            raise unittest.SkipTest("OPENAI_API_KEY not set.")

    # ── Graph 빌드 ────────────────────────────────────────────────────────

    def test_build_graph_no_error(self):
        """그래프가 오류 없이 컴파일되어야 한다."""
        from agents.supervisor.agent import build_graph
        graph = build_graph(retriever=self.retriever)
        self.assertIsNotNone(graph)

    # ── 개별 에이전트 출력 형식 ───────────────────────────────────────────

    def test_market_research_returns_markdown(self):
        """MarketResearchAgent.run() 이 result 키와 마크다운 문자열을 반환해야 한다."""
        from agents.market_research.agent import MarketResearchAgent
        agent = MarketResearchAgent(retriever=self.retriever)
        result = agent.run({})
        self.assertIn("result", result)
        self.assertIsInstance(result["result"], str)
        self.assertGreater(len(result["result"]), 100)

    def test_company_research_returns_markdown(self):
        """CompanyResearchAgent.run() 이 lg_result/catl_result 마크다운을 반환해야 한다."""
        from agents.company_research.agent import CompanyResearchAgent
        agent = CompanyResearchAgent(retriever=self.retriever)
        result = agent.run({})
        self.assertIn("lg_result", result)
        self.assertIn("catl_result", result)
        self.assertIn("# LG에너지솔루션 전략 분석", result["lg_result"])
        self.assertIn("# CATL 전략 분석", result["catl_result"])

    def test_swot_returns_markdown(self):
        """SWOTAnalysisAgent.run() 이 result 키와 마크다운 문자열을 반환해야 한다."""
        from agents.swot_analysis.agent import SWOTAnalysisAgent
        agent = SWOTAnalysisAgent()
        result = agent.run({
            "market_background": "글로벌 EV 시장 캐즘 진행 중.",
            "lg_strategy": "LG에너지솔루션 전략 분석 내용.",
            "catl_strategy": "CATL 전략 분석 내용.",
        })
        self.assertIn("result", result)
        self.assertIsInstance(result["result"], str)
        self.assertGreater(len(result["result"]), 100)

    def test_report_writer_returns_markdown(self):
        """ReportWriterAgent.run() 이 result 키와 마크다운 보고서를 반환해야 한다."""
        from agents.report_writer.agent import ReportWriterAgent
        agent = ReportWriterAgent()
        result = agent.run({
            "market_background": "배터리 시장 외부 환경 분석.",
            "lg_strategy": "LG에너지솔루션 전략.",
            "catl_strategy": "CATL 전략.",
            "comparative_swot": "SWOT 비교 분석.",
        })
        self.assertIn("result", result)
        md = result["result"]
        self.assertIn("# 배터리 시장 전략 비교 보고서", md)
        self.assertIn("## 1. SUMMARY", md)
        self.assertIn("## 6. 종합 시사점", md)

    # ── 전체 워크플로우 ───────────────────────────────────────────────────

    def test_full_workflow(self):
        """SupervisorAgent.run() 이 최종 마크다운 보고서를 반환해야 한다."""
        from agents.supervisor.agent import SupervisorAgent
        supervisor = SupervisorAgent(retriever=self.retriever)
        report = supervisor.run()

        # 출력 확인
        sys.stdout.write("\n\n========== FINAL REPORT ==========\n")
        sys.stdout.write(report[:3000])   # 앞 3000자만 출력
        sys.stdout.write("\n... (truncated)\n")
        sys.stdout.flush()

        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 500)
        self.assertIn("# 배터리 시장 전략 비교 보고서", report)
        self.assertIn("## 1. SUMMARY", report)


if __name__ == "__main__":
    unittest.main()
