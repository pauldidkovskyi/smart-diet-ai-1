import streamlit as st
import pandas as pd
import datetime
import ai_assistant as ai  # Потрібно для категорій в налаштуваннях


def get_combined_data(data):
    """
    Збирає історію з усіх джерел (старий журнал + новий планувальник)
    і перетворює на Pandas DataFrame з правильною датою.
    """
    all_records = []

    # 1. Дані зі старого журналу (history)
    # Якщо там немає дати, ставимо сьогоднішню (або ігноруємо, але краще зберегти)
    for h in data.get("history", []):
        record_date = h.get("date", str(datetime.date.today()))
        all_records.append({
            "date": pd.to_datetime(record_date),
            "name": h.get("name", "Невідомо"),
            "calories": h.get("calories", 0)
        })

    # 2. Дані з Планувальника (diet_plan)
    # Тільки ті, що мають статус 'done'
    diet_plan = data.get("diet_plan", {})
    if isinstance(diet_plan, dict):
        for date_str, meals in diet_plan.items():
            if isinstance(meals, dict):  # Перевірка структури
                for meal_type, dishes in meals.items():
                    for dish in dishes:
                        if dish.get('status') == 'done':
                            all_records.append({
                                "date": pd.to_datetime(date_str),
                                "name": dish.get('dish', "Страва"),
                                "calories": dish.get('calories', 0)
                            })

    if not all_records:
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    # Сортуємо за датою
    df = df.sort_values(by="date")
    return df


def render_analytics(data):
    st.header("📊 Аналітика харчування")

    # Отримуємо чистий DataFrame
    df = get_combined_data(data)

    if df.empty:
        st.info("Ще немає даних для аналітики. Почніть відмічати виконані страви у Планувальнику!")
        render_settings(data)  # Показуємо налаштування навіть якщо пусто
        return

    # --- МЕТРИКИ (ЗАГАЛЬНІ) ---
    total_cals = df['calories'].sum()
    avg_cals = df['calories'].mean()
    days_tracked = df['date'].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("🔥 Всього спожито", f"{total_cals:,.0f} ккал")
    m2.metric("📅 Днів з трекінгом", days_tracked)
    # Середнє рахуємо як (Всього / Кількість унікальних днів)
    real_avg = total_cals / days_tracked if days_tracked > 0 else 0
    m3.metric("⚖️ Середнє за день", f"{real_avg:,.0f} ккал")

    st.write("---")

    # --- ВКЛАДКИ ЧАСУ ---
    tab_day, tab_month, tab_year = st.tabs(["📅 По днях", "🗓 По місяцях", "📆 По роках"])

    # 1. ПО ДНЯХ
    with tab_day:
        st.subheader("Динаміка за останні 30 днів")
        # Групуємо по даті, сумуємо калорії
        daily_df = df.groupby(df['date'].dt.date)['calories'].sum().reset_index()
        daily_df.columns = ['Дата', 'Калорії']

        # Показуємо тільки останні 30 записів
        st.bar_chart(daily_df.tail(30).set_index('Дата'), color="#FF4B4B")

        with st.expander("Детальна таблиця по днях"):
            st.dataframe(daily_df.sort_values('Дата', ascending=False), use_container_width=True)

    # 2. ПО МІСЯЦЯХ
    with tab_month:
        st.subheader("Підсумки по місяцях")
        # Створюємо колонку "Рік-Місяць"
        df['month_year'] = df['date'].dt.to_period('M').astype(str)
        monthly_df = df.groupby('month_year')['calories'].sum().reset_index()
        monthly_df.columns = ['Місяць', 'Калорії']

        st.bar_chart(monthly_df.set_index('Місяць'), color="#4BFF4B")
        st.caption("Тут сумуються всі калорії за календарний місяць.")

    # 3. ПО РОКАХ
    with tab_year:
        st.subheader("Річна статистика")
        df['year'] = df['date'].dt.year.astype(
            str)  # Перетворюємо рік на рядок, щоб графік не думав що це число (2,023.5)
        yearly_df = df.groupby('year')['calories'].sum().reset_index()
        yearly_df.columns = ['Рік', 'Калорії']

        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.bar_chart(yearly_df.set_index('Рік'), color="#4B4BFF")
        with col_table:
            st.dataframe(yearly_df, hide_index=True)

    st.write("---")
    render_settings(data)


def render_settings(data):
    """Блок налаштувань винесено в окрему функцію для чистоти"""
    with st.expander("🎨 Налаштування стилю (Іконки та Кольори)"):
        st.caption("Натисни на іконку, щоб змінити її. Обери колір для підсвітки.")
        current_colors = data["settings"].get("category_colors", {})
        current_icons = data["settings"].get("custom_icons", {})

        EMOJI_OPTIONS = {
            "М'ясо та Риба": ["🥩", "🍗", "🍖", "🥓", "🍔", "🍤", "🐟", "🍣"],
            "Овочі та Фрукти": ["🥦", "🍅", "🍆", "🌽", "🥕", "🥗", "🥔", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓"],
            "Молочні продукти": ["🥛", "🍼", "☕", "🫖", "🧀", "🍦"],
            "Бакалія": ["🍞", "🥐", "🥖", "🥨", "🥞", "🍝", "🍜", "🍚", "🍛", "🍙"],
            "Інше": ["🧀", "🥚", "🍕", "🌭", "🥪", "🌮", "🌯", "🥫", "🍱", "🥡", "🍫", "🍬", "🍭"]
        }

        cols = st.columns(len(ai.CATEGORIES))
        new_colors = {}
        new_icons = current_icons.copy()

        for i, full_cat_name in enumerate(ai.CATEGORIES):
            parts = full_cat_name.split(" ", 1)
            cat_pure_name = parts[1] if len(parts) > 1 else full_cat_name
            with cols[i]:
                st.markdown(f"**{cat_pure_name}**")
                active_icon = current_icons.get(full_cat_name, parts[0])

                # Popover для вибору іконки
                with st.popover(f"Іконка: {active_icon}"):
                    st.write("Обери нову:")
                    emoji_list = EMOJI_OPTIONS.get(cat_pure_name, EMOJI_OPTIONS["Інше"])
                    for j in range(0, len(emoji_list), 4):
                        row_emojis = emoji_list[j:j + 4]
                        em_cols = st.columns(4)
                        for k, emoji in enumerate(row_emojis):
                            if em_cols[k].button(emoji, key=f"icon_{i}_{j}_{k}"):
                                new_icons[full_cat_name] = emoji
                                st.rerun()

                default_color = current_colors.get(full_cat_name, "#444444")
                picked_color = st.color_picker(f"Колір", value=default_color, key=f"color_{i}")
                new_colors[full_cat_name] = picked_color

        if st.button("💾 Зберегти налаштування", use_container_width=True):
            data["settings"]["category_colors"] = new_colors
            data["settings"]["custom_icons"] = new_icons

            # Збереження через модуль data_handler
            # Оскільки ми всередині модуля, треба імпортувати або передати функцію
            # Але тут простіше просто викликати save з глобального контексту main,
            # проте правильніше зробити імпорт тут:
            import data_handler as dh
            dh.save_data(data)
            st.success("Стиль оновлено!")
            st.rerun()