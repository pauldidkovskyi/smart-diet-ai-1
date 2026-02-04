import json
import os
import copy

DATA_FILE = "data.json"

# ОНОВЛЕНА СХЕМА: Додали user_profile та workout_plan
DEFAULT_SCHEMA = {
    "fridge": [],
    "history": [],
    "recipes": [],
    "shopping_list": [],
    "diet_plan": {},
    "settings": {},
    "user_profile": {
        "name": "Атлет",
        "age": 25,
        "weight": 70,
        "height": 175,
        "gender": "Чоловіча",
        "activity_level": "Середній",
        "goal": "Підтримка форми"
    },
    "workout_plan": {}
}


def load_data():
    """
    Завантажує дані та гарантує, що всі ключі з DEFAULT_SCHEMA існують.
    """
    if not os.path.exists(DATA_FILE):
        return copy.deepcopy(DEFAULT_SCHEMA)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # "Лікуємо" дані (міграція)
        for key, default_val in DEFAULT_SCHEMA.items():
            if key not in data:
                data[key] = copy.deepcopy(default_val)

        # Додаткова перевірка: якщо профіль пустий словник (старий баг), перезаписуємо дефолтом
        if not data.get("user_profile"):
            data["user_profile"] = copy.deepcopy(DEFAULT_SCHEMA["user_profile"])

        return data

    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Помилка читання JSON ({e}). Створено нову базу.")
        return copy.deepcopy(DEFAULT_SCHEMA)


def save_data(data):
    """
    Безпечний запис (атомарний).
    """
    temp_file = f"{DATA_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        print(f"❌ Помилка запису даних: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)