import cv2
import numpy as np
import cvzone
import os
import sys
import time
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE   = [33, 160, 158, 133, 153, 144]
RIGHT_EYE  = [362, 385, 387, 263, 373, 380]

LEFT_EYE_LEFT_CORNER  = 33
LEFT_EYE_RIGHT_CORNER = 133
RIGHT_EYE_LEFT_CORNER = 362
RIGHT_EYE_RIGHT_CORNER= 263

LEFT_EYE_TOP    = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP   = 386
RIGHT_EYE_BOTTOM= 374

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

def _resource_path(filename):
    """
    Returns the correct path to a bundled resource whether running
    as a plain .py script or as a PyInstaller-frozen .exe.
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle — files are in _MEIPASS
        base = sys._MEIPASS
    else:
        # Normal script — same folder as this file
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)

MODEL_PATH = _resource_path("face_landmarker.task")

# ... rest of the file unchanged from here ...

def eye_aspect_ratio(landmarks, eye_indices, img_w, img_h):
    pts = np.array([
        [landmarks[i].x * img_w, landmarks[i].y * img_h]
        for i in eye_indices
    ])
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    return (A + B) / (2.0 * C)


class EyeTracker:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            print("Downloading face landmarker model (~29 MB)...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("Download complete.")

        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
        )
        self.detector        = mp_vision.FaceLandmarker.create_from_options(options)
        self.blink_threshold = 0.22
        self.blink_frames    = 0
        self.blink_consec    = 3
        self.long_blink_frames = 15
        self.last_ear        = None

        self._last_blink_time   = 0.0
        self._double_blink_gap  = 0.5
        self._pending_blink     = False

        self.LEFT_THRESH  = 0.40
        self.RIGHT_THRESH = 0.60
        self.UP_THRESH    = 0.40
        self.DOWN_THRESH  = 0.60

        self._h_buf = []
        self._v_buf = []
        self.SMOOTH = 5

    def process(self, frame):
        h, w     = frame.shape[:2]
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result   = self.detector.detect(mp_image)

        if not result.face_landmarks:
            self.last_ear = None
            return None, None, None, None, False, False

        lm = result.face_landmarks[0]

        def iris_centre(indices):
            xs = [lm[i].x for i in indices]
            ys = [lm[i].y for i in indices]
            return float(np.mean(xs)), float(np.mean(ys))

        lx, ly = iris_centre(LEFT_IRIS)
        rx, ry = iris_centre(RIGHT_IRIS)
        gaze_x = (lx + rx) / 2.0
        gaze_y = (ly + ry) / 2.0

        ll = lm[LEFT_EYE_LEFT_CORNER].x
        lr = lm[LEFT_EYE_RIGHT_CORNER].x
        rl = lm[RIGHT_EYE_LEFT_CORNER].x
        rr = lm[RIGHT_EYE_RIGHT_CORNER].x

        l_eye_cx   = (ll + lr) / 2.0
        l_half_w   = max(abs(lr - ll) / 2.0, 0.001)
        l_h_offset = (lx - l_eye_cx) / l_half_w

        r_eye_cx   = (rl + rr) / 2.0
        r_half_w   = max(abs(rr - rl) / 2.0, 0.001)
        r_h_offset = (rx - r_eye_cx) / r_half_w

        h_ratio = float(np.clip((l_h_offset + r_h_offset) / 2.0 * 0.5 + 0.5, 0.0, 1.0))

        lt  = lm[LEFT_EYE_TOP].y
        lb  = lm[LEFT_EYE_BOTTOM].y
        rt  = lm[RIGHT_EYE_TOP].y
        rb  = lm[RIGHT_EYE_BOTTOM].y

        l_eye_cy   = (lt + lb) / 2.0
        l_half_h   = max(abs(lb - lt) / 2.0, 0.001)
        l_v_offset = (ly - l_eye_cy) / l_half_h

        r_eye_cy   = (rt + rb) / 2.0
        r_half_h   = max(abs(rb - rt) / 2.0, 0.001)
        r_v_offset = (ry - r_eye_cy) / r_half_h

        v_ratio = float(np.clip((l_v_offset + r_v_offset) / 2.0 * 0.5 + 0.5, 0.0, 1.0))

        self._h_buf.append(h_ratio)
        self._v_buf.append(v_ratio)
        if len(self._h_buf) > self.SMOOTH: self._h_buf.pop(0)
        if len(self._v_buf) > self.SMOOTH: self._v_buf.pop(0)
        h_smooth = float(np.mean(self._h_buf))
        v_smooth = float(np.mean(self._v_buf))

        ear = (
            eye_aspect_ratio(lm, LEFT_EYE,  w, h) +
            eye_aspect_ratio(lm, RIGHT_EYE, w, h)
        ) / 2.0
        self.last_ear = ear

        long_blink   = False
        double_blink = False

        if ear < self.blink_threshold:
            self.blink_frames += 1
        else:
            if self.blink_frames >= self.long_blink_frames:
                long_blink = True
                self._pending_blink = False
            elif self.blink_frames >= self.blink_consec:
                now = time.time()
                if self._pending_blink and (now - self._last_blink_time) <= self._double_blink_gap:
                    double_blink = True
                    self._pending_blink = False
                else:
                    self._pending_blink = True
                    self._last_blink_time = now
            self.blink_frames = 0

        return (lx, ly), (rx, ry), h_smooth, v_smooth, long_blink, double_blink

    def get_direction(self, h_ratio, v_ratio):
        if h_ratio is None:
            return "center"
        if h_ratio < self.LEFT_THRESH:
            return "left"
        if h_ratio > self.RIGHT_THRESH:
            return "right"
        return "center"

    def draw_debug(self, frame, left_iris, right_iris, h_ratio, v_ratio,
                   direction="center", ear=None, blink=False):
        h, w = frame.shape[:2]
        if left_iris is not None:
            lx_px = int(left_iris[0] * w);  ly_px = int(left_iris[1] * h)
            rx_px = int(right_iris[0] * w); ry_px = int(right_iris[1] * h)

            cv2.circle(frame, (lx_px, ly_px), 6, (255, 255, 0), -1)
            cv2.circle(frame, (rx_px, ry_px), 6, (255, 0, 255), -1)

            dir_colour = {
                "left":   (0, 165, 255),
                "right":  (0, 255, 0),
                "up":     (255, 0, 0),
                "down":   (0, 0, 255),
                "center": (200, 200, 200),
            }.get(direction, (200, 200, 200))

            cvzone.putTextRect(frame, f"DIR: {direction.upper()}",
                               (10, 30), scale=1, thickness=1,
                               colorR=dir_colour, colorT=(0,0,0), offset=5)
            if h_ratio is not None:
                cvzone.putTextRect(frame, f"H:{h_ratio:.2f} V:{v_ratio:.2f}",
                                   (10, 65), scale=0.8, thickness=1,
                                   colorR=(40,40,40), colorT=(255,255,255), offset=4)
            if ear is not None:
                cvzone.putTextRect(frame, f"EAR:{ear:.3f}",
                                   (10, 95), scale=0.8, thickness=1,
                                   colorR=(40,40,40), colorT=(255,255,255), offset=4)
            if blink:
                cvzone.putTextRect(frame, "BLINK!", (10, 125),
                                   scale=1.2, thickness=2,
                                   colorR=(0, 0, 200), colorT=(255,255,255), offset=8)
        else:
            cvzone.putTextRect(frame, "No face", (10, 30),
                               scale=1, thickness=1,
                               colorR=(0,0,180), colorT=(255,255,255), offset=6)
        return frame

    def release(self):
        self.detector.close()