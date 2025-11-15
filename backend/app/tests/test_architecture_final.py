# backend/app/tests/test_architecture_final.py
import sys
from pathlib import Path
from PIL import Image
import fitz
import io

# === КРИТИЧЕСКАЯ КОРРЕКТИРОВКА ПУТЕЙ ===
# Скрипт в: backend/app/tests/
# Нужно подняться до: selected_output/pdfs/

# Поднимаемся от backend/app/tests/ до aiesec_hackathon/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Добавляем в sys.path
sys.path.insert(0, str(PROJECT_ROOT))

print("="*70)
print("🔧 ДИАГНОСТИКА ПУТЕЙ ДЛЯ ВАШЕЙ АРХИТЕКТУРЫ")
print("="*70)
print(f"📂 Текущая директория: {Path.cwd()}")
print(f"📂 PROJECT_ROOT: {PROJECT_ROOT}")
print(f"📂 Проверяем PDFS_DIR: {PROJECT_ROOT / 'selected_output' / 'pdfs'}")

# Проверяем critical пути
CRITICAL_PATHS = {
    'services': PROJECT_ROOT / 'backend' / 'app' / 'services',
    'models': PROJECT_ROOT / 'backend' / 'app' / 'models' / 'best.pt',
    'tests': PROJECT_ROOT / 'backend' / 'app' / 'tests',
    'pdfs': PROJECT_ROOT / 'selected_output' / 'pdfs'
}

for name, path in CRITICAL_PATHS.items():
    status = "✅ СУЩЕСТВУЕТ" if path.exists() else "❌ НЕТ"
    print(f"   {name:12} → {path} {status}")

print("="*70)

# ИМПОРТ
try:
    from backend.app.services.detection_services import DigitalInspector
    print("✅ Импорт успешен через полный путь")
except ImportError:
    try:
        from services.detection_services import DigitalInspector
        print("✅ Импорт успешен через относительный путь")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def convert_pdf_to_image(pdf_path: Path, page_num: int = 0, zoom: int = 3) -> Image.Image:
    """Конвертирует PDF в изображение"""
    print(f"\n📄 Открытие: {pdf_path.name}")
    print(f"📄 Страница: {page_num + 1}, Zoom: {zoom}x")
    
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    
    print(f"📊 Разрешение: {pix.width}x{pix.height}")
    
    img_data = pix.tobytes("ppm")
    image = Image.open(io.BytesIO(img_data))
    doc.close()
    
    return image

def save_debug_image(image: Image.Image, name: str):
    """Сохраняет промежуточное изображение"""
    debug_path = PROJECT_ROOT / 'backend' / 'app' / 'tests' / f'debug_{name}.jpg'
    image.save(debug_path, quality=95)
    print(f"💾 Сохранено: {debug_path}")

def test_pdf_processing():
    """ОСНОВНОЙ ТЕСТ"""
    print("\n" + "="*70)
    print("🚀 ТЕСТ ОБРАБОТКИ PDF")
    print("="*70)
    
    # !!! ИЗМЕНЁННЫЙ ПУТЬ К PDF !!!
    pdf_path = PROJECT_ROOT / 'selected_output' / 'pdfs' / 'АПЗ-2.pdf'
    
    if not pdf_path.exists():
        print(f"❌ PDF НЕ НАЙДЕН: {pdf_path}")
        print("📂 Доступные файлы:")
        
        pdfs_dir = PROJECT_ROOT / 'selected_output' / 'pdfs'
        if pdfs_dir.exists():
            for pdf in pdfs_dir.glob('*.pdf'):
                print(f"   📄 {pdf.name}")
                # Предлагаем использовать первый найденный
                if 'pdf_path' not in locals():
                    pdf_path = pdf
        else:
            print(f"❌ Папка не существует: {pdfs_dir}")
            return
    
    print(f"✅ Будет обработан: {pdf_path}")
    
    # Инициализация
    inspector = DigitalInspector()
    
    # Тест разных разрешений
    for zoom in [2, 3, 4]:
        print(f"\n{'='*50}")
        print(f"🔍 ZOOM: {zoom}x")
        print(f"{'='*50}")
        
        image = convert_pdf_to_image(pdf_path, zoom=zoom)
        save_debug_image(image, f"zoom{zoom}")
        
        # Детекция QR
        print("\n📱 Тест QR-кодов...")
        qr_results = inspector.detect_qr_codes(image)
        
        if qr_results:
            print(f"✅ НАЙДЕНО: {len(qr_results)} QR-кодов")
            
            for i, qr in enumerate(qr_results):
                bbox = qr['bbox']
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                print(f"   QR #{i+1}: conf={qr['confidence']:.4f}, area={area:.0f}px²")
            
            # Визуализация
            visualized = inspector.draw_detections(image, qr_results)
            result_path = PROJECT_ROOT / 'backend' / 'app' / 'tests' / f'qr_zoom{zoom}.jpg'
            visualized.save(result_path, quality=95)
            print(f"🎨 Сохранено: {result_path}")
            
            # Детектируем всё остальное
            signatures = inspector.detect_signatures(image)
            stamps = inspector.detect_stamps(image)
            
            print(f"\n✍️ Подписи: {len(signatures)}")
            print(f"🛡️ Штампы: {len(stamps)}")
            
            all_detections = []
            all_detections.extend(qr_results)
            all_detections.extend(signatures)
            all_detections.extend(stamps)
            
            visualized = inspector.draw_detections(image, all_detections)
            final_path = PROJECT_ROOT / 'backend' / 'app' / 'tests' / f'final_zoom{zoom}.jpg'
            visualized.save(final_path, quality=95)
            print(f"\n🎨 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ: {final_path}")
            
            break
        else:
            print("❌ QR не найдены, пробуем следующий zoom...")

def test_multiple_files():
    """Тест нескольких PDF"""
    print("\n" + "="*70)
    print("📂 ТЕСТ НЕСКОЛЬКИХ ФАЙЛОВ")
    print("="*70)
    
    pdfs_dir = PROJECT_ROOT / 'selected_output' / 'pdfs'
    pdf_files = list(pdfs_dir.glob('*.pdf'))
    
    print(f"📊 Найдено PDF: {len(pdf_files)}")
    
    if not pdf_files:
        print("❌ Нет файлов для теста")
        return
    
    inspector = DigitalInspector()
    
    for pdf_path in pdf_files[:3]:
        print(f"\n{'-'*50}")
        print(f"📄 {pdf_path.name}")
        print(f"{'-'*50}")
        
        try:
            image = convert_pdf_to_image(pdf_path, zoom=3)
            
            qr = inspector.detect_qr_codes(image)
            sigs = inspector.detect_signatures(image)
            stamps = inspector.detect_stamps(image)
            
            print(f"   📱 QR: {len(qr)} | ✍️ Подписи: {len(sigs)} | 🛡️ Штампы: {len(stamps)}")
            
            if len(qr) + len(sigs) + len(stamps) > 0:
                all_detections = []
                all_detections.extend(qr)
                all_detections.extend(sigs)
                all_detections.extend(stamps)
                
                visualized = inspector.draw_detections(image, all_detections)
                safe_name = pdf_path.stem.replace(' ', '_')
                output_path = PROJECT_ROOT / 'backend' / 'app' / 'tests' / f'{safe_name}.jpg'
                visualized.save(output_path, quality=95)
                print(f"   💾 Сохранено: {output_path}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_pdf_processing()
    test_multiple_files()
    
    print("\n" + "✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
    print(f"\n📂 Результаты в: {PROJECT_ROOT / 'backend' / 'app' / 'tests'}")
    