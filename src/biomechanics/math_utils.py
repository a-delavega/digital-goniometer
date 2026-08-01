import numpy as np

class BiomechanicsMath:
    """
    Pure business logic layer: Vector calculations and biometric formulas.
    Completely agnostic to the vision framework (MediaPipe/OpenCV).
    """
    
    @staticmethod
    def calculate_3d_angle(p_proximal: np.ndarray, p_vertex: np.ndarray, p_distal: np.ndarray) -> float:
        """
        Calculates the 3D spatial angle at the vertex formed by three points.
        
        Args:
            p_proximal (np.ndarray): [x, y, z] coordinate of the anchor point closest to the body.
            p_vertex (np.ndarray): [x, y, z] coordinate of the joint being measured.
            p_distal (np.ndarray): [x, y, z] coordinate of the bone moving away from the body.
            
        Returns:
            float: The flexion angle in degrees (0.0 to 180.0).
        """
        # 1. Create vectors originating from the vertex
        vector1 = p_proximal - p_vertex
        vector2 = p_distal - p_vertex
        
        # 2. Calculate the magnitudes (norms) of the vectors
        norm_v1 = np.linalg.norm(vector1)
        norm_v2 = np.linalg.norm(vector2)
        
        # Prevent division by zero if points perfectly overlap (e.g., tracking glitch)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        # 3. Compute the dot product
        dot_product = np.dot(vector1, vector2)
        
        # 4. Calculate the cosine of the angle
        # np.clip prevents floating-point inaccuracies that push the value slightly 
        # outside the valid [-1.0, 1.0] range for arccos.
        cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
        
        # 5. Convert from radians to degrees
        angle_rad = np.arccos(cos_theta)
        
        return float(np.degrees(angle_rad))