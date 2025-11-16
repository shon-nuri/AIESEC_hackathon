import os
from pathlib import Path
from fastapi import HTTPException, status
from pdf2image import convert_from_path
from pypdf import PdfReader

from backend.app.services.detection_services import DigitalInspector





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
    for page_result in results:
        print("Page:", page_result["page"])
        for det in page_result["detections"]:
            print(det)
