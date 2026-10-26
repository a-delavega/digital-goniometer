import unittest
import numpy as np
import sys
import os
from unittest.mock import patch
import mediapipe as mp

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from vision.tracker import HandTracker


class TestMediaPipeCompatibility(unittest.TestCase):

    def test_missing_legacy_api_has_actionable_error(self):
        with patch.object(mp, "solutions", None, create=True):
            with self.assertRaisesRegex(ImportError, "legacy Solutions API") as error:
                HandTracker()
            self.assertIn(mp.__version__, str(error.exception))
            self.assertIn(sys.executable, str(error.exception))


class TestHandTracker(unittest.TestCase):
    
    def setUp(self):
        """Initialize the tracker before each test."""
        self.tracker = HandTracker()

    def tearDown(self):
        """Clean up MediaPipe resources after each test to prevent ghost threads."""
        self.tracker.close()

    def test_process_empty_black_frame(self):
        """Test that the tracker handles a completely black frame without crashing."""
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        annotated_frame, results = self.tracker.process_frame(black_frame)
        landmarks_3d = self.tracker.get_world_landmarks(results)
        landmarks_2d = self.tracker.get_pixel_landmarks(results, black_frame.shape)
        
        # Assertions
        self.assertIsNotNone(annotated_frame, "The annotated frame should not be None.")
        self.assertIsNone(landmarks_3d, "World landmarks should be None when no hand is present.")
        self.assertIsNone(landmarks_2d, "Pixel landmarks should be None when no hand is present.")

if __name__ == '__main__':
    unittest.main()
