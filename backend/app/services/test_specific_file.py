# test_specific_file.py
import os
import sys
from pathlib import Path
import json
from PIL import Image

# Добавляем пути для импорта
sys.path.append(str(Path(__file__).parent.parent))

from detection_services import DigitalInspector

def test_specific_file(pdf_filename):
    """Тестирует конкретный PDF файл"""
    print(f"🔍 Тестируем файл: {pdf_filename}")
    
    # Находим папку с PDF
    current_dir = Path(__file__).parent
    pdfs_dir = current_dir.parent.parent.parent / 'selected_output' / 'pdfs'
    pdf_path = pdfs_dir / pdf_filename
    
    if not pdf_path.exists():
        print(f"❌ Файл не найден: {pdf_path}")
        return
    
    # Создаем инспектор
    inspector = DigitalInspector()
    
    # Конвертируем PDF
    import fitz
    import io
    
    print("📄 Конвертация PDF...")
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num, page in enumerate(doc):
        mat = fitz.Matrix(2, 2)  # 2x масштаб
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    
    doc.close()
    print(f"✅ Конвертировано {len(images)} страниц")
    
    results = {
        "file_name": pdf_filename,
        "total_pages": len(images),
        "pages": []
    }
    
    # Обрабатываем каждую страницу
    for i, image in enumerate(images):
        print(f"\n📖 Анализ страницы {i+1}...")
        
        # Детектируем объекты
        signatures = inspector.detect_signatures(image)
        qr_codes = inspector.detect_qr_codes(image)
        stamps = inspector.detect_stamps(image)
        
        print(f"   📊 Подписи: {len(signatures)}, QR-коды: {len(qr_codes)}, Штампы: {len(stamps)}")
        
        # Сохраняем результаты в JSON формат
        page_result = {
            "page_number": i + 1,
            "signatures": [
                {
                    "bbox": sig['bbox'],
                    "confidence": float(sig['confidence']),
                    "label": "signature"
                } for sig in signatures
            ],
            "qr_codes": [
                {
                    "bbox": qr['bbox'],
                    "confidence": float(qr['confidence']),
                    "label": "qr_code"
                } for qr in qr_codes
            ],
            "stamps": [
                {
                    "bbox": stamp['bbox'],
                    "confidence": float(stamp['confidence']),
                    "label": "stamp"
                } for stamp in stamps
            ]
        }
        results["pages"].append(page_result)
        
        # Визуализируем и сохраняем результат
        if signatures or qr_codes or stamps:
            result_image = inspector.draw_detections(image, signatures + qr_codes + stamps)
            output_image = f"detailed_result_{pdf_path.stem}_page_{i+1}.jpg"
            result_image.save(output_image, quality=95)
            print(f"   💾 Визуальный результат: {output_image}")
    
    # Сохраняем JSON результаты
    json_output = f"json_result_{pdf_path.stem}.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON результат: {json_output}")
    
    # Выводим сводку
    total_sig = sum(len(page['signatures']) for page in results['pages'])
    total_qr = sum(len(page['qr_codes']) for page in results['pages'])
    total_stamp = sum(len(page['stamps']) for page in results['pages'])
    
    print(f"\n📈 ИТОГИ для {pdf_filename}:")
    print(f"   Подписи: {total_sig}")
    print(f"   QR-коды: {total_qr}")
    print(f"   Штампы: {total_stamp}")
    print(f"   Страниц с обнаружениями: {sum(1 for page in results['pages'] if page['signatures'] or page['qr_codes'] or page['stamps'])}")

if __name__ == "__main__":
    # Тестируем конкретный файл
    test_specific_file("отр-1.pdf")