#!/usr/bin/env python3
"""
LLM Connection Test Script
Tests if OpenAI API is properly configured and connected
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from shared.logger import get_logger
from shared.llm_client import LLMClient
from config.settings import config

logger = get_logger(__name__)


def test_llm_connection():
    """Test LLM connection and basic functionality"""
    print("=" * 60)
    print("LLM Connection Test")
    print("=" * 60)
    
    # Test 1: Check environment configuration
    print("\n[1] Checking environment configuration...")
    print(f"  - API Key configured: {'✓' if config.llm.api_key else '✗'}")
    print(f"  - Model: {config.llm.model}")
    print(f"  - Temperature: {config.llm.temperature}")
    print(f"  - Max tokens: {config.llm.max_tokens}")
    
    if not config.llm.api_key:
        print("\n❌ ERROR: OPENAI_API_KEY not set in .env file")
        return False
    
    # Test 2: Initialize LLM client
    print("\n[2] Initializing LLM client...")
    try:
        llm = LLMClient()
        print("  ✓ LLM client initialized successfully")
    except Exception as e:
        print(f"  ✗ Failed to initialize LLM client: {str(e)}")
        return False
    
    # Test 3: Test basic connection
    print("\n[3] Testing connection to OpenAI API...")
    try:
        result = llm.test_connection()
        if result:
            print("  ✓ Connection test PASSED")
        else:
            print("  ⚠ Connection test returned unexpected response")
    except Exception as e:
        print(f"  ✗ Connection test FAILED: {str(e)}")
        return False
    
    # Test 4: Test simple prompt
    print("\n[4] Testing LLM with simple prompt...")
    try:
        response = llm.invoke(
            system_prompt="You are a helpful assistant.",
            user_prompt="What is 2+2? Answer in one sentence only.",
            max_tokens=50
        )
        print(f"  ✓ Response received: {response}")
    except Exception as e:
        print(f"  ✗ Prompt test FAILED: {str(e)}")
        return False
    
    # Test 5: Test Korean language
    print("\n[5] Testing LLM with Korean prompt...")
    try:
        response = llm.invoke(
            system_prompt="당신은 전문 분석가입니다.",
            user_prompt="배터리 시장의 현재 트렌드를 한 문장으로 설명하세요.",
            max_tokens=100
        )
        print(f"  ✓ Korean response received: {response}")
    except Exception as e:
        print(f"  ✗ Korean prompt test FAILED: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - LLM is properly connected!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_llm_connection()
    sys.exit(0 if success else 1)
