import streamlit as st
import pandas as pd
from PIL import Image
import ai_assistant as ai
import table_factory as tf
import data_handler as dh


# --- [ 1. ВІЗУАЛЬНІ ХЕЛПЕРИ V1.0 ] ---

def apply_display_categories(df, user_icons):
    """
    Готує дані для відображення: додає іконки до назв категорій.
    Це дозволяє JavaScript у table_factory правильно розпізнавати рядки для фарбування.
    """
    if df.empty or 'category' not in df.columns:
        return df

    df_display = df.copy()

    def format_cat(cat_str):
        # Розділяємо "🍎 М'ясо" на іконку та назву
        parts = cat_str.split(" ", 1)
        if len(parts) < 2:
            return cat_str

        # Перевіряємо, чи є у користувача кастомна іконка для цієї категорії
        icon = user_icons.get(cat_str, parts[0])
        return f"{icon} {parts[1]}"

    df_display['category'] = df_display['category'].apply(format_cat)
    return df_display


def restore_categories(data_list, user_icons):
    """
    Обернена функція: прибирає іконки перед збереженням у JSON.
    Це критично важливо для чистоти бази даних стартапу.
    """
    # Створюємо мапу: "Кастомна_Іконка Назва" -> "Оригінальна_Категорія"
    reverse_map = {}
    for raw_cat in ai.CATEGORIES:
        parts = raw_cat.split(" ", 1)
        if len(parts) == 2:
            display_name = f"{user_icons.get(raw_cat, parts[0])} {parts[1]}"
            reverse_map[display_name] = raw_cat

    clean_data = []
    for item in data_list:
        clean_item = item.copy()
        curr_cat = clean_item.get("category")

        # Якщо категорія у форматі з іконкою — повертаємо оригінал
        if curr_cat in reverse_map:
            clean_item["category"] = reverse_map[curr_cat]
        clean_data.append(clean_item)

    return clean_data


# --- [ 2. ОСНОВНИЙ МОДУЛЬ: ХОЛОДИЛЬНИК ] ---

def render_fridge(data):
    """
    Рендеринг вкладки Холодильник (Inventory).
    Виводить метрики, блок додавання через AI та професійну таблицю AgGrid.
    """
    st.header("🏢 Управління запасами")

    # Завантаження ресурсів
    user_icons = data.get("settings", {}).get("custom_icons", {})
    saved_colors = data.get("settings", {}).get("category_colors", {})
    fridge_items = data.get("fridge", [])

    # === БЛОК МЕТРИК ===
    if fridge_items:
        m1, m2, m3 = st.columns(3)
        m1.metric("Усього позицій", len(fridge_items))

        df_temp = pd.DataFrame(fridge_items)
        if not df_temp.empty and 'category' in df_temp.columns:
            m2.metric("Категорій", df_temp['category'].nunique())
            top_cat = df_temp['category'].value_counts().idxmax()

            # Форматуємо топ-категорію для красивого виводу в метриці
            pretty_top = apply_display_categories(pd.DataFrame({'category': [top_cat]}), user_icons)['category'][0]
            m3.metric("Топ категорія", pretty_top)

    # === БЛОК ДОДАВАННЯ ПРОДУКТІВ ===
    with st.expander("➕ Поповнити холодильник (AI)"):
        col_txt, col_img = st.columns(2)

        with col_txt:
            st.subheader("📝 Текстовий ввід")
            raw_text = st.text_input("Введіть продукти через кому:", key="f_text_v1",
                                     placeholder="яблука 2кг, молоко...")
            if st.button("Розібрати список", key="f_btn_txt", use_container_width=True):
                if raw_text:
                    with st.spinner("AI сортує продукти..."):
                        new_items = ai.parse_fridge_input(raw_text)
                        data["fridge"].extend(new_items)
                        dh.save_data(data)
                        st.rerun()

        with col_img:
            st.subheader("📸 Оцифрування")
            uploaded_file = st.file_uploader("Фото чека або продуктів:", type=["jpg", "png", "jpeg"], key="f_img_v1")
            if uploaded_file and st.button("🔍 Оцифрувати", key="f_btn_img", use_container_width=True):
                with st.spinner("AI розпізнає продукти..."):
                    img_items = ai.analyze_image(Image.open(uploaded_file))
                    data["fridge"].extend(img_items)
                    dh.save_data(data)
                    st.rerun()

    st.divider()

    # === ПРОФЕСІЙНА ТАБЛИЦЯ (Inventory Grid) ===
    if fridge_items:
        st.subheader("📊 Поточний стан складу")

        # Фільтр по категоріях
        all_cats = ["Усі продукти"] + ai.CATEGORIES
        selected_cat = st.selectbox("🔍 Фільтр по виду продукту:", all_cats)

        # 1. Підготовка DataFrame (Суворий порядок колонок)
        df = pd.DataFrame(fridge_items)
        if "category" not in df.columns:
            df["category"] = "🧀 Інше"

        # Гарантуємо 3 колонки: Продукт, Кількість, Категорія (Вид)
        df = df[['item', 'amount', 'category']]

        # 2. Підготовка мапи кольорів (Форматуємо ключі для JS)
        display_colors = {}
        for raw_cat, color_hex in saved_colors.items():
            fmt_cat = apply_display_categories(pd.DataFrame({'category': [raw_cat]}), user_icons)['category'][0]
            display_colors[fmt_cat] = color_hex

        # 3. Підготовка даних для відображення (Іконки)
        df_display = apply_display_categories(df, user_icons)

        # 4. Логіка фільтрації
        temp_filter_df = pd.DataFrame({'category': [selected_cat]})
        display_filter_name = apply_display_categories(temp_filter_df, user_icons)['category'][
            0] if selected_cat != "Усі продукти" else "Усі продукти"

        if display_filter_name != "Усі продукти":
            df_to_show = df_display[df_display["category"] == display_filter_name]
        else:
            # Сортуємо для "зебри" або групування
            df_to_show = df_display.sort_values(['category', 'item'])

        # --- ВИКЛИК ТАБЛИЦІ ---
        # Використовуємо твою AgGrid фабрику
        updated_data = tf.draw_pro_table(
            df_to_show,
            enable_grouping=False,  # Вимикаємо дерево, щоб бачити 3-ю колонку окремо
            color_map=display_colors
        )

        # 5. Кнопки управління
        c_save, c_clear = st.columns(2)
        with c_save:
            if st.button("💾 Фіксувати зміни в базі", use_container_width=True):
                # Отримуємо дані з AgGrid
                raw_table_res = updated_data if isinstance(updated_data, list) else updated_data.to_dict(
                    orient="records")
                # Очищуємо іконки
                data["fridge"] = restore_categories(raw_table_res, user_icons)
                dh.save_data(data)
                st.success("Зміни успішно збережені!")
                st.rerun()

        with c_clear:
            if st.button("🗑 Очистити склад", use_container_width=True):
                data["fridge"] = []
                dh.save_data(data)
                st.rerun()
    else:
        st.info("Ваш холодильник порожній. Використовуйте блок вище, щоб додати продукти.")


# --- [ 3. МОДУЛЬ: СПИСОК ПОКУПОК ] ---

def render_shopping(data):
    """Управління списком покупок (Shopping List)."""
    st.header("🛍 План закупівель")

    user_icons = data.get("settings", {}).get("custom_icons", {})
    saved_colors = data.get("settings", {}).get("category_colors", {})
    shopping_items = data.get("shopping_list", [])

    with st.expander("➕ Додати в список вручну"):
        shop_item_name = st.text_input("Назва товару:", key="s_manual_v1")
        if st.button("Додати", key="s_btn_manual"):
            if shop_item_name:
                # Використовуємо AI для миттєвої категоризації
                new_shop_items = ai.parse_fridge_input(shop_item_name)
                data["shopping_list"].extend(new_shop_items)
                dh.save_data(data)
                st.rerun()

    if shopping_items:
        st.write("Позначте куплені товари та натисніть кнопку внизу.")

        # Підготовка таблиці (Аналогічно складу)
        df_shop = pd.DataFrame(shopping_items)[['item', 'amount', 'category']]
        df_shop_display = apply_display_categories(df_shop, user_icons)

        shop_colors = {}
        for rc, ch in saved_colors.items():
            fmt = apply_display_categories(pd.DataFrame({'category': [rc]}), user_icons)['category'][0]
            shop_colors[fmt] = ch

        # Рендеринг списку покупок
        updated_shop = tf.draw_pro_table(df_shop_display, enable_grouping=False, color_map=shop_colors)

        # Кнопки дій для покупок
        col_s1, col_s2 = st.columns(2)

        # Конвертуємо результат AgGrid
        shop_table_data = updated_shop if isinstance(updated_shop, list) else updated_shop.to_dict(orient="records")

        with col_s1:
            if st.button("💾 Зберегти список", key="s_save_list", use_container_width=True):
                data["shopping_list"] = restore_categories(shop_table_data, user_icons)
                dh.save_data(data)
                st.toast("Список оновлено!")

        with col_s2:
            if st.button("✅ ПЕРЕНЕСТИ В ХОЛОДИЛЬНИК", type="primary", use_container_width=True):
                # Відновлюємо чисті категорії
                clean_bought = restore_categories(shop_table_data, user_icons)

                # Переносимо все в холодильник
                data["fridge"].extend(clean_bought)
                # Очищуємо список покупок
                data["shopping_list"] = []

                dh.save_data(data)
                st.balloons()
                st.success(f"Перенесено {len(clean_bought)} продуктів!")
                st.rerun()
    else:
        st.info("Ваш список покупок порожній")