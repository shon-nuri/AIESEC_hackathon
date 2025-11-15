# test_final.py - ТОЛЬКО PyMuPDF, без poppler
import os
import sys
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import io

# Добавляем пути для импорта
sys.path.append(str(Path(__file__).parent.parent))

def find_pdfs_directory():
    """Находит папку с PDF файлами"""
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

def pdf_to_images_pymupdf(pdf_path):
    """Конвертация PDF в изображения используя PyMuPDF"""
    try:
        import fitz
        print("   📄 Конвертация PDF через PyMuPDF...")
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num, page in enumerate(doc):
            # Создаем матрицу для увеличения DPI
            mat = fitz.Matrix(2, 2)  # 2x масштаб = ~150 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Конвертируем в PIL Image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
            
        doc.close()
        print(f"   ✅ Успешно конвертировано {len(images)} страниц")
        return images
        
    except Exception as e:
        print(f"❌ Ошибка конвертации PDF: {e}")
        raise

# Импортируем наш инспектор
try:
    from detection_services import DigitalInspector
    print("✅ Успешно импортирован DigitalInspector")
except ImportError as e:
    print(f"❌ Не могу импортировать detection_services: {e}")
    sys.exit(1)

def run_test():
    print("🚀 Запуск теста Digital Inspector (PyMuPDF only)")
    print("=" * 60)
    
    # Находим PDF файлы
    pdfs_dir = find_pdfs_directory()
    if pdfs_dir is None:
        print("❌ Папка с PDF не найдена!")
        return
    
    pdf_files = list(pdfs_dir.glob('*.pdf'))
    
    if not pdf_files:
        print("❌ PDF файлы не найдены!")
        return
    
    print(f"📁 Найдено PDF файлов: {len(pdf_files)}")
    
    # Создаем инспектор
    print("\n🔄 Инициализация Digital Inspector...")
    inspector = DigitalInspector()
    print("✅ Все модели загружены!")
    
    # Тестируем первые 3 файла
    for pdf_path in pdf_files[:3]:
        print(f"\n{'='*60}")
        print(f"🔍 Анализ: {pdf_path.name}")
        print(f"{'='*60}")
        
        try:
            # Конвертируем PDF
            images = pdf_to_images_pymupdf(pdf_path)
            
            total_sig = 0
            total_qr = 0
            total_stamp = 0
            
            for i, image in enumerate(images):
                print(f"   📖 Страница {i+1}/{len(images)}...")
                
                # Детектируем объекты
                signatures = inspector.detect_signatures(image)
                qr_codes = inspector.detect_qr_codes(image)
                stamps = inspector.detect_stamps(image)
                
                print(f"      📊 Подписи: {len(signatures)}, QR-коды: {len(qr_codes)}, Штампы: {len(stamps)}")
                
                # Показываем детали обнаружений
                if signatures:
                    for sig in signatures[:3]:  # Покажем первые 3
                        print(f"        ✍️ Подпись: conf={sig['confidence']:.3f}")
                
                if qr_codes:
                    for qr in qr_codes:
                        print(f"        📱 QR-код: conf={qr['confidence']:.3f}")
                
                if stamps:
                    for stamp in stamps[:3]:  # Покажем первые 3
                        print(f"        🛡️ Штамп: conf={stamp['confidence']:.3f}")
                
                total_sig += len(signatures)
                total_qr += len(qr_codes)
                total_stamp += len(stamps)
                
                # Сохраняем результат если есть обнаружения
                if signatures or qr_codes or stamps:
                    result_image = inspector.draw_detections(
                        image, signatures + qr_codes + stamps
                    )
                    output_path = f"result_{pdf_path.stem}_page_{i+1}.jpg"
                    result_image.save(output_path, quality=90)
                    print(f"      💾 Сохранено: {output_path}")
            
            print(f"\n   📈 ИТОГО по файлу:")
            print(f"      Подписи: {total_sig}")
            print(f"      QR-коды: {total_qr}") 
            print(f"      Штампы: {total_stamp}")
                  
        except Exception as e:
            print(f"❌ Ошибка обработки {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()