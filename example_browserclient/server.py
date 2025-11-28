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
    import csv
    import os
    from datetime import datetime
    from fuzzywuzzy import fuzz
    from grammar_processor import GrammarProcessor
    from tone_controller import ToneController
    from disfluency_filter import DisfluencyFilter
    from auto_formatter import AutoFormatter
    from feedback_memory import FeedbackMemory
    from database import TranscriptionDatabase

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('websockets').setLevel(logging.WARNING)

    # Initialize processors
    grammar = GrammarProcessor()
    tone_controller = ToneController()
    disfluency_filter = DisfluencyFilter()
    auto_formatter = AutoFormatter()
    
    # Initialize database
    db = TranscriptionDatabase()
    
    # Initialize feedback memory (no API needed)
    feedback_memory = FeedbackMemory()
    
    # Default tone mode
    current_tone_mode = 'neutral'
    current_transcription_id = None
    
    print(f"📊 Database stats: {db.get_stats()}")
    print("🔧 Rule-based auto-improvement enabled")

    is_running = True
    recorder = None
    recorder_ready = threading.Event()
    client_websocket = None
    main_loop = None  # This will hold our primary event loop
    
    # CSV log file for transcripts
    log_file = 'transcription_log.csv'
    
    def log_transcript(original, final, latency_ms, tone_mode):
        """Log transcript to CSV file with timestamp and latency"""
        try:
            file_exists = False
            try:
                with open(log_file, 'r'):
                    file_exists = True
            except FileNotFoundError:
                pass
            
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Timestamp', 'Original', 'Final', 'Latency (ms)', 'Tone Mode'])
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    original,
                    final,
                    latency_ms,
                    tone_mode
                ])
        except Exception as e:
            print(f"Error logging to CSV: {e}")

    def dedupe_repetition(text: str, window=8, score_thresh=85) -> str:
        """
        Advanced deduplication to remove repeated phrases.
        Uses sliding window with fuzzy matching to catch ASR repetitions.
        """
        if not text or len(text.strip()) == 0:
            return text
        
        tokens = text.split()
        if len(tokens) <= 1:
            return text
        
        i = 0
        out_tokens = []
        N = len(tokens)
        removed_count = 0
        
        while i < N:
            # Try larger windows first (more likely to be meaningful phrases)
            w = min(window, N - i)
            found_repeat = False
            
            for k in range(w, 0, -1):  # Start from largest window
                if i + k > N:
                    continue
                    
                seg = ' '.join(tokens[i:i+k])
                
                # Check if next k tokens repeat
                if i + k*2 <= N:
                    next_seg = ' '.join(tokens[i+k:i+2*k])
                    
                    # Use fuzzy match to handle ASR variations
                    similarity = fuzz.ratio(seg.lower(), next_seg.lower())
                    
                    if similarity >= score_thresh:
                        # Found repetition - keep first occurrence, skip second
                        out_tokens.extend(tokens[i:i+k])
                        i += 2*k
                        found_repeat = True
                        removed_count += k
                        print(f"🔄 Removed repetition: '{seg}' (similarity: {similarity}%)")
                        break
            
            if not found_repeat:
                out_tokens.append(tokens[i])
                i += 1
        
        result = ' '.join(out_tokens)
        
        # Additional pass: Remove immediate word repetitions (e.g., "the the", "I I")
        result = remove_immediate_duplicates(result)
        
        if removed_count > 0:
            print(f"✓ Deduplication: Removed {removed_count} repeated words")
        
        return result
    
    def remove_immediate_duplicates(text: str) -> str:
        """Remove immediate word repetitions like 'the the' or 'I I I'"""
        tokens = text.split()
        if len(tokens) <= 1:
            return text
        
        result = [tokens[0]]
        for i in range(1, len(tokens)):
            # Only add if different from previous word (case-insensitive)
            if tokens[i].lower() != tokens[i-1].lower():
                result.append(tokens[i])
            else:
                print(f"🔄 Removed immediate duplicate: '{tokens[i]}'")
        
        return ' '.join(result)

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
        'model': 'tiny.en',  # Fastest Whisper model
        'language': 'en',
        'silero_sensitivity': 0.5,
        'webrtc_sensitivity': 3,
        'post_speech_silence_duration': 3.0,  # 3 second pause to end transcription
        'min_length_of_recording': 0.2,
        'min_gap_between_recordings': 0,
        'enable_realtime_transcription': False,
        'beam_size': 1,  # Greedy decoding for maximum speed
        'initial_prompt': None,  # Skip prompt processing
        'suppress_tokens': [-1],  # Minimal token suppression
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
                
                import time
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
                
                MAX_LATENCY = 1.5  # Maximum allowed latency in seconds (for processing only)
                
                # Get transcription (not counted in latency)
                transcription_start = time.time()
                full_sentence = recorder.text()
                transcription_time = time.time() - transcription_start
                print(f"⏱️ Transcription: {transcription_time:.3f}s")
                
                # Start latency timer AFTER transcription
                start_time = time.time()
                
                if full_sentence:
                    # Check for high-confidence learned corrections only
                    # Only apply if exact match with 3+ approvals
                    learned_output = None
                    exact_match = db.check_exact_match(full_sentence, current_tone_mode)
                    
                    if exact_match:
                        # Check if this correction has been approved multiple times
                        cursor = db.conn.cursor()
                        cursor.execute('''
                            SELECT COUNT(*) as count FROM corrections
                            WHERE LOWER(original_text) = LOWER(?) 
                            AND corrected_output = ?
                            AND tone_mode = ?
                        ''', (full_sentence, exact_match, current_tone_mode))
                        correction_count = cursor.fetchone()['count']
                        
                        # Only use if seen 3+ times (high confidence)
                        if correction_count >= 3:
                            learned_output = exact_match
                            print(f"🧠 High-confidence learned correction ({correction_count}x): {learned_output}")
                    
                    if learned_output:
                        # Use learned output
                        final_sentence = learned_output
                        if main_loop is not None:
                            asyncio.run_coroutine_threadsafe(
                                send_to_client(json.dumps({
                                    'type': 'stage',
                                    'stage': 1,
                                    'text': full_sentence
                                })), main_loop)
                            asyncio.run_coroutine_threadsafe(
                                send_to_client(json.dumps({
                                    'type': 'fullSentence',
                                    'text': final_sentence
                                })), main_loop)
                            total_time = time.time() - start_time
                            asyncio.run_coroutine_threadsafe(
                                send_to_client(json.dumps({
                                    'type': 'recording_complete',
                                    'latency': int(total_time * 1000),
                                    'learned': True
                                })), main_loop)
                        recording_active.clear()
                        continue
                    
                    if main_loop is not None:
                        # Send stage 1: Original transcription
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 1,
                                'text': full_sentence
                            })), main_loop)
                    
                    # Apply deduplication to remove repetitions (fast operation)
                    cleaned_sentence = dedupe_repetition(full_sentence)
                    
                    if main_loop is not None:
                        # Send stage 2: After deduplication
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 2,
                                'text': cleaned_sentence
                            })), main_loop)
                    
                    # Remove disfluencies and fillers (fast operation)
                    filtered_sentence = disfluency_filter.clean_text(cleaned_sentence)
                    
                    if main_loop is not None:
                        # Send stage 3: After filtering
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 3,
                                'text': filtered_sentence
                            })), main_loop)
                    
                    # Calculate remaining time budget for processing
                    elapsed = time.time() - start_time
                    remaining_time = MAX_LATENCY - elapsed - 0.05  # Reserve 0.05s for final steps
                    
                    if remaining_time <= 0.1:
                        # Not enough time left, skip grammar correction
                        final_sentence = filtered_sentence
                        corrected_sentence = filtered_sentence
                        toned_sentence = filtered_sentence
                        print(f"⚠️ Time budget exceeded ({elapsed:.3f}s), using filtered text")
                    else:
                        # Try to complete grammar correction within strict time budget
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            try:
                                # Give grammar correction max 0.3s or remaining time, whichever is less
                                grammar_timeout = min(0.3, remaining_time - 0.1)
                                future = executor.submit(grammar.correct_text, filtered_sentence)
                                corrected_sentence = future.result(timeout=grammar_timeout)
                                print(f"After grammar: {corrected_sentence}")
                            except FuturesTimeoutError:
                                corrected_sentence = filtered_sentence
                                print(f"⚠️ Grammar correction timeout, using filtered text")
                        
                        # Apply tone transformation (fast operation)
                        tone_start = time.time()
                        toned_sentence = tone_controller.transform(corrected_sentence, current_tone_mode)
                        print(f"After tone ({current_tone_mode}): {toned_sentence}")
                        print(f"⏱️ Tone: {time.time() - tone_start:.3f}s")
                        
                        # Apply auto-formatting (fast operation)
                        format_start = time.time()
                        final_sentence = auto_formatter.format_text(toned_sentence, use_paragraphs=True)
                        print(f"After formatting: {final_sentence}")
                        print(f"⏱️ Formatting: {time.time() - format_start:.3f}s")
                    
                    if main_loop is not None:
                        # Send stage 4: After grammar correction
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 4,
                                'text': corrected_sentence
                            })), main_loop)
                        
                        # Send stage 5: After tone transformation
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'stage',
                                'stage': 5,
                                'text': toned_sentence
                            })), main_loop)
                        
                        # Send final result
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'fullSentence',
                                'text': final_sentence
                            })), main_loop)
                        
                        total_time = time.time() - start_time
                        
                        # Warn if processing exceeded target
                        if total_time > MAX_LATENCY:
                            print(f"⚠️ Processing exceeded {MAX_LATENCY}s target: {total_time:.3f}s")
                        
                        # Store in database
                        global current_transcription_id
                        current_transcription_id = db.store_transcription({
                            'original': full_sentence,
                            'cleaned': cleaned_sentence,
                            'filtered': filtered_sentence,
                            'grammar_corrected': corrected_sentence,
                            'tone_transformed': toned_sentence,
                            'final_output': final_sentence,
                            'tone_mode': current_tone_mode,
                            'latency_ms': int(total_time * 1000),
                            'transcription_time_ms': int(transcription_time * 1000),
                            'processing_time_ms': int(total_time * 1000)
                        })
                        
                        # Log to CSV file (legacy)
                        log_transcript(full_sentence, final_sentence, int(total_time * 1000), current_tone_mode)
                        
                        # Send stop signal to client with latency
                        asyncio.run_coroutine_threadsafe(
                            send_to_client(json.dumps({
                                'type': 'recording_complete',
                                'latency': int(total_time * 1000)  # Convert to milliseconds
                            })), main_loop)
                    else:
                        total_time = time.time() - start_time
                    print(f"\rOriginal: {full_sentence}")
                    print(f"\rCleaned: {cleaned_sentence}")
                    print(f"\rFiltered: {filtered_sentence}")
                    print(f"\rFinal: {final_sentence}")
                    print(f"\r⏱️  Total processing time: {total_time:.3f}s")
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
                        elif control.get('command') == 'set_tone':
                            global current_tone_mode
                            current_tone_mode = control.get('mode', 'neutral')
                            print(f"Tone mode changed to: {current_tone_mode}")
                        elif control.get('command') == 'get_history':
                            # Send recent history to client
                            limit = control.get('limit', 10)
                            recent = db.get_recent_transcriptions(limit)
                            history_data = []
                            for trans in recent:
                                history_data.append({
                                    'text': trans['final_output'],
                                    'latency': trans['latency_ms'],
                                    'timestamp': trans['timestamp']
                                })
                            await websocket.send(json.dumps({
                                'type': 'history_loaded',
                                'history': history_data
                            }))
                        elif control.get('command') == 'approve':
                            # User approves the output
                            original = control.get('original', '')
                            output = control.get('output', '')
                            tone_mode = control.get('tone_mode', current_tone_mode)
                            
                            # Store in database
                            db.store_feedback('approve', original, output, tone_mode, current_transcription_id)
                            feedback_memory.approve_output(original, output, tone_mode)
                            
                            stats = db.get_stats()
                            await websocket.send(json.dumps({
                                'type': 'feedback_received',
                                'message': '✓ Good output! System reinforced.',
                                'stats': stats
                            }))
                        elif control.get('command') == 'reject':
                            # User rejects the output
                            original = control.get('original', '')
                            output = control.get('output', '')
                            tone_mode = control.get('tone_mode', current_tone_mode)
                            
                            # Store in database
                            db.store_feedback('reject', original, output, tone_mode, current_transcription_id)
                            feedback_memory.reject_output(original, output, tone_mode)
                            
                            # Don't send feedback_received here - let user edit first
                            # The message will be sent after they submit their correction
                        elif control.get('command') == 'auto_improve':
                            # Auto-improve using ChatGPT
                            original = control.get('original', '')
                            wrong_output = control.get('wrong_output', '')
                            tone_mode = control.get('tone_mode', current_tone_mode)
                            
                            # Use rule-based auto-correction
                            correction = feedback_memory.auto_improve(original, wrong_output, tone_mode)
                            
                            if correction:
                                # Store in database
                                db.store_correction(original, wrong_output, correction, 'auto', tone_mode, current_transcription_id)
                                stats = db.get_stats()
                                await websocket.send(json.dumps({
                                    'type': 'auto_improved',
                                    'correction': correction,
                                    'message': '🔧 Rule-based correction applied and system learned!',
                                    'stats': stats
                                }))
                            else:
                                stats = db.get_stats()
                                error_message = '⚠️ Auto-correction unavailable. Please provide manual correction.'
                                await websocket.send(json.dumps({
                                    'type': 'auto_improve_failed',
                                    'message': error_message,
                                    'stats': stats
                                }))
                        elif control.get('command') == 'feedback':
                            # Manual correction
                            original = control.get('original', '')
                            system_output = control.get('system_output', '')
                            user_correction = control.get('user_correction', '')
                            tone_mode = control.get('tone_mode', current_tone_mode)
                            
                            # Store in database
                            db.store_correction(original, system_output, user_correction, 'manual', tone_mode, current_transcription_id)
                            feedback_memory.add_correction(original, system_output, user_correction, tone_mode)
                            
                            stats = db.get_stats()
                            await websocket.send(json.dumps({
                                'type': 'feedback_received',
                                'message': '✓ Manual correction stored!',
                                'stats': stats
                            }))
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
