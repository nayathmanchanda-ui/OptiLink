# OptiLink

**Hands-Free Gaze-Controlled Typing System**

OptiLink is a fully hands-free virtual keyboard controlled entirely by eye movement and blinks, using nothing more than a standard webcam. It's built for people with motor disabilities — ALS, cerebral palsy, spinal cord injuries, upper limb paralysis — who cannot use a traditional keyboard, as a low-cost alternative to dedicated eye-gaze communication devices, which often run from several thousand to tens of thousands of dollars.

> No hands. No touch. Just vision.

Live project page: https://opti-link.vercel.app/

## Features

| Feature | Description |
|---|---|
| Eye-Controlled | Navigate keys by looking left or right |
| Webcam Only | No special hardware — works on any PC with a camera |
| Blink Detection | Long blink selects a key, double blink backspaces |
| Auto-Calibration | Blink threshold auto-tunes to your eyes in ~3 seconds |
| Text-to-Speech | Typed text is read aloud, both on demand and when you close the app |
| Quick Phrases | One-look access to common needs: YES, NO, HELP, WATER, PAIN, FOOD, CATH |
| Audio Feedback | Distinct tones confirm scrolling vs. key selection |
| Single .exe | Packaged as one executable — no setup for the end user |

## How It Works

1. **Capture** — OpenCV reads webcam frames in real time
2. **Face & Iris Tracking** — MediaPipe's Face Landmarker tracks 468 facial landmarks, including iris position, per frame
3. **Gaze Direction** — Iris position relative to the eye corners is converted into a left / right / center signal
4. **Blink Detection** — Eye Aspect Ratio (EAR) is monitored; a sustained low EAR triggers a long blink (select), two in quick succession trigger a double blink (backspace)
5. **Keyboard Navigation** — The on-screen keyboard scrolls through letters, controls, and quick-phrase keys based on gaze direction, and confirms a selection on a long blink
6. **Speech Output** — Typed text can be spoken at any time via the SPEAK key, and is automatically read aloud when the session ends

## Tech Stack

- **Python** — core application logic
- **MediaPipe** — real-time face mesh and iris landmark tracking
- **OpenCV** — webcam capture and frame processing
- **Tkinter** — the on-screen keyboard and launcher UI
- **pyttsx3** — offline text-to-speech
- **PyAutoGUI** — system-level key press simulation
- **sounddevice / winsound** — audio feedback tones
- **PyInstaller** — compiles the app into a single `.exe`

## Installation

```bash
git clone https://github.com/nayathmanchanda-ui/OptiLink.git
cd OptiLink
pip install -r requirements.txt
python main.py
```

On first run, OptiLink automatically downloads the MediaPipe face landmarker model (~4 MB). **An internet connection is required for this first run only** — after that, OptiLink runs fully offline.

## Usage

- Look **left** or **right** to scroll through keys
- Hold a **long blink** to select the highlighted key
- **Double blink** to backspace
- Look to the **SPEAK** key and long-blink to hear your typed text aloud
- Press **Esc** at any time to exit — your typed text will be read back automatically when the app closes

## Building a Standalone Executable

```bash
pyinstaller --onefile --add-data "face_landmarker.task;." main.py
```

## How This Differs From Existing Tools

Free, open-source gaze-typing tools already exist — most notably [OptiKey](https://github.com/OptiKey/OptiKey), which pairs an on-screen keyboard with speech output. The key difference: OptiKey is designed around a dedicated IR eye-tracker (e.g. a Tobii 4C, ~$150 of hardware). OptiLink instead runs entirely on a standard webcam via MediaPipe's face and iris tracking — no dedicated eye-tracking hardware required at all.

## Project Status / Known Limitations

- Gaze navigation currently supports left/right scrolling only; vertical (up/down) gaze tracking is detected internally but not yet wired into navigation — a planned improvement for full 2D cursor control
- Requires a reasonably well-lit environment for reliable iris tracking
- Tested on Windows; cross-platform audio feedback falls back to a terminal beep on Linux

## Team

Built during a robotics internship by Nayath Manchanda, Yana kalra and Bhavyaa.

## License

MIT License — see [LICENSE](LICENSE) for details.
