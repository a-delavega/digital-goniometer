import threading
import cv2
from typing import Optional, Tuple
import numpy as np

class VideoStream:
    """
    Threaded video capture stream to prevent OpenCV I/O from blocking
    the main inference and rendering loop.
    """
    def __init__(self, src: int = 0):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

    def is_opened(self) -> bool:
        return self.cap.isOpened()

    def start(self) -> "VideoStream":
        if self.started:
            return self
        self.started = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        return self

    def _update(self):
        while self.started:
            grabbed, frame = self.cap.read()
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame
            if not grabbed:
                break

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self.read_lock:
            if not self.grabbed or self.frame is None:
                return False, None
            return True, self.frame.copy()

    def stop(self):
        self.started = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap.isOpened():
            self.cap.release()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
