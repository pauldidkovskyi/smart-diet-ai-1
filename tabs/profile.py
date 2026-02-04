import streamlit as st
import data_handler as dh


def render_profile(data):
    st.header("👤 Мій Профіль")
    st.caption("Ці дані потрібні AI для розрахунку калорій та плану тренувань.")

    prof = data.get("user_profile", {})

    with st.container(border=True):
        c1, c2 = st.columns(2)

        with c1:
            name = st.text_input("Ім'я", value=prof.get("name", "Атлет"))
            age = st.number_input("Вік", value=prof.get("age", 25), min_value=10, max_value=100)
            gender = st.selectbox("Стать", ["Чоловіча", "Жіноча"], index=0 if prof.get("gender") == "Чоловіча" else 1)

        with c2:
            weight = st.number_input("Вага (кг)", value=float(prof.get("weight", 70)), step=0.5)
            height = st.number_input("Зріст (см)", value=int(prof.get("height", 175)))

        st.write("---")

        c3, c4 = st.columns(2)
        with c3:
            activity = st.selectbox("Рівень активності",
                                    ["Сидячий", "Легкий", "Середній", "Високий", "Атлет"],
                                    index=["Сидячий", "Легкий", "Середній", "Високий", "Атлет"].index(
                                        prof.get("activity_level", "Середній")))
        with c4:
            goal = st.selectbox("Мета",
                                ["Схуднення", "Підтримка форми", "Набір маси", "Рекомпозиція"],
                                index=["Схуднення", "Підтримка форми", "Набір маси", "Рекомпозиція"].index(
                                    prof.get("goal", "Підтримка форми")))

        if st.button("💾 Оновити профіль", use_container_width=True):
            data["user_profile"] = {
                "name": name,
                "age": age,
                "gender": gender,
                "weight": weight,
                "height": height,
                "activity_level": activity,
                "goal": goal
            }
            dh.save_data(data)
            st.success("Дані збережено! AI врахує це в наступних розрахунках.")
            st.rerun()

    # Тут пізніше додамо графік зміни ваги