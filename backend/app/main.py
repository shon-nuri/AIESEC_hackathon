import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import tempfile

# Импорты для обработки изображений
from PIL import Image
import io
import fitz
from datetime import datetime

try:
    from detection_services import DigitalInspector
    HAS_MODELS = True
except Exception as e:
    print(f"⚠️ Модели не загружены: {e}")
    HAS_MODELS = False

app = FastAPI(
    title="StampNSign API",
    description="API для детекции подписей, QR-кодов и штампов",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация детектора
inspector = None

@app.on_event("startup")
async def startup_event():
    global inspector
    if HAS_MODELS:
        try:
            print("🚀 Инициализация StampNSign API...")
            inspector = DigitalInspector()
            print("✅ Все модели загружены")
        except Exception as e:
            print(f"❌ Ошибка загрузки моделей: {e}")
            inspector = None
    else:
        print("⚠️ Запуск без моделей")

# Создаем временную директорию для загрузок
UPLOAD_DIR = Path(tempfile.gettempdir()) / "stampnsign_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def serialize_detections(detections):
    """Сериализует детекции в JSON-совместимый формат"""
    return [{
        'label': str(det['label']),
        'bbox': [float(coord) for coord in det['bbox']],
        'confidence': float(det['confidence'])
    } for det in detections]

@app.get("/")
async def root():
    return {
        "message": "StampNSign API", 
        "status": "running",
        "models_loaded": inspector is not None
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy" if inspector else "degraded",
        "models_loaded": inspector is not None,
        "message": "API работает" if inspector else "API работает, но модели не загружены"
    }

@app.post("/api/detect/all")
async def detect_all(file: UploadFile = File(...)):
    if inspector is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Models are not available"}
        )
    
    try:
        file_content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            # Обработка PDF (ваш существующий код)
            images = pdf_to_images(file_content)
            results = []
            
            for i, image in enumerate(images):
                signatures = serialize_detections(inspector.detect_signatures(image))
                qr_codes = serialize_detections(inspector.detect_qr_codes(image))
                stamps = serialize_detections(inspector.detect_stamps(image))
                
                result_image = inspector.draw_detections(image, signatures + qr_codes + stamps)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"result_page_{i+1}_{timestamp}.jpg"
                output_path = UPLOAD_DIR / output_filename
                result_image.save(output_path)
                
                results.append({
                    "page": i + 1,
                    "detections": {
                        "signatures": signatures,
                        "qr_codes": qr_codes,
                        "stamps": stamps
                    },
                    "result_image_url": f"/uploads/{output_filename}",
                    "counts": {
                        "signatures": len(signatures),
                        "qr_codes": len(qr_codes),
                        "stamps": len(stamps)
                    }
                })
            
            return {
                "success": True,
                "file_type": "pdf",
                "total_pages": len(images),
                "pages": results
            }
        else:
            # Обработка изображения
            image = Image.open(io.BytesIO(file_content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            signatures = serialize_detections(inspector.detect_signatures(image))
            qr_codes = serialize_detections(inspector.detect_qr_codes(image))
            stamps = serialize_detections(inspector.detect_stamps(image))
            
            result_image = inspector.draw_detections(image, signatures + qr_codes + stamps)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"result_{timestamp}.jpg"
            output_path = UPLOAD_DIR / output_filename
            result_image.save(output_path)
            
            return {
                "success": True,
                "file_type": "image",
                "detections": {
                    "signatures": signatures,
                    "qr_codes": qr_codes,
                    "stamps": stamps
                },
                "result_image_url": f"/uploads/{output_filename}",
                "counts": {
                    "signatures": len(signatures),
                    "qr_codes": len(qr_codes),
                    "stamps": len(stamps)
                }
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Статические файлы
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Функция для обработки PDF (добавьте вашу существующую функцию)
def pdf_to_images(pdf_file):
    images = []
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file)
        tmp_path = tmp_file.name
    
    try:
        pdf_document = fitz.open(tmp_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            images.append(image)
        pdf_document.close()
    finally:
        os.unlink(tmp_path)
    
    return images

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
    