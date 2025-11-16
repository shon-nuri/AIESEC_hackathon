import os
import json
from pathlib import Path
import time
from datetime import datetime
import fitz  # PyMuPDF
import tempfile
import sys
from PIL import Image
import io
import cv2
import numpy as np

# Добавляем пути к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    try:
        from backend.app.detection_services import DigitalInspector
        print("✅ Модели загружены из backend.app.detection_services")
    except ImportError:
        from detection_services import DigitalInspector
        print("✅ Модели загружены из detection_services")
    
    HAS_MODELS = True
except ImportError as e:
    print(f"❌ Ошибка импорта моделей: {e}")
    print("📁 Попытка прямого создания детекторов...")
    HAS_MODELS = False

# Конфигурация путей
PDFS_DIR = Path(r"C:\Users\user\Desktop\Programming\aiesec_hackathon\selected_output\pdfs")
RESULTS_FILE = Path("test_results.json")

def create_detector_directly():
    """Создает детектор напрямую если импорт не работает"""
    try:
        from transformers import pipeline
        from qrdet import QRDetector
        from ultralytics import YOLO
        
        print("🔄 Создание детекторов напрямую...")
        
        class DigitalInspector:
            def __init__(self):
                print("🔄 Загрузка модели подписей...")
                self.signature_detector = pipeline(
                    "object-detection", 
                    model="mdefrance/yolos-base-signature-detection"
                )
                print("✅ Модель подписей загружена")
                
                print("🔄 Загрузка модели QR-кодов...")
                self.qr_detector = QRDetector(model_size='s')
                print("✅ Модель QR-кодов загружена")
                
                print("🔄 Загрузка модели штампов...")
                models_dir = project_root / 'models'
                stamp_model_path = models_dir / 'best.pt'
                if stamp_model_path.exists():
                    self.stamp_detector = YOLO(stamp_model_path)
                    print("✅ Модель штампов загружена")
                else:
                    self.stamp_detector = None
                    print("⚠️ Модель штампов не найдена")
            
            def detect_signatures(self, image):
                try:
                    results = self.signature_detector(image)
                    detections = []
                    for result in results:
                        box = result['box']
                        detections.append({
                            'label': 'signature',
                            'bbox': [float(box['xmin']), float(box['ymin']), float(box['xmax']), float(box['ymax'])],
                            'confidence': float(result['score'])
                        })
                    return detections
                except Exception as e:
                    print(f"❌ Ошибка детекции подписей: {e}")
                    return []
            
            def detect_qr_codes(self, image):
                try:
                    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    detections = self.qr_detector.detect(image=opencv_image, is_bgr=True)
                    
                    results = []
                    for detection in detections:
                        if hasattr(detection, 'bbox_xyxy'):
                            bbox = [float(x) for x in detection.bbox_xyxy]
                            confidence = float(detection.confidence)
                        elif isinstance(detection, dict):
                            bbox = [float(x) for x in detection['bbox_xyxy']]
                            confidence = float(detection['confidence'])
                        else:
                            continue
                        
                        results.append({
                            'label': 'qr_code',
                            'bbox': bbox,
                            'confidence': confidence
                        })
                    return results
                except Exception as e:
                    print(f"❌ Ошибка детекции QR-кодов: {e}")
                    return []
            
            def detect_stamps(self, image):
                if self.stamp_detector is None:
                    return []
                try:
                    results = self.stamp_detector(image)
                    detections = []
                    for result in results:
                        if result.boxes is not None:
                            for box in result.boxes:
                                x1, y1, x2, y2 = map(float, box.xyxy[0])
                                detections.append({
                                    'label': 'stamp',
                                    'bbox': [x1, y1, x2, y2],
                                    'confidence': float(box.conf.item())
                                })
                    return detections
                except Exception as e:
                    print(f"❌ Ошибка детекции штампов: {e}")
                    return []
        
        return DigitalInspector()
    
    except Exception as e:
        print(f"❌ Не удалось создать детекторы: {e}")
        return None

def pdf_to_images(pdf_file):
    """Конвертирует PDF в список изображений"""
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

def test_single_pdf(pdf_path, inspector):
    """Тестирует один PDF файл"""
    try:
        print(f"🔍 Обработка: {pdf_path.name}")
        
        # Читаем PDF файл
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Конвертируем в изображения
        images = pdf_to_images(pdf_content)
        
        pages_results = []
        
        for i, image in enumerate(images):
            start_time = time.time()
            
            # Детекция всех элементов
            signatures = inspector.detect_signatures(image)
            qr_codes = inspector.detect_qr_codes(image)
            stamps = inspector.detect_stamps(image)
            
            processing_time = time.time() - start_time
            
            page_result = {
                "page": i + 1,
                "processing_time": processing_time,
                "detections": {
                    "signatures": signatures,
                    "qr_codes": qr_codes,
                    "stamps": stamps
                },
                "counts": {
                    "signatures": len(signatures),
                    "qr_codes": len(qr_codes),
                    "stamps": len(stamps)
                }
            }
            
            pages_results.append(page_result)
            
            print(f"   📄 Страница {i+1}: {processing_time:.2f}с - "
                  f"✍️{len(signatures)} 📱{len(qr_codes)} 🏷️{len(stamps)}")
        
        return {
            "status": "success",
            "pages": pages_results,
            "total_pages": len(images),
            "total_counts": {
                "signatures": sum(page['counts']['signatures'] for page in pages_results),
                "qr_codes": sum(page['counts']['qr_codes'] for page in pages_results),
                "stamps": sum(page['counts']['stamps'] for page in pages_results)
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка обработки {pdf_path.name}: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def test_all_pdfs():
    """Тестирует все PDF файлы"""
    
    # Находим все PDF файлы
    pdf_files = list(PDFS_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ В папке {PDFS_DIR} не найдено PDF файлов")
        print(f"📁 Содержимое папки: {list(PDFS_DIR.glob('*'))}")
        return
    
    print(f"📁 Найдено {len(pdf_files)} PDF файлов для тестирования")
    
    # Инициализация инспектора
    print("🚀 Инициализация моделей...")
    
    if HAS_MODELS:
        inspector = DigitalInspector()
    else:
        inspector = create_detector_directly()
    
    if inspector is None:
        print("❌ Не удалось инициализировать детекторы")
        return
    
    print("✅ Все модели готовы")
    
    # Результаты тестирования
    test_results = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "pdfs_directory": str(PDFS_DIR),
            "total_files": len(pdf_files),
            "project_root": str(project_root)
        },
        "summary": {
            "successful": 0,
            "failed": 0,
            "total_processing_time": 0,
            "total_signatures": 0,
            "total_qr_codes": 0,
            "total_stamps": 0,
            "total_pages_processed": 0
        },
        "files": []
    }
    
    # Тестируем каждый файл
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n📊 Прогресс: {i}/{len(pdf_files)}")
        
        file_result = {
            "file_name": pdf_path.name,
            "file_size": os.path.getsize(pdf_path),
            "file_path": str(pdf_path)
        }
        
        start_time = time.time()
        result = test_single_pdf(pdf_path, inspector)
        total_time = time.time() - start_time
        
        file_result.update(result)
        file_result["total_processing_time"] = total_time
        
        if result["status"] == "success":
            test_results["summary"]["successful"] += 1
            test_results["summary"]["total_processing_time"] += total_time
            test_results["summary"]["total_signatures"] += result["total_counts"]["signatures"]
            test_results["summary"]["total_qr_codes"] += result["total_counts"]["qr_codes"]
            test_results["summary"]["total_stamps"] += result["total_counts"]["stamps"]
            test_results["summary"]["total_pages_processed"] += result["total_pages"]
        else:
            test_results["summary"]["failed"] += 1
        
        test_results["files"].append(file_result)
        
        # Сохраняем промежуточные результаты после каждого файла
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
    
    # Финальная статистика
    print(f"\n{'='*60}")
    print("📈 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"✅ Успешных файлов: {test_results['summary']['successful']}")
    print(f"❌ Ошибок: {test_results['summary']['failed']}")
    print(f"📄 Всего страниц обработано: {test_results['summary']['total_pages_processed']}")
    print(f"⏱️ Общее время: {test_results['summary']['total_processing_time']:.2f}с")
    print(f"📊 Всего найдено объектов:")
    print(f"   ✍️ Подписей: {test_results['summary']['total_signatures']}")
    print(f"   📱 QR-кодов: {test_results['summary']['total_qr_codes']}")
    print(f"   🏷️ Штампов: {test_results['summary']['total_stamps']}")
    print(f"💾 Результаты сохранены в: {RESULTS_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования PDF файлов")
    print(f"📁 Папка с PDF: {PDFS_DIR}")
    
    # Проверяем существование папки с PDF
    if not PDFS_DIR.exists():
        print(f"❌ Папка {PDFS_DIR} не существует!")
    else:
        test_all_pdfs()
        