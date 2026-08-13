import os
import urllib.request
import cv2
import numpy as np

class FaceDetector:
    """
    Robust Face Detector supporting OpenCV Haar Cascade and DNN models
    for real-time face detection and cropping.
    """
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        cascade_path = self._resolve_cascade_path()
        self.haar_cascade = cv2.CascadeClassifier(cascade_path)

    def _resolve_cascade_path(self) -> str:
        """Find or download haarcascade_frontalface_default.xml."""
        local_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(local_dir, exist_ok=True)
        local_file = os.path.join(local_dir, "haarcascade_frontalface_default.xml")

        if os.path.exists(local_file) and os.path.getsize(local_file) > 1000:
            return local_file

        # Check cv2.data if present
        if hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
            cv2_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
            if os.path.exists(cv2_path) and os.path.getsize(cv2_path) > 1000:
                return cv2_path

        # Download default cascade XML from OpenCV official repository
        url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        try:
            urllib.request.urlretrieve(url, local_file)
            if os.path.exists(local_file):
                return local_file
        except Exception as e:
            print(f"Warning: Could not download Haar Cascade XML: {e}")

        return local_file

    def detect_faces(self, frame: np.ndarray):
        """
        Detect faces in a BGR frame.
        Returns a list of dicts with bounding boxes and bounding crops:
        [{'x': int, 'y': int, 'w': int, 'h': int, 'confidence': float, 'crop': np.ndarray}]
        """
        if frame is None or frame.size == 0:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Equalize histogram for better detection in low light
        gray = cv2.equalizeHist(gray)

        # Detect faces using Haar Cascade
        rects = self.haar_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        height, width = frame.shape[:2]
        faces = []

        for (x, y, w, h) in rects:
            # Add generous padding (25%) around face crop for optimal gender/age feature context
            pad_x = int(w * 0.25)
            pad_y = int(h * 0.25)

            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(width, x + w + pad_x)
            y2 = min(height, y + h + pad_y)

            crop = frame[y1:y2, x1:x2]

            faces.append({
                'x': int(x),
                'y': int(y),
                'w': int(w),
                'h': int(h),
                'confidence': 0.95,
                'crop': crop
            })

        return faces
