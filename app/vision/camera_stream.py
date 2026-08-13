import cv2
import threading
import time
import base64
import numpy as np
import logging

logger = logging.getLogger("CameraStream")

class CameraStream:
    """
    Threaded Camera Manager capturing frames asynchronously from webcam or generator.
    """
    def __init__(self, camera_id: int = 0, fps: int = 30):
        self.camera_id = camera_id
        self.fps = fps
        self.cap = None
        self.running = False
        self.lock = threading.Lock()
        self.current_frame = None
        self.is_real_camera = False
        self.thread = None

    def start(self):
        """Start background camera thread."""
        if self.running:
            return

        self.running = True
        self._init_camera()
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info("Camera stream thread started.")

    def _init_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.is_real_camera = True
                logger.info(f"Connected to camera device {self.camera_id}")
            else:
                self.is_real_camera = False
                logger.warning(f"Unable to open camera {self.camera_id}. Operating in test frame generator mode.")
        except Exception as e:
            self.is_real_camera = False
            logger.warning(f"Camera initialization exception: {e}")

    def _update_loop(self):
        delay = 1.0 / self.fps
        angle = 0

        while self.running:
            start_time = time.time()
            frame = None

            if self.is_real_camera and self.cap and self.cap.isOpened():
                ret, grabbed_frame = self.cap.read()
                if ret and grabbed_frame is not None:
                    frame = grabbed_frame
                else:
                    # Camera disconnected or unreadable
                    self.is_real_camera = False

            if frame is None:
                # Generate an animated synthetic demo test frame with a simulated face
                frame = self._generate_test_frame(angle)
                angle = (angle + 3) % 360

            with self.lock:
                self.current_frame = frame

            elapsed = time.time() - start_time
            sleep_time = max(0.001, delay - elapsed)
            time.sleep(sleep_time)

    def get_frame(self) -> np.ndarray:
        """Get latest BGR frame."""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_jpeg_base64(self, frame: np.ndarray = None, quality: int = 80) -> str:
        """Encode BGR frame as JPEG base64 string."""
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return ""

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)
        if not ret:
            return ""
        return base64.b64encode(buffer).decode('utf-8')

    def stop(self):
        """Stop thread and release camera resource."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
        logger.info("Camera stream stopped.")

    def _generate_test_frame(self, angle: int) -> np.ndarray:
        """Generate a sleek synthetic webcam test frame with a sample face graphic."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Background gradient effect
        for y in range(480):
            img[y, :, 0] = int(20 + y * 0.05)
            img[y, :, 1] = int(25 + y * 0.08)
            img[y, :, 2] = int(35 + y * 0.1)

        # Draw simulated face oval in center
        cx, cy = 320 + int(np.sin(np.radians(angle)) * 20), 240 + int(np.cos(np.radians(angle)) * 10)
        cv2.ellipse(img, (cx, cy), (90, 120), 0, 0, 360, (215, 195, 175), -1)
        # Eyes
        cv2.circle(img, (cx - 35, cy - 25), 10, (60, 40, 30), -1)
        cv2.circle(img, (cx + 35, cy - 25), 10, (60, 40, 30), -1)
        # Smile
        cv2.ellipse(img, (cx, cy + 30), (35, 20), 0, 0, 180, (50, 40, 180), 4)

        # Add overlay text
        cv2.putText(img, "TEST CAMERA STREAM (No Hardware Webcam Detected)", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
        cv2.putText(img, "Connect USB/Built-in webcam to switch to live feed", (30, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        return img
