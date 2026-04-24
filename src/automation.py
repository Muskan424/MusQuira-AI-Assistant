"""
🖥️ System Automation — Full desktop control for MusQuira.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import subprocess, webbrowser, urllib.parse, datetime, platform, glob
from config import APP_PATHS, DEFAULT_CITY, WEATHER_API_KEY, WEATHER_UNITS


class SystemAutomation:
    def __init__(self, speak_cb=None, status_cb=None):
        self.speak  = speak_cb  or (lambda t: None)
        self.status = status_cb or (lambda t: None)
        self.os     = platform.system()
        self._pending_shutdown = False

    # ── Apps ─────────────────────────────────────────────────────────────────

    def open_app(self, name: str) -> str:
        name = name.lower().strip()
        aliases = {"browser":"chrome","file manager":"explorer","cmd":"terminal",
                   "command prompt":"terminal","code":"vscode","vs code":"vscode",
                   "music":"spotify","video":"vlc","files":"explorer"}
        name = aliases.get(name, name)
        path = APP_PATHS.get(name)
        if path:
            path = os.path.expandvars(path)
            try:
                subprocess.Popen([path])
                msg = f"Opening {name}."
            except:
                try:
                    subprocess.Popen([name])
                    msg = f"Launching {name}."
                except:
                    msg = f"Could not open {name}. Check the path in config.py."
        else:
            try:
                subprocess.Popen([name])
                msg = f"Opening {name}."
            except:
                msg = f"App '{name}' not configured. Add it to APP_PATHS."
        self.speak(msg)
        return msg

    def close_app(self, name: str) -> str:
        name = name.strip()
        if self.os == "Windows":
            exe = name if name.endswith(".exe") else name + ".exe"
            result = subprocess.run(["taskkill", "/f", "/im", exe],
                                    capture_output=True, text=True)
            msg = f"Closed {name}." if result.returncode == 0 else f"Could not close {name}."
        else:
            result = subprocess.run(["pkill", "-f", name], capture_output=True)
            msg = f"Closed {name}." if result.returncode == 0 else f"Could not close {name}."
        self.speak(msg)
        return msg

    # ── Web ───────────────────────────────────────────────────────────────────

    def google_search(self, query: str) -> str:
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        msg = f"Searching Google for: {query}"
        self.speak(msg); return msg

    def youtube_search(self, query: str) -> str:
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        msg = f"Playing {query} on YouTube."
        self.speak(msg); return msg

    # ── Weather ───────────────────────────────────────────────────────────────

    def get_weather(self, city: str = None) -> str:
        import requests
        city = city or DEFAULT_CITY
        if not WEATHER_API_KEY or "YOUR_" in WEATHER_API_KEY:
            return "Weather API key not set. Add it to config.py."
        try:
            url = (f"https://api.openweathermap.org/data/2.5/weather"
                   f"?q={city}&appid={WEATHER_API_KEY}&units={WEATHER_UNITS}")
            d = requests.get(url, timeout=5).json()
            if d.get("cod") == 200:
                sym  = "°C" if WEATHER_UNITS == "metric" else "°F"
                msg  = (f"Weather in {city}: {d['weather'][0]['description'].capitalize()}. "
                        f"Temp: {d['main']['temp']}{sym}, "
                        f"feels like {d['main']['feels_like']}{sym}. "
                        f"Humidity: {d['main']['humidity']}%.")
            else:
                msg = f"Could not get weather for {city}: {d.get('message','unknown error')}"
            self.speak(msg); return msg
        except Exception as e:
            return f"Weather error: {e}"

    # ── Time / Date ───────────────────────────────────────────────────────────

    def get_time(self) -> str:
        msg = f"The time is {datetime.datetime.now().strftime('%I:%M %p')}."
        self.speak(msg); return msg

    def get_date(self) -> str:
        msg = f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."
        self.speak(msg); return msg

    # ── System Info ───────────────────────────────────────────────────────────

    def system_info(self) -> str:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            msg  = (f"System: CPU at {cpu}%, "
                    f"RAM {ram.percent}% used ({ram.used//1024**3}GB / {ram.total//1024**3}GB), "
                    f"Disk {disk.percent}% used.")
            self.speak(msg); return msg
        except:
            return "psutil not installed — run: pip install psutil"

    # ── Volume / Media ────────────────────────────────────────────────────────

    def _send_key(self, char_code: int) -> str:
        if self.os == "Windows":
            subprocess.run(["powershell", "-c",
                f"(New-Object -ComObject WScript.Shell).SendKeys([char]{char_code})"],
                capture_output=True)

    def volume_up(self) -> str:
        self._send_key(175); return "Volume increased."

    def volume_down(self) -> str:
        self._send_key(174); return "Volume decreased."

    def mute(self) -> str:
        self._send_key(173); return "Audio toggled."

    # ── Screenshot ────────────────────────────────────────────────────────────

    def screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"MusQuira_{ts}.png")
            ImageGrab.grab().save(path)
            msg  = f"Screenshot saved to Desktop as MusQuira_{ts}.png"
            self.speak(msg); return msg
        except Exception as e:
            return f"Screenshot failed: {e}"

    # ── Shutdown / Restart ────────────────────────────────────────────────────

    def shutdown(self) -> str:
        if self.os == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "15"])
            return "Shutting down in 15 seconds. Say 'cancel shutdown' to abort."
        return "Shutdown not supported on this OS."

    def restart(self) -> str:
        if self.os == "Windows":
            subprocess.run(["shutdown", "/r", "/t", "15"])
            return "Restarting in 15 seconds."
        return "Restart not supported on this OS."

    def cancel_shutdown(self) -> str:
        if self.os == "Windows":
            subprocess.run(["shutdown", "/a"])
            return "Shutdown cancelled."
        return "Nothing to cancel."

    # ── File Search ───────────────────────────────────────────────────────────

    def find_file(self, name: str) -> str:
        dirs = [os.path.expanduser("~"),
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Downloads")]
        hits = []
        for d in dirs:
            hits.extend(glob.glob(os.path.join(d, "**", f"*{name}*"), recursive=True)[:3])
        if hits:
            msg = f"Found {len(hits)} file(s): {', '.join(os.path.basename(h) for h in hits[:3])}"
        else:
            msg = f"No files matching '{name}' found."
        self.speak(msg); return msg
