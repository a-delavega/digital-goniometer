import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional, Any

class HandTracker:
    """
    Vision layer: Encapsulates MediaPipe framework and frame processing.
    Acts as an adapter to decouple the AI inference from the main application.
    """
    
    def __init__(self, min_det_conf: float = 0.7, min_track_conf: float = 0.7):
        """
        Initializes the MediaPipe Hands model.
        
        Args:
            min_det_conf (float): Minimum confidence value (0.0 - 1.0) for hand detection.
            min_track_conf (float): Minimum confidence value (0.0 - 1.0) for landmark tracking.
        """
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        
        # We limit max_num_hands=1 to focus solely on the rehabilitation patient's hand
        # and significantly reduce computational load for Edge AI (ESP32 / Raspberry Pi).
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=min_det_conf,
            min_tracking_confidence=min_track_conf
        )
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Any]:
        """
        Performs AI inference on a single frame and renders the 2D skeleton cosmetically.
        
        Args:
            frame (np.ndarray): The raw BGR frame from OpenCV.
            
        Returns:
            Tuple[np.ndarray, Any]: The annotated BGR frame and the raw MediaPipe results.
        """
        # OpenCV uses BGR by default, but MediaPipe requires RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Performance optimization: pass by reference
        frame_rgb.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True
        
        # Convert back to BGR for OpenCV rendering
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        # Cosmetic rendering of the 2D landmarks for user feedback
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame_bgr, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS
                )
                    
        return frame_bgr, results
        
    def get_world_landmarks(self, results: Any) -> Optional[np.ndarray]:
        """
        Extracts the 3D real-world coordinates (in meters) from the AI prediction.
        The origin (0,0,0) is located at the wrist (landmark 0).
        
        Args:
            results (Any): Raw output from MediaPipe process().
            
        Returns:
            Optional[np.ndarray]: A (21, 3) NumPy matrix containing [x, y, z] for each landmark.
                                  Returns None if no hand is detected.
        """
        if not results.multi_hand_world_landmarks:
            return None
            
        # Extract the first hand detected (since max_num_hands=1)
        landmarks = results.multi_hand_world_landmarks[0].landmark
        
        # Convert to a highly optimized NumPy array for vector math
        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
        
        return coords
    
    def close(self):
        """
        Releases MediaPipe resources and background threads.
        Critical to prevent the terminal from hanging on exit.
        """
        self.hands.close()