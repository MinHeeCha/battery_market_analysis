#!/usr/bin/env python
"""간단한 에이전트 테스트"""
import sys
import os
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.market_research.agent import MarketResearchAgent

def test_agent_simple():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set in environment")

    print("=" * 60)
    print("MarketResearchAgent 테스트")
    print("=" * 60)

    agent = MarketResearchAgent()
    print("\n✓ Agent 초기화 완료")

    result = agent.run()
    print("\n✓ Agent 실행 완료")
    print("\n[결과]")
    print(f"상태: {'PASS' if result.get('passed') else 'FAIL'}")
    print(f"점수: {result.get('score', 'N/A')}/100")
    print(f"개정 횟수: {result.get('revision_count', 0)}")

    print(f"\n[토픽]")
    print(f"- 포함된 항목: {', '.join(result.get('included_topics', []))}")
    print(f"- 누락된 항목: {', '.join(result.get('missing_topics', []))}")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

    assert isinstance(result, dict)
    assert "passed" in result
    assert "score" in result


if __name__ == "__main__":
    test_agent_simple()
    sys.exit(0)
