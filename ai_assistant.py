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
else:
    print("⚠️ УВАГА: API Key не знайдено! AI функції не працюватимуть.")

# ВИПРАВЛЕНО: Використовуємо існуючу модель (1.5 або 2.0)
# 'gemini-1.5-flash' - найшвидша і найдешевша для таких задач
CURRENT_MODEL_NAME = 'gemini-1.5-flash'

CATEGORIES = [
    "🥩 М'ясо та Риба",
    "🥦 Овочі та Фрукти",
    "🥛 Молочні продукти",
    "🍞 Бакалія",
    "🧀 Інше"
]


# --- ХЕЛПЕРИ ---

def _get_model(json_mode=False):
    """
    Фабрика моделей. Створює об'єкт моделі з потрібною конфігурацією.
    Це економить код у функціях.
    """
    config = {"response_mime_type": "application/json"} if json_mode else {}
    return genai.GenerativeModel(CURRENT_MODEL_NAME, generation_config=config)


def _clean_json_response(text):
    """
    Іноді AI повертає JSON у Markdown блоках (```json ... ```).
    Ця функція чистить це сміття перед парсингом.
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```json|^```", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()


# --- ОСНОВНІ ФУНКЦІЇ ---

def get_calories_from_ai(product_name, amount_str="порція"):
    """
    Рахує калорії. Повертає int.
    """
    try:
        # Використовуємо звичайний текстовий режим
        model = _get_model(json_mode=False)

        prompt = (
            f"Завдання: Визнач калорійність.\n"
            f"Продукт: {product_name}\n"
            f"Кількість: {amount_str}\n"
            f"Відповідь: ТІЛЬКИ одне ціле число (ккал). Якщо не знаєш — пиши 0."
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Витягуємо перше число, яке знайдемо
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0

    except Exception as e:
        print(f"⚠️ Calorie AI error: {e}")
        return 0


def parse_fridge_input(text_input):
    """
    Перетворює текст списку на структурований JSON.
    """
    try:
        # Вмикаємо JSON режим
        model = _get_model(json_mode=True)

        prompt = (
            f"Твоя роль: Парсер списку покупок.\n"
            f"Вхідні дані: '{text_input}'\n"
            f"Завдання: Поверни JSON масив об'єктів {{'item': str, 'amount': str, 'category': str}}.\n"
            f"Правила:\n"
            f"1. 'category' має бути ТІЛЬКИ з цього списку: {json.dumps(CATEGORIES, ensure_ascii=False)}.\n"
            f"2. Якщо категорії немає — став '🧀 Інше'.\n"
            f"3. Якщо вага не вказана — пиши '1 шт'."
        )

        response = model.generate_content(prompt)
        text = _clean_json_response(response.text)
        parsed_data = json.loads(text)

        # Валідація категорій (Double check)
        final_list = []
        if isinstance(parsed_data, list):
            for x in parsed_data:
                if isinstance(x, dict):
                    # Страховка, якщо AI придумає свою категорію
                    if x.get("category") not in CATEGORIES:
                        x["category"] = "🧀 Інше"
                    final_list.append(x)

        return final_list

    except Exception as e:
        print(f"⚠️ Parse error: {e}")
        return []


def ask_chef(fridge_list, history, user_query, strict_mode=False):
    """
    Чат з шефом.
    """
    try:
        model = _get_model(json_mode=False)

        # Формуємо контекст. Якщо холодильник великий, можна обрізати, але для тексту це не критично.
        fridge_text = ", ".join([f"{i.get('item')} ({i.get('amount')})" for i in fridge_list])
        history_text = ", ".join([h.get('name', '') for h in history[-5:]]) if history else "пусто"

        system_instruction = (
            "Ти професійний Шеф-кухар. Твоя відповідь має бути корисною, структурованою і смачною. "
            "Використовуй емодзі. Форматуй відповідь Markdown."
        )

        if strict_mode:
            constraint = "⛔️ СУВОРИЙ РЕЖИМ: Використовуй ТІЛЬКИ продукти з холодильника (+ сіль, перець, олія, вода)."
        else:
            constraint = "Вільний режим: Можеш пропонувати докупити інгредієнти."

        prompt = (
            f"{system_instruction}\n"
            f"Холодильник: {fridge_text}\n"
            f"Історія страв: {history_text}\n"
            f"Запит користувача: {user_query}\n"
            f"{constraint}\n\n"
            f"Структура відповіді:\n"
            f"1. 🍽 Назва страви\n"
            f"2. 🛒 Інгредієнти (відміть, чого не вистачає)\n"
            f"3. 👨‍🍳 Рецепт (покроково)\n"
            f"4. 🔥 Орієнтовні калорії"
        )

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Вибачте, Шеф втомився (Помилка API: {e})"


def format_recipe(text):
    """
    Витягує назву рецепта для заголовка.
    """
    try:
        lines = [L.strip() for L in text.split('\n') if L.strip()]
        if not lines: return "AI Рецепт|||" + text

        # Шукаємо перший рядок, схожий на заголовок (без # і зірочок)
        title = lines[0].replace('#', '').replace('*', '').strip()

        # Обмежуємо довжину заголовка, щоб не ламати верстку
        if len(title) > 60:
            title = title[:57] + "..."

        return f"{title}|||{text}"
    except:
        return f"AI Рецепт|||{text}"


def analyze_recipe_for_cooking(recipe_text, current_fridge_list):
    """
    Аналізує рецепт і каже, що списати, а чого бракує.
    Повертає JSON.
    """
    try:
        model = _get_model(json_mode=True)

        # Передаємо JSON холодильника рядком
        fridge_context = json.dumps(current_fridge_list, ensure_ascii=False)

        prompt = (
            f"Ти кухонний калькулятор.\n"
            f"Рецепт: {recipe_text[:2000]} (обрізано для економії)\n"  # Обрізаємо занадто довгі рецепти
            f"Холодильник: {fridge_context}\n"
            f"Завдання: Порівняй інгредієнти рецепта з холодильником.\n\n"
            f"Поверни JSON:\n"
            f"{{\n"
            f"  'dish_name': 'Назва страви',\n"
            f"  'calories': 500, (int)\n"
            f"  'items_to_remove': [ {{'item': 'назва як в холодильнику', 'amount': 'скільки списати', 'category': '...'}} ],\n"
            f"  'missing_items': [ {{'item': 'чого нема', 'amount': 'скільки треба', 'category': '...'}} ]\n"
            f"}}\n"
            f"Важливо: Намагайся співставити продукти (наприклад 'яйця' і 'Яйце куряче' - це те саме)."
        )

        response = model.generate_content(prompt)
        text = _clean_json_response(response.text)
        return json.loads(text)

    except Exception as e:
        print(f"⚠️ Cooking analysis error: {e}")
        return None


def analyze_image(image):
    """
    Vision API: розпізнає продукти на фото.
    """
    try:
        model = _get_model(json_mode=True)

        prompt = (
            f"Проаналізуй зображення.\n"
            f"Випиши всі продукти харчування у форматі JSON масиву.\n"
            f"Поля: item, amount, category.\n"
            f"Категорії ТІЛЬКИ: {json.dumps(CATEGORIES, ensure_ascii=False)}.\n"
            f"Якщо не впевнений - category='🧀 Інше'."
        )

        # Gemini підтримує PIL Image напряму
        response = model.generate_content([prompt, image])
        text = _clean_json_response(response.text)
        return json.loads(text)

    except Exception as e:
        print(f"⚠️ Vision error: {e}")
        return []