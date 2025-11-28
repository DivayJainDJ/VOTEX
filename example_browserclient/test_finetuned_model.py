"""
Test script for the fine-tuned T5 grammar correction model
Tests the model with various grammar errors and compares with rule-based approach
"""

import sys
import time
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class FineTunedGrammarCorrector:
    def __init__(self, model_path="../grammar-correction-model"):
        """Initialize the fine-tuned T5 model"""
        print(f"Loading fine-tuned model from {model_path}...")
        start_time = time.time()
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            
            # Move to GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()
            
            load_time = time.time() - start_time
            print(f"✓ Model loaded successfully in {load_time:.2f}s")
            print(f"✓ Using device: {self.device}")
            
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            raise
    
    def correct_text(self, text: str, max_length: int = 128) -> str:
        """
        Correct grammar using the fine-tuned model
        
        Args:
            text: Input text with grammar errors
            max_length: Maximum output length
            
        Returns:
            Corrected text
        """
        if not text or len(text.strip()) == 0:
            return text
        
        try:
            # Add T5 prefix
            input_text = "grammar: " + text
            
            # Tokenize
            inputs = self.tokenizer(
                input_text, 
                return_tensors="pt",
                max_length=max_length,
                truncation=True
            ).to(self.device)
            
            # Generate correction
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=4,  # Beam search for better quality
                    early_stopping=True,
                    no_repeat_ngram_size=2  # Prevent repetition
                )
            
            # Decode
            corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up output - remove any "grammar:" prefix that leaked through
            if corrected.startswith("grammar:"):
                corrected = corrected[8:].strip()
            # Remove standalone "grammar" word if it appears
            corrected = re.sub(r'^grammar\s+', '', corrected)
            
            return corrected
            
        except Exception as e:
            print(f"Error during correction: {e}")
            return text


def run_tests():
    """Run comprehensive tests on the fine-tuned model"""
    
    print("="*70)
    print("FINE-TUNED T5 GRAMMAR CORRECTION MODEL - TEST SUITE")
    print("="*70)
    print()
    
    # Initialize model
    try:
        corrector = FineTunedGrammarCorrector()
    except Exception as e:
        print(f"Failed to initialize model: {e}")
        return
    
    # Test cases from the training notebook
    test_cases = [
        # Word order errors
        ("i have a tomorrow match", "i have a match tomorrow"),
        ("i have a today meeting", "i have a meeting today"),
        ("i have a tonight party", "i have a party tonight"),
        
        # Article errors
        ("this is a umbrella", "this is an umbrella"),
        ("this is an laptop", "this is a laptop"),
        ("i have a apple", "i have an apple"),
        
        # Subject-verb agreement
        ("he dont like it", "he doesn't like it"),
        ("she have a car", "she has a car"),
        ("they was going", "they were going"),
        
        # Common mistakes
        ("i could of done it", "i could have done it"),
        ("i should of known", "i should have known"),
        ("your going home", "you're going home"),
        
        # Tense errors
        ("i go yesterday", "i went yesterday"),
        ("we was there", "we were there"),
        
        # Other errors
        ("i dont have no money", "i don't have any money"),
        ("he go always to school", "he always goes to school"),
        ("she is more better", "she is better"),
    ]
    
    print("\nRunning tests...\n")
    
    correct_count = 0
    total_time = 0
    
    for i, (incorrect, expected) in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}")
        print(f"  Input:    '{incorrect}'")
        print(f"  Expected: '{expected}'")
        
        # Time the correction
        start = time.time()
        result = corrector.correct_text(incorrect)
        elapsed = time.time() - start
        total_time += elapsed
        
        print(f"  Output:   '{result}'")
        print(f"  Time:     {elapsed:.3f}s")
        
        # Check if correct
        is_correct = result.strip().lower() == expected.strip().lower()
        if is_correct:
            print("  Status:   ✓ PASS")
            correct_count += 1
        else:
            print("  Status:   ✗ FAIL")
        
        print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests:     {len(test_cases)}")
    print(f"Passed:          {correct_count}")
    print(f"Failed:          {len(test_cases) - correct_count}")
    print(f"Accuracy:        {correct_count/len(test_cases)*100:.1f}%")
    print(f"Avg time/test:   {total_time/len(test_cases):.3f}s")
    print(f"Total time:      {total_time:.2f}s")
    print("="*70)


def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*70)
    print("INTERACTIVE MODE")
    print("="*70)
    print("Enter text to correct (or 'quit' to exit)\n")
    
    corrector = FineTunedGrammarCorrector()
    
    while True:
        try:
            text = input("Input: ").strip()
            if text.lower() in ['quit', 'exit', 'q']:
                break
            
            if not text:
                continue
            
            start = time.time()
            corrected = corrector.correct_text(text)
            elapsed = time.time() - start
            
            print(f"Output: {corrected}")
            print(f"Time: {elapsed:.3f}s\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}\n")
    
    print("Goodbye!")


if __name__ == "__main__":
    # Run automated tests
    run_tests()
    
    # Optionally run interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()
