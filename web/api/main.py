from fastapi import FastAPI, UploadFile, File, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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