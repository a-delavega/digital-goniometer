import unittest
import os
import sys
import tempfile
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from viewer.parser import parse_session_csv

class TestViewerParser(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8")
        writer = csv.writer(self.temp_file)
        writer.writerow([
            "timestamp", "elapsed_time_s", "joint_name", "raw_angle_deg",
            "smoothed_angle_deg", "posture_deviation_deg", "is_cheating", "isometry_held"
        ])
        writer.writerow([100.0, 1.0, "INDEX_MCP", 120.0, 119.5, 2.0, 0, 0])
        writer.writerow([101.0, 2.0, "INDEX_MCP", 90.0, 90.5, 18.0, 1, 1])
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_parse_session_csv_computes_metrics(self):
        data = parse_session_csv(self.temp_file.name)
        self.assertEqual(data["total_records"], 2)
        self.assertEqual(data["duration_s"], 1.0)
        self.assertIn("INDEX_MCP", data["joints"])
        
        mcp = data["joints"]["INDEX_MCP"]
        self.assertEqual(mcp["min_angle_deg"], 90.5)
        self.assertEqual(mcp["max_angle_deg"], 119.5)
        self.assertEqual(mcp["rom_deg"], 29.0)
        
        # Check global metrics
        self.assertEqual(data["global_metrics"]["cheating_frames"], 1)
        self.assertEqual(data["global_metrics"]["cheating_percentage"], 50.0)
        self.assertEqual(data["global_metrics"]["isometry_frames"], 1)

    def test_parse_empty_csv(self):
        empty_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8")
        empty_file.close()
        data = parse_session_csv(empty_file.name)
        self.assertEqual(data["total_records"], 0)
        os.remove(empty_file.name)

if __name__ == '__main__':
    unittest.main()
