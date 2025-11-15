# utils/path_utils.py
import os
from pathlib import Path

def get_project_root():
    """Возвращает корневую директорию проекта"""
    current_file = Path(__file__)
    
    # Поднимаемся на нужный уровень в зависимости от расположения файла
    if 'backend/app/services' in str(current_file):
        return current_file.parent.parent.parent.parent
    else:
        # Ищем по характерным файлам
        for parent in current_file.parents:
            if (parent / 'selected_output').exists() or (parent / 'backend').exists():
                return parent
        return current_file.parent

def find_pdfs_directory():
    """Находит папку с PDF файлами"""
    root = get_project_root()
    
    # Ищем в разных возможных местах
    possible_locations = [
        root / 'selected_output' / 'pdfs',
        root / 'backend' / 'app' / 'services' / 'test_data',
        root / 'test_data',
        root / 'pdfs',
    ]
    
    for location in possible_locations:
        if location.exists():
            pdf_files = list(location.glob('*.pdf'))
            if pdf_files:
                print(f"✅ Найдены PDF в: {location}")
                return location
    
    # Если не нашли, создаем папку и просим пользователя добавить файлы
    test_data_dir = root / 'backend' / 'app' / 'services' / 'test_data'
    test_data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Создана папка для тестовых данных: {test_data_dir}")
    print("📄 Пожалуйста, добавьте PDF файлы в эту папку")
    return test_data_dir

def find_model_file(filename):
    """Находит файл модели"""
    root = get_project_root()
    
    possible_locations = [
        root / 'models' / filename,
        root / 'backend' / 'app' / 'services' / filename,
        root / filename,
        root / 'StampNSign' / filename,
    ]
    
    for location in possible_locations:
        if location.exists():
            print(f"✅ Модель найдена: {location}")
            return location
    
    print(f"❌ Файл модели не найден: {filename}")
    print("🔍 Ищем в проекте...")
    
    # Рекурсивный поиск
    for file_path in root.rglob(filename):
        if file_path.is_file():
            print(f"✅ Найден: {file_path}")
            return file_path
    
    return None