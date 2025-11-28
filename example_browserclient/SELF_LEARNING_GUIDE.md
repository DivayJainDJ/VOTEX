# Self-Learning System Guide

## Overview
The system now has **approve/reject feedback** with **ChatGPT auto-improvement** to continuously learn and improve accuracy.

---

## How It Works

### 1. **After Each Transcription**
You see two buttons:
- **👍 Good Output** - Approve the result
- **👎 Wrong Output** - Reject and correct

### 2. **Approve Flow** (Good Output)
```
User clicks "👍 Good Output"
    ↓
System records approval
    ↓
Accuracy score increases
    ↓
Current behavior is reinforced
```

### 3. **Reject Flow** (Wrong Output)
```
User clicks "👎 Wrong Output"
    ↓
System records rejection
    ↓
Correction interface appears
    ↓
User has 2 options:
    ├─ 🤖 Auto-Fix (ChatGPT)
    └─ ✏️ Manual correction
```

### 4. **Auto-Fix with ChatGPT**
```
User clicks "🤖 Auto-Fix"
    ↓
System sends to ChatGPT API
    ↓
ChatGPT provides correction
    ↓
System learns automatically
    ↓
Rule is stored for future use
```

### 5. **Manual Correction**
```
User types correction
    ↓
Clicks "✓ Submit"
    ↓
System extracts rules
    ↓
Learns from correction
```

---

## Setup

### Enable ChatGPT Auto-Improvement

#### Option 1: Environment Variable (Recommended)
```bash
# Windows
set OPENAI_API_KEY=sk-your-api-key-here
python server.py

# Linux/Mac
export OPENAI_API_KEY=sk-your-api-key-here
python server.py
```

#### Option 2: Create .env file
```bash
# Create .env file in example_browserclient folder
echo OPENAI_API_KEY=sk-your-api-key-here > .env
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

---

## User Interface

### After Transcription:
```
┌─────────────────────────────────────┐
│  📝 Final Output                    │
│  "I gotta go to the store."        │
│  ⏱️ Latency: 5ms                   │
│                                     │
│  [👍 Good Output] [👎 Wrong Output]│
└─────────────────────────────────────┘
```

### After Rejection:
```
┌─────────────────────────────────────┐
│  ✏️ Provide Correction:             │
│  ┌─────────────────────────────┐   │
│  │ I need to go to the store.  │   │
│  └─────────────────────────────┘   │
│  [✓ Submit] [🤖 Auto-Fix] [✕ Cancel]│
│                                     │
│  📊 Accuracy: 85.2% | Approved: 23 │
│      Rejected: 4 | Active rules: 12│
└─────────────────────────────────────┘
```

---

## Example Workflows

### Workflow 1: Approve Good Output
1. Say: "Hello, how are you?"
2. System outputs: "Hello, how are you?"
3. Click: **👍 Good Output**
4. Result: Accuracy increases, behavior reinforced

### Workflow 2: Reject and Auto-Fix
1. Say: "I gotta bounce"
2. System outputs: "I gotta bounce."
3. Click: **👎 Wrong Output**
4. Click: **🤖 Auto-Fix**
5. ChatGPT suggests: "I need to leave."
6. System learns automatically
7. Next time: "I gotta bounce" → "I need to leave."

### Workflow 3: Reject and Manual Correct
1. Say: "Bruh I'm tired"
2. System outputs: "Bruh I'm tired."
3. Click: **👎 Wrong Output**
4. Type: "I am feeling exhausted."
5. Click: **✓ Submit**
6. System learns the correction

---

## Learning Mechanisms

### 1. **Exact Match Learning**
- Stores complete phrase corrections
- Instant recall on exact match
- Fastest learning method

### 2. **Rule Extraction**
- Identifies word-level patterns
- Requires 2+ examples to activate
- Applies across similar phrases

### 3. **Reinforcement Learning**
- Approvals strengthen current behavior
- Rejections mark areas for improvement
- Accuracy score tracks performance

### 4. **ChatGPT Integration**
- Provides intelligent corrections
- Learns from AI suggestions
- Reduces manual correction effort

---

## Accuracy Tracking

### Metrics Displayed:
- **Accuracy**: % of approved outputs
- **Approved**: Total good outputs
- **Rejected**: Total wrong outputs
- **Active Rules**: Rules with 2+ examples

### Formula:
```
Accuracy = Approved / (Approved + Rejected) × 100%
```

### Example:
```
Approved: 85
Rejected: 15
Accuracy: 85 / (85 + 15) = 85%
```

---

## Data Storage

### Files Created:
1. **feedback_memory.json** - All learning data
2. **transcription_log.csv** - Transcription history

### feedback_memory.json Structure:
```json
{
  "corrections": [
    {
      "timestamp": "2025-11-28T05:00:00",
      "original": "I gotta go",
      "system_output": "I gotta go.",
      "user_correction": "I need to leave.",
      "tone_mode": "neutral"
    }
  ],
  "rules": {
    "gotta→need:neutral": {
      "count": 2,
      "examples": [...]
    }
  },
  "approved": [...],
  "rejected": [...],
  "accuracy_score": 0.85
}
```

---

## Advanced Features

### Tone-Specific Learning
- Each tone mode learns independently
- Formal corrections don't affect casual
- Allows context-appropriate responses

### Continuous Improvement
- System gets better with each feedback
- Rules accumulate over time
- Accuracy increases automatically

### Smart Fallbacks
- If ChatGPT unavailable, manual correction works
- If no API key, system still learns from manual input
- Graceful degradation

---

## Best Practices

### 1. **Be Consistent**
- Use same corrections for same errors
- Helps system learn patterns faster

### 2. **Approve Good Outputs**
- Don't just correct errors
- Approvals are equally important

### 3. **Use Auto-Fix**
- Saves time on complex corrections
- ChatGPT provides high-quality suggestions

### 4. **Check Stats**
- Monitor accuracy over time
- See which rules are active

### 5. **Restart Periodically**
- Verify persistence works
- Check learned behaviors

---

## Troubleshooting

### ChatGPT Not Working?
```
Check:
1. OPENAI_API_KEY is set correctly
2. API key is valid and has credits
3. Internet connection is active
4. Server logs show "ChatGPT enabled"
```

### Corrections Not Applying?
```
Check:
1. Need 2+ examples for rule activation
2. Exact phrase match for instant recall
3. Tone mode matches original
4. feedback_memory.json is being updated
```

### Low Accuracy?
```
Solutions:
1. Approve more good outputs
2. Provide consistent corrections
3. Use Auto-Fix for better suggestions
4. Review rejected outputs
```

---

## API Costs (ChatGPT)

### Estimated Costs:
- **GPT-3.5-turbo**: ~$0.001 per correction
- **100 corrections**: ~$0.10
- **1000 corrections**: ~$1.00

### Cost Optimization:
- Use manual corrections when possible
- Auto-Fix only for complex cases
- Approve good outputs (free)

---

## Future Enhancements

### Planned Features:
1. ✅ Approve/Reject buttons
2. ✅ ChatGPT auto-improvement
3. ✅ Accuracy tracking
4. 🔄 Batch learning from history
5. 🔄 Export/import learned rules
6. 🔄 A/B testing different models
7. 🔄 Community rule sharing

---

## Success Metrics

### After 100 Interactions:
- Accuracy: 70-80%
- Active Rules: 15-25
- Instant Corrections: 30-40%

### After 500 Interactions:
- Accuracy: 85-90%
- Active Rules: 50-75
- Instant Corrections: 60-70%

### After 1000 Interactions:
- Accuracy: 90-95%
- Active Rules: 100-150
- Instant Corrections: 80-90%

---

## Summary

The self-learning system:
- ✅ Learns from every interaction
- ✅ Gets smarter over time
- ✅ Reduces manual corrections
- ✅ Tracks accuracy automatically
- ✅ Uses AI for intelligent suggestions
- ✅ Persists across sessions
- ✅ Adapts to your preferences

**Start using it now and watch it improve!**
