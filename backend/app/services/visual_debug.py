# visual_debug.py
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import io

sys.path.append(str(Path(__file__).parent.parent))
from detection_services import DigitalInspector

def visualize_detections():
    """Визуализирует детекции на реальных изображениях"""
    inspector = DigitalInspector()
    
    # Прямой путь к PDF
    pdf_path = Path("C:/Users/user/Desktop/Programming/aiesec_hackathon/selected_output/pdfs/АПЗ-2.pdf")
    
    # Конвертируем только первую страницу
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[0]  # Первая страница
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("ppm")
    image = Image.open(io.BytesIO(img_data))
    doc.close()
    
    print(f"📐 Размер изображения: {image.size}")
    
    # Детектируем объекты
    signatures = inspector.detect_signatures(image)
    qr_codes = inspector.detect_qr_codes(image) 
    stamps = inspector.detect_stamps(image)
    
    print(f"🔍 Обнаружено: {len(signatures)} подписей, {len(qr_codes)} QR-кодов, {len(stamps)} штампов")
    
    # Визуализируем
    draw = ImageDraw.Draw(image)
    colors = {'signature': 'red', 'qr_code': 'green', 'stamp': 'blue'}
    
    # Рисуем подписи
    for det in signatures:
        bbox = det['bbox']
        draw.rectangle(bbox, outline=colors['signature'], width=3)
        draw.text((bbox[0], bbox[1]-20), f"SIG: {det['confidence']:.2f}", fill=colors['signature'])
        print(f"✍️ Подпись: {bbox}, conf: {det['confidence']:.2f}")
    
    # Рисуем QR-коды
    for det in qr_codes:
        bbox = det['bbox']
        draw.rectangle(bbox, outline=colors['qr_code'], width=3)
        draw.text((bbox[0], bbox[1]-20), f"QR: {det['confidence']:.2f}", fill=colors['qr_code'])
        print(f"📱 QR-код: {bbox}, conf: {det['confidence']:.2f}")
    
    # Рисуем штампы
    for det in stamps:
        bbox = det['bbox']
        draw.rectangle(bbox, outline=colors['stamp'], width=3)
        draw.text((bbox[0], bbox[1]-20), f"STAMP: {det['confidence']:.2f}", fill=colors['stamp'])
        print(f"🛡️ Штамп: {bbox}, conf: {det['confidence']:.2f}")
    
    # Сохраняем результат
    image.save("visual_debug_result.jpg", quality=95)
    print("💾 Визуализация сохранена: visual_debug_result.jpg")

if __name__ == "__main__":
    visualize_detections()
    