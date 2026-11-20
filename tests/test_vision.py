import unittest
import numpy as np
from fastapi.testclient import TestClient

from app.vision.face_detector import FaceDetector
from app.vision.analyzer import FaceAnalyzer
from app.api.server import app

class TestVisionPipeline(unittest.TestCase):

    def setUp(self):
        self.detector = FaceDetector()
        self.analyzer = FaceAnalyzer(use_deepface=False)

    def test_face_detector_empty_frame(self):
        faces = self.detector.detect_faces(None)
        self.assertEqual(faces, [])

    def test_face_detector_synthetic_frame(self):
        # Create a synthetic image containing a simulated face rectangle
        img = np.zeros((480, 640, 3), dtype=np.uint8)
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
        self.assertIn('is_suspect', result)
        self.assertIn('identity', result)
        self.assertIn('threat_level', result)
        self.assertIsInstance(result['age'], int)
        self.assertIn(result['gender'], ['Male', 'Female', 'Unknown'])

    def test_enrolled_watchlist_profiles(self):
        """Verify watchlist has Sailu and Deepika as suspects, and others as members."""
        enrolled = {m['id']: m for m in self.analyzer.enrolled_faces}
        
        # Verify suspects
        self.assertIn('sailu', enrolled, "Sailu must be enrolled in watchlist")
        self.assertTrue(enrolled['sailu']['is_suspect'], "Sailu must be classified as a suspect")
        self.assertEqual(enrolled['sailu']['threat_level'], 'CRITICAL')

        self.assertIn('deepika', enrolled, "Deepika must be enrolled in watchlist")
        self.assertTrue(enrolled['deepika']['is_suspect'], "Deepika must be classified as a suspect")
        self.assertEqual(enrolled['deepika']['threat_level'], 'CRITICAL')

        # Verify authorized members
        for mem_id, mem_name in [('bhargavi', 'Bhargavi'), ('jhansi', 'Jhansi'), ('reeshma', 'Reeshma')]:
            self.assertIn(mem_id, enrolled, f"{mem_name} must be enrolled in watchlist")
            self.assertFalse(enrolled[mem_id]['is_suspect'], f"{mem_name} must NOT be classified as suspect")
            self.assertEqual(enrolled[mem_id]['threat_level'], 'NONE')
            self.assertEqual(enrolled[mem_id]['status'], 'AUTHORIZED MEMBER')

    def test_suspect_identification_logic(self):
        """Verify similarity search correctly flags suspects vs authorized members."""
        enrolled = {m['id']: m for m in self.analyzer.enrolled_faces}
        
        # Mocking query vectors identical to enrolled embeddings
        for target_id in ['sailu', 'deepika']:
            target_vec = np.array(enrolled[target_id]['embedding'], dtype=np.float32)
            # Find best match using cosine similarity logic
            best_dist = float('inf')
            best_match = None
            for m in self.analyzer.enrolled_faces:
                v = np.array(m['embedding'], dtype=np.float32)
                cos_sim = np.dot(target_vec, v) / (np.linalg.norm(target_vec) * np.linalg.norm(v))
                dist = 1.0 - cos_sim
                if dist < best_dist:
                    best_dist = dist
                    best_match = m
            
            self.assertEqual(best_match['id'], target_id)
            self.assertTrue(best_match['is_suspect'])
            self.assertAlmostEqual(best_dist, 0.0, places=4)

        for target_id in ['bhargavi', 'jhansi', 'reeshma']:
            target_vec = np.array(enrolled[target_id]['embedding'], dtype=np.float32)
            best_dist = float('inf')
            best_match = None
            for m in self.analyzer.enrolled_faces:
                v = np.array(m['embedding'], dtype=np.float32)
                cos_sim = np.dot(target_vec, v) / (np.linalg.norm(target_vec) * np.linalg.norm(v))
                dist = 1.0 - cos_sim
                if dist < best_dist:
                    best_dist = dist
                    best_match = m
            
            self.assertEqual(best_match['id'], target_id)
            self.assertFalse(best_match['is_suspect'])
            self.assertEqual(best_match['threat_level'], 'NONE')

    def test_unknown_face_rejection(self):
        """Verify orthogonal / random embedding does not match suspects or members."""
        # Create an orthogonal vector
        rnd_vec = np.random.randn(128).astype(np.float32)
        rnd_norm = np.linalg.norm(rnd_vec)
        
        best_dist = float('inf')
        threshold = 0.40
        for m in self.analyzer.enrolled_faces:
            v = np.array(m['embedding'], dtype=np.float32)
            cos_sim = np.dot(rnd_vec, v) / (rnd_norm * np.linalg.norm(v))
            dist = 1.0 - cos_sim
            if dist < best_dist:
                best_dist = dist
        
        # Random vector will have cosine distance around 1.0, exceeding threshold
        self.assertGreater(best_dist, threshold)

    def test_api_members_endpoint(self):
        """Test GET /api/members returns correct suspect and member counts."""
        client = TestClient(app)
        response = client.get("/api/members")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 5)
        self.assertEqual(data["suspects_count"], 2)
        self.assertEqual(data["members_count"], 3)
        ids = [m["id"] for m in data["members"]]
        self.assertIn("sailu", ids)
        self.assertIn("deepika", ids)
        self.assertIn("bhargavi", ids)
        self.assertIn("jhansi", ids)
        self.assertIn("reeshma", ids)

if __name__ == '__main__':
    unittest.main()
