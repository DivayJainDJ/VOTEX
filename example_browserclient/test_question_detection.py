"""
Test question detection in paragraph detector
"""

from paragraph_detector import ParagraphDetector

print("="*70)
print("QUESTION DETECTION TEST")
print("="*70)
print()

detector = ParagraphDetector()

# Test cases - mix of questions and statements
test_cases = [
    # Clear questions
    ("what is your name", True),
    ("where are you going", True),
    ("when did you arrive", True),
    ("why did this happen", True),
    ("how does this work", True),
    ("who is responsible", True),
    
    # Questions with auxiliary verbs
    ("is this correct", True),
    ("are you ready", True),
    ("was it good", True),
    ("were they there", True),
    ("do you understand", True),
    ("does it work", True),
    ("did you see that", True),
    ("can you help me", True),
    ("could you explain", True),
    ("would you like coffee", True),
    ("should we start", True),
    ("will you come", True),
    
    # Questions from the user's example
    ("there should be question mark but it's not coming up", False),  # Statement
    ("what I'm trying to say is we should probably do a smaller cleaner release", False),  # Statement with "what"
    
    # Statements
    ("this is a statement", False),
    ("I think we should wait", False),
    ("the deadline was fine", False),
    ("everyone was confused", False),
    
    # Tricky cases
    ("I don't know what to do", False),  # "what" but not a question
    ("tell me what happened", False),  # Command, not question
    ("what a beautiful day", False),  # Exclamation
]

print("Testing question detection:\n")

correct = 0
total = len(test_cases)

for text, expected_is_question in test_cases:
    detected = detector.is_question(text)
    status = "✓" if detected == expected_is_question else "✗"
    
    if detected == expected_is_question:
        correct += 1
    
    print(f"{status} '{text}'")
    print(f"   Expected: {'Question' if expected_is_question else 'Statement'}")
    print(f"   Detected: {'Question' if detected else 'Statement'}")
    
    # Show formatted output
    formatted = detector.format_text_with_breaks(text, 'sentence')
    print(f"   Output: {repr(formatted)}")
    print()

print("="*70)
print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
print("="*70)
