import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import json
from PIL import Image

# Завантаження змінних
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# ВИКОРИСТОВУЄМО СТАБІЛЬНУ МОДЕЛЬ (щоб не було помилок 429)
CURRENT_MODEL_NAME = 'gemini-2.5-flash'
# Якщо 1.5 не працює, зміни на 'gemini-exp-1206' або 'gemini-pro'

CATEGORIES = [
    "🥩 М'ясо та Риба",
    "🥦 Овочі та Фрукти",
    "🥛 Молочні продукти",
    "🍞 Бакалія",
    "🧀 Інше"
]


def get_calories_from_ai(product_name, amount_str="порція"):
    """
    Рахує калорії. Покращена версія для Планувальника.
    Завжди повертає ціле число (int).
    """
    try:
        model = genai.GenerativeModel(CURRENT_MODEL_NAME)
        prompt = (
            f"Скільки кілокалорій (ккал) у продукті: '{product_name}', кількість/вага: '{amount_str}'? "
            f"Важливо: Напиши ТІЛЬКИ одне ціле число. Без слів 'ккал', 'калорій', 'приблизно'. "
            f"Якщо не вказана вага, рахуй середню порцію. "
            f"Приклад відповіді: 250"
        )
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Шукаємо всі групи цифр у тексті
        numbers = re.findall(r'\d+', text)

        if numbers:
            return int(numbers[0])  # Беремо перше знайдене число
        else:
            return 0
    except Exception as e:
        print(f"Calorie AI error: {e}")
        return 0


def parse_fridge_input(text_input):
    """
    Розбирає текст (список покупок або склад) на JSON.
    Використовується в Складі та Списку покупок.
    """
    try:
        model = genai.GenerativeModel(CURRENT_MODEL_NAME, generation_config={"response_mime_type": "application/json"})

        prompt = (
            f"Проаналізуй список продуктів: '{text_input}'. "
            f"Поверни JSON масив об'єктів. Кожен об'єкт має поля: "
            f"'item' (назва), 'amount' (кількість/вага - якщо немає, пиши '1 шт'), 'category'. "
            f"Категорію обирай СТРОГО одну з цього списку: {CATEGORIES}. "
            f"Якщо категорії немає в списку, став '🧀 Інше'."
        )

        response = model.generate_content(prompt)
        parsed_data = json.loads(response.text)

        # Додаткова перевірка категорій (на випадок галюцинацій AI)
        final_list = []
        for x in parsed_data:
            if isinstance(x, dict):
                if "category" not in x or x["category"] not in CATEGORIES:
                    x["category"] = "🧀 Інше"
                final_list.append(x)

        return final_list

    except Exception as e:
        print(f"Parse error: {e}")
        return []


def ask_chef(fridge_list, history, user_query, strict_mode=False):
    """
    Шеф-кухар з підтримкою суворого режиму.
    """
    try:
        model = genai.GenerativeModel(CURRENT_MODEL_NAME)

        fridge_text = ", ".join([f"{item['item']} ({item['amount']})" for item in fridge_list])
        history_text = ", ".join([h['name'] for h in history[-5:]]) if history else "пусто"

        if strict_mode:
            constraint = (
                "СТРОГЕ ОБМЕЖЕННЯ: Готуй ТІЛЬКИ з продуктів у списку 'Холодильник'. "
                "Не додавай нічого зайвого, крім води, солі та базових спецій. "
                "Якщо неможливо приготувати запит користувача, запропонуй щось інше з наявного."
            )
        else:
            constraint = (
                "Можеш використовувати будь-які інгредієнти. "
                "Якщо чогось немає в холодильнику - обов'язково виділи це в окремий список 'Треба докупити'."
            )

        prompt = (
            f"Ти Шеф. Холодильник: {fridge_text}. Запит: {user_query}. "
            f"{constraint} "
            f"Історія: {history_text}. "
            f"Відповідь структуруй: Назва, Інгредієнти (що є/чого нема), Рецепт, Ккал."
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Помилка Шефа: {e}"


def format_recipe(text):
    """Форматує рецепт для збереження в книгу"""
    try:
        # Проста евристика: беремо перший рядок як назву
        lines = text.split('\n')
        title = lines[0].replace('#', '').replace('*', '').strip()
        if len(title) > 50: title = "Смачний рецепт"
        return f"{title}|||{text}"
    except:
        return f"AI Рецепт|||{text}"


def analyze_recipe_for_cooking(recipe_text, current_fridge_list):
    """
    Аналіз рецепту: повертає JSON зі списками
    items_to_remove (що списати) та missing_items (чого не вистачає).
    """
    try:
        model = genai.GenerativeModel(CURRENT_MODEL_NAME, generation_config={"response_mime_type": "application/json"})

        fridge_context = json.dumps(current_fridge_list, ensure_ascii=False)

        prompt = (
            f"Рецепт: '{recipe_text}'.\n"
            f"Холодильник (JSON): {fridge_context}.\n\n"
            "Поверни JSON з полями:\n"
            "1. 'dish_name': Назва страви.\n"
            "2. 'calories': Калорійність (тільки число int).\n"
            "3. 'items_to_remove': Список (item, amount, category), які Є в холодильнику і будуть використані.\n"
            "4. 'missing_items': Список (item, amount, category), яких НЕ вистачає (або їх мало).\n"
            f"Категорії бери тільки з: {CATEGORIES}"
        )

        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Cooking analysis error: {e}")
        return None


def analyze_image(image):
    """Сканер чеків"""
    try:
        model = genai.GenerativeModel(CURRENT_MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        prompt = (
            f"Проаналізуй фото (чек або холодильник). Випиши продукти. "
            f"Поверни JSON масив: 'item', 'amount', 'category'. "
            f"Категорії ТІЛЬКИ такі: {CATEGORIES}."
        )
        response = model.generate_content([prompt, image])
        return json.loads(response.text)
    except Exception as e:
        print(f"Vision error: {e}")
        return []