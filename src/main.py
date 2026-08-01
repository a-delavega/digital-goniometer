import cv2
import sys
from typing import List

# Import our custom modules
from biomechanics.joints_map import HandJoint
from biomechanics.math_utils import BiomechanicsMath
from vision.tracker import HandTracker

class GoniometerApp:
    """
    Main Orchestrator App.
    Coordinates camera input, AI tracking, biometric math, and UI rendering.
    """
    
    def __init__(self, target_joints: List[HandJoint], camera_index: int = 0):
        """
        Initializes the application.
        
        Args:
            target_joints (List[HandJoint]): A list of up to 3 joints to measure simultaneously.
            camera_index (int): The ID of the webcam (0 is usually the default laptop camera).
        """
        # Enforce the maximum limit of 3 joints for UI and performance reasons
        self.target_joints = target_joints[:3] 
        self.tracker = HandTracker()
        
        # Initialize OpenCV video capture
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print("[ERROR] Could not access the webcam. Please check your hardware.")
            sys.exit(1)

    def run(self):
        """
        Starts the main processing loop.
        """
        print(f"\n[INFO] Starting Digital Goniometer for {len(self.target_joints)} joint(s).")
        print("[INFO] Press 'q' on the video window to exit.\n")
        
        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                print("[WARNING] Ignoring empty camera frame.")
                continue

            # 1. Flip the frame horizontally for a natural 'mirror' effect (UX for patients)
            frame = cv2.flip(frame, 1)
            
            # 2. Vision Layer: Get annotated frame and raw landmarks
            annotated_frame, results = self.tracker.process_frame(frame)
            landmarks_3d = self.tracker.get_world_landmarks(results)
            
            # 3. Biomechanics Layer: Calculate angles if a hand is detected
            if landmarks_3d is not None:
                # Iterate over the selected joints dynamically
                for index, joint in enumerate(self.target_joints):
                    # Extract the specific 3D indices for this joint
                    p_prox_idx, p_vertex_idx, p_distal_idx = joint.indices
                    
                    p_proximal = landmarks_3d[p_prox_idx]
                    p_vertex = landmarks_3d[p_vertex_idx]
                    p_distal = landmarks_3d[p_distal_idx]
                    
                    # Compute the true 3D spatial angle
                    angle = BiomechanicsMath.calculate_3d_angle(
                        p_proximal, p_vertex, p_distal
                    )
                    
                    # 4. Telemetry UI: Draw text on screen
                    # Dynamically offset the Y position based on the index to avoid overlapping
                    y_position = 40 + (index * 40)
                    text = f"{joint.name}: {int(angle)} deg"
                    
                    cv2.putText(
                        annotated_frame, 
                        text, 
                        (20, y_position), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        1, 
                        (0, 255, 0), # Green color (BGR)
                        2, 
                        cv2.LINE_AA
                    )

            # Render the final composite frame
            cv2.imshow('Digital Goniometer - Rehab Edge AI', annotated_frame)

            # Exit condition (wait 1ms for key press)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Cleanup hardware resources
        self.cap.release()
        cv2.destroyAllWindows()


def main():
    """
    Entry point of the script. Handles user configuration via console.
    """
    print("========================================")
    print("   EDGE AI REHABILITATION GONIOMETER    ")
    print("========================================")
    print("Available Joints for Analysis:")
    print("1: PINKY_MCP (Base of pinky)")
    print("2: PINKY_PIP (Middle of pinky)")
    print("3: INDEX_MCP (Base of index)")
    print("4: INDEX_PIP (Middle of index)")
    print("5: THUMB_MCP (Base of thumb)")
    print("----------------------------------------")
    
    # Simple mapping dictionary
    joint_map = {
        "1": HandJoint.PINKY_MCP,
        "2": HandJoint.PINKY_PIP,
        "3": HandJoint.INDEX_MCP,
        "4": HandJoint.INDEX_PIP,
        "5": HandJoint.THUMB_MCP
    }
    
    # Prompt user for up to 3 joints
    user_input = input("Enter up to 3 joint numbers separated by commas (e.g. 1,2): ")
    
    selected_joints = []
    # Split input string by comma, strip whitespaces, and map to Enum
    for choice in user_input.split(','):
        clean_choice = choice.strip()
        if clean_choice in joint_map:
            selected_joints.append(joint_map[clean_choice])
            
    # Fallback if user enters garbage or nothing
    if not selected_joints:
        print("[WARNING] Invalid selection. Defaulting to PINKY_MCP.")
        selected_joints = [HandJoint.PINKY_MCP]
        
    # Enforce maximum 3 joints rule before initializing the app
    if len(selected_joints) > 3:
        print("[WARNING] More than 3 joints selected. Only the first 3 will be analyzed.")
        selected_joints = selected_joints[:3]
        
    # Instantiate and run the app
    app = GoniometerApp(target_joints=selected_joints)
    app.run()


if __name__ == "__main__":
    main()