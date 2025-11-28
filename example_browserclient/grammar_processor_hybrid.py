"""
Hybrid Grammar Processor - Combines fine-tuned T5 model with rule-based fallback
Optimized for speed and accuracy
"""

import re
import time
from typing import Optional
from grammar_processor import GrammarProcessor

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available, using rule-based only")


class HybridGrammarProcessor:
    """
    Hybrid grammar correction combining:
    1. Fine-tuned T5 model (primary, high accuracy)
    2. Rule-based processor (fallback, fast)
    """
    
    def __init__(self, model_path="../grammar-correction-model", use_model=True):
        """
        Initialize hybrid processor
        
        Args:
            model_path: Path to fine-tuned model
            use_model: Whether to use ML model (False = rule-based only)
        """
        print("Initializing Hybrid Grammar Processor...")
        
        # Always initialize rule-based processor (fallback)
        self.rule_based = GrammarProcessor()
        
        # Try to load ML model
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self.model_available = False
        
        if use_model and TRANSFORMERS_AVAILABLE:
            try:
                print(f"Loading fine-tuned model from {model_path}...")
                start = time.time()
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
                
                # Use GPU if available
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model.to(self.device)
                self.model.eval()
                
                self.model_available = True
                load_time = time.time() - start
                print(f"✓ Model loaded in {load_time:.2f}s on {self.device}")
                
            except Exception as e:
                print(f"✗ Could not load model: {e}")
                print("✓ Falling back to rule-based processor")
        else:
            print("✓ Using rule-based processor only")
    
    def correct_with_model(self, text: str, max_length: int = 128) -> Optional[str]:
        """
        Correct using fine-tuned model
        
        Returns:
            Corrected text or None if model unavailable/fails
        """
        if not self.model_available or not text:
            return None
        
        try:
            input_text = "grammar: " + text
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=max_length,
                truncation=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=2,  # Reduced for speed
                    early_stopping=True,
                    no_repeat_ngram_size=2
                )
            
            corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up output - remove "grammar:" prefix if present
            if corrected.startswith("grammar:"):
                corrected = corrected[8:].strip()
            corrected = re.sub(r'^grammar\s+', '', corrected)
            
            return corrected
            
        except Exception as e:
            print(f"Model correction failed: {e}")
            return None
    
    def correct_text(self, text: str, timeout: float = 1.0) -> str:
        """
        Correct text using hybrid approach with timeout
        
        Args:
            text: Input text with potential errors
            timeout: Max time for model correction (seconds)
            
        Returns:
            Corrected text
        """
        if not text or len(text.strip()) == 0:
            return text
        
        # Try model first (if available)
        if self.model_available:
            start = time.time()
            corrected = self.correct_with_model(text)
            elapsed = time.time() - start
            
            if corrected and elapsed < timeout:
                # Model succeeded within timeout
                return corrected
            elif elapsed >= timeout:
                print(f"Model timeout ({elapsed:.2f}s), using rule-based")
        
        # Fallback to rule-based
        return self.rule_based.correct_text(text)
    
    def get_stats(self) -> dict:
        """Get processor statistics"""
        return {
            "model_available": self.model_available,
            "device": self.device,
            "rule_based_available": True,
            "transformers_installed": TRANSFORMERS_AVAILABLE
        }


# Example usage and comparison
if __name__ == "__main__":
    print("="*70)
    print("HYBRID GRAMMAR PROCESSOR - COMPARISON TEST")
    print("="*70)
    print()
    
    # Initialize processors
    hybrid = HybridGrammarProcessor(use_model=True)
    rule_based = GrammarProcessor()
    
    print(f"\nProcessor stats: {hybrid.get_stats()}\n")
    
    # Test cases
    test_cases = [
        "i have a tomorrow match",
        "he dont like it",
        "this is a umbrella",
        "i could of done it",
        "she have a car",
        "your going home",
        "i go yesterday",
        "i dont have no money",
    ]
    
    print("Comparing corrections:\n")
    
    for text in test_cases:
        print(f"Original:    '{text}'")
        
        # Rule-based
        start = time.time()
        rule_result = rule_based.correct_text(text)
        rule_time = time.time() - start
        print(f"Rule-based:  '{rule_result}' ({rule_time:.3f}s)")
        
        # Hybrid (model + fallback)
        start = time.time()
        hybrid_result = hybrid.correct_text(text)
        hybrid_time = time.time() - start
        print(f"Hybrid:      '{hybrid_result}' ({hybrid_time:.3f}s)")
        
        print()
