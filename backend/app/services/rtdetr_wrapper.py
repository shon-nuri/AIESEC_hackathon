# rtdetr_wrapper.py
import torch
from PIL import Image
import torchvision.transforms as T

class RTDETRWrapper:
    def __init__(self, model_path, device='cuda'):
        self.device = device if torch.cuda.is_available() else 'cpu'
        # Load pretrained RT-DETR (custom or official weights)
        self.model = torch.load(model_path, map_location=self.device)
        self.model.eval()
        self.transform = T.Compose([
            T.Resize((800, 800)),
            T.ToTensor(),
            T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
        ])
    
    def detect(self, pil_image, label_name='object', conf_thresh=0.3):
        img_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(img_tensor)[0]  # dict with boxes & scores

        detections = []
        boxes = outputs['boxes'].cpu()
        scores = outputs['scores'].cpu()
        labels = outputs['labels'].cpu() if 'labels' in outputs else [label_name]*len(boxes)

        for box, score, lbl in zip(boxes, scores, labels):
            if score < conf_thresh:
                continue
            x1, y1, x2, y2 = box.tolist()
            detections.append({
                'label': label_name if isinstance(lbl,str) else str(lbl),
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(score)
            })
        return detections
