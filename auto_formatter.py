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
    
    def segment_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        return nltk.sent_tokenize(text)
    
    def capitalize_sentences(self, sentences: List[str]) -> List[str]:
        """Capitalize first letter of each sentence"""
        return [s[0].upper() + s[1:] if s else s for s in sentences]
    
    def add_punctuation(self, text: str) -> str:
        """Add periods to sentences without punctuation"""
        sentences = self.segment_sentences(text)
        formatted = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[-1] in '.!?':
                sentence += '.'
            formatted.append(sentence)
        
        return ' '.join(formatted)
    
    def create_paragraphs(self, text: str, sentences_per_paragraph: int = 3) -> str:
        """Group sentences into paragraphs"""
        sentences = self.segment_sentences(text)
        paragraphs = []
        
        for i in range(0, len(sentences), sentences_per_paragraph):
            paragraph = ' '.join(sentences[i:i + sentences_per_paragraph])
            paragraphs.append(paragraph)
        
        return '\n\n'.join(paragraphs)
    
    def convert_to_bullets(self, text: str) -> str:
        """Convert sentences to bullet points"""
        sentences = self.segment_sentences(text)
        bullets = [f"• {sentence.strip()}" for sentence in sentences if sentence.strip()]
        return '\n'.join(bullets)
    
    def format_text(self, text: str, use_paragraphs: bool = False, use_bullets: bool = False) -> str:
        """Apply all formatting"""
        # Add punctuation
        text = self.add_punctuation(text)
        
        # Segment and capitalize
        sentences = self.segment_sentences(text)
        sentences = self.capitalize_sentences(sentences)
        
        if use_bullets:
            return self.convert_to_bullets(' '.join(sentences))
        elif use_paragraphs:
            return self.create_paragraphs(' '.join(sentences))
        else:
            return ' '.join(sentences)