## Preprocessing Module

The preprocessing pipeline for Features 1 and 2 lives in `data_pipeline/ingestion/preprocessing.py`.
It is intentionally limited to:

1. Dataset ingestion and validation.
2. Vehicle and trip identification.

The module exposes a reusable `PreprocessingPipeline` class so other parts of the application can call it with either a pandas dataframe or a CSV path.

Validation behavior:

- Canonicalizes source column names into `RPM`, `MAF`, `Throttle`, `Speed`, and `Timestamp`.
- Accepts a file only if all required columns are present.
- Produces an ingestion record with filename, processing timestamp, row count, checksum, and any missing fields.
- Rejects invalid files and records the failed validation in the audit log.

Vehicle and trip identification behavior:

- Parses filenames such as `2017-07-05_Seat_Leon_RT_S_Stau.csv` to extract vehicle make and model.
- Builds a pseudonymous `vehicle_id` from the make and model.
- Segments trips whenever the time gap between consecutive rows exceeds 10 minutes.
- Attaches `trip_id`, `vehicle_id`, `vehicle_make`, `vehicle_model`, and `source_filename` to each segmented trip dataframe.

The existing `data_phase1.py` and `data_phase2.py` scripts now act as thin CLI wrappers around the shared preprocessing module for debugging and compatibility.

## Virtual Environment Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install pandas
```

## CLI Debugging

Run the preprocessing module against the sample dataset directory:

```bash
python -m data_pipeline.ingestion.preprocessing
```

Run it against a specific file:

```bash
python -m data_pipeline.ingestion.preprocessing data_samples/10.35097-1130/data/dataset/OBD-II-Dataset/2017-07-05_Seat_Leon_RT_S_Stau.csv
```

Write debug artifacts, including the ingestion audit log and segmented trip CSV files:

```bash
python -m data_pipeline.ingestion.preprocessing data_samples/10.35097-1130/data/dataset/OBD-II-Dataset --output-dir debug/preprocessing
```

You can also use the legacy wrapper scripts:

```bash
python data_pipeline/ingestion/data_phase1.py --output-dir debug/preprocessing
python data_pipeline/ingestion/data_phase2.py --output-dir debug/preprocessing
```

## Programmatic Usage

```python
import pandas as pd

from data_pipeline.ingestion.preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline(trip_gap_minutes=10)

file_result = pipeline.ingest_file(
	"data_samples/10.35097-1130/data/dataset/OBD-II-Dataset/2017-07-05_Seat_Leon_RT_S_Stau.csv"
)

dataframe = pd.read_csv(
	"data_samples/10.35097-1130/data/dataset/OBD-II-Dataset/2017-07-05_Seat_Leon_RT_S_Stau.csv"
)
dataframe_result = pipeline.ingest_dataframe(dataframe, source_name="manual_debug.csv")
```

Both methods return a `ProcessedDataset` object from the preprocessing module. This is a Python dataclass, not raw JSON.

Returned object shape:

```python
ProcessedDataset(
	validation=ValidationReport(...),
	vehicle=VehicleInfo(...),
	trips=[ProcessedTrip(...)]
)
```

### Validation Metadata

The `validation` field contains a `ValidationReport` dataclass with:

```python
ValidationReport(
	filename: str,
	source_path: str | None,
	status: str,
	processed_at: str,
	row_count: int,
	checksum: str,
	missing_fields: list[str],
	column_mapping: dict[str, str],
	notes: list[str],
)
```

Key points:

- `status` is typically `accepted` or `rejected`.
- `checksum` is an MD5 hash.
- `missing_fields` lists schema problems for rejected files.
- `column_mapping` shows which source columns were normalized into canonical names.

### Vehicle Metadata

The `vehicle` field contains a `VehicleInfo` dataclass:

```python
VehicleInfo(
	make: str | None,
	model: str | None,
	vehicle_id: str,
	source_filename: str,
)
```

### Trip Results

The `trips` field is a list of `ProcessedTrip` dataclasses:

```python
ProcessedTrip(
	metadata=TripMetadata(...),
	dataframe=<pandas.DataFrame>,
)
```

Each `metadata` field is a `TripMetadata` dataclass:

```python
TripMetadata(
	trip_id: str,
	source_filename: str,
	source_path: str | None,
	vehicle_id: str,
	vehicle_make: str | None,
	vehicle_model: str | None,
	segment_index: int,
	row_count: int,
	start_timestamp: str | None,
	end_timestamp: str | None,
)
```

### Trip DataFrame Format

Each trip's `dataframe` is a normal pandas DataFrame. It contains:

- The normalized source columns such as `RPM`, `MAF`, `Throttle`, `Speed`, and `Timestamp`.
- The attached metadata column `trip_id`.
- The attached metadata column `vehicle_id`.
- The attached metadata column `vehicle_make`.
- The attached metadata column `vehicle_model`.
- The attached metadata column `source_filename`.

Example usage:

```python
result = pipeline.ingest_file(
	"data_samples/10.35097-1130/data/dataset/OBD-II-Dataset/2017-07-05_Seat_Leon_RT_S_Stau.csv"
)

print(result.validation.status)
print(result.validation.checksum)
print(result.vehicle.vehicle_id)
print(len(result.trips))

first_trip = result.trips[0]
print(first_trip.metadata.trip_id)
print(first_trip.metadata.start_timestamp)
print(first_trip.dataframe.head())
```

If JSON-compatible metadata is needed, the module includes serializer helpers for validation and trip metadata. The trip data itself remains a pandas DataFrame unless explicitly converted with pandas methods such as `to_dict()` or `to_json()`.
