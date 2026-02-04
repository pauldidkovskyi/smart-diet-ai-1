import streamlit as st
import data_handler as dh

# Імпортуємо всі модулі (включно з новими)
try:
    from tabs import inventory, kitchen, analytics, profile, sport
except ImportError as e:
    st.error(f"⚠️ Помилка імпорту модулів: {e}. Перевір папку 'tabs'.")
    st.stop()

# 1. Налаштування сторінки
st.set_page_config(
    page_title="Smart Health AI",  # Змінили назву на більш глобальну
    page_icon="⚡️",
    layout="centered",
    initial_sidebar_state="expanded"
)


def load_css():
    st.markdown("""
        <style>
        .main-title { text-align: center; color: #FF4B4B; font-size: 2.5rem; margin-bottom: 0; }
        .sub-title { text-align: center; color: #666; font-style: italic; margin-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)


def init_session_state():
    if "data" not in st.session_state:
        st.session_state["data"] = dh.load_data()
    if "last_ai_response" not in st.session_state:
        st.session_state.last_ai_response = None
    if "missing_products" not in st.session_state:
        st.session_state.missing_products = []


def main():
    load_css()
    init_session_state()
    data_ref = st.session_state["data"]

    # --- БОКОВА ПАНЕЛЬ (НАВІГАЦІЯ) ---
    with st.sidebar:
        st.title("⚡️ Smart Health")

        # Відображаємо ім'я користувача, якщо є
        user_name = data_ref.get("user_profile", {}).get("name", "Атлет")
        st.write(f"Привіт, **{user_name}**!")

        st.write("---")
        app_mode = st.radio("Обери режим:", [
            "🍎 Харчування",
            "💪 Спорт",
            "👤 Профіль",
            "⚙️ Аналітика"
        ])

        st.write("---")
        st.caption("v1.1 (Beta Sport)")

    # --- ОСНОВНА ЧАСТИНА ---

    if app_mode == "👤 Профіль":
        profile.render_profile(data_ref)

    elif app_mode == "💪 Спорт":
        sport.render_sport_dashboard(data_ref)

    elif app_mode == "⚙️ Аналітика":
        # Аналітика тепер окремим пунктом
        analytics.render_analytics(data_ref)

    elif app_mode == "🍎 Харчування":
        st.markdown("<h2 style='text-align: center;'>🍎 Кухня</h2>", unsafe_allow_html=True)

        # Вкладки харчування
        food_tabs = st.tabs([
            "📅 Планувальник",
            "❄️ Холодильник",
            "🛒 Покупки",
            "👨‍🍳 Шеф-кухар",
            "📖 Рецепти"
        ])

        with food_tabs[0]:
            kitchen.render_planner(data_ref)
        with food_tabs[1]:
            inventory.render_fridge(data_ref)
        with food_tabs[2]:
            inventory.render_shopping(data_ref)
        with food_tabs[3]:
            kitchen.render_chef(data_ref)
        with food_tabs[4]:
            kitchen.render_recipes(data_ref)


if __name__ == "__main__":
    main()