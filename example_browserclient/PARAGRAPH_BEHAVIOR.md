# Paragraph Detection - Correct Behavior

## ✅ How It Actually Works

### Silence Thresholds

| Silence Duration | What Happens | Recording Status |
|-----------------|--------------|------------------|
| **< 2 seconds** | Continue speaking | ✅ Recording active |
| **= 2 seconds** | **Paragraph break** (`\n\n`) | ✅ **Recording continues** |
| **= 5 seconds** | **End transcription** | ❌ **Recording stops**, text processed |

## Key Concept

**2 seconds = Paragraph break, NOT end of transcription**
- System adds `\n\n` (double newline)
- Recording **continues**
- You can keep speaking

**5 seconds = End of transcription**
- Recording **stops**
- Text is processed through pipeline
- Final output sent to client

## Example Usage

### Scenario 1: Multi-Paragraph Dictation

**You speak:**
```
"First paragraph here"
(pause 2 seconds)
"Second paragraph here"
(pause 2 seconds)  
"Third paragraph here"
(pause 5 seconds - done!)
```

**System behavior:**
1. Records "First paragraph here"
2. Detects 2s pause → adds `\n\n`, **keeps recording**
3. Records "Second paragraph here"
4. Detects 2s pause → adds `\n\n`, **keeps recording**
5. Records "Third paragraph here"
6. Detects 5s pause → **stops recording**, processes

**Final output:**
```
First paragraph here.

Second paragraph here.

Third paragraph here.
```

### Scenario 2: Quick Dictation

**You speak:**
```
"Just one paragraph"
(pause 5 seconds)
```

**System behavior:**
1. Records "Just one paragraph"
2. Detects 5s pause → **stops recording**, processes

**Final output:**
```
Just one paragraph.
```

## Technical Implementation

### Realtime Transcription
- Enabled with `enable_realtime_transcription: True`
- Callback: `on_realtime_transcription_update()`
- Detects 2-second pauses during recording
- Adds paragraph breaks in real-time

### End Transcription
- Configured with `post_speech_silence_duration: 5.0`
- After 5 seconds of silence, recording stops
- Text goes through full processing pipeline

## Configuration

### Current Settings (server.py)

```python
recorder_config = {
    'post_speech_silence_duration': 5.0,  # 5s to end transcription
    'enable_realtime_transcription': True,  # For 2s paragraph detection
    'on_realtime_transcription_update': on_realtime_transcription_update,
    ...
}
```

### Adjusting Thresholds

**To change end transcription time:**
```python
'post_speech_silence_duration': 3.0,  # End after 3 seconds
```

**To change paragraph break time:**
- Currently hardcoded at 2 seconds in realtime callback
- Modify `on_realtime_transcription_update()` function

## Benefits

1. **Long-form dictation** - Speak multiple paragraphs without stopping
2. **Natural pauses** - 2 seconds is natural paragraph break timing
3. **Clear ending** - 5 seconds clearly signals "I'm done"
4. **Real-time feedback** - See paragraphs form as you speak

## Testing

### Test in Browser
1. Open http://localhost:8080
2. Click "Start Recording"
3. Say: "First paragraph" → pause 2s
4. Say: "Second paragraph" → pause 2s
5. Say: "Third paragraph" → pause 5s
6. Watch the output with paragraph breaks!

### Expected Behavior
- After each 2s pause: New paragraph appears, mic still active
- After 5s pause: Recording stops, text processed

## Comparison

### ❌ OLD (Incorrect)
- 2s = sentence ending (`. `)
- 5s = paragraph break (`\n\n`)
- Recording stops after any pause

### ✅ NEW (Correct)
- 2s = paragraph break (`\n\n`), **keep recording**
- 5s = end transcription, **stop recording**
- Can dictate multiple paragraphs in one session

## Visual Timeline

```
User: "Para 1"  [2s pause]  "Para 2"  [2s pause]  "Para 3"  [5s pause]
      ↓                     ↓                     ↓          ↓
      Recording...          Still recording...    Still...   STOP!
      ↓                     ↓                     ↓          ↓
      Text: "Para 1"        "Para 1\n\nPara 2"   "...\n\nPara 3"  → Process
```

## Status

✅ Implemented  
✅ Server running  
✅ Realtime transcription enabled  
✅ Paragraph breaks at 2s  
✅ End transcription at 5s  

Ready to use!
