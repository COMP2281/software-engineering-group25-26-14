def compute_trip_metrics(df):

    metrics = {}

    if "Speed" in df.columns:
        metrics["average_speed"] = float(df["Speed"].mean(skipna=True))
    else:
        metrics["average_speed"] = 0

    if "RPM" in df.columns:
        metrics["average_rpm"] = float(df["RPM"].mean(skipna=True))
    else:
        metrics["average_rpm"] = 0

    # Placeholder until real fuel model exists
    metrics["average_fuel_efficiency"] = 8.5

    return metrics