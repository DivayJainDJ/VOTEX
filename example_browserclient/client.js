// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Speech-to-Text client...');
    
    let socket = new WebSocket("ws://localhost:8001");
    let displayDiv = document.getElementById('finalText');
    let statusDiv = document.getElementById('status');
    let micButton = document.getElementById('micButton');
    let historyDiv = document.getElementById('history');
    let server_available = false;
    let mic_available = false;
    let mic_active = false;
    let audioContext = null;
    let processor = null;
    let stream = null;
    let history = [];

    const serverCheckInterval = 5000;

    // Stage elements
    const stages = {
        1: document.getElementById('stage1'),
        2: document.getElementById('stage2'),
        3: document.getElementById('stage3'),
        4: document.getElementById('stage4')
    };

    const stageContents = {
        1: document.getElementById('stage1-content'),
        2: document.getElementById('stage2-content'),
        3: document.getElementById('stage3-content'),
        4: document.getElementById('stage4-content')
    };

    function resetStages() {
        for (let i = 1; i <= 4; i++) {
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

    function addToHistory(text) {
        history.unshift(text);
        if (history.length > 10) history.pop();
        
        historyDiv.innerHTML = history.map((item, index) => 
            `<div class="history-item">${index + 1}. ${item}</div>`
        ).join('');
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
            } else if (data.type === 'fullSentence') {
                displayDiv.textContent = data.text;
                addToHistory(data.text);
            } else if (data.type === 'recording_complete') {
                stopRecording();
                statusDiv.textContent = "✅ Complete - Click to record again";
                statusDiv.style.color = "#66ff66";
                
                for (let i = 1; i <= 4; i++) {
                    stages[i].classList.add('active');
                }
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
        } else if (data.type === 'fullSentence') {
            displayDiv.textContent = data.text;
            addToHistory(data.text);
        } else if (data.type === 'recording_complete') {
            stopRecording();
            statusDiv.textContent = "✅ Complete - Click to record again";
            statusDiv.style.color = "#66ff66";
            
            for (let i = 1; i <= 4; i++) {
                stages[i].classList.add('active');
            }
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

    console.log('Client initialized successfully');
});
