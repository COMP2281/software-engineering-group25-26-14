import pandas as pd
import glob
import os

print(f"Current working directory: {os.getcwd()}")

# Path to your dataset folder
DATA_PATH = "10.35097-1130/10.35097-1130/data/dataset/OBD-II-Dataset/OBD-II-Dataset/*.csv"
print(f"Looking for files at: {DATA_PATH}")
print(f"Files found: {len(glob.glob(DATA_PATH))}")

COLUMN_CANDIDATES = {
    "RPM": ["Engine RPM [RPM]", "RPM"],
    "Speed": ["Vehicle Speed Sensor [km/h]", "Speed", "Speed [km/h]"],
    "MAF": ["Air Flow Rate from Mass Flow Sensor [g/s]", "MAF", "Mass Air Flow [g/s]"],
    "Throttle": ["Absolute Throttle Position [%]", "Throttle"]
}


def find_and_rename(df):
    rename_map = {}
    for canon, candidates in COLUMN_CANDIDATES.items():
        for c in candidates:
            if c in df.columns:
                rename_map[c] = canon
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def clean_dataframe(df):
    """Clean and process OBD-II dataframe: rename columns, coerce numeric, interpolate, filter outliers."""
    
    df = find_and_rename(df)
    
    # Convert to numeric
    for col in ["RPM", "Speed", "MAF"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Require at least Speed and MAF
    if not {"Speed", "MAF"}.issubset(set(df.columns)):
        raise ValueError("Required columns 'Speed' and 'MAF' are missing after renaming.")
    
    # Interpolate small gaps
    cols_to_interp = [c for c in ["Speed", "MAF", "RPM"] if c in df.columns]
    if cols_to_interp:
        df[cols_to_interp] = df[cols_to_interp].interpolate(
            method="linear",
            limit=5,
            limit_direction="both"
        )
    
    # Drop rows still missing required values
    df = df.dropna(subset=["Speed", "MAF"])
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Filter unrealistic values
    df = df[df["Speed"].between(0, 250)]
    
    if "RPM" in df.columns:
        df = df[df["RPM"].between(0, 10000)]
    
    df = df[df["MAF"].between(0.0, 500.0)]
    
    return df


def main():
    all_trips = []
    cleaned_dir = "10.35097-1130/cleaned_data"
    os.makedirs(cleaned_dir, exist_ok=True)

    summary = {"files_processed": 0, "rows_before": 0, "rows_after": 0}

    for file in glob.glob(DATA_PATH):
        try:
            summary["files_processed"] += 1
            raw_df = pd.read_csv(file)

            initial_rows = len(raw_df)
            summary["rows_before"] += initial_rows

            # Compute start/end times from raw Time column
            if "Time" in raw_df.columns:
                times = pd.to_datetime(raw_df["Time"], errors="coerce").dropna()
                start_time = str(times.iloc[0]) if len(times) > 0 else None
                end_time = str(times.iloc[-1]) if len(times) > 0 else None
            else:
                start_time = end_time = None

            df = clean_dataframe(raw_df)

            cleaned_rows = len(df)
            summary["rows_after"] += cleaned_rows

            # Add metadata
            trip_name = os.path.basename(file)
            #df["Trip"] = trip_name
            #df["start_time"] = start_time
            #df["end_time"] = end_time

            out_path = os.path.join(cleaned_dir, trip_name)
            df.to_csv(out_path.replace('.csv', '_cleaned.csv'), index=False)

            all_trips.append(df)

        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue

    if all_trips:
        final_df = pd.concat(all_trips, ignore_index=True)
        out_combined = "10.35097-1130/cleaned_data.csv"
        final_df.to_csv(out_combined, index=False)

        print(f"Generated {summary['files_processed']} cleaned files in {cleaned_dir}")
        print(f"Combined dataset saved to {out_combined}")
        print(f"Rows before: {summary['rows_before']}, after: {summary['rows_after']}")
        print(final_df.head())
    else:
        print("No trips processed. Check DATA_PATH and CSV files.")


if __name__ == '__main__':
    main()
