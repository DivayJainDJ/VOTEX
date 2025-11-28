/**
 * Text Enhancement JavaScript Bridge
 * 
 * This module provides a JavaScript wrapper for the existing disfluency_filter.py functionality,
 * implementing text processing pipeline using existing grammar correction and ensuring
 * enhanced text output matches existing component behavior.
 * 
 * Requirements: 1.2, 2.4
 */

class TextEnhancementBridge {
  constructor(options = {}) {
    // Configuration options
    this.options = {
      enableDisfluencyFilter: options.enableDisfluencyFilter !== false,
      enableGrammarCorrection: options.enableGrammarCorrection !== false,
      enableCapitalization: options.enableCapitalization !== false,
      enablePunctuation: options.enablePunctuation !== false,
      ...options
    };

    // Filler words and disfluencies (matching the Python implementation)
    this.fillers = new Set([
      'umm', 'uhh', 'ehh', 'uh', 'um', 'er', 'ah', 'oh',
      'you know', 'like', 'so', 'well', 'actually', 'basically',
      'literally', 'totally', 'really', 'very', 'just', 'kind of',
      'sort of', 'i mean', 'you see', 'right', 'okay', 'alright'
    ]);

    // Pattern for repeated words (stuttering) - matches Python regex
    this.stutterPattern = /\b(\w+)(\s+\1){2,}\b/gi;

    // Common grammar correction patterns
    this.grammarPatterns = [
      // Basic contractions
      { pattern: /\bi am\b/gi, replacement: "I'm" },
      { pattern: /\byou are\b/gi, replacement: "you're" },
      { pattern: /\bhe is\b/gi, replacement: "he's" },
      { pattern: /\bshe is\b/gi, replacement: "she's" },
      { pattern: /\bit is\b/gi, replacement: "it's" },
      { pattern: /\bwe are\b/gi, replacement: "we're" },
      { pattern: /\bthey are\b/gi, replacement: "they're" },
      
      // Common word corrections
      { pattern: /\bwanna\b/gi, replacement: "want to" },
      { pattern: /\bgonna\b/gi, replacement: "going to" },
      { pattern: /\bkinda\b/gi, replacement: "kind of" },
      { pattern: /\bsorta\b/gi, replacement: "sort of" },
      
      // Double negatives (basic cases)
      { pattern: /\bdon't have no\b/gi, replacement: "don't have any" },
      { pattern: /\bcan't get no\b/gi, replacement: "can't get any" },
      
      // Subject-verb agreement (basic cases)
      { pattern: /\bi was\b/gi, replacement: "I was" },
      { pattern: /\byou was\b/gi, replacement: "you were" },
      { pattern: /\bwe was\b/gi, replacement: "we were" },
      { pattern: /\bthey was\b/gi, replacement: "they were" }
    ];

    // Callbacks
    this.onTextProcessed = options.onTextProcessed || null;
    this.onError = options.onError || null;
  }

  /**
   * Main text enhancement method that applies all enabled filters
   * Matches the behavior of the existing disfluency_filter.py clean_text method
   */
  enhanceText(text) {
    try {
      if (!text || typeof text !== 'string') {
        return '';
      }

      let enhancedText = text;

      // Apply disfluency filtering (matches Python implementation order)
      if (this.options.enableDisfluencyFilter) {
        // Remove stutters first (matches Python order)
        enhancedText = this.removeStutters(enhancedText);
        if (typeof enhancedText !== 'string') {
          enhancedText = text; // fallback to original
        }
        
        // Remove fillers
        enhancedText = this.removeFillers(enhancedText);
        if (typeof enhancedText !== 'string') {
          enhancedText = text; // fallback to original
        }
      }

      // Apply grammar corrections
      if (this.options.enableGrammarCorrection) {
        enhancedText = this.applyGrammarCorrections(enhancedText);
        if (typeof enhancedText !== 'string') {
          enhancedText = text; // fallback to original
        }
      }

      // Clean up extra spaces (matches Python implementation)
      if (typeof enhancedText === 'string') {
        enhancedText = enhancedText.replace(/\s+/g, ' ').trim();
      } else {
        enhancedText = text; // fallback to original
      }

      // Apply capitalization and punctuation
      if (this.options.enableCapitalization || this.options.enablePunctuation) {
        enhancedText = this.applyCapitalizationAndPunctuation(enhancedText);
      }

      // Notify callback if provided
      if (this.onTextProcessed) {
        this.onTextProcessed(enhancedText, text);
      }

      return enhancedText;

    } catch (error) {
      console.error('Error enhancing text:', error);
      if (this.onError) {
        this.onError('Text enhancement failed: ' + error.message);
      }
      return text; // Return original text on error
    }
  }

  /**
   * Remove filler words and phrases
   * Matches the Python remove_fillers method behavior
   */
  removeFillers(text) {
    try {
      if (!text || typeof text !== 'string') {
        return text || '';
      }
      
      // Validate input length to prevent performance issues
      if (text.length > 10000) {
        console.warn('Text too long for filler removal, truncating');
        text = text.substring(0, 10000);
      }
      
      const originalWords = text.split(/\s+/);
      const lowerWords = text.toLowerCase().split(/\s+/);
      const filtered = [];
      let i = 0;

      // Add timeout protection for very long texts
      const startTime = Date.now();
      const maxProcessingTime = 5000; // 5 seconds max

      while (i < lowerWords.length) {
        // Check for timeout
        if (Date.now() - startTime > maxProcessingTime) {
          console.warn('Filler removal timeout, returning partial result');
          // Add remaining words without processing
          filtered.push(...originalWords.slice(i));
          break;
        }
        
        let foundFiller = false;

        // Check for multi-word fillers (sorted by length, longest first)
        const sortedFillers = Array.from(this.fillers).sort((a, b) => b.length - a.length);
        
        for (const filler of sortedFillers) {
          const fillerWords = filler.split(' ');
          
          if (i + fillerWords.length <= lowerWords.length) {
            const wordSequence = lowerWords.slice(i, i + fillerWords.length).join(' ');
            
            if (wordSequence === filler) {
              i += fillerWords.length;
              foundFiller = true;
              break;
            }
          }
        }

        if (!foundFiller) {
          filtered.push(originalWords[i]); // Use original case
          i++;
        }
      }

      return filtered.join(' ');
    } catch (error) {
      console.error('Error in removeFillers:', error);
      if (this.onError) {
        this.onError('Filler removal failed: ' + error.message);
      }
      return text; // Return original text on error
    }
  }

  /**
   * Remove stuttering (repeated words)
   * Matches the Python remove_stutters method behavior
   */
  removeStutters(text) {
    try {
      if (!text || typeof text !== 'string') {
        return text || '';
      }
      
      // Validate input length
      if (text.length > 10000) {
        console.warn('Text too long for stutter removal, truncating');
        text = text.substring(0, 10000);
      }
      
      return text.replace(this.stutterPattern, '$1');
    } catch (error) {
      console.error('Error in removeStutters:', error);
      if (this.onError) {
        this.onError('Stutter removal failed: ' + error.message);
      }
      return text; // Return original text on error
    }
  }

  /**
   * Apply grammar corrections using pattern matching
   */
  applyGrammarCorrections(text) {
    try {
      if (!text || typeof text !== 'string') {
        return text || '';
      }
      
      // Validate input length
      if (text.length > 10000) {
        console.warn('Text too long for grammar correction, truncating');
        text = text.substring(0, 10000);
      }
      
      let correctedText = text;
      const startTime = Date.now();
      const maxProcessingTime = 3000; // 3 seconds max

      for (const { pattern, replacement } of this.grammarPatterns) {
        // Check for timeout
        if (Date.now() - startTime > maxProcessingTime) {
          console.warn('Grammar correction timeout, returning partial result');
          break;
        }
        
        try {
          correctedText = correctedText.replace(pattern, replacement);
        } catch (patternError) {
          console.warn('Grammar pattern failed:', pattern, patternError);
          // Continue with other patterns
        }
      }

      return correctedText;
    } catch (error) {
      console.error('Error in applyGrammarCorrections:', error);
      if (this.onError) {
        this.onError('Grammar correction failed: ' + error.message);
      }
      return text; // Return original text on error
    }
  }

  /**
   * Apply capitalization and punctuation rules
   * Matches the Python behavior for sentence starting uppercase and period ending
   */
  applyCapitalizationAndPunctuation(text) {
    if (!text) {
      return text;
    }

    let result = text;

    // Capitalize first letter (matches Python implementation)
    if (this.options.enableCapitalization && result.length > 0) {
      result = result.charAt(0).toUpperCase() + result.slice(1);
    }

    // Add period if sentence doesn't end with punctuation (matches Python implementation)
    if (this.options.enablePunctuation && result.length > 0) {
      const lastChar = result.charAt(result.length - 1);
      if (!/[.!?]/.test(lastChar)) {
        result += '.';
      }
    }

    return result;
  }

  /**
   * Process text with specific enhancement options
   */
  processWithOptions(text, options = {}) {
    const originalOptions = { ...this.options };
    
    // Temporarily update options
    this.options = { ...this.options, ...options };
    
    try {
      const result = this.enhanceText(text);
      return result;
    } finally {
      // Restore original options
      this.options = originalOptions;
    }
  }

  /**
   * Get processing statistics for the last enhancement
   */
  getProcessingStats(originalText, enhancedText) {
    if (!originalText || !enhancedText) {
      return null;
    }

    const originalWords = originalText.split(/\s+/).filter(word => word.length > 0);
    const enhancedWords = enhancedText.split(/\s+/).filter(word => word.length > 0);
    
    return {
      originalLength: originalText.length,
      enhancedLength: enhancedText.length,
      originalWordCount: originalWords.length,
      enhancedWordCount: enhancedWords.length,
      wordsRemoved: originalWords.length - enhancedWords.length,
      compressionRatio: enhancedText.length / originalText.length
    };
  }

  /**
   * Validate if text needs enhancement
   */
  needsEnhancement(text) {
    if (!text || typeof text !== 'string') {
      return false;
    }

    // Check for fillers
    const words = text.toLowerCase().split(/\s+/);
    const hasFillers = words.some(word => this.fillers.has(word));
    
    // Check for stutters
    const hasStutters = this.stutterPattern.test(text);
    
    // Check for basic grammar issues
    const hasGrammarIssues = this.grammarPatterns.some(({ pattern }) => pattern.test(text));
    
    // Check capitalization
    const needsCapitalization = text.length > 0 && text.charAt(0) !== text.charAt(0).toUpperCase();
    
    // Check punctuation
    const needsPunctuation = text.length > 0 && !/[.!?]$/.test(text.trim());

    return hasFillers || hasStutters || hasGrammarIssues || needsCapitalization || needsPunctuation;
  }

  /**
   * Update configuration options
   */
  updateOptions(newOptions) {
    this.options = { ...this.options, ...newOptions };
  }

  /**
   * Add custom filler words
   */
  addFillers(fillers) {
    if (Array.isArray(fillers)) {
      fillers.forEach(filler => this.fillers.add(filler.toLowerCase()));
    } else if (typeof fillers === 'string') {
      this.fillers.add(fillers.toLowerCase());
    }
  }

  /**
   * Remove custom filler words from the filler list
   */
  removeCustomFillers(fillers) {
    if (Array.isArray(fillers)) {
      fillers.forEach(filler => this.fillers.delete(filler.toLowerCase()));
    } else if (typeof fillers === 'string') {
      this.fillers.delete(fillers.toLowerCase());
    }
  }

  /**
   * Add custom grammar correction patterns
   */
  addGrammarPattern(pattern, replacement) {
    this.grammarPatterns.push({ pattern, replacement });
  }

  /**
   * Get current configuration
   */
  getConfiguration() {
    return {
      options: { ...this.options },
      fillerCount: this.fillers.size,
      grammarPatternCount: this.grammarPatterns.length
    };
  }

  /**
   * Reset to default configuration
   */
  resetToDefaults() {
    this.options = {
      enableDisfluencyFilter: true,
      enableGrammarCorrection: true,
      enableCapitalization: true,
      enablePunctuation: true
    };
  }
}

// Export for use in extension
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TextEnhancementBridge;
} else if (typeof window !== 'undefined') {
  window.TextEnhancementBridge = TextEnhancementBridge;
}