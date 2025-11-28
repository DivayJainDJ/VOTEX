import re
import nltk
from typing import List

class AutoFormatter:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab')
        
        # Common abbreviations that shouldn't end sentences
        self.abbreviations = {'mr', 'mrs', 'dr', 'prof', 'inc', 'ltd', 'vs', 'etc', 'i.e', 'e.g'}
        
        # Question indicators
        self.question_words = {'what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose'}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove multiple punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        return text.strip()
    
    def segment_sentences(self, text: str) -> List[str]:
        """Enhanced sentence segmentation"""
        text = self.clean_text(text)
        
        # Use NLTK for initial segmentation
        sentences = nltk.sent_tokenize(text)
        
        # Post-process to fix common errors
        fixed_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Check if previous sentence ended with abbreviation
                words = sentence.lower().split()
                if (fixed_sentences and 
                    len(words) > 0 and 
                    any(abbr in fixed_sentences[-1].lower() for abbr in self.abbreviations)):
                    # Merge with previous sentence
                    fixed_sentences[-1] += ' ' + sentence
                else:
                    fixed_sentences.append(sentence)
        
        return fixed_sentences
    
    def detect_questions(self, sentence: str) -> bool:
        """Detect if sentence should be a question"""
        words = sentence.lower().split()
        if not words:
            return False
        
        # Check for question words at start
        if words[0] in self.question_words:
            return True
        
        # Check for inverted word order (auxiliary verbs)
        aux_verbs = {'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should'}
        if len(words) > 1 and words[0] in aux_verbs:
            return True
        
        return False
    
    def smart_punctuation(self, sentences: List[str]) -> List[str]:
        """Add intelligent punctuation"""
        formatted = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Remove existing punctuation at end
            while sentence and sentence[-1] in '.!?,':
                sentence = sentence[:-1].strip()
            
            if sentence:
                # Detect question
                if self.detect_questions(sentence):
                    sentence += '?'
                # Detect exclamation (simple heuristic)
                elif any(word in sentence.lower() for word in ['wow', 'amazing', 'great', 'terrible', 'help']):
                    sentence += '!'
                else:
                    sentence += '.'
                
                formatted.append(sentence)
        
        return formatted
    
    def capitalize_sentences(self, sentences: List[str]) -> List[str]:
        """Enhanced capitalization"""
        formatted = []
        
        for sentence in sentences:
            if not sentence:
                continue
            
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            
            # Capitalize 'I'
            sentence = re.sub(r'\bi\b', 'I', sentence)
            
            # Capitalize after punctuation
            sentence = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), sentence)
            
            formatted.append(sentence)
        
        return formatted
    
    def create_paragraphs(self, sentences: List[str], sentences_per_paragraph: int = 3) -> str:
        """Smart paragraph creation"""
        if len(sentences) <= sentences_per_paragraph:
            return ' '.join(sentences)
        
        paragraphs = []
        current_paragraph = []
        
        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)
            
            # Create paragraph break conditions
            should_break = (
                len(current_paragraph) >= sentences_per_paragraph or
                (i < len(sentences) - 1 and 
                 any(word in sentence.lower() for word in ['however', 'meanwhile', 'furthermore', 'moreover']))
            )
            
            if should_break or i == len(sentences) - 1:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
        
        return '\n\n'.join(paragraphs)
    
    def format_text(self, text: str, use_paragraphs: bool = True) -> str:
        """Enhanced text formatting with automatic paragraph detection"""
        if not text or not text.strip():
            return text
        
        # Clean input
        text = self.clean_text(text)
        
        # Segment sentences
        sentences = self.segment_sentences(text)
        
        # Apply smart punctuation
        sentences = self.smart_punctuation(sentences)
        
        # Capitalize properly
        sentences = self.capitalize_sentences(sentences)
        
        # Always create paragraphs for better readability
        if len(sentences) > 2:
            return self.create_paragraphs(sentences)
        else:
            return ' '.join(sentences)


# Test cases
if __name__ == '__main__':
    formatter = AutoFormatter()
    
    test_cases = [
        # Basic formatting
        "hello world this is a test",
        
        # Questions
        "what is your name how are you doing",
        
        # Mixed punctuation
        "this is great wow that's amazing",
        
        # Abbreviations
        "mr smith went to dr jones inc for a meeting",
        
        # Multiple sentences
        "i went to the store yesterday i bought some milk and bread then i came home",
        
        # Complex case
        "what time is it now i think it's around 3 pm but i'm not sure can you check"
    ]
    
    print("=== Auto-Formatter Test Cases ===")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input:     {test}")
        
        # Test basic formatting
        basic = formatter.format_text(test)
        print(f"Basic:     {basic}")
        
        # Test with paragraphs
        if len(formatter.segment_sentences(test)) > 2:
            para = formatter.format_text(test, use_paragraphs=True)
            print(f"Paragraph: {para.replace(chr(10), ' [NEWLINE] ')}")
    
    print("\n=== Individual Component Tests ===")
    
    # Test sentence segmentation
    test_text = "hello world this is a test what time is it"
    sentences = formatter.segment_sentences(test_text)
    print(f"\nSegmentation: {sentences}")
    
    # Test question detection
    questions = ["what is this", "how are you", "this is good"]
    for q in questions:
        is_q = formatter.detect_questions(q)
        print(f"'{q}' -> Question: {is_q}")
    
    # Test smart punctuation
    test_sentences = ["what is your name", "this is amazing", "i went home"]
    punctuated = formatter.smart_punctuation(test_sentences)
    print(f"\nPunctuation: {punctuated}")
    
    print("\n=== Tests Complete ===")