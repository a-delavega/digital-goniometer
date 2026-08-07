import unittest
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from biomechanics.joints_map import HandJoint

class TestHandJointMap(unittest.TestCase):
    
    def test_all_joints_have_three_indices(self):
        """Test that every defined joint contains exactly 3 landmark indices."""
        for joint in HandJoint:
            indices = joint.indices
            
            # Assert the tuple has exactly 3 elements (Proximal, Vertex, Distal)
            self.assertEqual(len(indices), 3, f"{joint.name} does not have exactly 3 indices.")
            
    def test_indices_within_mediapipe_bounds(self):
        """Test that all landmark indices are within MediaPipe's valid range (0-20)."""
        for joint in HandJoint:
            for index in joint.indices:
                # Assert index is an integer between 0 and 20
                self.assertIsInstance(index, int)
                self.assertTrue(0 <= index <= 20, f"Index {index} in {joint.name} is out of bounds.")

if __name__ == '__main__':
    unittest.main()