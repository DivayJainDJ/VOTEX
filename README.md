VOTEX — Real-Time Offline Speech-to-Text Engine

VOTEX is a lightweight, fast, and fully offline **real-time speech-to-text (STT) system designed for personal assistants, automation tools, accessibility applications, and voice-controlled interfaces.

Powered by Whisper, VOTEX processes audio locally and provides low-latency transcription with no internet connection required.

---

🚀 Features

🔊 Real-Time Transcription  
Transcribes speech as you speak with smooth, continuous updates.

📴 Fully Offline  
No cloud services. No API calls.  
Your audio stays on your device.

⚡ Fast & Lightweight  
Optimized to run even on laptops without GPUs.

🧩 Customizable  
Configure:
- Audio sensitivity  
- Silence detection  
- Model size  
- Thresholds  
- Recording parameters  

🎙 Built-in VAD (Voice Activity Detection)  
Automatically detects when you start/stop speaking.

🛠 Modular Design  
Includes:
- STT server  
- CLI client  
- Optional web interface  
- Audio processing utilities  

---

🏗 Architecture Overview


+-------------------------+
|       VOTEX SERVER      |
|  (Audio + Whisper STT)  |
+-----------+-------------+
            |
         WebSocket
            |
+-----------+-------------+
|            CLIENTS      |
|  - CLI Transcriber      |
|  - Browser Interface    |
|  - Custom Apps          |
+-------------------------+


---

📦 Installation

1. Clone the Repository**
sh
git clone https://github.com/MUKUL-PRASAD-SIGH/VOTEXNEW.git
cd VOTEXNEW

2. Create Python Environment**
sh
conda create -n votex python=3.10
conda activate votex

3. Install Dependencies**
sh
pip install -r requirements.txt

4. (macOS Only) Install Audio Dependencies**
sh
brew install portaudio ffmpeg


---

▶️ Running VOTEX

Terminal 1 — Start the STT Server**
sh
conda activate votex
cd VOTEXNEW
python -m RealtimeSTT_server.stt_server

You should see:

Control server started on ws://localhost:8011
Data server started on ws://localhost:8012


---

### **Terminal 2 — Start the CLI Transcriber**

#### List available microphones:
sh
python -m sounddevice

Example output:
0 MacBook Microphone
1 MacBook Speakers

Start continuous transcription:
sh
python RealtimeSTT_server/stt_cli_client.py -i 0 --continous

Where `-i 0` selects mic device index 0.

---

## 🌐 Optional: Launch Web Interface

sh
cd example_webserver
python server.py

Open the link shown in the terminal (e.g., http://localhost:8000).

---

🛠 Customization

Change STT Model
Edit:

RealtimeSTT_server/stt_server.py


Example:
python
model="medium"
language="en"


Adjust VAD + Silence Detection
Tune:
- post_silence  
- early_transcription  
- sensitivity  
- min recording length  

(These parameters are inside the server config.)

Adjust from CLI:
sh
-s PARAM VALUE


---

📂 Project Structure


VOTEXNEW/
│── RealtimeSTT/
│── RealtimeSTT_server/
│── example_app/
│── example_webserver/
│── tests/
│── requirements.txt
│── setup.py
│── README.md


---

👨‍💻 Developers

VOTEX Team**
- Divay Jain  
- Mukul Prasad Singh  
- (Add more contributors here)

---

📜 License
Released under the MIT License.

---

⭐ Support Us

If VOTEX helped you, please ⭐ star the repository.  
It motivates us to develop further improvements!

