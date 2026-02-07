import streamlit as st
import pandas as pd

# Налаштування сторінки (імітуємо мобільний вигляд)
st.set_page_config(page_title="Smart Diet Mobile", layout="centered", initial_sidebar_state="collapsed")

# --- CSS ДЛЯ КРУГЛИХ МЕТРИК ТА СТИЛЮ ---
# Це найскладніша частина - змусити Streamlit виглядати як мобільний додаток
st.markdown("""
    <style>
    /* Приховуємо стандартне меню */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Стиль для круглих метрик */
    .metric-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin: 0 auto;
        border: 3px solid;
        background-color: #1E1E1E;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value { font-size: 18px; font-weight: bold; color: white; }
    .metric-label { font-size: 12px; color: #ccc; }

    /* Кольори для режимів */
    .food-mode { border-color: #4CAF50; color: #4CAF50; } /* Зелений */
    .sport-mode { border-color: #2196F3; color: #2196F3; } /* Синій */

    /* Стиль календаря */
    .calendar-day {
        text-align: center;
        padding: 5px;
        border-radius: 10px;
        background-color: #262730;
        margin: 2px;
        font-size: 12px;
    }
    .active-day {
        border: 1px solid #ffffff;
        background-color: #444;
    }

    /* Кнопки дій */
    .action-row {
        display: flex;
        justify_content: space-between;
        padding: 10px;
        border-bottom: 1px solid #333;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- ЛОГІКА ПЕРЕМИКАННЯ РЕЖИМІВ ---
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Food"  # Food або Sport

# Верхній перемикач (Custom Toggle)
c1, c2 = st.columns(2)
with c1:
    if st.button("🍏 FOOD", use_container_width=True,
                 type="primary" if st.session_state.app_mode == "Food" else "secondary"):
        st.session_state.app_mode = "Food"
        st.rerun()
with c2:
    if st.button("🏋️‍♂️ SPORT", use_container_width=True,
                 type="primary" if st.session_state.app_mode == "Sport" else "secondary"):
        st.session_state.app_mode = "Sport"
        st.rerun()

# --- ВІЗУАЛІЗАЦІЯ ---

# 1. КАЛЕНДАР (Рядок 1-7)
st.write("")  # відступ
days = st.columns(7)
for i, col in enumerate(days):
    day_num = i + 1
    # Просто для прикладу підсвітимо 3-й день як активний
    active_class = "active-day" if day_num == 3 else ""
    col.markdown(f"<div class='calendar-day {active_class}'>{day_num}</div>", unsafe_allow_html=True)

st.write("---")

# 2. ГОЛОВНИЙ ЕКРАН (Залежить від режиму)
if st.session_state.app_mode == "Food":
    # === РЕЖИМ ЇЖІ (Зелений) ===

    # Прогрес бар калорій
    st.progress(0.65, text="🔥 Калорії: 1950 / 3000")

    st.write("")  # відступ

    # Круглі метрики (БЖВ)
    m1, m2, m3 = st.columns(3)


    def draw_circle(label, val, unit, color_class):
        return f"""
        <div class="metric-circle {color_class}">
            <div class="metric-value">{val}{unit}</div>
            <div class="metric-label">{label}</div>
        </div>
        """


    m1.markdown(draw_circle("Білки", 120, "г", "food-mode"), unsafe_allow_html=True)
    m2.markdown(draw_circle("Жири", 60, "г", "food-mode"), unsafe_allow_html=True)
    m3.markdown(draw_circle("Вуглев", 250, "г", "food-mode"), unsafe_allow_html=True)

    # Нижня частина (Макроси - Волокна, Цукор, Сіль)
    st.write("")
    m4, m5, m6 = st.columns(3)
    m4.markdown(draw_circle("Клітк.", 25, "г", "food-mode"), unsafe_allow_html=True)
    m5.markdown(draw_circle("Цукор", 10, "г", "food-mode"), unsafe_allow_html=True)
    m6.markdown(draw_circle("Сіль", 3, "г", "food-mode"), unsafe_allow_html=True)

    st.write("---")

    # Список прийомів їжі (Action List)
    meals = ["Сніданок", "Обід", "Вечеря", "Перекус"]
    for meal in meals:
        c_name, c_btn = st.columns([3, 1])
        c_name.subheader(meal)
        if c_btn.button("➕", key=f"add_{meal}"):
            st.toast(f"Додаємо щось у {meal}...")

else:
    # === РЕЖИМ СПОРТУ (Синій) ===

    # Прогрес бар активності
    st.progress(0.40, text="⚡ Активність: 40%")

    st.write("")  # відступ

    # Круглі метрики (М'язові групи)
    m1, m2, m3 = st.columns(3)


    def draw_circle_sport(label, status, color_class):
        return f"""
        <div class="metric-circle {color_class}">
            <div class="metric-value">{status}</div>
            <div class="metric-label">{label}</div>
        </div>
        """


    m1.markdown(draw_circle_sport("Спина", "Ok", "sport-mode"), unsafe_allow_html=True)
    m2.markdown(draw_circle_sport("Руки", "Pomp", "sport-mode"), unsafe_allow_html=True)
    m3.markdown(draw_circle_sport("Ноги", "Rest", "sport-mode"), unsafe_allow_html=True)

    st.write("")
    m4, m5, m6 = st.columns(3)
    m4.markdown(draw_circle_sport("Груди", "Ok", "sport-mode"), unsafe_allow_html=True)
    m5.markdown(draw_circle_sport("Плечі", "Ok", "sport-mode"), unsafe_allow_html=True)
    m6.markdown(draw_circle_sport("Прес", "Fire", "sport-mode"), unsafe_allow_html=True)

    st.write("---")

    # Список тренувань
    workouts = ["День ніг", "День рук", "День спини", "Full-body"]
    for wo in workouts:
        c_name, c_btn = st.columns([3, 1])
        c_name.subheader(wo)
        if c_btn.button("➕", key=f"start_{wo}"):
            st.toast(f"Починаємо {wo}!")

# --- SIDEBAR (Бокове меню - Сюди переїде старий функціонал) ---
with st.sidebar:
    st.title("⚙️ Меню")
    st.info("Тут живуть складні функції")

    menu = st.radio("Навігація", ["👤 Профіль", "🧊 Холодильник", "🛍 Покупки", "👨‍🍳 Шеф-кухар", "🎨 Налаштування теми"])

    st.divider()
    if menu == "🧊 Холодильник":
        st.write("Тут буде виклик функції `render_fridge(data)`")
        # render_fridge(data)
    elif menu == "🛍 Покупки":
        st.write("Тут буде виклик функції `render_shopping(data)`")
    elif menu == "🎨 Налаштування теми":
        st.color_picker("Основний колір", "#CCFF00")