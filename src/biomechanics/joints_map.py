from enum import Enum
from typing import Tuple

class HandJoint(Enum):
    """
    Defines the anatomical mapping of hand joints using 3D landmarks (0-20).
    Structure: (Proximal_Point, Articular_Vertex, Distal_Point)
    """
    
    # --- INDEX FINGER ---
    INDEX_MCP = (0, 5, 6)   # Metacarpophalangeal (Base): Wrist -> Knuckle -> PIP
    INDEX_PIP = (5, 6, 7)   # Proximal Interphalangeal: Knuckle -> PIP -> DIP
    INDEX_DIP = (6, 7, 8)   # Distal Interphalangeal: PIP -> DIP -> Fingertip
    
    # --- MIDDLE FINGER ---
    MIDDLE_MCP = (0, 9, 10)
    MIDDLE_PIP = (9, 10, 11)
    
    # --- PINKY FINGER ---
    PINKY_MCP = (0, 17, 18)
    PINKY_PIP = (17, 18, 19)
    PINKY_DIP = (18, 19, 20)
    
    # --- THUMB ---
    THUMB_CMC = (0, 1, 2)   # Carpometacarpal
    THUMB_MCP = (1, 2, 3)
    THUMB_IP = (2, 3, 4)

    @property
    def indices(self) -> Tuple[int, int, int]:
        """
        Returns the tuple of indices to extract coordinates from the 3D array.
        
        Returns:
            Tuple[int, int, int]: (proximal_idx, vertex_idx, distal_idx)
        """
        return self.value