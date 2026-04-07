#!/usr/bin/env python3
"""
Test context integration in MarketResearchAgent
Verifies that context is properly formatted and included in prompts
"""

import sys
sys.path.insert(0, '/Users/minhee/Documents/skala/ch21_Agent/Battery_analysis')

from agents.market_research.agent import MarketResearchAgent
from agents.market_research.prompts import MARKET_RESEARCH_USER_PROMPT_TEMPLATE


def test_context_formatting():
    """Test that context is properly formatted"""
    agent = MarketResearchAgent()
    
    # Test 1: Dict context
    print("=" * 60)
    print("TEST 1: Dict context formatting")
    print("=" * 60)
    context_dict = {
        'sector': '배터리 시장',
        'focus_area': '전기차 배터리 기술',
        'region': '아시아 태평양'
    }
    result = agent._format_context(context_dict)
    print("Input:", context_dict)
    print("\nFormatted output:")
    print(result)
    print()
    
    # Test 2: String context
    print("=" * 60)
    print("TEST 2: String context formatting")
    print("=" * 60)
    context_str = "전기차 배터리 시장의 성장 항목 분석"
    result = agent._format_context(context_str)
    print("Input:", context_str)
    print("Formatted output:", result)
    print()
    
    # Test 3: Empty context
    print("=" * 60)
    print("TEST 3: Empty context formatting")
    print("=" * 60)
    result = agent._format_context({})
    print("Input: {}")
    print("Formatted output:", result)
    print()
    
    # Test 4: Search results formatting
    print("=" * 60)
    print("TEST 4: Search results formatting")
    print("=" * 60)
    search_results = {
        "배터리 시장 규모": [
            {"content": "2023년 글로벌 배터리 시장 규모는 약 50조 원", "score": 0.95},
            {"content": "연평균 성장률 15-20%", "score": 0.90}
        ]
    }
    result = agent._format_search_results(search_results)
    print("Search results formatted:")
    print(result)
    print()
    
    # Test 5: Template formatting with context and search
    print("=" * 60)
    print("TEST 5: Template formatting with both placeholders")
    print("=" * 60)
    context_str = agent._format_context(context_dict)
    search_str = agent._format_search_results(search_results)
    
    try:
        user_prompt = MARKET_RESEARCH_USER_PROMPT_TEMPLATE.format(
            context=context_str,
            search_results=search_str
        )
        print("✓ Template formatting SUCCESS")
        print("\nGenerated prompt (first 400 chars):")
        print(user_prompt[:400])
        print("...")
    except Exception as e:
        print(f"✗ Template formatting FAILED: {e}")
        return False
    
    # Test 6: Verify context is included in prompt
    print("\n" + "=" * 60)
    print("TEST 6: Verify context inclusion in prompt")
    print("=" * 60)
    if "요청 배경" in user_prompt and context_str in user_prompt:
        print("✓ Context properly included in prompt")
    else:
        print("✗ Context NOT found in prompt")
        return False
    
    # Test 7: Verify search results are included in prompt
    print("\n" + "=" * 60)
    print("TEST 7: Verify search results inclusion in prompt")
    print("=" * 60)
    if "검색 결과" in user_prompt and "배터리 시장 규모" in user_prompt:
        print("✓ Search results properly included in prompt")
    else:
        print("✗ Search results NOT found in prompt")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_context_formatting()
    sys.exit(0 if success else 1)
