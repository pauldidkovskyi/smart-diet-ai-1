from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd
import json


def draw_pro_table(df, enable_grouping=True, color_map=None):
    """
    Малює таблицю з точним розрахунком висоти, щоб уникнути зникнення.
    """

    gb = GridOptionsBuilder.from_dataframe(df)

    # Загальні налаштування
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=True,
    )

    # Налаштування колонок
    # flex=1 змушує колонки розтягуватись на всю ширину (прибирає щілини збоку)
    gb.configure_column("item", headerName="🍎 Продукт", minWidth=180, flex=2, checkboxSelection=True,
                        headerCheckboxSelection=True, pinned='left')
    gb.configure_column("amount", headerName="⚖️ Кількість", minWidth=100, flex=1)

    # Якщо групування увімкнено - ховаємо колонку, якщо ні - показуємо
    gb.configure_column("category", headerName="📂 Категорія", minWidth=120, rowGroup=enable_grouping, hide=False,
                        flex=1)

    # Логіка інтерфейсу
    grid_options_dict = {
        "domLayout": 'normal',  # Повертаємо 'normal', бо 'autoHeight' ховає таблицю
        "rowSelection": 'multiple',
        "groupSelectsChildren": True,
        "suppressRowClickSelection": True,
        "animateRows": True,
    }

    if enable_grouping:
        grid_options_dict["groupDefaultExpanded"] = -1

    gb.configure_grid_options(**grid_options_dict)

    # --- МАГІЯ КОЛЬОРІВ ---
    if color_map is None:
        color_map = {}

    colors_json = json.dumps(color_map, ensure_ascii=False)

    jscode = f"""
    function(params) {{
        var colorMap = {colors_json};
        if (params.data && params.data.category) {{
            var cat = params.data.category;
            if (cat in colorMap) {{
                return {{'background-color': colorMap[cat] + '40'}}; 
            }}
        }}
        if (params.node.rowIndex % 2 === 0) {{
            return {{'background-color': '#0E1117'}}; 
        }} else {{
            return {{'background-color': '#161920'}}; 
        }}
    }}
    """

    gb.configure_grid_options(getRowStyle=JsCode(jscode))

    grid_options = gb.build()

    # --- ТОЧНИЙ РОЗРАХУНОК ВИСОТИ (Щоб не було щілин) ---
    ROW_HEIGHT = 35  # Висота одного рядка в пікселях
    HEADER_HEIGHT = 50  # Висота шапки таблиці

    # Рахуємо кількість рядків даних
    total_rows = len(df)

    # Якщо є групування, додаємо висоту для заголовків категорій
    if enable_grouping and 'category' in df.columns:
        unique_categories = df['category'].nunique()
        total_rows += unique_categories

    # Фінальна висота = (рядки * 35) + заголовок
    # + 5 пікселів про запас для меж
    calculated_height = (total_rows * ROW_HEIGHT) + HEADER_HEIGHT + 5

    # Ставимо розумні межі:
    # Мінімум 150px (щоб таблиця не була занадто малою, якщо там 1 продукт)
    # Максимум 600px (щоб не займала весь екран, якщо там 100 продуктів - з'явиться скрол)
    final_height = min(600, max(150, calculated_height))

    # Рендеринг
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,

        # Це розтягує колонки на всю ширину (прибирає білу полосу праворуч)
        fit_columns_on_grid_load=True,

        theme='balham',

        # Використовуємо наш точний розрахунок
        height=final_height,

        allow_unsafe_jscode=True,
        custom_css={
            ".ag-root-wrapper": {
                "border": "1px solid #333",
                "background-color": "#0E1117",
                "border-radius": "5px"
            },
            ".ag-header": {"background-color": "#262730", "color": "white"},
            ".ag-row": {"color": "white", "background-color": "#0E1117"},
            ".ag-even": {"background-color": "#0E1117"},
            ".ag-odd": {"background-color": "#161920"},
            # Прибирає білий фон, якщо раптом з'явиться пусте місце
            ".ag-layout-normal": {"background-color": "#0E1117"}
        }
    )

    return grid_response['data']