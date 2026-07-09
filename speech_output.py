"""
speech_output.py  —  OptiLink — TTS Output Window
Opens automatically when OptiLink is closed.
Auto-speaks whatever was typed, with replay / copy controls.

Requires:  pip install pyttsx3
""" 

import tkinter as tk
import threading
import sys

# ── Palette (matches OptiLink palette) ────────────────────────
BG      = "#0d0d1a"
BG2     = "#12122a"
CARD    = "#1a1a2e"
FG      = "#e2e8f0"
FG_DIM  = "#64748b"
ACCENT  = "#7c3aed"
ACCENT2 = "#06b6d4"
SUCCESS = "#10b981"
WARNING = "#f59e0b"
DANGER  = "#ef4444"
BORDER  = "#2a2a4a"


# ── TTS engine ────────────────────────────────────────────────

class _TTSWorker:
    """Thread-safe wrapper around pyttsx3."""

    def __init__(self):
        self._lock   = threading.Lock()
        self._engine = None
        self._ok     = False
        self._init()

    def _init(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 150)
            self._engine.setProperty("volume", 1.0)
            self._ok = True
        except Exception as e:
            print(f"[TTS] pyttsx3 unavailable: {e}")
            self._ok = False

    @property
    def available(self):
        return self._ok

    def speak(self, text: str, on_start=None, on_done=None, on_error=None):
        """Speak text in a background thread."""
        def _run():
            with self._lock:
                try:
                    if on_start:
                        on_start()
                    if self._engine:
                        self._engine.say(text)
                        self._engine.runAndWait()
                    if on_done:
                        on_done()
                except Exception as err:
                    print(f"[TTS] error: {err}")
                    if on_error:
                        on_error(str(err))
        threading.Thread(target=_run, daemon=True).start()


# ── Public entry point ────────────────────────────────────────

def show_speech_output(typed_text: str):
    """
    Open the TTS output window.  Blocks until the user closes it.
    Call this from main.py after the keyboard window closes.
    """
    tts = _TTSWorker()

    root = tk.Tk()
    root.title("🔊  OptiLink — Speech Output")
    root.configure(bg=BG)
    root.resizable(True, True)
    root.minsize(500, 400)

    W, H = 580, 460
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")
    root.attributes("-topmost", True)

    # ── Header ────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=BG2, pady=14)
    hdr.pack(fill="x")

    tk.Label(hdr, text="🔊",
        font=("Consolas", 22), fg=ACCENT2, bg=BG2).pack(side="left", padx=(20, 8))

    hdr_txt = tk.Frame(hdr, bg=BG2)
    hdr_txt.pack(side="left")
    tk.Label(hdr_txt, text="Speech Output",
        font=("Consolas", 16, "bold"), fg=FG, bg=BG2, anchor="w").pack(anchor="w")
    tk.Label(hdr_txt, text="Your OptiLink typed text — playing automatically",
        font=("Consolas", 9), fg=FG_DIM, bg=BG2, anchor="w").pack(anchor="w")

    # ── Text display card ─────────────────────────────────────
    card = tk.Frame(root, bg=CARD, padx=22, pady=18)
    card.pack(fill="both", expand=True, padx=22, pady=16)

    tk.Label(card, text="Typed text",
        font=("Consolas", 9), fg=FG_DIM, bg=CARD, anchor="w").pack(anchor="w")

    text_var = tk.StringVar()

    if typed_text:
        display_text = typed_text
        text_colour  = FG
    else:
        display_text = "(nothing was typed)"
        text_colour  = FG_DIM

    text_var.set(display_text)

    text_lbl = tk.Label(card,
        textvariable=text_var,
        font=("Consolas", 16),
        fg=text_colour,
        bg=CARD,
        wraplength=500,
        justify="left",
        anchor="nw")
    text_lbl.pack(anchor="nw", fill="both", expand=True, pady=(6, 0))

    # ── Character / word count ────────────────────────────────
    if typed_text:
        words = len(typed_text.split())
        chars = len(typed_text)
        meta  = f"{chars} char{'s' if chars != 1 else ''}  ·  {words} word{'s' if words != 1 else ''}"
    else:
        meta = ""

    tk.Label(card, text=meta,
        font=("Consolas", 8), fg=FG_DIM, bg=CARD, anchor="w").pack(anchor="w", pady=(6, 0))

    # ── Status row ────────────────────────────────────────────
    status_var = tk.StringVar(value="")
    status_lbl = tk.Label(root, textvariable=status_var,
        font=("Consolas", 11), fg=ACCENT2, bg=BG)
    status_lbl.pack(pady=(0, 6))

    # ── Buttons ───────────────────────────────────────────────
    btn_row = tk.Frame(root, bg=BG)
    btn_row.pack(pady=(0, 18))

    _speaking = [False]

    def _set_status(state: str):
        """Thread-safe status update (called from TTS worker thread)."""
        msgs = {
            "speaking": ("🔊  Speaking…",   ACCENT2),
            "done":     ("✓  Done",          SUCCESS),
            "error":    ("⚠  TTS error — is pyttsx3 installed?", DANGER),
            "nosupport":("⚠  TTS not available — copy the text manually.", WARNING),
            "empty":    ("  Nothing to speak.", FG_DIM),
        }
        msg, col = msgs.get(state, ("", FG_DIM))
        try:
            root.after(0, lambda: status_var.set(msg))
            root.after(0, lambda: status_lbl.config(fg=col))
        except Exception:
            pass

    def _tts_text(raw: str) -> str:
        """
        Make pyttsx3 pronounce typed text naturally.
        All-caps runs (acronyms/words) are lowercased so the TTS engine
        reads them as words rather than spelling each letter individually.
        """
        import re
        return re.sub(r'[A-Z]{2,}', lambda m: m.group(0).lower(), raw)

    def speak_now():
        if not typed_text:
            _set_status("empty")
            return
        if _speaking[0]:
            return
        _speaking[0] = True

        def _on_done():
            _speaking[0] = False
            _set_status("done")

        def _on_error(e):
            _speaking[0] = False
            _set_status("error")

        if tts.available:
            tts.speak(
                _tts_text(typed_text),
                on_start=lambda: _set_status("speaking"),
                on_done=_on_done,
                on_error=_on_error,
            )
        else:
            _speaking[0] = False
            _set_status("nosupport")

    def copy_text():
        root.clipboard_clear()
        root.clipboard_append(typed_text)
        _set_status("done")
        status_var.set("✓  Copied to clipboard!")

    # ── Speak Again button
    speak_btn = tk.Button(btn_row,
        text="🔊  Speak Again",
        font=("Consolas", 11, "bold"),
        bg=ACCENT, fg="white",
        activebackground="#6d28d9", activeforeground="white",
        relief="flat", bd=0, padx=18, pady=10,
        cursor="hand2",
        command=speak_now)
    speak_btn.pack(side="left", padx=6)
    speak_btn.bind("<Enter>", lambda _e: speak_btn.config(bg="#6d28d9"))
    speak_btn.bind("<Leave>", lambda _e: speak_btn.config(bg=ACCENT))

    # ── Copy button
    copy_btn = tk.Button(btn_row,
        text="📋  Copy",
        font=("Consolas", 11, "bold"),
        bg=CARD, fg=FG,
        activebackground=BORDER, activeforeground=FG,
        relief="flat", bd=0, padx=18, pady=10,
        cursor="hand2",
        command=copy_text)
    copy_btn.pack(side="left", padx=6)

    # ── Close button
    close_btn = tk.Button(btn_row,
        text="✕  Close",
        font=("Consolas", 11, "bold"),
        bg=BG2, fg=FG_DIM,
        activebackground=CARD, activeforeground=FG,
        relief="flat", bd=0, padx=18, pady=10,
        cursor="hand2",
        command=root.destroy)
    close_btn.pack(side="left", padx=6)

    # ── Footer hint ───────────────────────────────────────────
    tk.Label(root,
        text="Tip: install  pyttsx3  if speech is unavailable  (pip install pyttsx3)",
        font=("Consolas", 8), fg=FG_DIM, bg=BG).pack(pady=(0, 8))

    # ── Auto-speak after a short delay ────────────────────────
    if typed_text:
        root.after(1000, speak_now)
    else:
        _set_status("empty")

    root.mainloop()