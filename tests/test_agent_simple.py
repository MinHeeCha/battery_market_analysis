#!/usr/bin/env python
"""간단한 에이전트 테스트"""
import sys
import os


# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.market_research.agent import MarketResearchAgent

try:
    print("=" * 60)
    print("MarketResearchAgent 테스트")
    print("=" * 60)
    
    agent = MarketResearchAgent()
    print("\n✓ Agent 초기화 완료")
    
    result = agent.run()
    print("\n✓ Agent 실행 완료")
    print("\n[결과]")
    print(f"상태: {'PASS' if result.get('pass_evaluation') else 'FAIL'}")
    print(f"점수: {result.get('external_relevance_score', 'N/A')}/100")
    print(f"개정 횟수: {result.get('revision_count', 0)}")
    
    if result.get('evaluation_details'):
        print("\n[평가 세부사항]")
        eval_details = result['evaluation_details']
        print(f"- 외부 환경 중심성: {eval_details.get('environment_centrality_score', 'N/A')}/50")
        print(f"- 항목 포함도: {eval_details.get('key_topics_score', 'N/A')}/50")
        print(f"- 개선사항: {eval_details.get('improvements', [])}")
    
    print(f"\n[토픽]")
    print(f"- 포함된 항목: {', '.join(result.get('included_topics', []))}")
    print(f"- 누락된 항목: {', '.join(result.get('missing_topics', []))}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 에러: {type(e).__name__}")
    print(f"  {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
