import streamlit as st
import datetime


def render_sport_dashboard(data):
    st.header("💪 Тренувальний центр")

    # Тимчасова заглушка, поки ми робимо AI тренера
    st.info("🚧 Цей розділ в розробці. Скоро тут з'явиться твій персональний план тренувань.")

    tab1, tab2 = st.tabs(["📅 Календар тренувань", "🤖 AI Тренер"])

    with tab1:
        st.subheader("Мій розклад")
        selected_date = st.date_input("Дата тренування", datetime.date.today())
        st.write(f"План на {selected_date}:")
        st.caption("Тут будуть вправи...")

        # Заглушка для UI
        with st.expander("➕ Додати тренування вручну"):
            st.text_input("Назва (напр. Жим лежачи)")
            st.button("Додати запис")

    with tab2:
        st.subheader("Генератор програм")
        st.write("Тут ми будемо просити AI створити програму під твій профіль.")