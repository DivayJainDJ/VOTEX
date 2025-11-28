VOTEX — Real-Time Speech-to-Text Engine

VOTEX is a lightweight real-time speech-to-text (STT) system using a Python WebSocket server with multiple clients (CLI, browser, and web UI). It supports real-time audio streaming, transcription, formatting, disfluency removal, grammar correction, and tone control.

---

🚀 Features
- Real-time low-latency transcription  
- Whisper-based STT (local & offline)  
- CLI microphone client  
- Browser & Web UI demos  
- Auto punctuation & formatting  
- Disfluency removal (uh, um, etc.)  
- Optional grammar & tone improvement (T5-based)  
- Works on CPU or GPU  
- Fully configurable (model, language, VAD, sensitivity)

---

🧱 Project Structure
VOTEX/
├── RealtimeSTT/ # STT utilities
├── RealtimeSTT_server/ # Core server + CLI client
├── example_webserver/ # Web UI demo
├── example_browserclient/ # Browser WebSocket demo
├── grammar-correction-model/ # T5 grammar/tone model
├── auto_formatter.py
├── disfluency_filter.py
└── requirements.txt / gpu.txt

yaml
Copy code

---

⚙️ Installation
bash
git clone https://github.com/DivayJainDJ/VOTEX.git
cd VOTEX
conda create -n votex python=3.10
conda activate votex
pip install -r requirements.txt
macOS:

bash
Copy code
brew install portaudio ffmpeg
GPU (optional):

bash
Copy code
pip install -r requirements-gpu.txt
▶️ Run the STT Server
bash
Copy code
python -m RealtimeSTT_server.stt_server
You’ll see:

nginx
Copy code
Control server: ws://localhost:8011
Data server:    ws://localhost:8012
Run CLI Client
bash
Copy code
python -m sounddevice      # find device index
python RealtimeSTT_server/stt_cli_client.py -i 0 --continous
🌐 Web & Browser Demos
Web UI:

bash
Copy code
cd example_webserver
python server.py
Browser WebSocket demo:

Copy code
example_browserclient/
✍️ Grammar & Tone (Optional)
Use:

grammar-correction-model/

auto_formatter.py

disfluency_filter.py

👥 Contributors

Akash Biswas

Divay Jain

Mukul Prasad

Arav Gupta

📜 License
MIT License.

⭐ Support
Star ⭐ the repo if you find VOTEX useful!

---






