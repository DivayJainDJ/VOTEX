"""
Paragraph Detection Module
Detects sentence endings vs paragraph breaks based on silence duration
"""

import time
import re
from typing import Literal


class ParagraphDetector:
    """
    Detects paragraph breaks vs sentence endings using dual silence thresholds
    """
    
    # Silence thresholds
    SENTENCE_PAUSE = 2.0      # seconds - normal sentence ending
    PARAGRAPH_PAUSE = 5.0     # seconds - paragraph break / end of thought
    
    def __init__(self, sentence_pause: float = 2.0, paragraph_pause: float = 5.0):
        """
        Initialize paragraph detector
        
        Args:
            sentence_pause: Silence duration for sentence ending (seconds)
            paragraph_pause: Silence duration for paragraph break (seconds)
        """
        self.sentence_pause = sentence_pause
        self.paragraph_pause = paragraph_pause
        self.last_voice_time = time.time()
        self.silence_start = None
        self.is_silent = False
        
        print(f"📝 Paragraph Detector initialized:")
        print(f"   Sentence pause: {sentence_pause}s → '.'")
        print(f"   Paragraph pause: {paragraph_pause}s → '\\n\\n'")
    
    def mark_voice_activity(self):
        """Call this when voice/speech is detected"""
        self.last_voice_time = time.time()
        if self.is_silent:
            self.is_silent = False
            self.silence_start = None
    
    def mark_silence_start(self):
        """Call this when silence begins"""
        if not self.is_silent:
            self.is_silent = True
            self.silence_start = time.time()
    
    def get_silence_duration(self) -> float:
        """Get current silence duration in seconds"""
        if self.is_silent and self.silence_start:
            return time.time() - self.silence_start
        return 0.0
    
    def detect_break_type(self, silence_duration: float = None) -> Literal['none', 'sentence', 'paragraph']:
        """
        Detect what type of break occurred based on silence duration
        
        Args:
            silence_duration: Optional explicit silence duration. If None, calculates from last voice time
            
        Returns:
            'none' - no break detected
            'sentence' - sentence ending detected
            'paragraph' - paragraph break detected
        """
        if silence_duration is None:
            silence_duration = self.get_silence_duration()
        
        if silence_duration >= self.paragraph_pause:
            return 'paragraph'
        elif silence_duration >= self.sentence_pause:
            return 'sentence'
        else:
            return 'none'
    
    def get_punctuation(self, silence_duration: float = None) -> str:
        """
        Get appropriate punctuation/formatting based on silence duration
        
        Args:
            silence_duration: Optional explicit silence duration
            
        Returns:
            '' - no punctuation
            '. ' - sentence ending
            '.\n\n' - paragraph break
        """
        break_type = self.detect_break_type(silence_duration)
        
        if break_type == 'paragraph':
            return '.\n\n'
        elif break_type == 'sentence':
            return '. '
        else:
            return ''
    
    def is_question(self, text: str) -> bool:
        """
        Detect if text is a question
        
        Args:
            text: Input text
            
        Returns:
            True if text appears to be a question
        """
        text_lower = text.lower().strip()
        
        # Exclude statements that start with "what" but aren't questions
        # e.g., "what I'm trying to say", "what a beautiful day"
        non_question_patterns = [
            r'^what\s+(i\'m|im|i am)\s+',  # "what I'm trying to say"
            r'^what\s+a\s+',  # "what a beautiful day" (exclamation)
            r'^what\s+(we|they|he|she|it)\s+(need|want|should|can|could)',  # "what we need is"
            r'know\s+what\s+to',  # "I don't know what to do"
            r'tell\s+me\s+what',  # "tell me what happened"
        ]
        
        for pattern in non_question_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # Question words at start (direct questions)
        question_starters = (
            'what', 'where', 'when', 'why', 'who', 'whom', 'whose', 'which', 'how',
            'is', 'are', 'was', 'were', 'am',
            'do', 'does', 'did',
            'can', 'could', 'would', 'should', 'will', 'shall',
            'have', 'has', 'had',
            'may', 'might', 'must'
        )
        
        # Check if starts with question word
        first_word = text_lower.split()[0] if text_lower.split() else ''
        if first_word in question_starters:
            return True
        
        # Check for question patterns (auxiliary verb + subject)
        question_patterns = [
            r'^\b(is|are|was|were|am)\b\s+\w+',  # "is this", "are you"
            r'^\b(do|does|did)\b\s+\w+',  # "do you", "does it"
            r'^\b(can|could|would|should|will|shall)\b\s+\w+',  # "can you", "would you"
            r'^\b(have|has|had)\b\s+\w+',  # "have you", "has it"
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def format_text_with_breaks(self, text: str, break_type: Literal['sentence', 'paragraph']) -> str:
        """
        Format text with appropriate breaks
        
        Args:
            text: Input text
            break_type: Type of break to add
            
        Returns:
            Formatted text with appropriate punctuation/breaks
        """
        text = text.strip()
        
        # Remove existing trailing punctuation
        if text and text[-1] in '.!?':
            text = text[:-1].strip()
        
        # Detect if it's a question
        is_question = self.is_question(text)
        
        if break_type == 'paragraph':
            if is_question:
                return f"{text}?\n\n"
            else:
                return f"{text}.\n\n"
        elif break_type == 'sentence':
            if is_question:
                return f"{text}? "
            else:
                return f"{text}. "
        else:
            return text
    
    def reset(self):
        """Reset detector state"""
        self.last_voice_time = time.time()
        self.silence_start = None
        self.is_silent = False


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("PARAGRAPH DETECTOR - TEST")
    print("="*70)
    print()
    
    detector = ParagraphDetector(sentence_pause=2.0, paragraph_pause=5.0)
    
    # Simulate different silence durations
    test_cases = [
        (1.0, "Short pause - no break"),
        (2.5, "Medium pause - sentence ending"),
        (6.0, "Long pause - paragraph break"),
        (3.0, "3 second pause - sentence ending"),
        (8.0, "Very long pause - paragraph break"),
    ]
    
    print("Testing silence detection:\n")
    for duration, description in test_cases:
        break_type = detector.detect_break_type(duration)
        punctuation = detector.get_punctuation(duration)
        
        print(f"Silence: {duration}s - {description}")
        print(f"  Break type: {break_type}")
        print(f"  Punctuation: {repr(punctuation)}")
        print()
    
    # Test text formatting
    print("\nTesting text formatting:\n")
    
    test_texts = [
        ("Hello everyone", "sentence"),
        ("This is a new paragraph", "paragraph"),
        ("What is your name", "sentence"),
        ("End of thought here", "paragraph"),
    ]
    
    for text, break_type in test_texts:
        formatted = detector.format_text_with_breaks(text, break_type)
        print(f"Input:  '{text}' ({break_type})")
        print(f"Output: {repr(formatted)}")
        print()
    
    print("="*70)
    print("✓ Test complete!")
