"""
⚙️  MusQuira Configuration
Edit this file to set your API keys and preferences.
"""

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"      # platform.openai.com
WEATHER_API_KEY     = "YOUR_OPENWEATHERMAP_API_KEY_HERE"   # openweathermap.org (free)

# ── OpenAI Settings ───────────────────────────────────────────────────────────
OPENAI_MODEL        = "gpt-3.5-turbo"   # or "gpt-4o"
OPENAI_MAX_TOKENS   = 400
OPENAI_TEMPERATURE  = 0.75

SYSTEM_PROMPT = """You are MusQuira, a highly intelligent AI assistant with the personality of JARVIS from Iron Man.
You are sharp, witty, precise, and always helpful. You address the user respectfully.
Keep responses concise (2-3 sentences) unless asked for detail.
You can control the computer, search the web, and answer any question intelligently.
When you perform system actions, briefly confirm what you did."""

# ── Wake Word ─────────────────────────────────────────────────────────────────
WAKE_WORD           = "hey musquira"
ASSISTANT_NAME      = "MusQuira"

# ── Voice ─────────────────────────────────────────────────────────────────────
VOICE_RATE          = 170
VOICE_VOLUME        = 1.0
VOICE_GENDER        = "female"   # "male" or "female"

# ── Speech Recognition ────────────────────────────────────────────────────────
LISTEN_TIMEOUT      = 6
PHRASE_TIMEOUT      = 9
ENERGY_THRESHOLD    = 300
DYNAMIC_ENERGY      = True

# ── Memory ────────────────────────────────────────────────────────────────────
CONTEXT_WINDOW      = 16   # messages kept in memory

# ── Face Recognition ─────────────────────────────────────────────────────────
FACE_DATA_DIR       = "data/faces"
FACE_CONFIDENCE     = 0.55
ENABLE_FACE_LOGIN   = True

# ── Weather ───────────────────────────────────────────────────────────────────
DEFAULT_CITY        = "Delhi"
WEATHER_UNITS       = "metric"

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_W            = 1100
WINDOW_H            = 750

# ── App Paths (Windows) ───────────────────────────────────────────────────────
APP_PATHS = {
    "notepad":       "notepad.exe",
    "calculator":    "calc.exe",
    "paint":         "mspaint.exe",
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "explorer":      "explorer.exe",
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vscode":        r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify":       r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "discord":       r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe",
    "terminal":      "cmd.exe",
    "powershell":    "powershell.exe",
    "task manager":  "taskmgr.exe",
    "control panel": "control.exe",
}
