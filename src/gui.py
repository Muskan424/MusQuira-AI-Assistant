"""
🎨 MusQuira GUI — JARVIS-inspired UI with face-login, animated HUD, chat history.
"""

import sys, os, math, time, threading, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
from tkinter import font as tkfont, simpledialog, messagebox

from config import OPENAI_API_KEY, WINDOW_W, WINDOW_H, WAKE_WORD, ASSISTANT_NAME, ENABLE_FACE_LOGIN

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS  — JARVIS Holographic Blue
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "void":       "#000408",
    "deep":       "#020c14",
    "panel":      "#041220",
    "panel2":     "#071a2e",
    "border":     "#0a3a5c",
    "border2":    "#0d4f7a",
    "arc":        "#00aaff",
    "arc2":       "#0066cc",
    "glow":       "#00d4ff",
    "glow2":      "#00ffee",
    "amber":      "#ffaa00",
    "red":        "#ff3333",
    "green":      "#00ff88",
    "dim":        "#0a2030",
    "text":       "#c8e8ff",
    "text2":      "#6aadcc",
    "text3":      "#2a5a7a",
    "user_bg":    "#04213a",
    "ai_bg":      "#020f1e",
    "white":      "#e8f8ff",
}

F = {
    "hud":     ("Courier New", 28, "bold"),
    "title":   ("Courier New", 16, "bold"),
    "sub":     ("Courier New", 10),
    "body":    ("Courier New", 11),
    "small":   ("Courier New", 9),
    "tiny":    ("Courier New", 8),
    "chat":    ("Consolas", 11),
    "label":   ("Courier New", 9, "bold"),
}


# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATED ARC REACTOR (center orb)
# ══════════════════════════════════════════════════════════════════════════════

class ArcReactor(tk.Canvas):
    def __init__(self, parent, size=160, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=C["void"], highlightthickness=0, **kw)
        self.sz     = size
        self.cx     = size // 2
        self.cy     = size // 2
        self.angle  = 0
        self.pulse  = 0
        self.mode   = "idle"    # idle | listening | processing | speaking
        self._job   = None
        self._draw()

    def set_mode(self, mode: str):
        self.mode = mode

    def _draw(self):
        self.delete("all")
        cx, cy = self.cx, self.cy
        self.pulse = (self.pulse + 0.06) % (2 * math.pi)
        self.angle = (self.angle + 1.8) % 360
        pulse_factor = 0.5 + 0.5 * math.sin(self.pulse)

        col_map = {
            "idle":       C["arc"],
            "listening":  C["glow"],
            "processing": C["amber"],
            "speaking":   C["glow2"],
            "error":      C["red"],
        }
        col = col_map.get(self.mode, C["arc"])

        # ── Outer dim rings ────────────────────────────────────────────────
        for r, a in [(68, 0.10), (58, 0.14), (50, 0.20)]:
            self._oval(cx, cy, r, fill=self._alpha_blend(col, a))

        # ── Spinning arc segments ──────────────────────────────────────────
        for i, span in enumerate([90, 60, 45, 30]):
            start = self.angle + i * 95
            r     = 55 - i * 7
            w     = max(1, 3 - i)
            self.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=start, extent=span,
                            outline=col, width=w, style=tk.ARC)

        # ── Pulsing glow core ──────────────────────────────────────────────
        core_r = int(28 + 6 * pulse_factor)
        for r, f in [(core_r + 10, 0.08), (core_r + 5, 0.15), (core_r, 0.30)]:
            self._oval(cx, cy, r, fill=self._alpha_blend(col, f))
        self._oval(cx, cy, core_r - 4, fill=col)

        # ── Center dot ────────────────────────────────────────────────────
        self._oval(cx, cy, 6, fill=C["white"])

        # ── Crosshair lines ───────────────────────────────────────────────
        hl = 30
        for dx, dy in [(hl, 0), (-hl, 0), (0, hl), (0, -hl)]:
            self.create_line(cx, cy, cx + dx, cy + dy,
                             fill=self._alpha_blend(col, 0.25), width=1)

        # ── Mode text ─────────────────────────────────────────────────────
        mode_labels = {"idle":"STANDBY","listening":"LISTENING",
                       "processing":"PROCESSING","speaking":"SPEAKING","error":"ERROR"}
        label = mode_labels.get(self.mode, "STANDBY")
        self.create_text(cx, cy + 52, text=label, font=F["tiny"], fill=col)

        self._job = self.after(30, self._draw)

    def _oval(self, cx, cy, r, fill="", outline=""):
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=fill, outline=outline or "")

    def _alpha_blend(self, hex_col: str, alpha: float) -> str:
        r = int(hex_col[1:3], 16)
        g = int(hex_col[3:5], 16)
        b = int(hex_col[5:7], 16)
        br, bg, bb = int(C["void"][1:3], 16), int(C["void"][3:5], 16), int(C["void"][5:7], 16)
        return "#{:02x}{:02x}{:02x}".format(
            int(br + (r - br) * alpha),
            int(bg + (g - bg) * alpha),
            int(bb + (b - bb) * alpha),
        )

    def stop(self):
        if self._job:
            self.after_cancel(self._job)


# ══════════════════════════════════════════════════════════════════════════════
#  WAVEFORM BAR  (listening animation)
# ══════════════════════════════════════════════════════════════════════════════

class Waveform(tk.Canvas):
    def __init__(self, parent, w=300, h=40, **kw):
        super().__init__(parent, width=w, height=h,
                         bg=C["void"], highlightthickness=0, **kw)
        self.w, self.h = w, h
        self.active    = False
        self._t        = 0
        self._job      = None
        self._draw()

    def _draw(self):
        self.delete("all")
        if self.active:
            bars = 30
            bar_w = self.w / bars
            for i in range(bars):
                phase = self._t + i * 0.4
                ht    = int((math.sin(phase) * 0.5 + 0.5) * self.h * 0.85 + 3)
                x0    = i * bar_w + 1
                x1    = x0 + bar_w - 2
                y0    = (self.h - ht) // 2
                y1    = y0 + ht
                alpha = 0.4 + 0.6 * ((math.sin(phase) + 1) / 2)
                col   = self._blend(alpha)
                self.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
            self._t += 0.18
        else:
            y = self.h // 2
            self.create_line(0, y, self.w, y, fill=C["border"], width=1)
        self._job = self.after(40, self._draw)

    def _blend(self, alpha):
        r = int(0 + 170 * alpha); g = int(100 + 120 * alpha); b = int(200 + 55 * alpha)
        return f"#{min(255,r):02x}{min(255,g):02x}{min(255,b):02x}"

    def set_active(self, v: bool):
        self.active = v

    def stop(self):
        if self._job: self.after_cancel(self._job)


# ══════════════════════════════════════════════════════════════════════════════
#  SCAN LINE OVERLAY  (boot / face-login effect)
# ══════════════════════════════════════════════════════════════════════════════

class ScanOverlay(tk.Canvas):
    def __init__(self, parent, w, h, **kw):
        super().__init__(parent, width=w, height=h,
                         bg="", highlightthickness=0, **kw)
        self.w, self.h = w, h
        self._y   = 0
        self._job = None
        self._running = False

    def start(self):
        self._running = True
        self._animate()

    def _animate(self):
        if not self._running:
            return
        self.delete("all")
        self._y = (self._y + 3) % self.h
        # Scanline
        self.create_line(0, self._y, self.w, self._y, fill=C["glow"], width=2)
        # Dim overlay
        for y in range(0, self.h, 4):
            self.create_line(0, y, self.w, y, fill="#00000030", width=1)
        self._job = self.after(20, self._animate)

    def stop(self):
        self._running = False
        self.delete("all")
        if self._job:
            self.after_cancel(self._job)


# ══════════════════════════════════════════════════════════════════════════════
#  CHAT BUBBLE
# ══════════════════════════════════════════════════════════════════════════════

class Bubble(tk.Frame):
    def __init__(self, parent, text, role, ts="", **kw):
        super().__init__(parent, bg=C["void"], **kw)
        is_user = role == "user"

        outer = tk.Frame(self, bg=C["void"])
        outer.pack(fill=tk.X, pady=2)

        name = tk.Label(outer,
                        text="▶ YOU" if is_user else f"◆ {ASSISTANT_NAME.upper()}",
                        font=F["label"],
                        fg=C["amber"] if is_user else C["glow"],
                        bg=C["void"])
        name.pack(anchor="e" if is_user else "w", padx=4)

        bubble = tk.Frame(outer,
                          bg=C["user_bg"] if is_user else C["ai_bg"],
                          highlightbackground=C["amber"] if is_user else C["border2"],
                          highlightthickness=1,
                          padx=14, pady=8)
        bubble.pack(anchor="e" if is_user else "w",
                    padx=(80 if is_user else 4, 4 if is_user else 80))

        tk.Label(bubble, text=text, font=F["chat"],
                 fg=C["text"],
                 bg=C["user_bg"] if is_user else C["ai_bg"],
                 wraplength=520,
                 justify=tk.RIGHT if is_user else tk.LEFT).pack()

        if ts:
            tk.Label(outer, text=ts, font=F["tiny"],
                     fg=C["text3"], bg=C["void"]).pack(
                anchor="e" if is_user else "w", padx=4)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class LoginScreen(tk.Frame):
    def __init__(self, parent, on_success, on_skip, **kw):
        super().__init__(parent, bg=C["void"], **kw)
        self.on_success = on_success
        self.on_skip    = on_skip
        self._build()

    def _build(self):
        # Background grid lines (holographic effect)
        for i in range(0, 1200, 60):
            tk.Frame(self, bg=C["dim"], width=1, height=750).place(x=i, y=0)
        for j in range(0, 750, 60):
            tk.Frame(self, bg=C["dim"], width=1200, height=1).place(x=0, y=j)

        # Center card
        card = tk.Frame(self, bg=C["panel"],
                        highlightbackground=C["border2"],
                        highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # Arc
        self.arc = ArcReactor(card, size=140)
        self.arc.pack(pady=(30, 10))

        tk.Label(card, text="M U S Q U I R A", font=("Courier New", 22, "bold"),
                 fg=C["glow"], bg=C["panel"]).pack()
        tk.Label(card, text="ADVANCED AI ASSISTANT", font=F["sub"],
                 fg=C["text2"], bg=C["panel"]).pack(pady=(2, 0))
        tk.Label(card, text="─" * 38, fg=C["border2"], bg=C["panel"], font=F["small"]).pack(pady=6)

        self.status = tk.Label(card, text="INITIALIZING BIOMETRIC SCAN…",
                               font=F["small"], fg=C["text2"], bg=C["panel"])
        self.status.pack(pady=4)

        self.progress_var = tk.DoubleVar(value=0)
        prog_frame = tk.Frame(card, bg=C["panel"])
        prog_frame.pack(pady=6, padx=40, fill=tk.X)
        self.prog_canvas = tk.Canvas(prog_frame, height=4, bg=C["dim"],
                                     highlightthickness=0, width=320)
        self.prog_canvas.pack(fill=tk.X)

        btn_row = tk.Frame(card, bg=C["panel"])
        btn_row.pack(pady=(14, 8))

        self._mkbtn(btn_row, "👁  FACE LOGIN", self._face_login,  C["arc"]).pack(side=tk.LEFT, padx=6)
        self._mkbtn(btn_row, "ENROLL FACE",   self._enroll,       C["text3"]).pack(side=tk.LEFT, padx=6)
        self._mkbtn(btn_row, "SKIP LOGIN",    self.on_skip,       C["dim"]).pack(side=tk.LEFT, padx=6)

        tk.Label(card, text="v2.0  //  JARVIS-CLASS INTERFACE",
                 font=F["tiny"], fg=C["text3"], bg=C["panel"]).pack(pady=(4, 20))

    def _mkbtn(self, p, text, cmd, bg):
        b = tk.Button(p, text=text, font=F["small"], fg=C["text"],
                      bg=bg, relief=tk.FLAT, cursor="hand2",
                      padx=14, pady=6, command=cmd)
        b.bind("<Enter>", lambda e: b.configure(bg=C["border"]))
        b.bind("<Leave>", lambda e: b.configure(bg=bg))
        return b

    def _set_status(self, msg):
        self.after(0, lambda: self.status.configure(text=msg))

    def _set_progress(self, pct):
        def _draw():
            self.prog_canvas.delete("all")
            w = self.prog_canvas.winfo_width() or 320
            x = int(w * pct / 100)
            self.prog_canvas.create_rectangle(0, 0, x, 4, fill=C["glow"], outline="")
        self.after(0, _draw)

    def _face_login(self):
        self.arc.set_mode("processing")
        self._set_status("Activating camera…")
        def _run():
            from src.face_auth import recognize_face
            for i in range(0, 60, 5):
                self._set_progress(i)
                time.sleep(0.1)
            user = recognize_face(status_cb=self._set_status, timeout=18)
            self._set_progress(100)
            if user:
                self._set_status(f"IDENTITY CONFIRMED: {user.upper()}")
                self.arc.set_mode("idle")
                self.after(800, lambda: self.on_success(user))
            else:
                self._set_status("FACE NOT RECOGNISED — ACCESS DENIED")
                self.arc.set_mode("error")
        threading.Thread(target=_run, daemon=True).start()

    def _enroll(self):
        name = simpledialog.askstring("Enroll", "Enter your name:", parent=self)
        if not name:
            return
        self.arc.set_mode("processing")
        self._set_status(f"Enrolling {name}… look at camera.")
        def _run():
            from src.face_auth import enroll_face
            ok = enroll_face(name, status_cb=self._set_status)
            if ok:
                self._set_status(f"ENROLLED: {name.upper()} — You can now face login.")
                self.arc.set_mode("idle")
            else:
                self._set_status("ENROLLMENT FAILED — Check camera & lighting.")
                self.arc.set_mode("error")
        threading.Thread(target=_run, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class MusQuiraApp:
    def __init__(self, root: tk.Tk):
        self.root      = root
        self.username  = "User"
        self.assistant = None
        self._continuous = False

        root.title(f"MusQuira — JARVIS Interface")
        root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        root.configure(bg=C["void"])
        root.resizable(True, True)
        root.minsize(900, 620)

        if ENABLE_FACE_LOGIN:
            self._show_login()
        else:
            self._launch_main("User")

    # ── Login ─────────────────────────────────────────────────────────────────

    def _show_login(self):
        self._login_frame = LoginScreen(self.root,
                                        on_success=self._launch_main,
                                        on_skip=lambda: self._launch_main("Guest"))
        self._login_frame.place(x=0, y=0, relwidth=1, relheight=1)

    def _launch_main(self, username: str):
        self.username = username
        if hasattr(self, "_login_frame"):
            self._login_frame.destroy()
        self._build_main()
        self._init_assistant()
        self._check_key()
        self._greet()

    # ── Build Main UI ─────────────────────────────────────────────────────────

    def _build_main(self):
        root = self.root

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = tk.Frame(root, bg=C["panel"], height=52)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="◆  M U S Q U I R A",
                 font=("Courier New", 15, "bold"),
                 fg=C["glow"], bg=C["panel"]).pack(side=tk.LEFT, padx=20, pady=14)

        # Clock
        self.clock_lbl = tk.Label(topbar, text="", font=F["sub"],
                                  fg=C["text2"], bg=C["panel"])
        self.clock_lbl.pack(side=tk.LEFT, padx=20)
        self._tick_clock()

        # User badge
        tk.Label(topbar, text=f"◈  {self.username.upper()}",
                 font=F["label"], fg=C["amber"], bg=C["panel"]).pack(side=tk.RIGHT, padx=20)

        self.mem_lbl = tk.Label(topbar, text="MEM: 0 exchanges",
                                font=F["tiny"], fg=C["text3"], bg=C["panel"])
        self.mem_lbl.pack(side=tk.RIGHT, padx=10)

        # ── Main body ─────────────────────────────────────────────────────────
        body = tk.Frame(root, bg=C["void"])
        body.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left = tk.Frame(body, bg=C["panel"], width=210)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        self._build_left(left)

        # Center: Arc + chat
        center = tk.Frame(body, bg=C["void"])
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_center(center)

        # Right panel
        right = tk.Frame(body, bg=C["panel"], width=220)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)
        self._build_right(right)

        # ── Status bar ────────────────────────────────────────────────────────
        sbar = tk.Frame(root, bg=C["panel2"], height=28)
        sbar.pack(fill=tk.X, side=tk.BOTTOM)
        sbar.pack_propagate(False)
        self._sdot = tk.Label(sbar, text="●", font=F["body"],
                               fg=C["green"], bg=C["panel2"])
        self._sdot.pack(side=tk.LEFT, padx=(12, 4))
        self.status_lbl = tk.Label(sbar, text="SYSTEM ONLINE",
                                   font=F["small"], fg=C["text2"], bg=C["panel2"])
        self.status_lbl.pack(side=tk.LEFT)
        tk.Label(sbar, text=f"GPT │ OpenAI  //  {ASSISTANT_NAME.upper()} v2.0",
                 font=F["tiny"], fg=C["text3"], bg=C["panel2"]).pack(side=tk.RIGHT, padx=12)

    # ── Left Panel ────────────────────────────────────────────────────────────

    def _build_left(self, parent):
        self._hdr(parent, "QUICK COMMANDS")

        cmds = [
            ("▶ Notepad",           "open notepad"),
            ("▶ Chrome",            "open chrome"),
            ("▶ Calculator",        "open calculator"),
            ("▶ VS Code",           "open vscode"),
            ("▶ Terminal",          "open terminal"),
            ("▶ Task Manager",      "open task manager"),
            ("◈ Google Search",     "search for Python tips"),
            ("◈ YouTube",           "play lo-fi music on YouTube"),
            ("◈ Weather",           "what is the weather today"),
            ("◈ System Info",       "system info"),
            ("◈ Screenshot",        "take a screenshot"),
            ("◈ Time",              "what time is it"),
        ]
        for label, cmd in cmds:
            self._side_btn(parent, label, cmd)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=8, pady=10)
        self._hdr(parent, "CONTROLS")

        self.wake_var = tk.BooleanVar(value=True)
        tk.Checkbutton(parent,
                       text=f'Wake: "{WAKE_WORD}"',
                       variable=self.wake_var,
                       font=F["tiny"],
                       fg=C["text2"], bg=C["panel"],
                       selectcolor=C["panel2"],
                       activebackground=C["panel"],
                       command=self._toggle_wake).pack(padx=12, pady=4, anchor="w")

        self._side_btn(parent, "🧹 Clear Memory", "clear memory", color=C["amber"])

    def _hdr(self, parent, text):
        tk.Label(parent, text=text, font=F["tiny"],
                 fg=C["text3"], bg=C["panel"]).pack(pady=(12, 2), padx=12, anchor="w")

    def _side_btn(self, parent, label, cmd, color=None):
        color = color or C["panel2"]
        b = tk.Button(parent, text=label, font=F["tiny"],
                      fg=C["text"], bg=color,
                      relief=tk.FLAT, cursor="hand2",
                      anchor="w", padx=12,
                      command=lambda c=cmd: self._text_cmd(c))
        b.pack(fill=tk.X, padx=6, pady=1, ipady=5)
        b.bind("<Enter>", lambda e: b.configure(bg=C["border"]))
        b.bind("<Leave>", lambda e: b.configure(bg=color))

    # ── Center Panel ──────────────────────────────────────────────────────────

    def _build_center(self, parent):
        # Arc reactor
        arc_row = tk.Frame(parent, bg=C["void"])
        arc_row.pack(pady=(10, 0))

        self.arc = ArcReactor(arc_row, size=160)
        self.arc.pack(side=tk.LEFT, padx=20)

        # Waveform + status
        side_info = tk.Frame(arc_row, bg=C["void"])
        side_info.pack(side=tk.LEFT, fill=tk.Y, pady=10)

        tk.Label(side_info, text="AUDIO INPUT", font=F["tiny"],
                 fg=C["text3"], bg=C["void"]).pack(anchor="w")
        self.wave = Waveform(side_info, w=260, h=44)
        self.wave.pack(pady=4)

        tk.Label(side_info, text="STATUS", font=F["tiny"],
                 fg=C["text3"], bg=C["void"]).pack(anchor="w", pady=(8, 0))
        self.arc_status = tk.Label(side_info, text="STANDBY",
                                   font=F["sub"], fg=C["arc"], bg=C["void"])
        self.arc_status.pack(anchor="w")

        # Chat
        chat_hdr = tk.Frame(parent, bg=C["panel2"])
        chat_hdr.pack(fill=tk.X, pady=(8, 0))
        tk.Label(chat_hdr, text="◆  CONVERSATION LOG", font=F["label"],
                 fg=C["text2"], bg=C["panel2"]).pack(side=tk.LEFT, padx=14, pady=6)
        tk.Button(chat_hdr, text="CLEAR LOG", font=F["tiny"],
                  fg=C["text3"], bg=C["panel2"], relief=tk.FLAT,
                  cursor="hand2", command=self._clear_log).pack(side=tk.RIGHT, padx=10)

        # Scrollable chat
        chat_outer = tk.Frame(parent, bg=C["void"])
        chat_outer.pack(fill=tk.BOTH, expand=True)

        self.chat_canvas = tk.Canvas(chat_outer, bg=C["void"], highlightthickness=0)
        vscroll = tk.Scrollbar(chat_outer, orient="vertical",
                               command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_frame  = tk.Frame(self.chat_canvas, bg=C["void"])
        self._chat_win   = self.chat_canvas.create_window((0, 0),
                                                           window=self.chat_frame,
                                                           anchor="nw")
        self.chat_frame.bind("<Configure>",
                             lambda e: self.chat_canvas.configure(
                                 scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>",
                              lambda e: self.chat_canvas.itemconfig(
                                  self._chat_win, width=e.width))
        self.chat_canvas.bind("<MouseWheel>",
                              lambda e: self.chat_canvas.yview_scroll(
                                  int(-1 * (e.delta / 120)), "units"))

        # Input row
        inp_row = tk.Frame(parent, bg=C["panel"])
        inp_row.pack(fill=tk.X)

        self.mic_btn = tk.Button(inp_row, text="🎤", font=("Segoe UI Emoji", 16),
                                 bg=C["arc2"], fg=C["white"],
                                 relief=tk.FLAT, cursor="hand2", padx=10,
                                 command=self._toggle_mic)
        self.mic_btn.pack(side=tk.LEFT, padx=(10, 4), pady=10)

        self.text_var = tk.StringVar()
        self.entry = tk.Entry(inp_row, textvariable=self.text_var,
                              font=F["body"], fg=C["text"],
                              bg=C["panel2"], insertbackground=C["glow"],
                              relief=tk.FLAT, bd=0,
                              highlightthickness=1,
                              highlightbackground=C["border"],
                              highlightcolor=C["glow"])
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, pady=10)
        self.entry.bind("<Return>", self._on_enter)
        self._set_placeholder()

        tk.Button(inp_row, text="SEND", font=F["label"],
                  fg=C["void"], bg=C["glow"], relief=tk.FLAT,
                  cursor="hand2", padx=14, pady=10,
                  command=self._send_typed).pack(side=tk.LEFT, padx=(4, 4), pady=10)

        self.cont_btn = tk.Button(inp_row, text="▶ CONTINUOUS",
                                  font=F["tiny"],
                                  fg=C["text"], bg=C["arc2"],
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=10, pady=10,
                                  command=self._toggle_continuous)
        self.cont_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)

    # ── Right Panel ───────────────────────────────────────────────────────────

    def _build_right(self, parent):
        self._hdr(parent, "SYSTEM STATS")

        self.cpu_lbl  = self._stat_row(parent, "CPU")
        self.ram_lbl  = self._stat_row(parent, "RAM")
        self.disk_lbl = self._stat_row(parent, "DISK")
        self._update_stats()

        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=8, pady=10)
        self._hdr(parent, "MEMORY LOG")
        self.mem_log = tk.Text(parent, font=F["tiny"], fg=C["text2"],
                               bg=C["panel2"], relief=tk.FLAT,
                               state=tk.DISABLED, height=10, wrap=tk.WORD,
                               padx=8, pady=6)
        self.mem_log.pack(fill=tk.X, padx=6)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill=tk.X, padx=8, pady=10)
        self._hdr(parent, "FACE AUTH")

        self._side_btn(parent, "👁  Enroll Face",   "__enroll__", color=C["arc2"])
        self._side_btn(parent, "🗑  Delete Faces",  "__delete__", color=C["panel2"])

        enrolled_frame = tk.Frame(parent, bg=C["panel"])
        enrolled_frame.pack(fill=tk.X, padx=8)
        self.enrolled_lbl = tk.Label(enrolled_frame, text="No faces enrolled.",
                                     font=F["tiny"], fg=C["text3"], bg=C["panel"],
                                     wraplength=180, justify=tk.LEFT)
        self.enrolled_lbl.pack(anchor="w")
        self._refresh_enrolled()

    def _stat_row(self, parent, label):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(row, text=f"{label}:", font=F["tiny"],
                 fg=C["text3"], bg=C["panel"], width=5, anchor="w").pack(side=tk.LEFT)
        val = tk.Label(row, text="--", font=F["tiny"], fg=C["glow"], bg=C["panel"])
        val.pack(side=tk.LEFT)
        return val

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tick_clock(self):
        self.clock_lbl.configure(
            text=datetime.datetime.now().strftime("%Y.%m.%d  %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def _update_stats(self):
        try:
            import psutil
            self.cpu_lbl.configure( text=f"{psutil.cpu_percent()}%")
            self.ram_lbl.configure( text=f"{psutil.virtual_memory().percent}%")
            self.disk_lbl.configure(text=f"{psutil.disk_usage('/').percent}%")
        except:
            self.cpu_lbl.configure(text="N/A")
        self.root.after(4000, self._update_stats)

    def _refresh_enrolled(self):
        try:
            from src.face_auth import list_enrolled
            names = list_enrolled()
            self.enrolled_lbl.configure(
                text="Enrolled: " + (", ".join(names) if names else "None"))
        except:
            pass

    def set_status(self, msg: str):
        def _do():
            self.status_lbl.configure(text=msg)
            self.arc_status.configure(text=msg.upper()[:30])
            # Color dot
            col = C["green"]
            if any(w in msg.lower() for w in ["listen", "👂"]):
                col = C["glow"]; self.arc.set_mode("listening"); self.wave.set_active(True)
            elif any(w in msg.lower() for w in ["process", "⚙️"]):
                col = C["amber"]; self.arc.set_mode("processing"); self.wave.set_active(False)
            elif any(w in msg.lower() for w in ["error", "❌", "failed"]):
                col = C["red"]; self.arc.set_mode("error"); self.wave.set_active(False)
            elif any(w in msg.lower() for w in ["speak", "saying"]):
                col = C["glow2"]; self.arc.set_mode("speaking")
            else:
                col = C["green"]; self.arc.set_mode("idle"); self.wave.set_active(False)
            self._sdot.configure(fg=col)
        self.root.after(0, _do)

    def on_user(self, text: str):
        self.root.after(0, lambda: self._add_bubble(text, "user"))
        self.root.after(0, self._update_mem_lbl)

    def on_reply(self, text: str):
        self.root.after(0, lambda: self._add_bubble(text, "assistant"))
        self.root.after(0, self._update_mem_lbl)
        self.root.after(0, self._append_mem_log)

    def _add_bubble(self, text, role):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        b = Bubble(self.chat_frame, text, role, ts)
        b.pack(fill=tk.X, padx=10, pady=3)
        self.root.after(60, lambda: self.chat_canvas.yview_moveto(1.0))

    def _append_mem_log(self):
        if self.assistant:
            info = self.assistant.memory_info()
            self.mem_log.configure(state=tk.NORMAL)
            self.mem_log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M')}] {info}\n")
            self.mem_log.see(tk.END)
            self.mem_log.configure(state=tk.DISABLED)

    def _update_mem_lbl(self):
        if self.assistant:
            self.mem_lbl.configure(text=f"MEM: {self.assistant.memory_info()}")

    def _add_sys_msg(self, text):
        f = tk.Frame(self.chat_frame, bg=C["void"])
        f.pack(pady=8)
        tk.Label(f, text=text, font=F["small"], fg=C["text2"],
                 bg=C["panel2"], wraplength=480, justify=tk.CENTER,
                 padx=16, pady=10).pack()

    def _clear_log(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()

    def _set_placeholder(self):
        self.entry.insert(0, "Type a command or press 🎤 to speak…")
        self.entry.configure(fg=C["text3"])
        self.entry.bind("<FocusIn>",  self._clr_ph)
        self.entry.bind("<FocusOut>", self._rst_ph)

    def _clr_ph(self, e):
        if self.entry.get() == "Type a command or press 🎤 to speak…":
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=C["text"])

    def _rst_ph(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Type a command or press 🎤 to speak…")
            self.entry.configure(fg=C["text3"])

    # ── Interactions ──────────────────────────────────────────────────────────

    def _text_cmd(self, cmd):
        # Handle special GUI-only commands
        if cmd == "__enroll__":
            from tkinter import simpledialog
            name = simpledialog.askstring("Enroll Face", "Enter your name:", parent=self.root)
            if name:
                def _run():
                    from src.face_auth import enroll_face
                    enroll_face(name, status_cb=self.set_status)
                    self._refresh_enrolled()
                threading.Thread(target=_run, daemon=True).start()
            return
        if cmd == "__delete__":
            from tkinter import simpledialog
            name = simpledialog.askstring("Delete Face", "Name to delete:", parent=self.root)
            if name:
                from src.face_auth import delete_enrollment
                try:
                    from src.face_auth import delete_enrollment
                    ok = delete_enrollment(name)
                    self._add_sys_msg(f"{'Deleted' if ok else 'Not found'}: {name}")
                    self._refresh_enrolled()
                except:
                    pass
            return
        threading.Thread(target=self.assistant.process,
                         args=(cmd,), daemon=True).start()

    def _send_typed(self):
        text = self.entry.get().strip()
        if text and text != "Type a command or press 🎤 to speak…":
            self.entry.delete(0, tk.END)
            threading.Thread(target=self.assistant.process,
                             args=(text,), daemon=True).start()

    def _on_enter(self, e):
        self._send_typed()

    def _toggle_mic(self):
        if self._continuous:
            return
        self.mic_btn.configure(bg=C["glow"], text="⏹")
        self.wave.set_active(True)
        self.arc.set_mode("listening")
        def _done():
            self.root.after(0, lambda: self.mic_btn.configure(bg=C["arc2"], text="🎤"))
            self.root.after(0, lambda: self.wave.set_active(False))
        def _run():
            self.assistant.listen_once()
            _done()
        threading.Thread(target=_run, daemon=True).start()

    def _toggle_continuous(self):
        if not self._continuous:
            self._continuous = True
            self.cont_btn.configure(text="⏹ STOP", bg=C["red"])
            self.mic_btn.configure(bg=C["red"])
            self.wave.set_active(True)
            self.assistant.start_continuous()
        else:
            self._continuous = False
            self.cont_btn.configure(text="▶ CONTINUOUS", bg=C["arc2"])
            self.mic_btn.configure(bg=C["arc2"], text="🎤")
            self.wave.set_active(False)
            self.assistant.stop_continuous()

    def _toggle_wake(self):
        if self.assistant:
            self.assistant.toggle_wake(self.wake_var.get())

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_assistant(self):
        from src.assistant import Assistant
        self.assistant = Assistant(
            on_user=self.on_user,
            on_reply=self.on_reply,
            on_status=self.set_status,
            on_error=lambda m: self.set_status(f"❌ {m}"),
        )

    def _check_key(self):
        if "YOUR_" in OPENAI_API_KEY:
            self.root.after(400, lambda: self._add_sys_msg(
                "⚠️ OpenAI API key not set.\n"
                "Open config.py → set OPENAI_API_KEY\n"
                "Get your key at platform.openai.com"))

    def _greet(self):
        msg = f"Welcome back, {self.username}. All systems are online. How may I assist you?"
        self.root.after(600, lambda: self._add_bubble(msg, "assistant"))
        self.root.after(800, lambda: self.assistant.speech.speak(msg) if self.assistant else None)
