import os

class RehabConfig:
    """
    Core configuration and medical thresholds for the application.
    """
    # Biomechanics thresholds
    MAX_PALM_DEVIATION_DEGREES = 15.0
    ISOMETRY_HOLD_SECONDS = 3.0
    ISOMETRY_ANGLE_TOLERANCE = 3.0  # Angle variance (deg) to qualify as holding isometry
    
    # Calibration settings
    CALIBRATION_FRAMES_REQUIRED = 30  # Number of stable frames needed for posture baseline
    
    # Data Export Settings
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    EXPORT_DIR = os.path.join(PROJECT_ROOT, 'exports')
    CSV_PREFIX = "patient_session_"
