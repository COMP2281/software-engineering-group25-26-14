import pandas as pd
import numpy as np
from typing import Dict, Any, List

from preprocessing import PreprocessingPipeline, BatchProcessingResult


# -------------------------
# CONFIGURATION
# -------------------------

HARSH_ACCEL = 2.5
HARSH_BRAKE = -3.5
OVER_REV_RPM = 4000
THROTTLE_AGGRESSIVE = 80
IDLE_SPEED = 3

ROLLING_WINDOW = 5
BASE_FUEL_EFF = 15.0


# -------------------------
# DATA PREPARATION
# -------------------------

def prepare_trip_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    df["time_delta"] = df["Timestamp"].diff().dt.total_seconds().fillna(0)

    speed_mps = df["Speed"] / 3.6

    df["accel_raw"] = speed_mps.diff() / df["time_delta"]
    df["accel_raw"] = df["accel_raw"].replace([np.inf, -np.inf], 0).fillna(0)

    # rolling window acceleration smoothing
    df["acceleration"] = (
        df["accel_raw"]
        .rolling(ROLLING_WINDOW, center=True)
        .mean()
        .fillna(0)
    )

    df["instant_fuel_eff"] = BASE_FUEL_EFF

    return df


# -------------------------
# RPM-SPEED EFFICIENCY MODEL
# -------------------------

def rpm_speed_efficiency(speed: float, rpm: float) -> float:

    if speed < 5:
        return 1.0

    ideal_rpm = 1200 + speed * 35

    deviation = abs(rpm - ideal_rpm)

    efficiency = max(0, 1 - deviation / 4000)

    return efficiency


# -------------------------
# EVENT DETECTION
# -------------------------

def detect_events(df: pd.DataFrame) -> List[Dict[str, Any]]:

    events = []

    for _, row in df.iterrows():

        fuel_waste = 0

        if row["acceleration"] > HARSH_ACCEL:
            fuel_waste = 0.03
            events.append({
                "type": "harsh_acceleration",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": fuel_waste
            })

        if row["acceleration"] < HARSH_BRAKE:
            fuel_waste = 0.02
            events.append({
                "type": "harsh_braking",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": fuel_waste
            })

        if row["RPM"] > OVER_REV_RPM:
            fuel_waste = 0.01
            events.append({
                "type": "over_revving",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": fuel_waste
            })

        if row["Throttle"] > THROTTLE_AGGRESSIVE:
            fuel_waste = 0.015
            events.append({
                "type": "aggressive_throttle",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": fuel_waste
            })

        if row["Speed"] < IDLE_SPEED and row["RPM"] > 800:
            fuel_waste = row["time_delta"] * 0.0003
            events.append({
                "type": "idling",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": fuel_waste
            })

        efficiency = rpm_speed_efficiency(row["Speed"], row["RPM"])

        if efficiency < 0.4 and row["Speed"] > 20:
            events.append({
                "type": "inefficient_gear_usage",
                "timestamp": str(row["Timestamp"]),
                "fuel_waste_l": 0.02
            })

    return events


# -------------------------
# EVENT COUNTING
# -------------------------

def count_events(events: List[Dict[str, Any]]) -> Dict[str, int]:

    counts: Dict[str, int] = {}

    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + 1

    return counts


# -------------------------
# FUEL WASTE ESTIMATION
# -------------------------

def estimate_fuel_waste(events: List[Dict[str, Any]]) -> float:

    waste = 0

    for e in events:
        waste += e.get("fuel_waste_l", 0)

    return waste


# -------------------------
# TRIP METRICS
# -------------------------

def compute_trip_metrics(df: pd.DataFrame) -> Dict[str, Any]:

    duration = df["time_delta"].sum()

    distance = (df["Speed"] * df["time_delta"] / 3600).sum()

    avg_speed = df["Speed"].mean()

    avg_rpm = df["RPM"].mean()

    idle_time = df.loc[df["Speed"] < IDLE_SPEED, "time_delta"].sum()

    avg_fuel_eff = df["instant_fuel_eff"].mean()

    return {
        "duration_sec": duration,
        "distance_km": distance,
        "avg_speed": avg_speed,
        "avg_rpm": avg_rpm,
        "idle_time_sec": idle_time,
        "avg_fuel_efficiency": avg_fuel_eff
    }


# -------------------------
# EFFICIENCY SCORE
# -------------------------

def compute_efficiency_score(counts: Dict[str, int]) -> int:

    score = 100

    score -= counts.get("harsh_acceleration", 0) * 3
    score -= counts.get("harsh_braking", 0) * 4
    score -= counts.get("over_revving", 0) * 2
    score -= counts.get("aggressive_throttle", 0) * 1
    score -= counts.get("idling", 0) * 0.5
    score -= counts.get("inefficient_gear_usage", 0) * 1

    score = max(0, min(100, score))

    return int(score)


# -------------------------
# ECO DRIVING CLASSIFICATION
# -------------------------

def classify_driver(score: int) -> str:

    if score >= 85:
        return "eco"

    if score >= 65:
        return "normal"

    return "aggressive"


# -------------------------
# TRIP ANALYSIS
# -------------------------

def analyze_trip(df: pd.DataFrame) -> Dict[str, Any]:

    df = prepare_trip_dataframe(df)

    events = detect_events(df)

    counts = count_events(events)

    metrics = compute_trip_metrics(df)

    fuel_waste = estimate_fuel_waste(events)

    score = compute_efficiency_score(counts)

    driver_type = classify_driver(score)

    return {

        "trip_metrics": metrics,

        "event_counts": counts,

        "events": events,

        "fuel_waste_liters": fuel_waste,

        "efficiency_score": score,

        "driver_classification": driver_type
    }


# -------------------------
# BATCH ANALYSIS
# -------------------------

def analyze_batch(result: BatchProcessingResult):

    output = []

    for dataset in result.processed_datasets:

        if dataset.validation.status != "accepted":
            continue

        for trip in dataset.trips:

            analysis = analyze_trip(trip.dataframe)

            output.append({
                "trip_id": trip.metadata.trip_id,
                "vehicle_id": trip.metadata.vehicle_id,
                "vehicle_make": trip.metadata.vehicle_make,
                "vehicle_model": trip.metadata.vehicle_model,
                "analysis": analysis
            })

    return output