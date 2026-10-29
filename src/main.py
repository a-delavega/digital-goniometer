import cv2
import sys
import os
import subprocess
import argparse
import time
import math
from collections import deque
import numpy as np
from typing import List, Dict, Optional, Tuple

# Automatically detect and re-execute inside the project virtual environment (venv)
# if the script was launched using a global Python or an external environment.
_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_VENV_PYTHON = os.path.join(_PROJECT_ROOT, "venv", "Scripts", "python.exe")

if (
    os.path.exists(_VENV_PYTHON)
    and os.path.normpath(sys.executable).lower() != os.path.normpath(_VENV_PYTHON).lower()
    and os.environ.get("GONIO_REEXEC") != "1"
):
    env = os.environ.copy()
    env["GONIO_REEXEC"] = "1"
    res = subprocess.run([_VENV_PYTHON, os.path.abspath(__file__)] + sys.argv[1:], env=env)
    sys.exit(res.returncode)

# Ensure 'src' is always on sys.path regardless of execution working directory
sys.path.insert(0, _SCRIPT_DIR)

# Import our custom modules
from biomechanics.joints_map import HandJoint
from biomechanics.math_utils import BiomechanicsMath, OneEuroFilter
from biomechanics.repetition_counter import RepetitionCounter
from vision.tracker import HandTracker
from vision.stream import VideoStream
from core.config import RehabConfig
from core.session_exporter import SessionExporter


class GoniometerApp:
    """
    Main Orchestrator App.
    Coordinates camera input, AI tracking, biometric math, filtering, session export, and UI rendering.
    """
    
    # Visual color palette (BGR)
    PALETTE = [
        (0, 255, 255),  # Yellow
        (255, 128, 0),  # Cyan / Light Blue
        (0, 200, 100),  # Bright Green
    ]

    def __init__(self, target_joints: List[HandJoint], camera_index: int = 0, export_session: bool = True):
        self.target_joints = target_joints[:3] 
        self.tracker = HandTracker()
        self.stream = VideoStream(camera_index)
        
        # State variables for posture calibration
        self.baseline_palm_normal: Optional[np.ndarray] = None
        self.calibration_buffer: List[np.ndarray] = []
        self.is_calibrated = False
        
        # Filtering (One Euro Filter per joint)
        self.filters: Dict[str, OneEuroFilter] = {}
        
        # Repetition counters per joint
        self.rep_counters: Dict[str, RepetitionCounter] = {
            joint.name: RepetitionCounter() for joint in self.target_joints
        }
        
        # Real-time history buffer for mini-oscilloscope graph (last 100 frames per joint)
        self.history: Dict[str, deque] = {joint.name: deque(maxlen=100) for joint in self.target_joints}
        
        # Isometry state tracking per joint: {joint_name: (reference_angle, start_time, held)}
        self.isometry_tracker: Dict[str, Dict] = {}
        
        # Session Exporting
        self.exporter = SessionExporter(RehabConfig.EXPORT_DIR, RehabConfig.CSV_PREFIX) if export_session else None
        self.start_time = time.time()
        
        if not self.stream.is_opened():
            print("[ERROR] Could not access the webcam. Please check your hardware.")
            sys.exit(1)

    def reset_calibration(self):
        """Allows patient/clinician to recalibrate posture without restarting the app."""
        self.baseline_palm_normal = None
        self.calibration_buffer.clear()
        self.is_calibrated = False
        print("[INFO] Posture calibration reset.")

    def _draw_hud(self, frame: np.ndarray, deviation: float, is_cheating: bool, handedness_info: Optional[Tuple[str, float]] = None):
        """Renders header overlay with posture alert status, detected hand, and keyboard shortcuts."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (490, 60), (25, 25, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        hand_tag = ""
        if handedness_info:
            label, conf = handedness_info
            hand_tag = f" | {label.upper()} ({int(conf * 100)}%)"

        if not self.is_calibrated:
            progress = len(self.calibration_buffer)
            total = RehabConfig.CALIBRATION_FRAMES_REQUIRED
            text = f"CALIBRATING: {progress}/{total}{hand_tag}"
            color = (0, 215, 255) # Amber
        elif is_cheating:
            text = f"COMPENSATION ALERT! Rot: {int(deviation)} deg{hand_tag}"
            color = (0, 0, 255) # Red
        else:
            text = f"POSTURE OK (Dev: {int(deviation)} deg){hand_tag}"
            color = (0, 255, 0) # Green

        cv2.putText(frame, text, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.60, color, 2)
        cv2.putText(frame, "Keys: [C] Recalibrate | [Q] Quit", (15, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def _draw_joint_biofeedback(
        self,
        frame: np.ndarray,
        p_prox_2d: np.ndarray,
        p_vert_2d: np.ndarray,
        p_dist_2d: np.ndarray,
        angle: float,
        color: Tuple[int, int, int],
        is_held: bool
    ):
        """
        Draws dynamic visual biofeedback on the hand:
        - Glowing skeletal bone vectors connecting the joint.
        - Vertex circle marker.
        - Angular circular sector/arc representing current Range of Motion.
        - Live floating angle badge near the vertex.
        """
        vx, vy = int(p_vert_2d[0]), int(p_vert_2d[1])
        px, py = int(p_prox_2d[0]), int(p_prox_2d[1])
        dx, dy = int(p_dist_2d[0]), int(p_dist_2d[1])

        # Draw bone vectors
        bone_color = (0, 255, 255) if is_held else color
        cv2.line(frame, (px, py), (vx, vy), bone_color, 3, cv2.LINE_AA)
        cv2.line(frame, (vx, vy), (dx, dy), bone_color, 3, cv2.LINE_AA)

        # Draw vertex anchor
        cv2.circle(frame, (vx, vy), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (vx, vy), 9, bone_color, 2, cv2.LINE_AA)

        # Draw angular arc sector
        v_prox = np.array([px - vx, py - vy], dtype=float)
        v_dist = np.array([dx - vx, dy - vy], dtype=float)

        len_prox = np.linalg.norm(v_prox)
        len_dist = np.linalg.norm(v_dist)

        if len_prox > 5 and len_dist > 5:
            ang_prox = math.degrees(math.atan2(v_prox[1], v_prox[0]))
            ang_dist = math.degrees(math.atan2(v_dist[1], v_dist[0]))

            # Determine angular sweep direction
            diff = (ang_dist - ang_prox) % 360
            radius = int(min(len_prox, len_dist) * 0.45)
            radius = max(18, min(40, radius))

            start_angle = ang_prox
            end_angle = ang_prox + diff if diff <= 180 else ang_prox - (360 - diff)

            overlay = frame.copy()
            cv2.ellipse(
                overlay,
                (vx, vy),
                (radius, radius),
                0,
                start_angle,
                end_angle,
                bone_color,
                -1,
                cv2.LINE_AA
            )
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
            cv2.ellipse(
                frame,
                (vx, vy),
                (radius, radius),
                0,
                start_angle,
                end_angle,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )

        # Floating angle badge
        badge_text = f"{int(angle)} deg"
        badge_x = vx + 15
        badge_y = vy - 10
        cv2.rectangle(frame, (badge_x - 4, badge_y - 14), (badge_x + 65, badge_y + 6), (20, 20, 20), -1)
        cv2.putText(frame, badge_text, (badge_x, badge_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    def _draw_oscilloscope_graph(self, frame: np.ndarray):
        """
        Renders a live mini real-time graph (oscilloscope) at the bottom-right
        tracking the angular flexion trajectory of each joint over time.
        """
        h, w = frame.shape[:2]
        gw, gh = 230, 95
        gx = w - gw - 15
        gy = h - gh - 20

        # Background card with translucency
        overlay = frame.copy()
        cv2.rectangle(overlay, (gx, gy), (gx + gw, gy + gh), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        cv2.rectangle(frame, (gx, gy), (gx + gw, gy + gh), (80, 80, 80), 1)

        # Guide reference lines (180 deg top, 90 deg middle, 0 deg bottom)
        cv2.putText(frame, "ROM History", (gx + 8, gy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        y_90 = gy + int(gh * 0.5)
        cv2.line(frame, (gx + 30, y_90), (gx + gw - 8, y_90), (50, 50, 50), 1)
        cv2.putText(frame, "90", (gx + 8, y_90 + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (120, 120, 120), 1)

        # Plot line curves per joint
        for idx, joint in enumerate(self.target_joints):
            points = self.history.get(joint.name, [])
            if len(points) < 2:
                continue

            color = self.PALETTE[idx % len(self.PALETTE)]
            n = len(points)
            step = (gw - 40) / max(1, points.maxlen - 1)

            curve_pts = []
            for i, val in enumerate(points):
                px = int(gx + 32 + (i + (points.maxlen - n)) * step)
                # Map 0..180 deg to bottom..top of graph area
                normalized_val = np.clip(val / 180.0, 0.0, 1.0)
                py = int(gy + gh - 8 - (normalized_val * (gh - 26)))
                curve_pts.append((px, py))

            for i in range(len(curve_pts) - 1):
                cv2.line(frame, curve_pts[i], curve_pts[i + 1], color, 2, cv2.LINE_AA)

    def run(self):
        print(f"\n[INFO] Starting Digital Goniometer for {len(self.target_joints)} joint(s).")
        print("[INFO] Press 'c' to recalibrate posture, 'q' to exit.\n")
        
        window_name = 'Digital Goniometer - Rehab Edge AI'
        self.stream.start()
        last_log_time = 0.0

        try:
            while True:
                success, frame = self.stream.read()
                if not success or frame is None:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                current_time = time.time()
                elapsed_session = current_time - self.start_time

                annotated_frame, results = self.tracker.process_frame(frame)
                landmarks_3d = self.tracker.get_world_landmarks(results)
                landmarks_2d = self.tracker.get_pixel_landmarks(results, annotated_frame.shape)
                handedness_info = self.tracker.get_handedness(results)
                
                deviation = 0.0
                is_cheating = False

                if landmarks_3d is not None:
                    # --- CHEAT DETECTION & CALIBRATION ---
                    p_wrist = landmarks_3d[0]
                    p_index_mcp = landmarks_3d[5]
                    p_pinky_mcp = landmarks_3d[17]
                    
                    current_palm_normal = BiomechanicsMath.calculate_palm_normal(p_wrist, p_index_mcp, p_pinky_mcp)
                    
                    if not self.is_calibrated:
                        self.calibration_buffer.append(current_palm_normal)
                        if len(self.calibration_buffer) >= RehabConfig.CALIBRATION_FRAMES_REQUIRED:
                            avg_normal = np.mean(self.calibration_buffer, axis=0)
                            norm = np.linalg.norm(avg_normal)
                            self.baseline_palm_normal = avg_normal / norm if norm > 0 else avg_normal
                            self.is_calibrated = True
                    else:
                        deviation = BiomechanicsMath.calculate_angle_between_vectors(
                            self.baseline_palm_normal, current_palm_normal
                        )
                        is_cheating = (deviation > RehabConfig.MAX_PALM_DEVIATION_DEGREES)

                    # --- RANGE OF MOTION, FILTERING & VISUALIZATION ---
                    should_log = (current_time - last_log_time >= 0.1)
                    for index, joint in enumerate(self.target_joints):
                        p_prox_idx, p_vertex_idx, p_distal_idx = joint.indices
                        p_proximal = landmarks_3d[p_prox_idx]
                        p_vertex = landmarks_3d[p_vertex_idx]
                        p_distal = landmarks_3d[p_distal_idx]
                        
                        raw_angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
                        
                        # Apply 1€ Filter
                        if joint.name not in self.filters:
                            self.filters[joint.name] = OneEuroFilter(current_time, raw_angle)
                        smoothed_angle = self.filters[joint.name].filter(current_time, raw_angle)

                        # Update historical trajectory for oscilloscope
                        self.history[joint.name].append(smoothed_angle)

                        # Update Repetition Counter & Quality
                        rep_counter = self.rep_counters.setdefault(joint.name, RepetitionCounter())
                        reps_done, new_rep_completed = rep_counter.update(smoothed_angle)

                        # Check Isometry
                        iso_state = self.isometry_tracker.setdefault(
                            joint.name, {"target": smoothed_angle, "start": current_time, "held": False}
                        )
                        if abs(smoothed_angle - iso_state["target"]) <= RehabConfig.ISOMETRY_ANGLE_TOLERANCE:
                            if current_time - iso_state["start"] >= RehabConfig.ISOMETRY_HOLD_SECONDS:
                                iso_state["held"] = True
                        else:
                            iso_state["target"] = smoothed_angle
                            iso_state["start"] = current_time
                            iso_state["held"] = False

                        # Draw anatomical biofeedback arc and vectors on the hand
                        joint_color = self.PALETTE[index % len(self.PALETTE)]
                        if landmarks_2d is not None:
                            self._draw_joint_biofeedback(
                                annotated_frame,
                                landmarks_2d[p_prox_idx],
                                landmarks_2d[p_vertex_idx],
                                landmarks_2d[p_distal_idx],
                                smoothed_angle,
                                joint_color,
                                iso_state["held"]
                            )

                        # Logging to CSV session
                        if self.exporter and should_log:
                            detected_hand_label = handedness_info[0] if handedness_info else "Unknown"
                            self.exporter.log_record(
                                elapsed_time_s=elapsed_session,
                                joint_name=joint.name,
                                raw_angle=raw_angle,
                                smoothed_angle=smoothed_angle,
                                deviation=deviation,
                                is_cheating=is_cheating,
                                isometry_held=iso_state["held"],
                                reps_completed=reps_done,
                                handedness=detected_hand_label
                            )

                        # HUD Metric List on Left
                        y_pos = 90 + (index * 42)
                        iso_badge = " [ISO HOLD!]" if iso_state["held"] else ""
                        badge_color = (0, 255, 255) if iso_state["held"] else joint_color
                        reps_badge = f" | Reps: {reps_done}"
                        cv2.putText(annotated_frame, f"{joint.name}: {int(smoothed_angle)} deg{reps_badge}{iso_badge}", 
                                    (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.70, badge_color, 2, cv2.LINE_AA)

                    if should_log:
                        last_log_time = current_time

                # Draw top HUD and bottom-right oscilloscope
                self._draw_hud(annotated_frame, deviation, is_cheating, handedness_info)
                self._draw_oscilloscope_graph(annotated_frame)
                
                cv2.imshow(window_name, annotated_frame)
                
                # --- KEYBOARD CONTROLS ---
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.reset_calibration()

                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        break
                except cv2.error:
                    break

        finally:
            self.stream.stop()
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            self.tracker.close()
            if self.exporter:
                print(f"[INFO] Rehabilitation session saved to: {self.exporter.file_path}")


def run_interactive_wizard() -> List[HandJoint]:
    """Runs the step-by-step console assistant to configure target joints."""
    selected_joints = []
    
    fingers = {
        "1": "THUMB",
        "2": "INDEX",
        "3": "MIDDLE",
        "4": "RING",
        "5": "PINKY"
    }
    
    phalanges = {
        "1": "MCP",
        "2": "PIP",
        "3": "DIP"
    }

    try:
        num_joints = int(input("How many joints do you want to measure simultaneously? (1-3): "))
        num_joints = max(1, min(3, num_joints))
    except ValueError:
        print("[WARNING] Invalid input. Defaulting to 1 joint.")
        num_joints = 1

    for i in range(num_joints):
        print(f"\n--- Configuring Joint {i+1} of {num_joints} ---")
        print("Select Finger:")
        print("1: Thumb   2: Index   3: Middle   4: Ring   5: Pinky")
        f_choice = input("Choice (1-5): ").strip()
        finger_name = fingers.get(f_choice, "PINKY")
        
        print(f"Select Phalanx for {finger_name}:")
        if finger_name == "THUMB":
            print("1: CMC (Base)   2: MCP (Middle)   3: IP (Tip)")
        else:
            print("1: MCP (Base)   2: PIP (Middle)   3: DIP (Tip)")
            
        p_choice = input("Choice (1-3): ").strip()
        phalanx_name = phalanges.get(p_choice, "MCP")
        
        if finger_name == "THUMB":
            if phalanx_name == "MCP": phalanx_name = "CMC"
            elif phalanx_name == "PIP": phalanx_name = "MCP"
            elif phalanx_name == "DIP": phalanx_name = "IP"

        enum_string = f"{finger_name}_{phalanx_name}"
        joint_enum = getattr(HandJoint, enum_string)
        selected_joints.append(joint_enum)
        print(f"[SUCCESS] Added {enum_string} to tracking list.")

    return selected_joints


def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses optional command-line arguments to bypass the interactive wizard."""
    all_joint_names = [j.name for j in HandJoint]

    parser = argparse.ArgumentParser(
        description="Digital Goniometer - Vision-based Range of Motion (ROM) assessment tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python src/main.py\n"
               "  python src/main.py --joints INDEX_PIP\n"
               "  python src/main.py --joints INDEX_MCP MIDDLE_PIP --camera 0 --no-export\n"
    )
    parser.add_argument(
        "-j", "--joints",
        nargs="+",
        metavar="JOINT",
        help=f"Target joint(s) to monitor (up to 3). Choices: {', '.join(all_joint_names)}"
    )
    parser.add_argument(
        "-c", "--camera",
        type=int,
        default=0,
        help="Webcam device index (default: 0)"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Disable automatic CSV rehabilitation session logging"
    )

    return parser.parse_args(args)


def main(cli_args: Optional[List[str]] = None):
    """
    Entry point of the script. Handles user configuration via arguments or interactive CLI wizard.
    """
    print("========================================")
    print("    EDGE AI REHABILITATION GONIOMETER    ")
    print("========================================")
    
    parsed = parse_cli_args(cli_args)
    
    selected_joints: List[HandJoint] = []
    
    if parsed.joints:
        for name in parsed.joints:
            name_upper = name.strip().upper()
            if hasattr(HandJoint, name_upper):
                selected_joints.append(getattr(HandJoint, name_upper))
                print(f"[CLI] Selected joint: {name_upper}")
            else:
                print(f"[WARNING] Unknown joint name '{name}'. Skipping.")
        
        if not selected_joints:
            print("[WARNING] No valid joints provided via arguments. Launching interactive wizard...")
            selected_joints = run_interactive_wizard()
    else:
        selected_joints = run_interactive_wizard()

    export_session = not parsed.no_export
    camera_idx = parsed.camera

    print("\n[INFO] Starting camera...")
    app = GoniometerApp(
        target_joints=selected_joints,
        camera_index=camera_idx,
        export_session=export_session
    )
    app.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
