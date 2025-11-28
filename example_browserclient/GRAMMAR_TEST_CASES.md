# Grammar Correction Test Cases

## Test Cases for Speech-to-Text Grammar Errors

### 1. Word Order Errors
**Common in STT when time expressions are misplaced**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "i have a tomorrow match" | "I have a match tomorrow." | Time word placement |
| "i have a today meeting" | "I have a meeting today." | Time word placement |
| "we have a tonight party" | "We have a party tonight." | Time word placement |
| "he go always to school" | "He always goes to school." | Adverb placement |

### 2. Article Errors (a/an)
**STT often gets articles wrong based on sound**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "this is a umbrella" | "This is an umbrella." | Wrong article before vowel |
| "this is an laptop" | "This is a laptop." | Wrong article before consonant |
| "i have a apple" | "I have an apple." | Wrong article before vowel |
| "she is an teacher" | "She is a teacher." | Wrong article before consonant |
| "i saw a elephant" | "I saw an elephant." | Wrong article before vowel |

### 3. Subject-Verb Agreement
**Common grammar mistakes in casual speech**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "he dont like it" | "He doesn't like it." | Wrong verb form |
| "she have a car" | "She has a car." | Wrong verb form |
| "they was going" | "They were going." | Wrong verb form |
| "he do his homework" | "He does his homework." | Wrong verb form |
| "it dont work" | "It doesn't work." | Wrong verb form |

### 4. Common Mistakes (could of, should of)
**Phonetic errors from STT**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "i could of done it" | "I could have done it." | "of" instead of "have" |
| "i should of known" | "I should have known." | "of" instead of "have" |
| "i would of gone" | "I would have gone." | "of" instead of "have" |
| "they might of left" | "They might have left." | "of" instead of "have" |

### 5. Homophones (your/you're, its/it's, there/their/they're)
**STT can't distinguish these by sound**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "your going home" | "You're going home." | your → you're |
| "its a nice day" | "It's a nice day." | its → it's |
| "their going away" | "They're going away." | their → they're |
| "there car is red" | "Their car is red." | there → their |
| "your the best" | "You're the best." | your → you're |

### 6. Tense Errors
**Mixing past/present/future incorrectly**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "i go yesterday" | "I went yesterday." | Wrong tense |
| "she see me tomorrow" | "She will see me tomorrow." | Wrong tense |
| "we was there" | "We were there." | Wrong tense |
| "he come here yesterday" | "He came here yesterday." | Wrong tense |

### 7. Double Negatives
**Common in casual speech**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "i dont have no money" | "I don't have any money." | Double negative |
| "i cant see nothing" | "I can't see anything." | Double negative |
| "he dont know nobody" | "He doesn't know anybody." | Double negative |

### 8. Preposition Errors
**Wrong preposition usage**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "different than you" | "Different from you." | Wrong preposition |
| "married with her" | "Married to her." | Wrong preposition |
| "in the weekend" | "On the weekend." | Wrong preposition |
| "good in math" | "Good at math." | Wrong preposition |

### 9. Capitalization Errors
**STT doesn't know proper capitalization**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "i went to paris" | "I went to Paris." | Missing capitals |
| "john and mary" | "John and Mary." | Missing capitals |
| "i love monday" | "I love Monday." | Missing capitals |
| "we met in january" | "We met in January." | Missing capitals |

### 10. Missing Punctuation
**STT often omits punctuation**

| Input | Expected Output | Error Type |
|-------|----------------|------------|
| "hello how are you" | "Hello, how are you?" | Missing punctuation |
| "yes i can do it" | "Yes, I can do it." | Missing punctuation |
| "wait what happened" | "Wait, what happened?" | Missing punctuation |

## Quick Test Script

Run these test cases:

```bash
cd example_browserclient
python test_finetuned_model.py
```

Or test interactively:

```bash
python test_finetuned_model.py --interactive
```

## Testing in the Web Interface

1. Open http://localhost:8080
2. Click "Start Recording"
3. Speak these test phrases:
   - "i have a tomorrow match"
   - "he dont like it"
   - "this is a umbrella"
   - "i could of done it"
   - "your going home"

4. Watch the corrections in real-time!

## Expected Behavior

- **Rule-based corrections**: Fast (<5ms), handles common patterns
- **Model corrections**: Slower (~140ms), attempts complex fixes
- **Hybrid mode**: Tries model first, falls back to rules if needed

## Performance Metrics

Current system performance:
- **Latency**: <1.5s total (STT + grammar + formatting)
- **Grammar correction**: 100-200ms (model) or <5ms (rules)
- **Accuracy**: Depends on error type and model training
