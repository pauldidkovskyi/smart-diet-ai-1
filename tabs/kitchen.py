import streamlit as st
import datetime
import time
import copy
import pandas as pd
import ai_assistant as ai
import data_handler as dh


def render_planner(data):
    st.header("📅 Планувальник харчування")

    col_date, col_stats = st.columns([1, 2])
    with col_date:
        selected_date = st.date_input("Обери день", value=datetime.date.today())
        str_date = str(selected_date)

        if str_date not in data["diet_plan"]:
            data["diet_plan"][str_date] = {"Сніданок": [], "Обід": [], "Вечеря": [], "Перекус": []}

    day_plan = data["diet_plan"][str_date]
    if isinstance(day_plan, list): day_plan = {"Сніданок": [], "Обід": [], "Вечеря": [], "Перекус": []}

    total_cals = 0
    eaten_cals = 0
    for m_type, items in day_plan.items():
        for it in items:
            total_cals += it.get('calories', 0)
            if it.get('status') == 'done':
                eaten_cals += it.get('calories', 0)

    with col_stats:
        st.write("")
        m1, m2 = st.columns(2)
        m1.metric("📌 План на день", f"{total_cals} ккал")
        m2.metric("✅ Вже з'їдено", f"{eaten_cals} ккал", delta=f"{eaten_cals - total_cals}")

    st.write("---")
    meal_types = ["Сніданок", "Обід", "Вечеря", "Перекус"]

    for m_type in meal_types:
        with st.expander(f"🍽 {m_type}", expanded=True):
            if day_plan[m_type]:
                for idx, dish in enumerate(day_plan[m_type]):
                    col_check, col_name, col_cal, col_del = st.columns([0.1, 0.6, 0.2, 0.1])
                    is_done = dish.get('status') == 'done'

                    if col_check.checkbox("Done", value=is_done, key=f"chk_{str_date}_{m_type}_{idx}",
                                          label_visibility="collapsed"):
                        if dish.get('status') != 'done':
                            dish['status'] = 'done'
                            dh.save_data(data)
                            st.rerun()
                    else:
                        if dish.get('status') == 'done':
                            dish['status'] = 'planned'
                            dh.save_data(data)
                            st.rerun()

                    dish_text = f"~~{dish['dish']}~~" if is_done else f"**{dish['dish']}**"
                    col_name.markdown(dish_text)
                    col_cal.caption(f"{dish['calories']} ккал")

                    if col_del.button("❌", key=f"del_{str_date}_{m_type}_{idx}"):
                        day_plan[m_type].pop(idx)
                        dh.save_data(data)
                        st.rerun()
            else:
                st.caption("Поки нічого не заплановано")

            t_man, t_book = st.tabs(["📝 Вручну", "📖 З книги рецептів"])

            with t_man:
                c_input, c_btn = st.columns([3, 1])
                new_dish = c_input.text_input("Назва страви", key=f"in_{str_date}_{m_type}",
                                              placeholder="Напр. Вівсянка", label_visibility="collapsed")
                if c_btn.button("➕ Додати", key=f"add_{str_date}_{m_type}"):
                    if new_dish:
                        with st.spinner("⏳"):
                            cals = ai.get_calories_from_ai(new_dish, "порція")
                        day_plan[m_type].append({"dish": new_dish, "calories": cals, "status": "planned"})
                        dh.save_data(data)
                        st.rerun()

            with t_book:
                if data["recipes"]:
                    recipe_titles = [r["title"] for r in data["recipes"]]
                    selected_rec = st.selectbox("Обери рецепт", recipe_titles, key=f"sel_rec_{str_date}_{m_type}")

                    if st.button("📥 Додати рецепт", key=f"add_rec_btn_{str_date}_{m_type}"):
                        with st.spinner("Рахую калорії..."):
                            cals = ai.get_calories_from_ai(selected_rec, "порція")
                        day_plan[m_type].append({"dish": selected_rec, "calories": cals, "status": "planned"})
                        dh.save_data(data)
                        st.success(f"Додано: {selected_rec}")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.info("Ваша кулінарна книга порожня.")

    st.write("---")
    with st.popover("🔄 Скопіювати план з іншого дня", use_container_width=True):
        st.write("Оберіть дату, з якої взяти меню:")
        source_date_obj = st.date_input("Дата-джерело", value=selected_date - datetime.timedelta(days=1),
                                        key="copy_source_date")
        source_date_str = str(source_date_obj)
        st.caption(f"Увага: Це замінить поточний план на {str_date}!")

        if st.button("✅ Застосувати копіювання", use_container_width=True):
            if source_date_str in data["diet_plan"] and isinstance(data["diet_plan"][source_date_str], dict):
                data["diet_plan"][str_date] = copy.deepcopy(data["diet_plan"][source_date_str])
                for meal_list in data["diet_plan"][str_date].values():
                    for item in meal_list:
                        item['status'] = 'planned'
                dh.save_data(data)
                st.success(f"Успішно скопійовано з {source_date_str}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"На {source_date_str} немає збереженого плану.")


def render_chef(data):
    st.header("👨‍🍳 Консультація Шефа")
    user_q = st.text_input("Що приготувати?", key="chef_q")

    col_opt1, col_opt2 = st.columns([2, 1])
    with col_opt1:
        is_strict = st.checkbox("🥗 Готувати ТІЛЬКИ з наявних продуктів?", value=False)
    with col_opt2:
        btn_ask = st.button("Спитати шефа", key="btn_chef_ask", use_container_width=True)

    if btn_ask:
        with st.spinner("Шеф аналізує холодильник..."):
            st.session_state.last_ai_response = ai.ask_chef(data["fridge"], data["history"], user_q,
                                                            strict_mode=is_strict)
            st.session_state.missing_products = []

    if st.session_state.last_ai_response:
        st.info("Відповідь Шефа:")
        st.markdown(st.session_state.last_ai_response)

        c_sh1, c_sh2 = st.columns(2)
        with c_sh1:
            if st.button("💾 Зберегти рецепт", key="chef_save"):
                res = ai.format_recipe(st.session_state.last_ai_response)
                title, content = res.split("|||") if "|||" in res else ("AI Рецепт", res)
                data["recipes"].append(
                    {"title": title.strip(), "content": content.strip(), "date": str(datetime.date.today()),
                     "source": "AI Шеф"})
                dh.save_data(data)
                st.success("Збережено!")

        with c_sh2:
            if st.button("🍳 Приготувати / Аналіз", key="chef_cook"):
                with st.spinner("Перевіряю продукти..."):
                    cook = ai.analyze_recipe_for_cooking(st.session_state.last_ai_response, data["fridge"])
                    if cook:
                        missing = cook.get('missing_items', [])
                        if missing:
                            st.session_state.missing_products = missing
                            st.toast("Знайдено відсутні продукти!", icon="🛒")
                        else:
                            for r_item in cook.get('items_to_remove', []):
                                if r_item in data["fridge"]: data["fridge"].remove(r_item)
                            today_str = str(datetime.date.today())
                            if today_str not in data["diet_plan"]: data["diet_plan"][today_str] = {"Сніданок": [],
                                                                                                   "Обід": [],
                                                                                                   "Вечеря": [],
                                                                                                   "Перекус": []}
                            data["diet_plan"][today_str]["Обід"].append({
                                "dish": cook.get('dish_name', 'AI'),
                                "calories": cook.get('calories', 0),
                                "status": "done"
                            })
                            dh.save_data(data)
                            st.success(f"Готово! +{cook.get('calories', 0)} ккал")
                            st.rerun()

        if st.session_state.missing_products:
            st.warning("🛑 Увага! Цього не вистачає:")
            st.dataframe(pd.DataFrame(st.session_state.missing_products)[["item", "amount"]], hide_index=True)
            if st.button("🛒 Додати відсутнє в Список Покупок?", key="add_missing_chef"):
                data["shopping_list"].extend(st.session_state.missing_products)
                dh.save_data(data)
                st.success("Додано в список покупок!")
                st.session_state.missing_products = []
                time.sleep(1)
                st.rerun()


def render_recipes(data):
    st.header("📖 Моя Кулінарна Книга")
    with st.expander("➕ Додати свій рецепт"):
        t = st.text_input("Назва", key="rec_title")
        c = st.text_area("Текст", key="rec_content")
        if st.button("Зберегти", key="rec_save"):
            if t and c:
                data["recipes"].append({"title": t, "content": c, "date": str(datetime.date.today())})
                dh.save_data(data)
                st.rerun()

    if data["recipes"]:
        for i, r in enumerate(data["recipes"]):
            with st.expander(f"🥘 {r['title']}"):
                st.markdown(r['content'])
                c_cook, c_plan, c_del = st.columns([1, 1, 0.5])

                with c_cook:
                    if st.button("🍳 Приготувати", key=f"cook_rec_{i}", use_container_width=True):
                        cook = ai.analyze_recipe_for_cooking(r['content'], data["fridge"])
                        if cook:
                            missing = cook.get('missing_items', [])
                            if missing:
                                st.session_state.missing_products = missing
                                st.error("Не вистачає!")
                            else:
                                for r_item in cook.get('items_to_remove', []):
                                    if r_item in data["fridge"]: data["fridge"].remove(r_item)
                                today_str = str(datetime.date.today())
                                if today_str not in data["diet_plan"]: data["diet_plan"][today_str] = {"Сніданок": [],
                                                                                                       "Обід": [],
                                                                                                       "Вечеря": [],
                                                                                                       "Перекус": []}
                                data["diet_plan"][today_str]["Обід"].append({
                                    "dish": r['title'],
                                    "calories": cook.get('calories', 0),
                                    "status": "done"
                                })
                                dh.save_data(data)
                                st.rerun()

                with c_plan:
                    with st.popover("📅 В календар", use_container_width=True):
                        st.write("Куди додати?")
                        plan_date = st.date_input("Дата", datetime.date.today(), key=f"plan_d_{i}")
                        plan_meal = st.selectbox("Прийом", ["Сніданок", "Обід", "Вечеря", "Перекус"], key=f"plan_m_{i}")

                        if st.button("Записати", key=f"plan_save_{i}"):
                            with st.spinner("⏳"):
                                cals = ai.get_calories_from_ai(r['title'], "порція")

                            s_date = str(plan_date)
                            if s_date not in data["diet_plan"]:
                                data["diet_plan"][s_date] = {"Сніданок": [], "Обід": [], "Вечеря": [], "Перекус": []}

                            data["diet_plan"][s_date][plan_meal].append({
                                "dish": r['title'],
                                "calories": cals,
                                "status": "planned"
                            })
                            dh.save_data(data)
                            st.success("ОК!")
                            time.sleep(0.5)
                            st.rerun()

                with c_del:
                    if st.button("🗑", key=f"del_rec_{i}", use_container_width=True):
                        data["recipes"].pop(i)
                        dh.save_data(data)
                        st.rerun()

                if st.session_state.missing_products and st.button("🛒 Додати дефіцит в покупки?",
                                                                   key=f"shop_rec_btn_{i}"):
                    data["shopping_list"].extend(st.session_state.missing_products)
                    dh.save_data(data)
                    st.success("Додано!")
                    st.session_state.missing_products = []
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Немає рецептів.")