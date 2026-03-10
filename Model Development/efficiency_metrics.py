import numpy as np


def compute_trip_metrics(df):

    metrics = {}

    # Distance travelled (approx if speed exists)
    if "speed" in df.columns:
        metrics["avg_speed"] = df["speed"].mean()
    else:
        metrics["avg_speed"] = 0

    # Average RPM
    if "RPM" in df.columns:
        metrics["avg_rpm"] = df["RPM"].mean()
    else:
        metrics["avg_rpm"] = 0

    # TEMPORARY PLACEHOLDER
    # Replace when InstantFuelEfficiency is added
    metrics["avg_fuel_efficiency"] = 8.5

    return metrics