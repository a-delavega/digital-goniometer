import unittest
import os
import shutil
import tempfile
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.session_exporter import SessionExporter

class TestSessionExporter(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_csv_creation_and_logging(self):
        exporter = SessionExporter(export_dir=self.test_dir, csv_prefix="test_session_")
        self.assertTrue(os.path.exists(exporter.file_path))

        exporter.log_record(
            elapsed_time_s=1.5,
            joint_name="INDEX_MCP",
            raw_angle=92.3,
            smoothed_angle=90.1,
            deviation=5.0,
            is_cheating=False,
            isometry_held=True,
            reps_completed=3,
            handedness="Right"
        )

        with open(exporter.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)  # Header + 1 record
        self.assertIn("INDEX_MCP", lines[1])
        self.assertIn("Right", lines[1])
        self.assertIn("90.1", lines[1])
        self.assertIn(",3", lines[1])

if __name__ == '__main__':
    unittest.main()
