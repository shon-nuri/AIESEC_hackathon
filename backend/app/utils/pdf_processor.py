# backend/app/services/pdf_processor.py
import fitz  # PyMuPDF
from PIL import Image
import tempfile
import os
from pathlib import Path
from typing import List, Dict
from .detection_services import digital_inspector

class PDFProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg']
    
    def process_pdf(self, pdf_path: Path, output_dir: Path = None) -> List[Dict]:
        """Обрабатывает PDF файл и возвращает результаты"""
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp())
        
        output_dir.mkdir(exist_ok=True)
        
        print(f"📖 Обработка PDF: {pdf_path}")
        
        all_results = []
        
        try:
            doc = fitz.open(pdf_path)
            
            # Особое внимание к первой и последней страницам
            important_pages = [0, len(doc) - 1]  # Первая и последняя
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Увеличиваем DPI для важных страниц
                zoom = 3.0 if page_num in important_pages else 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("ppm")
                image = Image.open(io.BytesIO(img_data))
                
                # Обработка страницы
                result = digital_inspector.process_document(image, page_num)
                all_results.append(result)
                
                # Визуализация для важных страниц
                if page_num in important_pages or len(result['detections']) > 0:
                    visualized = digital_inspector.draw_detections(image, result['detections'])
                    output_path = output_dir / f"page_{page_num + 1}_detections.png"
                    visualized.save(output_path)
                    print(f"💾 Визуализация сохранена: {output_path}")
            
            doc.close()
            
            # Сохраняем JSON результаты
            json_output = output_dir / "detection_results.json"
            digital_inspector.save_results_json(all_results, json_output)
            
            return all_results
            
        except Exception as e:
            print(f"❌ Ошибка обработки PDF: {e}")
            raise

    def process_single_image(self, image_path: Path) -> Dict:
        """Обрабатывает одиночное изображение"""
        image = Image.open(image_path)
        return digital_inspector.process_document(image, 0)
    