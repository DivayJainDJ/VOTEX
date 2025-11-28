"""
Integration test for grammar correction in the server pipeline
Tests both rule-based and hybrid (model + rules) approaches
"""

import time

print("Testing Grammar Correction Integration\n")
print("="*70)

# Test 1: Rule-based only
print("\n1. Testing Rule-Based Grammar Processor")
print("-"*70)
from grammar_processor import GrammarProcessor

rule_based = GrammarProcessor()

test_cases = [
    "i have a tomorrow match",
    "he dont like it",
    "this is a umbrella",
    "i could of done it",
    "she have a car",
]

for text in test_cases:
    start = time.time()
    result = rule_based.correct_text(text)
    elapsed = time.time() - start
    print(f"Input:  '{text}'")
    print(f"Output: '{result}' ({elapsed*1000:.1f}ms)")
    print()

# Test 2: Hybrid (if available)
print("\n2. Testing Hybrid Grammar Processor (Model + Rules)")
print("-"*70)

try:
    from grammar_processor_hybrid import HybridGrammarProcessor
    
    hybrid = HybridGrammarProcessor(use_model=True)
    print(f"Stats: {hybrid.get_stats()}\n")
    
    for text in test_cases:
        start = time.time()
        result = hybrid.correct_text(text, timeout=1.0)
        elapsed = time.time() - start
        print(f"Input:  '{text}'")
        print(f"Output: '{result}' ({elapsed*1000:.1f}ms)")
        print()
    
except ImportError as e:
    print(f"⚠️ Hybrid processor not available: {e}")
except Exception as e:
    print(f"❌ Error testing hybrid: {e}")

print("="*70)
print("\n✓ Integration test complete!")
print("\nTo use in server:")
print("  - Rule-based: Already integrated (fast, ~1-5ms)")
print("  - Hybrid: Automatically used if transformers installed (~100-200ms)")
