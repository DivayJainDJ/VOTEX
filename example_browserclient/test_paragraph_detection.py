"""
Test paragraph detection with realistic examples
"""

from paragraph_detector import ParagraphDetector

print("="*70)
print("PARAGRAPH DETECTION - REALISTIC EXAMPLES")
print("="*70)
print()

detector = ParagraphDetector(sentence_pause=2.0, paragraph_pause=5.0)

# Simulate realistic dictation scenarios
scenarios = [
    {
        "name": "Email Dictation",
        "segments": [
            ("Dear John", 2.5, "sentence"),
            ("I hope this email finds you well", 3.0, "sentence"),
            ("I wanted to discuss the project timeline", 6.0, "paragraph"),
            ("Please let me know your availability", 2.5, "sentence"),
            ("Best regards", 7.0, "paragraph"),
        ]
    },
    {
        "name": "Meeting Notes",
        "segments": [
            ("Meeting notes for today", 3.0, "sentence"),
            ("Attendees John and Mary", 6.0, "paragraph"),
            ("Action items", 3.0, "sentence"),
            ("Review proposal by Friday", 6.0, "paragraph"),
            ("Next meeting Monday", 2.0, "sentence"),
        ]
    },
    {
        "name": "Blog Post",
        "segments": [
            ("Introduction to machine learning", 3.0, "sentence"),
            ("Machine learning is transforming technology", 6.0, "paragraph"),
            ("There are three main types", 3.0, "sentence"),
            ("Supervised learning", 2.0, "sentence"),
            ("Unsupervised learning", 2.0, "sentence"),
            ("And reinforcement learning", 7.0, "paragraph"),
        ]
    }
]

for scenario in scenarios:
    print(f"\n{'='*70}")
    print(f"Scenario: {scenario['name']}")
    print('='*70)
    print()
    
    full_text = ""
    
    for text, silence, expected_break in scenario['segments']:
        # Detect break type
        break_type = detector.detect_break_type(silence)
        
        # Format text
        formatted = detector.format_text_with_breaks(text, break_type)
        full_text += formatted
        
        # Show details
        print(f"Text: '{text}'")
        print(f"  Silence: {silence}s")
        print(f"  Detected: {break_type}")
        print(f"  Output: {repr(formatted)}")
        print()
    
    print("Final Output:")
    print("-" * 70)
    print(full_text)
    print()

print("="*70)
print("✓ Test complete!")
print()
print("To test in real-time:")
print("  1. Open http://localhost:8080")
print("  2. Click 'Start Recording'")
print("  3. Speak sentences with 2-3s pauses")
print("  4. Pause 5+ seconds for paragraph breaks")
print("="*70)
