/**
 * Main Bridge Coordinator
 * 
 * This module coordinates between the RealtimeSTT and TextEnhancement bridges,
 * providing a unified interface for the extension to use both components together.
 * 
 * Requirements: 1.2, 2.3, 2.4
 */

class LiveTextEnhancementBridge {
  constructor(options = {}) {
    this.options = {
      language: options.language || '',
      enableRealtimeTranscription: options.enableRealtimeTranscription || false,
      enableDisfluencyFilter: options.enableDisfluencyFilter !== false,
      enableGrammarCorrection: options.enableGrammarCorrection !== false,
      ...options
    };

    // Initialize component bridges
    this.sttBridge = null;
    this.textBridge = null;
    
    // State management
    this.isInitialized = false;
    this.isActive = false;
    
    // Callbacks
    this.onTranscriptionUpdate = options.onTranscriptionUpdate || null;
    this.onRealtimeUpdate = options.onRealtimeUpdate || null;
    this.onEnhancedTextUpdate = options.onEnhancedTextUpdate || null;
    this.onRecordingStart = options.onRecordingStart || null;
    this.onRecordingStop = options.onRecordingStop || null;
    this.onError = options.onError || null;
    
    // Processing state
    this.lastRawText = '';
    this.lastEnhancedText = '';
  }

  /**
   * Initialize both component bridges
   */
  async initialize() {
    try {
      if (this.isInitialized) {
        return;
      }

      // Initialize Text Enhancement Bridge first (no dependencies)
      try {
        this.textBridge = new TextEnhancementBridge({
          enableDisfluencyFilter: this.options.enableDisfluencyFilter,
          enableGrammarCorrection: this.options.enableGrammarCorrection,
          enableCapitalization: true,
          enablePunctuation: true,
          onTextProcessed: (enhancedText, originalText) => {
            this._handleTextEnhanced(enhancedText, originalText);
          },
          onError: (error) => {
            this._handleError('Text Enhancement Error: ' + error);
          }
        });
        console.log('Text Enhancement Bridge initialized successfully');
      } catch (textError) {
        console.error('Failed to initialize Text Enhancement Bridge:', textError);
        // Continue with STT initialization even if text enhancement fails
        this._handleError('Text enhancement unavailable: ' + textError.message);
      }

      // Initialize RealtimeSTT Bridge with retry logic
      let sttInitialized = false;
      const maxRetries = 2;
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          this.sttBridge = new RealtimeSTTBridge({
            language: this.options.language,
            enableRealtimeTranscription: this.options.enableRealtimeTranscription,
            onTranscriptionUpdate: (text) => {
              this._handleTranscriptionUpdate(text);
            },
            onRealtimeUpdate: (text) => {
              this._handleRealtimeUpdate(text);
            },
            onRecordingStart: () => {
              this._handleRecordingStart();
            },
            onRecordingStop: () => {
              this._handleRecordingStop();
            },
            onError: (error) => {
              this._handleError('Speech Recognition Error: ' + error);
            }
          });

          // Initialize the RealtimeSTT bridge with audio processing pipeline
          await this.sttBridge.initialize();
          
          // Verify that the audio processing pipeline is properly connected
          const sttState = this.sttBridge.getState();
          if (!sttState.isInitialized) {
            throw new Error('RealtimeSTT bridge initialization failed - state check failed');
          }
          
          console.log('Audio processing pipeline connected successfully');
          console.log('STT Bridge state:', sttState);
          sttInitialized = true;
          break; // Success, exit retry loop
          
        } catch (sttError) {
          console.error(`STT initialization attempt ${attempt} failed:`, sttError);
          
          if (attempt === maxRetries) {
            // Final attempt failed, provide fallback
            this._handleError('Audio processing initialization failed after ' + maxRetries + ' attempts: ' + sttError.message);
            
            // Check if we can provide a fallback mode
            if (this.textBridge) {
              console.log('Falling back to text-only mode');
              this.isInitialized = true; // Allow text enhancement only
              return;
            } else {
              throw sttError; // No fallback available
            }
          } else {
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
          }
        }
      }
      
      if (sttInitialized) {
        this.isInitialized = true;
        console.log('Live Text Enhancement Bridge initialized successfully with audio processing pipeline');
      }
      
    } catch (error) {
      console.error('Error initializing Live Text Enhancement Bridge:', error);
      
      // Clean up any partially initialized components
      this._cleanupOnInitializationError();
      
      this._handleError('Failed to initialize: ' + error.message);
      throw error;
    }
  }

  /**
   * Clean up resources when initialization fails
   */
  _cleanupOnInitializationError() {
    try {
      if (this.sttBridge) {
        this.sttBridge.destroy();
        this.sttBridge = null;
      }
      
      this.textBridge = null;
      this.isInitialized = false;
    } catch (cleanupError) {
      console.warn('Error during initialization cleanup:', cleanupError);
    }
  }

  /**
   * Start the complete text enhancement pipeline
   */
  async start() {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      if (this.isActive) {
        return;
      }

      // Start the audio processing pipeline if available
      if (this.sttBridge) {
        try {
          await this.sttBridge.start();
          
          // Verify that audio processing is active
          const sttState = this.sttBridge.getState();
          if (!sttState.isRecording) {
            console.warn('Audio recording may not have started properly');
            this._handleError('Audio recording failed to start - microphone may be unavailable');
          } else {
            console.log('Audio processing started successfully');
          }
        } catch (sttStartError) {
          console.error('Failed to start STT bridge:', sttStartError);
          
          // Provide fallback behavior
          if (this.textBridge) {
            console.log('STT failed to start, continuing with text enhancement only');
            this._handleError('Audio processing unavailable - text enhancement only mode active');
          } else {
            throw sttStartError;
          }
        }
      } else {
        console.log('STT bridge not available, text enhancement only mode');
        if (this.textBridge) {
          this._handleError('Audio processing not available - text enhancement only mode active');
        } else {
          throw new Error('No components available - both audio and text processing failed');
        }
      }
      
      this.isActive = true;
      
      console.log('Live Text Enhancement Bridge started');
      console.log('Pipeline state:', this.getState());
      
    } catch (error) {
      console.error('Error starting Live Text Enhancement Bridge:', error);
      this._handleError('Failed to start processing pipeline: ' + error.message);
      throw error;
    }
  }

  /**
   * Stop the text enhancement pipeline
   */
  stop() {
    try {
      if (!this.isActive) {
        return;
      }

      this.sttBridge.stop();
      this.isActive = false;
      
      console.log('Live Text Enhancement Bridge stopped');
      
    } catch (error) {
      console.error('Error stopping Live Text Enhancement Bridge:', error);
      this._handleError('Failed to stop: ' + error.message);
    }
  }

  /**
   * Handle transcription updates from STT bridge
   */
  _handleTranscriptionUpdate(rawText) {
    try {
      this.lastRawText = rawText;
      
      // Notify callback with raw text
      if (this.onTranscriptionUpdate) {
        try {
          this.onTranscriptionUpdate(rawText);
        } catch (callbackError) {
          console.error('Error in transcription update callback:', callbackError);
        }
      }

      // Process text through enhancement bridge with fallback
      let enhancedText = rawText; // Fallback to raw text
      
      if (this.textBridge) {
        try {
          enhancedText = this.textBridge.enhanceText(rawText);
          this.lastEnhancedText = enhancedText;
        } catch (enhancementError) {
          console.error('Text enhancement failed, using raw text:', enhancementError);
          this._handleError('Text enhancement failed: ' + enhancementError.message);
          enhancedText = rawText; // Use raw text as fallback
        }
      } else {
        console.warn('Text bridge not available, using raw text');
      }
      
      // Notify callback with enhanced text
      if (this.onEnhancedTextUpdate) {
        try {
          this.onEnhancedTextUpdate(enhancedText, rawText);
        } catch (callbackError) {
          console.error('Error in enhanced text update callback:', callbackError);
        }
      }
      
    } catch (error) {
      console.error('Error handling transcription update:', error);
      this._handleError('Failed to process transcription: ' + error.message);
      
      // Fallback: still try to notify with raw text
      if (this.onEnhancedTextUpdate && rawText) {
        try {
          this.onEnhancedTextUpdate(rawText, rawText);
        } catch (fallbackError) {
          console.error('Fallback notification also failed:', fallbackError);
        }
      }
    }
  }

  /**
   * Handle realtime updates from STT bridge
   */
  _handleRealtimeUpdate(rawText) {
    try {
      // Process realtime text through enhancement bridge with fallback
      let enhancedText = rawText; // Fallback to raw text
      
      if (this.textBridge) {
        try {
          enhancedText = this.textBridge.enhanceText(rawText);
        } catch (enhancementError) {
          console.warn('Realtime text enhancement failed, using raw text:', enhancementError);
          enhancedText = rawText; // Use raw text as fallback
        }
      }
      
      // Notify callback with enhanced realtime text
      if (this.onRealtimeUpdate) {
        try {
          this.onRealtimeUpdate(enhancedText, rawText);
        } catch (callbackError) {
          console.error('Error in realtime update callback:', callbackError);
        }
      }
      
    } catch (error) {
      console.error('Error handling realtime update:', error);
      this._handleError('Failed to process realtime text: ' + error.message);
      
      // Fallback: still try to notify with raw text
      if (this.onRealtimeUpdate && rawText) {
        try {
          this.onRealtimeUpdate(rawText, rawText);
        } catch (fallbackError) {
          console.error('Fallback realtime notification also failed:', fallbackError);
        }
      }
    }
  }

  /**
   * Handle text enhancement completion
   */
  _handleTextEnhanced(enhancedText, originalText) {
    // This is called by the text bridge when processing is complete
    console.log('Text enhanced:', { original: originalText, enhanced: enhancedText });
  }

  /**
   * Handle recording start
   */
  _handleRecordingStart() {
    if (this.onRecordingStart) {
      this.onRecordingStart();
    }
  }

  /**
   * Handle recording stop
   */
  _handleRecordingStop() {
    if (this.onRecordingStop) {
      this.onRecordingStop();
    }
  }

  /**
   * Handle errors from component bridges
   */
  _handleError(error) {
    console.error('Bridge error:', error);
    if (this.onError) {
      this.onError(error);
    }
  }

  /**
   * Get current state of all components
   */
  getState() {
    return {
      isInitialized: this.isInitialized,
      isActive: this.isActive,
      sttState: this.sttBridge ? this.sttBridge.getState() : null,
      textBridgeConfig: this.textBridge ? this.textBridge.getConfiguration() : null,
      lastRawText: this.lastRawText,
      lastEnhancedText: this.lastEnhancedText
    };
  }

  /**
   * Update configuration for both bridges
   */
  updateOptions(newOptions) {
    this.options = { ...this.options, ...newOptions };
    
    if (this.sttBridge) {
      this.sttBridge.updateOptions({
        language: newOptions.language,
        enableRealtimeTranscription: newOptions.enableRealtimeTranscription
      });
    }
    
    if (this.textBridge) {
      this.textBridge.updateOptions({
        enableDisfluencyFilter: newOptions.enableDisfluencyFilter,
        enableGrammarCorrection: newOptions.enableGrammarCorrection
      });
    }
  }

  /**
   * Process text directly through enhancement bridge (for testing)
   */
  enhanceText(text) {
    if (!this.textBridge) {
      throw new Error('Text bridge not initialized');
    }
    return this.textBridge.enhanceText(text);
  }

  /**
   * Check if text needs enhancement
   */
  needsEnhancement(text) {
    if (!this.textBridge) {
      return false;
    }
    return this.textBridge.needsEnhancement(text);
  }

  /**
   * Get processing statistics
   */
  getProcessingStats(originalText, enhancedText) {
    if (!this.textBridge) {
      return null;
    }
    return this.textBridge.getProcessingStats(originalText, enhancedText);
  }

  /**
   * Clean up all resources
   */
  destroy() {
    try {
      this.stop();
      
      if (this.sttBridge) {
        this.sttBridge.destroy();
        this.sttBridge = null;
      }
      
      this.textBridge = null;
      this.isInitialized = false;
      
      console.log('Live Text Enhancement Bridge destroyed');
      
    } catch (error) {
      console.error('Error destroying Live Text Enhancement Bridge:', error);
    }
  }
}

// Export for use in extension
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LiveTextEnhancementBridge;
} else if (typeof window !== 'undefined') {
  window.LiveTextEnhancementBridge = LiveTextEnhancementBridge;
}