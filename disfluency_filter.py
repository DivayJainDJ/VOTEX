import re

class DisfluencyFilter:
    def __init__(self):
        # Common filler words and disfluencies
        self.fillers = {
            'umm', 'uhh', 'ehh', 'uh', 'um', 'er', 'ah', 'oh',
            'you know', 'like', 'so', 'well', 'actually', 'basically',
            'literally', 'totally', 'really', 'very', 'just', 'kind of',
            'sort of', 'i mean', 'you see', 'right', 'okay', 'alright'
        }
        
        # Pattern for repeated words (stuttering)
        self.stutter_pattern = re.compile(r'\b(\w+)(\s+\1){2,}\b', re.IGNORECASE)
        
    def remove_fillers(self, text: str) -> str:
        """Remove filler words and phrases"""
        words = text.lower().split()
        filtered = []
        i = 0
        
        while i < len(words):
            # Check for multi-word fillers
            found_filler = False
            for filler in sorted(self.fillers, key=len, reverse=True):
                filler_words = filler.split()
                if (i + len(filler_words) <= len(words) and 
                    ' '.join(words[i:i+len(filler_words)]) == filler):
                    i += len(filler_words)
                    found_filler = True
                    break
            
            if not found_filler:
                filtered.append(words[i])
                i += 1
        
        return ' '.join(filtered)
    
    def remove_stutters(self, text: str) -> str:
        """Remove stuttering (repeated words)"""
        return self.stutter_pattern.sub(r'\1', text)
    
    def clean_text(self, text: str) -> str:
        """Apply all disfluency removal"""
        # Remove stutters first
        text = self.remove_stutters(text)
        # Remove fillers
        text = self.remove_fillers(text)
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        return text