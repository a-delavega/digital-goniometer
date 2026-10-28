from enum import Enum
from typing import Optional, Tuple, Dict, Any

class RepetitionState(Enum):
    EXTENSION = "EXTENSION"
    FLEXION = "FLEXION"

class RepetitionCounter:
    """
    State machine that tracks clinical flexion/extension repetition cycles for a joint.
    Also assesses repetition quality and fatigue indicators (ROM degradation).
    """
    def __init__(
        self,
        flexion_threshold_deg: float = 105.0,
        extension_threshold_deg: float = 145.0
    ):
        self.flexion_thresh = float(flexion_threshold_deg)
        self.extension_thresh = float(extension_threshold_deg)
        
        self.state = RepetitionState.EXTENSION
        self.rep_count = 0
        self.current_min_angle = 180.0
        self.current_max_angle = 0.0
        
        # History of peak ROM achieved per repetition: [(min_angle, max_angle, rom)]
        self.rep_history = []

    def update(self, angle: float) -> Tuple[int, bool]:
        """
        Processes a new smoothed angle reading.
        
        Returns:
            Tuple[int, bool]: (current_rep_count, is_new_rep_completed)
        """
        new_rep = False

        if self.state == RepetitionState.EXTENSION:
            # While in extension, track how far the joint opens before flexing
            if angle > self.current_max_angle:
                self.current_max_angle = angle

            # Transition to FLEXION when crossing below threshold
            if angle <= self.flexion_thresh:
                self.state = RepetitionState.FLEXION
                self.current_min_angle = angle
                
        elif self.state == RepetitionState.FLEXION:
            # While in flexion, track lowest angle (deepest flexion)
            if angle < self.current_min_angle:
                self.current_min_angle = angle

            # Transition back to EXTENSION when joint opens past threshold
            if angle >= self.extension_thresh:
                self.state = RepetitionState.EXTENSION
                self.rep_count += 1
                new_rep = True
                
                # The rep ends at the maximum angle reached during return
                self.current_max_angle = angle
                rom = self.current_max_angle - self.current_min_angle
                self.rep_history.append({
                    "rep_number": self.rep_count,
                    "min_angle": round(self.current_min_angle, 1),
                    "max_angle": round(self.current_max_angle, 1),
                    "rom_deg": round(rom, 1)
                })
                
                # Reset extremes for next repetition cycle
                self.current_min_angle = angle
                self.current_max_angle = 0.0

        return self.rep_count, new_rep

        return self.rep_count, new_rep

    def get_fatigue_metric(self) -> Optional[float]:
        """
        Calculates ROM drop percentage between first rep and latest rep.
        Returns percentage decrease (e.g., 15.2 for 15.2% loss of motion).
        """
        if len(self.rep_history) < 2:
            return None
        initial_rom = self.rep_history[0]["rom_deg"]
        latest_rom = self.rep_history[-1]["rom_deg"]
        if initial_rom <= 0:
            return 0.0
        drop = ((initial_rom - latest_rom) / initial_rom) * 100.0
        return round(drop, 1)
