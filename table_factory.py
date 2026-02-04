from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd
import json


def draw_pro_table(df, enable_grouping=False, color_map=None):
    """
    Малює професійну таблицю AgGrid:
    - 3 видимі колонки (Продукт, Кількість, Вид продукту)
    - Білі квадратні чекбокси
    - Кольорове маркування рядків через JS
    - Оптимальний розмір тексту (16px)
    """

    # 1. Ініціалізація конструктора
    gb = GridOptionsBuilder.from_dataframe(df)

    # 2. Глобальні налаштування колонок
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=True,
        minWidth=100
    )

    # 3. Налаштування конкретних колонок
    # Колонка "item" (Продукт) з білим чекбоксом
    gb.configure_column(
        "item",
        headerName="🍎 Продукт",
        flex=2,
        checkboxSelection=True,
        headerCheckboxSelection=True,
        pinned='left'
    )

    # Колонка "amount" (Кількість)
    gb.configure_column(
        "amount",
        headerName="⚖️ Кількість",
        flex=1
    )

    # Колонка "category" (Вид продукту)
    # ПРИМІТКА: hide=False гарантує, що вона завжди буде в таблиці як третя колонка
    gb.configure_column(
        "category",
        headerName="📂 Вид продукту",
        rowGroup=enable_grouping,
        hide=False
    )

    # 4. Опції вибору рядків
    gb.configure_selection(
        'multiple',
        use_checkbox=True,
        groupSelectsChildren=True
    )

    # 5. Налаштування поведінки сітки
    gb.configure_grid_options(
        domLayout='normal',
        animateRows=True,
        suppressRowClickSelection=True,
        groupDefaultExpanded=-1 if enable_grouping else 0,
        rowHeight=40  # Висота рядка для зручного читання
    )

    # 6. JS-код для кольорового маркування (getRowStyle)
    if color_map is None:
        color_map = {}

    # Перетворюємо мапу кольорів у JSON для передачі в JS
    colors_json = json.dumps(color_map, ensure_ascii=False)

    jscode = f"""
    function(params) {{
        // Базовий шрифт
        var style = {{'font-size': '16px', 'display': 'flex', 'align-items': 'center'}};

        // Якщо це заголовок групи
        if (params.node.group) {{
            return {{
                'background-color': '#262730', 
                'font-weight': 'bold', 
                'font-size': '17px',
                'color': '#FFFFFF'
            }};
        }}

        // Якщо це звичайний рядок
        var colorMap = {colors_json};
        if (params.data && params.data.category) {{
            var cat = params.data.category;
            if (cat in colorMap) {{
                // Додаємо колір з прозорістю 40 (hex)
                style['background-color'] = colorMap[cat] + '40';
            }}
        }} else {{
            // Зебра (чергування кольорів)
            if (params.node.rowIndex % 2 === 0) {{
                style['background-color'] = '#0E1117';
            }} else {{
                style['background-color'] = '#161920';
            }}
        }}

        return style;
    }}
    """
    gb.configure_grid_options(getRowStyle=JsCode(jscode))

    # Будуємо Grid Options
    grid_options = gb.build()

    # 7. Кастомний CSS для білих чекбоксів та оформлення
    custom_css = {
        # Шапка таблиці
        ".ag-header-cell-label": {
            "font-size": "17px",
            "font-weight": "bold",
            "color": "#FFFFFF"
        },
        # Самі клітинки
        ".ag-cell": {
            "border-right": "1px solid #262730 !important"
        },
        # БІЛІ ЧЕКБОКСИ (Стиль v1.0)
        ".ag-checkbox-input-wrapper": {
            "background-color": "#FFFFFF !important",
            "border-radius": "3px",
            "width": "18px",
            "height": "18px",
            "border": "1px solid #CCC"
        },
        # Колір "галочки" всередині білого чекбокса
        ".ag-checkbox-input-wrapper.ag-checked::after": {
            "color": "#000000 !important"
        },
        # Чекбокс у шапці (Select All)
        ".ag-header-select-all": {
            "background-color": "#FFFFFF !important",
            "border-radius": "3px"
        }
    }

    # Розрахунок висоти (мін 250px, макс 600px)
    calculated_height = (len(df) * 40) + 60
    final_height = min(600, max(250, calculated_height))

    # 8. Рендеринг AgGrid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        height=final_height,
        fit_columns_on_grid_load=True,
        theme='streamlit',
        allow_unsafe_jscode=True,
        custom_css=custom_css
    )

    return grid_response['data']