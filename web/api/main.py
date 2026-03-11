from fastapi import FastAPI, UploadFile, File, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

import io
import pandas as pd

import sys
from pathlib import Path

import uuid
from pydantic import BaseModel

# add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "Model Development"))
sys.path.append(str(ROOT / "AI Coaching"))

from data_pipeline.ingestion.preprocessing import PreprocessingPipeline
from model_engine import analyse_trip
from granite_coaching import GraniteCoachingService

UPLOAD_STORE = {}  # store uploaded validated trips in-memory, keyed by session_id

# Pydantic model for analysis request
class AnalyseRequest(BaseModel):
    session_id: str

granite_service = GraniteCoachingService()

def validate_csv_upload(contents: bytes, filename: str):
    '''
    Validates the uploaded CSV file by attempting to parse it and then running it through the preprocessing pipeline's validation logic.
    '''
    try:
        df = pd.read_csv(io.BytesIO(contents))

    except Exception as e:
        return False, f"CSV parsing failed: {str(e)}", None

    pipeline = PreprocessingPipeline()
    dataset = pipeline.ingest_dataframe(df, source_name=filename)
    validation = dataset.validation

    if validation.status == "accepted":
        return True, None, dataset

    if validation.missing_fields:
        error = f"Missing columns: {', '.join(validation.missing_fields)}"
    else:
        error = "CSV failed validation"

    return False, error, None

def compute_trip_summary(df, analysis_result):
    """
    Compute a consistent trip summary including:
      - duration_mins
      - distance_km
      - fuel_consumed_liters
      - average_fuel_economy
    """
    # Ensure Timestamp column is datetime
    if "Timestamp" in df.columns and not df["Timestamp"].empty:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        duration_secs = (df["Timestamp"].max() - df["Timestamp"].min()).total_seconds()
        duration_mins = round(duration_secs / 60, 2)
    else:
        duration_mins = 0

    trip_metrics = analysis_result.get("trip_metrics", {})
    avg_speed = trip_metrics.get("average_speed", 0)
    distance_km = round(avg_speed * (duration_mins / 60), 2)

    # Calculate fuel consumed from distance and average fuel economy
    avg_fuel = trip_metrics.get("average_fuel_efficiency", 8.5)
    fuel_consumed = round((distance_km / 100) * avg_fuel, 2)

    # Total fuel in dataframe if available (sum column)
    total_fuel_used = df.get("Fuel Used", pd.Series(dtype=float)).sum() if "Fuel Used" in df.columns else fuel_consumed

    return {
        "duration_mins": duration_mins,
        "distance_km": distance_km,
        "fuel_consumed_liters": fuel_consumed,
        "average_fuel_economy": avg_fuel,
        "total_fuel_used": total_fuel_used
    }

def get_ai_feedback(trip_summary, events):
    """
    Generate AI feedback for a trip, using the precomputed trip_summary.
    Positive feedback comes first, then negative feedback if any inefficiencies exist.
    """
    inefficiencies = [
        {"type": e.get("type", "Unknown"),
         "count": 1,
         "total_duration_secs": e.get("duration", 0)}
        for e in events
    ]

    feedback = []

    # Positive feedback
    try:
        feedback.append(granite_service.generate_positive_reinforcement(trip_summary))
    except Exception as e:
        feedback.append(f"Error generating Positive feedback: {e}")

    # Negative feedback (only if inefficiencies exist)
    if inefficiencies:
        try:
            feedback.append(granite_service.generate_coaching_message(trip_summary, inefficiencies))
        except Exception as e:
            feedback.append(f"Error generating Negative feedback: {e}")

    return feedback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend is running!"}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    '''
    Accepts multiple CSV files, and validates them using the validation logic from the data pipeline. 
    Returns a list of results for each file, indicating whether it was valid or not, and indicates missing fields if applicable.
    '''
    messages = []
    all_valid = True
    session_id = str(uuid.uuid4())
    stored_trips = []

    for file in files:
        contents = await file.read()
        valid, error_message, dataset = validate_csv_upload(contents, file.filename)

        if valid:
            messages.append({"name": file.filename})
            for trip in dataset.trips:
                stored_trips.append(trip)
        else:
            all_valid = False
            messages.append({"name": file.filename, "error": error_message})
    
    if all_valid:
        UPLOAD_STORE[session_id] = stored_trips

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_valid else status.HTTP_400_BAD_REQUEST,
        content={
            "files": messages,
            "session_id": session_id if all_valid else None
        }
    )

@app.post("/analyse")
async def analyse_trips(request: AnalyseRequest):
    '''
    Analyses the uploaded trips for a given session_id, 
    and returns the results in the expected format for the frontend, 
    including AI feedback generated by the GraniteCoachingService.
    '''

    session_id = request.session_id

    if session_id not in UPLOAD_STORE:
        return JSONResponse(status_code=404, content={"error": "Session not found"})

    trip_objects = UPLOAD_STORE[session_id]
    analysis_results = []

    try:
        for trip in trip_objects:
            result = analyse_trip(trip.dataframe)

            trip_summary = compute_trip_summary(trip.dataframe, result)

            ai_feedback = get_ai_feedback(trip_summary, result.get("events", []))

            # map analyse_trip output to frontend expected format
            mapped_result = {
                "trip_id": trip.metadata.trip_id,
                "start_time": trip.metadata.start_timestamp,
                "end_time": trip.metadata.end_timestamp,
                "vehicle_make": trip.metadata.vehicle_make or "Unknown",
                "vehicle_model": trip.metadata.vehicle_model or "Unknown",
                "total_fuel_used": trip.dataframe.get("Fuel Used", 0).sum() if "Fuel Used" in trip.dataframe.columns else 0,
                "average_fuel_economy": result["trip_metrics"].get("average_fuel_efficiency", 0),
                "confidence": "High",  # could compute based on data quality
                "missing_data_percentage": 0,  # optionally calculate missing data %
                "imputed_value_count": 0,  # optionally count imputed values
                "thresholds": {
                    "high_rpm": 3000,
                    "harsh_throttle": 3.0,
                    "hard_braking": -3.0,
                },
                "events": result["events"],
                "efficiency_score": result["efficiency_score"],
                "score_breakdown": result["score_breakdown"],
                "ai_feedback": ai_feedback,
            }

            analysis_results.append(mapped_result)
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Analysis failed: {str(e)}", "trips": []}
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": "Analysis complete",
            "trips": analysis_results
        }
    )