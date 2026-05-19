"""
continent — ru 翻译
"""

STRINGS: dict[str, str] = {
    "continent_remove_confirm_title": "Удалить континент",
    "continent_remove_confirm_msg": "Удалить континент \"{name}\"? Провинции этого континента останутся без континента. Отменяемо (Ctrl+Z).",
    "cont_dlg_add": "Добавить",
    "cont_dlg_add_prompt": "Название континента (английскими буквами, без пробелов):",
    "cont_dlg_add_title": "Добавить континент",
    "cont_dlg_assigned_fmt": "Назначена провинция {0} → {1}",
    "cont_dlg_assigning_fmt": "Назначение в: {0} — кликайте по провинциям на холсте",
    "cont_dlg_delete": "Удалить",
    "cont_dlg_delete_confirm_fmt": "Удалить '{0}'? Провинции, назначенные ему, перейдут на первый континент.",
    "cont_dlg_delete_title": "Удалить континент",
    "cont_dlg_err_min_one": "Должен остаться минимум 1 континент",
    "cont_dlg_err_select": "Сначала выберите континент",
    "cont_dlg_list_item_fmt": "пров.: {0}",
    "cont_dlg_rename": "Переименовать",
    "cont_dlg_rename_prompt": "Новое название:",
    "cont_dlg_rename_title": "Переименовать континент",
    "cont_dlg_start_assign": "Начать назначение провинций",
    "cont_dlg_stop_assign": "Остановить назначение",
    "cont_dlg_tip": """Использование:
1. Добавьте континенты (минимум 1 на МОД)
2. Выберите континент, нажмите «Начать назначение»
3. Кликайте по сухопутным провинциям на холсте → назначение континенту
4. Нажмите снова для остановки""",
    "cont_dlg_title": "Редактор континентов",
    "continent_add_btn": "Добавить",
    "continent_add_dlg_label": "Название континента (английскими буквами):",
    "continent_add_dlg_title": "Добавить континент",
    "continent_assign_by_state": "Назначить по регионам",
    "continent_delete_btn": "Удалить",
    "continent_pick_btn": "Начать назначение провинций",
    "continent_rename_btn": "Переименовать",
    "continent_rename_dlg_label": "Новое название:",
    "continent_rename_dlg_title": "Переименовать",
    "continent_tip": "🌍 Континенты = регионы целей в HOI4 (Северная Америка / Европа / Африка...). Влияют на разрешение целей wargoal.\nВсе сухопутные провинции должны принадлежать континенту (записывается в continent.txt + definition.csv).\nИспользование: добавьте континенты → режим выбора → клик по провинциям.",
    "dlg_continent_add_failed": "Не удалось добавить континент",
    "dlg_continent_delete_failed": "Ошибка удаления",
    "dlg_continent_rename_failed": "Ошибка переименования",
}
