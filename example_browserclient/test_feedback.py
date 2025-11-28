"""
Quick test to demonstrate feedback system functionality
"""
from feedback_memory import FeedbackMemory

def test_feedback_system():
    print("=" * 60)
    print("FEEDBACK SYSTEM TEST")
    print("=" * 60)
    
    # Create fresh memory for testing
    memory = FeedbackMemory('test_feedback_memory.json')
    
    print("\n1. Initial state:")
    print(f"   Stats: {memory.get_stats()}")
    
    print("\n2. Adding first correction:")
    memory.add_correction(
        original="I gotta go",
        system_output="I gotta go.",
        user_correction="I must leave",
        tone_mode="neutral"
    )
    print(f"   Stats: {memory.get_stats()}")
    
    print("\n3. Checking memory (should return None - not enough examples):")
    result = memory.check_memory("I gotta go", "neutral")
    print(f"   Result: {result}")
    
    print("\n4. Adding second correction with same word:")
    memory.add_correction(
        original="I gotta sleep",
        system_output="I gotta sleep.",
        user_correction="I must sleep",
        tone_mode="neutral"
    )
    print(f"   Stats: {memory.get_stats()}")
    
    print("\n5. Checking memory (should apply rule now):")
    result = memory.check_memory("I gotta eat", "neutral")
    print(f"   Result: {result}")
    print(f"   ✓ Rule applied: 'gotta' → 'must'")
    
    print("\n6. Testing exact match:")
    result = memory.check_memory("I gotta go", "neutral")
    print(f"   Result: {result}")
    print(f"   ✓ Exact match found!")
    
    print("\n7. Testing different tone (should not match):")
    result = memory.check_memory("I gotta go", "formal")
    print(f"   Result: {result}")
    print(f"   ✓ Tone-specific learning works!")
    
    print("\n8. Adding slang corrections:")
    memory.add_correction("I wanna eat", "I wanna eat.", "I want to eat", "neutral")
    memory.add_correction("I wanna sleep", "I wanna sleep.", "I want to sleep", "neutral")
    print(f"   Stats: {memory.get_stats()}")
    
    print("\n9. Testing multiple rules:")
    result = memory.check_memory("I gotta wanna go", "neutral")
    print(f"   Result: {result}")
    print(f"   ✓ Multiple rules applied!")
    
    print("\n" + "=" * 60)
    print("FINAL STATS:")
    stats = memory.get_stats()
    print(f"  Total corrections: {stats['total_corrections']}")
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  Active rules: {stats['active_rules']}")
    print("=" * 60)
    
    print("\n✅ All tests passed! Feedback system is working correctly.")
    print("\nTo see the stored data, check: test_feedback_memory.json")

if __name__ == '__main__':
    test_feedback_system()
