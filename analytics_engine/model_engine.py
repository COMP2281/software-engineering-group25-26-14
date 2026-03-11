import pandas as pd
from efficiency_metrics import compute_trip_metrics

HIGH_RPM_THRESHOLD = 3000
HARSH_THROTTLE_RATE = 80
MIN_PEDAL_CHANGE = 15
HARD_BRAKE_DECEL = -2.5


def parse_timestamp(series):
    return pd.to_datetime(series, errors="coerce")


def analyse_trip(df: pd.DataFrame):

    df = df.copy()

    # initialise events FIRST
    events = []

    # -------------------------
    # TIMESTAMP CLEANING
    # -------------------------

    df["Timestamp"] = parse_timestamp(df["Timestamp"])
    df = df.dropna(subset=["Timestamp"])

    if df.empty:
        return empty_result()

    df = df.sort_values("Timestamp")

    # -------------------------
    # NUMERIC CLEANING
    # -------------------------

    df["RPM"] = pd.to_numeric(df["RPM"], errors="coerce")
    df["Speed"] = pd.to_numeric(df["Speed"], errors="coerce")
    df["Accelerator Pedal Position D [%]"] = pd.to_numeric(
        df["Accelerator Pedal Position D [%]"], errors="coerce"
    )

    # -------------------------
    # TIME DELTA
    # -------------------------

    df["time_delta"] = df["Timestamp"].diff().dt.total_seconds()
    df = df[df["time_delta"] > 0]

    # -------------------------
    # HIGH RPM EVENTS
    # -------------------------

    df["high_rpm_flag"] = df["RPM"] > HIGH_RPM_THRESHOLD

    high_rpm_groups = (df["high_rpm_flag"] != df["high_rpm_flag"].shift()).cumsum()

    for _, group in df[df["high_rpm_flag"]].groupby(high_rpm_groups):

        start_time = group["Timestamp"].iloc[0]
        end_time = group["Timestamp"].iloc[-1]

        duration = (end_time - start_time).total_seconds()

        # ignore tiny spikes
        if duration > 0.5:

            events.append({
                "type": "high_rpm",
                "timestamp": str(start_time),
                "duration": round(duration, 2)
            })

    # -------------------------
    # HARSH THROTTLE
    # -------------------------

    df["pedal_delta"] = df["Accelerator Pedal Position D [%]"].diff()
    df["pedal_rate"] = df["pedal_delta"] / df["time_delta"]

    df["harsh_throttle_flag"] = (
        (df["pedal_rate"] > HARSH_THROTTLE_RATE)
        | (df["pedal_delta"] > MIN_PEDAL_CHANGE)
    )

    # group continuous throttle bursts
    throttle_groups = (
        df["harsh_throttle_flag"] != df["harsh_throttle_flag"].shift()
    ).cumsum()

    for _, group in df[df["harsh_throttle_flag"]].groupby(throttle_groups):

        start_time = group["Timestamp"].iloc[0]
        end_time = group["Timestamp"].iloc[-1]

        duration = (end_time - start_time).total_seconds()

        # ignore micro spikes
        if duration > 0.3:

            events.append({
                "type": "harsh_throttle",
                "timestamp": str(start_time),
                "duration": round(duration, 2)
            })

    # -------------------------
    # HARD BRAKING
    # -------------------------

    # convert speed to m/s
    df["speed_mps"] = df["Speed"] / 3.6

    # compute acceleration
    df["speed_delta"] = df["speed_mps"].diff()
    df["acceleration"] = df["speed_delta"] / df["time_delta"]

    df["hard_brake_flag"] = df["acceleration"] < HARD_BRAKE_DECEL

    # group continuous braking segments
    brake_groups = (df["hard_brake_flag"] != df["hard_brake_flag"].shift()).cumsum()

    for _, group in df[df["hard_brake_flag"]].groupby(brake_groups):

        start_time = group["Timestamp"].iloc[0]
        end_time = group["Timestamp"].iloc[-1]

        duration = (end_time - start_time).total_seconds()

        # ignore tiny spikes
        if duration > 0.5:

            events.append({
                "type": "hard_braking",
                "timestamp": str(start_time),
                "duration": round(duration, 2)
            })

    # -------------------------
    # METRICS
    # -------------------------

    trip_metrics = compute_trip_metrics(df)

    avg_fuel_efficiency = trip_metrics["average_fuel_efficiency"]

    # -------------------------
    # EVENT COUNTS
    # -------------------------

    high_rpm_count = len([e for e in events if e["type"] == "high_rpm"])
    harsh_throttle_count = len([e for e in events if e["type"] == "harsh_throttle"])
    hard_brake_count = len([e for e in events if e["type"] == "hard_braking"])

    # -------------------------
    # SCORING
    # -------------------------

    fuel_score = max(0, 100 - avg_fuel_efficiency * 5)
    rpm_score = max(0, 100 - high_rpm_count * 5)
    throttle_score = max(0, 100 - harsh_throttle_count * 2)
    braking_score = max(0, 100 - hard_brake_count * 3)

    efficiency_score = int(
        (fuel_score + rpm_score + throttle_score + braking_score) / 4
    )

    score_breakdown = {
        "fuel_economy": int(fuel_score),
        "high_rpm": int(rpm_score),
        "harsh_throttle": int(throttle_score),
        "hard_braking": int(braking_score)
    }

    ai_context = {
        "event_summary": {
            "high_rpm_events": high_rpm_count,
            "harsh_throttle_events": harsh_throttle_count,
            "hard_braking_events": hard_brake_count
        },
        "trip_metrics": trip_metrics,
        "score_breakdown": score_breakdown
    }

    return {
        "events": events,
        "trip_metrics": trip_metrics,
        "efficiency_score": efficiency_score,
        "score_breakdown": score_breakdown,
        "ai_context": ai_context
    }


def empty_result():

    return {
        "events": [],
        "trip_metrics": {
            "average_speed": 0,
            "average_rpm": 0,
            "average_fuel_efficiency": 8.5
        },
        "efficiency_score": 0,
        "score_breakdown": {
            "fuel_economy": 0,
            "high_rpm": 0,
            "harsh_throttle": 0,
            "hard_braking": 0
        },
        "ai_context": {}
    }