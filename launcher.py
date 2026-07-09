import tkinter as tk
import sys

BG      = "#0f0f1a"
CARD    = "#1e1e2e"
ACCENT  = "#7c3aed"
FG      = "#e2e8f0"
FG_DIM  = "#64748b"
SUCCESS = "#10b981"
BTN_HV  = "#6d28d9"

def show_launcher():
    result = [False]

    root = tk.Tk()
    root.title("OptiLink — Launcher")
    root.configure(bg=BG)
    root.resizable(False, False)

    W, H = 520, 620
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    # Clamp to screen height so START button is never pushed off-screen
    H = min(H, sh - 80)
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{max(0, (sh-H)//2)}")

    # ── CRITICAL: pack bottom FIRST before the expanding content frame ──
    # In tkinter, side="bottom" widgets must be packed before side="top"
    # expanding widgets, otherwise the expanding frame consumes all space.
    bottom = tk.Frame(root, bg=BG)
    bottom.pack(side="bottom", fill="x", pady=(0, 16))

    # ── Scrollable content (packed after bottom so it fills remaining space) ─
    content = tk.Frame(root, bg=BG)
    content.pack(fill="both", expand=True)

    # ── OptiLink logo canvas ──────────────────────────────────
    logo = tk.Canvas(content, width=120, height=64, bg=BG, highlightthickness=0)
    logo.pack(pady=(20, 0))
    # Outer glow ring
    logo.create_oval(8, 4, 112, 60, outline=ACCENT, width=2, dash=(4, 3))
    # Eye shape
    logo.create_arc(14, 12, 106, 52, start=0,   extent=180, style="chord",
                    fill="#1a1a30", outline=ACCENT, width=2)
    logo.create_arc(14, 12, 106, 52, start=180, extent=180, style="chord",
                    fill="#1a1a30", outline=ACCENT, width=2)
    # Iris — teal
    logo.create_oval(44, 16, 76, 48, fill="#06b6d4", outline="")
    # Pupil
    logo.create_oval(52, 24, 68, 40, fill=BG, outline="")
    # Highlight
    logo.create_oval(61, 26, 66, 31, fill="white", outline="")
    # Link nodes either side
    logo.create_oval(2,  26, 12, 36, fill=ACCENT, outline="")
    logo.create_oval(108,26,118, 36, fill=ACCENT, outline="")
    logo.create_line(12, 31, 22, 31, fill=ACCENT, width=2)
    logo.create_line(98, 31,108, 31, fill=ACCENT, width=2)

    # ── Title — two-tone "OptiLink" ───────────────────────────
    title_frame = tk.Frame(content, bg=BG)
    title_frame.pack(pady=(10, 2))
    tk.Label(title_frame, text="Opti",
             font=("Consolas", 22, "bold"), fg=FG,       bg=BG).pack(side="left")
    tk.Label(title_frame, text="Link",
             font=("Consolas", 22, "bold"), fg="#06b6d4", bg=BG).pack(side="left")

    tk.Label(content, text="Eye-controlled communication, reimagined",
             font=("Consolas", 9), fg=FG_DIM, bg=BG).pack()

    # ── Divider ──────────────────────────────────────────────
    div = tk.Canvas(content, height=1, bg=BG, highlightthickness=0)
    div.pack(fill="x", padx=40, pady=12)
    div.create_line(0, 0, 480, 0, fill=CARD, width=1)

    # ── Feature cards ─────────────────────────────────────────
    infos = [
        ("👁",  "Eye Tracking",      "MediaPipe face landmark detection"),
        ("🎯",  "Auto-Calibration",  "Blink threshold tuned to your eyes"),
        ("⌨",  "Gaze Typing",        "Look left/right to scroll, long blink to type"),
        ("🔔",  "Sound Feedback",    "Beep/chime on every key press — distinct tones"),
        ("🔄",  "Blink Progress",    "Arc ring fills as you hold the blink"),
        ("🔊",  "Text to Speech",    "Close window → auto-speaks everything you typed"),
    ]

    for icon, title, desc in infos:
        card = tk.Frame(content, bg=CARD, padx=12, pady=7)
        card.pack(fill="x", padx=28, pady=3)
        tk.Label(card, text=icon,  font=("Consolas", 13),
                 bg=CARD, fg=FG).pack(side="left", padx=(0, 10))
        txt = tk.Frame(card, bg=CARD)
        txt.pack(side="left")
        tk.Label(txt, text=title, font=("Consolas", 10, "bold"),
                 fg=FG, bg=CARD, anchor="w").pack(anchor="w")
        tk.Label(txt, text=desc,  font=("Consolas", 8),
                 fg=FG_DIM, bg=CARD, anchor="w").pack(anchor="w")

    # ── START button (inside bottom frame, packed first above) ──
    def on_start():
        result[0] = True
        root.destroy()

    btn = tk.Button(
        bottom, text="▶   LAUNCH OPTILINK",
        font=("Consolas", 13, "bold"),
        bg=ACCENT, fg="white",
        activebackground=BTN_HV,
        activeforeground="white",
        relief="flat", bd=0,
        padx=28, pady=10,
        cursor="hand2",
        command=on_start
    )
    btn.pack(pady=(8, 4))
    btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HV))
    btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))

    tk.Label(bottom,
             text="OptiLink  ·  Requires:  opencv-python  mediapipe  cvzone  pyautogui  pyttsx3",
             font=("Consolas", 8), fg=FG_DIM, bg=BG).pack()

    root.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit(0)))
    root.mainloop()
    return result[0]