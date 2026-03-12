import os
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from model_engine import analyse_trip
from data_pipeline.ingestion.preprocessing import PreprocessingPipeline


def main():

    print("Starting trip analysis...\n")

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir.parent / "data_samples" / "10.35097-1130"/ "data" / "dataset" / "OBD-II-Dataset"

    pipeline = PreprocessingPipeline()

    result = pipeline.ingest_path(data_dir)

    print(f"Files processed: {len(result.processed_datasets)}\n")

    printed_schema = False

    for dataset in result.processed_datasets:

        if dataset.validation.status != "accepted":
            print(f"Skipping rejected file: {dataset.validation.filename}")
            continue

        for trip in dataset.trips:

            print(f"Processing trip: {trip.metadata.trip_id}")

            try:
                df = trip.dataframe

                if "Timestamp" in df.columns:
                    df["Timestamp"] = pd.to_datetime(
                        df["Timestamp"], format="%H:%M:%S.%f", errors="coerce"
                    ).astype("datetime64[ns]")

                if not printed_schema:

                    print("\nColumns:")
                    for col in df.columns:
                        print(f" - {col}")

                    print("\nColumn types:")
                    print(df.dtypes)

                    print("\nFirst 5 rows:")
                    print(df.head())

                    print("\n" + "=" * 60 + "\n")

                    printed_schema = True

                analysis = analyse_trip(df)

                print("Result:", analysis)

            except Exception as e:
                print(f"Error analysing trip {trip.metadata.trip_id}: {e}")

            print("-" * 40)


if __name__ == "__main__":
    main()