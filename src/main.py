import cv2
import sys
from typing import List

# Import our custom modules
from biomechanics.joints_map import HandJoint
from biomechanics.math_utils import BiomechanicsMath
from vision.tracker import HandTracker
from core.config import RehabConfig  # <-- NUEVO IMPORT

class GoniometerApp:
    """
    Main Orchestrator App.
    Coordinates camera input, AI tracking, biometric math, and UI rendering.
    """
    
    def __init__(self, target_joints: List[HandJoint], camera_index: int = 0):
        self.target_joints = target_joints[:3] 
        self.tracker = HandTracker()
        
        # State variable to store the initial palm posture (calibration)
        self.baseline_palm_normal = None
        
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print("[ERROR] Could not access the webcam. Please check your hardware.")
            sys.exit(1)

    def run(self):
        print(f"\n[INFO] Starting Digital Goniometer for {len(self.target_joints)} joint(s).")
        print("[INFO] Press 'q' on the video window to exit.\n")
        
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)
            annotated_frame, results = self.tracker.process_frame(frame)
            landmarks_3d = self.tracker.get_world_landmarks(results)
            
            if landmarks_3d is not None:
                # --- CHEAT DETECTION LOGIC (Articular Isolation) ---
                # Landmark 0: Wrist, 5: Index Base, 17: Pinky Base
                p_wrist = landmarks_3d[0]
                p_index_mcp = landmarks_3d[5]
                p_pinky_mcp = landmarks_3d[17]
                
                current_palm_normal = BiomechanicsMath.calculate_palm_normal(p_wrist, p_index_mcp, p_pinky_mcp)
                
                # Calibrate baseline if not set
                if self.baseline_palm_normal is None:
                    self.baseline_palm_normal = current_palm_normal
                    cv2.putText(annotated_frame, "CALIBRATING POSTURE...", (20, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                else:
                    # Calculate deviation from baseline
                    deviation = BiomechanicsMath.calculate_angle_between_vectors(
                        self.baseline_palm_normal, current_palm_normal
                    )
                    
                    # Evaluate against medical thresholds
                    if deviation > RehabConfig.MAX_PALM_DEVIATION_DEGREES:
                        warning_text = f"CHEATING! Wrist Rotated: {int(deviation)} deg"
                        cv2.putText(annotated_frame, warning_text, (20, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)  # Red text
                    else:
                        ok_text = f"Posture OK. Deviation: {int(deviation)} deg"
                        cv2.putText(annotated_frame, ok_text, (20, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)  # Green text

                # --- RANGE OF MOTION (ROM) LOGIC ---
                for index, joint in enumerate(self.target_joints):
                    p_prox_idx, p_vertex_idx, p_distal_idx = joint.indices
                    
                    p_proximal = landmarks_3d[p_prox_idx]
                    p_vertex = landmarks_3d[p_vertex_idx]
                    p_distal = landmarks_3d[p_distal_idx]
                    
                    angle = BiomechanicsMath.calculate_3d_angle(p_proximal, p_vertex, p_distal)
                    
                    # Offset Y position so it draws below the cheat detection text
                    y_position = 70 + (index * 40)
                    cv2.putText(annotated_frame, f"{joint.name}: {int(angle)} deg", 
                                (20, y_position), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                # Reset baseline when hand is not on screen
                self.baseline_palm_normal = None

            cv2.imshow('Digital Goniometer - Rehab Edge AI', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


def main():
    """
    Entry point of the script. Handles user configuration via an interactive CLI wizard.
    """
    print("========================================")
    print("   EDGE AI REHABILITATION GONIOMETER    ")
    print("========================================")
    
    selected_joints = []
    
    # Dictionaries to map user inputs to specific strings
    fingers = {
        "1": "THUMB",
        "2": "INDEX",
        "3": "MIDDLE",
        "4": "RING",
        "5": "PINKY"
    }
    
    phalanges = {
        "1": "MCP", # Base knuckle (or CMC for thumb base)
        "2": "PIP", # Middle joint (or MCP for thumb)
        "3": "DIP"  # Tip joint (or IP for thumb)
    }

    # Ask how many joints to analyze
    try:
        num_joints = int(input("How many joints do you want to measure simultaneously? (1-3): "))
        num_joints = max(1, min(3, num_joints)) # Clamp between 1 and 3
    except ValueError:
        print("[WARNING] Invalid input. Defaulting to 1 joint.")
        num_joints = 1

    # Loop to select each joint step by step
    for i in range(num_joints):
        print(f"\n--- Configuring Joint {i+1} of {num_joints} ---")
        
        # STEP 1: Select Finger
        print("Select Finger:")
        print("1: Thumb   2: Index   3: Middle   4: Ring   5: Pinky")
        f_choice = input("Choice (1-5): ").strip()
        finger_name = fingers.get(f_choice, "PINKY") # Default to Pinky if invalid
        
        # STEP 2: Select Phalanx
        print(f"Select Phalanx for {finger_name}:")
        if finger_name == "THUMB":
            print("1: CMC (Base)   2: MCP (Middle)   3: IP (Tip)")
        else:
            print("1: MCP (Base)   2: PIP (Middle)   3: DIP (Tip)")
            
        p_choice = input("Choice (1-3): ").strip()
        phalanx_name = phalanges.get(p_choice, "MCP")
        
        # Special case for Thumb terminology mapping
        if finger_name == "THUMB":
            if phalanx_name == "MCP": phalanx_name = "CMC"
            elif phalanx_name == "PIP": phalanx_name = "MCP"
            elif phalanx_name == "DIP": phalanx_name = "IP"

        # Combine both strings to match the Enum name (e.g., "PINKY_MCP")
        enum_string = f"{finger_name}_{phalanx_name}"
        
        # Fetch the actual Enum object dynamically
        joint_enum = getattr(HandJoint, enum_string)
        selected_joints.append(joint_enum)
        print(f"[SUCCESS] Added {enum_string} to tracking list.")

    print("\n[INFO] Starting camera...")
    app = GoniometerApp(target_joints=selected_joints)
    app.run()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()