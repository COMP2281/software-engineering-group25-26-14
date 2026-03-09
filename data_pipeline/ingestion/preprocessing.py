from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

REQUIRED_COLUMNS = ("RPM", "MAF", "Throttle", "Speed", "Timestamp")
TIME_ALIASES = ("Timestamp", "Time")
TRIP_GAP_MINUTES = 10

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "RPM": ("RPM", "Engine RPM [RPM]"),
    "MAF": ("MAF", "Air Flow Rate from Mass Flow Sensor [g/s]", "Mass Air Flow [g/s]"),
    "Throttle": ("Throttle", "Absolute Throttle Position [%]"),
    "Speed": ("Speed", "Vehicle Speed Sensor [km/h]", "Speed [km/h]"),
    "Timestamp": TIME_ALIASES,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_dataframe_checksum(dataframe: pd.DataFrame) -> str:
    hashed = pd.util.hash_pandas_object(dataframe, index=True).values.tobytes()
    return hashlib.md5(hashed).hexdigest()


def build_file_checksum(file_path: Path) -> str:
    digest = hashlib.md5()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_columns(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    rename_map: dict[str, str] = {}
    for canonical_name, candidates in COLUMN_ALIASES.items():
        for candidate in candidates:
            if candidate in dataframe.columns:
                rename_map[candidate] = canonical_name
                break

    normalized = dataframe.rename(columns=rename_map)
    return normalized, rename_map


def missing_required_columns(dataframe: pd.DataFrame) -> list[str]:
    return [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]


def parse_vehicle_from_filename(filename: str) -> tuple[str | None, str | None, str]:
    stem = Path(filename).stem
    parts = stem.split("_")
    make = parts[1] if len(parts) > 1 else None
    model = parts[2] if len(parts) > 2 else None
    identity_source = "::".join(part for part in (make, model) if part)
    if not identity_source:
        identity_source = stem
    vehicle_id = hashlib.md5(identity_source.encode("utf-8")).hexdigest()[:8]
    return make, model, vehicle_id


def parse_timestamps(timestamp_series: pd.Series) -> pd.Series:
    parsed = pd.Series(pd.NaT, index=timestamp_series.index, dtype="datetime64[ns]")
    timestamp_text = timestamp_series.astype("string")

    for time_format in ("%H:%M:%S.%f", "%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        remaining = parsed.isna()
        if not remaining.any():
            break
        parsed.loc[remaining] = pd.to_datetime(
            timestamp_text.loc[remaining],
            format=time_format,
            errors="coerce",
        )

    return parsed


@dataclass(slots=True)
class ValidationReport:
    filename: str
    source_path: str | None
    status: str
    processed_at: str
    row_count: int
    checksum: str
    missing_fields: list[str] = field(default_factory=list)
    column_mapping: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VehicleInfo:
    make: str | None
    model: str | None
    vehicle_id: str
    source_filename: str


@dataclass(slots=True)
class TripMetadata:
    trip_id: str
    source_filename: str
    source_path: str | None
    vehicle_id: str
    vehicle_make: str | None
    vehicle_model: str | None
    segment_index: int
    row_count: int
    start_timestamp: str | None
    end_timestamp: str | None


@dataclass(slots=True)
class ProcessedTrip:
    metadata: TripMetadata
    dataframe: pd.DataFrame


@dataclass(slots=True)
class ProcessedDataset:
    validation: ValidationReport
    vehicle: VehicleInfo
    trips: list[ProcessedTrip]


@dataclass(slots=True)
class BatchProcessingResult:
    processed_datasets: list[ProcessedDataset]
    audit_log: list[ValidationReport]


class PreprocessingPipeline:
    def __init__(self, trip_gap_minutes: int = TRIP_GAP_MINUTES) -> None:
        self.trip_gap_minutes = trip_gap_minutes

    def ingest_dataframe(self, dataframe: pd.DataFrame, source_name: str = "dataframe") -> ProcessedDataset:
        normalized, column_mapping = normalize_columns(dataframe.copy())
        checksum = build_dataframe_checksum(normalized)
        return self._process_dataframe(
            dataframe=normalized,
            source_name=source_name,
            source_path=None,
            checksum=checksum,
            column_mapping=column_mapping,
        )

    def ingest_file(self, file_path: str | Path) -> ProcessedDataset:
        source = Path(file_path)
        dataframe = pd.read_csv(source)
        normalized, column_mapping = normalize_columns(dataframe)
        checksum = build_file_checksum(source)
        return self._process_dataframe(
            dataframe=normalized,
            source_name=source.name,
            source_path=str(source),
            checksum=checksum,
            column_mapping=column_mapping,
        )

    def ingest_path(self, input_path: str | Path) -> BatchProcessingResult:
        source = Path(input_path)
        if source.is_file():
            files = [source]
        elif source.is_dir():
            files = sorted(source.glob("*.csv"))
        else:
            raise FileNotFoundError(f"Input path does not exist: {source}")

        processed_datasets: list[ProcessedDataset] = []
        audit_log: list[ValidationReport] = []

        for file_path in files:
            dataset = self.ingest_file(file_path)
            processed_datasets.append(dataset)
            audit_log.append(dataset.validation)

        return BatchProcessingResult(processed_datasets=processed_datasets, audit_log=audit_log)

    def _process_dataframe(
        self,
        dataframe: pd.DataFrame,
        source_name: str,
        source_path: str | None,
        checksum: str,
        column_mapping: dict[str, str],
    ) -> ProcessedDataset:
        missing_fields = missing_required_columns(dataframe)
        validation = ValidationReport(
            filename=source_name,
            source_path=source_path,
            status="accepted" if not missing_fields else "rejected",
            processed_at=utc_now_iso(),
            row_count=len(dataframe),
            checksum=checksum,
            missing_fields=missing_fields,
            column_mapping=column_mapping,
        )

        make, model, vehicle_id = parse_vehicle_from_filename(source_name)
        vehicle = VehicleInfo(
            make=make,
            model=model,
            vehicle_id=vehicle_id,
            source_filename=source_name,
        )

        if missing_fields:
            validation.notes.append("Rejected during schema validation.")
            return ProcessedDataset(validation=validation, vehicle=vehicle, trips=[])

        trips, notes = self._segment_trips(
            dataframe=dataframe,
            source_name=source_name,
            source_path=source_path,
            vehicle=vehicle,
        )
        validation.notes.extend(notes)
        return ProcessedDataset(validation=validation, vehicle=vehicle, trips=trips)

    def _segment_trips(
        self,
        dataframe: pd.DataFrame,
        source_name: str,
        source_path: str | None,
        vehicle: VehicleInfo,
    ) -> tuple[list[ProcessedTrip], list[str]]:
        parsed_timestamps = parse_timestamps(dataframe["Timestamp"])
        notes: list[str] = []

        if parsed_timestamps.isna().all():
            notes.append("Timestamp values could not be parsed; returned a single trip using file row order.")
            trip_metadata = TripMetadata(
                trip_id=f"{Path(source_name).stem}_trip_001",
                source_filename=source_name,
                source_path=source_path,
                vehicle_id=vehicle.vehicle_id,
                vehicle_make=vehicle.make,
                vehicle_model=vehicle.model,
                segment_index=1,
                row_count=len(dataframe),
                start_timestamp=None,
                end_timestamp=None,
            )
            return [(ProcessedTrip(metadata=trip_metadata, dataframe=self._attach_trip_columns(dataframe.copy(), trip_metadata)))], notes

        trip_frames: list[pd.DataFrame] = []
        trip_start_index = 0
        gap_threshold = self.trip_gap_minutes * 60

        for current_index in range(1, len(dataframe)):
            previous_timestamp = parsed_timestamps.iloc[current_index - 1]
            current_timestamp = parsed_timestamps.iloc[current_index]
            if pd.isna(previous_timestamp) or pd.isna(current_timestamp):
                continue

            gap_seconds = (current_timestamp - previous_timestamp).total_seconds()
            if gap_seconds > gap_threshold:
                trip_frames.append(dataframe.iloc[trip_start_index:current_index].copy())
                trip_start_index = current_index

        trip_frames.append(dataframe.iloc[trip_start_index:].copy())

        processed_trips: list[ProcessedTrip] = []
        for segment_index, trip_frame in enumerate(trip_frames, start=1):
            trip_timestamps = parse_timestamps(trip_frame["Timestamp"])
            valid_timestamps = trip_timestamps.dropna()
            trip_metadata = TripMetadata(
                trip_id=f"{Path(source_name).stem}_trip_{segment_index:03d}",
                source_filename=source_name,
                source_path=source_path,
                vehicle_id=vehicle.vehicle_id,
                vehicle_make=vehicle.make,
                vehicle_model=vehicle.model,
                segment_index=segment_index,
                row_count=len(trip_frame),
                start_timestamp=valid_timestamps.iloc[0].isoformat() if not valid_timestamps.empty else None,
                end_timestamp=valid_timestamps.iloc[-1].isoformat() if not valid_timestamps.empty else None,
            )
            processed_trips.append(
                ProcessedTrip(
                    metadata=trip_metadata,
                    dataframe=self._attach_trip_columns(trip_frame, trip_metadata),
                )
            )

        if parsed_timestamps.isna().any():
            notes.append("Some Timestamp values could not be parsed and were ignored when checking time gaps.")

        return processed_trips, notes

    @staticmethod
    def _attach_trip_columns(dataframe: pd.DataFrame, metadata: TripMetadata) -> pd.DataFrame:
        dataframe["trip_id"] = metadata.trip_id
        dataframe["vehicle_id"] = metadata.vehicle_id
        dataframe["vehicle_make"] = metadata.vehicle_make
        dataframe["vehicle_model"] = metadata.vehicle_model
        dataframe["source_filename"] = metadata.source_filename
        return dataframe


def serialize_validation_report(report: ValidationReport) -> dict[str, Any]:
    return asdict(report)


def serialize_trip_metadata(trip: ProcessedTrip) -> dict[str, Any]:
    return asdict(trip.metadata)


def write_debug_output(result: BatchProcessingResult, output_dir: str | Path) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    trips_dir = destination / "trips"
    trips_dir.mkdir(exist_ok=True)

    audit_payload = [serialize_validation_report(report) for report in result.audit_log]
    (destination / "ingestion_audit.json").write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")

    trip_manifest: list[dict[str, Any]] = []
    for dataset in result.processed_datasets:
        if dataset.validation.status != "accepted":
            continue

        for trip in dataset.trips:
            trip_file_name = f"{trip.metadata.trip_id}.csv"
            trip.dataframe.to_csv(trips_dir / trip_file_name, index=False)
            trip_manifest.append(serialize_trip_metadata(trip))

    (destination / "trip_manifest.json").write_text(json.dumps(trip_manifest, indent=2), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate OBD CSV files and segment them into trips for debugging or batch preprocessing."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        default="data_samples/10.35097-1130/data/dataset/OBD-II-Dataset",
        help="CSV file or folder containing CSV files to process.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for debug artifacts such as audit logs and segmented trip CSV files.",
    )
    parser.add_argument(
        "--gap-minutes",
        type=int,
        default=TRIP_GAP_MINUTES,
        help="Trip split threshold in minutes. Default: 10.",
    )
    return parser


def summarize_batch(result: BatchProcessingResult) -> str:
    accepted = sum(1 for item in result.audit_log if item.status == "accepted")
    rejected = len(result.audit_log) - accepted
    trip_count = sum(len(dataset.trips) for dataset in result.processed_datasets)
    lines = [
        f"Files processed: {len(result.audit_log)}",
        f"Accepted: {accepted}",
        f"Rejected: {rejected}",
        f"Trips identified: {trip_count}",
    ]

    for report in result.audit_log:
        if report.status == "rejected":
            lines.append(
                f"REJECTED {report.filename}: missing {', '.join(report.missing_fields)}"
            )

    return "\n".join(lines)


def cli_main(argv: Iterable[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    pipeline = PreprocessingPipeline(trip_gap_minutes=args.gap_minutes)
    result = pipeline.ingest_path(args.input_path)
    print(summarize_batch(result))

    if args.output_dir:
        write_debug_output(result, args.output_dir)
        print(f"Debug output written to {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())