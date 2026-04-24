"""
🎤 Speech Engine — Mic input + TTS output for MusQuira.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import speech_recognition as sr
import pyttsx3
import threading
from config import (VOICE_RATE, VOICE_VOLUME, VOICE_GENDER,
                    LISTEN_TIMEOUT, PHRASE_TIMEOUT, ENERGY_THRESHOLD, DYNAMIC_ENERGY)


class SpeechEngine:
    def __init__(self, status_cb=None, error_cb=None):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold    = ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY

        self.tts = pyttsx3.init()
        self._setup_tts()

        self._status = status_cb or (lambda m: None)
        self._error  = error_cb  or (lambda m: None)
        self._stop   = threading.Event()
        self._tts_lock = threading.Lock()
        self.is_listening = False

    def _setup_tts(self):
        self.tts.setProperty("rate",   VOICE_RATE)
        self.tts.setProperty("volume", VOICE_VOLUME)
        voices = self.tts.getProperty("voices") or []
        if voices:
            if VOICE_GENDER == "female":
                v = next((x for x in voices if "zira" in x.name.lower()
                          or "female" in x.name.lower() or "hazel" in x.name.lower()), voices[-1])
            else:
                v = next((x for x in voices if "david" in x.name.lower()
                          or "mark" in x.name.lower()), voices[0])
            self.tts.setProperty("voice", v.id)

    def speak(self, text: str):
        def _do():
            with self._tts_lock:
                try:
                    self.tts.say(text)
                    self.tts.runAndWait()
                except Exception as e:
                    self._error(f"TTS: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def listen_once(self) -> str | None:
        try:
            with sr.Microphone() as src:
                self._status("🔇 Calibrating mic…")
                self.recognizer.adjust_for_ambient_noise(src, duration=0.6)
                self._status("👂 Listening…")
                audio = self.recognizer.listen(src, timeout=LISTEN_TIMEOUT,
                                               phrase_time_limit=PHRASE_TIMEOUT)
                self._status("⚙️ Recognising…")
                return self.recognizer.recognize_google(audio).strip()
        except sr.WaitTimeoutError:
            self._status("⏱️ Timeout — nothing heard.")
        except sr.UnknownValueError:
            self._status("❓ Couldn't understand.")
        except sr.RequestError as e:
            self._error(f"Speech API: {e}")
        except OSError:
            self._error("Microphone not found.")
        return None

    def start_continuous(self, on_phrase):
        self._stop.clear()
        self.is_listening = True
        def _loop():
            while not self._stop.is_set():
                t = self.listen_once()
                if t:
                    on_phrase(t)
        threading.Thread(target=_loop, daemon=True).start()

    def stop_continuous(self):
        self._stop.set()
        self.is_listening = False
