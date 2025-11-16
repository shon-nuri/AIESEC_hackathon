import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pypdf import PdfReader
from pathlib import Path
from pdf2image import convert_from_path

from backend.app.services.detection_services import DigitalInspector


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

@router.post("process")
def process_files():
    inspector = DigitalInspector()
    directory_path = 'files/'
    files = os.listdir(directory_path)
    file = os.path.join(directory_path, files[0])
    if not os.path.isfile(file):
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Error with files")
    p = Path(file)
    suffix = p.suffix
    pages = len(PdfReader(file).pages)
    if suffix == ".pdf" and pages > 1:
        pages = convert_from_path(file)
        results = inspector.detect_document_pages(
            pages,
            apply_precise_on_ends=True,
            verbose=True
        )
    

        



@router.get("{id}/export")
def export_files(id: int):
    pass