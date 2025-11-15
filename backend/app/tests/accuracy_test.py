# test_qr_final.py - РАБОЧИЙ ТЕСТ
import sys
from pathlib import Path
from PIL import Image
import fitz
import io
import cv2

# === ИСПРАВЛЕННАЯ КОНФИГУРАЦИЯ ПУТЕЙ ===
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print(f"🌳 PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📂 Путь к services: {PROJECT_ROOT / 'services'}")
print(f"📂 Путь к models: {PROJECT_ROOT / 'models'}")

from services.detection_services import DigitalInspector

def test_single_page():
    """Тест одной страницы с максимальной отладкой"""
    print("\n" + "="*60)
    print("🔍 ТЕСТ ОТДЕЛЬНОЙ СТРАНИЦЫ")
    print("="*60)
    
    # Абсолютный путь к PDF
    pdf_path = PROJECT_ROOT / 'selected_output' / 'pdfs' / 'АПЗ-2.pdf'
    
    if not pdf_path.exists():
        print(f"❌ Файл не найден: {pdf_path}")
        print(f"📂 Содержимое папки:")
        for f in (PROJECT_ROOT / 'selected_output' / 'pdfs').glob('*'):
            print(f"   - {f.name}")
        return
    
    print(f"✅ Найден PDF: {pdf_path}")
    
    # Открываем PDF
    doc = fitz.open(pdf_path)
    page = doc[0]  # Первая страница
    
    # Пробуем разные разрешения
    for zoom in [2, 3, 4, 5]:
        print(f"\n{'-'*50}")
        print(f"🔄 TEST: Zoom {zoom}x")
        print(f"{'-'*50}")
        
        # Конвертируем в изображение
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img_data = pix.tobytes("ppm")
        image = Image.open(io.BytesIO(img_data))
        
        print(f"📐 Разрешение: {image.width}x{image.height}")
        print(f"🎨 Режим: {image.mode}")
        
        # Сохраняем для ручной проверки
        debug_img_path = PROJECT_ROOT / 'tests' / f'debug_zoom{zoom}.jpg'
        image.save(debug_img_path, quality=95)
        print(f"💾 Сохранено: {debug_img_path}")
        
        # Инициализируем детектор
        inspector = DigitalInspector()
        
        # ДЕТЕКЦИЯ QR-КОДОВ
        print("\n📱 Детекция QR-кодов...")
        qr_results = inspector.detect_qr_codes(image)
        
        if len(qr_results) > 0:
            print(f"✅ НАЙДЕНО QR-КОДОВ: {len(qr_results)}")
            
            for i, qr in enumerate(qr_results):
                bbox = qr['bbox']
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                print(f"   QR #{i+1}: conf={qr['confidence']:.4f}, area={area:.0f}px²")
                print(f"   Координаты: {bbox}")
            
            # Детектируем остальное
            signatures = inspector.detect_signatures(image)
            stamps = inspector.detect_stamps(image)
            
            print(f"✍️ Подписи: {len(signatures)}")
            print(f"🛡️ Штампы: {len(stamps)}")
            
            # Создаём визуализацию
            all_detections = []
            all_detections.extend(qr_results)
            all_detections.extend(signatures)
            all_detections.extend(stamps)
            
            visualized = inspector.draw_detections(image, all_detections)
            output_path = PROJECT_ROOT / 'tests' / f'result_zoom{zoom}.jpg'
            visualized.save(output_path, quality=95)
            print(f"🎨 Визуализация: {output_path}")
            
            break  # Выходим из цикла zoom
        else:
            print("❌ QR-коды не найдены")
    
    doc.close()

def test_multiple_pdfs():
    """Тест нескольких PDF файлов"""
    print("\n" + "="*60)
    print("📂 ТЕСТ НЕСКОЛЬКИХ PDF")
    print("="*60)
    
    pdfs_dir = PROJECT_ROOT / 'selected_output' / 'pdfs'
    pdf_files = list(pdfs_dir.glob('*.pdf'))
    
    print(f"📄 Найдено PDF файлов: {len(pdf_files)}")
    
    if not pdf_files:
        print("❌ PDF файлы не найдены!")
        return
    
    inspector = DigitalInspector()
    
    for pdf_path in pdf_files[:3]:  # Тест первых 3 файлов
        print(f"\n{'-'*40}")
        print(f"📄 Обработка: {pdf_path.name}")
        print(f"{'-'*40}")
        
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            doc.close()
            
            # Детекция
            qr = inspector.detect_qr_codes(image)
            sigs = inspector.detect_signatures(image)
            stamps = inspector.detect_stamps(image)
            
            print(f"   QR: {len(qr)} | Подписи: {len(sigs)} | Штампы: {len(stamps)}")
            
            if len(qr) + len(sigs) + len(stamps) > 0:
                # Сохраняем результат
                all_detections = []
                all_detections.extend(qr)
                all_detections.extend(sigs)
                all_detections.extend(stamps)
                
                visualized = inspector.draw_detections(image, all_detections)
                output_path = PROJECT_ROOT / 'tests' / f'{pdf_path.stem}_result.jpg'
                visualized.save(output_path, quality=95)
                print(f"   💾 Сохранено: {output_path}")
            else:
                print("   ⚠️ Объекты не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка обработки {pdf_path.name}: {e}")

if __name__ == "__main__":
    test_single_page()
    test_multiple_pdfs()
    
    print("\n" + "✅ Тесты завершены!")
    print("\n📂 Проверьте результаты в папке:", PROJECT_ROOT / 'tests')
    