import streamlit as st
import ai_assistant as ai
import data_handler as dh
import datetime


def render_sport_dashboard(data):
    st.header("💪 Тренувальний центр")

    # Отримуємо профіль
    prof = data.get("user_profile", {})
    if not prof.get("name"):
        st.warning("Спочатку заповни вкладку '👤 Профіль'!")
        return

    # Якщо плану ще немає в базі - ініціалізуємо
    if "workout_plan_text" not in data:
        data["workout_plan_text"] = ""

    tab1, tab2 = st.tabs(["📋 Мій План", "⚙️ Генератор"])

    # --- Вкладка 1: Відображення плану ---
    with tab1:
        if data["workout_plan_text"]:
            st.markdown(data["workout_plan_text"])

            st.write("---")
            if st.button("🗑 Видалити цей план", key="del_plan"):
                data["workout_plan_text"] = ""
                dh.save_data(data)
                st.rerun()
        else:
            st.info("У тебе ще немає активної програми. Перейди в 'Генератор', щоб створити її.")

    # --- Вкладка 2: Генератор ---
    with tab2:
        st.subheader("Створення нової програми")

        c1, c2 = st.columns(2)
        with c1:
            equipment = st.selectbox("Яке обладнання є?", [
                "Вдома (власна вага)",
                "Вдома (гантелі + турнік)",
                "Тренажерний зал (Full Gym)",
                "Вуличний майданчик (Workout)",
                "Тільки резинки (Resistance bands)"
            ])

        with c2:
            st.write(f"**Для кого:** {prof.get('name')}")
            st.write(f"**Мета:** {prof.get('goal')}")

        if st.button("🚀 Згенерувати програму тренувань", use_container_width=True):
            with st.spinner("AI Тренер аналізує твої параметри і пише план..."):
                # Викликаємо AI
                new_plan = ai.generate_workout_plan(prof, equipment)

                # Зберігаємо результат
                data["workout_plan_text"] = new_plan
                # Додаємо дату створення (щоб знати, коли оновлювати)
                data["workout_plan_date"] = str(datetime.date.today())

                dh.save_data(data)
                st.balloons()
                st.success("Програма готова! Переглянь її у вкладці 'Мій План'.")
                st.rerun()