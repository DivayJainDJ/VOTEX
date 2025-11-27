# grammar_processor.py
"""
Comprehensive rule-based grammar correction for STT output
Fixes: word order, articles, verb forms, tense, punctuation, capitalization
"""

import re
from collections import defaultdict


class GrammarProcessor:
    def __init__(self):
        print("Initializing comprehensive rule-based grammar processor...")
        
        # Common irregular verbs
        self.irregular_verbs = {
            'go': {'past': 'went', 'past_participle': 'gone', 'present_3rd': 'goes'},
            'have': {'past': 'had', 'past_participle': 'had', 'present_3rd': 'has'},
            'do': {'past': 'did', 'past_participle': 'done', 'present_3rd': 'does'},
            'be': {'past': 'was', 'past_participle': 'been', 'present_3rd': 'is'},
            'see': {'past': 'saw', 'past_participle': 'seen', 'present_3rd': 'sees'},
            'make': {'past': 'made', 'past_participle': 'made', 'present_3rd': 'makes'},
            'take': {'past': 'took', 'past_participle': 'taken', 'present_3rd': 'takes'},
        }
        
        # Time expressions
        self.time_words = ['today', 'tomorrow', 'yesterday', 'tonight', 'now', 'later', 
                          'soon', 'morning', 'afternoon', 'evening', 'night', 'week', 
                          'month', 'year', 'monday', 'tuesday', 'wednesday', 'thursday',
                          'friday', 'saturday', 'sunday']
        
        # Frequency adverbs
        self.frequency_adverbs = ['always', 'usually', 'often', 'sometimes', 'rarely', 
                                 'never', 'frequently', 'occasionally', 'seldom']
        
        print("Grammar processor initialized with comprehensive rules")

    def fix_articles(self, text):
        """Fix a/an article errors"""
        vowel_sounds = ['a', 'e', 'i', 'o', 'u', 'hour', 'honest', 'honor']
        words = text.split()
        fixed_words = []
        
        for i in range(len(words)):
            word = words[i]
            
            if i > 0 and words[i-1].lower() == 'a':
                next_word_lower = word.lower().strip('.,!?;:')
                if next_word_lower and (next_word_lower[0] in 'aeiou' or next_word_lower in vowel_sounds):
                    fixed_words[-1] = 'an' if words[i-1] == 'a' else 'An'
            
            elif i > 0 and words[i-1].lower() == 'an':
                next_word_lower = word.lower().strip('.,!?;:')
                if next_word_lower and next_word_lower[0] not in 'aeiou' and next_word_lower not in vowel_sounds:
                    fixed_words[-1] = 'a' if words[i-1] == 'an' else 'A'
            
            fixed_words.append(word)
        
        return ' '.join(fixed_words)

    def fix_word_order(self, text):
        """Fix common word order issues"""
        words = text.split()
        
        # Pattern 1: "article + time_word + noun" -> "article + noun + time_word"
        # Example: "a tomorrow match" -> "a match tomorrow"
        i = 0
        while i < len(words) - 2:
            if words[i].lower() in ['a', 'an', 'the']:
                if words[i+1].lower() in self.time_words:
                    # Found pattern: article + time + (next word is likely noun)
                    if i + 2 < len(words):
                        article = words[i]
                        time_word = words[i+1]
                        noun = words[i+2]
                        # Reorder: article + noun + time
                        words[i] = article
                        words[i+1] = noun
                        words[i+2] = time_word
                        print(f"Fixed word order: '{article} {time_word} {noun}' -> '{article} {noun} {time_word}'")
            i += 1
        
        # Pattern 2: Frequency adverbs should come before main verb
        # "I go always" -> "I always go"
        for i in range(1, len(words) - 1):
            if words[i].lower() in self.frequency_adverbs:
                # Check if previous word is a verb (not auxiliary)
                if words[i-1].lower() not in ['am', 'is', 'are', 'was', 'were', 'have', 'has', 'had']:
                    # Swap adverb with previous word
                    words[i], words[i-1] = words[i-1], words[i]
        
        return ' '.join(words)

    def fix_subject_verb_agreement(self, text):
        """Fix subject-verb agreement"""
        words = text.split()
        
        for i in range(len(words) - 1):
            subject = words[i].lower()
            verb = words[i+1].lower()
            
            # Third person singular (he, she, it) needs 's' on verb
            if subject in ['he', 'she', 'it']:
                if verb == 'have':
                    words[i+1] = 'has'
                elif verb == 'do':
                    words[i+1] = 'does'
                elif verb == 'go':
                    words[i+1] = 'goes'
                elif verb not in ['is', 'was', 'has', 'does'] and not verb.endswith('s'):
                    if not verb.endswith(('ss', 'sh', 'ch', 'x', 'z')):
                        words[i+1] = verb + 's'
            
            # Plural subjects (we, they, you, I) don't need 's'
            elif subject in ['i', 'you', 'we', 'they']:
                if verb == 'has':
                    words[i+1] = 'have'
                elif verb == 'does':
                    words[i+1] = 'do'
                elif verb == 'goes':
                    words[i+1] = 'go'
        
        return ' '.join(words)

    def fix_double_negatives(self, text):
        """Fix double negatives"""
        # "I don't have no" -> "I don't have any"
        text = re.sub(r"\bdon't\s+have\s+no\b", "don't have any", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdidn't\s+have\s+no\b", "didn't have any", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcan't\s+see\s+nothing\b", "can't see anything", text, flags=re.IGNORECASE)
        return text

    def fix_prepositions(self, text):
        """Fix common preposition errors"""
        # "different than" -> "different from"
        text = re.sub(r'\bdifferent\s+than\b', 'different from', text, flags=re.IGNORECASE)
        
        # "on the weekend" -> "on the weekend" or "at the weekend"
        text = re.sub(r'\bin\s+the\s+weekend\b', 'on the weekend', text, flags=re.IGNORECASE)
        
        # "married with" -> "married to"
        text = re.sub(r'\bmarried\s+with\b', 'married to', text, flags=re.IGNORECASE)
        
        return text

    def fix_common_mistakes(self, text):
        """Fix common grammar mistakes"""
        # "could of" -> "could have"
        text = re.sub(r'\bcould\s+of\b', 'could have', text, flags=re.IGNORECASE)
        text = re.sub(r'\bshould\s+of\b', 'should have', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwould\s+of\b', 'would have', text, flags=re.IGNORECASE)
        
        # "alot" -> "a lot"
        text = re.sub(r'\balot\b', 'a lot', text, flags=re.IGNORECASE)
        
        # "your" vs "you're"
        text = re.sub(r'\byour\s+(going|coming|doing)\b', r"you're \1", text, flags=re.IGNORECASE)
        
        # "its" vs "it's"
        text = re.sub(r'\bits\s+(going|coming|doing)\b', r"it's \1", text, flags=re.IGNORECASE)
        
        # "there" vs "their" vs "they're"
        text = re.sub(r'\btheir\s+(is|are|was|were)\b', r'there \1', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthere\s+(going|coming)\b', r"they're \1", text, flags=re.IGNORECASE)
        
        return text

    def fix_contractions(self, text):
        """Fix missing contractions"""
        # "I am" -> "I'm" (optional, for natural speech)
        text = re.sub(r'\bI am\b', "I'm", text)
        text = re.sub(r'\byou are\b', "you're", text, flags=re.IGNORECASE)
        text = re.sub(r'\bhe is\b', "he's", text, flags=re.IGNORECASE)
        text = re.sub(r'\bshe is\b', "she's", text, flags=re.IGNORECASE)
        text = re.sub(r'\bit is\b', "it's", text, flags=re.IGNORECASE)
        text = re.sub(r'\bwe are\b', "we're", text, flags=re.IGNORECASE)
        text = re.sub(r'\bthey are\b', "they're", text, flags=re.IGNORECASE)
        
        return text

    def add_punctuation(self, text):
        """Add proper punctuation"""
        # Add period at end if missing
        if text and not text[-1] in '.!?':
            text = text + '.'
        
        # Add comma before conjunctions in long sentences
        if len(text.split()) > 8:
            text = re.sub(r'\s+(and|but|or|so|yet)\s+', r', \1 ', text)
        
        return text

    def fix_capitalization(self, text):
        """Fix capitalization"""
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Capitalize after sentence endings
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Capitalize "I"
        text = re.sub(r'\bi\b', 'I', text)
        
        # Capitalize days and months
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        months = ['january', 'february', 'march', 'april', 'may', 'june', 
                 'july', 'august', 'september', 'october', 'november', 'december']
        
        for day in days:
            text = re.sub(r'\b' + day + r'\b', day.capitalize(), text, flags=re.IGNORECASE)
        for month in months:
            text = re.sub(r'\b' + month + r'\b', month.capitalize(), text, flags=re.IGNORECASE)
        
        return text

    def correct_text(self, text: str) -> str:
        """
        Apply comprehensive grammar correction rules (optimized for speed)
        
        Args:
            text (str): raw STT text with possible errors
        Returns:
            str: corrected text
        """
        if not text or len(text.strip()) == 0:
            return text

        try:
            # Apply all correction rules in order (optimized)
            corrected = text.lower()  # Start with lowercase
            
            # Fast path: combine multiple regex operations
            # 1-2. Fix common mistakes and double negatives (combined)
            corrected = self.fix_common_mistakes(corrected)
            corrected = self.fix_double_negatives(corrected)
            
            # 3. Fix word order (critical for STT)
            corrected = self.fix_word_order(corrected)
            
            # 4-5. Fix articles (skip subject-verb for speed)
            corrected = self.fix_articles(corrected)
            
            # 6. Skip prepositions for speed
            
            # 7. Fix capitalization
            corrected = self.fix_capitalization(corrected)
            
            # 8. Add punctuation
            corrected = self.add_punctuation(corrected)
            
            # 9. Clean up spacing (single pass)
            corrected = re.sub(r'\s+([,.!?;:])', r'\1', corrected)
            corrected = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', corrected)
            corrected = re.sub(r'\s+', ' ', corrected).strip()
            
            return corrected
            
        except Exception as e:
            print(f"Grammar correction error: {e}")
            # Fallback: basic fixes
            if text:
                text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
                if not text[-1] in '.!?':
                    text += '.'
            return text


# Example usage
if __name__ == "__main__":
    gp = GrammarProcessor()
    
    tests = [
        "i have a tomorrow match",
        "he dont like it",
        "i could of done it",
        "its a nice day",
        "i go always to school",
        "she have a car",
        "this is a umbrella",
        "i dont have no money"
    ]
    
    for raw in tests:
        print(f"Original:  {raw}")
        print(f"Corrected: {gp.correct_text(raw)}")
        print()
