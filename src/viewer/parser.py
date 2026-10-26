import os
import json
import csv
from typing import Dict, Any, List

def parse_session_csv(file_path: str) -> Dict[str, Any]:
    """
    Parses a goniometer patient session CSV file and extracts clinical metrics
    and time series data ready for dashboard visualization.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    records: List[Dict[str, Any]] = []

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                records.append({
                    "timestamp": float(row.get("timestamp", 0.0)),
                    "elapsed_time_s": float(row.get("elapsed_time_s", 0.0)),
                    "joint_name": row.get("joint_name", "UNKNOWN"),
                    "raw_angle_deg": float(row.get("raw_angle_deg", 0.0)),
                    "smoothed_angle_deg": float(row.get("smoothed_angle_deg", 0.0)),
                    "posture_deviation_deg": float(row.get("posture_deviation_deg", 0.0)),
                    "is_cheating": int(row.get("is_cheating", 0)) == 1,
                    "isometry_held": int(row.get("isometry_held", 0)) == 1,
                })
            except (ValueError, TypeError):
                continue

    if not records:
        return {
            "filename": filename,
            "total_records": 0,
            "duration_s": 0.0,
            "joints": {},
            "global_metrics": {
                "cheating_frames": 0,
                "cheating_percentage": 0.0,
                "isometry_frames": 0
            }
        }

    duration = max(r["elapsed_time_s"] for r in records) - min(r["elapsed_time_s"] for r in records)
    total_records = len(records)
    cheating_count = sum(1 for r in records if r["is_cheating"])
    isometry_count = sum(1 for r in records if r["isometry_held"])

    # Group by joint
    joints_data: Dict[str, Dict[str, Any]] = {}
    for r in records:
        jname = r["joint_name"]
        if jname not in joints_data:
            joints_data[jname] = {
                "timestamps": [],
                "elapsed": [],
                "raw_angles": [],
                "smoothed_angles": [],
                "deviations": [],
                "cheating": [],
                "isometry": []
            }
        jd = joints_data[jname]
        jd["timestamps"].append(r["timestamp"])
        jd["elapsed"].append(r["elapsed_time_s"])
        jd["raw_angles"].append(r["raw_angle_deg"])
        jd["smoothed_angles"].append(r["smoothed_angle_deg"])
        jd["deviations"].append(r["posture_deviation_deg"])
        jd["cheating"].append(1 if r["is_cheating"] else 0)
        jd["isometry"].append(1 if r["isometry_held"] else 0)

    # Compute per-joint statistics
    joint_summaries: Dict[str, Any] = {}
    for jname, data in joints_data.items():
        angles = data["smoothed_angles"]
        min_ang = min(angles) if angles else 0.0
        max_ang = max(angles) if angles else 0.0
        rom = max_ang - min_ang
        avg_ang = sum(angles) / len(angles) if angles else 0.0
        
        joint_summaries[jname] = {
            "series": data,
            "rom_deg": round(rom, 1),
            "min_angle_deg": round(min_ang, 1),
            "max_angle_deg": round(max_ang, 1),
            "avg_angle_deg": round(avg_ang, 1),
            "sample_count": len(angles)
        }

    return {
        "filename": filename,
        "total_records": total_records,
        "duration_s": round(duration, 1),
        "joints": joint_summaries,
        "global_metrics": {
            "cheating_frames": cheating_count,
            "cheating_percentage": round((cheating_count / total_records) * 100, 1) if total_records else 0.0,
            "isometry_frames": isometry_count
        }
    }
