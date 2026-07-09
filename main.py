import cv2
import numpy as np
import tkinter as tk
import threading
import time
from eye_tracker import EyeTracker
from optilink_keyboard import OptiLinkKeyboard
from launcher import show_launcher
from speech_output import show_speech_output


def auto_tune_blink_threshold(tracker, cap, seconds=3):
    """
    Silently reads <seconds> worth of frames with eyes open to
    calculate a personal blink threshold — no window shown.
    """
    print(f"[AutoTune] Measuring EAR for {seconds}s — keep eyes open...")
    samples = []
    deadline = time.time() + seconds
    while time.time() < deadline:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        left_iris, right_iris, h, v, long_blink, double_blink = tracker.process(frame)
        if tracker.last_ear:
            samples.append(tracker.last_ear)

    if len(samples) > 10:
        mean_ear = float(np.mean(samples))
        tracker.blink_threshold = round(mean_ear * 0.65, 3)
        print(f"[AutoTune] blink threshold set to {tracker.blink_threshold}")
    else:
        print("[AutoTune] Not enough data — keeping default threshold 0.22")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("Starting OptiLink...")

    if not show_launcher():
        return

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    tracker = EyeTracker()

    # Auto-tune blink threshold silently before keyboard opens
    auto_tune_blink_threshold(tracker, cap, seconds=3)

    print("Launching OptiLink...")

    keyboard_alive = [True]

    def on_keyboard_close():
        keyboard_alive[0] = False
        try:
            keyboard.root.destroy()
        except:
            pass

    keyboard = OptiLinkKeyboard(on_close_callback=on_keyboard_close)
    keyboard.set_status("ACTIVE")
    keyboard.root.update()

    # ── Main loop ─────────────────────────────────────────
    while keyboard_alive[0]:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        left_iris, right_iris, h_ratio, v_ratio, long_blink, double_blink = tracker.process(frame)
        face_detected = left_iris is not None

        if face_detected:
            direction = tracker.get_direction(h_ratio, v_ratio)
        else:
            direction = "center"

        try:
            if double_blink:
                keyboard.notify_double_blink()
            elif long_blink:
                keyboard.notify_long_blink()
            keyboard.update_direction(direction, face_detected=face_detected)
        except Exception:
            break

    typed_text = keyboard.typed_text

    cap.release()
    tracker.release()
    try:
        keyboard.root.destroy()
    except:
        pass

    show_speech_output(typed_text)


if __name__ == "__main__":
    main()