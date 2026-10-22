import cv2
import sys
import os
import time
import numpy as np
from typing import List, Dict, Optional

# Ensure 'src' is always on sys.path regardless of execution working directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import our custom modules
from biomechanics.joints_map import HandJoint
from biomechanics.math_utils import BiomechanicsMath, OneEuroFilter
from vision.tracker import HandTracker
from vision.stream import VideoStream
from core.config import RehabConfig
from core.session_exporter import SessionExporter


class GoniometerApp:
    """
    Main Orchestrator App.
    Coordinates camera input, AI tracking, biometric math, filtering, session export, and UI rendering.
    """
    
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

    def _draw_hud(self, frame: np.ndarray, deviation: float, is_cheating: bool):
        # Draw top status banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (450, 60), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        if not self.is_calibrated:
            progress = len(self.calibration_buffer)
            total = RehabConfig.CALIBRATION_FRAMES_REQUIRED
            text = f"CALIBRATING POSTURE: {progress}/{total}"
            color = (0, 215, 255) # Yellow/Orange
        elif is_cheating:
            text = f"COMPENSATION ALERT! Rot: {int(deviation)} deg"
            color = (0, 0, 255) # Red
        else:
            text = f"POSTURE OK (Dev: {int(deviation)} deg)"
            color = (0, 255, 0) # Green

        cv2.putText(frame, text, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        cv2.putText(frame, "Keys: [C] Recalibrate | [Q] Quit", (15, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def _draw_joint_arc(self, frame: np.ndarray, vertex_2d: np.ndarray, p1_2d: np.ndarray, p2_2d: np.ndarray, angle: float):
        """Draws visual biofeedback sector/arc on the image."""
        try:
            v_pt = tuple(vertex_2d.astype(int))
            cv2.circle(frame, v_pt, 6, (0, 255, 255), -1)
        except Exception:
            pass

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
                h, w, _ = frame.shape
                current_time = time.time()
                elapsed_session = current_time - self.start_time

                annotated_frame, results = self.tracker.process_frame(frame)
                landmarks_3d = self.tracker.get_world_landmarks(results)
                
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

                    # --- RANGE OF MOTION & FILTERING ---
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

                        # Check Isometry
                        iso_state = self.isometry_tracker.setdefault(joint.name, {"target": smoothed_angle, "start": current_time, "held": False})
                        if abs(smoothed_angle - iso_state["target"]) <= RehabConfig.ISOMETRY_ANGLE_TOLERANCE:
                            if current_time - iso_state["start"] >= RehabConfig.ISOMETRY_HOLD_SECONDS:
                                iso_state["held"] = True
                        else:
                            iso_state["target"] = smoothed_angle
                            iso_state["start"] = current_time
                            iso_state["held"] = False

                        # Logging to CSV session
                        if self.exporter and should_log:
                            self.exporter.log_record(
                                elapsed_time_s=elapsed_session,
                                joint_name=joint.name,
                                raw_angle=raw_angle,
                                smoothed_angle=smoothed_angle,
                                deviation=deviation,
                                is_cheating=is_cheating,
                                isometry_held=iso_state["held"]
                            )

                        # UI Rendering for Joint
                        y_pos = 90 + (index * 42)
                        iso_badge = " [ISO HOLD!]" if iso_state["held"] else ""
                        joint_color = (0, 255, 255) if iso_state["held"] else (255, 255, 255)
                        cv2.putText(annotated_frame, f"{joint.name}: {int(smoothed_angle)} deg{iso_badge}", 
                                    (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.75, joint_color, 2)

                    if should_log:
                        last_log_time = current_time

                self._draw_hud(annotated_frame, deviation, is_cheating)
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


def main():
    """
    Entry point of the script. Handles user configuration via an interactive CLI wizard.
    """
    print("========================================")
    print("    EDGE AI REHABILITATION GONIOMETER    ")
    print("========================================")
    
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

    print("\n[INFO] Starting camera...")
    app = GoniometerApp(target_joints=selected_joints)
    app.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
