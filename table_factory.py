from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd
import json


def draw_pro_table(df, enable_grouping=True, color_map=None):
    """
    Малює професійну таблицю з коректною обробкою JS та висоти.
    """

    # Ініціалізація
    gb = GridOptionsBuilder.from_dataframe(df)

    # Базові налаштування колонок
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=True,  # Дозволяє редагувати прямо в таблиці
        minWidth=100
    )

    # Конкретні колонки
    gb.configure_column("item", headerName="🍎 Продукт", flex=2, checkboxSelection=True, headerCheckboxSelection=True,
                        pinned='left')
    gb.configure_column("amount", headerName="⚖️ Кількість", flex=1)

    # Налаштування групування
    # hide=True приховує колонку категорії, бо вона буде в заголовку групи (економить місце)
    gb.configure_column("category", headerName="📂 Категорія", rowGroup=enable_grouping, hide=enable_grouping)

    # Опції поведінки
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren=True)
    gb.configure_grid_options(
        domLayout='normal',  # Дозволяє внутрішній скрол
        animateRows=True,
        suppressRowClickSelection=True,  # Щоб виділяти тільки чекбоксом
        groupDefaultExpanded=-1 if enable_grouping else 0  # -1 розгортає всі групи одразу
    )

    # --- ВИПРАВЛЕНИЙ JS ДЛЯ КОЛЬОРІВ ---
    if color_map is None: color_map = {}
    colors_json = json.dumps(color_map, ensure_ascii=False)

    # JS функція тепер перевіряє, чи це група, щоб не крашитись
    jscode = f"""
    function(params) {{
        // 1. Якщо це рядок групи - даємо темно-сірий фон
        if (params.node.group) {{
            return {{'background-color': '#262730', 'font-weight': 'bold'}};
        }}

        // 2. Якщо це звичайний рядок і є категорія в мапі кольорів
        var colorMap = {colors_json};
        if (params.data && params.data.category) {{
            var cat = params.data.category;
            if (cat in colorMap) {{
                // Додаємо прозорість 40 (hex) до кольору
                return {{'background-color': colorMap[cat] + '40'}}; 
            }}
        }}

        // 3. Дефолтна "зебра" (чергування кольорів)
        return {{
            'background-color': params.node.rowIndex % 2 === 0 ? '#0E1117' : '#161920'
        }};
    }}
    """
    gb.configure_grid_options(getRowStyle=JsCode(jscode))

    grid_options = gb.build()

    # --- РОЗРАХУНОК ВИСОТИ ---
    # Робимо трохи простіше: динамічно, але з лімітом
    # 35px на рядок + 50px шапка
    calculated_height = (len(df) * 35) + 50
    # Якщо є групи, додаємо ще трохи місця (приблизно)
    if enable_grouping and 'category' in df.columns:
        calculated_height += (df['category'].nunique() * 35)

    # Обмежуємо: не менше 200px, не більше 500px (далі скрол)
    final_height = min(500, max(200, calculated_height))

    # Рендеринг
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        height=final_height,
        fit_columns_on_grid_load=True,  # Розтягує на всю ширину
        theme='streamlit',  # Використовуємо рідну тему (або 'balham-dark')
        allow_unsafe_jscode=True,
        custom_css={
            ".ag-root-wrapper": {"border": "1px solid #333", "border-radius": "8px"},
            ".ag-header": {"background-color": "#1f2229", "font-weight": "bold"},
            # Вирівнювання тексту по вертикалі
            ".ag-cell": {"display": "flex", "align-items": "center"}
        }
    )

    # Повертаємо дані (або grid_response['selected_rows'] якщо треба тільки виділене)
    return grid_response['data']