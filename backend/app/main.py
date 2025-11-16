from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
from PIL import Image
import io
from datetime import datetime
import fitz  # PyMuPDF
import tempfile
import json

from services.detection_services import DigitalInspector

app = FastAPI(title="StampNSign API", version="1.0.0")

# CORS для фронтенда
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация детектора
print("🚀 Инициализация StampNSign API...")
inspector = DigitalInspector()
print("✅ Все модели загружены")

# Директории
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def serialize_detections(detections):
    """Сериализует детекции в JSON-совместимый формат"""
    serialized = []
    for detection in detections:
        serialized.append({
            'label': str(detection['label']),
            'bbox': [float(coord) for coord in detection['bbox']],
            'confidence': float(detection['confidence'])
        })
    return serialized

def pdf_to_images(pdf_file):
    """Конвертирует PDF в список изображений"""
    images = []
    
    # Сохраняем временный файл PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_file)
        tmp_path = tmp_file.name
    
    try:
        # Открываем PDF с помощью PyMuPDF
        pdf_document = fitz.open(tmp_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Увеличиваем разрешение
            img_data = pix.tobytes("ppm")
            
            # Конвертируем в PIL Image
            image = Image.open(io.BytesIO(img_data))
            # Конвертируем в RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            images.append(image)
        
        pdf_document.close()
        
    finally:
        # Удаляем временный файл
        os.unlink(tmp_path)
    
    return images

@app.get("/")
async def root():
    return {"message": "StampNSign API", "status": "running"}

@app.post("/api/detect/all")
async def detect_all(file: UploadFile = File(...)):
    """Обнаружение всех элементов на изображении или PDF"""
    try:
        print(f"📥 Получен файл: {file.filename}")
        file_content = await file.read()
        
        # Определяем тип файла
        if file.filename.lower().endswith('.pdf'):
            print("📄 Обработка PDF файла...")
            # Обработка PDF
            images = pdf_to_images(file_content)
            results = []
            
            for i, image in enumerate(images):
                print(f"🔍 Анализ страницы {i+1}...")
                
                # Детекция всех элементов
                signatures = serialize_detections(inspector.detect_signatures(image))
                qr_codes = serialize_detections(inspector.detect_qr_codes(image))
                stamps = serialize_detections(inspector.detect_stamps(image))
                
                # Сохранение результата с bounding boxes
                result_image = inspector.draw_detections(image, signatures + qr_codes + stamps)
                
                # Сохраняем изображение результата
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
            
            total_counts = {
                "signatures": sum(len(page["detections"]["signatures"]) for page in results),
                "qr_codes": sum(len(page["detections"]["qr_codes"]) for page in results),
                "stamps": sum(len(page["detections"]["stamps"]) for page in results)
            }
            
            print(f"✅ PDF обработан: {len(images)} страниц, найдено {total_counts}")
            
            return {
                "success": True,
                "file_type": "pdf",
                "total_pages": len(images),
                "pages": results,
                "total_counts": total_counts
            }
            
        else:
            print("🖼️ Обработка изображения...")
            # Обработка изображения
            image = Image.open(io.BytesIO(file_content))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Детекция всех элементов
            signatures = serialize_detections(inspector.detect_signatures(image))
            qr_codes = serialize_detections(inspector.detect_qr_codes(image))
            stamps = serialize_detections(inspector.detect_stamps(image))
            
            # Сохранение результата с bounding boxes
            result_image = inspector.draw_detections(image, signatures + qr_codes + stamps)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"result_{timestamp}.jpg"
            output_path = UPLOAD_DIR / output_filename
            result_image.save(output_path)
            
            result_data = {
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
            
            print(f"✅ Изображение обработано: {result_data['counts']}")
            
            return result_data
        
    except Exception as e:
        print(f"❌ Ошибка при обработке файла: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/health")
async def health_check():
    """Проверка статуса API и моделей"""
    return {
        "status": "healthy",
        "models_loaded": {
            "signatures": True,
            "qr_codes": True,
            "stamps": inspector.stamp_detector is not None and inspector.stamp_detector.model is not None
        },
        "supported_formats": ["jpg", "jpeg", "png", "pdf"]
    }

# Статические файлы для доступа к обработанным изображениям
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    print("🌐 Запуск сервера на http://localhost:8000")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
