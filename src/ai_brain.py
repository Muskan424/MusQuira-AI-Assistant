"""
🧠 MusQuira AI Brain — OpenAI GPT with context memory & intent routing.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import openai
from config import (OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS,
                    OPENAI_TEMPERATURE, SYSTEM_PROMPT, CONTEXT_WINDOW, DEFAULT_CITY)


class AIBrain:
    def __init__(self):
        self.client  = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.history = []
        self.last_intent = None
        self.last_entity = None

    # ── Core GPT call ─────────────────────────────────────────────────────────

    def think(self, user_msg: str, ctx_hint: str = "") -> str:
        full_msg = f"{user_msg} [{ctx_hint}]" if ctx_hint else user_msg
        self.history.append({"role": "user", "content": full_msg})
        if len(self.history) > CONTEXT_WINDOW * 2:
            self.history = self.history[-(CONTEXT_WINDOW * 2):]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history
        try:
            resp = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE,
            )
            reply = resp.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except openai.AuthenticationError:
            return "⚠️ Invalid OpenAI API key. Please update config.py."
        except openai.RateLimitError:
            return "⚠️ Rate limit reached. Please wait a moment."
        except openai.APIConnectionError:
            return "⚠️ Cannot reach OpenAI — check your internet connection."
        except Exception as e:
            return f"⚠️ AI Error: {str(e)}"

    # ── Intent Classification ─────────────────────────────────────────────────

    def classify_intent(self, text: str) -> dict:
        t = text.lower().strip()

        # System actions
        if any(w in t for w in ["open ", "launch ", "start ", "run "]):
            entity = self._extract_app(t)
            if entity:
                self.last_intent, self.last_entity = "open_app", entity
                return {"intent": "open_app", "entity": entity}

        if any(w in t for w in ["search ", "google ", "look up ", "find "]):
            q = self._after(t, ["search for","google","look up","search","find"])
            self.last_intent, self.last_entity = "web_search", q
            return {"intent": "web_search", "entity": q}

        if "youtube" in t or ("play" in t and self.last_intent == "youtube"):
            q = self._youtube_query(t)
            self.last_intent, self.last_entity = "youtube", q
            return {"intent": "youtube", "entity": q}

        if any(w in t for w in ["weather", "temperature", "forecast", "rain"]):
            city = self._city(t)
            return {"intent": "weather", "entity": city}

        if any(w in t for w in ["what time", "current time", "time is it"]):
            return {"intent": "time", "entity": None}

        if any(w in t for w in ["what date", "today's date", "what day", "today is"]):
            return {"intent": "date", "entity": None}

        if "screenshot" in t:
            return {"intent": "screenshot", "entity": None}

        if any(w in t for w in ["volume up", "increase volume", "louder", "turn up"]):
            return {"intent": "volume_up", "entity": None}

        if any(w in t for w in ["volume down", "decrease volume", "quieter", "turn down"]):
            return {"intent": "volume_down", "entity": None}

        if "mute" in t or "silence" in t:
            return {"intent": "mute", "entity": None}

        if "shutdown" in t or "turn off computer" in t or "power off" in t:
            return {"intent": "shutdown", "entity": None}

        if "restart" in t or "reboot" in t:
            return {"intent": "restart", "entity": None}

        if any(w in t for w in ["clear memory", "forget", "reset chat", "new conversation"]):
            return {"intent": "clear_memory", "entity": None}

        if any(w in t for w in ["cpu", "ram", "memory usage", "battery", "system info"]):
            return {"intent": "system_info", "entity": None}

        if "close " in t or "kill " in t or "quit " in t:
            app = self._after(t, ["close","kill","quit"]).strip()
            return {"intent": "close_app", "entity": app}

        # Context-aware follow-up
        if self.last_intent == "youtube" and "play" in t:
            return {"intent": "youtube", "entity": t}

        return {"intent": "ai_chat", "entity": text}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_app(self, t: str) -> str | None:
        from config import APP_PATHS
        apps = list(APP_PATHS.keys()) + ["browser","file manager","cmd","code","music","video"]
        for app in apps:
            if app in t:
                return app
        for trigger in ["open","launch","start","run"]:
            if trigger in t:
                rest = t.split(trigger, 1)[-1].strip().split()[0:1]
                if rest:
                    return rest[0]
        return None

    def _after(self, t: str, phrases: list) -> str:
        for p in sorted(phrases, key=len, reverse=True):
            if p in t:
                return t.split(p, 1)[-1].strip()
        return t

    def _youtube_query(self, t: str) -> str:
        for p in ["play on youtube","youtube play","play","on youtube","youtube"]:
            t = t.replace(p, "")
        return t.strip()

    def _city(self, t: str) -> str:
        for p in ["weather in","temperature in","forecast for","weather at","weather"]:
            if p in t:
                part = t.split(p, 1)[-1].strip().split()[0:2]
                if part:
                    return " ".join(part)
        return DEFAULT_CITY

    def clear(self):
        self.history.clear()
        self.last_intent = None
        self.last_entity = None

    def memory_summary(self) -> str:
        n = len(self.history) // 2
        return f"{n} exchange{'s' if n != 1 else ''} in memory"
