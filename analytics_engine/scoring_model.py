def compute_efficiency_score(events, metrics):

    counts = {
        "high_rpm": 0,
        "harsh_throttle": 0,
        "hard_braking": 0
    }

    for e in events:
        counts[e["type"]] += 1

    fuel_eff = metrics["average_fuel_efficiency"]

    fuel_score = min(100, int(fuel_eff * 6))

    rpm_score = max(0, 100 - counts["high_rpm"] * 5)

    throttle_score = max(0, 100 - counts["harsh_throttle"] * 5)

    braking_score = max(0, 100 - counts["hard_braking"] * 6)

    breakdown = {
        "fuel_economy": fuel_score,
        "high_rpm": rpm_score,
        "harsh_throttle": throttle_score,
        "hard_braking": braking_score
    }

    final_score = int(sum(breakdown.values()) / len(breakdown))

    return final_score, breakdown