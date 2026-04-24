"""
🤖 MusQuira Assistant — Central orchestrator.
"""

import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ai_brain      import AIBrain
from src.speech_engine import SpeechEngine
from src.automation    import SystemAutomation
from config            import WAKE_WORD, ASSISTANT_NAME


class Assistant:
    def __init__(self, on_user=None, on_reply=None, on_status=None, on_error=None):
        self.on_user   = on_user   or (lambda t: None)
        self.on_reply  = on_reply  or (lambda t: None)
        self.on_status = on_status or (lambda t: None)
        self.on_error  = on_error  or (lambda t: None)

        self.brain  = AIBrain()
        self.speech = SpeechEngine(status_cb=self.on_status, error_cb=self.on_error)
        self.auto   = SystemAutomation(speak_cb=self.speech.speak, status_cb=self.on_status)

        self.wake_word    = WAKE_WORD.lower()
        self.wake_enabled = True
        self.continuous   = False

    # ── Command Processor ─────────────────────────────────────────────────────

    def process(self, text: str):
        text = text.strip()
        if not text:
            return
        self.on_user(text)
        self.on_status("⚙️ Processing…")

        t = text.lower()

        # Confirmation flows
        if "confirm shutdown" in t:
            self._reply(self.auto.shutdown()); return
        if "confirm restart" in t:
            self._reply(self.auto.restart()); return
        if "cancel shutdown" in t:
            self._reply(self.auto.cancel_shutdown()); return

        data   = self.brain.classify_intent(text)
        intent = data["intent"]
        entity = data["entity"]

        handlers = {
            "open_app":    lambda: self.auto.open_app(entity),
            "close_app":   lambda: self.auto.close_app(entity),
            "web_search":  lambda: self.auto.google_search(entity),
            "youtube":     lambda: self.auto.youtube_search(entity),
            "weather":     lambda: self.auto.get_weather(entity),
            "time":        lambda: self.auto.get_time(),
            "date":        lambda: self.auto.get_date(),
            "screenshot":  lambda: self.auto.screenshot(),
            "volume_up":   lambda: self.auto.volume_up(),
            "volume_down": lambda: self.auto.volume_down(),
            "mute":        lambda: self.auto.mute(),
            "system_info": lambda: self.auto.system_info(),
            "shutdown":    lambda: f"Say 'confirm shutdown' to proceed.",
            "restart":     lambda: f"Say 'confirm restart' to proceed.",
            "clear_memory":lambda: self._clear_memory(),
        }

        if intent in handlers:
            result = handlers[intent]()
            if intent not in ("web_search","youtube","open_app","close_app","screenshot","weather"):
                self.speech.speak(result)
            self._reply(result)
        else:
            result = self.brain.think(text)
            self.speech.speak(result)
            self._reply(result)

    def _reply(self, text: str):
        self.on_reply(text)
        self.on_status("✅ Ready")

    def _clear_memory(self) -> str:
        self.brain.clear()
        return "Memory cleared. Starting fresh!"

    # ── Listening ─────────────────────────────────────────────────────────────

    def listen_once(self):
        def _run():
            self.on_status("👂 Listening…")
            text = self.speech.listen_once()
            if text:
                self.process(text)
            else:
                self.on_status("❌ Nothing heard.")
        threading.Thread(target=_run, daemon=True).start()

    def start_continuous(self):
        self.continuous = True
        self.on_status(f"🔁 Continuous — say \"{WAKE_WORD}\"")

        def on_phrase(text: str):
            if not self.continuous:
                return
            tl = text.lower()
            if self.wake_enabled:
                if self.wake_word in tl:
                    cmd = tl.replace(self.wake_word, "").strip()
                    if cmd:
                        self.process(cmd)
                    else:
                        self.speech.speak("Yes? How can I help?")
                        follow = self.speech.listen_once()
                        if follow:
                            self.process(follow)
            else:
                self.process(text)

        self.speech.start_continuous(on_phrase)

    def stop_continuous(self):
        self.continuous = False
        self.speech.stop_continuous()
        self.on_status("✅ Ready")

    def toggle_wake(self, enabled: bool):
        self.wake_enabled = enabled

    def memory_info(self) -> str:
        return self.brain.memory_summary()

    def clear_memory(self):
        self.brain.clear()
