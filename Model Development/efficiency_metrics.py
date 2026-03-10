import numpy as np


def compute_trip_metrics(df):

    avg_fuel_eff = df["InstantFuelEfficiency"].mean()

    speed_mean = df["Speed"].mean()

    distance_km = (df["Speed"] / 3.6 * df["Timestamp"].diff().dt.total_seconds()).sum() / 1000

    return {
        "average_fuel_efficiency": avg_fuel_eff,
        "average_speed": speed_mean,
        "distance_km": distance_km
    }