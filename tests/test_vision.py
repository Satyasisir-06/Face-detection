import unittest
import numpy as np
from app.vision.face_detector import FaceDetector
from app.vision.analyzer import FaceAnalyzer

class TestVisionPipeline(unittest.TestCase):

    def setUp(self):
        self.detector = FaceDetector()
        self.analyzer = FaceAnalyzer(use_deepface=False)

    def test_face_detector_empty_frame(self):
        faces = self.detector.detect_faces(None)
        self.assertEqual(faces, [])

    def test_face_detector_synthetic_frame(self):
        # Create a synthetic image containing a filled circle (simulated face)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw a synthetic face rectangle
        img[100:250, 200:350] = (200, 180, 160)
        faces = self.detector.detect_faces(img)
        self.assertIsInstance(faces, list)

    def test_face_analyzer_crop(self):
        crop = np.full((100, 100, 3), 150, dtype=np.uint8)
        result = self.analyzer.analyze_crop(crop, face_id="test_face")
        
        self.assertIn('age', result)
        self.assertIn('gender', result)
        self.assertIn('emotion', result)
        self.assertIn('emotions_distribution', result)
        self.assertIsInstance(result['age'], int)
        self.assertIn(result['gender'], ['Male', 'Female', 'Unknown'])

if __name__ == '__main__':
    unittest.main()
