import pandas as pd
from typing import Dict, Any, List

from preprocessing import PreprocessingPipeline, BatchProcessingResult


HARSH_ACCEL_THRESHOLD = 3
HARSH_BRAKE_THRESHOLD = -4
OVER_REV_RPM = 4000
THROTTLE_AGGRESSIVE = 80
IDLE_SPEED = 3


def prepare_trip_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    df["time_delta"] = df["Timestamp"].diff().dt.total_seconds().fillna(0)

    speed_mps = df["Speed"] / 3.6
    df["acceleration"] = speed_mps.diff() / df["time_delta"]
    df["acceleration"] = df["acceleration"].fillna(0)

    df["instant_fuel_eff"] = 15.0

    return df


def detect_events(df: pd.DataFrame) -> List[Dict[str, Any]]:

    events = []

    for _, row in df.iterrows():

        if row["acceleration"] > HARSH_ACCEL_THRESHOLD:
            events.append({
                "type": "harsh_acceleration",
                "timestamp": str(row["Timestamp"])
            })

        if row["acceleration"] < HARSH_BRAKE_THRESHOLD:
            events.append({
                "type": "harsh_braking",
                "timestamp": str(row["Timestamp"])
            })

        if row["RPM"] > OVER_REV_RPM:
            events.append({
                "type": "over_revving",
                "timestamp": str(row["Timestamp"])
            })

        if row["Throttle"] > THROTTLE_AGGRESSIVE:
            events.append({
                "type": "aggressive_throttle",
                "timestamp": str(row["Timestamp"])
            })

        if row["Speed"] < IDLE_SPEED and row["RPM"] > 800:
            events.append({
                "type": "idling",
                "timestamp": str(row["Timestamp"])
            })

    return events


def count_events(events: List[Dict[str, Any]]) -> Dict[str, int]:

    counts: Dict[str, int] = {}

    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + 1

    return counts


def compute_trip_metrics(df: pd.DataFrame) -> Dict[str, Any]:

    duration = df["time_delta"].sum()

    distance = (df["Speed"] * df["time_delta"] / 3600).sum()

    avg_speed = df["Speed"].mean()

    avg_rpm = df["RPM"].mean()

    avg_fuel_eff = df["instant_fuel_eff"].mean()

    idle_time = df.loc[df["Speed"] < IDLE_SPEED, "time_delta"].sum()

    return {
        "duration_sec": duration,
        "distance_km": distance,
        "avg_speed": avg_speed,
        "avg_rpm": avg_rpm,
        "avg_fuel_efficiency": avg_fuel_eff,
        "idle_time_sec": idle_time
    }


def compute_efficiency_score(event_counts: Dict[str, int]) -> int:

    score = 100

    score -= event_counts.get("harsh_acceleration", 0) * 3
    score -= event_counts.get("harsh_braking", 0) * 4
    score -= event_counts.get("over_revving", 0) * 2
    score -= event_counts.get("aggressive_throttle", 0) * 1
    score -= event_counts.get("idling", 0) * 0.5

    score = max(0, min(100, score))

    return int(score)


def analyze_trip(df: pd.DataFrame) -> Dict[str, Any]:

    df = prepare_trip_dataframe(df)

    events = detect_events(df)

    event_counts = count_events(events)

    metrics = compute_trip_metrics(df)

    score = compute_efficiency_score(event_counts)

    return {
        "trip_metrics": metrics,
        "events": events,
        "event_counts": event_counts,
        "efficiency_score": score
    }


def analyze_batch(result: BatchProcessingResult):

    analysis_output = []

    for dataset in result.processed_datasets:

        if dataset.validation.status != "accepted":
            continue

        for trip in dataset.trips:

            trip_analysis = analyze_trip(trip.dataframe)

            analysis_output.append({
                "trip_id": trip.metadata.trip_id,
                "vehicle_id": trip.metadata.vehicle_id,
                "vehicle_make": trip.metadata.vehicle_make,
                "vehicle_model": trip.metadata.vehicle_model,
                "analysis": trip_analysis
            })

    return analysis_output