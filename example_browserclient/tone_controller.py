# tone_controller.py
"""
Advanced Tone/Style Control for text transformation (Non-LLM)
Modes: Neutral (baseline), Formal, Casual, Soft/Polite, Concise, Friendly
Pipeline: Speech → Neutral → Tone Transformation
"""

import re


class ToneController:
    def __init__(self):
        print("Initializing Advanced Tone Controller...")
        
        # Slang/Casual to Neutral normalization
        self.normalize_map = {
            r'\bhey\b': 'hello',
            r'\bhi\b': 'hello',
            r'\byo\b': 'hello',
            r'\bdude\b': '',
            r'\bman\b': '',
            r'\bguys\b': 'everyone',
            r'\bwanna\b': 'want to',
            r'\bgonna\b': 'going to',
            r'\bgotta\b': 'have to',
            r'\bkinda\b': 'kind of',
            r'\bsorta\b': 'sort of',
            r'\byeah\b': 'yes',
            r'\bnope\b': 'no',
            r'\byep\b': 'yes',
            r'\bok\b': 'okay',
            r'\bsuper\b': 'very',
            r'\btotally\b': 'completely',
            r'\bbasically\b': 'essentially',
        }
        
        # Formal templates
        self.formal_prefixes = [
            'I would like to inform you that',
            'I wish to',
            'I would appreciate if',
            'May I suggest that',
        ]
        
        # Soft/Polite modifiers
        self.softeners = ['perhaps', 'possibly', 'if possible', 'kindly', 'please']
        
        print("Tone Controller initialized with 6 modes")

    def normalize(self, text: str) -> str:
        """Convert casual speech to neutral baseline"""
        result = text.lower()
        
        # Apply normalization
        for pattern, replacement in self.normalize_map.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Remove filler words
        fillers = ['like', 'um', 'uh', 'you know', 'i mean']
        for filler in fillers:
            result = re.sub(r'\b' + filler + r'\b', '', result, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Capitalize first letter and fix spacing
        result = re.sub(r'\s+', ' ', result).strip()
        if result:
            result = result[0].upper() + result[1:]
        
        return result

    def to_formal(self, text: str) -> str:
        """Transform to formal/professional tone"""
        result = text
        
        # Expand all contractions
        contractions = {
            r"\bI'm\b": "I am",
            r"\byou're\b": "you are",
            r"\bhe's\b": "he is",
            r"\bshe's\b": "she is",
            r"\bit's\b": "it is",
            r"\bwe're\b": "we are",
            r"\bthey're\b": "they are",
            r"\bcan't\b": "cannot",
            r"\bwon't\b": "will not",
            r"\bdon't\b": "do not",
            r"\bdoesn't\b": "does not",
            r"\bdidn't\b": "did not",
        }
        
        for pattern, replacement in contractions.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Add formal prefix for statements
        if re.match(r'^I (want|need|have|am)', result, re.IGNORECASE):
            result = re.sub(r'^I ', 'I would like to ', result, flags=re.IGNORECASE)
        
        # Replace casual words
        result = re.sub(r'\bget\b', 'obtain', result, flags=re.IGNORECASE)
        result = re.sub(r'\bshow\b', 'demonstrate', result, flags=re.IGNORECASE)
        result = re.sub(r'\bhelp\b', 'assist', result, flags=re.IGNORECASE)
        result = re.sub(r'\bask\b', 'inquire', result, flags=re.IGNORECASE)
        
        return result

    def to_casual(self, text: str) -> str:
        """Transform to casual/friendly tone"""
        result = text
        
        # Add contractions
        expansions = {
            r"\bI am\b": "I'm",
            r"\byou are\b": "you're",
            r"\bhe is\b": "he's",
            r"\bshe is\b": "she's",
            r"\bit is\b": "it's",
            r"\bwe are\b": "we're",
            r"\bthey are\b": "they're",
            r"\bcannot\b": "can't",
            r"\bwill not\b": "won't",
            r"\bdo not\b": "don't",
        }
        
        for pattern, replacement in expansions.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Add casual words
        result = re.sub(r'\bwant to\b', 'wanna', result, flags=re.IGNORECASE)
        result = re.sub(r'\bgoing to\b', 'gonna', result, flags=re.IGNORECASE)
        result = re.sub(r'\bhave to\b', 'gotta', result, flags=re.IGNORECASE)
        
        # Add casual greeting
        if not re.match(r'^(hey|hi|yo)', result, re.IGNORECASE):
            result = 'Hey, ' + result[0].lower() + result[1:]
        
        return result

    def to_soft(self, text: str) -> str:
        """Transform to soft/polite tone"""
        result = text
        
        # Add softeners
        if re.match(r'^I (want|need|would like)', result, re.IGNORECASE):
            result = re.sub(r'^I ', 'If possible, I ', result, flags=re.IGNORECASE)
        
        # Add "please" if not present
        if 'please' not in result.lower():
            # Add before verb
            result = re.sub(r'\b(can|could|would)\s+you\b', r'\1 you please', result, flags=re.IGNORECASE)
            
            # Or add at end if it's a request
            if re.search(r'\b(want|need|like)\b', result, flags=re.IGNORECASE):
                result = result.rstrip('.') + ', please.'
        
        # Use softer verbs
        result = re.sub(r'\bneed\b', 'would appreciate', result, flags=re.IGNORECASE)
        result = re.sub(r'\bwant\b', 'would like', result, flags=re.IGNORECASE)
        
        return result

    def to_concise(self, text: str) -> str:
        """Transform to concise/direct tone"""
        result = text
        
        # Remove all softeners and fillers
        removals = [
            'if possible', 'perhaps', 'possibly', 'maybe', 'I think', 
            'I believe', 'in my opinion', 'it seems', 'kind of', 'sort of',
            'basically', 'actually', 'literally', 'honestly', 'just'
        ]
        
        for phrase in removals:
            result = re.sub(r'\b' + re.escape(phrase) + r'\b', '', result, flags=re.IGNORECASE)
        
        # Remove "I would like to" → direct statement
        result = re.sub(r'I would like to\s+', 'I ', result, flags=re.IGNORECASE)
        result = re.sub(r'I want to\s+', 'I ', result, flags=re.IGNORECASE)
        
        # Clean up
        result = re.sub(r'\s+', ' ', result).strip()
        result = re.sub(r'\s+([,.!?])', r'\1', result)
        
        return result

    def to_friendly(self, text: str) -> str:
        """Transform to friendly/warm tone"""
        result = text
        
        # Add friendly greeting if not present
        if not re.match(r'^(hey|hi|hello)', result, re.IGNORECASE):
            result = 'Hi! ' + result
        
        # Add enthusiasm
        if result.endswith('.'):
            result = result[:-1] + '!'
        
        # Use friendlier words
        result = re.sub(r'\bokay\b', 'great', result, flags=re.IGNORECASE)
        result = re.sub(r'\byes\b', 'absolutely', result, flags=re.IGNORECASE)
        
        # Add contractions for warmth
        result = re.sub(r'\bI am\b', "I'm", result)
        result = re.sub(r'\bI will\b', "I'll", result)
        
        return result

    def transform(self, text: str, mode: str = 'neutral') -> str:
        """
        Transform text to specified tone
        Pipeline: Input → Normalize → Apply Tone
        
        Args:
            text: Input text (raw or normalized)
            mode: 'neutral', 'formal', 'casual', 'soft', 'concise', 'friendly'
        
        Returns:
            Transformed text
        """
        mode = mode.lower()
        
        # First normalize the text (baseline)
        normalized = self.normalize(text)
        
        # Then apply tone transformation
        if mode == 'neutral':
            return normalized
        elif mode == 'formal':
            return self.to_formal(normalized)
        elif mode == 'casual':
            return self.to_casual(normalized)
        elif mode == 'soft':
            return self.to_soft(normalized)
        elif mode == 'concise':
            return self.to_concise(normalized)
        elif mode == 'friendly':
            return self.to_friendly(normalized)
        else:
            return normalized


# Example usage
if __name__ == "__main__":
    tc = ToneController()
    
    test_sentence = "Hey dude, I kinda wanna leave now"
    
    print(f"Original: {test_sentence}\n")
    
    modes = ['neutral', 'formal', 'casual', 'soft', 'concise', 'friendly']
    
    for mode in modes:
        result = tc.transform(test_sentence, mode)
        print(f"{mode.capitalize():12s}: {result}")
