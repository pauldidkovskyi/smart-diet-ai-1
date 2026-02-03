import streamlit as st
import datetime
import time
import copy
import pandas as pd
import ai_assistant as ai
import data_handler as dh

# --- КОНСТАНТИ ТА ХЕЛПЕРИ ---

MEAL_TYPES = ["Сніданок", "Обід", "Вечеря", "Перекус"]


def get_or_create_day_plan(data, date_str):
    """
    Безпечно дістає план на день. Якщо його нема або там старий формат (list)
    — створює нову структуру.
    """
    if date_str not in data["diet_plan"] or isinstance(data["diet_plan"][date_str], list):
        data["diet_plan"][date_str] = {m: [] for m in MEAL_TYPES}
    return data["diet_plan"][date_str]


def process_cooking(data, cook_result, meal_type="Обід"):
    """
    Централізована логіка: списати продукти з холодильника -> записати страву в історію.
    Повертає missing_items, якщо чогось бракує.
    """
    missing = cook_result.get('missing_items', [])
    if missing:
        return missing  # Не готуємо, якщо чогось нема

    # Списуємо продукти
    for r_item in cook_result.get('items_to_remove', []):
        if r_item in data["fridge"]:
            data["fridge"].remove(r_item)

    # Записуємо в план харчування (сьогодні)
    today_str = str(datetime.date.today())
    day_plan = get_or_create_day_plan(data, today_str)

    day_plan[meal_type].append({
        "dish": cook_result.get('dish_name', 'AI Dish'),
        "calories": cook_result.get('calories', 0),
        "status": "done"
    })

    return []  # Повертаємо пустий список, бо все ок


# --- ОСНОВНІ ФУНКЦІЇ ---

def render_planner(data):
    st.header("📅 Планувальник харчування")

    col_date, col_stats = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("Обери день", value=datetime.date.today())
        str_date = str(selected_date)
        # Використовуємо хелпер замість ручної перевірки
        day_plan = get_or_create_day_plan(data, str_date)

    # Рахуємо калорії через генератор (швидше і компактніше)
    all_items = [item for meal in day_plan.values() for item in meal]
    total_cals = sum(item.get('calories', 0) for item in all_items)
    eaten_cals = sum(item.get('calories', 0) for item in all_items if item.get('status') == 'done')

    with col_stats:
        st.write("")
        m1, m2 = st.columns(2)
        m1.metric("📌 План на день", f"{total_cals} ккал")
        m2.metric("✅ Вже з'їдено", f"{eaten_cals} ккал", delta=f"{eaten_cals - total_cals}")

    st.write("---")

    for m_type in MEAL_TYPES:
        with st.expander(f"🍽 {m_type}", expanded=True):
            items = day_plan[m_type]
            if items:
                for idx, dish in enumerate(items):
                    c_chk, c_name, c_cal, c_del = st.columns([0.1, 0.6, 0.2, 0.1])
                    is_done = dish.get('status') == 'done'

                    # Логіка чекбокса
                    if c_chk.checkbox("Done", value=is_done, key=f"chk_{str_date}_{m_type}_{idx}",
                                      label_visibility="collapsed"):
                        if not is_done:
                            dish['status'] = 'done'
                            dh.save_data(data)
                            st.rerun()
                    else:
                        if is_done:
                            dish['status'] = 'planned'
                            dh.save_data(data)
                            st.rerun()

                    dish_text = f"~~{dish['dish']}~~" if is_done else f"**{dish['dish']}**"
                    c_name.markdown(dish_text)
                    c_cal.caption(f"{dish['calories']} ккал")

                    if c_del.button("❌", key=f"del_{str_date}_{m_type}_{idx}"):
                        day_plan[m_type].pop(idx)
                        dh.save_data(data)
                        st.rerun()
            else:
                st.caption("Поки нічого не заплановано")

            # Вкладки додавання
            t_man, t_book = st.tabs(["📝 Вручну", "📖 З книги"])

            with t_man:
                c_in, c_btn = st.columns([3, 1])
                new_dish = c_in.text_input("Страва", key=f"in_{str_date}_{m_type}", label_visibility="collapsed")
                if c_btn.button("➕", key=f"add_{str_date}_{m_type}") and new_dish:
                    with st.spinner("⏳"):
                        cals = ai.get_calories_from_ai(new_dish, "порція")
                    day_plan[m_type].append({"dish": new_dish, "calories": cals, "status": "planned"})
                    dh.save_data(data)
                    st.rerun()

            with t_book:
                if data["recipes"]:
                    titles = [r["title"] for r in data["recipes"]]
                    sel_rec = st.selectbox("Рецепт", titles, key=f"sel_rec_{str_date}_{m_type}",
                                           label_visibility="collapsed")
                    if st.button("📥 Додати", key=f"btn_rec_{str_date}_{m_type}"):
                        with st.spinner("Рахую..."):
                            cals = ai.get_calories_from_ai(sel_rec, "порція")
                        day_plan[m_type].append({"dish": sel_rec, "calories": cals, "status": "planned"})
                        dh.save_data(data)
                        st.rerun()
                else:
                    st.caption("Книга порожня")

    st.write("---")
    # Логіка копіювання
    with st.popover("🔄 Скопіювати план"):
        src_date = st.date_input("Звідки брати?", value=selected_date - datetime.timedelta(days=1))
        src_str = str(src_date)

        if st.button("✅ Копіювати", use_container_width=True):
            if src_str in data["diet_plan"] and isinstance(data["diet_plan"][src_str], dict):
                # Deepcopy - це правильно, тут лишаємо
                new_plan = copy.deepcopy(data["diet_plan"][src_str])
                # Скидаємо статуси на 'planned'
                for m_list in new_plan.values():
                    for item in m_list: item['status'] = 'planned'

                data["diet_plan"][str_date] = new_plan
                dh.save_data(data)
                st.success("Скопійовано!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("На обрану дату немає плану.")


def render_chef(data):
    st.header("👨‍🍳 Консультація Шефа")

    # Ініціалізуємо session_state, щоб не було помилок при першому запуску
    if "missing_products" not in st.session_state: st.session_state.missing_products = []
    if "last_ai_response" not in st.session_state: st.session_state.last_ai_response = None

    user_q = st.text_input("Що приготувати?", key="chef_q")
    col1, col2 = st.columns([2, 1])
    is_strict = col1.checkbox("ТІЛЬКИ з наявного", value=False)

    if col2.button("Спитати шефа", use_container_width=True):
        with st.spinner("Думаю..."):
            st.session_state.last_ai_response = ai.ask_chef(data["fridge"], data["history"], user_q,
                                                            strict_mode=is_strict)
            st.session_state.missing_products = []  # Скидаємо старі помилки

    if st.session_state.last_ai_response:
        resp = st.session_state.last_ai_response
        st.info("Відповідь:")
        st.markdown(resp)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Зберегти рецепт"):
                # Парсинг відповіді
                parts = resp.split("|||")
                title, content = (parts[0], parts[1]) if len(parts) > 1 else ("AI Рецепт", resp)

                data["recipes"].append({
                    "title": title.strip(),
                    "content": content.strip(),
                    "date": str(datetime.date.today()),
                    "source": "AI Шеф"
                })
                dh.save_data(data)
                st.success("Збережено в книгу!")

        with c2:
            if st.button("🍳 Приготувати"):
                with st.spinner("Перевіряю продукти..."):
                    cook_res = ai.analyze_recipe_for_cooking(resp, data["fridge"])
                    if cook_res:
                        # Використовуємо наш новий хелпер
                        missing = process_cooking(data, cook_res)

                        if missing:
                            st.session_state.missing_products = missing
                            st.toast("Чогось не вистачає!", icon="🛒")
                        else:
                            dh.save_data(data)
                            st.balloons()
                            st.success(f"Приготовано! +{cook_res.get('calories', 0)} ккал")
                            st.rerun()

        # Блок з відсутніми продуктами
        if st.session_state.missing_products:
            st.warning("Треба докупити:")
            st.dataframe(pd.DataFrame(st.session_state.missing_products)[["item", "amount"]], hide_index=True)
            if st.button("🛒 Додати в список покупок"):
                data["shopping_list"].extend(st.session_state.missing_products)
                dh.save_data(data)
                st.session_state.missing_products = []
                st.success("Додано!")
                time.sleep(1)
                st.rerun()


def render_recipes(data):
    st.header("📖 Моя Кулінарна Книга")

    # Ініціалізація змінних сесії (безпека)
    if "missing_products" not in st.session_state: st.session_state.missing_products = []

    with st.expander("➕ Створити рецепт"):
        t = st.text_input("Назва", key="rec_title")
        c = st.text_area("Опис", key="rec_content")
        if st.button("Зберегти", key="rec_save") and t and c:
            data["recipes"].append({"title": t, "content": c, "date": str(datetime.date.today())})
            dh.save_data(data)
            st.rerun()

    if not data["recipes"]:
        st.info("Ще немає рецептів.")
        return

    for i, r in enumerate(data["recipes"]):
        with st.expander(f"🥘 {r['title']}"):
            st.markdown(r['content'])
            c_cook, c_plan, c_del = st.columns([1, 1, 0.5])

            with c_cook:
                if st.button("🍳 Готувати", key=f"cook_rec_{i}", use_container_width=True):
                    cook_res = ai.analyze_recipe_for_cooking(r['content'], data["fridge"])
                    # Примусово додаємо назву, якщо AI не повернув її (бо тут ми точно знаємо назву)
                    if cook_res: cook_res['dish_name'] = r['title']

                    missing = process_cooking(data, cook_res) if cook_res else ["Error parsing"]

                    if missing:
                        st.session_state.missing_products = missing
                        st.error("Не вистачає продуктів!")
                    else:
                        dh.save_data(data)
                        st.success("Приготовано!")
                        st.rerun()

            with c_plan:
                with st.popover("📅 В календар", use_container_width=True):
                    p_date = st.date_input("Дата", datetime.date.today(), key=f"pd_{i}")
                    p_meal = st.selectbox("Прийом", MEAL_TYPES, key=f"pm_{i}")

                    if st.button("Записати", key=f"ps_{i}"):
                        cals = ai.get_calories_from_ai(r['title'], "порція")

                        target_plan = get_or_create_day_plan(data, str(p_date))
                        target_plan[p_meal].append({
                            "dish": r['title'],
                            "calories": cals,
                            "status": "planned"
                        })
                        dh.save_data(data)
                        st.success("Додано!")
                        st.rerun()

            with c_del:
                if st.button("🗑", key=f"del_{i}"):
                    data["recipes"].pop(i)
                    dh.save_data(data)
                    st.rerun()

            # Якщо є дефіцит продуктів (відображається під конкретним рецептом або загально)
            if st.session_state.missing_products:
                st.warning("Є дефіцит (див. вище)")
                # Тут можна дублювати кнопку додавання в кошик,
                # але краще винести її в загальний блок, щоб не спамити кнопками