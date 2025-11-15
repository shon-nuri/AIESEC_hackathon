# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import tempfile
from pathlib import Path
from services.detection_services import digital_inspector
from utils.pdf_processor import PDFProcessor

app = FastAPI(title="Digital Inspector API", version="1.0.0")

# Монтируем статические файлы
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

processor = PDFProcessor()

@app.post("/api/inspect")
async def inspect_document(file: UploadFile = File(...)):
    """API endpoint для инспекции документов"""
    try:
        # Сохраняем загруженный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        # Обрабатываем файл
        results = processor.process_pdf(tmp_path)
        
        # Удаляем временный файл
        tmp_path.unlink()
        
        return {
            "status": "success",
            "results": results,
            "message": f"Обработано {len(results)} страниц"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Digital Inspector API", "status": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)