if __name__ == '__main__':
    print("Starting server, please wait...")
    from RealtimeSTT import AudioToTextRecorder
    import asyncio
    import websockets
    import threading
    import numpy as np
    from scipy.signal import resample
    import json
    import logging
    import sys
    from fuzzywuzzy import fuzz
    from grammar_processor import GrammarProcessor
    from disfluency_filter import DisfluencyFilter

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('websockets').setLevel(logging.WARNING)

    # Initialize processors
    grammar = GrammarProcessor()
    disfluency_filter = DisfluencyFilter()

    is_running = True
    recorder = None
    recorder_ready = threading.Event()
    client_websocket = None
    main_loop = None  # This will hold our primary event loop

    def dedupe_repetition(text: str, window=6, score_thresh=92) -> str:
        """Collapse repeated phrases. Strategy:
        - split into tokens
        - for each sliding window (n tokens), check if the next window repeats the same text (fuzzy)
        - if repeated, drop the duplicate
        This is fast and works for back-to-back repetition typical in spoken text."""
        tokens = text.split()
        i = 0
        out_tokens = []
        N = len(tokens)
        while i < N:
            # examine windows up to given window size but not exceeding remaining tokens
            w = min(window, N - i)
            found_repeat = False
            for k in range(1, w+1):
                seg = ' '.join(tokens[i:i+k])
                # compare the next k tokens
                if i + k*2 <= N:
                    next_seg = ' '.join(tokens[i+k:i+2*k])
                    # use fuzzy match to allow minor ASR differences
                    s = fuzz.ratio(seg, next_seg)
                    if s >= score_thresh:
                        # skip the next_seg (dedupe)
                        out_tokens.extend(tokens[i:i+k])
                        i += 2*k
                        found_repeat = True
                        break
            if not found_repeat:
                out_tokens.append(tokens[i])
                i += 1
        return ' '.join(out_tokens)

    async def send_to_client(message):
        global client_websocket
        if client_websocket:
            try:
                await client_websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                client_websocket = None
                print("Client disconnected")

    # Called when speech is detected (start of recording)
    def recording_started():
        global main_loop
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                send_to_client(json.dumps({
                    'type': 'recording_started'
                })), main_loop)
    
    # Called when speech ends (processing begins)
    def recording_stopped():
        global main_loop
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                send_to_client(json.dumps({
                    'type': 'processing'
                })), main_loop)

    recorder_config = {
        'spinner': False,
        'use_microphone': False,
        'model': 'small.en',  # Better accuracy than base
        'language': 'en',
        'silero_sensitivity': 0.5,
        'webrtc_sensitivity': 3,
        'post_speech_silence_duration': 0.4,  # Slightly longer for better capture
        'min_length_of_recording': 0.3,
        'min_gap_between_recordings': 0,
        'enable_realtime_transcription': False,
        'beam_size': 5,  # Better accuracy with beam search
        'on_recording_start': recording_started,
        'on_recording_stop': recording_stopped,
    }

    recording_active = threading.Event()
    
    def run_recorder():
        global recorder, main_loop, is_running
        print("Initializing RealtimeSTT...")
        recorder = AudioToTextRecorder(**recorder_config)
        print("RealtimeSTT initialized")
        recorder_ready.set()

        # Loop indefinitely checking for full sentence output.
        while is_running:
            try:
                # Wait until recording is activated
                recording_active.wait()
                
                full_sentence = recorder.text()
                if full_sentence:
                    if main_loop is not None:
                        # Send stage 1: Original transcription
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 1,
                                'text': full_sentence
                            })), main_loop)
                    
                    # Apply deduplication to remove repetitions
                    cleaned_sentence = dedupe_repetition(full_sentence)
                    
                    if main_loop is not None:
                        # Send stage 2: After deduplication
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 2,
                                'text': cleaned_sentence
                            })), main_loop)
                    
                    # Remove disfluencies and fillers
                    filtered_sentence = disfluency_filter.clean_text(cleaned_sentence)
                    
                    if main_loop is not None:
                        # Send stage 3: After filtering
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 3,
                                'text': filtered_sentence
                            })), main_loop)
                    
                    # Apply grammar correction (now fixed)
                    final_sentence = grammar.correct_text(filtered_sentence)
                    
                    if main_loop is not None:
                        # Send stage 4: After grammar correction
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 4,
                                'text': final_sentence
                            })), main_loop)
                        
                        # Send final result
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'fullSentence',
                                'text': final_sentence
                            })), main_loop)
                        
                        # Send stop signal to client
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'recording_complete'
                            })), main_loop)
                    print(f"\rOriginal: {full_sentence}")
                    print(f"\rCleaned: {cleaned_sentence}")
                    print(f"\rFiltered: {filtered_sentence}")
                    print(f"\rFinal: {final_sentence}")
                    # Stop recording after getting result
                    recording_active.clear()
            except Exception as e:
                print(f"Error in recorder thread: {e}")
                continue

    def decode_and_resample(audio_data, original_sample_rate, target_sample_rate):
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            num_original_samples = len(audio_np)
            num_target_samples = int(num_original_samples * target_sample_rate / original_sample_rate)
            resampled_audio = resample(audio_np, num_target_samples)
            return resampled_audio.astype(np.int16).tobytes()
        except Exception as e:
            print(f"Error in resampling: {e}")
            return audio_data

    async def echo(websocket):
        global client_websocket
        print("Client connected")
        client_websocket = websocket

        try:
            async for message in websocket:
                if not recorder_ready.is_set():
                    print("Recorder not ready")
                    continue

                try:
                    # Check if it's a control message
                    if isinstance(message, str):
                        control = json.loads(message)
                        if control.get('command') == 'start_recording':
                            recording_active.set()
                            print("Recording started by client")
                        elif control.get('command') == 'stop_recording':
                            recording_active.clear()
                            print("Recording stopped by client")
                        continue
                    
                    # Only process audio if recording is active
                    if not recording_active.is_set():
                        continue
                    
                    # Read the metadata length (first 4 bytes)
                    metadata_length = int.from_bytes(message[:4], byteorder='little')
                    # Get the metadata JSON string
                    metadata_json = message[4:4+metadata_length].decode('utf-8')
                    metadata = json.loads(metadata_json)
                    sample_rate = metadata['sampleRate']
                    # Get the audio chunk following the metadata
                    chunk = message[4+metadata_length:]
                    resampled_chunk = decode_and_resample(chunk, sample_rate, 16000)
                    recorder.feed_audio(resampled_chunk)
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            if client_websocket == websocket:
                client_websocket = None
            recording_active.clear()

    async def main():
        global main_loop
        main_loop = asyncio.get_running_loop()

        recorder_thread = threading.Thread(target=run_recorder)
        recorder_thread.daemon = True
        recorder_thread.start()
        recorder_ready.wait()

        print("Server started. Press Ctrl+C to stop the server.")
        async with websockets.serve(echo, "localhost", 8001):
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                print("\nShutting down server...")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        is_running = False
        recorder.stop()
        recorder.shutdown()
    finally:
        if recorder:
            del recorder
