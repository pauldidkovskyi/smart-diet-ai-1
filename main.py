import streamlit as st
import data_handler as dh

# Імпорти модулів (переконайся, що в папці tabs є файл __init__.py, або просто файли лежать поруч)
# Якщо виникає помилка імпорту, спробуй: from tabs import inventory, kitchen, analytics
try:
    from tabs import inventory, kitchen, analytics
except ImportError:
    st.error("⚠️ Не знайдено модулі в папці 'tabs'. Перевір структуру проєкту.")
    st.stop()

# 1. Налаштування сторінки МАЄ бути першою командою Streamlit
st.set_page_config(
    page_title="Smart Diet AI",
    page_icon="🍎",
    layout="centered",
    initial_sidebar_state="collapsed"
)


def load_css():
    """Трохи магії CSS для красивих заголовків та відступів"""
    st.markdown("""
        <style>
        .main-title { text-align: center; color: #FF4B4B; font-size: 3rem; margin-bottom: 0; }
        .sub-title { text-align: center; color: #666; margin-top: -10px; font-style: italic; }
        .stTabs [data-baseweb="tab-list"] { justify-content: center; }
        </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """
    Ініціалізація даних.
    Завантажуємо з диска ТІЛЬКИ якщо їх ще немає в пам'яті.
    Це прискорює роботу в 10 разів.
    """
    if "data" not in st.session_state:
        st.session_state["data"] = dh.load_data()

    # Допоміжні змінні для AI та UI
    if "last_ai_response" not in st.session_state:
        st.session_state.last_ai_response = None
    if "missing_products" not in st.session_state:
        st.session_state.missing_products = []


def main():
    load_css()
    init_session_state()

    st.markdown("<h1 class='main-title'>🍎 Smart Diet AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Твій персональний шеф-кухар та розумний холодильник</p>", unsafe_allow_html=True)
    st.write("---")

    # Створюємо вкладки
    # (Використовуємо змінні, щоб код був чистішим)
    tabs = st.tabs([
        "❄️ Холодильник",
        "🛒 Покупки",
        "📅 Планувальник",
        "📊 Аналітика",  # Об'єднав з налаштуваннями логічно
        "👨‍🍳 Шеф-кухар",
        "📖 Рецепти"
    ])

    # Оскільки ми використовуємо session_state, передаємо посилання на об'єкт даних.
    # Зміни в функціях будуть відразу відображатись у session_state['data'].
    data_ref = st.session_state["data"]

    with tabs[0]:
        inventory.render_fridge(data_ref)

    with tabs[1]:
        inventory.render_shopping(data_ref)

    with tabs[2]:
        kitchen.render_planner(data_ref)

    with tabs[3]:
        # Тут render_analytics всередині себе викликає render_settings
        analytics.render_analytics(data_ref)

    with tabs[4]:
        kitchen.render_chef(data_ref)

    with tabs[5]:
        kitchen.render_recipes(data_ref)


if __name__ == "__main__":
    main()