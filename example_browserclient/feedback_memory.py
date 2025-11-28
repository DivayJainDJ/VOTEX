"""
Self-Learning Feedback System with Auto-Improvement
- Approve/Reject mechanism
- ChatGPT integration for corrections
- Automatic rule updates
"""
import json
import os
from datetime import datetime
import requests


class FeedbackMemory:
    def __init__(self, memory_file='feedback_memory.json'):
        self.memory_file = memory_file
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load feedback memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migrate old format to new format
                    if 'approved' not in data:
                        data['approved'] = []
                    if 'rejected' not in data:
                        data['rejected'] = []
                    if 'accuracy_score' not in data:
                        data['accuracy_score'] = 0.0
                    return data
            except:
                return {
                    'corrections': [],
                    'rules': {},
                    'approved': [],
                    'rejected': [],
                    'accuracy_score': 0.0
                }
        return {
            'corrections': [],
            'rules': {},
            'approved': [],
            'rejected': [],
            'accuracy_score': 0.0
        }
    
    def save_memory(self):
        """Save feedback memory to file"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def add_correction(self, original, system_output, user_correction, tone_mode):
        """Store a user correction"""
        correction_entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'system_output': system_output,
            'user_correction': user_correction,
            'tone_mode': tone_mode
        }
        self.memory['corrections'].append(correction_entry)
        
        # Try to extract rules
        self._extract_rules(original, system_output, user_correction, tone_mode)
        self.save_memory()
        print(f"✓ Feedback stored: {len(self.memory['corrections'])} total corrections")
    
    def _extract_rules(self, original, system_output, user_correction, tone_mode):
        """Extract transformation rules from corrections"""
        # Simple word-level rule extraction
        original_words = original.lower().split()
        correction_words = user_correction.lower().split()
        
        # Look for word replacements
        for i, word in enumerate(original_words):
            if i < len(correction_words) and word != correction_words[i]:
                rule_key = f"{word}→{correction_words[i]}:{tone_mode}"
                if rule_key not in self.memory['rules']:
                    self.memory['rules'][rule_key] = {'count': 0, 'examples': []}
                self.memory['rules'][rule_key]['count'] += 1
                if len(self.memory['rules'][rule_key]['examples']) < 3:
                    self.memory['rules'][rule_key]['examples'].append({
                        'original': original,
                        'correction': user_correction
                    })
    
    def check_memory(self, text, tone_mode):
        """Check if we have a learned correction for this input"""
        text_normalized = text.lower().strip()
        
        # Check exact matches first
        for correction in self.memory['corrections']:
            if (correction['original'].lower().strip() == text_normalized and 
                correction['tone_mode'] == tone_mode):
                return correction['user_correction']
        
        # Apply learned rules
        result = text
        for rule_key, rule_data in self.memory['rules'].items():
            if rule_data['count'] >= 2:  # Only apply rules seen 2+ times
                parts = rule_key.split(':')
                if len(parts) == 2 and parts[1] == tone_mode:
                    word_rule = parts[0].split('→')
                    if len(word_rule) == 2:
                        from_word, to_word = word_rule
                        result = result.replace(from_word, to_word)
        
        return result if result != text else None
    
    def approve_output(self, original, output, tone_mode):
        """User approves the output - reinforces current behavior"""
        approval_entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'output': output,
            'tone_mode': tone_mode
        }
        self.memory['approved'].append(approval_entry)
        self._update_accuracy_score()
        self.save_memory()
        print(f"✓ Output approved! Accuracy: {self.memory['accuracy_score']:.1%}")
    
    def reject_output(self, original, output, tone_mode):
        """User rejects the output - marks for improvement"""
        rejection_entry = {
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'output': output,
            'tone_mode': tone_mode,
            'needs_correction': True
        }
        self.memory['rejected'].append(rejection_entry)
        self._update_accuracy_score()
        self.save_memory()
        print(f"✗ Output rejected. Accuracy: {self.memory['accuracy_score']:.1%}")
        return rejection_entry
    

    
    def get_simple_correction(self, text, tone_mode):
        """Simple rule-based correction as fallback"""
        result = text
        
        # Basic tone transformations
        if tone_mode == 'formal':
            replacements = {
                'gotta': 'must',
                'wanna': 'want to',
                'gonna': 'going to',
                'yeah': 'yes',
                'nope': 'no',
                'hey': 'hello',
                'dude': 'sir/madam',
                'bruh': '',
                'kinda': 'somewhat',
                'sorta': 'somewhat'
            }
        elif tone_mode == 'casual':
            replacements = {
                'must': 'gotta',
                'want to': 'wanna',
                'going to': 'gonna'
            }
        else:
            replacements = {}
        
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result.strip()
    
    def auto_improve(self, original, wrong_output, tone_mode):
        """Automatically improve using rule-based corrections"""
        # Use simple rule-based correction
        print("🔧 Using rule-based auto-correction")
        simple_correction = self.get_simple_correction(original, tone_mode)
        
        if simple_correction != original:
            # Store the correction
            self.add_correction(original, wrong_output, simple_correction, tone_mode)
            print(f"🧠 Auto-learned: '{original}' → '{simple_correction}'")
            return simple_correction
        
        return None
    
    def _update_accuracy_score(self):
        """Calculate accuracy based on approvals vs rejections"""
        total_feedback = len(self.memory['approved']) + len(self.memory['rejected'])
        if total_feedback > 0:
            self.memory['accuracy_score'] = len(self.memory['approved']) / total_feedback
    
    def get_stats(self):
        """Get feedback statistics"""
        return {
            'total_corrections': len(self.memory['corrections']),
            'total_rules': len(self.memory['rules']),
            'active_rules': sum(1 for r in self.memory['rules'].values() if r['count'] >= 2),
            'approved': len(self.memory.get('approved', [])),
            'rejected': len(self.memory.get('rejected', [])),
            'accuracy': f"{self.memory.get('accuracy_score', 0) * 100:.1f}%"
        }
