import pandas as pd
from model_engine import analyse_trip


def prepare_dataframe(df):
    """
    Prepares the dataframe so the behaviour model can run.
    Adds acceleration and other derived values.
    """

    # convert timestamps
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # convert speed to meters per second
    df["speed_mps"] = df["Speed"] / 3.6

    # calculate time difference
    df["time_diff"] = df["Timestamp"].diff().dt.total_seconds()

    # calculate speed difference
    df["speed_diff"] = df["speed_mps"].diff()

    # calculate acceleration
    df["acceleration"] = df["speed_diff"] / df["time_diff"]

    return df


def main():

    # path to your test dataset
    csv_path = "../data/2018-02-28_Seat_Leon_S_RT_Normal.csv"

    print("Loading dataset...")

    df = pd.read_csv(csv_path)

    print("Preparing dataframe...")

    df = prepare_dataframe(df)

    print("Running model...")

    result = analyse_trip(df)

    print("\n==============================")
    print("MODEL RESULTS")
    print("==============================\n")

    print("Efficiency Score:")
    print(result["efficiency_score"])

    print("\nScore Breakdown:")
    print(result["score_breakdown"])

    print("\nTrip Metrics:")
    print(result["trip_metrics"])

    print("\nNumber of Events Detected:")
    print(len(result["events"]))

    print("\nFirst 5 Events:")
    print(result["events"][:5])

    print("\nAI Context (for Granite AI):")
    print(result["ai_context"])

    print("\nModel run completed successfully.")


if __name__ == "__main__":
    main()