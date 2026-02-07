import streamlit as st
import pandas as pd
import datetime
import data_handler as dh
import ai_assistant as ai

# Імпортуємо всі твої модулі (переконайся, що файли існують у папці tabs/)
from tabs import inventory, profile, chef, settings

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(
    page_title="Smart Diet",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. ДАНІ ТА СТАН ---
if "data" not in st.session_state:
    st.session_state.data = dh.load_data()
    # Гарантуємо наявність необхідних ключів
    for key in ["diary", "recipes", "profile", "settings"]:
        if key not in st.session_state.data:
            st.session_state.data[key] = {} if key != "recipes" else []

data = st.session_state.data

# Ініціалізація змінних сесії
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Food"

# Отримуємо налаштування кольору (або дефолт)
user_settings = data.get("settings", {})
accent_color = user_settings.get("theme_color", "#CCFF00")

# --- 3. CSS (СТИЛІЗАЦІЯ) ---
st.markdown(f"""
    <style>
    /* Прибираємо зайве */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* ЗМІННІ КОЛЬОРІВ (Динамічні) */
    :root {{
        --food-color: {accent_color};
        --sport-color: #00E5FF;
        --bg-dark: #1E1E1E;
    }}

    /* СТИЛЬ КІЛЬЦЕВОЇ ДІАГРАМИ (DONUT CHART) */
    .donut-chart {{
        position: relative;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        transition: transform 0.2s;
    }}
    .donut-chart:hover {{ transform: scale(1.05); }}

    .donut-inner {{
        width: 68px;
        height: 68px;
        background-color: var(--bg-dark);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 2;
    }}

    .metric-value {{ font-size: 15px; font-weight: bold; color: white; margin-bottom: -2px; line-height: 1.2;}}
    .metric-label {{ font-size: 10px; color: #aaa; text-transform: uppercase; margin-top: 2px;}}

    /* Стиль карток */
    .action-card {{
        background-color: #262730;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid #444;
    }}
    .action-title {{ font-weight: bold; font-size: 15px; }}
    .action-sub {{ font-size: 12px; color: #888; }}

    /* Заголовок дати */
    .date-header {{
        background-color: #262730;
        padding: 8px 15px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border: 1px solid #333;
    }}

    /* Кнопка календаря (іконка) */
    div[data-testid="stPopover"] > button {{
        border: none;
        background: transparent;
        font-size: 24px;
        padding: 0;
    }}
    div[data-testid="stPopover"] > button:hover {{
        background: transparent;
        color: var(--food-color);
        border: none;
    }}
    </style>
""", unsafe_allow_html=True)


# --- 4. ФУНКЦІЯ МАЛЮВАННЯ ДІАГРАМ ---
def draw_donut(label, val, goal, unit, color_hex):
    """Малює CSS пончик-діаграму"""
    if goal and goal > 0:
        percent = min(100, int((val / goal) * 100))
    else:
        percent = 100  # Повне коло, якщо немає цілі

    gradient = f"conic-gradient({color_hex} {percent}%, #333333 0)"

    return f"""
    <div class="donut-chart" style="background: {gradient};">
        <div class="donut-inner">
            <div class="metric-value">{val}<span style="font-size:9px; color:#888">{unit}</span></div>
            <div class="metric-label">{label}</div>
        </div>
    </div>
    """


# --- 5. БОКОВА ПАНЕЛЬ ---
with st.sidebar:
    st.title("⚡ Smart Diet")
    st.caption("v2.5 Full Integration")

    # Повне меню з усіма функціями
    nav = st.radio(
        "Навігація",
        ["🏠 Головна", "🧊 Холодильник", "🛍 Список покупок", "👨‍🍳 AI Шеф", "👤 Профіль", "⚙️ Налаштування"],
        index=0
    )
    st.divider()

# --- 6. МАРШРУТИЗАЦІЯ (ЛОГІКА СТОРІНОК) ---

if nav == "🧊 Холодильник":
    inventory.render_fridge(data)

elif nav == "🛍 Список покупок":
    inventory.render_shopping(data)

elif nav == "👤 Профіль":
    # Підключаємо реальний модуль профілю
    profile.render_profile(data)

elif nav == "👨‍🍳 AI Шеф":
    # Підключаємо модуль рецептів
    chef.render_chef(data)

elif nav == "⚙️ Налаштування":
    # Підключаємо налаштування
    settings.render_settings(data)

elif nav == "🏠 Головна":

    # === DASHBOARD (ГОЛОВНИЙ ЕКРАН) ===

    # 1. Перемикач режимів
    col_sw1, col_sw2 = st.columns(2)
    with col_sw1:
        if st.button("🍏 FOOD", use_container_width=True,
                     type="primary" if st.session_state.app_mode == "Food" else "secondary"):
            st.session_state.app_mode = "Food"
            st.rerun()
    with col_sw2:
        if st.button("🏋️‍♂️ SPORT", use_container_width=True,
                     type="primary" if st.session_state.app_mode == "Sport" else "secondary"):
            st.session_state.app_mode = "Sport"
            st.rerun()

    st.write("")

    # 2. Дата та Календар
    date_str = st.session_state.selected_date.strftime("%d %B, %A")
    c_date_label, c_date_btn = st.columns([5, 1])

    with c_date_label:
        st.markdown(f"""
        <div class="date-header">
            <span style="font-size: 18px; font-weight: bold; color: white;">📅 {date_str}</span>
        </div>
        """, unsafe_allow_html=True)

    with c_date_btn:
        with st.popover("📅", help="Змінити дату"):
            new_date = st.date_input("Оберіть дату", value=st.session_state.selected_date)
            if new_date != st.session_state.selected_date:
                st.session_state.selected_date = new_date
                st.rerun()

    # Отримуємо цілі з профілю (для динамічних діаграм)
    user_prof = data.get("user_profile", {})
    targets = user_prof.get("targets", {})

    # Дефолтні цілі, якщо профіль ще не налаштований
    GOAL_CAL = targets.get("calories", 2500)
    GOAL_PROT = targets.get("protein", 150)
    GOAL_FAT = targets.get("fats", 80)
    GOAL_CARB = targets.get("carbs", 300)
    GOAL_WATER = targets.get("water", 2.5)

    # 3. ВІДОБРАЖЕННЯ ДАНИХ
    if st.session_state.app_mode == "Food":
        THEME_COLOR = accent_color  # Використовуємо колір з налаштувань

        # Імітація спожитого (поки що). Пізніше підключимо data['diary']
        current_cal = 1950

        st.caption(f"🔥 Калорії (Ціль: {GOAL_CAL})")
        progress_val = min(1.0, current_cal / GOAL_CAL)
        st.progress(progress_val, text=f"{current_cal} ккал")
        st.write("")

        # Метрики-Діаграми (БЖВ)
        c1, c2, c3 = st.columns(3)
        c1.markdown(draw_donut("Білки", 140, GOAL_PROT, "г", THEME_COLOR), unsafe_allow_html=True)
        c2.markdown(draw_donut("Жири", 65, GOAL_FAT, "г", THEME_COLOR), unsafe_allow_html=True)
        c3.markdown(draw_donut("Вуглев", 210, GOAL_CARB, "г", THEME_COLOR), unsafe_allow_html=True)

        st.write("")
        c4, c5, c6 = st.columns(3)
        c4.markdown(draw_donut("Вода", 2.5, GOAL_WATER, "л", "#00E5FF"), unsafe_allow_html=True)
        c5.markdown(draw_donut("Цукор", 15, 50, "г", "#FF5252"), unsafe_allow_html=True)
        c6.markdown(draw_donut("Сіль", 4, 6, "г", "#FFFFFF"), unsafe_allow_html=True)

        st.divider()
        st.subheader("🍽 Записати прийом їжі")

        meals = ["Сніданок", "Обід", "Вечеря", "Перекус"]
        for meal in meals:
            with st.expander(f"➕ {meal}"):
                c_in, c_ok = st.columns([3, 1])
                with c_in:
                    txt = st.text_input(f"Страва", key=f"t_{meal}")
                with c_ok:
                    st.write("");
                    st.write("")
                    if st.button("OK", key=f"b_{meal}"):
                        if txt:
                            st.toast(f"Додано: {txt}")
                            # Тут в майбутньому: збереження в diary

            st.markdown(f"""
            <div class="action-card" style="border-left-color: {THEME_COLOR};">
                <div>
                    <div class="action-title">{meal}</div>
                    <div class="action-sub">Немає записів</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # SPORT MODE
        THEME_COLOR = "#00E5FF"  # Неоновий синій

        st.caption("⚡ Фізична активність")
        st.progress(0.4, text="40%")
        st.write("")

        c1, c2, c3 = st.columns(3)
        c1.markdown(draw_donut("Спина", 100, 100, "%", THEME_COLOR), unsafe_allow_html=True)
        c2.markdown(draw_donut("Груди", 80, 100, "%", THEME_COLOR), unsafe_allow_html=True)
        c3.markdown(draw_donut("Ноги", 20, 100, "%", "#FF5252"), unsafe_allow_html=True)

        st.divider()
        st.subheader("🏋️‍♂️ Активність")

        with st.expander("➕ Додати тренування"):
            st.selectbox("Тип", ["Силове", "Кардіо", "Розтяжка"])
            st.slider("Тривалість (хв)", 10, 120, 45)
            if st.button("Зберегти тренування"):
                st.success("Тренування додано!")

        st.markdown(f"""
        <div class="action-card" style="border-left-color: {THEME_COLOR};">
            <div>
                <div class="action-title">Силове</div>
                <div class="action-sub">19:00 • Груди + Трицепс</div>
            </div>
        </div>
        """, unsafe_allow_html=True)