# 👉 讀 OBD-II CSV
# 👉 清洗數據
# 👉 插值補 missing
# 👉 過濾異常值
# 👉 計算 L/100km
# 👉 儲存 cleaned CSV
# 👉 合併成一個總 
import pandas as pd
import glob
import os

print(f"Current working directory: {os.getcwd()}")

# Path to your dataset folder (note nested folder in this repo)
DATA_PATH = "10.35097-1130/10.35097-1130/data/dataset/OBD-II-Dataset/OBD-II-Dataset/*.csv"
print(f"Looking for files at: {DATA_PATH}")
print(f"Files found: {len(glob.glob(DATA_PATH))}")

# Constants
AFR = 14.7          # Air-Fuel Ratio for petrol
FUEL_DENSITY = 745  # g/L

COLUMN_CANDIDATES = {
    "RPM": ["Engine RPM [RPM]", "RPM"],
    "Speed": ["Vehicle Speed Sensor [km/h]", "Speed", "Speed [km/h]"],
    "MAF": ["Air Flow Rate from Mass Flow Sensor [g/s]", "MAF", "Mass Air Flow [g/s]"],
    "Throttle": ["Absolute Throttle Position [%]", "Throttle"]
}


def estimate_fuel_l_per_100km(maf, speed):
    """Estimate fuel consumption in L/100km"""
    try:
        if speed <= 0 or maf <= 0:
            return 0.0
    except Exception:
        return 0.0
    fuel_rate_lps = maf / (AFR * FUEL_DENSITY)  # L/s
    fuel_lph = fuel_rate_lps * 3600             # L/h
    return (fuel_lph / speed) * 100


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


def main():
    all_trips = []
    cleaned_dir = "10.35097-1130/cleaned_trips"
    os.makedirs(cleaned_dir, exist_ok=True)

    summary = {"files_processed": 0, "rows_before": 0, "rows_after": 0}

    for file in glob.glob(DATA_PATH):
        try:
            summary["files_processed"] += 1
            df = pd.read_csv(file)

            df = find_and_rename(df)

            # Ensure numeric columns exist before coercion
            for col in ["RPM", "Speed", "MAF"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            initial_rows = len(df)
            summary["rows_before"] += initial_rows

            # Require at least Speed and MAF to estimate fuel; RPM optional
            if not {"Speed", "MAF"}.issubset(set(df.columns)):
                print(f"Skipping {os.path.basename(file)}: required columns missing")
                continue

            # Interpolate small gaps (limit consecutive NaNs)
            cols_to_interp = [c for c in ["Speed", "MAF", "RPM"] if c in df.columns]
            if cols_to_interp:
                df[cols_to_interp] = df[cols_to_interp].interpolate(method="linear", limit=5, limit_direction="both")

            # Drop rows where Speed or MAF are missing after interpolation
            df = df.dropna(subset=["Speed", "MAF"])

            # Remove duplicates
            df = df.drop_duplicates()

            # Filter unrealistic values
            df = df[df["Speed"].between(0, 250)]
            if "RPM" in df.columns:
                df = df[df["RPM"].between(0, 10000)]
            df = df[df["MAF"].between(0.0, 500.0)]

            # Recount
            cleaned_rows = len(df)
            summary["rows_after"] += cleaned_rows

            # Compute fuel estimate
            df["Fuel_L_per_100km"] = df.apply(lambda row: estimate_fuel_l_per_100km(row["MAF"], row["Speed"]), axis=1)

            # Add trip name and save per-trip cleaned CSV
            trip_name = os.path.basename(file)
            df["Trip"] = trip_name
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
        print(f"Cleaned data saved to {out_combined}")
        print(f"Files processed: {summary['files_processed']}")
        print(f"Rows before: {summary['rows_before']}, after: {summary['rows_after']}")
        print(final_df.head())
    else:
        print("No trips processed. Check DATA_PATH and CSV files.")


if __name__ == '__main__':
    main()




