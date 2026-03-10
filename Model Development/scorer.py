import pandas as pd
import numpy as np


def prepare_trip_metrics(df):

    df = df.copy()

    df["Time"] = pd.to_datetime(df["Time"])

    df["time_diff"] = df["Time"].diff().dt.total_seconds().fillna(0)

    speed_mps = df["Vehicle Speed Sensor [km/h]"] / 3.6

    df["acceleration"] = speed_mps.diff() / df["time_diff"]
    df["acceleration"] = df["acceleration"].fillna(0)

    return df


def detect_behaviours(df):

    events = []

    for i, row in df.iterrows():

        if row["acceleration"] > 3:
            events.append(("Harsh Acceleration", row["Time"]))

        if row["acceleration"] < -4:
            events.append(("Harsh Braking", row["Time"]))

        if row["Engine RPM [RPM]"] > 4000:
            events.append(("Over Revving", row["Time"]))

        if row["Absolute Throttle Position [%]"] > 80:
            events.append(("Aggressive Throttle", row["Time"]))

        if (
            row["Vehicle Speed Sensor [km/h]"] < 30
            and row["Engine RPM [RPM]"] > 2500
        ):
            events.append(("Inefficient Cruise", row["Time"]))

        if (
            row["Vehicle Speed Sensor [km/h]"] < 3
            and row["Engine RPM [RPM]"] > 800
        ):
            events.append(("Idle", row["Time"]))

    return events


def count_events(events):

    counts = {}

    for e, _ in events:
        counts[e] = counts.get(e, 0) + 1

    return counts


def compute_trip_summary(df):

    duration = df["time_diff"].sum()

    avg_speed = df["Vehicle Speed Sensor [km/h]"].mean()

    avg_rpm = df["Engine RPM [RPM]"].mean()

    distance = (df["Vehicle Speed Sensor [km/h]"] * df["time_diff"] / 3600).sum()

    avg_fe = df["Instantaneous Fuel Efficiency"].mean()

    return {
        "duration_sec": duration,
        "distance_km": distance,
        "avg_speed": avg_speed,
        "avg_rpm": avg_rpm,
        "avg_fuel_efficiency": avg_fe
    }


def compute_efficiency_score(event_counts):

    score = 100

    score -= event_counts.get("Harsh Acceleration", 0) * 3
    score -= event_counts.get("Harsh Braking", 0) * 4
    score -= event_counts.get("Over Revving", 0) * 2
    score -= event_counts.get("Aggressive Throttle", 0) * 1
    score -= event_counts.get("Idle", 0) * 0.5

    return max(0, min(100, score))


def analyze_trip(df):

    df = prepare_trip_metrics(df)

    events = detect_behaviours(df)

    counts = count_events(events)

    summary = compute_trip_summary(df)

    score = compute_efficiency_score(counts)

    return {
        "trip_summary": summary,
        "events": events,
        "event_counts": counts,
        "efficiency_score": score
    }