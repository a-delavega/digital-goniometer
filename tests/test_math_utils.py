import unittest
import numpy as np
import sys
import os

# Add the 'src' directory to the Python path to import custom modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from biomechanics.math_utils import BiomechanicsMath

class TestBiomechanicsMath(unittest.TestCase):
    
    def test_calculate_3d_angle_90_degrees(self):
        """Test that a perfect right angle returns 90.0 degrees."""
        p_proximal = np.array([1.0, 0.0, 0.0])  # Point on the X-axis
        p_vertex = np.array([0.0, 0.0, 0.0])    # Vertex at the origin
        p_distal = np.array([0.0, 1.0, 0.0])    # Point on the Y-axis
        
        angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
        
        # Assert that the calculated angle is exactly 90.0 degrees
        self.assertAlmostEqual(angle, 90.0, places=2)

    def test_calculate_3d_angle_180_degrees(self):
        """Test that a straight line returns 180.0 degrees."""
        p_proximal = np.array([-1.0, 0.0, 0.0]) # Point on the negative X-axis
        p_vertex = np.array([0.0, 0.0, 0.0])    # Vertex at the origin
        p_distal = np.array([1.0, 0.0, 0.0])    # Point on the positive X-axis
        
        angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
        
        # Assert that the calculated angle is exactly 180.0 degrees
        self.assertAlmostEqual(angle, 180.0, places=2)

    def test_calculate_angle_between_identical_vectors(self):
        """Test that the angle between two identical vectors is exactly 0.0 degrees."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        
        angle = BiomechanicsMath.calculate_angle_between_vectors(v1, v2)
        
        # Assert no deviation between identical posture vectors
        self.assertAlmostEqual(angle, 0.0, places=2)

    def test_calculate_palm_normal_orthogonal(self):
        """Test palm normal vector calculation using standard orthogonal planes."""
        # Simulating a flat palm on the XY plane
        p_wrist = np.array([0.0, 0.0, 0.0])
        p_index_mcp = np.array([1.0, 0.0, 0.0])  # Vector 1 along X-axis
        p_pinky_mcp = np.array([0.0, 1.0, 0.0])  # Vector 2 along Y-axis
        
        normal = BiomechanicsMath.calculate_palm_normal(p_wrist, p_index_mcp, p_pinky_mcp)
        
        # Cross product of X and Y axes should strictly be the Z axis [0.0, 0.0, 1.0]
        expected_normal = np.array([0.0, 0.0, 1.0])
        
        # Use numpy's built-in array testing framework for vector comparison
        np.testing.assert_array_almost_equal(normal, expected_normal, decimal=2)

if __name__ == '__main__':
    unittest.main()