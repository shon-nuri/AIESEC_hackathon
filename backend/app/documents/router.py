import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File


router = APIRouter(
    prefix="/documents"
)

UPLOAD_DIR = "files"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def create_upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot save file: {e}")

    return {
        "filename": file.filename, 
        "saved_to": file_location,
        "content_type": file.content_type,
    }