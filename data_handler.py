import json
import os
import copy  # <-- Додали для копіювання об'єктів

DATA_FILE = "data.json"

# Єдине джерело правди для структури даних
DEFAULT_SCHEMA = {
    "fridge": [],
    "history": [],
    "recipes": [],
    "shopping_list": [],
    "diet_plan": {},
    "settings": {}
}

def load_data():
    """
    Завантажує дані та гарантує, що всі ключі з DEFAULT_SCHEMA існують.
    """
    # Якщо файлу немає — одразу віддаємо чисту копію шаблону
    if not os.path.exists(DATA_FILE):
        return copy.deepcopy(DEFAULT_SCHEMA)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # "Лікуємо" дані
        for key, default_val in DEFAULT_SCHEMA.items():
            if key not in data:
                # ВАЖЛИВО: Використовуємо deepcopy, щоб не змінювати сам шаблон DEFAULT_SCHEMA
                data[key] = copy.deepcopy(default_val)

        return data

    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Помилка читання JSON ({e}). Створено нову базу.")
        return copy.deepcopy(DEFAULT_SCHEMA)


def save_data(data):
    """
    Безпечний запис: спочатку в тимчасовий файл, потім підміна.
    """
    temp_file = f"{DATA_FILE}.tmp"
    try:
        # Пишемо в .tmp
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # Атомарна підміна (миттєва операція)
        os.replace(temp_file, DATA_FILE)

    except Exception as e:
        print(f"❌ Помилка запису даних: {e}")
        # Прибираємо сміття
        if os.path.exists(temp_file):
            os.remove(temp_file)