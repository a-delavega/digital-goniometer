import unittest
import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from biomechanics.math_utils import BiomechanicsMath, OneEuroFilter

class TestBiomechanicsMath(unittest.TestCase):
    
    def test_calculate_3d_angle_90_degrees(self):
        """Test that a perfect right angle returns 90.0 degrees."""
        p_proximal = np.array([1.0, 0.0, 0.0])
        p_vertex = np.array([0.0, 0.0, 0.0])
        p_distal = np.array([0.0, 1.0, 0.0])
        
        angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
        self.assertAlmostEqual(angle, 90.0, places=2)

    def test_calculate_3d_angle_180_degrees(self):
        """Test that a straight line returns 180.0 degrees."""
        p_proximal = np.array([-1.0, 0.0, 0.0])
        p_vertex = np.array([0.0, 0.0, 0.0])
        p_distal = np.array([1.0, 0.0, 0.0])
        
        angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
        self.assertAlmostEqual(angle, 180.0, places=2)

    def test_calculate_angle_between_identical_vectors(self):
        """Test that the angle between two identical vectors is exactly 0.0 degrees."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        
        angle = BiomechanicsMath.calculate_angle_between_vectors(v1, v2)
        self.assertAlmostEqual(angle, 0.0, places=2)

    def test_calculate_palm_normal_orthogonal(self):
        """Test palm normal vector calculation using standard orthogonal planes."""
        p_wrist = np.array([0.0, 0.0, 0.0])
        p_index_mcp = np.array([1.0, 0.0, 0.0])
        p_pinky_mcp = np.array([0.0, 1.0, 0.0])
        
        normal = BiomechanicsMath.calculate_palm_normal(p_wrist, p_index_mcp, p_pinky_mcp)
        expected_normal = np.array([0.0, 0.0, 1.0])
        np.testing.assert_array_almost_equal(normal, expected_normal, decimal=2)

    def test_one_euro_filter_smoothing(self):
        """Test that OneEuroFilter filters high frequency jitter."""
        filter_instance = OneEuroFilter(t0=0.0, x0=90.0)
        
        # Feed high-frequency jitter at small time steps
        val1 = filter_instance.filter(t=0.033, x=95.0)
        val2 = filter_instance.filter(t=0.066, x=85.0)
        
        # Smoothed output should not spike all the way to 95 or 85
        self.assertLess(val1, 95.0)
        self.assertGreater(val1, 90.0)
        self.assertGreater(val2, 85.0)

if __name__ == '__main__':
    unittest.main()
