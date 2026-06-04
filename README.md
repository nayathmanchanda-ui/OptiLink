# OptiLink — Hands-Free Gaze-Controlled Typing System

OptiLink is a hands-free virtual keyboard for Windows, controlled entirely through eye movement and blink detection. Designed for individuals with motor disabilities, it requires no specialized hardware — only a standard webcam.

---

## Background

Millions of people living with ALS, cerebral palsy, spinal cord injuries, or upper limb disabilities are unable to use conventional input devices. Existing assistive communication solutions are often prohibitively expensive ($5,000–$30,000+), hardware-dependent, and inaccessible to most users globally. OptiLink was built to address this gap — providing a free, accessible alternative that works on any standard PC.

---

## How It Works

OptiLink uses Google's MediaPipe Face Mesh to track 468 facial landmarks in real time at 60 FPS. Iris position is used to estimate gaze direction, which controls a highlight cursor across the on-screen keyboard. Key selection is triggered by blink gestures:

- **Long blink** — select the highlighted key
- **Double blink** — backspace / delete
- **Auto-calibrated threshold** — blink sensitivity is personalized during an initial calibration step before use

Typed text is rendered on screen and read aloud through an offline text-to-speech engine.

---

## Features

| Feature | Details |
|---|---|
| Gaze-Controlled Navigation | Iris tracking via MediaPipe Face Mesh at 60 FPS |
| Blink-to-Select Input | Long blink to select, double blink for backspace |
| Auto-Calibration | Blink threshold personalized per user on startup |
| Text-to-Speech | Offline voice output via pyttsx3 |
| Audio Feedback | Keypress confirmation sounds on every selection |
| Full Keyboard Layout | All letters, numbers, symbols, space, clear, and speak controls |
| Offline Operation | Fully functional without internet after first run |
| Single Executable | Ships as a standalone .exe — no installation required |

---

## Technology Stack

| Library | Purpose |
|---|---|
| Python | Core application logic |
| MediaPipe | Real-time face mesh and iris landmark detection |
| OpenCV | Webcam capture and image processing |
| Tkinter | Virtual keyboard GUI |
| pyttsx3 | Offline text-to-speech output |
| PyInstaller | Compiles the application into a single .exe |

---

## Comparison with Existing Solutions

| | Traditional Assistive Devices | OptiLink |
|---|---|---|
| Cost | $5,000 – $30,000+ | Free |
| Hardware Required | Specialized equipment | Standard webcam |
| Portability | Fixed, bulky setup | Any Windows PC |
| Setup | Complex, technical | Single .exe, one click |
| Internet Dependency | Often cloud-reliant | Fully offline |

---

## Getting Started

### Run from Source

```bash
git clone https://github.com/nayathmanchanda-ui/optilink.git
cd optilink
pip install mediapipe opencv-python pyttsx3
python main.py
```

### Download Executable

A pre-built Windows executable is available at [gazekeyboard.vercel.app](https://gazekeyboard.vercel.app). No installation required — download and run.

---

## System Requirements

| | Minimum |
|---|---|
| OS | Windows 10 (64-bit) |
| Webcam | Any standard built-in or USB webcam |
| RAM | 4 GB |
| Internet | Required on first run only |

---

## Links

- Website: [gazekeyboard.vercel.app](https://gazekeyboard.vercel.app)
