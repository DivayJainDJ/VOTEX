// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Speech-to-Text client...');
    
    let socket = new WebSocket("ws://localhost:8001");
    let displayDiv = document.getElementById('finalText');
    let statusDiv = document.getElementById('status');
    let micButton = document.getElementById('micButton');
    let historyDiv = document.getElementById('history');
    let latencyDiv = document.getElementById('latencyDisplay');
    let server_available = false;
    let mic_available = false;
    let mic_active = false;
    let audioContext = null;
    let processor = null;
    let stream = null;
    let history = [];
    let recordingStartTime = 0;
    let currentTranscript = '';
    let currentLatency = 0;
    let currentOriginal = '';
    let currentToneMode = 'neutral';

    const serverCheckInterval = 5000;
    
    // Feedback UI elements
    const feedbackButtons = document.getElementById('feedbackButtons');
    const approveButton = document.getElementById('approveButton');
    const rejectButton = document.getElementById('rejectButton');
    const feedbackSection = document.getElementById('feedbackSection');
    const correctionInput = document.getElementById('correctionInput');
    const submitFeedback = document.getElementById('submitFeedback');
    const autoImproveButton = document.getElementById('autoImproveButton');
    const cancelFeedback = document.getElementById('cancelFeedback');
    const feedbackStats = document.getElementById('feedbackStats');

    // Stage elements
    const stages = {
        1: document.getElementById('stage1'),
        2: document.getElementById('stage2'),
        3: document.getElementById('stage3'),
        4: document.getElementById('stage4'),
        5: document.getElementById('stage5')
    };

    const stageContents = {
        1: document.getElementById('stage1-content'),
        2: document.getElementById('stage2-content'),
        3: document.getElementById('stage3-content'),
        4: document.getElementById('stage4-content'),
        5: document.getElementById('stage5-content')
    };

    function resetStages() {
        for (let i = 1; i <= 5; i++) {
            stages[i].classList.remove('active');
            stageContents[i].textContent = 'Waiting...';
        }
    }

    function updateStage(stageNum, text) {
        stages[stageNum].classList.add('active');
        stageContents[stageNum].textContent = text || 'Processing...';
        
        for (let i = 1; i < stageNum; i++) {
            stages[i].classList.remove('active');
        }
    }

    function addToHistory(text, latency) {
        const timestamp = new Date().toLocaleTimeString();
        const historyEntry = {
            text: text,
            latency: latency,
            timestamp: timestamp
        };
        history.unshift(historyEntry);
        if (history.length > 10) history.pop();
        
        historyDiv.innerHTML = history.map((item, index) => {
            const latencyColor = item.latency < 1000 ? '#4caf50' : item.latency < 1500 ? '#ffeb3b' : '#ff6666';
            return `<div class="history-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="flex: 1;">${index + 1}. ${item.text}</span>
                    <span style="color: ${latencyColor}; font-size: 12px; margin-left: 10px; white-space: nowrap;">
                        ⏱️ ${item.latency}ms
                    </span>
                </div>
                <div style="font-size: 11px; color: #666; margin-top: 3px;">${item.timestamp}</div>
            </div>`;
        }).join('');
    }

    function updateStatus() {
        if (!mic_available) {
            statusDiv.textContent = "🎤 Please allow microphone access";
            statusDiv.style.color = "#ff6666";
        } else if (!server_available) {
            statusDiv.textContent = "🖥️ Connecting to server...";
            statusDiv.style.color = "#ffaa66";
        } else if (mic_active) {
            statusDiv.textContent = "🔴 Recording - Speak now";
            statusDiv.style.color = "#66ff66";
        } else {
            statusDiv.textContent = "Click microphone to start recording";
            statusDiv.style.color = "#888";
        }
    }

    function updateLatencyDisplay(latency) {
        latencyDiv.style.display = 'inline-block';
        
        // Add warning if exceeding target
        if (latency > 1500) {
            latencyDiv.textContent = `⏱️ Latency: ${latency}ms ⚠️ (Target: <1500ms)`;
        } else {
            latencyDiv.textContent = `⏱️ Latency: ${latency}ms`;
        }
        
        // Color code based on speed
        latencyDiv.classList.remove('fast', 'medium', 'slow');
        if (latency < 1000) {
            latencyDiv.classList.add('fast');
        } else if (latency < 1500) {
            latencyDiv.classList.add('medium');
        } else {
            latencyDiv.classList.add('slow');
        }
    }

    function toggleMicrophone() {
        if (!mic_available || !server_available) {
            console.log('Cannot toggle: mic_available=', mic_available, 'server_available=', server_available);
            return;
        }
        
        mic_active = !mic_active;
        console.log('Microphone toggled:', mic_active);
        
        if (mic_active) {
            micButton.classList.add('active');
            resetStages();
            displayDiv.textContent = 'Listening...';
            latencyDiv.style.display = 'none';
            recordingStartTime = Date.now();
            
            // Hide feedback UI when starting new recording
            feedbackButtons.style.display = 'none';
            feedbackSection.style.display = 'none';
            
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ command: 'start_recording' }));
                console.log('Sent start_recording command');
            }
        } else {
            micButton.classList.remove('active');
            
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ command: 'stop_recording' }));
                console.log('Sent stop_recording command');
            }
        }
        
        updateStatus();
    }

    function stopRecording() {
        mic_active = false;
        micButton.classList.remove('active');
        
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ command: 'stop_recording' }));
        }
        
        updateStatus();
    }

    function connectToServer() {
        socket = new WebSocket("ws://localhost:8001");

        socket.onopen = function() {
            server_available = true;
            console.log('WebSocket connected');
            updateStatus();
            
            // Request history on connection
            socket.send(JSON.stringify({
                command: 'get_history',
                limit: 10
            }));
        };

        socket.onmessage = function(event) {
            let data = JSON.parse(event.data);
            console.log('Received:', data.type);

            if (data.type === 'recording_started') {
                statusDiv.textContent = "🎙️ Listening...";
                statusDiv.style.color = "#66ff66";
                resetStages();
            } else if (data.type === 'processing') {
                statusDiv.textContent = "⚡ Processing...";
                statusDiv.style.color = "#ffaa66";
            } else if (data.type === 'stage') {
                updateStage(data.stage, data.text);
                if (data.stage === 1) {
                    currentOriginal = data.text;
                }
            } else if (data.type === 'fullSentence') {
                displayDiv.textContent = data.text;
                currentTranscript = data.text;
            } else if (data.type === 'recording_complete') {
                stopRecording();
                
                if (data.learned) {
                    statusDiv.textContent = "🧠 Used learned correction";
                    statusDiv.style.color = "#00e5ff";
                } else {
                    statusDiv.textContent = "✅ Complete - Click to record again";
                    statusDiv.style.color = "#66ff66";
                }
                
                // Update latency display and add to history
                if (data.latency) {
                    currentLatency = data.latency;
                    updateLatencyDisplay(data.latency);
                    addToHistory(currentTranscript, currentLatency);
                }
                
                // Show approve/reject buttons
                feedbackButtons.style.display = 'flex';
                
                for (let i = 1; i <= 5; i++) {
                    stages[i].classList.add('active');
                }
            } else if (data.type === 'feedback_received') {
                // Show feedback message temporarily
                const tempMessage = document.createElement('div');
                tempMessage.textContent = data.message + ` | Accuracy: ${data.stats.accuracy} | Approved: ${data.stats.approved} | Rejected: ${data.stats.rejected}`;
                tempMessage.style.cssText = 'margin-top: 10px; padding: 10px; background: rgba(76,175,80,0.2); border-radius: 5px; color: #4caf50; font-size: 12px;';
                displayDiv.parentElement.appendChild(tempMessage);
                
                setTimeout(() => {
                    tempMessage.remove();
                    // Only hide feedback section if it's not currently visible (i.e., user is not editing)
                    if (feedbackSection.style.display !== 'block') {
                        updateStatus();
                    }
                }, 2000);
            } else if (data.type === 'auto_improved') {
                correctionInput.value = data.correction;
                feedbackStats.textContent = data.message + ` | Accuracy: ${data.stats.accuracy}`;
                feedbackStats.style.color = '#9c27b0';
            } else if (data.type === 'auto_improve_failed') {
                feedbackStats.textContent = data.message;
                feedbackStats.style.color = '#ff6666';
            } else if (data.type === 'history_loaded') {
                // Load history from database
                console.log('Loading history:', data.history.length, 'items');
                history = data.history.map(item => ({
                    text: item.text,
                    latency: item.latency,
                    timestamp: new Date(item.timestamp).toLocaleTimeString()
                }));
                
                // Display history
                historyDiv.innerHTML = history.map((item, index) => {
                    const latencyColor = item.latency < 1000 ? '#4caf50' : item.latency < 1500 ? '#ffeb3b' : '#ff6666';
                    return `<div class="history-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="flex: 1;">${index + 1}. ${item.text}</span>
                            <span style="color: ${latencyColor}; font-size: 12px; margin-left: 10px; white-space: nowrap;">
                                ⏱️ ${item.latency}ms
                            </span>
                        </div>
                        <div style="font-size: 11px; color: #666; margin-top: 3px;">${item.timestamp}</div>
                    </div>`;
                }).join('');
            }
        };

        socket.onclose = function() {
            server_available = false;
            console.log('WebSocket disconnected');
            updateStatus();
        };

        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    }

    // Initial connection
    socket.onopen = function() {
        server_available = true;
        console.log('WebSocket connected');
        updateStatus();
        
        // Request history on connection
        socket.send(JSON.stringify({
            command: 'get_history',
            limit: 10
        }));
    };

    socket.onmessage = function(event) {
        let data = JSON.parse(event.data);
        console.log('Received:', data.type);

        if (data.type === 'recording_started') {
            statusDiv.textContent = "🎙️ Listening...";
            statusDiv.style.color = "#66ff66";
            resetStages();
        } else if (data.type === 'processing') {
            statusDiv.textContent = "⚡ Processing...";
            statusDiv.style.color = "#ffaa66";
        } else if (data.type === 'stage') {
            updateStage(data.stage, data.text);
            if (data.stage === 1) {
                currentOriginal = data.text;
            }
        } else if (data.type === 'fullSentence') {
            displayDiv.textContent = data.text;
            currentTranscript = data.text;
        } else if (data.type === 'recording_complete') {
            stopRecording();
            
            if (data.learned) {
                statusDiv.textContent = "🧠 Used learned correction";
                statusDiv.style.color = "#00e5ff";
            } else {
                statusDiv.textContent = "✅ Complete - Click to record again";
                statusDiv.style.color = "#66ff66";
            }
            
            // Update latency display and add to history
            if (data.latency) {
                currentLatency = data.latency;
                updateLatencyDisplay(data.latency);
                addToHistory(currentTranscript, currentLatency);
            }
            
            // Show approve/reject buttons
            feedbackButtons.style.display = 'flex';
            
            for (let i = 1; i <= 5; i++) {
                stages[i].classList.add('active');
            }
        } else if (data.type === 'feedback_received') {
            // Show feedback message temporarily
            const tempMessage = document.createElement('div');
            tempMessage.textContent = data.message + ` | Accuracy: ${data.stats.accuracy} | Approved: ${data.stats.approved} | Rejected: ${data.stats.rejected}`;
            tempMessage.style.cssText = 'margin-top: 10px; padding: 10px; background: rgba(76,175,80,0.2); border-radius: 5px; color: #4caf50; font-size: 12px;';
            displayDiv.parentElement.appendChild(tempMessage);
            
            setTimeout(() => {
                tempMessage.remove();
                // Only hide feedback section if it's not currently visible (i.e., user is not editing)
                if (feedbackSection.style.display !== 'block') {
                    updateStatus();
                }
            }, 2000);
        } else if (data.type === 'auto_improved') {
            correctionInput.value = data.correction;
            feedbackStats.textContent = data.message + ` | Accuracy: ${data.stats.accuracy}`;
            feedbackStats.style.color = '#9c27b0';
        } else if (data.type === 'auto_improve_failed') {
            feedbackStats.textContent = data.message;
            feedbackStats.style.color = '#ff6666';
        } else if (data.type === 'history_loaded') {
            // Load history from database
            console.log('Loading history:', data.history.length, 'items');
            history = data.history.map(item => ({
                text: item.text,
                latency: item.latency,
                timestamp: new Date(item.timestamp).toLocaleTimeString()
            }));
            
            // Display history
            historyDiv.innerHTML = history.map((item, index) => {
                const latencyColor = item.latency < 1000 ? '#4caf50' : item.latency < 1500 ? '#ffeb3b' : '#ff6666';
                return `<div class="history-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="flex: 1;">${index + 1}. ${item.text}</span>
                        <span style="color: ${latencyColor}; font-size: 12px; margin-left: 10px; white-space: nowrap;">
                            ⏱️ ${item.latency}ms
                        </span>
                    </div>
                    <div style="font-size: 11px; color: #666; margin-top: 3px;">${item.timestamp}</div>
                </div>`;
            }).join('');
        }
    };

    socket.onclose = function() {
        server_available = false;
        console.log('WebSocket disconnected');
        updateStatus();
    };

    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    // Reconnect periodically if disconnected
    setInterval(() => {
        if (!server_available) {
            console.log('Attempting to reconnect...');
            connectToServer();
        }
    }, serverCheckInterval);

    // Set up microphone button
    micButton.addEventListener('click', toggleMicrophone);
    
    // Set up tone selector buttons
    const toneButtons = document.querySelectorAll('.tone-btn');
    toneButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const selectedTone = this.getAttribute('data-tone');
            
            // Update active state
            toneButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update current tone mode
            currentToneMode = selectedTone;
            
            // Send tone change command to server
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    command: 'set_tone',
                    mode: selectedTone
                }));
                console.log('Tone changed to:', selectedTone);
                
                // Show feedback
                const originalText = statusDiv.textContent;
                statusDiv.textContent = `✨ Tone set to ${selectedTone}`;
                statusDiv.style.color = "#00e5ff";
                setTimeout(() => {
                    updateStatus();
                }, 1500);
            }
        });
    });
    
    updateStatus();

    // Request microphone access
    navigator.mediaDevices.getUserMedia({ 
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
        } 
    })
    .then(mediaStream => {
        stream = mediaStream;
        audioContext = new AudioContext();
        let source = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);
        mic_available = true;
        console.log('Microphone access granted');
        updateStatus();

        processor.onaudioprocess = function(e) {
            if (!mic_active || socket.readyState !== WebSocket.OPEN) {
                return;
            }

            let inputData = e.inputBuffer.getChannelData(0);
            let outputData = new Int16Array(inputData.length);

            for (let i = 0; i < inputData.length; i++) {
                outputData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
            }

            let metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
            let metadataBytes = new TextEncoder().encode(metadata);
            let metadataLength = new ArrayBuffer(4);
            let metadataLengthView = new DataView(metadataLength);
            metadataLengthView.setInt32(0, metadataBytes.byteLength, true);
            let combinedData = new Blob([metadataLength, metadataBytes, outputData.buffer]);
            socket.send(combinedData);
        };
    })
    .catch(e => {
        console.error('Microphone access error:', e);
        statusDiv.textContent = "❌ Microphone access denied";
        statusDiv.style.color = "#ff6666";
    });

    // Approve/Reject button handlers
    approveButton.addEventListener('click', function() {
        // Send approval to server
        socket.send(JSON.stringify({
            command: 'approve',
            original: currentOriginal,
            output: currentTranscript,
            tone_mode: currentToneMode
        }));
        feedbackButtons.style.display = 'none';
        statusDiv.textContent = '✓ Output approved! System learning...';
        statusDiv.style.color = '#4caf50';
        
        // Reset after 2 seconds
        setTimeout(() => {
            updateStatus();
        }, 2000);
    });
    
    rejectButton.addEventListener('click', function() {
        // Send rejection to server
        socket.send(JSON.stringify({
            command: 'reject',
            original: currentOriginal,
            output: currentTranscript,
            tone_mode: currentToneMode
        }));
        feedbackButtons.style.display = 'none';
        feedbackSection.style.display = 'block';
        correctionInput.value = currentTranscript;
        correctionInput.focus();
        correctionInput.select();
        feedbackStats.textContent = '✗ Output rejected. Provide correction or use Auto-Fix.';
        feedbackStats.style.color = '#ff6666';
    });
    
    autoImproveButton.addEventListener('click', function() {
        // Request ChatGPT auto-improvement
        feedbackStats.textContent = '🤖 Asking ChatGPT for correction...';
        feedbackStats.style.color = '#9c27b0';
        socket.send(JSON.stringify({
            command: 'auto_improve',
            original: currentOriginal,
            wrong_output: currentTranscript,
            tone_mode: currentToneMode
        }));
    });
    
    submitFeedback.addEventListener('click', function() {
        const userCorrection = correctionInput.value.trim();
        if (userCorrection && userCorrection !== currentTranscript) {
            // Send manual feedback to server
            socket.send(JSON.stringify({
                command: 'feedback',
                original: currentOriginal,
                system_output: currentTranscript,
                user_correction: userCorrection,
                tone_mode: currentToneMode
            }));
            feedbackStats.textContent = '✓ Manual correction submitted! Learning...';
            feedbackStats.style.color = '#4caf50';
        } else {
            feedbackSection.style.display = 'none';
            feedbackButtons.style.display = 'flex';
        }
    });
    
    cancelFeedback.addEventListener('click', function() {
        feedbackSection.style.display = 'none';
        feedbackButtons.style.display = 'flex';
    });
    
    console.log('Client initialized successfully');
});
