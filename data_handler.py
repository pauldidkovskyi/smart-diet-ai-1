import json
import os

DATA_FILE = "data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "fridge": [],
            "history": [],
            "recipes": [],
            "shopping_list": [],
            "diet_plan": {},  # <-- НОВЕ ПОЛЕ: Планувальник
            "settings": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Перевірки цілісності (щоб старі файли не ламали програму)
            if "fridge" not in data: data["fridge"] = []
            if "history" not in data: data["history"] = []
            if "diet_plan" not in data: data["diet_plan"] = {}  # <-- Додаємо при завантаженні
            if "recipes" not in data: data["recipes"] = []
            if "shopping_list" not in data: data["shopping_list"] = []
            if "settings" not in data: data["settings"] = {}
            return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {"fridge": [], "history": [], "diet_plan": {}, "recipes": [], "shopping_list": [], "settings": {}}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")