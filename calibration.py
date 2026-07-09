import numpy as np

class Calibrator:
    """
    Collects (eye_x, eye_y) -> (screen_x, screen_y) pairs,
    then fits a least-squares affine transform.
    """
    def __init__(self, screen_w, screen_h):
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.eye_pts    = []
        self.screen_pts = []
        self.transform  = None

    def add_point(self, eye_xy, screen_xy):
        self.eye_pts.append(eye_xy)
        self.screen_pts.append(screen_xy)

    def calibrate(self):
        if len(self.eye_pts) < 4:
            raise ValueError("Need at least 4 calibration points")
        src = np.array(self.eye_pts,    dtype=np.float32)
        dst = np.array(self.screen_pts, dtype=np.float32)
        A   = np.column_stack([src, np.ones(len(src))])
        self.transform, _, _, _ = np.linalg.lstsq(A, dst, rcond=None)
        return self.transform

    def map(self, eye_x, eye_y):
        if self.transform is None:
            return (
                int(eye_x * self.screen_w),
                int(eye_y * self.screen_h)
            )
        pt     = np.array([eye_x, eye_y, 1.0])
        mapped = pt @ self.transform
        sx = int(np.clip(mapped[0], 0, self.screen_w  - 1))
        sy = int(np.clip(mapped[1], 0, self.screen_h - 1))
        return sx, sy
    