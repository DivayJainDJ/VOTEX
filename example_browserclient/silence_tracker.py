"""
Silence Tracker for Real-time STT
Tracks actual silence duration during recording for paragraph detection
"""

import time
import threading


class SilenceTracker:
    """
    Tracks silence duration in real-time during audio recording
    Works with RealtimeSTT to detect sentence vs paragraph breaks
    """
    
    def __init__(self):
        self.last_speech_time = time.time()
        self.silence_start_time = None
        self.is_currently_silent = False
        self.last_silence_duration = 0.0
        self.lock = threading.Lock()
        
        print("🔇 Silence Tracker initialized")
    
    def mark_speech(self):
        """Call when speech/voice is detected"""
        with self.lock:
            self.last_speech_time = time.time()
            if self.is_currently_silent:
                # Silence just ended
                if self.silence_start_time:
                    self.last_silence_duration = time.time() - self.silence_start_time
                self.is_currently_silent = False
                self.silence_start_time = None
    
    def mark_silence(self):
        """Call when silence is detected"""
        with self.lock:
            if not self.is_currently_silent:
                # Silence just started
                self.is_currently_silent = True
                self.silence_start_time = time.time()
    
    def get_current_silence_duration(self) -> float:
        """Get current ongoing silence duration in seconds"""
        with self.lock:
            if self.is_currently_silent and self.silence_start_time:
                return time.time() - self.silence_start_time
            return 0.0
    
    def get_last_silence_duration(self) -> float:
        """Get the duration of the last completed silence period"""
        with self.lock:
            return self.last_silence_duration
    
    def reset(self):
        """Reset tracker state"""
        with self.lock:
            self.last_speech_time = time.time()
            self.silence_start_time = None
            self.is_currently_silent = False
            self.last_silence_duration = 0.0
    
    def get_stats(self) -> dict:
        """Get current tracker statistics"""
        with self.lock:
            return {
                'is_silent': self.is_currently_silent,
                'current_silence': self.get_current_silence_duration(),
                'last_silence': self.last_silence_duration,
                'time_since_speech': time.time() - self.last_speech_time
            }


# Example usage
if __name__ == "__main__":
    import time
    
    print("="*70)
    print("SILENCE TRACKER - TEST")
    print("="*70)
    print()
    
    tracker = SilenceTracker()
    
    # Simulate speech and silence
    print("Simulating speech pattern:\n")
    
    # Speech
    print("Speaking...")
    tracker.mark_speech()
    time.sleep(0.5)
    
    # Short silence
    print("Short silence (1s)...")
    tracker.mark_silence()
    time.sleep(1.0)
    print(f"  Current silence: {tracker.get_current_silence_duration():.2f}s")
    
    # Speech again
    print("Speaking again...")
    tracker.mark_speech()
    print(f"  Last silence was: {tracker.get_last_silence_duration():.2f}s")
    time.sleep(0.5)
    
    # Long silence
    print("Long silence (3s)...")
    tracker.mark_silence()
    time.sleep(3.0)
    print(f"  Current silence: {tracker.get_current_silence_duration():.2f}s")
    
    # Speech
    print("Speaking...")
    tracker.mark_speech()
    print(f"  Last silence was: {tracker.get_last_silence_duration():.2f}s")
    
    print("\nStats:", tracker.get_stats())
    
    print("\n" + "="*70)
    print("✓ Test complete!")
