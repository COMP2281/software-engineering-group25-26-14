from fastapi import FastAPI, UploadFile, File, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

import asyncio

def validate_csv_upload(contents: bytes):
    """
    this is for feature 1
    this will call a function that checks if the csv file is in the correct format
    """

    #valid, error = insert_csv_validation_function(contents)

    ## Test code
    import random
    if random.choice([True, False]):
        valid, error = True, None
    else:
        valid, error = False, "Missing Column: 'MAF' (test)"

    return valid, error

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
    messages = []
    all_valid = True

    for file in files:
        contents = await file.read()
        valid, error_message = validate_csv_upload(contents)

        if valid:
            messages.append({"name": file.filename})
        else:
            all_valid = False
            messages.append({"name": file.filename, "error": error_message})

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_valid else status.HTTP_400_BAD_REQUEST,
        content={"files": messages},
    )

@app.post("/analyse")
async def analyse_trips(files: List[UploadFile] = File(...)):
    '''
    this would call the function does the trip analysis
    this function should return a list of dictionaries (one for each trip), with all the data needed for visualisations

    format would be something like:
    [
        {
            "trip_id": "trip1",
            "start_time": "2024-01-01T08:00:00",
            "end_time": "2024-01-01T08:30:00",
            "vehicle_make": "Seat",
            "vehicle_model": "Leon",
            "total_fuel_used": 5.0,
            "average_fuel_economy": 6.0,
            "confidence": "High",
            "missing_data_percentage": 1.5,
            "imputed_value_count": 10,
            "thresholds": {
                "high_rpm": 3000,
                "harsh_throttle": 3.0,
                "hard_braking": 3.0
            },
            "models": {
                ...
            },
            "events": [
                "event1": {
                    "type": "high_rpm",
                    "timestamp": "2024-01-01T08:10:00",
                    "duration": 5,
                    "context": ...
                },
                ...
            "efficiency_score": 85,
            "score_breakdown": {
                "fuel_economy": 90,
                "high_rpm": 80,
                "harsh_throttle": 85,
                "hard_braking": 80
            },
            "ai_feedback": [
                "Negative: Try to avoid high RPMs as they can decrease fuel efficiency.",
                "Positive: You had no hard braking events, which is great for fuel economy! Keep it up!"
                ...
            ]
        },
        ...
    ]
    '''

    #analysis_results = insert_analysis_function(files)

    # test code
    await asyncio.sleep(1)
    import random
    events = ["high_rpm", "hard_braking", "harsh_throttle"]
    confidence_levels = ["High", "Medium", "Low"]

    scores_fuel, scores_rpm, scores_throttle, scores_braking = [random.randint(0, 100) for _ in range(4)]
    efficiency_score = (scores_fuel + scores_rpm + scores_throttle + scores_braking) // 4

    scores_fuel_2, scores_rpm_2, scores_throttle_2, scores_braking_2 = [random.randint(0, 100) for _ in range(4)]
    efficiency_score_2 = (scores_fuel_2 + scores_rpm_2 + scores_throttle_2 + scores_braking_2) // 4

    test_data = [
        {
            "trip_id": "trip1",
            "start_time": "2024-01-01T08:00:00",
            "end_time": "2024-01-01T08:30:00",
            "vehicle_make": "Seat",
            "vehicle_model": "Leon",
            "total_fuel_used": round(random.uniform(2.0, 10.0), 2),
            "average_fuel_economy": round(random.uniform(5.0, 10.0), 2),
            "confidence": random.choice(confidence_levels),
            "missing_data_percentage": round(random.uniform(0, 5), 2),
            "imputed_value_count": random.randint(0, 20),
            "thresholds": {
                "high_rpm": 3000,
                "harsh_throttle": 3.0,
                "hard_braking": 3.0
            },
            "events": [
                {
                    "type": random.choice(events),
                    "timestamp": "2024-01-01T08:10:00",
                    "duration": random.randint(1, 10),
                },
                {
                    "type": random.choice(events),
                    "timestamp": "2024-01-01T08:20:00",
                    "duration": random.randint(1, 10),
                }
            ],
            "efficiency_score": efficiency_score,
            "score_breakdown": {
                "fuel_economy": scores_fuel,
                "high_rpm": scores_rpm,
                "harsh_throttle": scores_throttle,
                "hard_braking": scores_braking
            },
            "ai_feedback": [
                "Negative: Try to avoid high RPMs as they can decrease fuel efficiency.",
                "Positive: You had no hard braking events, which is great for fuel economy! Keep it up!"
            ]
        },
                {
            "trip_id": "trip2",
            "start_time": "2024-01-02T09:00:00",
            "end_time": "2024-01-02T09:30:00",
            "vehicle_make": "Wolkswagen",
            "vehicle_model": "Golf",
            "total_fuel_used": round(random.uniform(2.0, 10.0), 2),
            "average_fuel_economy": round(random.uniform(5.0, 10.0), 2),
            "confidence": random.choice(confidence_levels),
            "missing_data_percentage": round(random.uniform(0, 5), 2),
            "imputed_value_count": random.randint(0, 20),
            "thresholds": {
                "high_rpm": 3000,
                "harsh_throttle": 3.0,
                "hard_braking": 3.0
            },
            "events": [
                {
                    "type": random.choice(events),
                    "timestamp": "2024-01-02T09:10:00",
                    "duration": random.randint(1, 10),
                },
                {
                    "type": random.choice(events),
                    "timestamp": "2024-01-02T09:20:00",
                    "duration": random.randint(1, 10),
                }
            ],
            "efficiency_score": efficiency_score_2,
            "score_breakdown": {
                "fuel_economy": scores_fuel_2,
                "high_rpm": scores_rpm_2,
                "harsh_throttle": scores_throttle_2,
                "hard_braking": scores_braking_2
            },
            "ai_feedback": [
                "Negative: Try to avoid harsh throttle events as they can decrease fuel efficiency.",
                "Positive: Your fuel economy was good! Keep up the good work!"
            ]
        }
    ]

    return JSONResponse(
        status_code=200,
        content={
            "message": "Analysis complete",
            "trips": test_data
        }
    )