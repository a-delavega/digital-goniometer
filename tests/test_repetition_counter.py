import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from biomechanics.repetition_counter import RepetitionCounter, RepetitionState

class TestRepetitionCounter(unittest.TestCase):

    def test_full_repetition_cycle(self):
        counter = RepetitionCounter(flexion_threshold_deg=100.0, extension_threshold_deg=140.0)
        
        # Start at full extension (160 deg)
        reps, new_rep = counter.update(160.0)
        self.assertEqual(reps, 0)
        self.assertFalse(new_rep)
        self.assertEqual(counter.state, RepetitionState.EXTENSION)

        # Flex down to 90 deg (crosses below 100 deg)
        reps, new_rep = counter.update(90.0)
        self.assertEqual(reps, 0)
        self.assertFalse(new_rep)
        self.assertEqual(counter.state, RepetitionState.FLEXION)

        # Return to full extension (150 deg, crosses above 140 deg)
        reps, new_rep = counter.update(150.0)
        self.assertEqual(reps, 1)
        self.assertTrue(new_rep)
        self.assertEqual(counter.state, RepetitionState.EXTENSION)
        self.assertEqual(len(counter.rep_history), 1)
        self.assertEqual(counter.rep_history[0]["min_angle"], 90.0)
        self.assertEqual(counter.rep_history[0]["max_angle"], 150.0)

    def test_fatigue_metric_calculation(self):
        counter = RepetitionCounter(flexion_threshold_deg=100.0, extension_threshold_deg=140.0)
        
        # Rep 1: 160 -> 80 -> 160 (min=80, max=160, ROM = 80)
        counter.update(160.0)
        counter.update(80.0)
        counter.update(160.0)
        
        # Rep 2: 150 -> 100 -> 150 (min=100, max=150, ROM = 50)
        counter.update(150.0)
        counter.update(100.0)
        counter.update(150.0)

        fatigue = counter.get_fatigue_metric()
        self.assertIsNotNone(fatigue)
        # Drop from 80 to 50 is (80 - 50) / 80 = 37.5%
        self.assertAlmostEqual(fatigue, 37.5, places=1)

if __name__ == '__main__':
    unittest.main()
