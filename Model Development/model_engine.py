from .behaviour_detection import detect_driver_behaviour
from .scoring_model import compute_efficiency_score
from .efficiency_metrics import compute_trip_metrics
from .ai_context import generate_ai_context


def analyse_trip(df):

    behaviour_events = detect_driver_behaviour(df)

    trip_metrics = compute_trip_metrics(df)

    score, score_breakdown = compute_efficiency_score(
        behaviour_events,
        trip_metrics
    )

    ai_context = generate_ai_context(
        behaviour_events,
        trip_metrics,
        score_breakdown
    )

    return {
        "events": behaviour_events,
        "trip_metrics": trip_metrics,
        "efficiency_score": score,
        "score_breakdown": score_breakdown,
        "ai_context": ai_context
    }