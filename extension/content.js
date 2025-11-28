// Content script for Live Text Enhancement Extension

(function() {
  'use strict';

  // Extension state
  let isEnabled = false;
  let currentPlatform = null;
  let overlay = null;
  let textEnhancementBridge = null;

  // Initialize content script
  initializeContentScript();

  async function initializeContentScript() {
    try {
      console.log('Initializing content script...');
      
      // Detect platform first
      const detectedPlatform = detectPlatform();
      
      if (!detectedPlatform) {
        console.log('Content script loaded on unsupported platform, skipping initialization');
        return;
      }
      
      // Load bridge scripts
      await loadBridgeScripts();
      
      // Get current extension state
      const response = await chrome.runtime.sendMessage({ action: 'getState' });
      if (response) {
        isEnabled = response.isEnabled;
        
        // Always inject interface on supported platforms (will be hidden if disabled)
        await injectInterface();
        
        if (isEnabled) {
          await initializeBridge();
        }
      } else {
        // Fallback: inject interface but keep it disabled
        await injectInterface();
      }
      
      console.log('Content script initialized successfully on:', currentPlatform);
    } catch (error) {
      console.error('Error initializing content script:', error);
      notifyError('Failed to initialize content script: ' + error.message);
    }
  }

  async function loadBridgeScripts() {
    try {
      // Load the bridge scripts dynamically
      const scripts = [
        'realtime-stt-bridge.js',
        'text-enhancement-bridge.js',
        'bridge.js'
      ];

      for (const scriptName of scripts) {
        const script = document.createElement('script');
        script.src = chrome.runtime.getURL(scriptName);
        script.type = 'text/javascript';
        
        await new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
      }
      
      console.log('Bridge scripts loaded successfully');
    } catch (error) {
      console.error('Error loading bridge scripts:', error);
      throw error;
    }
  }

  async function initializeBridge() {
    try {
      if (!window.LiveTextEnhancementBridge) {
        throw new Error('LiveTextEnhancementBridge not available - bridge scripts may not have loaded');
      }

      // Initialize the bridge with proper audio processing configuration
      textEnhancementBridge = new window.LiveTextEnhancementBridge({
        // Audio processing configuration
        sampleRate: 16000,
        bufferSize: 512,
        language: '', // Auto-detect language
        enableRealtimeTranscription: true,
        
        // Text enhancement configuration
        enableDisfluencyFilter: true,
        enableGrammarCorrection: true,
        enableCapitalization: true,
        enablePunctuation: true,
        
        // Callbacks for audio processing pipeline
        onTranscriptionUpdate: (rawText) => {
          console.log('Raw transcription:', rawText);
          updateStatus('Processing...');
        },
        onEnhancedTextUpdate: (enhancedText, rawText) => {
          updateTextDisplay(enhancedText);
          updateStatus('Active');
          console.log('Enhanced text:', enhancedText);
          console.log('Raw text:', rawText);
        },
        onRealtimeUpdate: (enhancedText, rawText) => {
          updateTextDisplay(enhancedText + ' (live)');
          updateStatus('Listening...');
        },
        onRecordingStart: () => {
          updateTextDisplay('Listening...');
          updateStatus('Recording');
          console.log('Audio recording started');
        },
        onRecordingStop: () => {
          updateStatus('Processing...');
          console.log('Audio recording stopped');
        },
        onError: (error) => {
          console.error('Bridge error:', error);
          handleBridgeError(error);
        }
      });

      // Initialize the audio processing pipeline with retry logic
      let initAttempts = 0;
      const maxAttempts = 3;
      
      while (initAttempts < maxAttempts) {
        try {
          await textEnhancementBridge.initialize();
          break; // Success, exit retry loop
        } catch (initError) {
          initAttempts++;
          console.warn(`Bridge initialization attempt ${initAttempts} failed:`, initError);
          
          if (initAttempts >= maxAttempts) {
            throw initError; // Re-throw after max attempts
          }
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000 * initAttempts));
        }
      }
      
      console.log('Text enhancement bridge initialized with audio processing pipeline');
      
      // Verify that the audio processing components are properly connected
      const bridgeState = textEnhancementBridge.getState();
      console.log('Bridge state after initialization:', bridgeState);
      
      if (!bridgeState.isInitialized) {
        throw new Error('Bridge initialization failed - components not properly connected');
      }
      
      updateStatus('Ready');
      
    } catch (error) {
      console.error('Error initializing bridge:', error);
      
      // Provide fallback behavior
      const fallbackError = handleBridgeInitializationError(error);
      notifyError(fallbackError);
      updateStatus('Error');
    }
  }

  function handleBridgeError(error) {
    console.error('Bridge runtime error:', error);
    
    let userFriendlyError = 'Audio processing error';
    let shouldRetry = false;
    
    if (error.includes('permission')) {
      userFriendlyError = 'Microphone permission denied. Please allow access and refresh the page.';
    } else if (error.includes('NotFoundError') || error.includes('microphone')) {
      userFriendlyError = 'No microphone found. Please connect a microphone and try again.';
    } else if (error.includes('NotReadableError')) {
      userFriendlyError = 'Microphone is busy. Please close other applications using the microphone.';
    } else if (error.includes('initialization')) {
      userFriendlyError = 'Failed to initialize audio processing. Please refresh the page.';
      shouldRetry = true;
    } else if (error.includes('timeout')) {
      userFriendlyError = 'Audio processing timeout. Please try again.';
      shouldRetry = true;
    }
    
    updateTextDisplay('Error: ' + userFriendlyError);
    updateStatus('Error');
    notifyError(userFriendlyError);
    
    // Offer retry for certain errors
    if (shouldRetry) {
      setTimeout(() => {
        updateTextDisplay('Click extension icon to retry...');
      }, 3000);
    }
  }

  function handleBridgeInitializationError(error) {
    let fallbackMessage = 'Failed to initialize audio processing';
    
    if (error.message.includes('not available')) {
      fallbackMessage = 'Extension components not loaded. Please refresh the page and try again.';
    } else if (error.message.includes('permission')) {
      fallbackMessage = 'Microphone permission required. Please allow access in browser settings.';
    } else if (error.message.includes('NotFoundError')) {
      fallbackMessage = 'No microphone detected. Please connect a microphone and refresh the page.';
    } else if (error.message.includes('NotAllowedError')) {
      fallbackMessage = 'Microphone access denied. Please allow microphone access and refresh the page.';
    } else if (error.message.includes('NotReadableError')) {
      fallbackMessage = 'Microphone is being used by another application. Please close other apps and try again.';
    } else if (error.message.includes('components not properly connected')) {
      fallbackMessage = 'Audio processing components failed to connect. Please refresh the page.';
    }
    
    return fallbackMessage;
  }

  function detectPlatform() {
    const hostname = window.location.hostname;
    const pathname = window.location.pathname;
    
    // Enhanced platform detection with more specific checks
    if (hostname.includes('meet.google.com')) {
      currentPlatform = 'googlemeet';
      document.body.setAttribute('data-platform', 'googlemeet');
    } else if (hostname.includes('zoom.us') || hostname.includes('.zoom.us')) {
      currentPlatform = 'zoom';
      document.body.setAttribute('data-platform', 'zoom');
    } else {
      currentPlatform = null;
      document.body.removeAttribute('data-platform');
    }
    
    console.log('Platform detected:', currentPlatform || 'Unknown/Unsupported');
    
    // Notify background script of platform detection
    chrome.runtime.sendMessage({
      action: 'platformDetected',
      platform: currentPlatform,
      hostname: hostname,
      pathname: pathname
    }).catch(error => {
      console.error('Error notifying background script:', error);
    });
    
    return currentPlatform;
  }

  async function injectInterface() {
    if (overlay) {
      return; // Already injected
    }
    
    // Only inject on supported platforms
    if (!currentPlatform) {
      console.log('Skipping interface injection - unsupported platform');
      return;
    }
    
    try {
      // Create overlay container with platform-specific positioning
      overlay = document.createElement('div');
      overlay.id = 'live-text-enhancement-overlay';
      
      // Base styles
      const baseStyles = `
        position: fixed;
        width: 300px;
        max-height: 200px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 16px;
        border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        z-index: 999999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        overflow-y: auto;
        display: none;
        transition: opacity 0.3s ease-in-out;
      `;
      
      // Platform-specific positioning
      let platformStyles = '';
      if (currentPlatform === 'googlemeet') {
        platformStyles = 'top: 80px; right: 20px;';
      } else if (currentPlatform === 'zoom') {
        platformStyles = 'top: 60px; right: 20px;';
      } else {
        platformStyles = 'top: 20px; right: 20px;';
      }
      
      overlay.style.cssText = baseStyles + platformStyles;
      
      // Create header with platform indicator
      const header = document.createElement('div');
      header.style.cssText = `
        font-weight: bold;
        margin-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        padding-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      `;
      
      const title = document.createElement('span');
      title.textContent = 'Live Text Enhancement';
      
      const headerRight = document.createElement('div');
      headerRight.style.cssText = 'display: flex; align-items: center; gap: 8px;';
      
      const platformIndicator = document.createElement('span');
      platformIndicator.style.cssText = `
        font-size: 10px;
        opacity: 0.7;
        text-transform: uppercase;
      `;
      platformIndicator.textContent = currentPlatform === 'googlemeet' ? 'Google Meet' : 
                                     currentPlatform === 'zoom' ? 'Zoom' : 'Unknown';
      
      // Add minimize button
      const minimizeButton = document.createElement('button');
      minimizeButton.innerHTML = '−';
      minimizeButton.style.cssText = `
        background: none;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
        line-height: 1;
        opacity: 0.7;
        transition: opacity 0.2s;
      `;
      minimizeButton.onmouseover = () => minimizeButton.style.opacity = '1';
      minimizeButton.onmouseout = () => minimizeButton.style.opacity = '0.7';
      
      let isMinimized = false;
      minimizeButton.onclick = (e) => {
        e.stopPropagation();
        const textDisplay = overlay.querySelector('#enhanced-text-display');
        const statusIndicator = overlay.querySelector('#status-indicator');
        
        if (isMinimized) {
          textDisplay.style.display = 'block';
          statusIndicator.style.display = 'block';
          minimizeButton.innerHTML = '−';
          overlay.style.height = 'auto';
          isMinimized = false;
        } else {
          textDisplay.style.display = 'none';
          statusIndicator.style.display = 'none';
          minimizeButton.innerHTML = '+';
          overlay.style.height = 'auto';
          isMinimized = true;
        }
      };
      
      headerRight.appendChild(platformIndicator);
      headerRight.appendChild(minimizeButton);
      
      header.appendChild(title);
      header.appendChild(headerRight);
      
      // Create text display area
      const textDisplay = document.createElement('div');
      textDisplay.id = 'enhanced-text-display';
      textDisplay.style.cssText = `
        min-height: 40px;
        max-height: 120px;
        line-height: 1.4;
        background: rgba(0, 0, 0, 0.9);
        color: #ffffff;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        padding: 8px;
        border-radius: 4px;
        margin-top: 8px;
        overflow-y: auto;
        word-wrap: break-word;
        white-space: pre-wrap;
        font-weight: 500;
        border: 1px solid rgba(255, 255, 255, 0.1);
      `;
      textDisplay.textContent = 'Waiting for speech...';
      
      // Create status indicator
      const statusIndicator = document.createElement('div');
      statusIndicator.id = 'status-indicator';
      statusIndicator.style.cssText = `
        font-size: 10px;
        opacity: 0.6;
        margin-top: 4px;
        text-align: right;
      `;
      statusIndicator.textContent = 'Ready';
      
      overlay.appendChild(header);
      overlay.appendChild(textDisplay);
      overlay.appendChild(statusIndicator);
      
      // Wait for DOM to be ready before injecting
      if (document.readyState === 'loading') {
        await new Promise(resolve => {
          document.addEventListener('DOMContentLoaded', resolve);
        });
      }
      
      // Inject into page
      document.body.appendChild(overlay);
      
      if (isEnabled) {
        overlay.style.display = 'block';
      }
      
      console.log(`Interface injected successfully for ${currentPlatform}`);
      
      // Add platform-specific DOM integration
      await handlePlatformSpecificIntegration();
      
    } catch (error) {
      console.error('Error injecting interface:', error);
      notifyError('Failed to inject interface: ' + error.message);
    }
  }

  async function handlePlatformSpecificIntegration() {
    if (!currentPlatform) return;
    
    try {
      if (currentPlatform === 'googlemeet') {
        // Wait for Google Meet interface to load
        await waitForElement('[data-meeting-title], [jsname="HlFzId"]', 5000);
        console.log('Google Meet interface detected and ready');
        
        // Adjust overlay position if needed based on Meet's UI
        const meetHeader = document.querySelector('[data-meeting-title], .gb_Pc');
        if (meetHeader) {
          const headerHeight = meetHeader.offsetHeight;
          if (overlay && headerHeight > 60) {
            overlay.style.top = (headerHeight + 20) + 'px';
          }
        }
        
      } else if (currentPlatform === 'zoom') {
        // Wait for Zoom interface to load
        await waitForElement('.meeting-client-view, .zm-video-container', 5000);
        console.log('Zoom interface detected and ready');
        
        // Adjust overlay position if needed based on Zoom's UI
        const zoomHeader = document.querySelector('.meeting-client-header, .zm-video-container-header');
        if (zoomHeader) {
          const headerHeight = zoomHeader.offsetHeight;
          if (overlay && headerHeight > 50) {
            overlay.style.top = (headerHeight + 10) + 'px';
          }
        }
      }
    } catch (error) {
      console.log('Platform-specific integration completed with warnings:', error.message);
      // Don't throw error as this is not critical
    }
  }

  function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }

      const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
          obs.disconnect();
          resolve(element);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element ${selector} not found within ${timeout}ms`));
      }, timeout);
    });
  }

  function removeInterface() {
    if (overlay) {
      overlay.remove();
      overlay = null;
      console.log('Interface removed');
    }
  }

  function showOverlay() {
    if (overlay) {
      overlay.style.display = 'block';
    }
  }

  function hideOverlay() {
    if (overlay) {
      overlay.style.display = 'none';
    }
  }

  function updateTextDisplay(text) {
    if (overlay) {
      const textDisplay = overlay.querySelector('#enhanced-text-display');
      if (textDisplay) {
        const displayText = text || 'Waiting for speech...';
        
        // Add visual feedback for different types of content
        if (displayText.includes('(live)')) {
          textDisplay.style.borderLeft = '3px solid #4CAF50'; // Green for live text
          textDisplay.style.fontStyle = 'italic';
        } else if (displayText.startsWith('Error:')) {
          textDisplay.style.borderLeft = '3px solid #f44336'; // Red for errors
          textDisplay.style.fontStyle = 'normal';
        } else if (displayText.includes('Listening') || displayText.includes('Processing')) {
          textDisplay.style.borderLeft = '3px solid #2196F3'; // Blue for status
          textDisplay.style.fontStyle = 'italic';
        } else {
          textDisplay.style.borderLeft = '3px solid rgba(255, 255, 255, 0.3)'; // Default
          textDisplay.style.fontStyle = 'normal';
        }
        
        textDisplay.textContent = displayText;
        
        // Auto-scroll to bottom if content is long
        textDisplay.scrollTop = textDisplay.scrollHeight;
      }
    }
  }

  function updateStatus(status) {
    if (overlay) {
      const statusIndicator = overlay.querySelector('#status-indicator');
      if (statusIndicator) {
        statusIndicator.textContent = status;
      }
    }
  }

  function notifyError(error) {
    chrome.runtime.sendMessage({
      action: 'error',
      error: error
    });
  }

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
    try {
      switch (message.action) {
        case 'enable':
          isEnabled = true;
          updateStatus('Enabling...');
          
          if (!overlay) {
            await injectInterface();
          }
          showOverlay();
          
          // Initialize and start the audio processing pipeline
          if (!textEnhancementBridge) {
            await initializeBridge();
          }
          if (textEnhancementBridge) {
            updateStatus('Starting audio processing...');
            await textEnhancementBridge.start();
            
            // Verify that the audio processing pipeline is active
            const bridgeState = textEnhancementBridge.getState();
            if (bridgeState.isActive && bridgeState.sttState?.isRecording) {
              updateStatus('Active - Listening');
              updateTextDisplay('Ready to listen...');
            } else {
              updateStatus('Active - Audio setup incomplete');
              updateTextDisplay('Audio processing may not be fully active');
            }
          }
          
          console.log('Extension enabled with audio processing pipeline in content script');
          break;
          
        case 'disable':
          isEnabled = false;
          updateStatus('Disabling...');
          
          // Stop the audio processing pipeline
          if (textEnhancementBridge) {
            textEnhancementBridge.stop();
            
            // Verify that the audio processing has stopped
            const bridgeState = textEnhancementBridge.getState();
            if (!bridgeState.isActive) {
              updateStatus('Disabled');
              updateTextDisplay('Extension disabled');
            } else {
              updateStatus('Disabled - Cleanup incomplete');
              updateTextDisplay('Audio processing may still be active');
            }
          } else {
            updateStatus('Disabled');
            updateTextDisplay('Extension disabled');
          }
          
          hideOverlay();
          
          console.log('Extension disabled with audio processing pipeline stopped in content script');
          break;
          
        case 'updateText':
          updateTextDisplay(message.text);
          break;
          
        case 'getStatus':
          sendResponse({
            success: true,
            platform: currentPlatform,
            isEnabled: isEnabled,
            hasOverlay: !!overlay,
            hasBridge: !!textEnhancementBridge
          });
          return;
          
        default:
          console.log('Unknown message action:', message.action);
      }
      
      sendResponse({ success: true });
    } catch (error) {
      console.error('Error handling message:', error);
      sendResponse({ success: false, error: error.message });
    }
  });

  // Handle page navigation for single-page applications
  let lastUrl = location.href;
  let lastPlatform = currentPlatform;
  
  const navigationObserver = new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      console.log('Page navigation detected:', url);
      
      const newPlatform = detectPlatform();
      
      // If platform changed, reinitialize
      if (newPlatform !== lastPlatform) {
        lastPlatform = newPlatform;
        console.log('Platform change detected:', lastPlatform, '->', newPlatform);
        
        // Clean up existing interface
        removeInterface();
        
        // Reinitialize if on supported platform
        if (newPlatform) {
          setTimeout(async () => {
            try {
              await injectInterface();
              if (isEnabled && !textEnhancementBridge) {
                await initializeBridge();
              }
            } catch (error) {
              console.error('Error reinitializing after platform change:', error);
            }
          }, 1000);
        }
      } else if (newPlatform && !overlay) {
        // Same platform but interface missing - re-inject
        setTimeout(async () => {
          try {
            await injectInterface();
            if (isEnabled && !textEnhancementBridge) {
              await initializeBridge();
            }
          } catch (error) {
            console.error('Error re-injecting interface:', error);
          }
        }, 1000);
      }
    }
  });
  
  navigationObserver.observe(document, { subtree: true, childList: true });

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    if (textEnhancementBridge) {
      textEnhancementBridge.destroy();
    }
    if (navigationObserver) {
      navigationObserver.disconnect();
    }
  });

})();