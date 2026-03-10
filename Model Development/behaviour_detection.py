from .event_segmentation import segment_event


HIGH_RPM_THRESHOLD = 3000
HARSH_ACCEL_THRESHOLD = 3
HARD_BRAKE_THRESHOLD = -3


def detect_driver_behaviour(df):

    events = []

    events += segment_event(
        df,
        lambda r: r["RPM"] > HIGH_RPM_THRESHOLD,
        "high_rpm"
    )

    events += segment_event(
        df,
        lambda r: r["acceleration"] > HARSH_ACCEL_THRESHOLD,
        "harsh_throttle"
    )

    events += segment_event(
        df,
        lambda r: r["acceleration"] < HARD_BRAKE_THRESHOLD,
        "hard_braking"
    )

    return events