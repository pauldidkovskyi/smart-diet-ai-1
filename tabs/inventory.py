import streamlit as st
import pandas as pd
from PIL import Image
import ai_assistant as ai
import table_factory as tf
import data_handler as dh


def get_display_category(base_cat_string, user_icons):
    """Допоміжна функція для іконок"""
    parts = base_cat_string.split(" ", 1)
    if len(parts) < 2: return base_cat_string
    icon, text = parts[0], parts[1]
    if base_cat_string in user_icons:
        return f"{user_icons[base_cat_string]} {text}"
    return base_cat_string


def render_fridge(data):
    """Вкладка Склад"""
    st.header("🏢 Управління запасами")

    # Метрики
    if data["fridge"]:
        df = pd.DataFrame(data["fridge"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Усього позицій", len(df))
        c2.metric("Категорій", df['category'].nunique() if 'category' in df else 0)

        user_icons = data["settings"].get("custom_icons", {})
        top_cat = df['category'].value_counts().idxmax() if not df.empty else "—"
        c3.metric("Топ категорія", get_display_category(top_cat, user_icons))

    # Блок додавання
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
    if data["fridge"]:
        st.subheader("📊 Інтерактивний інвентар")
        filter_options = ["Усі продукти"] + ai.CATEGORIES
        selected_cat = st.selectbox("🔍 Що показати?", filter_options)

        df = pd.DataFrame(data["fridge"])
        user_icons = data["settings"].get("custom_icons", {})

        if not df.empty:
            df['category'] = df['category'].apply(lambda x: get_display_category(x, user_icons))

        display_selected_cat = get_display_category(selected_cat,
                                                    user_icons) if selected_cat != "Усі продукти" else "Усі продукти"

        if display_selected_cat != "Усі продукти":
            df_to_show = df[df["category"] == display_selected_cat]
            should_group = False
        else:
            df_to_show = df.sort_values(['category', 'item'])
            should_group = True

        saved_colors = data["settings"].get("category_colors", {})
        display_colors = {get_display_category(k, user_icons): v for k, v in saved_colors.items()}

        updated_df_data = tf.draw_pro_table(df_to_show, enable_grouping=should_group, color_map=display_colors)

        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 Фіксувати зміни", use_container_width=True):
                reverse_map = {get_display_category(c, user_icons): c for c in ai.CATEGORIES}
                temp_data = updated_df_data if isinstance(updated_df_data, list) else updated_df_data.to_dict(
                    orient="records")

                for item in temp_data:
                    curr = item.get("category")
                    if curr in reverse_map: item["category"] = reverse_map[curr]

                data["fridge"] = temp_data
                dh.save_data(data)
                st.success("Зміни збережено!")
                st.rerun()

        with col_clear:
            if st.button("🗑 Очистити склад", use_container_width=True):
                data["fridge"] = []
                dh.save_data(data)
                st.rerun()
    else:
        st.info("Холодильник порожній.")


def render_shopping(data):
    """Вкладка Покупки"""
    st.header("🛍 Що треба купити")

    with st.expander("➕ Додати в список вручну"):
        shop_input = st.text_input("Назва продукту:", key="shop_text_add")
        if st.button("Додати", key="btn_shop_add"):
            if shop_input:
                with st.spinner("AI категоризує..."):
                    items = ai.parse_fridge_input(shop_input)
                    data["shopping_list"].extend(items)
                    dh.save_data(data)
                    st.rerun()

    if data["shopping_list"]:
        st.caption("Виділи продукти та натисни 'Купив', щоб перенести їх у холодильник.")

        user_icons = data["settings"].get("custom_icons", {})
        df_shop = pd.DataFrame(data["shopping_list"])
        if not df_shop.empty:
            df_shop['category'] = df_shop['category'].apply(lambda x: get_display_category(x, user_icons))

        saved_colors = data["settings"].get("category_colors", {})
        display_colors = {get_display_category(k, user_icons): v for k, v in saved_colors.items()}

        updated_shop_data = tf.draw_pro_table(df_shop, enable_grouping=True, color_map=display_colors)

        c_save_shop, c_bought = st.columns(2)

        with c_save_shop:
            if st.button("💾 Зберегти список", key="save_shop_list", use_container_width=True):
                reverse_map = {get_display_category(c, user_icons): c for c in ai.CATEGORIES}
                temp_shop = updated_shop_data if isinstance(updated_shop_data, list) else updated_shop_data.to_dict(
                    orient="records")
                for item in temp_shop:
                    curr = item.get("category")
                    if curr in reverse_map: item["category"] = reverse_map[curr]

                data["shopping_list"] = temp_shop
                dh.save_data(data)
                st.success("Оновлено!")
                st.rerun()

        with c_bought:
            if st.button("✅ Я КУПИВ ЦЕ (В Холодильник)", use_container_width=True):
                temp_shop = updated_shop_data if isinstance(updated_shop_data, list) else updated_shop_data.to_dict(
                    orient="records")
                reverse_map = {get_display_category(c, user_icons): c for c in ai.CATEGORIES}
                final_items = []
                for item in temp_shop:
                    curr = item.get("category")
                    if curr in reverse_map: item["category"] = reverse_map[curr]
                    final_items.append(item)

                data["fridge"].extend(final_items)
                data["shopping_list"] = []
                dh.save_data(data)
                st.balloons()
                st.success("Продукти перенесено на склад!")
                st.rerun()
    else:
        st.info("Список покупок порожній.")