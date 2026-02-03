import streamlit as st
import pandas as pd
from PIL import Image
import ai_assistant as ai
import table_factory as tf
import data_handler as dh


# --- Хелпери для категорій (щоб не дублювати код) ---

def apply_display_categories(df, user_icons):
    """Додає іконки до категорій у DataFrame для краси."""
    if df.empty or 'category' not in df.columns:
        return df

    # Робимо копію, щоб не ламати оригінальні дані в пам'яті
    df_display = df.copy()

    def format_cat(cat_str):
        # Логіка та сама: розбиваємо рядок, шукаємо іконку
        parts = cat_str.split(" ", 1)
        if len(parts) < 2: return cat_str
        text = parts[1]
        # Якщо є кастомна іконка - беремо її, інакше лишаємо як було
        return f"{user_icons.get(cat_str, parts[0])} {text}"

    df_display['category'] = df_display['category'].apply(format_cat)
    return df_display


def restore_categories(data_list, user_icons):
    """Відновлює оригінальні назви категорій перед збереженням у JSON."""
    # Створюємо мапу: "Іконка Назва" -> "Оригінальна Назва"
    # Це потрібно, щоб база даних завжди була чиста
    reverse_map = {}
    for raw_cat in ai.CATEGORIES:
        parts = raw_cat.split(" ", 1)
        if len(parts) == 2:
            display_cat = f"{user_icons.get(raw_cat, parts[0])} {parts[1]}"
            reverse_map[display_cat] = raw_cat

    # Проходимось по списку і міняємо назад
    clean_data = []
    for item in data_list:
        # Копіюємо, щоб не чіпати UI об'єкт
        clean_item = item.copy()
        curr = clean_item.get("category")
        if curr in reverse_map:
            clean_item["category"] = reverse_map[curr]
        clean_data.append(clean_item)

    return clean_data


# --- Основні функції ---

def render_fridge(data):
    """Вкладка Холодильник"""
    st.header("🏢 Управління запасами")

    fridge_items = data["fridge"]

    # Метрики: рахуємо напряму зі списку (швидше, ніж створювати DF)
    if fridge_items:
        c1, c2, c3 = st.columns(3)
        c1.metric("Усього позицій", len(fridge_items))

        # Для складнішої агрегації DF все ж зручніший
        df = pd.DataFrame(fridge_items)
        c2.metric("Категорій", df['category'].nunique() if 'category' in df else 0)

        user_icons = data["settings"].get("custom_icons", {})
        top_cat = df['category'].value_counts().idxmax() if not df.empty else "—"

        # Тут трохи спростив виклик форматування
        c3.metric("Топ категорія",
                  apply_display_categories(pd.DataFrame({'category': [top_cat]}), user_icons)['category'][0])

    # Блок додавання (залишив логіку без змін, вона нормальна)
    with st.expander("➕ Додати продукти"):
        col_text, col_scan = st.columns(2)
        with col_text:
            st.subheader("📝 Текст")
            raw_input = st.text_input("Список через кому:", key="fridge_add", placeholder="молоко, сир...")
            if st.button("Розібрати список", key="btn_fridge_add", use_container_width=True):
                if raw_input:
                    with st.spinner("AI сортує..."):
                        items = ai.parse_fridge_input(raw_input)
                        data["fridge"].extend(items)
                        dh.save_data(data)
                        st.rerun()
        with col_scan:
            st.subheader("🧾 Чек")
            uploaded_file = st.file_uploader("Фото чека", type=["jpg", "jpeg", "png"], key="fridge_upl")
            if uploaded_file and st.button("🔍 Оцифрувати чек", key="btn_fridge_upl", use_container_width=True):
                with st.spinner("AI сканує..."):
                    items = ai.analyze_image(Image.open(uploaded_file))
                    data["fridge"].extend(items)
                    dh.save_data(data)
                    st.rerun()

    st.write("---")

    # Таблиця
    if fridge_items:
        st.subheader("📊 Холодильник")
        filter_options = ["Усі продукти"] + ai.CATEGORIES
        selected_cat = st.selectbox("🔍 Що показати?", filter_options)

        df = pd.DataFrame(fridge_items)
        user_icons = data["settings"].get("custom_icons", {})

        # Форматуємо категорії для відображення
        df_display = apply_display_categories(df, user_icons)

        # Фільтрація
        # Треба отримати "красиву" назву обраної категорії для порівняння
        temp_df = pd.DataFrame({'category': [selected_cat]})
        display_selected_cat = apply_display_categories(temp_df, user_icons)['category'][
            0] if selected_cat != "Усі продукти" else "Усі продукти"

        if display_selected_cat != "Усі продукти":
            df_to_show = df_display[df_display["category"] == display_selected_cat]
            should_group = False
        else:
            df_to_show = df_display.sort_values(['category', 'item'])
            should_group = True

        # Кольори для таблиці
        saved_colors = data["settings"].get("category_colors", {})
        # Генеруємо мапу кольорів на льоту, використовуючи "красиві" назви як ключі
        display_colors = {}
        for raw_cat, color in saved_colors.items():
            # Створюємо фейковий DF, щоб перевикористати функцію форматування
            fmt_cat = apply_display_categories(pd.DataFrame({'category': [raw_cat]}), user_icons)['category'][0]
            display_colors[fmt_cat] = color

        updated_data = tf.draw_pro_table(df_to_show, enable_grouping=should_group, color_map=display_colors)

        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Фіксувати зміни", use_container_width=True):
                # Перетворюємо назад у словник
                curr_data = updated_data if isinstance(updated_data, list) else updated_data.to_dict(orient="records")

                # Чистимо категорії від іконок перед записом у БД
                data["fridge"] = restore_categories(curr_data, user_icons)

                dh.save_data(data)
                st.success("Зміни збережено!")
                st.rerun()

        with col_clear:
            if st.button("🗑 Очистити холодильник", use_container_width=True):
                data["fridge"] = []
                dh.save_data(data)
                st.rerun()
    else:
        st.info("Холодильник порожній.")


def render_shopping(data):
    """Вкладка Покупки"""
    st.header("🛍 Що треба купити")

    # Додавання
    with st.expander("➕ Додати в список вручну"):
        shop_input = st.text_input("Назва продукту:", key="shop_text_add")
        if st.button("Додати", key="btn_shop_add"):
            if shop_input:
                with st.spinner("AI категоризує..."):
                    items = ai.parse_fridge_input(shop_input)
                    data["shopping_list"].extend(items)
                    dh.save_data(data)
                    st.rerun()

    shopping_items = data["shopping_list"]

    if shopping_items:
        st.caption("Виділи продукти та натисни 'Купив', щоб перенести їх у холодильник.")

        user_icons = data["settings"].get("custom_icons", {})
        df_shop = pd.DataFrame(shopping_items)

        # Використовуємо наш хелпер для красивих категорій
        df_display = apply_display_categories(df_shop, user_icons)

        # Кольори (аналогічно fridge)
        saved_colors = data["settings"].get("category_colors", {})
        display_colors = {}
        for raw_cat, color in saved_colors.items():
            fmt_cat = apply_display_categories(pd.DataFrame({'category': [raw_cat]}), user_icons)['category'][0]
            display_colors[fmt_cat] = color

        updated_shop_data = tf.draw_pro_table(df_display, enable_grouping=True, color_map=display_colors)

        c_save_shop, c_bought = st.columns(2)

        # Конвертуємо дані таблиці в список словників один раз
        table_data_dicts = updated_shop_data if isinstance(updated_shop_data, list) else updated_shop_data.to_dict(
            orient="records")

        with c_save_shop:
            if st.button("💾 Зберегти список", key="save_shop_list", use_container_width=True):
                # Відновлюємо "чисті" категорії
                data["shopping_list"] = restore_categories(table_data_dicts, user_icons)
                dh.save_data(data)
                st.success("Оновлено!")
                st.rerun()

        with c_bought:
            if st.button("✅ Я КУПИВ ЦЕ (В Холодильник)", use_container_width=True):
                # Відновлюємо категорії
                clean_items = restore_categories(table_data_dicts, user_icons)

                # Переносимо все в холодильник
                data["fridge"].extend(clean_items)
                data["shopping_list"] = []  # Очищаємо список покупок

                dh.save_data(data)
                st.balloons()
                st.success("Продукти перенесено в холодильник!")
                st.rerun()
    else:
        st.info("Список покупок порожній.")