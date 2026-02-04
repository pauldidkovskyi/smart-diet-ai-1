import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Завантажуємо змінні середовища з .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print("--- ПОЧАТОК ПЕРЕВІРКИ ---")

if not api_key:
    print("❌ ПОМИЛКА: Не знайдено GOOGLE_API_KEY! Перевір файл .env")
    exit()
else:
    print(f"🔑 Ключ знайдено: {api_key[:8]}...")

# 2. Налаштовуємо бібліотеку
genai.configure(api_key=api_key)

try:
    print("\n📡 Роблю запит до Google API за списком моделей...")

    # 3. Отримуємо список всіх моделей
    all_models = list(genai.list_models())

    found_any = False
    print("\n📋 ОСЬ ЩО ТОБІ ДОСТУПНО:")

    for m in all_models:
        # Нам цікаві тільки ті, що вміють генерувати текст (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            print(f"   ✅ {m.name}")
            found_any = True

    if not found_any:
        print("\n⚠️ Дивно... Список отримано, але текстових моделей там немає.")
    else:
        print(
            "\n🚀 Інструкція: Скопіюй будь-яку назву зі списку вище (наприклад 'models/gemini-pro') і встав у CURRENT_MODEL_NAME.")

except Exception as e:
    print(f"\n❌ КРИТИЧНА ПОМИЛКА ПІДКЛЮЧЕННЯ:\n{e}")

print("\n--- КІНЕЦЬ ПЕРЕВІРКИ ---")