# web_app.py
import streamlit as st
import tempfile
import os
from pathlib import Path
import json
import sys

# Добавляем пути для импорта
sys.path.append(str(Path(__file__).parent.parent))

from detection_services import DigitalInspector

def pdf_to_images(pdf_path):
    """Конвертирует PDF в изображения используя PyMuPDF"""
    import fitz
    from PIL import Image
    import io
    
    doc = fitz.open(pdf_path)
    images = []
    
    for page in doc:
        mat = fitz.Matrix(2, 2)  # 2x масштаб для качества
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    
    doc.close()
    return images

def main():
    st.set_page_config(
        page_title="Digital Inspector",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Digital Inspector")
    st.markdown("Автоматическая детекция подписей, QR-кодов и штампов в документах")
    
    # Загружаем модель один раз
    if 'inspector' not in st.session_state:
        with st.spinner('Загрузка моделей...'):
            st.session_state.inspector = DigitalInspector()
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        "Загрузите PDF документ", 
        type=['pdf'],
        help="Загрузите строительный документ для анализа"
    )
    
    if uploaded_file is not None:
        # Сохраняем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Конвертируем PDF
            with st.spinner('Конвертация PDF...'):
                images = pdf_to_images(tmp_path)
            
            st.success(f"✅ Документ загружен: {len(images)} страниц")
            
            # Обрабатываем каждую страницу
            all_results = []
            
            for page_num, image in enumerate(images):
                st.subheader(f"📄 Страница {page_num + 1}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Показываем оригинал
                    st.image(image, caption=f"Оригинал - Страница {page_num + 1}", use_column_width=True)
                
                with col2:
                    # Детектируем и показываем результат
                    with st.spinner(f'Анализ страницы {page_num + 1}...'):
                        signatures = st.session_state.inspector.detect_signatures(image)
                        qr_codes = st.session_state.inspector.detect_qr_codes(image)
                        stamps = st.session_state.inspector.detect_stamps(image)
                    
                    # Визуализируем
                    result_image = st.session_state.inspector.draw_detections(
                        image, signatures + qr_codes + stamps
                    )
                    
                    st.image(result_image, caption=f"Результат анализа - Страница {page_num + 1}", use_column_width=True)
                    
                    # Показываем статистику
                    st.metric("Подписи", len(signatures))
                    st.metric("QR-коды", len(qr_codes))
                    st.metric("Штампы", len(stamps))
                
                # Сохраняем результаты для JSON
                page_results = {
                    "page_number": page_num + 1,
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
                all_results.append(page_results)
            
            # Генерируем JSON результат
            final_results = {
                "file_name": uploaded_file.name,
                "total_pages": len(images),
                "pages": all_results
            }
            
            # Показываем общую статистику
            st.subheader("📊 Общая статистика")
            total_sig = sum(len(page['signatures']) for page in all_results)
            total_qr = sum(len(page['qr_codes']) for page in all_results)
            total_stamp = sum(len(page['stamps']) for page in all_results)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего подписей", total_sig)
            with col2:
                st.metric("Всего QR-кодов", total_qr)
            with col3:
                st.metric("Всего штампов", total_stamp)
            
            # Предлагаем скачать JSON
            json_str = json.dumps(final_results, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Скачать JSON результаты",
                data=json_str,
                file_name=f"results_{uploaded_file.name}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ Ошибка обработки: {e}")
        
        finally:
            # Удаляем временный файл
            os.unlink(tmp_path)
    
    else:
        # Демонстрационная секция
        st.info("""
        ### 🚀 Как использовать:
        1. Загрузите PDF документ через кнопку выше
        2. Дождитесь обработки всех страниц
        3. Просмотрите визуальные результаты с bounding boxes
        4. Скачайте JSON с детальными результатами
        
        ### 🔍 Что детектируется:
        - **🔴 Подписи** - красные bounding boxes
        - **🟢 QR-коды** - зеленые bounding boxes  
        - **🔵 Штампы** - синие bounding boxes
        """)

if __name__ == "__main__":
    main()
    