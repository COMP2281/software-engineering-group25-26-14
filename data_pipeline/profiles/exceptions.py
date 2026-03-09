"""
Custom exceptions for the Vehicle Profile Calibration module.
"""

class CalibrationDataError(Exception):
    """Raised when the input dataset is missing, empty, or lacks required columns for calibration."""
    pass

class VehicleResolutionError(Exception):
    """Raised when the vehicle specs cannot be resolved from the external API and defaults must be used, or when the API response is invalid."""
    pass
