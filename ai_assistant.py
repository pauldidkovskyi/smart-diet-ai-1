import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import json
from PIL import Image

# Завантаження змінних середовища
load_dotenv()

CATEGORIES = [
    "🥩 М'ясо та Риба",
    "🥦 Овочі та Фрукти",
    "🥛 Молочні продукти",
    "🍞 Бакалія",
    "🧀 Інше"
]


# --- ХЕЛПЕРИ (ДОПОМІЖНІ ФУНКЦІЇ) ---

def get_api_key():
    """
    Отримує API ключ з Secrets (Streamlit Cloud) або .env (Локально).
    """
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass

    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key

    return None


def _get_model(json_mode=False):
    """
    АВТОМАТИЧНИЙ ПІДБІР МОДЕЛІ.
    Ця функція сама знайде, яка модель доступна для твого ключа.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError("API Key не знайдено! Перевір налаштування.")

    genai.configure(api_key=api_key)

    # Базові налаштування
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    if json_mode:
        generation_config["response_mime_type"] = "application/json"

    # 1. Спроба №1: Жорстко пробуємо Flash (вона найкраща)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        model.generate_content("test")  # Перевірка зв'язку
        return model
    except:
        pass  # Якщо Flash немає, йдемо далі

    # 2. Спроба №2: Авто-пошук по списку доступних моделей
    try:
        print("⚠️ Flash недоступна, шукаємо іншу модель...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        # Логіка вибору: шукаємо 'flash', якщо ні - 'pro', якщо ні - будь-що стабільне
        chosen_model_name = None

        # Шукаємо Pro (1.5 або 1.0)
        for name in available_models:
            if 'pro' in name and 'vision' not in name:
                chosen_model_name = name
                break

        # Якщо Pro немає, беремо першу ліпшу gemini
        if not chosen_model_name:
            for name in available_models:
                if 'gemini' in name:
                    chosen_model_name = name
                    break

        if chosen_model_name:
            # print(f"✅ Підключено до: {chosen_model_name}")
            return genai.GenerativeModel(chosen_model_name, generation_config=generation_config)

    except Exception as e:
        raise ValueError(f"Помилка при пошуку моделей: {e}")

    raise ValueError("Не знайдено жодної робочої моделі AI для цього ключа.")


def _clean_json_response(text):
    """Чистить JSON від зайвих символів markdown."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```json|^```", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()


# --- ОСНОВНІ ФУНКЦІЇ (ПОВНІ ПРОМПТИ) ---

def get_calories_from_ai(product_name, amount_str="порція"):
    """
    Рахує калорії. Повертає int.
    """
    try:
        model = _get_model(json_mode=False)

        prompt = (
            f"Завдання: Визнач калорійність.\n"
            f"Продукт: {product_name}\n"
            f"Кількість: {amount_str}\n"
            f"Відповідь: ТІЛЬКИ одне ціле число (ккал). Якщо не знаєш — пиши 0."
        )

        response = model.generate_content(prompt)
        text = response.text.strip()
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

        # Валідація категорій
        final_list = []
        if isinstance(parsed_data, list):
            for x in parsed_data:
                if isinstance(x, dict):
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
        title = lines[0].replace('#', '').replace('*', '').strip()
        if len(title) > 60:
            title = title[:57] + "..."
        return f"{title}|||{text}"
    except:
        return f"AI Рецепт|||{text}"


def analyze_recipe_for_cooking(recipe_text, current_fridge_list):
    """
    Аналізує рецепт і каже, що списати, а чого бракує.
    """
    try:
        model = _get_model(json_mode=True)
        fridge_context = json.dumps(current_fridge_list, ensure_ascii=False)

        prompt = (
            f"Ти кухонний калькулятор.\n"
            f"Рецепт: {recipe_text[:2000]} (обрізано для економії)\n"
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
        response = model.generate_content([prompt, image])
        text = _clean_json_response(response.text)
        return json.loads(text)

    except Exception as e:
        print(f"⚠️ Vision error: {e}")
        return []


def generate_workout_plan(user_profile, equipment="Вдома (власна вага)"):
    """
    Генерує план тренувань на тиждень на основі профілю.
    """
    try:
        model = _get_model(json_mode=False)

        # Формуємо портрет атлета
        profile_text = (
            f"Вік: {user_profile.get('age')}, Вага: {user_profile.get('weight')}, "
            f"Стать: {user_profile.get('gender')}, Рівень: {user_profile.get('activity_level')}, "
            f"Мета: {user_profile.get('goal')}"
        )

        prompt = (
            f"Ти професійний фітнес-тренер. Склади програму тренувань на тиждень.\n"
            f"Профіль атлета: {profile_text}\n"
            f"Доступне обладнання: {equipment}\n\n"
            f"Вимоги:\n"
            f"1. Розпиши тренування по днях (День 1, День 2...).\n"
            f"2. Вкажи вправи, кількість підходів і повторень.\n"
            f"3. Обов'язково додай розминку і заминку.\n"
            f"4. Форматуй красиво використовуючи Markdown (жирний шрифт, списки).\n"
            f"5. Якщо мета 'Схуднення' - додай кардіо. Якщо 'Набір' - фокус на силовів."
            f"6. Пиши українською мовою."
        )

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Тренер зараз зайнятий (Помилка: {e})"