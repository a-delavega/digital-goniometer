import unittest
import numpy as np
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from vision.tracker import HandTracker

class TestHandTracker(unittest.TestCase):
    
    def setUp(self):
        """Initialize the tracker before each test."""
        self.tracker = HandTracker()

    def tearDown(self):
        """Clean up MediaPipe resources after each test to prevent ghost threads."""
        self.tracker.close()

    def test_process_empty_black_frame(self):
        """Test that the tracker handles a completely black frame without crashing."""
        # Create a completely black image (height=480, width=640, 3 color channels)
        # using an 8-bit unsigned integer numpy array (standard OpenCV format)
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Process the fake frame
        annotated_frame, results = self.tracker.process_frame(black_frame)
        landmarks_3d = self.tracker.get_world_landmarks(results)
        
        # Assertions
        # 1. The tracker should return an image (even if it just returns the black frame back)
        self.assertIsNotNone(annotated_frame, "The annotated frame should not be None.")
        
        # 2. It should return None for landmarks because there are no hands in a black image
        self.assertIsNone(landmarks_3d, "World landmarks should be None when no hand is present.")

if __name__ == '__main__':
    unittest.main()