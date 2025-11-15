# check_structure.py
from pathlib import Path

def check_project_structure():
    root = Path.cwd()
    print(f"📁 Текущая директория: {root}")
    
    # Ищем важные папки и файлы
    items_to_find = [
        'selected_output/pdfs',
        'models/best.pt', 
        'backend/app/services',
        'requirements.txt'
    ]
    
    for item in items_to_find:
        path = root / item
        if path.exists():
            print(f"✅ Найдено: {item}")
        else:
            print(f"❌ Не найдено: {item}")

if __name__ == "__main__":
    check_project_structure()