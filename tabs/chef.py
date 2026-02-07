import streamlit as st
import time
import random
import data_handler as dh


def render_chef(data):
    st.header("👨‍🍳 AI Шеф-Кухар")
    st.caption("Шеф аналізує твій холодильник і пропонує рецепти під твої цілі.")

    # 1. ОТРИМАННЯ ДАНИХ
    fridge = data.get("fridge", [])

    # Перевірка та ініціалізація списку рецептів
    if "recipes" not in data or not isinstance(data["recipes"], list):
        data["recipes"] = []
    saved_recipes = data["recipes"]

    # Отримуємо ціль користувача (для тегів рецепту)
    user_goal = data.get("user_profile", {}).get("goal", "Підтримка")

    # 2. СТВОРЕННЯ ВКЛАДОК
    tab_gen, tab_book = st.tabs(["🎲 Генератор рецептів", "📖 Моя книга рецептів"])

    # --- ВКЛАДКА 1: ГЕНЕРАТОР ---
    with tab_gen:
        if not fridge:
            st.warning(
                "🥕 Твій холодильник порожній! Додай продукти у вкладці 'Холодильник', щоб Шеф міг щось приготувати.")
        else:
            # A. Вибір продуктів
            fridge_list = [item['item'] for item in fridge]

            st.subheader("1. Що будемо використовувати?")
            selected_ingredients = st.multiselect(
                "Обери інгредієнти (або залиш порожнім для сюрпризу):",
                fridge_list
            )

            # B. Налаштування рецепту
            c1, c2 = st.columns(2)
            with c1:
                meal_type = st.selectbox("Тип прийому", ["Сніданок", "Обід", "Вечеря", "Перекус"])
            with c2:
                time_limit = st.select_slider("Час приготування", options=["15 хв", "30 хв", "45 хв", "60+ хв"])

            # C. Кнопка генерації
            if st.button("🍳 Придумати рецепт", use_container_width=True, type="primary"):
                with st.spinner("AI Шеф комбінує смаки та рахує калорії..."):
                    time.sleep(1.5)  # Ефект "думання"

                    # --- Логіка створення рецепту (Імітація) ---
                    base_ing = selected_ingredients if selected_ingredients else ["Яйця", "Овочі"]
                    main_product = base_ing[0].capitalize() if base_ing else "Сюрприз"

                    # Динамічна назва та калорії
                    if meal_type == "Сніданок":
                        rec_name = f"Енергійний омлет із {main_product}"
                        cal = 450
                    elif meal_type == "Вечеря":
                        rec_name = f"Легкий салат із {main_product}"
                        cal = 350
                    else:
                        rec_name = f"Ситне рагу з {main_product} та спеціями"
                        cal = 650

                    # Формування об'єкта рецепту
                    new_recipe = {
                        "name": rec_name,
                        "type": meal_type,
                        "time": time_limit,
                        "calories": f"{cal} ккал",
                        "ingredients": base_ing + ["Спеції", "Олія"],
                        "instructions": [
                            f"Підготуйте {', '.join(base_ing)}.",
                            "Розігрійте пательню або духовку.",
                            f"Змішайте інгредієнти та готуйте {time_limit}.",
                            "Подавайте гарячим. Смачного!"
                        ],
                        "tags": [user_goal, "Healthy"]
                    }

                    # Зберігаємо результат у сесію
                    st.session_state['generated_recipe'] = new_recipe

        # D. Відображення результату
        if 'generated_recipe' in st.session_state:
            rec = st.session_state['generated_recipe']

            st.divider()
            st.subheader("🎉 Результат:")

            # HTML-картка
            st.markdown(f"""
            <div style="
                background-color: #262730; 
                padding: 20px; 
                border-radius: 12px; 
                border-left: 5px solid #CCFF00;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            ">
                <h3 style="margin-top:0; color: #CCFF00;">{rec.get('name', 'Без назви')}</h3>
                <div style="display:flex; gap: 15px; margin-bottom: 15px; font-size: 14px; color: #ddd;">
                    <span>⏱ {rec.get('time', '--')}</span>
                    <span>🔥 {rec.get('calories', '--')}</span>
                    <span>🍽 {rec.get('type', '--')}</span>
                </div>
                <hr style="border-color: #444;">
                <p><b>🛒 Інгредієнти:</b> {', '.join(rec.get('ingredients', []))}</p>
                <p><b>📝 Інструкція:</b></p>
                <ol>
                    {''.join([f'<li>{step}</li>' for step in rec.get('instructions', [])])}
                </ol>
            </div>
            """, unsafe_allow_html=True)

            st.write("")

            # E. Збереження в книгу
            if st.button("❤️ Додати в книгу рецептів", use_container_width=True):
                # Перевіряємо на дублікати за назвою
                names = [r.get('name') for r in data["recipes"]]
                if rec.get('name') not in names:
                    data["recipes"].append(rec)
                    dh.save_data(data)
                    st.toast("Рецепт збережено!")
                    st.balloons()
                else:
                    st.warning("Цей рецепт вже є у твоїй книзі!")

    # --- ВКЛАДКА 2: КНИГА РЕЦЕПТІВ ---
    with tab_book:
        if not saved_recipes:
            st.info("У книзі поки пусто. Згенеруй свій перший рецепт у вкладці 'Генератор'!")
        else:
            st.write(f"Збережено рецептів: {len(saved_recipes)}")

            # Безпечний цикл виводу (захист від KeyError)
            for i, recipe in enumerate(saved_recipes):

                # Використовуємо .get() для безпеки
                r_name = recipe.get("name", "Невідомий рецепт")
                r_cal = recipe.get("calories", "---")
                r_time = recipe.get("time", "--")
                r_type = recipe.get("type", "Інше")
                r_ingred = recipe.get("ingredients", [])
                r_instr = recipe.get("instructions", [])

                with st.expander(f"🍽 {r_name} ({r_cal})"):
                    st.write(f"**Час:** {r_time} | **Тип:** {r_type}")
                    st.write(f"**Інгредієнти:** {', '.join(r_ingred)}")

                    if r_instr:
                        st.write("**Інструкція:**")
                        for step in r_instr:
                            st.write(f"- {step}")

                    # Кнопка видалення
                    if st.button("🗑 Видалити рецепт", key=f"del_rec_{i}"):
                        data["recipes"].pop(i)
                        dh.save_data(data)
                        st.rerun()