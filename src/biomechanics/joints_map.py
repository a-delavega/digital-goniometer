from enum import Enum
from typing import Tuple

class HandJoint(Enum):
    """
    Defines the anatomical mapping of all hand joints using 3D landmarks (0-20).
    Structure: (Proximal_Point, Articular_Vertex, Distal_Point)
    """
    
    # --- THUMB ---
    THUMB_CMC = (0, 1, 2)
    THUMB_MCP = (1, 2, 3)
    THUMB_IP  = (2, 3, 4)

    # --- INDEX ---
    INDEX_MCP = (0, 5, 6)
    INDEX_PIP = (5, 6, 7)
    INDEX_DIP = (6, 7, 8)
    
    # --- MIDDLE ---
    MIDDLE_MCP = (0, 9, 10)
    MIDDLE_PIP = (9, 10, 11)
    MIDDLE_DIP = (10, 11, 12)
    
    # --- RING ---
    RING_MCP = (0, 13, 14)
    RING_PIP = (13, 14, 15)
    RING_DIP = (14, 15, 16)
    
    # --- PINKY ---
    PINKY_MCP = (0, 17, 18)
    PINKY_PIP = (17, 18, 19)
    PINKY_DIP = (18, 19, 20)

    @property
    def indices(self) -> Tuple[int, int, int]:
        return self.value