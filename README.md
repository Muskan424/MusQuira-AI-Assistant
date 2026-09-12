# 🤖 MusQuira —  AI Voice Assistant

> *"Good evening. I am MusQuira, your advanced AI assistant."*

A full-featured, GPT-powered voice assistant with a **JARVIS-inspired holographic UI**, face recognition login, desktop automation, and real-time AI responses.

---

## ✨ Features

| Feature | Details |
|---|---|
| 👁️ Face Recognition Login | Enroll your face once; auto-login via webcam |
| 🎙️ Smart Voice Input | One-shot mic button + always-on continuous mode |
| 🔔 Wake Word | "Hey MusQuira" activates the assistant in continuous mode |
| 🤖 GPT Intelligence | OpenAI GPT-3.5/4 — full conversational AI |
| 🖥️ Full Desktop Control | Open/close apps, volume, screenshots, shutdown |
| 🌐 Web Integration | Google search, YouTube, live weather |
| 🧠 Context Memory | Remembers last 16 exchanges for smart follow-ups |
| 📊 System Stats | Live CPU, RAM, Disk usage in sidebar |
| 🎨 JARVIS UI | Animated arc reactor, holographic HUD, chat bubbles |

---

## 🚀 Setup (3 steps)

### Step 1 — Install Python 3.10+
Download from **https://python.org** — check ✅ **"Add Python to PATH"**

### Step 2 — Install dependencies

```bash
# Double-click install.bat  OR run in terminal:
pip install -r requirements.txt
```

> **PyAudio error on Windows?**
> ```
> pip install pipwin
> pipwin install pyaudio
> ```

> **face_recognition install error?**
> ```
> pip install cmake dlib face-recognition
> ```
> Or skip face login by setting `ENABLE_FACE_LOGIN = False` in config.py

### Step 3 — Set your API key

Open **`config.py`** and replace:

```python
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
```

Get your key at: **https://platform.openai.com/api-keys**

### Step 4 — Run!

```bash
python main.py
# or double-click run.bat
```

---

## 👁️ Face Recognition Login

1. On the login screen, click **"ENROLL FACE"**
2. Type your name and look at the camera (takes ~5 seconds)
3. Next time, click **"FACE LOGIN"** — it recognizes you automatically!

To skip face login: set `ENABLE_FACE_LOGIN = False` in config.py

---

## 🗣️ Voice Commands

### Apps
```
"Open Notepad"       "Open Chrome"       "Open VS Code"
"Open Calculator"    "Open Spotify"      "Open Terminal"
"Close notepad"      "Close chrome"
```

### Web
```
"Search for machine learning tutorials"
"Play lo-fi hip hop on YouTube"
"What's the weather in Mumbai?"
```

### System
```
"What time is it?"     "Today's date?"
"Take a screenshot"    "Volume up / down / mute"
"System info"          "Shutdown" (say "confirm shutdown" to proceed)
```

### AI Conversation
```
"Explain black holes in simple terms"
"Write a Python function to sort a list"
"Tell me a joke"
"What is the meaning of life?"
```

### Context-Aware
```
"Open YouTube"
→ "Play jazz music"    ← MusQuira remembers you meant YouTube
```

### Memory
```
"Clear memory"   →   Resets conversation history
```

---

## ⚙️ Configuration (`config.py`)

| Key | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required** |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Use `gpt-4o` for smarter responses |
| `WEATHER_API_KEY` | — | Free at openweathermap.org |
| `WAKE_WORD` | `hey musquira` | Activation phrase in continuous mode |
| `ENABLE_FACE_LOGIN` | `True` | Set `False` to skip face login |
| `DEFAULT_CITY` | `Delhi` | Your city for weather queries |
| `VOICE_GENDER` | `female` | `"male"` or `"female"` |
| `CONTEXT_WINDOW` | `16` | Messages kept in memory |

---

## 📁 Project Structure

```
musquira/
├── main.py              ← Launch here
├── config.py            ← All settings & keys
├── requirements.txt
├── install.bat          ← Windows installer
├── run.bat              ← Windows launcher
├── data/
│   └── faces/           ← Enrolled face data (auto-created)
└── src/
    ├── gui.py           ← Full JARVIS UI (login + main)
    ├── assistant.py     ← Orchestrator
    ├── ai_brain.py      ← GPT + intent classification
    ├── speech_engine.py ← Mic + TTS
    ├── automation.py    ← Desktop control
    └── face_auth.py     ← Face recognition login
```

---

## 🔧 Troubleshooting

**face_recognition won't install?**
Install Visual C++ Build Tools first from Microsoft, then:
```
pip install cmake dlib face-recognition
```
Or just disable it: `ENABLE_FACE_LOGIN = False`

**Mic not working?**
Windows Settings → Privacy → Microphone → Allow access

**App not opening?**
Update the path in `APP_PATHS` in config.py for your system

---

*MusQuira — Powered by OpenAI GPT & Python*
I am learning Git and GitHub.
This change is made on my practice branch.
