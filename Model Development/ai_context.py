def generate_ai_context(events, metrics, score_breakdown):

    event_summary = {
        "high_rpm_events": 0,
        "harsh_throttle_events": 0,
        "hard_braking_events": 0
    }

    for e in events:
        if e["type"] == "high_rpm":
            event_summary["high_rpm_events"] += 1
        elif e["type"] == "harsh_throttle":
            event_summary["harsh_throttle_events"] += 1
        elif e["type"] == "hard_braking":
            event_summary["hard_braking_events"] += 1

    return {
        "event_summary": event_summary,
        "trip_metrics": metrics,
        "score_breakdown": score_breakdown
    }