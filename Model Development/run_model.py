import os
import pandas as pd
from model_engine import analyse_trip


def main():

    print("Starting trip analysis...\n")

    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to data folder
    data_dir = os.path.join(base_dir, "..", "data")

    if not os.path.exists(data_dir):
        print("ERROR: Data folder not found:", data_dir)
        return

    # Get all CSV files
    trip_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]

    if not trip_files:
        print("No CSV trip files found in:", data_dir)
        return

    print(f"Found {len(trip_files)} trip files\n")

    for file in trip_files:

        csv_path = os.path.join(data_dir, file)

        print(f"Processing trip: {file}")

        try:
            df = pd.read_csv(csv_path)

            result = analyse_trip(df)

            print("Result:", result)

        except Exception as e:
            print(f"Error processing {file}: {e}")

        print("-" * 40)


if __name__ == "__main__":
    main()