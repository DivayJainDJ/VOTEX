"""Quick live example of grammar correction"""
from grammar_processor_hybrid import HybridGrammarProcessor
import time

print("\n" + "="*70)
print("LIVE GRAMMAR CORRECTION EXAMPLES")
print("="*70 + "\n")

# Initialize
g = HybridGrammarProcessor()
print(f"Using: {'Hybrid (Model + Rules)' if g.model_available else 'Rules Only'}\n")

# Test cases
examples = [
    ("i could of done it", "Common mistake: 'of' instead of 'have'"),
    ("he dont like it", "Subject-verb agreement error"),
    ("this is a umbrella", "Wrong article before vowel"),
    ("i have a tomorrow match", "Word order error"),
    ("your going home", "Homophone error: your/you're"),
]

for text, description in examples:
    print(f"📝 {description}")
    print(f"   Input:  '{text}'")
    
    start = time.time()
    result = g.correct_text(text)
    elapsed = (time.time() - start) * 1000
    
    print(f"   Output: '{result}'")
    print(f"   Time:   {elapsed:.1f}ms")
    print()

print("="*70)
print("✓ Test complete!")
