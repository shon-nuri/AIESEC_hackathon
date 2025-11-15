# test_real_pdfs_fixed.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import os
import sys
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

# Добавляем пути для импорта
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.path_utils import find_pdfs_directory, find_model_file
except ImportError:
    print("❌ Не могу импортировать utils, создаем временные функции...")
    
    def find_pdfs_directory():
        current_dir = Path(__file__).parent
        possible_locations = [
            current_dir.parent.parent.parent / 'selected_output' / 'pdfs',
            current_dir / 'test_data',
        ]
        
        for location in possible_locations:
            if location.exists():
                pdf_files = list(location.glob('*.pdf'))
                if pdf_files:
                    print(f"✅ Найдены PDF в: {location}")
                    return location
        return None

# ИМПОРТИРУЕМ convert_from_path правильно!
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("⚠️ pdf2image не установлен, используем PyMuPDF")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("❌ PyMuPDF не установлен")

# Импортируем наши детекторы
try:
    from detection_services import DigitalInspector
except ImportError:
    print("❌ Не могу импортировать detection_service, создаем минимальную версию...")
    
    # Минимальная версия детекторов
    from transformers import pipeline
    from qrdet import QRDetector
    from ultralytics import YOLO
    
    class DigitalInspector:
        def __init__(self):
            print("🔄 Загрузка модели подписей...")
            self.signature_detector = pipeline(
                "object-detection", 
                model="mdefrance/yolos-base-signature-detection"
            )
            
            print("🔄 Загрузка модели QR-кодов...")
            self.qr_detector = QRDetector(model_size='s')
            
            print("🔄 Загрузка модели штампов...")
            try:
                model_path = find_model_file('best.pt')
                if model_path:
                    self.stamp_detector = YOLO(model_path)
                else:
                    self.stamp_detector = None
                    print("⚠️ Модель штампов не загружена")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки модели штампов: {e}")
                self.stamp_detector = None
        
        def detect_signatures(self, image):
            try:
                results = self.signature_detector(image)
                detections = []
                for result in results:
                    box = result['box']
                    detections.append({
                        'label': 'signature',
                        'bbox': [box['xmin'], box['ymin'], box['xmax'], box['ymax']],
                        'confidence': result['score']
                    })
                return detections
            except Exception as e:
                print(f"❌ Ошибка детекции подписей: {e}")
                return []
        
        def detect_qr_codes(self, image):
            try:
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                detections = self.qr_detector.detect(image=opencv_image, is_bgr=True, legacy=True)
                
                results = []
                for detection in detections:
                    results.append({
                        'label': 'qr_code',
                        'bbox': detection['bbox_xyxy'],
                        'confidence': detection['confidence']
                    })
                return results
            except Exception as e:
                print(f"❌ Ошибка детекции QR-кодов: {e}")
                return []
        
        def detect_stamps(self, image):
            if not self.stamp_detector:
                return []
            try:
                results = self.stamp_detector(image)
                detections = []
                
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append({
                            'label': 'stamp',
                            'bbox': [x1, y1, x2, y2],
                            'confidence': box.conf.item()
                        })
                return detections
            except Exception as e:
                print(f"❌ Ошибка детекции штампов: {e}")
                return []
        
        def draw_detections(self, image, detections):
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            colors = {
                'signature': (255, 0, 0),    # Красный
                'qr_code': (0, 255, 0),      # Зеленый  
                'stamp': (0, 0, 255),        # Синий
            }
            
            for detection in detections:
                label = detection['label']
                bbox = detection['bbox']
                confidence = detection.get('confidence', 0)
                color = colors.get(label, (128, 128, 128))
                
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color, 3)
                
                label_text = f"{label} {confidence:.2f}"
                cv2.putText(opencv_image, label_text, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            return Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))

def find_model_file(filename):
    """Ищет файл модели"""
    current_dir = Path(__file__).parent
    possible_locations = [
        current_dir.parent.parent.parent / 'models' / filename,
        current_dir.parent.parent / 'models' / filename,
        current_dir / filename,
    ]
    
    for location in possible_locations:
        if location.exists():
            print(f"✅ Модель найдена: {location}")
            return location
    
    # Рекурсивный поиск
    root_dir = current_dir.parent.parent.parent
    for file_path in root_dir.rglob(filename):
        if file_path.is_file():
            print(f"✅ Найден: {file_path}")
            return file_path
    
    print(f"❌ Файл модели не найден: {filename}")
    return None

def pdf_to_images_safe(pdf_path):
    """Безопасная конвертация PDF"""
    try:
        if PDF2IMAGE_AVAILABLE:
            print("   Используем pdf2image...")
            return convert_from_path(pdf_path, dpi=150)
        elif PYMUPDF_AVAILABLE:
            print("   Используем PyMuPDF...")
            import fitz
            doc = fitz.open(pdf_path)
            images = []
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            doc.close()
            return images
        else:
            raise Exception("Нет доступных PDF конвертеров")
    except Exception as e:
        print(f"❌ Ошибка конвертации PDF: {e}")
        raise

def quick_test():
    print("🚀 Быстрый тест Digital Inspector")
    
    # Проверяем зависимости
    if not PDF2IMAGE_AVAILABLE and not PYMUPDF_AVAILABLE:
        print("❌ Нет доступных PDF конвертеров!")
        return
    
    # Находим PDF файлы
    pdfs_dir = find_pdfs_directory()
    if pdfs_dir is None:
        print("❌ Папка с PDF не найдена!")
        return
    
    pdf_files = list(pdfs_dir.glob('*.pdf'))
    
    if not pdf_files:
        print("❌ PDF файлы не найдены!")
        return
    
    print(f"\n📁 Найдено PDF файлов: {len(pdf_files)}")
    
    # Создаем инспектор
    print("🔄 Инициализация Digital Inspector...")
    inspector = DigitalInspector()
    print("✅ Все модели загружены!")
    
    # Тестируем первые 2 файла
    for pdf_path in pdf_files[:2]:
        print(f"\n{'='*50}")
        print(f"🔍 Анализ: {pdf_path.name}")
        print(f"{'='*50}")
        
        try:
            # Конвертируем PDF
            import io  # Добавляем для PyMuPDF
            images = pdf_to_images_safe(pdf_path)
            print(f"   📄 Страниц: {len(images)}")
            
            total_sig = 0
            total_qr = 0
            total_stamp = 0
            
            for i, image in enumerate(images):
                print(f"   🔎 Анализ страницы {i+1}...")
                
                # Детектируем объекты с обработкой ошибок
                try:
                    signatures = inspector.detect_signatures(image)
                except Exception as e:
                    print(f"      ❌ Ошибка подписей: {e}")
                    signatures = []
                
                try:
                    qr_codes = inspector.detect_qr_codes(image)
                except Exception as e:
                    print(f"      ❌ Ошибка QR-кодов: {e}")
                    qr_codes = []
                
                try:
                    stamps = inspector.detect_stamps(image)
                except Exception as e:
                    print(f"      ❌ Ошибка штампов: {e}")
                    stamps = []
                
                print(f"      📊 Подписи={len(signatures)}, QR={len(qr_codes)}, Штампы={len(stamps)}")
                
                # Покажем детали если есть обнаружения
                if signatures:
                    for sig in signatures:
                        print(f"        ✍️ Подпись: conf={sig['confidence']:.3f}")
                if qr_codes:
                    for qr in qr_codes:
                        print(f"        📱 QR-код: conf={qr['confidence']:.3f}")
                if stamps:
                    for stamp in stamps:
                        print(f"        🛡️ Штамп: conf={stamp['confidence']:.3f}")
                
                total_sig += len(signatures)
                total_qr += len(qr_codes)
                total_stamp += len(stamps)
                
                # Сохраняем результат если есть обнаружения
                if signatures or qr_codes or stamps:
                    try:
                        result_image = inspector.draw_detections(
                            image, signatures + qr_codes + stamps
                        )
                        output_path = f"result_{pdf_path.stem}_page_{i+1}.jpg"
                        result_image.save(output_path, quality=90)
                        print(f"      💾 Сохранено: {output_path}")
                    except Exception as e:
                        print(f"      ❌ Ошибка сохранения: {e}")
            
            print(f"\n   📊 ИТОГО по файлу:")
            print(f"      Подписи: {total_sig}")
            print(f"      QR-коды: {total_qr}")
            print(f"      Штампы: {total_stamp}")
                  
        except Exception as e:
            print(f"❌ Ошибка обработки {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    quick_test()
