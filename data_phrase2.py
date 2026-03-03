#  讀 OBD-II CSV
#  驗證數據
#  分 trip
#  識別車輛
#  根據車型用不同 threshold
#  清洗數據
#  計油耗
#  偵測不良駕駛行為
#  計效率分數
#  生成 coaching 建議
#  儲存 cleaned data + metadata

# names are changed into RPM    Speed   MAF Throttle    Time

import pandas as pd
import glob
import os
import hashlib
from datetime import datetime
import json

print(f"Current working directory: {os.getcwd()}")

# Path to your dataset folder (note nested folder in this repo)
DATA_PATH = "10.35097-1130/10.35097-1130/data/dataset/OBD-II-Dataset/OBD-II-Dataset/*.csv"
print(f"Looking for files at: {DATA_PATH}")
print(f"Files found: {len(glob.glob(DATA_PATH))}")

# Constants
AFR = 14.7          # Air-Fuel Ratio for petrol
FUEL_DENSITY = 745  # g/L
TRIP_GAP_MINUTES = 10  # Gap threshold to segment trips

COLUMN_CANDIDATES = {
    "RPM": ["Engine RPM [RPM]", "RPM"],
    "Speed": ["Vehicle Speed Sensor [km/h]", "Speed", "Speed [km/h]"],
    "MAF": ["Air Flow Rate from Mass Flow Sensor [g/s]", "MAF", "Mass Air Flow [g/s]"],
    "Throttle": ["Absolute Throttle Position [%]", "Throttle"],
    "Time": ["Time"],
}

REQUIRED_COLUMNS = {"Speed", "MAF"}

# ============================================================================
# STEP 5: VEHICLE PROFILE CALIBRATION
# ============================================================================

VEHICLE_PROFILES = {
    "Seat_Leon": {
        "make": "Seat",
        "model": "Leon",
        "rpm_high_threshold": 3500,
        "harsh_throttle_threshold": 30,
        "braking_threshold": -8.0,
        "fuel_model_version": "v1",
    },
    "default": {
        "rpm_high_threshold": 3000,
        "harsh_throttle_threshold": 30,
        "braking_threshold": -8.0,
        "fuel_model_version": "v1",
    }
}


def get_vehicle_profile(make, model):
    """Get calibrated thresholds for a vehicle (STEP 5)."""
    key = f"{make}_{model}"
    if key in VEHICLE_PROFILES:
        return VEHICLE_PROFILES[key]
    return VEHICLE_PROFILES["default"]


# ============================================================================
# STEP 3: DATASET INGESTION & VALIDATION (BR1)
# ============================================================================

def validate_dataset(df, filename=""):
    """
    Validate dataset schema and generate ingestion metadata.
    
    Returns:
        dict with validation status, row count, checksum, timestamp, missing %, errors
    """
    errors = []
    
    # Check required columns exist
    if not REQUIRED_COLUMNS.issubset(set(df.columns)):
        missing = REQUIRED_COLUMNS - set(df.columns)
        errors.append(f"Missing required columns: {missing}")
    
    # Check for empty dataframe
    if df.empty:
        errors.append("Dataframe is empty")
    
    # Validate numeric columns
    for col in ["RPM", "Speed", "MAF", "Throttle"]:
        if col in df.columns:
            numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
            non_numeric_count = len(df) - numeric_count
            if non_numeric_count > len(df) * 0.5:
                errors.append(f"Column {col}: {non_numeric_count} non-numeric values")
    
    # Calculate missing data percentage
    missing_pct = (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100 if df.size > 0 else 0
    
    # Generate checksum
    checksum = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
    
    return {
        "valid": len(errors) == 0,
        "rows": len(df),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat(),
        "missing_pct": round(missing_pct, 2),
        "errors": errors,
        "filename": filename,
    }


# ============================================================================
# STEP 4: TRIP & VEHICLE IDENTIFICATION
# ============================================================================

def extract_vehicle_from_filename(filename):
    """
    Extract vehicle make/model from filename.
    Example: "2017-07-05_Seat_Leon_RT_S_Stau.csv" → {make, model, vehicle_id}
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    parts = name.split('_')
    
    vehicle_info = {
        "make": None,
        "model": None,
        "vehicle_id": None,
        "raw_filename": os.path.basename(filename),
    }
    
    if len(parts) >= 4:
        vehicle_info["make"] = parts[1]
        vehicle_info["model"] = parts[2]
        vehicle_key = f"{parts[1]}{parts[2]}"
        vehicle_info["vehicle_id"] = hashlib.md5(vehicle_key.encode()).hexdigest()[:8]
    
    return vehicle_info


def segment_into_trips(df, time_col="Time", gap_minutes=TRIP_GAP_MINUTES):
    """
    Segment dataframe into trips based on time gaps.
    Returns: list of {trip_id, start_time, end_time, rows, df}
    """
    if time_col not in df.columns:
        return [{"trip_id": "trip_001", "start_time": None, "end_time": None, "rows": len(df), "df": df}]
    
    try:
        df_sorted = df.copy()
        df_sorted[time_col] = pd.to_datetime(df_sorted[time_col], format="%H:%M:%S.%f", errors='coerce')
        df_sorted = df_sorted.dropna(subset=[time_col]).sort_values(time_col).reset_index(drop=True)
    except:
        return [{"trip_id": "trip_001", "start_time": None, "end_time": None, "rows": len(df), "df": df}]
    
    trips = []
    trip_num = 1
    current_trip_start_idx = 0
    
    for i in range(1, len(df_sorted)):
        time_diff = (df_sorted.iloc[i][time_col] - df_sorted.iloc[i-1][time_col]).total_seconds() / 60
        
        if time_diff > gap_minutes:
            trip_data = {
                "trip_id": f"trip_{trip_num:03d}",
                "start_time": df_sorted.iloc[current_trip_start_idx][time_col],
                "end_time": df_sorted.iloc[i-1][time_col],
                "rows": i - current_trip_start_idx,
                "df": df_sorted.iloc[current_trip_start_idx:i].copy(),
            }
            trips.append(trip_data)
            trip_num += 1
            current_trip_start_idx = i
    
    # Add final trip
    if current_trip_start_idx < len(df_sorted):
        trip_data = {
            "trip_id": f"trip_{trip_num:03d}",
            "start_time": df_sorted.iloc[current_trip_start_idx][time_col],
            "end_time": df_sorted.iloc[-1][time_col],
            "rows": len(df_sorted) - current_trip_start_idx,
            "df": df_sorted.iloc[current_trip_start_idx:].copy(),
        }
        trips.append(trip_data)
    
    return trips

# formula Fuel=MAF​/(AFR×FuelDensity)
def estimate_fuel_l_per_100km(maf, speed):
    """Estimate fuel consumption in L/100km"""
    try:
        if speed <= 0 or maf <= 0:
            return 0.0
    except Exception:
        return 0.0
    fuel_rate_lps = maf / (AFR * FUEL_DENSITY)
    fuel_lph = fuel_rate_lps * 3600
    return (fuel_lph / speed) * 100


def detect_behaviors(df, vehicle_profile=None):
    """STEP 7: Scan a cleaned trip frame for inefficiency events using vehicle profile thresholds."""
    if vehicle_profile is None:
        vehicle_profile = VEHICLE_PROFILES["default"]
    
    rpm_thresh = vehicle_profile.get("rpm_high_threshold", 3000)
    braking_threshold = vehicle_profile.get("braking_threshold", -8.0)
    
    events = {
        "high_rpm": 0,  # RPM > threshold with throttle > 20% for >2s
        "harsh_throttle": 0, # Throttle increase >30% in <=1s
        "hard_braking": 0, # Decel < braking_threshold x 3.6 (speed/change in time)
    }
    if "Time" not in df.columns:
        return events
    # convert time to seconds since start
    t = pd.to_datetime(df["Time"], format="%H:%M:%S.%f", errors='coerce')
    if t.isna().all():
        return events
    secs = (t - t.iloc[0]).dt.total_seconds()
    df = df.copy()
    df["_sec"] = secs
    # RPM acceleration: rpm>rpm_thresh & throttle>20 for >2s consecutively
    thr_thresh = 20
    duration_thresh = 2
    mask = (df["RPM"] > rpm_thresh) & (df["Throttle"] > thr_thresh)
    # count clusters lasting >duration_thresh
    if mask.any():
        groups = (mask != mask.shift()).cumsum()
        for _, grp in df[mask].groupby(groups):
            if grp["_sec"].iloc[-1] - grp["_sec"].iloc[0] >= duration_thresh:
                events["high_rpm"] += 1
    # harsh throttle: throttle increase >30% in <=1s
    if "Throttle" in df.columns:
        dt = df["_sec"].diff().fillna(0)
        dth = df["Throttle"].diff().fillna(0)
        thresh = 30
        events["harsh_throttle"] = int(((dth > thresh) & (dt <= 1)).sum())
    # hard braking: decel >8 m/s2 (~28.8 km/h per sec) with throttle near 0
    if "Speed" in df.columns:
        ds = df["Speed"].diff().fillna(0)
        dt = df["_sec"].diff().fillna(0)
        decel = ds / dt  # km/h per sec
        events["hard_braking"] = int(((decel < braking_threshold * 3.6) & (df.get("Throttle", 0) < 5)).sum())
    return events

#formula for calculating the points Score=100−FuelPenalty−2×high_rpm−1.5×harsh_throttle−2×hard_braking
def score_trip(events, fuel_estimate):
    """Compute simple efficiency score based on events and fuel."""
    base = 100.0
    # fuel penalty relative to 8 L/100km ideal
    if fuel_estimate is None:
        fuel_pen = 0
    else:
        fuel_pen = max(0, fuel_estimate - 8) * 2
    score = base - fuel_pen - 2 * events.get("high_rpm", 0) - 1.5 * events.get("harsh_throttle", 0) - 2 * events.get("hard_braking", 0)
    return max(0, min(100, score))


def granite_coach(summary):
    """Create a prompt and return dummy coaching advice (stub for API)."""
    prompt = f"Efficiency Score: {summary['score']}\n"
    prompt += f"High RPM events: {summary['high_rpm']}\n"
    prompt += f"Harsh throttle events: {summary['harsh_throttle']}\n"
    prompt += f"Hard braking events: {summary['hard_braking']}\n"
    prompt += f"Fuel economy: {summary['fuel_estimate']:.2f} L/100km\n"
    # stub return
    return "Keep RPM low, avoid sudden throttle, brake gently."


def find_and_rename(df):
    """Normalize column names to canonical forms"""
    rename_map = {}
    for canon, candidates in COLUMN_CANDIDATES.items():
        for c in candidates:
            if c in df.columns:
                rename_map[c] = canon
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def clean_and_score_trip(df, trip_id, vehicle_id, vehicle_make, vehicle_model, ingestion_metadata):
    """
    Clean trip data and compute metadata with comprehensive quality reporting (STEP 9).
    Returns: dict with trip stats, cleaned dataframe, and quality report
    """
    result = {
        "trip_id": trip_id,
        "vehicle_id": vehicle_id,
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "rows_before": len(df),
        "rows_after": 0,
        "missing_pct": 0.0,
        "confidence": "unknown",
        "errors": [],
        "df": None,
        "fuel_estimate": None,
        "quality_report": {},
    }
    
    try:
        # Get vehicle profile (STEP 5)
        vehicle_profile = get_vehicle_profile(vehicle_make, vehicle_model)
        result["vehicle_profile_used"] = vehicle_profile.get("fuel_model_version", "v1")
        
        # Track quality metrics (STEP 9)
        quality_report = {
            "rows_input": len(df),
            "rows_cleaned": 0,
            "row_retention_pct": 0.0,
            "interpolation_counts": {},
            "outliers_removed": {},
            "vehicle_profile_used": vehicle_profile.get("fuel_model_version", "v1"),
        }
        
        # Ensure numeric and track interpolation before
        df_before_interp = df.copy()
        for col in ["RPM", "Speed", "MAF"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Require Speed & MAF
        if not {"Speed", "MAF"}.issubset(set(df.columns)):
            result["errors"].append("Missing Speed or MAF")
            return result
        
        # Interpolate and track NaN counts before/after
        cols_to_interp = [c for c in ["Speed", "MAF", "RPM"] if c in df.columns]
        if cols_to_interp:
            for col in cols_to_interp:
                nans_before = df[col].isna().sum()
                df[col] = df[col].interpolate(method="linear", limit=5, limit_direction="both")
                nans_after = df[col].isna().sum()
                imputed_count = nans_before - nans_after
                if imputed_count > 0:
                    quality_report["interpolation_counts"][col] = int(imputed_count)
        
        # Drop remaining NaN (speed/MAF required)
        rows_before_drop = len(df)
        df = df.dropna(subset=["Speed", "MAF"])
        rows_after_drop = len(df)
        
        # Drop duplicates
        df = df.drop_duplicates()
        rows_after_dedup = len(df)
        
        # Filter outliers and track removals (STEP 9)
        outliers_removed = {}
        
        speed_outliers = len(df[~df["Speed"].between(0, 250)])
        if speed_outliers > 0:
            outliers_removed["speed"] = speed_outliers
        df = df[df["Speed"].between(0, 250)]
        
        if "RPM" in df.columns:
            rpm_outliers = len(df[~df["RPM"].between(0, 10000)])
            if rpm_outliers > 0:
                outliers_removed["rpm"] = rpm_outliers
            df = df[df["RPM"].between(0, 10000)]
        
        maf_outliers = len(df[~df["MAF"].between(0.0, 500.0)])
        if maf_outliers > 0:
            outliers_removed["maf"] = maf_outliers
        df = df[df["MAF"].between(0.0, 500.0)]
        
        if outliers_removed:
            quality_report["outliers_removed"] = outliers_removed
        
        result["rows_after"] = len(df)
        quality_report["rows_cleaned"] = len(df)
        
        # Calculate row retention % and missing %
        if result["rows_before"] > 0:
            quality_report["row_retention_pct"] = round((result["rows_after"] / result["rows_before"]) * 100, 2)
        
        missing_pct = (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100 if len(df) > 0 else 0
        result["missing_pct"] = round(missing_pct, 2)
        
        # Confidence levels
        if missing_pct < 2 and result["rows_after"] / result["rows_before"] > 0.95:
            result["confidence"] = "high"
        elif missing_pct < 5 and result["rows_after"] / result["rows_before"] > 0.80:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"
        
        quality_report["confidence_level"] = result["confidence"]
        
        # Fuel estimate
        if len(df) > 0:
            df["Fuel_L_per_100km"] = df.apply(lambda row: estimate_fuel_l_per_100km(row["MAF"], row["Speed"]), axis=1)
            result["fuel_estimate"] = df["Fuel_L_per_100km"].mean()

            # detection & scoring with vehicle profile (STEP 5 + STEP 7)
            events = detect_behaviors(df, vehicle_profile)
            result["events"] = events
            result["score"] = score_trip(events, result["fuel_estimate"])
            # simple coaching message
            result["coach_text"] = granite_coach({
                **events,
                "score": result["score"],
                "fuel_estimate": result["fuel_estimate"]
            })
        
        result["quality_report"] = quality_report
        result["df"] = df
        
    except Exception as e:
        result["errors"].append(str(e))
    
    return result


def main():
    all_trips_processed = []
    ingestion_log = []
    cleaned_dir = "10.35097-1130/cleaned_Data"
    metadata_dir = "10.35097-1130/Trip_feedbacks"
    os.makedirs(cleaned_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    
    global_stats = {
        "files_processed": 0,
        "files_valid": 0,
        "files_invalid": 0,
        "total_rows_before": 0,
        "total_rows_after": 0,
        "total_trips": 0,
    }
    
    for file in glob.glob(DATA_PATH):
        try:
            print(f"\n📂 Processing: {os.path.basename(file)}")
            global_stats["files_processed"] += 1
            
            df = pd.read_csv(file)
            df = find_and_rename(df)
            
            # STEP 3: Validate
            ingestion_meta = validate_dataset(df, file)
            ingestion_log.append(ingestion_meta)
            
            if not ingestion_meta["valid"]:
                print(f"  ❌ Validation failed: {ingestion_meta['errors']}")
                global_stats["files_invalid"] += 1
                continue
            
            global_stats["files_valid"] += 1
            global_stats["total_rows_before"] += ingestion_meta["rows"]
            
            # STEP 4: Extract vehicle
            vehicle_info = extract_vehicle_from_filename(file)
            print(f"  🚗 Vehicle: {vehicle_info['make']} {vehicle_info['model']} (ID: {vehicle_info['vehicle_id']})")
            
            # STEP 4: Segment trips
            trips = segment_into_trips(df, time_col="Time", gap_minutes=TRIP_GAP_MINUTES)
            print(f"  🛣️  Found {len(trips)} trip(s)")
            
            for trip in trips:
                trip_id = trip["trip_id"]
                trip_df = trip["df"]
                
                # Clean and score (STEP 5 + STEP 9 integrated)
                trip_result = clean_and_score_trip(
                    trip_df, 
                    trip_id, 
                    vehicle_info["vehicle_id"],
                    vehicle_info["make"],
                    vehicle_info["model"],
                    ingestion_meta
                )
                
                if trip_result["df"] is not None and len(trip_result["df"]) > 0:
                    # Add metadata columns
                    trip_result["df"]["trip_id"] = trip_id
                    trip_result["df"]["vehicle_id"] = vehicle_info["vehicle_id"]
                    trip_result["df"]["vehicle_make"] = vehicle_info["make"]
                    trip_result["df"]["vehicle_model"] = vehicle_info["model"]
                    trip_result["df"]["confidence"] = trip_result["confidence"]
                    
                    # Save cleaned CSV
                    out_filename = f"{os.path.splitext(os.path.basename(file))[0]}_{trip_id}_cleaned.csv"
                    out_path = os.path.join(cleaned_dir, out_filename)
                    trip_result["df"].to_csv(out_path, index=False)
                    
                    # Save metadata JSON with comprehensive quality report (STEP 9)
                    trip_metadata = {
                        "trip_id": trip_id,
                        "vehicle_id": vehicle_info["vehicle_id"],
                        "vehicle_make": vehicle_info["make"],
                        "vehicle_model": vehicle_info["model"],
                        "start_time": str(trip["start_time"]),
                        "end_time": str(trip["end_time"]),
                        "rows_before": trip_result["rows_before"],
                        "rows_after": trip_result["rows_after"],
                        "missing_pct": trip_result["missing_pct"],
                        "confidence": trip_result["confidence"],
                        "fuel_estimate_l_per_100km": trip_result["fuel_estimate"],
                        "events": trip_result.get("events", {}),
                        "score": trip_result.get("score", None),
                        "coach": trip_result.get("coach_text", ""),
                        "ingestion_checksum": ingestion_meta["checksum"],
                        "ingestion_timestamp": ingestion_meta["timestamp"],
                        "quality_report": trip_result.get("quality_report", {}),
                    }
                    
                    meta_filename = out_filename.replace(".csv", "_meta.json")
                    meta_path = os.path.join(metadata_dir, meta_filename)
                    with open(meta_path, 'w') as f:
                        json.dump(trip_metadata, f, indent=2)
                    
                    print(f"    ✅ {trip_id}: {trip_result['rows_after']} rows | Confidence: {trip_result['confidence']} | Fuel: {trip_result['fuel_estimate']:.2f} L/100km")
                    
                    all_trips_processed.append(trip_result["df"])
                    global_stats["total_trips"] += 1
                    global_stats["total_rows_after"] += trip_result["rows_after"]
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            global_stats["files_invalid"] += 1
            continue
    
    # Final summary
    print(f"\n{'='*70}")
    print(f"📊 PROCESSING SUMMARY")
    print(f"{'='*70}")
    print(f"Files: {global_stats['files_valid']}/{global_stats['files_processed']} valid")
    print(f"Total trips: {global_stats['total_trips']}")
    if global_stats['total_rows_before'] > 0:
        print(f"Rows: {global_stats['total_rows_before']:,} → {global_stats['total_rows_after']:,} ({(global_stats['total_rows_after'] / global_stats['total_rows_before'] * 100):.1f}%)")
    print(f"{'='*70}\n")
    
    # Save combined dataset
    if all_trips_processed:
        final_df = pd.concat(all_trips_processed, ignore_index=True)
        out_combined = "10.35097-1130/cleaned_data.csv"
        final_df.to_csv(out_combined, index=False)
        print(f"✅ Combined cleaned data: {out_combined}")
    
    # Save ingestion log
    log_path = "10.35097-1130/ingestion_log.json"
    with open(log_path, 'w') as f:
        json.dump(ingestion_log, f, indent=2)
    print(f"✅ Ingestion log: {log_path}\n")


if __name__ == '__main__':
    main()


