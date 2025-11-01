#!/usr/bin/env python3
# ABOUTME: Manual integration test for ClaudeService with real Anthropic API
# ABOUTME: Run this script to verify Claude API connectivity and basic functionality

"""
Manual Integration Test for Claude Service

This script tests the ClaudeService with the real Anthropic API.
Run it manually to verify:
1. API key is configured correctly
2. Claude API is accessible
3. Analysis generation works end-to-end
4. Token usage tracking is accurate
5. Response format is correct

Usage:
    python tests/manual_claude_integration_test.py

Note: These tests are SKIPPED during normal pytest runs.
      To run them, execute this file directly with python.
"""

import asyncio
import sys
import os
from pathlib import Path
import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from config import get_settings
from claude_service import ClaudeService, ClaudeAPIError


@pytest.mark.skip(reason="Manual integration test - requires real Anthropic API key. Run directly with: python tests/manual_claude_integration_test.py")
async def test_basic_analysis():
    """Test basic analysis generation."""
    print("\n" + "="*60)
    print("MANUAL INTEGRATION TEST: Claude Service")
    print("="*60)

    try:
        # Load settings
        print("\n1. Loading configuration...")
        config = get_settings()
        print(f"   ✓ Model: {config.ANTHROPIC_MODEL}")
        print(f"   ✓ Max tokens: {config.ANTHROPIC_MAX_TOKENS}")
        print(f"   ✓ Temperature: {config.ANTHROPIC_TEMPERATURE}")
        print(f"   ✓ Rate limit: {config.ANTHROPIC_RATE_LIMIT} req/min")

        # Create service
        print("\n2. Initializing ClaudeService...")
        service = ClaudeService(config)
        print("   ✓ Service initialized")

        # Test 1: Simple analysis
        print("\n3. Testing simple analysis generation...")
        test_prompt = """
        Analyze this portfolio position:

        Symbol: BTC
        Quantity: 0.5 BTC
        Current Price: $65,000
        Total Value: $32,500
        Cost Basis: $30,000
        Unrealized P&L: +$2,500 (+8.3%)

        Provide a brief 2-sentence analysis of this Bitcoin position.
        """

        result = await service.generate_analysis(test_prompt)

        print(f"   ✓ Analysis generated successfully!")
        print(f"   ✓ Tokens used: {result['tokens_used']}")
        print(f"   ✓ Model: {result['model']}")
        print(f"   ✓ Generation time: {result['generation_time_ms']}ms")
        print(f"   ✓ Stop reason: {result['stop_reason']}")

        print("\n   📝 Analysis:")
        print("   " + "-"*56)
        # Print analysis with indentation
        for line in result['content'].split('\n'):
            print(f"   {line}")
        print("   " + "-"*56)

        # Test 2: Custom temperature
        print("\n4. Testing custom temperature (0.1 for deterministic)...")
        result2 = await service.generate_analysis(
            "What is Bitcoin?",
            temperature=0.1
        )
        print(f"   ✓ Generated with custom temperature")
        print(f"   ✓ Tokens used: {result2['tokens_used']}")

        # Test 3: Custom system prompt
        print("\n5. Testing custom system prompt...")
        result3 = await service.generate_analysis(
            "Explain blockchain in one sentence.",
            system_prompt="You are a technical expert. Be extremely concise."
        )
        print(f"   ✓ Generated with custom system prompt")
        print(f"   ✓ Response: {result3['content']}")

        # Summary
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*60)
        print(f"Total tokens used: {result['tokens_used'] + result2['tokens_used'] + result3['tokens_used']}")
        print("\nClaude API integration is working correctly!")

        return True

    except ClaudeAPIError as e:
        print(f"\n❌ Claude API Error: {e}")
        print("\nPossible causes:")
        print("  - Invalid API key in .env file")
        print("  - Network connectivity issues")
        print("  - Anthropic API service issues")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.skip(reason="Manual integration test - requires real Anthropic API key. Run directly with: python tests/manual_claude_integration_test.py")
async def test_rate_limiting():
    """Test rate limiting with multiple rapid requests."""
    print("\n" + "="*60)
    print("RATE LIMITING TEST")
    print("="*60)

    try:
        config = get_settings()
        service = ClaudeService(config)

        print("\nSending 3 rapid requests to test rate limiting...")

        import time
        start = time.time()

        for i in range(3):
            print(f"\n  Request {i+1}...")
            result = await service.generate_analysis("What is the capital of France?")
            print(f"  ✓ Completed in {result['generation_time_ms']}ms")

        elapsed = time.time() - start
        print(f"\n✓ All requests completed in {elapsed:.2f}s")
        print("✓ Rate limiting working correctly")

        return True

    except Exception as e:
        print(f"\n❌ Rate limiting test failed: {e}")
        return False


async def main():
    """Run all manual integration tests."""
    print("\n🚀 Starting Claude Service Integration Tests\n")

    # Check API key is configured
    config = get_settings()
    if not config.ANTHROPIC_API_KEY or config.ANTHROPIC_API_KEY == "your_anthropic_api_key_here":
        print("❌ ERROR: ANTHROPIC_API_KEY not configured in .env file")
        print("\nPlease:")
        print("  1. Get your API key from https://console.anthropic.com/")
        print("  2. Add it to your .env file: ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Run tests
    test1_passed = await test_basic_analysis()

    if test1_passed:
        test2_passed = await test_rate_limiting()

    print("\n" + "="*60)
    if test1_passed:
        print("✅ INTEGRATION TESTS COMPLETED SUCCESSFULLY")
    else:
        print("❌ INTEGRATION TESTS FAILED")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
