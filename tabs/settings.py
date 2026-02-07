import streamlit as st
import data_handler as dh
import os


def render_settings(data):
    st.header("⚙️ Налаштування системи")

    # Ініціалізація налаштувань у базі, якщо їх немає
    if "settings" not in data:
        data["settings"] = {"theme_color": "#CCFF00", "language": "UA"}

    # --- БЛОК 1: ВІЗУАЛІЗАЦІЯ ---
    st.subheader("🎨 Персоналізація")

    with st.container(border=True):
        c1, c2 = st.columns(2)

        with c1:
            # Вибір акцентного кольору для FOOD режиму
            current_color = data["settings"].get("theme_color", "#CCFF00")
            new_color = st.color_picker("Акцентний колір (Food Mode)", value=current_color)

            if new_color != current_color:
                data["settings"]["theme_color"] = new_color
                dh.save_data(data)
                st.rerun()  # Перезавантаження, щоб застосувати колір

        with c2:
            st.info(f"Поточний колір: **{new_color}**")
            st.caption("Цей колір використовується для діаграм та кнопок у режимі харчування.")

    st.divider()

    # --- БЛОК 2: УПРАВЛІННЯ ДАНИМИ (DANGER ZONE) ---
    st.subheader("💾 Управління даними")
    st.caption("Будь обережний, ці дії незворотні.")

    # Використовуємо expander для безпеки, щоб випадково не натиснути
    with st.expander("🗑 Відкрити зону видалення", expanded=False):

        col_clear_1, col_clear_2 = st.columns(2)

        with col_clear_1:
            st.write("📦 **Очищення сховищ**")

            if st.button("Очистити Холодильник", use_container_width=True):
                data["fridge"] = []
                dh.save_data(data)
                st.toast("Холодильник порожній!", icon="🗑")
                time.sleep(1)
                st.rerun()

            if st.button("Очистити Список покупок", use_container_width=True):
                data["shopping_list"] = []
                dh.save_data(data)
                st.toast("Список покупок очищено!", icon="🗑")
                st.rerun()

        with col_clear_2:
            st.write("☢️ **Повне скидання**")

            # Подвійний захист від дурня (Checkbox + Button)
            confirm_reset = st.checkbox("Я розумію, що втрачу всі дані")

            if st.button("⚠️ FACTORY RESET", type="primary", disabled=not confirm_reset, use_container_width=True):
                # Скидаємо все до дефолту
                data.clear()
                data["fridge"] = []
                data["shopping_list"] = []
                data["recipes"] = []
                data["profile"] = {}
                data["settings"] = {"theme_color": "#CCFF00"}
                data["diary"] = {}

                dh.save_data(data)
                st.error("Систему повністю скинуто до заводських налаштувань.")
                st.balloons()
                st.rerun()

    st.divider()

    # --- БЛОК 3: ІНФО ---
    with st.container():
        st.caption(f"📂 Файл бази даних: `{os.path.abspath('data.json')}`")
        st.caption(f"📊 Кількість записів у щоденнику: {len(data.get('diary', {}))}")
        st.caption("v2.5 Pro Mobile Build")