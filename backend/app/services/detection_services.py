# backend/app/services/detection_services.py
import os
import json
from pathlib import Path
import torch
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from transformers import pipeline
from qrdet import QRDetector
import time
from typing import List, Dict, Tuple, Optional
import easyocr

# === PATH CONFIGURATION ===
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'backend' / 'app' / 'models'
OUTPUT_DIR = PROJECT_ROOT / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

class AdvancedSignatureDetector:
    def __init__(self):
        print("🔄 Загрузка улучшенного детектора подписей...")
        try:
            self.detector = pipeline(
                "object-detection",
                model="nickmuchi/yolos-small-finetuned-signature-verification",
                device=0 if torch.cuda.is_available() else -1
            )
        except Exception as e:
            print(f"⚠️ Основная модель недоступна: {e}, используем fallback")
            self.detector = pipeline(
                "object-detection",
                model="mdefrance/yolos-base-signature-detection"
            )
        
        # Инициализируем OCR для поиска текстовых подсказок
        self.reader = easyocr.Reader(['ru', 'en'])
        print("✅ Улучшенный детектор подписей загружен")
    
    def find_signature_text_regions(self, image: Image.Image) -> List[Dict]:
        """Находит области с текстом 'подпись', 'Ф.И.О', 'signature' и т.д."""
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Увеличиваем контраст для лучшего распознавания текста
        lab = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0).apply(lab[:, :, 0])
        enhanced_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Распознаем текст
        results = self.reader.readtext(enhanced_image)
        
        signature_keywords = ['подпись', 'подписи', 'фио', 'ф.и.о', 'signature', 'signed', 'name']
        text_regions = []
        
        for (bbox, text, confidence) in results:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in signature_keywords) and confidence > 0.3:
                # Преобразуем bbox в формат [x1, y1, x2, y2]
                points = np.array(bbox).reshape(-1, 2)
                x1, y1 = points.min(axis=0)
                x2, y2 = points.max(axis=0)
                
                # Расширяем область поиска (вниз от текста)
                height = y2 - y1
                expanded_region = [
                    max(0, int(x1 - 20)),
                    max(0, int(y2 - 10)),  # Начинаем немного выше текста
                    min(image.width, int(x2 + 20)),
                    min(image.height, int(y2 + height * 3))  # Ищем подпись ниже текста
                ]
                
                text_regions.append({
                    'bbox': expanded_region,
                    'text': text,
                    'confidence': confidence
                })
                print(f"📝 Найден текст подписи: '{text}' в области {expanded_region}")
        
        return text_regions
    
    def detect_in_region(self, image: Image.Image, region: List[int]) -> List[Dict]:
        """Детектирует подписи в указанной области"""
        x1, y1, x2, y2 = region
        region_image = image.crop((x1, y1, x2, y2))
        
        if region_image.size[0] == 0 or region_image.size[1] == 0:
            return []
        
        # Увеличиваем контраст в области
        enhancer = ImageEnhance.Contrast(region_image)
        region_image = enhancer.enhance(2.0)
        
        results = self.detector(region_image)
        detections = []
        
        for result in results:
            if result['score'] > 0.25:  # Более низкий порог для текстовых областей
                box = result['box']
                # Преобразуем координаты обратно к исходному изображению
                absolute_bbox = [
                    x1 + box['xmin'],
                    y1 + box['ymin'],
                    x1 + box['xmax'],
                    y1 + box['ymax']
                ]
                
                detections.append({
                    'label': 'signature',
                    'bbox': absolute_bbox,
                    'confidence': result['score'],
                    'area': (box['xmax'] - box['xmin']) * (box['ymax'] - box['ymin']),
                    'source': 'text_guided'
                })
        
        return detections
    
    def detect_signatures(self, image: Image.Image) -> List[Dict]:
        start_time = time.time()
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Оптимизация размера
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        all_detections = []
        
        # Шаг 1: Поиск по текстовым подсказкам
        print("🔍 Поиск текстовых указателей подписей...")
        text_regions = self.find_signature_text_regions(image)
        
        for region in text_regions:
            region_detections = self.detect_in_region(image, region['bbox'])
            all_detections.extend(region_detections)
        
        # Шаг 2: Общий поиск по всему изображению (только если не нашли по тексту)
        if not all_detections:
            print("🔍 Общий поиск подписей...")
            results = self.detector(image)
            
            for result in results:
                if result['score'] > 0.3:
                    box = result['box']
                    detections.append({
                        'label': 'signature',
                        'bbox': [box['xmin'], box['ymin'], box['xmax'], box['ymax']],
                        'confidence': result['score'],
                        'area': (box['xmax'] - box['xmin']) * (box['ymax'] - box['ymin']),
                        'source': 'general'
                    })
        
        # Убираем дубликаты
        filtered_detections = self._remove_overlapping_detections(all_detections)
        
        print(f"⏱️ Детекция подписей: {time.time() - start_time:.2f}s, найдено: {len(filtered_detections)}")
        return filtered_detections
    
    def _remove_overlapping_detections(self, detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """Убирает пересекающиеся детекции"""
        if not detections:
            return []
        
        # Сортируем по уверенности
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        filtered = []
        
        for i, det in enumerate(detections):
            keep = True
            for kept in filtered:
                iou = self._calculate_iou(det['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    keep = False
                    break
            if keep:
                filtered.append(det)
        
        return filtered
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Вычисляет Intersection over Union"""
        x11, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Вычисляем площадь пересечения
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Вычисляем объединение
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0

class RobustQRCodeDetector:
    def __init__(self):
        print("🔄 Загрузка улучшенного детектора QR-кодов...")
        self.detector = QRDetector(model_size='s')
        print("✅ Детектор QR-кодов загружен")
    
    def detect_qr_codes(self, image: Image.Image) -> List[Dict]:
        start_time = time.time()
        
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        try:
            # Предобработка для улучшения детекции
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            detections = self.detector.detect(image=enhanced, is_bgr=False)
            results = []
            
            for detection in detections:
                if hasattr(detection, 'bbox_xyxy'):
                    bbox = detection.bbox_xyxy
                    confidence = detection.confidence
                elif isinstance(detection, dict):
                    bbox = detection['bbox_xyxy']
                    confidence = detection['confidence']
                else:
                    continue
                
                if confidence > 0.1:  # Низкий порог для QR-кодов
                    results.append({
                        'label': 'qr_code',
                        'bbox': [int(x) for x in bbox],
                        'confidence': float(confidence),
                        'area': (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    })
            
            print(f"⏱️ Детекция QR: {time.time() - start_time:.2f}s, найдено: {len(results)}")
            return results
            
        except Exception as e:
            print(f"❌ Ошибка детекции QR: {e}")
            return []

class EnhancedStampDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = MODELS_DIR / 'best.pt'
        
        if not os.path.exists(model_path):
            print(f"⚠️ Модель штампов не найдена: {model_path}")
            print("   Используется YOLOv8n (fallback)...")
            self.model = YOLO('yolov8n.pt')
        else:
            print(f"✅ Загрузка модели штампов: {model_path}")
            self.model = YOLO(model_path)
        
        # Дополнительные фильтры для штампов
        self.min_stamp_area = 500  # Минимальная площадь штампа
        self.max_stamp_area = 50000  # Максимальная площадь штампа
    
    def detect_stamps(self, image: Image.Image) -> List[Dict]:
        start_time = time.time()
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Детекция с низким порогом уверенности
        results = self.model(image, conf=0.3, iou=0.4)
        detections = []
        
        for result in results:
            for box in result.boxes:
                conf = float(box.conf.item())
                if conf > 0.3:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)
                    
                    # Фильтруем по размеру
                    if self.min_stamp_area <= area <= self.max_stamp_area:
                        # Проверяем форму (штампы обычно квадратные/круглые)
                        width = x2 - x1
                        height = y2 - y1
                        aspect_ratio = width / height if height > 0 else 0
                        
                        # Штампы обычно имеют соотношение сторон близкое к 1
                        if 0.5 <= aspect_ratio <= 2.0:
                            detections.append({
                                'label': 'stamp',
                                'bbox': [x1, y1, x2, y2],
                                'confidence': conf,
                                'area': area,
                                'aspect_ratio': aspect_ratio
                            })
        
        print(f"⏱️ Детекция штампов: {time.time() - start_time:.2f}s, найдено: {len(detections)}")
        return detections

class DigitalInspector:
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 ИНИЦИАЛИЗАЦИЯ УЛУЧШЕННОГО DigitalInspector")
        print("="*70)
        
        self.signature_detector = AdvancedSignatureDetector()
        self.qr_detector = RobustQRCodeDetector()
        self.stamp_detector = EnhancedStampDetector()
        
        print("✅ DigitalInspector инициализирован!\n")
    
    def process_document(self, image: Image.Image, page_num: int = 0) -> Dict:
        """Основной метод обработки документа"""
        start_time = time.time()
        
        print(f"\n📄 Обработка страницы {page_num + 1}...")
        
        # Детекция всех элементов
        signatures = self.detect_signatures(image)
        qr_codes = self.detect_qr_codes(image)
        stamps = self.detect_stamps(image)
        
        # Обработка пересечений
        processed_detections = self._resolve_overlaps(signatures, stamps, qr_codes)
        
        # Создание результата
        result = {
            'page_number': page_num,
            'detections': processed_detections,
            'image_size': image.size,
            'processing_time': time.time() - start_time,
            'elements_found': {
                'signatures': len([d for d in processed_detections if d['label'] == 'signature']),
                'stamps': len([d for d in processed_detections if d['label'] == 'stamp']),
                'qr_codes': len([d for d in processed_detections if d['label'] == 'qr_code'])
            }
        }
        
        print(f"✅ Страница {page_num + 1} обработана за {result['processing_time']:.2f}s")
        print(f"   📝 Подписи: {result['elements_found']['signatures']}")
        print(f"   🏷️ Штампы: {result['elements_found']['stamps']}")
        print(f"   📱 QR-коды: {result['elements_found']['qr_codes']}")
        
        return result
    
    def _resolve_overlaps(self, signatures: List[Dict], stamps: List[Dict], qr_codes: List[Dict]) -> List[Dict]:
        """Разрешает пересечения между разными типами детекций"""
        all_detections = signatures + stamps + qr_codes
        
        # Сортируем по уверенности
        all_detections.sort(key=lambda x: x['confidence'], reverse=True)
        final_detections = []
        
        for detection in all_detections:
            overlap_found = False
            
            for kept in final_detections:
                iou = self._calculate_iou(detection['bbox'], kept['bbox'])
                
                # Разные правила для разных типов пересечений
                if iou > 0.3:
                    if detection['label'] == kept['label']:
                        # Для одинаковых типов оставляем более уверенную
                        overlap_found = True
                        break
                    else:
                        # Для разных типов применяем приоритеты
                        if detection['label'] == 'qr_code' and kept['label'] in ['signature', 'stamp']:
                            # QR-коды имеют высший приоритет
                            final_detections.remove(kept)
                        elif detection['label'] == 'stamp' and kept['label'] == 'signature':
                            # Штампы имеют приоритет над подписями при пересечении
                            if detection['confidence'] > kept['confidence'] * 1.2:
                                final_detections.remove(kept)
                            else:
                                overlap_found = True
                                break
            
            if not overlap_found:
                final_detections.append(detection)
        
        return final_detections
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Вычисляет Intersection over Union"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0
    
    def detect_signatures(self, image: Image.Image) -> List[Dict]:
        return self.signature_detector.detect_signatures(image)
    
    def detect_qr_codes(self, image: Image.Image) -> List[Dict]:
        return self.qr_detector.detect_qr_codes(image)
    
    def detect_stamps(self, image: Image.Image) -> List[Dict]:
        return self.stamp_detector.detect_stamps(image)
    
    def draw_detections(self, image: Image.Image, detections: List[Dict]) -> Image.Image:
        """Рисует bounding boxes с улучшенной визуализацией"""
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        colors = {
            'signature': (0, 0, 255),    # Красный
            'qr_code': (0, 255, 0),      # Зеленый
            'stamp': (255, 0, 0),        # Синий
        }
        
        for detection in detections:
            label = detection['label']
            bbox = detection['bbox']
            confidence = detection.get('confidence', 0)
            source = detection.get('source', 'general')
            
            color = colors.get(label, (128, 128, 128))
            x1, y1, x2, y2 = map(int, bbox)
            
            # Рисуем bounding box
            thickness = 4 if source == 'text_guided' else 2
            cv2.rectangle(opencv_image, (x1, y1), (x2, y2), color, thickness)
            
            # Подпись с фоном
            label_text = f"{label}: {confidence:.2f}"
            if source == 'text_guided':
                label_text += " 📝"
            
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            
            # Фон для текста
            cv2.rectangle(opencv_image, 
                         (x1, y1 - text_height - 10),
                         (x1 + text_width, y1), 
                         color, -1)
            
            # Текст
            cv2.putText(opencv_image, label_text, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return Image.fromarray(cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB))
    
    def save_results_json(self, results: List[Dict], output_path: Path):
        """Сохраняет результаты в JSON формате"""
        output_data = {
            'metadata': {
                'processing_time': sum(r['processing_time'] for r in results),
                'total_pages': len(results),
                'total_elements': sum(r['elements_found']['signatures'] + 
                                    r['elements_found']['stamps'] + 
                                    r['elements_found']['qr_codes'] for r in results)
            },
            'pages': []
        }
        
        for result in results:
            page_data = {
                'page_number': result['page_number'],
                'image_size': result['image_size'],
                'processing_time': result['processing_time'],
                'detections': []
            }
            
            for detection in result['detections']:
                detection_data = {
                    'label': detection['label'],
                    'bbox': detection['bbox'],
                    'confidence': round(detection['confidence'], 3)
                }
                page_data['detections'].append(detection_data)
            
            output_data['pages'].append(page_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результаты сохранены в: {output_path}")

# Глобальный инстанс для easy access
digital_inspector = DigitalInspector()
