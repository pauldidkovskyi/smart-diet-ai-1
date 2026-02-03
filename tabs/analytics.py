import streamlit as st
import pandas as pd
import datetime
import ai_assistant as ai
import data_handler as dh


# --- ХЕЛПЕРИ ---

def get_combined_data(data):
    """
    Збирає історію з усіх джерел і формує чистий DataFrame.
    Виправлено помилку з лапками та додано захист від "битого" JSON.
    """
    all_records = []

    # 1. Дані зі старого журналу (history)
    for h in data.get("history", []):
        all_records.append({
            "date": h.get("date", str(datetime.date.today())),
            "name": h.get("name", "Невідомо"),
            "calories": h.get("calories", 0)
        })

    # 2. Дані з Планувальника (diet_plan)
    diet_plan = data.get("diet_plan", {})

    # Перевіряємо, чи diet_plan справді словник (захист даних)
    if isinstance(diet_plan, dict):
        for date_str, meals in diet_plan.items():
            # Захист: іноді структура може бути пошкоджена
            if not isinstance(meals, dict): continue

            for m_type, dishes in meals.items():
                if not isinstance(dishes, list): continue

                for dish in dishes:
                    if dish.get('status') == 'done':
                        # ТУТ БУЛА ПОМИЛКА: виправлено лапки в 'calories'
                        val = dish.get('calories', 0)
                        all_records.append({
                            "date": date_str,
                            "name": dish.get('dish', "Страва"),
                            "calories": val
                        })

    if not all_records:
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Конвертуємо дати у datetime (помилки стають NaT і видаляються)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    # Гарантуємо, що калорії - це числа
    df['calories'] = pd.to_numeric(df['calories'], errors='coerce').fillna(0)

    return df.sort_values(by="date")


# --- ОСНОВНІ ФУНКЦІЇ ---

def render_analytics(data):
    st.header("📊 Аналітика харчування")

    df = get_combined_data(data)

    if df.empty:
        st.info("Даних ще немає. Почніть відмічати виконані страви у Планувальнику!")
        render_settings(data)
        return

    # --- МЕТРИКИ ---
    total_cals = df['calories'].sum()
    # Рахуємо унікальні дні (dt.date відкидає час)
    days_tracked = df['date'].dt.date.nunique()

    # Захист від ділення на нуль
    avg_daily = total_cals / days_tracked if days_tracked > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Всього спожито", f"{total_cals:,.0f} ккал")
    c2.metric("📅 Активних днів", days_tracked)
    c3.metric("⚖️ Середнє за день", f"{avg_daily:,.0f} ккал")

    st.write("---")

    # --- ГРАФІКИ ---
    t_day, t_month, t_year = st.tabs(["📅 По днях", "🗓 По місяцях", "📆 По роках"])

    with t_day:
        st.subheader("Останні 30 днів")
        # Групуємо по даті
        daily = df.groupby(df['date'].dt.date)['calories'].sum().reset_index()
        daily.columns = ['Дата', 'Калорії']
        # Повертаємо у datetime для коректного графіка Streamlit
        daily['Дата'] = pd.to_datetime(daily['Дата'])

        st.bar_chart(daily.tail(30).set_index('Дата'), color="#FF4B4B")

        with st.expander("Детальна таблиця"):
            # Форматуємо дату красиво для таблиці
            daily_show = daily.copy()
            daily_show['Дата'] = daily_show['Дата'].dt.strftime('%Y-%m-%d')
            st.dataframe(daily_show.sort_values('Дата', ascending=False), use_container_width=True)

    with t_month:
        st.subheader("По місяцях")
        df_m = df.copy()
        df_m['month'] = df_m['date'].dt.to_period('M').astype(str)
        monthly = df_m.groupby('month')['calories'].sum().reset_index()
        st.bar_chart(monthly.set_index('month'), color="#4BFF4B")

    with t_year:
        st.subheader("Річна статистика")
        df_y = df.copy()
        df_y['year'] = df_y['date'].dt.year.astype(str)
        yearly = df_y.groupby('year')['calories'].sum().reset_index()

        col_ch, col_tb = st.columns([2, 1])
        col_ch.bar_chart(yearly.set_index('year'), color="#4B4BFF")
        col_tb.dataframe(yearly, hide_index=True)

    st.write("---")
    render_settings(data)


def render_settings(data):
    """
    Налаштування стилю.
    Виправлено логіку збереження, щоб уникнути втрати даних при перезавантаженні сторінки.
    """
    with st.expander("🎨 Налаштування стилю (Іконки та Кольори)"):
        st.caption("Натисни на іконку — збережеться одразу.")

        # Ініціалізація ключів, якщо їх немає (Fix для нових користувачів)
        if "settings" not in data: data["settings"] = {}
        if "category_colors" not in data["settings"]: data["settings"]["category_colors"] = {}
        if "custom_icons" not in data["settings"]: data["settings"]["custom_icons"] = {}

        current_colors = data["settings"]["category_colors"]
        current_icons = data["settings"]["custom_icons"]

        # Довідник емодзі
        EMOJI_OPTIONS = {
            "М'ясо та Риба": ["🥩", "🍗", "🍖", "🍔", "🍤", "🐟", "🍣", "🥓"],
            "Овочі та Фрукти": ["🥦", "🍅", "🍆", "🌽", "🥕", "🥗", "🥔", "🍎", "🍐", "🍌", "🍉", "🍇"],
            "Молочні продукти": ["🥛", "🍼", "☕", "🧀", "🍦", "🥣"],
            "Бакалія": ["🍞", "🥐", "🥖", "🥨", "🥞", "🍝", "🍜", "🍚", "🍪"],
            "Інше": ["🧀", "🥚", "🍕", "🌭", "🥪", "🌮", "🌯", "🥫", "🍱", "🥡", "🍫", "🍬", "🍭"]
        }

        cols = st.columns(len(ai.CATEGORIES))

        # Словник для збору нових кольорів з форми
        pending_colors = {}

        for i, full_cat_name in enumerate(ai.CATEGORIES):
            # Розбираємо рядок "🥩 М'ясо" на ["🥩", "М'ясо"]
            parts = full_cat_name.split(" ", 1)
            cat_clean_name = parts[1] if len(parts) > 1 else full_cat_name

            # Активна іконка: або з налаштувань, або дефолтна з назви
            active_icon = current_icons.get(full_cat_name, parts[0])

            with cols[i]:
                st.markdown(f"**{cat_clean_name}**")

                # --- ВИБІР ІКОНКИ ---
                with st.popover(f"{active_icon}"):
                    st.write("Обери нову:")
                    # Беремо список емодзі для категорії або загальний
                    emoji_list = EMOJI_OPTIONS.get(cat_clean_name, EMOJI_OPTIONS["Інше"])

                    # Малюємо сітку 4xN
                    for j in range(0, len(emoji_list), 4):
                        row_emojis = emoji_list[j:j + 4]
                        em_cols = st.columns(4)
                        for k, emoji in enumerate(row_emojis):
                            # Унікальний ключ для кожної кнопки
                            if em_cols[k].button(emoji, key=f"icon_btn_{i}_{j}_{k}"):
                                # Миттєве збереження
                                data["settings"]["custom_icons"][full_cat_name] = emoji
                                dh.save_data(data)
                                st.rerun()

                # --- ВИБІР КОЛЬОРУ ---
                default_color = current_colors.get(full_cat_name, "#444444")
                picked_color = st.color_picker("Колір", value=default_color, key=f"color_pick_{i}")
                pending_colors[full_cat_name] = picked_color

        st.write("")
        if st.button("💾 Зберегти кольори", use_container_width=True):
            # Оновлюємо масив кольорів
            data["settings"]["category_colors"] = pending_colors
            dh.save_data(data)
            st.success("Налаштування збережено!")
            st.rerun()