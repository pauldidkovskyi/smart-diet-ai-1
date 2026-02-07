import streamlit as st
import data_handler as dh


def render_profile(data):
    st.header("👤 Профіль Атлета")
    st.caption("Налаштуй свої параметри, щоб AI розрахував ідеальні норми БЖВ.")

    # Завантажуємо існуючий профіль або ставимо дефолтні значення
    prof = data.get("user_profile", {})

    # Дефолтні значення (якщо профіль порожній)
    default_weight = float(prof.get("weight", 90.0))
    default_height = int(prof.get("height", 187))
    default_age = int(prof.get("age", 20))
    default_gender = prof.get("gender", "Чоловік")
    default_activity_str = prof.get("activity_level", "Середній (1.55)")
    default_goal = prof.get("goal", "Підтримка форми")

    # --- БЛОК РЕДАГУВАННЯ ---
    with st.expander("📝 Редагувати параметри тіла", expanded=True):
        c1, c2 = st.columns(2)

        with c1:
            name = st.text_input("Ім'я / Нікнейм", value=prof.get("name", "User"))
            age = st.number_input("Вік", value=default_age, min_value=10, max_value=100)
            gender = st.selectbox("Стать", ["Чоловік", "Жінка"], index=0 if default_gender == "Чоловік" else 1)

        with c2:
            weight = st.number_input("Вага (кг)", value=default_weight, step=0.5)
            height = st.number_input("Зріст (см)", value=default_height)

        st.write("---")

        c3, c4 = st.columns(2)

        # Словник активності для розрахунків
        activity_map = {
            "Сидячий (1.2)": 1.2,
            "Легкий (1.375)": 1.375,
            "Середній (1.55)": 1.55,
            "Високий (1.725)": 1.725,
            "Атлет (1.9)": 1.9
        }

        # Знаходимо індекс для selectbox
        act_keys = list(activity_map.keys())
        try:
            act_index = act_keys.index(default_activity_str)
        except ValueError:
            act_index = 2  # Середній за дефолтом

        with c3:
            activity_key = st.selectbox("Рівень активності", act_keys, index=act_index)
            activity_val = activity_map[activity_key]

        with c4:
            goal_options = ["Схуднення", "Підтримка форми", "Набір маси"]
            try:
                goal_index = goal_options.index(default_goal)
            except ValueError:
                goal_index = 1
            goal = st.selectbox("Твоя мета", goal_options, index=goal_index)

        # --- КНОПКА РОЗРАХУНКУ ТА ЗБЕРЕЖЕННЯ ---
        if st.button("💾 Розрахувати та Зберегти", use_container_width=True, type="primary"):

            # 1. Формула Міффліна-Сан Жеора
            if gender == "Чоловік":
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

            # 2. Добова норма (TDEE)
            tdee = bmr * activity_val

            # 3. Коригування під ціль
            if goal == "Схуднення":
                target_cal = int(tdee * 0.85)  # Дефіцит 15%
            elif goal == "Набір маси":
                target_cal = int(tdee * 1.15)  # Профіцит 15%
            else:
                target_cal = int(tdee)

            # 4. Розрахунок макросів (Спортивний стандарт)
            # Білок: 2г на кг ваги
            # Жири: 1г на кг ваги
            # Вуглеводи: решта калорій

            target_prot = int(weight * 2.0)
            target_fat = int(weight * 1.0)

            # Калорії, що лишилися на вуглеводи (1г білка=4ккал, 1г жиру=9ккал)
            cal_occupied = (target_prot * 4) + (target_fat * 9)
            remaining_cal = target_cal - cal_occupied
            target_carb = int(remaining_cal / 4)

            # Вода: 35 мл на кг
            target_water = round(weight * 0.035, 1)

            # ЗБЕРЕЖЕННЯ В DATA
            data["user_profile"] = {
                "name": name,
                "age": age,
                "gender": gender,
                "weight": weight,
                "height": height,
                "activity_level": activity_key,
                "goal": goal,
                # Зберігаємо розраховані цілі, щоб main.py їх бачив
                "targets": {
                    "calories": target_cal,
                    "protein": target_prot,
                    "fats": target_fat,
                    "carbs": target_carb,
                    "water": target_water
                }
            }

            dh.save_data(data)
            st.success("Профіль оновлено! Норми перераховані під твою вагу.")
            st.rerun()

    # --- ВІДОБРАЖЕННЯ РЕЗУЛЬТАТІВ ---
    # Якщо цілі вже розраховані, показуємо їх красиво
    if "targets" in prof:
        t = prof["targets"]

        st.subheader("📊 Твої розраховані норми на день")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔥 Калорії", f"{t['calories']}")
        m2.metric("🥩 Білки", f"{t['protein']} г")
        m3.metric("🥑 Жири", f"{t['fats']} г")
        m4.metric("🍚 Вуглеводи", f"{t['carbs']} г")

        st.info(f"💧 Рекомендована норма води: **{t.get('water', 2.5)} літра**")

    else:
        st.info("👆 Натисни 'Зберегти', щоб побачити свої норми калорій.")