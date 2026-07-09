import tkinter as tk
import pyautogui
import pyttsx3
import threading
import time
import sys
import os
import numpy as np

# ── Cross-platform beep ───────────────────────────────────────────────────────
_sd = None
_SD_CHECKED = False

def _get_sd():
    global _sd, _SD_CHECKED
    if _SD_CHECKED:
        return _sd
    _SD_CHECKED = True
    try:
        import sounddevice as sd
        _sd = sd
    except Exception:
        _sd = None
    return _sd

def _make_tone(freq=880, duration=0.07, volume=0.25, rate=44100):
    t    = np.linspace(0, duration, int(rate * duration), endpoint=False)
    wave = (np.sin(2 * np.pi * freq * t) * volume * 32767).astype(np.int16)
    fade = int(len(wave) * 0.2)
    wave[-fade:] = (wave[-fade:] * np.linspace(1, 0, fade)).astype(np.int16)
    return wave

_SCROLL_TONE = _make_tone(freq=660, duration=0.05, volume=0.18)
_PRESS_TONE  = _make_tone(freq=880, duration=0.09, volume=0.30)

def _play_tone(wave, rate=44100):
    def _do():
        sd = _get_sd()
        if sd is not None:
            try:
                sd.play(wave, samplerate=rate, blocking=True)
                return
            except Exception:
                pass
        if sys.platform == "win32":
            try:
                import winsound
                winsound.Beep(880, 80)
            except Exception:
                pass
        elif sys.platform == "darwin":
            os.system("afplay /System/Library/Sounds/Tink.aiff &")
        else:
            print("\a", end="", flush=True)
    threading.Thread(target=_do, daemon=True).start()

def _beep_scroll():
    _play_tone(_SCROLL_TONE)

def _beep_press():
    _play_tone(_PRESS_TONE)

# ── Key layout ────────────────────────────────────────────────
ALL_KEYS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["SPACE", "BACK", "CLEAR", "SPEAK"]

# Quick-phrase keys — scrolled/selected just like letter keys
PHRASE_KEYS = ["YES", "NO", "OKAY", "HELP", "WATER", "CATHETER CHANGE", "FOOD", "PAIN"]
ALL_KEYS = ALL_KEYS + PHRASE_KEYS

# Map phrase key → display label (keep buttons compact)
PHRASE_DISPLAY = {
    "YES":              "✔ YES",
    "NO":               "✘ NO",
    "OKAY":             "👍 OKAY",
    "HELP":             "🆘 HELP",
    "WATER":            "💧 WATER",
    "CATHETER CHANGE":  "🔄 CATH",
    "FOOD":             "🍽 FOOD",
    "PAIN":             "⚡ PAIN",
}

# Colour accents for phrase buttons (bg, fg)
PHRASE_COLORS = {
    "YES":              ("#065f46", "#6ee7b7"),   # green
    "NO":               ("#7f1d1d", "#fca5a5"),   # red
    "OKAY":             ("#1e3a5f", "#93c5fd"),   # blue
    "HELP":             ("#78350f", "#fde68a"),   # amber — urgent
    "WATER":            ("#0c4a6e", "#7dd3fc"),   # sky
    "CATHETER CHANGE":  ("#312e81", "#c4b5fd"),   # indigo
    "FOOD":             ("#14532d", "#86efac"),   # emerald
    "PAIN":             ("#4c0519", "#fda4af"),   # rose — urgent
}

# ── Colours ───────────────────────────────────────────────────
BG         = "#0f0f1a"
KEY_NORMAL = "#1e1e2e"
KEY_SELECT = "#7c3aed"
KEY_FLASH  = "#06b6d4"
KEY_BORDER = "#2e2e4e"
FG         = "#e2e8f0"
FG_DIM     = "#64748b"
ACCENT     = "#7c3aed"
ACCENT2    = "#06b6d4"
SUCCESS    = "#10b981"
WARNING    = "#f59e0b"
DANGER     = "#ef4444"

SCROLL_INTERVAL = 0.35


class OptiLinkKeyboard:
    def __init__(self, on_close_callback=None):
        self.root = tk.Tk()
        self.root.title("👁  OptiLink")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.configure(bg=BG)

        self._on_close_callback = on_close_callback

        if on_close_callback:
            self.root.protocol("WM_DELETE_WINDOW", on_close_callback)

        # ── Bind Escape key to close ───────────────────────
        self.root.bind("<Escape>", self._handle_escape)

        self.root.attributes("-fullscreen", True)
        self.root.update_idletasks()
        self.SW = self.root.winfo_screenwidth()
        self.SH = self.root.winfo_screenheight()

        self.SX = self.SW / 1920
        self.SY = self.SH / 1080

        def S(n):
            return max(1, int(n * min(self.SX, self.SY)))

        self.S = S

        self.cursor_idx  = 0
        self.direction   = "center"
        self.last_scroll = time.time()
        self.typed_text  = ""
        self.key_count   = 0
        self.status      = "ACTIVE"
        self._ready      = False
        self._speaking   = False

        self.buttons = {}

        self._build_ui()
        self.root.after(300, self._mark_ready)

    def _handle_escape(self, event=None):
        """Escape key → same as clicking the window close button."""
        if self._on_close_callback:
            self._on_close_callback()
        else:
            try:
                self.root.destroy()
            except Exception:
                pass

    def _mark_ready(self):
        self._ready = True
        self._highlight_current()

    def _build_ui(self):
        S = self.S

        ROW1 = list("ABCDEFGHIJKLM")
        ROW2 = list("NOPQRSTUVWXYZ") + ["SPACE", "BACK", "CLEAR", "SPEAK"]

        # ── Status bar ────────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=S(20), pady=(S(10), S(4)))

        self.status_dot = tk.Label(top, text="●",
            font=("Consolas", S(15)), fg=SUCCESS, bg=BG)
        self.status_dot.pack(side="left")

        self.status_label = tk.Label(top,
            text=" ACTIVE  —  OptiLink",
            font=("Consolas", S(14), "bold"), fg=SUCCESS, bg=BG)
        self.status_label.pack(side="left")

        # Two-tone brand name in the status bar (right of status text)
        brand_frame = tk.Frame(top, bg=BG)
        brand_frame.pack(side="left", padx=S(10))
        tk.Label(brand_frame, text="Opti",
            font=("Consolas", S(11), "bold"), fg=FG_DIM, bg=BG).pack(side="left")
        tk.Label(brand_frame, text="Link",
            font=("Consolas", S(11), "bold"), fg="#06b6d4", bg=BG).pack(side="left")

        # ── ESC hint (right side of status bar) ───────────
        tk.Label(top,
            text="Press ESC to exit",
            font=("Consolas", S(10)), fg=FG_DIM, bg=BG
        ).pack(side="right", padx=S(8))

        self.dir_label = tk.Label(top, text="◉ CENTER",
            font=("Consolas", S(13)), fg=FG_DIM, bg=BG)
        self.dir_label.pack(side="right", padx=S(16))

        # ── Typed text display ────────────────────────────
        txt_frame = tk.Frame(self.root, bg=KEY_NORMAL,
                             padx=S(14), pady=S(10))
        txt_frame.pack(fill="x", padx=S(20), pady=(S(4), S(8)))

        tk.Label(txt_frame, text="✎ ",
            font=("Consolas", S(18)), fg=FG_DIM,
            bg=KEY_NORMAL).pack(side="left")

        self.text_display = tk.Label(txt_frame, text="",
            font=("Consolas", S(22)), fg=FG,
            bg=KEY_NORMAL, anchor="w", width=55)
        self.text_display.pack(side="left")

        self.cursor_blink = tk.Label(txt_frame, text="▌",
            font=("Consolas", S(22)), fg=ACCENT, bg=KEY_NORMAL)
        self.cursor_blink.pack(side="left")
        self._blink_cursor()

        # ── Key rows ──────────────────────────────────────
        def make_key_row(parent, labels):
            row = tk.Frame(parent, bg=BG)
            row.pack(fill="x", padx=S(20), pady=S(4))
            for label in labels:
                is_speak = label == "SPEAK"
                display  = {"SPACE": "SPC", "BACK": "⌫",
                            "CLEAR": "CLR", "SPEAK": "🔊"}.get(label, label)

                btn = tk.Button(
                    row, text=display,
                    font=("Consolas", S(18), "bold"),
                    bg="#134e2a" if is_speak else KEY_NORMAL,
                    fg=SUCCESS   if is_speak else FG,
                    activebackground=KEY_SELECT,
                    relief="flat", bd=0,
                    pady=S(16),
                    cursor="none",
                    highlightthickness=2,
                    highlightbackground="#1a6b38" if is_speak else KEY_BORDER,
                )
                btn.pack(side="left", padx=S(3), fill="x", expand=True)
                self.buttons[label] = btn

        keys_frame = tk.Frame(self.root, bg=BG)
        keys_frame.pack(fill="x")
        make_key_row(keys_frame, ROW1)
        make_key_row(keys_frame, ROW2)

        # ── Quick-phrase row ──────────────────────────────────
        phrase_row = tk.Frame(self.root, bg=BG)
        phrase_row.pack(fill="x", padx=self.S(20), pady=(self.S(2), self.S(4)))

        tk.Label(phrase_row, text="PHRASES:",
            font=("Consolas", self.S(9)), fg=FG_DIM, bg=BG,
            padx=self.S(4)).pack(side="left")

        for phrase in PHRASE_KEYS:
            bg_col, fg_col = PHRASE_COLORS.get(phrase, (KEY_NORMAL, FG))
            display = PHRASE_DISPLAY.get(phrase, phrase)
            btn = tk.Button(
                phrase_row, text=display,
                font=("Consolas", self.S(12), "bold"),
                bg=bg_col, fg=fg_col,
                activebackground=KEY_SELECT,
                relief="flat", bd=0,
                pady=self.S(10),
                cursor="none",
                highlightthickness=2,
                highlightbackground=fg_col,
            )
            btn.pack(side="left", padx=self.S(3), fill="x", expand=True)
            self.buttons[phrase] = btn

        # ── Large current key box ─────────────────────────
        big_frame = tk.Frame(self.root, bg=KEY_SELECT,
                             padx=S(5), pady=S(5))
        big_frame.pack(fill="both", expand=True,
                       padx=S(20), pady=(S(8), S(8)))

        inner = tk.Frame(big_frame, bg=BG)
        inner.pack(fill="both", expand=True)

        self.big_key_label = tk.Label(inner,
            text=ALL_KEYS[0],
            font=("Consolas", S(200), "bold"),
            fg="white", bg=BG,
            anchor="center")
        self.big_key_label.pack(fill="both", expand=True)

        self.pos_label = tk.Label(inner,
            text=f"1 / {len(ALL_KEYS)}",
            font=("Consolas", S(15)), fg=FG_DIM, bg=BG)
        self.pos_label.pack(pady=(0, S(4)))

        # ── Gesture legend ────────────────────────────────
        leg = tk.Frame(self.root, bg=KEY_NORMAL,
                       padx=S(14), pady=S(8))
        leg.pack(fill="x", padx=S(20), pady=(0, S(12)))

        gestures = [
            ("◀ Left",        "scroll left"),
            ("▶ Right",       "scroll right"),
            ("😑 Long blink",  "type key"),
            ("😑😑 Dbl blink", "backspace"),
            ("🔊 SPEAK",       "speak text"),
        ]
        for i, (g, d) in enumerate(gestures):
            tk.Label(leg, text=f"{g} = {d}",
                font=("Consolas", S(11)), fg=FG_DIM,
                bg=KEY_NORMAL, padx=S(8)).pack(side="left")
            if i < len(gestures) - 1:
                tk.Label(leg, text="│", font=("Consolas", S(11)),
                    fg=KEY_BORDER, bg=KEY_NORMAL).pack(side="left")

    def _blink_cursor(self):
        c = self.cursor_blink.cget("fg")
        self.cursor_blink.config(fg=ACCENT if c == BG else BG)
        self.root.after(500, self._blink_cursor)

    def set_status(self, status: str):
        self.status = status
        configs = {
            "ACTIVE":      (SUCCESS, " ACTIVE  —  OptiLink"),
            "CALIBRATING": (WARNING, " CALIBRATING…"),
            "NO_FACE":     (DANGER,  " NO FACE DETECTED"),
        }
        colour, text = configs.get(status, (FG_DIM, status))
        self.status_dot.config(fg=colour)
        self.status_label.config(text=text, fg=colour)

    def _highlight_current(self):
        for label, btn in self.buttons.items():
            if label == "SPEAK":
                btn.config(bg="#134e2a", fg=SUCCESS)
            elif label in PHRASE_COLORS:
                bg_col, fg_col = PHRASE_COLORS[label]
                btn.config(bg=bg_col, fg=fg_col)
            else:
                btn.config(bg=KEY_NORMAL, fg=FG)

        current = ALL_KEYS[self.cursor_idx]
        if current in self.buttons:
            self.buttons[current].config(bg=KEY_SELECT, fg="white")

        if current in PHRASE_DISPLAY:
            display = PHRASE_DISPLAY[current]
        else:
            display = {"SPACE": "SPC ␣", "BACK": "⌫", "CLEAR": "✕", "SPEAK": "🔊"}.get(current, current)
        self.big_key_label.config(text=display)
        self.pos_label.config(text=f"{self.cursor_idx + 1} / {len(ALL_KEYS)}")

    def update_direction(self, direction, face_detected=True):
        if not self._ready:
            self.root.update()
            return

        if not face_detected:
            self.set_status("NO_FACE")
        elif self.status != "ACTIVE":
            self.set_status("ACTIVE")

        self.direction = direction

        dir_icons = {
            "left":   "◀ LEFT",
            "right":  "▶ RIGHT",
            "center": "◉ CENTER",
        }
        dir_colours = {
            "left":   "#f59e0b",
            "right":  "#f59e0b",
            "center": FG_DIM,
        }
        self.dir_label.config(
            text=dir_icons.get(direction, "◉ CENTER"),
            fg=dir_colours.get(direction, FG_DIM)
        )

        now = time.time()
        if direction in ("left", "right"):
            if now - self.last_scroll >= SCROLL_INTERVAL:
                if direction == "left":
                    self.cursor_idx = (self.cursor_idx - 1) % len(ALL_KEYS)
                else:
                    self.cursor_idx = (self.cursor_idx + 1) % len(ALL_KEYS)
                self._highlight_current()
                _beep_scroll()
                self.last_scroll = now

        self.root.update()

    def notify_long_blink(self):
        if not self._ready:
            return
        self._press(ALL_KEYS[self.cursor_idx])

    def notify_double_blink(self):
        if not self._ready:
            return
        _beep_press()
        self._backspace()

    def _press(self, label):
        _beep_press()
        if label in PHRASE_KEYS:
            self._press_phrase(label)
        elif label == "SPACE":
            self._space()
        elif label == "BACK":
            self._backspace()
        elif label == "CLEAR":
            self.typed_text = ""
            self._update_display()
            self._flash(label)
        elif label == "SPEAK":
            self._speak()
        else:
            pyautogui.press(label.lower())
            self.typed_text += label
            self._update_display()
            self.key_count += 1
            self._flash(label)

    def _press_phrase(self, phrase):
        """Type the full phrase and speak it aloud immediately."""
        if self._speaking:
            return
        self.typed_text += ("" if not self.typed_text or self.typed_text.endswith(" ") else " ") + phrase.lower()
        self._update_display()
        self._flash(phrase)

        self._speaking = True
        if phrase in self.buttons:
            self.buttons[phrase].config(bg=WARNING, fg="#0f0f1a")
        self.big_key_label.config(fg=WARNING)

        def do_speak():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.say(phrase.lower())
                engine.runAndWait()
                try:
                    engine.stop()
                except Exception:
                    pass
            except Exception as e:
                print(f"[TTS] Phrase error: {e}")
            finally:
                self._speaking = False
                self.root.after(0, self._restore_speak_btn)

        threading.Thread(target=do_speak, daemon=True).start()

    def _speak(self):
        text = self.typed_text.strip()
        if not text or self._speaking:
            if "SPEAK" in self.buttons:
                self.buttons["SPEAK"].config(bg=DANGER)
                self.root.after(400, lambda: self.buttons["SPEAK"].config(
                    bg="#134e2a", fg=SUCCESS))
            return

        self._speaking = True
        if "SPEAK" in self.buttons:
            self.buttons["SPEAK"].config(bg=WARNING, fg="#0f0f1a")
        self.big_key_label.config(fg=WARNING)

        def do_speak():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.say(text)
                engine.runAndWait()
                try:
                    engine.stop()
                except Exception:
                    pass
            except Exception as e:
                print(f"[TTS] Error: {e}")
            finally:
                self._speaking = False
                self.root.after(0, self._restore_speak_btn)

        threading.Thread(target=do_speak, daemon=True).start()

    def _restore_speak_btn(self):
        if "SPEAK" in self.buttons:
            self.buttons["SPEAK"].config(bg="#134e2a", fg=SUCCESS)
        self.big_key_label.config(fg="white")
        self._highlight_current()

    def _space(self):
        pyautogui.press("space")
        self.typed_text += " "
        self._update_display()
        self._flash("SPACE")

    def _backspace(self):
        pyautogui.press("backspace")
        self.typed_text = self.typed_text[:-1]
        self._update_display()
        self._flash("BACK")

    def _update_display(self):
        t = self.typed_text[-60:] if len(self.typed_text) > 60 else self.typed_text
        self.text_display.config(text=t)

    def _flash(self, label):
        if label in self.buttons:
            self.buttons[label].config(bg=KEY_FLASH, fg="white")
        self.big_key_label.config(fg=KEY_FLASH)
        self.root.after(200, self._restore_flash)

    def _restore_flash(self):
        self.big_key_label.config(fg="white")
        self._highlight_current()