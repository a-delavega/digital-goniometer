import os

class RehabConfig:
    """
    Core configuration and medical thresholds for the application.
    """
    # Biomechanics thresholds
    MAX_PALM_DEVIATION_DEGREES = 15.0
    ISOMETRY_HOLD_SECONDS = 3.0
    
    # Data Export Settings
    # Use absolute paths relative to the project root to avoid folder nesting issues
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    EXPORT_DIR = os.path.join(PROJECT_ROOT, 'exports')
    CSV_PREFIX = "patient_session_"