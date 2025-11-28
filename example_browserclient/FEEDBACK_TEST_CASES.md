# Feedback System Test Cases

## Test Case 1: Basic Correction Learning
**Objective:** Verify system learns from a single correction

### Steps:
1. **Say:** "I gotta go to the store"
2. **System outputs:** "I gotta go to the store."
3. **Click:** "✏️ Correct This" button
4. **Edit to:** "I need to go to the store."
5. **Click:** "✓ Submit"
6. **Verify:** Stats show "Total corrections: 1"

### Expected Result:
- Feedback stored in `feedback_memory.json`
- Stats display updates

---

## Test Case 2: Rule Extraction (Single Word)
**Objective:** Verify system extracts word-level rules

### Steps:
1. **Say:** "I wanna eat pizza"
2. **System outputs:** "I wanna eat pizza."
3. **Correct to:** "I want to eat pizza."
4. **Submit feedback**
5. **Say again:** "I wanna sleep"
6. **System outputs:** "I wanna sleep."
7. **Correct to:** "I want to sleep."
8. **Submit feedback**

### Expected Result:
- After 2nd correction, rule "wanna→want to" is created
- Stats show "Active rules: 1"
- Next time you say "wanna", it auto-corrects to "want to"

---

## Test Case 3: Exact Match Learning
**Objective:** Verify system remembers exact phrase corrections

### Steps:
1. **Say:** "Bruh I'm tired"
2. **System outputs:** "Bruh I'm tired."
3. **Correct to:** "I am feeling exhausted."
4. **Submit feedback**
5. **Say again:** "Bruh I'm tired"

### Expected Result:
- System immediately outputs: "I am feeling exhausted."
- Status shows: "🧠 Used learned correction"
- Latency is very low (< 10ms) since it skips processing

---

## Test Case 4: Tone-Specific Learning
**Objective:** Verify corrections are tone-specific

### Steps:
1. **Set tone:** Formal
2. **Say:** "Hey dude"
3. **System outputs:** "Hello."
4. **Correct to:** "Good day, sir."
5. **Submit feedback**
6. **Change tone:** Casual
7. **Say:** "Hey dude"
8. **System outputs:** "Hey dude." (different from formal)

### Expected Result:
- Formal tone uses "Good day, sir."
- Casual tone uses original processing
- Corrections are tone-specific

---

## Test Case 5: Multiple Rules Accumulation
**Objective:** Verify multiple rules work together

### Steps:
1. Teach: "gonna" → "going to" (2 examples)
2. Teach: "wanna" → "want to" (2 examples)
3. Teach: "gotta" → "have to" (2 examples)
4. **Say:** "I gonna wanna gotta go"

### Expected Result:
- All three rules apply
- Output: "I going to want to have to go"
- Stats show "Active rules: 3"

---

## Test Case 6: Feedback Stats Tracking
**Objective:** Verify stats are accurate

### Steps:
1. Submit 5 different corrections
2. Check stats display

### Expected Result:
- "Total corrections: 5"
- "Active rules: X" (depends on repeated patterns)

---

## Test Case 7: Persistence Across Sessions
**Objective:** Verify feedback persists after restart

### Steps:
1. Submit correction: "yeah" → "yes"
2. **Stop server** (Ctrl+C)
3. **Restart server**
4. **Say:** "yeah"

### Expected Result:
- Server loads: "📊 Feedback stats: {'total_corrections': 1, ...}"
- Learned correction still applies

---

## Test Case 8: Visual Feedback
**Objective:** Verify UI updates correctly

### Steps:
1. Complete a transcription
2. Observe UI elements

### Expected Result:
- "✏️ Correct This" button appears
- Click shows input field with current text
- Submit shows success message
- Stats update in real-time

---

## Quick Test Script

### Minimal Test (2 minutes):
```
1. Say: "I gotta go"
2. Correct to: "I must leave"
3. Say: "I gotta go" again
4. Verify: Shows "🧠 Used learned correction"
```

### Full Test (5 minutes):
```
1. Test 3 different corrections
2. Verify stats update
3. Test exact match (Test Case 3)
4. Test rule extraction (Test Case 2)
5. Restart server and verify persistence
```

---

## Debugging

### Check feedback_memory.json:
```json
{
  "corrections": [
    {
      "timestamp": "2025-11-28T04:45:00",
      "original": "I gotta go",
      "system_output": "I gotta go.",
      "user_correction": "I must leave",
      "tone_mode": "neutral"
    }
  ],
  "rules": {
    "gotta→must:neutral": {
      "count": 1,
      "examples": [...]
    }
  }
}
```

### Check server logs:
- Look for: "✓ Feedback stored: X total corrections"
- Look for: "🧠 Using learned correction: ..."

### Check browser console:
- Should see: "Tone changed to: X"
- Should see: "Received: feedback_received"

---

## Expected Behavior Summary

| Action | Expected Result |
|--------|----------------|
| First correction | Stored, no auto-apply yet |
| Second same correction | Rule created (if word-level match) |
| Exact phrase repeat | Instant learned output |
| Different tone | Separate learning |
| Server restart | All corrections persist |
| Stats display | Real-time updates |

---

## Known Limitations

1. **Rule threshold:** Needs 2+ examples to create active rule
2. **Word-level only:** Only extracts simple word replacements
3. **Case sensitive:** "Gotta" vs "gotta" treated differently
4. **No phrase patterns:** Doesn't learn complex transformations yet

---

## Success Criteria

✅ Corrections are stored in JSON file
✅ Stats display updates correctly
✅ Exact matches return learned output instantly
✅ Rules apply after 2+ examples
✅ Feedback persists across restarts
✅ UI shows "🧠 Used learned correction" status
✅ Processing is skipped for learned outputs (< 10ms latency)
