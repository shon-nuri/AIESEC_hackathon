# detection_services.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import os
from pathlib import Path
from transformers import pipeline
import torch
from qrdet import QRDetector
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

# Автоматически определяем пути
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / 'models'

class SignatureDetector:
    def __init__(self):
        self.detector = pipeline(
            "object-detection", 
            model="mdefrance/yolos-base-signature-detection"
        )
    
    def detect_signatures(self, image):
        results = self.detector(image)
        
        detections = []
        for result in results:
            box = result['box']
            detections.append({
                'label': 'signature',
                'bbox': [float(box['xmin']), float(box['ymin']), float(box['xmax']), float(box['ymax'])],
                'confidence': float(result['score'])
            })
        
        return detections

class QRCodeDetector:
    def __init__(self):
        self.detector = QRDetector(model_size='s')
    
    def detect_qr_codes(self, image):
        # Конвертируем PIL в numpy array для OpenCV
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        try:
            # НОВЫЙ ФОРМАТ: используем новый вывод без legacy
            detections = self.detector.detect(image=opencv_image, is_bgr=True)
            
            results = []
            for detection in detections:
                # Новый формат вывода - это namedtuple или dict
                bbox = []
                confidence = 0.0
                
                if hasattr(detection, 'bbox_xyxy'):
                    # Если это namedtuple
                    bbox = [float(x) for x in detection.bbox_xyxy]
                    confidence = float(detection.confidence)
                elif isinstance(detection, dict):
                    # Если это dict
                    bbox = [float(x) for x in detection['bbox_xyxy']]
                    confidence = float(detection['confidence'])
                else:
                    # Пропускаем неизвестный формат
                    continue
                
                results.append({
                    'label': 'qr_code',
                    'bbox': bbox,  # [x1, y1, x2, y2]
                    'confidence': confidence
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Ошибка детекции QR-кодов: {e}")
            # Попробуем старый формат как fallback
            try:
                detections = self.detector.detect(image=opencv_image, is_bgr=True, legacy=True)
                results = []
                for detection in detections:
                    results.append({
                        'label': 'qr_code',
                        'bbox': [float(x) for x in detection['bbox_xyxy']],
                        'confidence': float(detection['confidence'])
                    })
                return results
            except Exception as fallback_error:
                print(f"❌ Fallback также не сработал: {fallback_error}")
                return []

class StampDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = MODELS_DIR / 'best.pt'
        
        if not os.path.exists(model_path):
            print(f"⚠️ Модель штампов не найдена: {model_path}")
            self.model = None
            return
        
        try:
            self.model = YOLO(model_path)
            print(f"✅ Модель штампов загружена: {model_path}")
        except Exception as e:
            print(f"❌ Ошибка загрузки модели штампов: {e}")
            self.model = None
    
    def detect_stamps(self, image):
        if self.model is None:
            return []
            
        try:
            results = self.model(image)
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

class DigitalInspector:
    def __init__(self):
        print("🔄 Загрузка модели подписей...")
        self.signature_detector = SignatureDetector()
        print("✅ Модель подписей загружена")
        
        print("🔄 Загрузка модели QR-кодов...")
        self.qr_detector = QRCodeDetector()
        print("✅ Модель QR-кодов загружена")
        
        print("🔄 Загрузка модели штампов...")
        self.stamp_detector = StampDetector()
        if self.stamp_detector.model is not None:
            print("✅ Модель штампов загружена")
        else:
            print("⚠️ Модель штампов не доступна")
    
    def detect_signatures(self, image):
        try:
            return self.signature_detector.detect_signatures(image)
        except Exception as e:
            print(f"❌ Ошибка детекции подписей: {e}")
            return []
    
    def detect_qr_codes(self, image):
        try:
            return self.qr_detector.detect_qr_codes(image)
        except Exception as e:
            print(f"❌ Ошибка детекции QR-кодов: {e}")
            return []
    
    def detect_stamps(self, image):
        try:
            if self.stamp_detector and self.stamp_detector.model is not None:
                return self.stamp_detector.detect_stamps(image)
            return []
        except Exception as e:
            print(f"❌ Ошибка детекции штампов: {e}")
            return []
    
    def draw_detections(self, image, detections):
        """Рисует bounding boxes на изображении"""
        try:
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
        except Exception as e:
            print(f"❌ Ошибка отрисовки детекций: {e}")
            return image
        