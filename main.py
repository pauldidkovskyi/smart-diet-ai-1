import streamlit as st
import data_handler as dh

# Імпортуємо наші нові модулі з папки tabs
from tabs import inventory, kitchen, analytics

st.set_page_config(page_title="Smart Diet AI", page_icon="🍎", layout="centered")


def main():
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🍎 Smart Diet AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Твій персональний шеф-кухар та розумний холодильник</p>",
                unsafe_allow_html=True)
    st.write("---")

    # Завантаження даних (одне на весь додаток)
    data = dh.load_data()

    # Глобальні змінні сесії
    if "last_ai_response" not in st.session_state:
        st.session_state.last_ai_response = None
    if "missing_products" not in st.session_state:
        st.session_state.missing_products = []

    # Головне меню
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🛒 Склад",
        "🛍 Покупки",
        "📅 Планувальник",
        "📊 Аналітика/Налаштування",
        "👨‍🍳 Шеф-кухар",
        "📖 Рецепти"
    ])

    # Виклик функцій з модулів
    with tab1:
        inventory.render_fridge(data)

    with tab2:
        inventory.render_shopping(data)

    with tab3:
        kitchen.render_planner(data)

    with tab4:
        analytics.render_analytics(data)

    with tab5:
        kitchen.render_chef(data)

    with tab6:
        kitchen.render_recipes(data)


if __name__ == "__main__":
    main()