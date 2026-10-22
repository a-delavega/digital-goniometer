import numpy as np
from typing import Optional

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
        vector1 = p_proximal - p_vertex
        vector2 = p_distal - p_vertex
        
        norm_v1 = np.linalg.norm(vector1)
        norm_v2 = np.linalg.norm(vector2)
        
        # Prevent division by zero if points perfectly overlap (e.g., tracking glitch)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        dot_product = np.dot(vector1, vector2)
        cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
        angle_rad = np.arccos(cos_theta)
        
        return float(np.degrees(angle_rad))
    
    @staticmethod
    def calculate_palm_normal(p_wrist: np.ndarray, p_index_mcp: np.ndarray, p_pinky_mcp: np.ndarray) -> np.ndarray:
        """
        Calculates the normal unit vector perpendicular to the palm plane formed by
        the wrist, index MCP, and pinky MCP.
        """
        v1 = p_index_mcp - p_wrist
        v2 = p_pinky_mcp - p_wrist
        normal = np.cross(v1, v2)
        norm_mag = np.linalg.norm(normal)
        if norm_mag == 0:
            return normal
        return normal / norm_mag

    @staticmethod
    def calculate_angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Calculates the angular deviation in degrees between two 3D vectors.
        """
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        dot_product = np.dot(v1, v2)
        cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_theta)))


class OneEuroFilter:
    """
    1€ Filter: An adaptive low-pass filter with minimal lag and jitter reduction.
    Ideal for real-time human movement & joint angle smoothing.
    """
    def __init__(self, t0: float, x0: float, dx0: float = 0.0, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    @staticmethod
    def _smoothing_factor(t_e: float, cutoff: float) -> float:
        r = 2 * np.pi * cutoff * t_e
        return r / (r + 1)

    @staticmethod
    def _exponential_smoothing(a: float, x: float, x_prev: float) -> float:
        return a * x + (1 - a) * x_prev

    def filter(self, t: float, x: float) -> float:
        t_e = t - self.t_prev
        if t_e <= 0.0:
            return self.x_prev

        # Compute filtered derivative of the signal
        a_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self._exponential_smoothing(a_d, dx, self.dx_prev)

        # Dynamic cutoff frequency based on speed of motion
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._smoothing_factor(t_e, cutoff)
        x_hat = self._exponential_smoothing(a, x, self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat
