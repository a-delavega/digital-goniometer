import unittest
import sys
import os

# Add the 'src' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.config import RehabConfig

class TestRehabConfig(unittest.TestCase):
    
    def test_medical_thresholds_exist_and_are_valid(self):
        """Test that medical configuration thresholds are strictly defined as positive floats."""
        
        # 1. Test MAX_PALM_DEVIATION_DEGREES
        self.assertTrue(hasattr(RehabConfig, 'MAX_PALM_DEVIATION_DEGREES'), 
                        "Missing MAX_PALM_DEVIATION_DEGREES in RehabConfig.")
        self.assertIsInstance(RehabConfig.MAX_PALM_DEVIATION_DEGREES, float, 
                              "MAX_PALM_DEVIATION_DEGREES must be a float.")
        self.assertGreater(RehabConfig.MAX_PALM_DEVIATION_DEGREES, 0.0, 
                           "Deviation threshold must be greater than zero.")
        
        # 2. Test ISOMETRY_HOLD_SECONDS
        self.assertTrue(hasattr(RehabConfig, 'ISOMETRY_HOLD_SECONDS'), 
                        "Missing ISOMETRY_HOLD_SECONDS in RehabConfig.")
        self.assertIsInstance(RehabConfig.ISOMETRY_HOLD_SECONDS, float, 
                              "ISOMETRY_HOLD_SECONDS must be a float.")
        self.assertGreater(RehabConfig.ISOMETRY_HOLD_SECONDS, 0.0, 
                           "Hold seconds must be greater than zero.")

if __name__ == '__main__':
    unittest.main()