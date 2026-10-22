import os
import csv
import time
from typing import Dict, Any, List

class SessionExporter:
    """
    Handles persisting rehabilitation session metrics to CSV in the configured export folder.
    """
    def __init__(self, export_dir: str, csv_prefix: str = "patient_session_"):
        self.export_dir = export_dir
        self.csv_prefix = csv_prefix
        os.makedirs(self.export_dir, exist_ok=True)
        
        self.session_id = time.strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(self.export_dir, f"{self.csv_prefix}{self.session_id}.csv")
        self._init_csv()

    def _init_csv(self):
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "elapsed_time_s",
                "joint_name",
                "raw_angle_deg",
                "smoothed_angle_deg",
                "posture_deviation_deg",
                "is_cheating",
                "isometry_held"
            ])

    def log_record(
        self,
        elapsed_time_s: float,
        joint_name: str,
        raw_angle: float,
        smoothed_angle: float,
        deviation: float,
        is_cheating: bool,
        isometry_held: bool
    ):
        with open(self.file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                f"{elapsed_time_s:.2f}",
                joint_name,
                f"{raw_angle:.1f}",
                f"{smoothed_angle:.1f}",
                f"{deviation:.1f}",
                int(is_cheating),
                int(isometry_held)
            ])
