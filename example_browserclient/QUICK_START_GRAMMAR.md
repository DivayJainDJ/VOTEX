# Quick Start: Grammar Correction

## ✅ Integration Complete

The fine-tuned T5 grammar model is now integrated into your RealtimeSTT system.

## 🚀 How to Use

### Start the Server
```bash
cd example_browserclient
python server.py
```

The server automatically detects and uses the hybrid grammar processor (model + rules).

### Test the Model
```bash
# Test the fine-tuned model alone
python test_finetuned_model.py

# Test integration (rule-based vs hybrid)
python test_integration.py
```

## 📊 Current Status

✅ **Integrated**: Model is loaded and available  
✅ **Fallback**: Rule-based processor as backup  
⚠️ **Accuracy**: 11.8% (model needs more training)  
✅ **Speed**: ~140ms with model, <5ms with rules  

## 🔧 Configuration Options

### Use Model + Rules (Default)
```python
from grammar_processor_hybrid import HybridGrammarProcessor
grammar = HybridGrammarProcessor(use_model=True)
```

### Use Rules Only (Faster)
```python
from grammar_processor import GrammarProcessor
grammar = GrammarProcessor()
```

### Adjust Timeout
```python
# Give model 0.5s before falling back to rules
corrected = grammar.correct_text(text, timeout=0.5)
```

## 🎯 What Works Now

### Rule-Based Corrections (Fast & Reliable)
- ✅ "could of" → "could have"
- ✅ Capitalization (first letter, "I")
- ✅ Basic punctuation
- ✅ Common contractions

### Model-Based Corrections (Needs Improvement)
- ⚠️ Limited accuracy (11.8%)
- ⚠️ Sometimes outputs "grammar:" prefix
- ✅ Fast inference (~140ms)
- ✅ Automatic fallback to rules

## 🔄 Improving the Model

To improve accuracy, retrain with more data:

1. Open `Fine_Tune_T5_Grammar_Correction.ipynb` in Google Colab
2. Expand training data (add 100+ examples)
3. Train for more epochs (20-30)
4. Download and replace `grammar-correction-model/`

## 📝 Example Usage

```python
from grammar_processor_hybrid import HybridGrammarProcessor

# Initialize
grammar = HybridGrammarProcessor()

# Correct text
text = "i have a tomorrow match"
corrected = grammar.correct_text(text)
print(corrected)  # Falls back to rules if model fails

# Check stats
print(grammar.get_stats())
# {'model_available': True, 'device': 'cpu', ...}
```

## 🐛 Troubleshooting

### Model not loading?
- Check if `transformers` is installed: `pip install transformers torch`
- System will automatically fall back to rule-based

### Slow performance?
- Reduce timeout: `grammar.correct_text(text, timeout=0.3)`
- Or use rule-based only: `GrammarProcessor()`

### Poor accuracy?
- Model needs retraining with more data
- Use rule-based processor for now (reliable for common errors)

## 📚 Files Reference

- `grammar_processor.py` - Rule-based (original)
- `grammar_processor_hybrid.py` - Model + Rules (new)
- `test_finetuned_model.py` - Test model accuracy
- `test_integration.py` - Compare approaches
- `server.py` - Main server (auto-uses hybrid)
- `GRAMMAR_MODEL_INTEGRATION.md` - Full documentation
