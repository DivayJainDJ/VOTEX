// Popup script for Live Text Enhancement Extension

document.addEventListener('DOMContentLoaded', async () => {
  const statusElement = document.getElementById('status');
  const statusText = document.getElementById('status-text');
  const toggleButton = document.getElementById('toggle-button');
  const platformInfo = document.getElementById('platform-info');
  const errorMessage = document.getElementById('error-message');
  
  // Configuration elements
  const disfluencyToggle = document.getElementById('disfluency-toggle');
  const grammarToggle = document.getElementById('grammar-toggle');
  const realtimeToggle = document.getElementById('realtime-toggle');

  // Load current extension state
  await loadExtensionState();

  // Set up toggle button event listener
  toggleButton.addEventListener('click', toggleExtension);
  
  // Set up configuration toggle listeners
  disfluencyToggle.addEventListener('click', () => toggleConfig('enableDisfluencyFilter'));
  grammarToggle.addEventListener('click', () => toggleConfig('enableGrammarCorrection'));
  realtimeToggle.addEventListener('click', () => toggleConfig('enableRealtimeDisplay'));

  async function loadExtensionState() {
    try {
      // Check platform support first
      const platformCheck = await checkPlatformSupport();
      
      // Get stored extension state and configuration
      const result = await chrome.storage.local.get([
        'isEnabled', 
        'currentPlatform', 
        'lastError',
        'enableDisfluencyFilter',
        'enableGrammarCorrection',
        'enableRealtimeDisplay'
      ]);
      
      const isEnabled = result.isEnabled || false;
      const currentPlatform = platformCheck.supported ? 
        (result.currentPlatform || platformCheck.platform) : 
        'Unsupported platform';
      const lastError = result.lastError || null;
      
      // Show platform warning if not supported
      if (!platformCheck.supported) {
        showError(platformCheck.reason);
        // Disable the toggle button
        toggleButton.disabled = true;
        toggleButton.style.opacity = '0.5';
        toggleButton.style.cursor = 'not-allowed';
      } else {
        // Re-enable toggle button if it was disabled
        toggleButton.disabled = false;
        toggleButton.style.opacity = '1';
        toggleButton.style.cursor = 'pointer';
      }
      
      // Configuration defaults
      const config = {
        enableDisfluencyFilter: result.enableDisfluencyFilter !== undefined ? result.enableDisfluencyFilter : true,
        enableGrammarCorrection: result.enableGrammarCorrection !== undefined ? result.enableGrammarCorrection : true,
        enableRealtimeDisplay: result.enableRealtimeDisplay !== undefined ? result.enableRealtimeDisplay : true
      };

      updateUI(isEnabled, currentPlatform, lastError);
      updateConfigUI(config);
      
      // Check for component health if enabled
      if (isEnabled && platformCheck.supported) {
        await checkComponentHealth();
      }
      
    } catch (error) {
      console.error('Error loading extension state:', error);
      showError('Failed to load extension state: ' + error.message);
    }
  }

  async function toggleExtension() {
    try {
      const result = await chrome.storage.local.get(['isEnabled']);
      const currentState = result.isEnabled || false;
      const newState = !currentState;

      // If enabling, check permissions first
      if (newState) {
        const hasPermissions = await checkPermissions();
        if (!hasPermissions) {
          return; // Permission check will show appropriate error
        }
      }

      // Update storage
      await chrome.storage.local.set({ isEnabled: newState });

      // Send message to background script
      const response = await chrome.runtime.sendMessage({
        action: newState ? 'enable' : 'disable'
      });

      // Check if the operation was successful
      if (response && response.error) {
        throw new Error(response.error);
      }

      // Update UI
      updateUI(newState, null, null);
      
      // Clear any previous errors
      hideError();
    } catch (error) {
      console.error('Error toggling extension:', error);
      
      // Provide specific error messages based on error type
      let errorMessage = 'Failed to toggle extension';
      if (error.message.includes('permission')) {
        errorMessage = 'Microphone permission required. Please allow access and try again.';
      } else if (error.message.includes('audio')) {
        errorMessage = 'Audio system error. Please check your microphone and try again.';
      } else if (error.message.includes('platform')) {
        errorMessage = 'This page is not supported. Please visit Google Meet or Zoom.';
      } else if (error.message.includes('initialization')) {
        errorMessage = 'Failed to initialize audio processing. Please refresh the page.';
      }
      
      showError(errorMessage);
      
      // Reset toggle state on error
      const result = await chrome.storage.local.get(['isEnabled']);
      const actualState = result.isEnabled || false;
      updateUI(actualState, null, errorMessage);
    }
  }

  function updateUI(isEnabled, platform, error) {
    if (isEnabled) {
      statusElement.className = 'status enabled';
      statusText.textContent = 'Extension Enabled';
      toggleButton.textContent = 'Disable';
      toggleButton.className = 'toggle-button disable';
    } else {
      statusElement.className = 'status disabled';
      statusText.textContent = 'Extension Disabled';
      toggleButton.textContent = 'Enable';
      toggleButton.className = 'toggle-button enable';
    }

    if (platform) {
      platformInfo.textContent = `Platform: ${platform}`;
    }

    if (error) {
      showError(error);
    } else {
      hideError();
    }
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
  }

  function hideError() {
    errorMessage.style.display = 'none';
  }

  async function checkPermissions() {
    try {
      // Check microphone permission
      const micPermission = await navigator.permissions.query({ name: 'microphone' });
      
      if (micPermission.state === 'denied') {
        showError('Microphone access denied. Please enable microphone permissions in browser settings.');
        return false;
      }
      
      if (micPermission.state === 'prompt') {
        // Try to request permission
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach(track => track.stop()); // Clean up
          return true;
        } catch (permError) {
          if (permError.name === 'NotAllowedError') {
            showError('Microphone permission denied. Please allow access and try again.');
          } else if (permError.name === 'NotFoundError') {
            showError('No microphone found. Please connect a microphone and try again.');
          } else if (permError.name === 'NotReadableError') {
            showError('Microphone is being used by another application. Please close other apps and try again.');
          } else {
            showError('Failed to access microphone: ' + permError.message);
          }
          return false;
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error checking permissions:', error);
      showError('Unable to check permissions. Please try again.');
      return false;
    }
  }

  async function checkPlatformSupport() {
    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs.length === 0) {
        return { supported: false, reason: 'No active tab found' };
      }
      
      const currentTab = tabs[0];
      const url = currentTab.url;
      
      if (!url) {
        return { supported: false, reason: 'Cannot access current page' };
      }
      
      const isGoogleMeet = url.includes('meet.google.com');
      const isZoom = url.includes('zoom.us');
      
      if (!isGoogleMeet && !isZoom) {
        return { 
          supported: false, 
          reason: 'This extension only works on Google Meet and Zoom. Please visit a supported platform.' 
        };
      }
      
      return { supported: true, platform: isGoogleMeet ? 'Google Meet' : 'Zoom' };
    } catch (error) {
      console.error('Error checking platform support:', error);
      return { supported: false, reason: 'Unable to check current page' };
    }
  }

  async function toggleConfig(configKey) {
    try {
      const result = await chrome.storage.local.get([configKey]);
      const currentValue = result[configKey] !== undefined ? result[configKey] : true;
      const newValue = !currentValue;
      
      // Update storage
      await chrome.storage.local.set({ [configKey]: newValue });
      
      // Update UI
      updateConfigToggle(configKey, newValue);
      
      // Notify background script of config change
      await chrome.runtime.sendMessage({
        action: 'configChanged',
        config: { [configKey]: newValue }
      });
      
      console.log(`Configuration updated: ${configKey} = ${newValue}`);
    } catch (error) {
      console.error('Error toggling configuration:', error);
      showError('Failed to update configuration');
    }
  }

  function updateConfigUI(config) {
    updateConfigToggle('enableDisfluencyFilter', config.enableDisfluencyFilter);
    updateConfigToggle('enableGrammarCorrection', config.enableGrammarCorrection);
    updateConfigToggle('enableRealtimeDisplay', config.enableRealtimeDisplay);
  }

  function updateConfigToggle(configKey, isEnabled) {
    let toggleElement;
    
    switch (configKey) {
      case 'enableDisfluencyFilter':
        toggleElement = disfluencyToggle;
        break;
      case 'enableGrammarCorrection':
        toggleElement = grammarToggle;
        break;
      case 'enableRealtimeDisplay':
        toggleElement = realtimeToggle;
        break;
      default:
        return;
    }
    
    if (toggleElement) {
      if (isEnabled) {
        toggleElement.classList.add('enabled');
      } else {
        toggleElement.classList.remove('enabled');
      }
    }
  }

  async function checkComponentHealth() {
    try {
      // Send health check message to content script
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tabs.length > 0) {
        const response = await chrome.tabs.sendMessage(tabs[0].id, { action: 'getStatus' });
        
        if (response && !response.success) {
          showError('Component health check failed: ' + (response.error || 'Unknown error'));
        } else if (response) {
          // Update platform info based on actual detection
          if (response.platform) {
            platformInfo.textContent = `Platform: ${response.platform}`;
          }
          
          // Show warnings for missing components
          if (!response.hasOverlay) {
            console.warn('UI overlay not detected');
          }
          if (!response.hasBridge) {
            console.warn('Audio processing bridge not initialized');
          }
        }
      }
    } catch (error) {
      // Content script might not be loaded yet, this is not critical
      console.log('Component health check skipped:', error.message);
    }
  }

  function showRetryButton() {
    const retryButton = document.createElement('button');
    retryButton.textContent = 'Retry';
    retryButton.style.cssText = `
      margin-top: 8px;
      padding: 4px 8px;
      background-color: #2196F3;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    `;
    
    retryButton.onclick = async () => {
      retryButton.remove();
      hideError();
      await loadExtensionState();
    };
    
    errorMessage.appendChild(retryButton);
  }

  // Enhanced error display with retry option for certain errors
  function showError(message) {
    errorMessage.innerHTML = ''; // Clear previous content
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    
    // Add retry button for recoverable errors
    if (message.includes('Failed to load') || 
        message.includes('health check') || 
        message.includes('Unable to check')) {
      showRetryButton();
    }
  }

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateStatus') {
      updateUI(message.isEnabled, message.platform, message.error);
    } else if (message.action === 'permissionError') {
      showError(message.error);
    } else if (message.action === 'componentError') {
      showError('Component error: ' + message.error);
    }
  });
});