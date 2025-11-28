// Background script for Live Text Enhancement Extension

// Extension state
let extensionState = {
  isEnabled: false,
  currentPlatform: null,
  isProcessing: false,
  lastError: null
};

// Initialize extension on startup
chrome.runtime.onStartup.addListener(initializeExtension);
chrome.runtime.onInstalled.addListener(initializeExtension);

async function initializeExtension() {
  try {
    // Load saved state
    const result = await chrome.storage.local.get(['isEnabled']);
    extensionState.isEnabled = result.isEnabled || false;
    
    console.log('Extension initialized, enabled:', extensionState.isEnabled);
  } catch (error) {
    console.error('Error initializing extension:', error);
    extensionState.lastError = 'Failed to initialize extension';
  }
}

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case 'enable':
          await handleEnable(sender);
          sendResponse({ success: true });
          break;
        case 'disable':
          await handleDisable(sender);
          sendResponse({ success: true });
          break;
        case 'platformDetected':
          handlePlatformDetected(message.platform, sender);
          sendResponse({ success: true });
          break;
        case 'getState':
          sendResponse({ success: true, state: extensionState });
          break;
        case 'error':
          handleError(message.error, sender);
          sendResponse({ success: true });
          break;
        case 'configChanged':
          await handleConfigChange(message.config, sender);
          sendResponse({ success: true });
          break;
        case 'healthCheck':
          const healthStatus = await performHealthCheck();
          sendResponse({ success: true, health: healthStatus });
          break;
        default:
          console.warn('Unknown message action:', message.action);
          sendResponse({ success: false, error: 'Unknown action: ' + message.action });
      }
    } catch (error) {
      console.error('Error handling message:', error);
      sendResponse({ 
        success: false, 
        error: error.message || 'Unknown error occurred' 
      });
    }
  })();
  
  return true; // Keep message channel open for async response
});

async function handleEnable(sender) {
  try {
    // Clear any previous errors
    extensionState.lastError = null;
    await chrome.storage.local.remove(['lastError']);
    
    extensionState.isEnabled = true;
    await chrome.storage.local.set({ isEnabled: true });
    
    // Notify all content scripts with error handling
    const notificationResult = await notifyContentScripts('enable');
    
    if (!notificationResult.success) {
      throw new Error('Failed to notify content scripts: ' + notificationResult.error);
    }
    
    console.log('Extension enabled successfully');
    
    // Send success response
    if (sender.tab) {
      chrome.tabs.sendMessage(sender.tab.id, { 
        action: 'enableSuccess' 
      }).catch(() => {
        // Ignore if popup is closed
      });
    }
    
  } catch (error) {
    console.error('Error enabling extension:', error);
    
    // Revert state on error (error recovery)
    extensionState.isEnabled = false;
    await chrome.storage.local.set({ isEnabled: false });
    
    // Set specific error message
    let errorMessage = 'Failed to enable extension';
    if (error.message.includes('permission')) {
      errorMessage = 'Microphone permission required';
    } else if (error.message.includes('audio')) {
      errorMessage = 'Audio system initialization failed';
    } else if (error.message.includes('platform')) {
      errorMessage = 'Unsupported platform detected';
    } else if (error.message.includes('content scripts')) {
      errorMessage = 'Failed to initialize on current page. Please refresh and try again.';
    }
    
    extensionState.lastError = errorMessage;
    await chrome.storage.local.set({ lastError: errorMessage });
    
    // Notify popup of error
    notifyPopup();
    
    throw error; // Re-throw for caller handling
  }
}

async function handleDisable(sender) {
  try {
    // Clear any previous errors
    extensionState.lastError = null;
    await chrome.storage.local.remove(['lastError']);
    
    extensionState.isEnabled = false;
    extensionState.isProcessing = false;
    await chrome.storage.local.set({ isEnabled: false });
    
    // Notify all content scripts with error handling
    const notificationResult = await notifyContentScripts('disable');
    
    if (!notificationResult.success) {
      console.warn('Some content scripts may not have been notified:', notificationResult.error);
      // Don't throw error for disable operation - it's better to have it disabled
    }
    
    console.log('Extension disabled successfully');
    
  } catch (error) {
    console.error('Error disabling extension:', error);
    
    // For disable operations, we still want to set the state to disabled
    // even if there were errors in the process
    extensionState.isEnabled = false;
    extensionState.isProcessing = false;
    await chrome.storage.local.set({ isEnabled: false });
    
    const errorMessage = 'Extension disabled with warnings. Some components may still be active.';
    extensionState.lastError = errorMessage;
    await chrome.storage.local.set({ lastError: errorMessage });
    
    // Notify popup of warning
    notifyPopup();
  }
}

function handlePlatformDetected(platform, sender) {
  extensionState.currentPlatform = platform;
  chrome.storage.local.set({ currentPlatform: platform });
  
  // Notify popup of platform detection
  notifyPopup();
  
  console.log('Platform detected:', platform);
}

function handleError(error, sender) {
  extensionState.lastError = error;
  chrome.storage.local.set({ lastError: error });
  
  // Notify popup of error
  notifyPopup();
  
  console.error('Extension error:', error);
}

async function handleConfigChange(config, sender) {
  try {
    // Store the configuration change
    await chrome.storage.local.set(config);
    
    // Notify all content scripts of configuration change
    await notifyContentScripts('configChanged', config);
    
    console.log('Configuration updated:', config);
  } catch (error) {
    console.error('Error handling config change:', error);
    extensionState.lastError = 'Failed to update configuration';
  }
}

async function notifyContentScripts(action, data = null) {
  let successCount = 0;
  let errorCount = 0;
  const errors = [];
  
  try {
    const tabs = await chrome.tabs.query({
      url: [
        'https://meet.google.com/*',
        'https://zoom.us/*',
        'https://*.zoom.us/*'
      ]
    });
    
    if (tabs.length === 0) {
      return {
        success: false,
        error: 'No supported platform tabs found. Please visit Google Meet or Zoom.',
        successCount: 0,
        errorCount: 0
      };
    }
    
    const promises = tabs.map(async (tab) => {
      try {
        const message = {
          action: action,
          state: extensionState
        };
        
        if (data) {
          message.data = data;
        }
        
        // Add timeout to prevent hanging
        const response = await Promise.race([
          chrome.tabs.sendMessage(tab.id, message),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), 5000)
          )
        ]);
        
        if (response && response.success === false) {
          throw new Error(response.error || 'Content script reported failure');
        }
        
        successCount++;
        console.log(`Successfully notified tab ${tab.id} with action: ${action}`);
        
      } catch (error) {
        errorCount++;
        const errorMsg = `Tab ${tab.id}: ${error.message}`;
        errors.push(errorMsg);
        console.warn('Could not send message to tab:', errorMsg);
        
        // Try to inject content script if it's missing
        if (error.message.includes('Could not establish connection') || 
            error.message.includes('Receiving end does not exist')) {
          try {
            await chrome.scripting.executeScript({
              target: { tabId: tab.id },
              files: ['content.js']
            });
            console.log(`Attempted to re-inject content script in tab ${tab.id}`);
          } catch (injectionError) {
            console.warn(`Failed to inject content script in tab ${tab.id}:`, injectionError);
          }
        }
      }
    });
    
    await Promise.all(promises);
    
    const result = {
      success: successCount > 0,
      successCount,
      errorCount,
      totalTabs: tabs.length
    };
    
    if (errorCount > 0) {
      result.error = `Failed to notify ${errorCount}/${tabs.length} tabs. Errors: ${errors.join('; ')}`;
    }
    
    return result;
    
  } catch (error) {
    console.error('Error in notifyContentScripts:', error);
    return {
      success: false,
      error: 'Failed to query tabs: ' + error.message,
      successCount: 0,
      errorCount: 1
    };
  }
}

async function notifyPopup() {
  try {
    await chrome.runtime.sendMessage({
      action: 'updateStatus',
      isEnabled: extensionState.isEnabled,
      platform: extensionState.currentPlatform,
      error: extensionState.lastError
    });
  } catch (error) {
    // Popup might not be open
    console.log('Could not notify popup');
  }
}

async function performHealthCheck() {
  const health = {
    extensionState: 'healthy',
    contentScripts: 'unknown',
    permissions: 'unknown',
    platform: 'unknown',
    issues: []
  };
  
  try {
    // Check extension state
    if (extensionState.lastError) {
      health.extensionState = 'error';
      health.issues.push('Extension error: ' + extensionState.lastError);
    }
    
    // Check content scripts
    const tabs = await chrome.tabs.query({
      url: [
        'https://meet.google.com/*',
        'https://zoom.us/*',
        'https://*.zoom.us/*'
      ]
    });
    
    if (tabs.length === 0) {
      health.platform = 'unsupported';
      health.issues.push('No supported platform tabs found');
    } else {
      health.platform = 'supported';
      
      // Test content script connectivity
      let workingTabs = 0;
      for (const tab of tabs) {
        try {
          await chrome.tabs.sendMessage(tab.id, { action: 'getStatus' });
          workingTabs++;
        } catch (error) {
          health.issues.push(`Tab ${tab.id}: Content script not responding`);
        }
      }
      
      health.contentScripts = workingTabs > 0 ? 'healthy' : 'error';
    }
    
    // Check permissions (basic check)
    try {
      const permissions = await chrome.permissions.getAll();
      if (permissions.permissions.includes('activeTab') && 
          permissions.origins.some(origin => 
            origin.includes('meet.google.com') || origin.includes('zoom.us'))) {
        health.permissions = 'healthy';
      } else {
        health.permissions = 'limited';
        health.issues.push('Missing required permissions');
      }
    } catch (error) {
      health.permissions = 'error';
      health.issues.push('Permission check failed: ' + error.message);
    }
    
  } catch (error) {
    health.extensionState = 'error';
    health.issues.push('Health check failed: ' + error.message);
  }
  
  return health;
}

// Enhanced error handling for runtime errors
chrome.runtime.onSuspend.addListener(() => {
  console.log('Extension is being suspended, cleaning up...');
  // Perform cleanup if needed
});

chrome.runtime.onStartup.addListener(() => {
  console.log('Browser startup detected, reinitializing extension...');
  initializeExtension();
});

// Handle tab updates to detect platform changes
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  try {
    if (changeInfo.status === 'complete' && tab.url) {
      if (tab.url.includes('meet.google.com')) {
        handlePlatformDetected('Google Meet', { tab: { id: tabId } });
      } else if (tab.url.includes('zoom.us')) {
        handlePlatformDetected('Zoom', { tab: { id: tabId } });
      }
    }
  } catch (error) {
    console.error('Error handling tab update:', error);
  }
});

// Handle tab removal to clean up state
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
  try {
    // Clean up any tab-specific state if needed
    console.log('Tab removed:', tabId);
  } catch (error) {
    console.error('Error handling tab removal:', error);
  }
});