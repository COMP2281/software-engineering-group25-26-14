import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from model_engine import analyse_trip
from data_pipeline.ingestion.preprocessing import PreprocessingPipeline


def main():

    print("Starting trip analysis...\n")

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir.parent / "data"

    pipeline = PreprocessingPipeline()

    result = pipeline.ingest_path(data_dir)

    print(f"Files processed: {len(result.processed_datasets)}\n")

    for dataset in result.processed_datasets:

        if dataset.validation.status != "accepted":
            print(f"Skipping rejected file: {dataset.validation.filename}")
            continue

        for trip in dataset.trips:

            print(f"Processing trip: {trip.metadata.trip_id}")

            try:
                df = trip.dataframe
                analysis = analyse_trip(df)

                print("Result:", analysis)

            except Exception as e:
                print(f"Error analysing trip {trip.metadata.trip_id}: {e}")

            print("-" * 40)


if __name__ == "__main__":
    main()