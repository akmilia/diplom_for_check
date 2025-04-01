import os

# Пример использования
# file_path = r'C:\Users\Камила\Desktop\diplom_for_check\src\database\manager.py'
file_path = r'C:\Users\Камила\Desktop\diplom_for_check\src\apps\users\models.py'


def clean_null_bytes(file_path):
    # Полный путь к файлу
    full_path = os.path.abspath(file_path)
    print(f"Обработка файла: {full_path}")
    
    # Шаг 1: Чтение файла в бинарном режиме
    try:
        with open(full_path, 'rb') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return False
    
    # Проверка наличия нулевых байтов
    if b'\x00' not in content:
        print("Файл не содержит нулевых байтов")
        return True
    
    # Шаг 2: Удаление нулевых байтов
    clean_content = content.replace(b'\x00', b'')
    
    # Шаг 3: Создание резервной копии
    backup_path = full_path + '.bak'
    try:
        os.rename(full_path, backup_path)
        print(f"Создана резервная копия: {backup_path}")
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")
        return False
    
    # Шаг 4: Запись очищенного файла
    try:
        with open(full_path, 'wb') as f:
            f.write(clean_content)
        print("Файл успешно очищен от нулевых байтов")
        return True
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        # Восстановление из резервной копии при ошибке
        os.rename(backup_path, full_path)
        print("Восстановлен оригинальный файл из резервной копии")
        return False


clean_null_bytes(file_path) 