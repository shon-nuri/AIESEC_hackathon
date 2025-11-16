import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


# -------------------------
# Innovations - расширенная версия
# -------------------------
class Innovations:
    """Helper for signatures, stamps, QR codes with improved handling of overlapping and partial signatures."""
    
    def __init__(self, signature_detector, stamp_detector, qr_detector=None, precise_stamp_model=None, rtdetr_detector=None):
        self.signature_detector = signature_detector
        self.stamp_detector = stamp_detector
        self.qr_detector = qr_detector
        self.precise_stamp_model = precise_stamp_model
        self.rtdetr_detector = rtdetr_detector

        self.default_keywords = [
            "Главный инженер","Ф.И.О.","Главный инженер проекта",
            "Руководитель","подпись","Подпись","М.П.","МП",
            "Технический директор","Директор","ТОО"
        ]

    # ---------------- Utilities ----------------
    def calculate_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB-xA) * max(0, yB-yA)
        boxAArea = max(1, (boxA[2]-boxA[0])) * max(1, (boxA[3]-boxA[1]))
        boxBArea = max(1, (boxB[2]-boxB[0])) * max(1, (boxB[3]-boxB[1]))
        return interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0.0

    def bbox_center_distance(self, boxA, boxB):
        ax = (boxA[0]+boxA[2])/2.0
        ay = (boxA[1]+boxA[3])/2.0
        bx = (boxB[0]+boxB[2])/2.0
        by = (boxB[1]+boxB[3])/2.0
        return np.hypot(ax-bx, ay-by)

    def expand_bbox(self, bbox, image_size, margin_ratio=0.25):
        w,h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        mx,my = int(w*margin_ratio), int(h*margin_ratio)
        x1 = max(0, bbox[0]-mx)
        y1 = max(0, bbox[1]-my)
        x2 = min(image_size[0], bbox[2]+mx)
        y2 = min(image_size[1], bbox[3]+my)
        return [int(x1), int(y1), int(x2), int(y2)]

    def crop_with_margin(self, pil_image, bbox, margin_ratio=0.25):
        img_w,img_h = pil_image.size
        x1,y1,x2,y2 = self.expand_bbox(bbox, (img_w,img_h), margin_ratio)
        return pil_image.crop((x1,y1,x2,y2)), (x1,y1,x2,y2)

    # ---------------- OCR / Keywords ----------------
    def search_keywords(self, image, keywords=None, return_ocr_text=False):
        if keywords is None: keywords = self.default_keywords
        if pytesseract is None:
            return ([], "") if return_ocr_text else []
        if not isinstance(image, Image.Image):
            image = Image.fromarray(cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB))
        ocr_data = pytesseract.image_to_data(image, lang='rus+eng', output_type=pytesseract.Output.DICT)
        found, ocr_text = [], []
        for i, word in enumerate(ocr_data.get('text', [])):
            if not word.strip(): continue
            ocr_text.append(word)
            for kw in keywords:
                if kw.lower() in word.lower():
                    x,y,w,h = ocr_data['left'][i],ocr_data['top'][i],ocr_data['width'][i],ocr_data['height'][i]
                    found.append({'keyword': kw,'word': word,'bbox':[x,y,x+w,y+h]})
        return (found, " ".join(ocr_text)) if return_ocr_text else found

    # ---------------- Partial/Expanded Signature Detection ----------------
    def detect_signature_on_stamp_expanded(self, image, stamp_bbox, expansion_ratio=0.5, sig_conf_thresh=0.35, stamp_conf_thresh=0.25):
        """Detect signatures inside or overlapping stamp area using RT-DETR + upscaled secondary pass."""
        if self.rtdetr_detector is None:
            return self.detect_signature_on_stamp(image, stamp_bbox)

        x1,y1,x2,y2 = self.expand_bbox(stamp_bbox, image.size, expansion_ratio)
        crop = image.crop((x1,y1,x2,y2))

        sigs = self.rtdetr_detector.detect(crop, label_name='signature', conf_thresh=sig_conf_thresh)
        stamps = self.rtdetr_detector.detect(crop, label_name='stamp', conf_thresh=stamp_conf_thresh)

        # upscale secondary pass
        crop_np = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
        h,w = crop_np.shape[:2]
        upscaled = cv2.resize(crop_np, (w*2,h*2), interpolation=cv2.INTER_CUBIC)
        sigs_up = self.rtdetr_detector.detect(Image.fromarray(cv2.cvtColor(upscaled, cv2.COLOR_BGR2RGB)), label_name='signature', conf_thresh=sig_conf_thresh)
        for s in sigs_up:
            bx1,by1,bx2,by2 = s['bbox']
            s['bbox'] = [int(bx1/2+x1), int(by1/2+y1), int(bx2/2+x1), int(by2/2+y1)]

        # map original crop back
        for s in sigs+stamps:
            bx1,by1,bx2,by2 = s['bbox']
            s['bbox'] = [bx1+x1, by1+y1, bx2+x1, by2+y1]

        return sigs+sigs_up+stamps

    def detect_signature_on_stamp(self, image, stamp_bbox):
        """Fallback if no RT-DETR"""
        x1,y1,x2,y2 = stamp_bbox
        crop = image.crop((x1,y1,x2,y2))
        sigs = self.signature_detector.detect_signatures(crop)
        for s in sigs:
            sx1,sy1,sx2,sy2 = s['bbox']
            s['bbox'] = [sx1+x1, sy1+y1, sx2+x1, sy2+y1]
        return sigs

    # ---------------- Main detection ----------------
    def detect_with_overlap_handling(self, pil_image, page_number=None, total_pages=None, keywords=None):
        if keywords is None: keywords = self.default_keywords

        sigs = self.signature_detector.detect_signatures(pil_image) if self.signature_detector else []
        stamps = self.stamp_detector.detect_stamps(pil_image) if self.stamp_detector else []
        qrs = self.qr_detector.detect_qr_codes(pil_image) if self.qr_detector else []
        found_keywords = self.search_keywords(pil_image, keywords)

        # Normalize
        def norm(det):
            return {'label':det.get('label'), 'bbox':list(map(int,det.get('bbox'))), 'confidence':float(det.get('confidence',0.0))}
        sigs=[norm(s) for s in sigs]
        stamps=[norm(s) for s in stamps]
        qrs=[norm(q) for q in qrs]

        # Refine stamps with expanded signature detection
        refined_stamps = []
        for st in stamps:
            extra = self.detect_signature_on_stamp_expanded(pil_image, st['bbox']) if self.rtdetr_detector else self.recheck_partial_stamp(pil_image, st['bbox'])
            refined_stamps.extend(extra if extra else [st])
        stamps = refined_stamps

        # Overlap resolution and confidence boosting
        final_dets = []
        def is_contained(inner,outer,thresh=0.6):
            xA=max(inner[0],outer[0]); yA=max(inner[1],outer[1])
            xB=min(inner[2],outer[2]); yB=min(inner[3],outer[3])
            interArea=max(0,xB-xA)*max(0,yB-yA)
            innerArea=(inner[2]-inner[0])*(inner[3]-inner[1])
            return interArea/innerArea>thresh if innerArea>0 else False

        final_dets.extend(stamps)
        for sig in sigs:
            for st in stamps:
                iou=self.calculate_iou(sig['bbox'], st['bbox'])
                if iou>0.1:
                    if is_contained(sig['bbox'], st['bbox'], 0.5):
                        sig['confidence']=min(0.999, sig['confidence']+0.2)
                    st['confidence'] *= 0.85
            final_dets.append(sig)

        # Remove near-duplicate stamps
        deduped=[]
        for det in final_dets:
            if det['label']=='stamp' and any(self.calculate_iou(det['bbox'], e['bbox'])>0.85 for e in deduped if e['label']=='stamp'):
                continue
            deduped.append(det)
        final_dets=deduped+qrs

        # Keyword boosting
        img_w,img_h=pil_image.size
        for det in final_dets:
            for kw in found_keywords:
                try:
                    dist=self.bbox_center_distance(det['bbox'], kw['bbox'])
                    diag=np.hypot(img_w,img_h)
                    if dist/diag<0.12:
                        det['confidence']=min(0.999, det.get('confidence',0)+0.2)
                    elif dist/diag<0.22:
                        det['confidence']=min(0.999, det.get('confidence',0)+0.08)
                except: continue

        return sorted(final_dets, key=lambda x:x['confidence'], reverse=True)
