"""
file_ops — ru 翻译
"""

STRINGS: dict[str, str] = {
    "file_ops_export_fail": "Ошибка экспорта",
    "file_ops_img_read_fail": "Не удалось прочитать изображение: {0}",
    "file_ops_import_confirm": "Импорт заменит текущие данные карты. Продолжить?",
    "file_ops_import_done": "Импорт завершён",
    "file_ops_import_fail": "Ошибка импорта: {0}",
    "file_ops_import_warnings": """Предупреждения:
""",
    "file_ops_invert_prompt": "Выберите Да для инвертирования: тёмное = суша, светлое = море (по умолчанию Нет)",
    "file_ops_invert_title": "Инвертировать?",
    "file_ops_landmask_done": "Импорт суши/моря завершён — суша {0}% / море {1}%",
    "file_ops_landmask_title": "Выберите исходное изображение суши/моря",
    "file_ops_load_fail": "Ошибка загрузки",
    "file_ops_loaded": "Проект загружен: {0}",
    "file_ops_loaded_gaps": "Проект загружен: {0} | ⚠ найдены пропуски ID провинций: {1}",
    "file_ops_map_size_prompt": "Выберите размер карты для нового проекта:",
    "file_ops_map_size_title": "Выберите размер карты",
    "file_ops_missing_files": """В папке отсутствуют необходимые файлы:
""",
    "file_ops_mod_imported": "Карта МОДа импортирована ({0}×{1}, провинций: {2}, регионов: {3}, страт. зон: {4}, ресурсов: {5})",
    "file_ops_new_confirm": "Создание нового проекта очистит текущие данные. Продолжить?",
    "file_ops_new_created": "Новый проект создан ({0}×{1})",
    "file_ops_open_title": "Открыть проект",
    "file_ops_proj_filter": "Проект HOI4 (*.hoi4proj);;Все файлы (*)",
    "file_ops_ref_fail": "Не удалось загрузить изображение",
    "file_ops_ref_loaded": "Референсное изображение загружено: {0}",
    "file_ops_save_fail": "Ошибка сохранения",
    "file_ops_save_title": "Сохранить проект",
    "file_ops_saved": "Проект сохранён: {0}",
    "file_ops_select_mod_dir": "Выберите папку МОДа HOI4 или ванильную папку",
    "file_ops_test_dialog_title": "Прогрессивный тестовый экспорт",
    "file_ops_test_export_ok": """Тестовый МОД Lv{0} экспортирован в:
{1}

{2}

Запустите игру для теста.
Если крашится — попробуйте уровень ниже; если работает — выше.""",
    "file_ops_test_export_title": "Тестовый экспорт",
    "file_ops_test_generating": "Генерация тестового МОДа Lv{0}...",
    "file_ops_test_lv1_desc": """Карта + Регионы + 1 страна (AAA) + снабжение + страт. зоны + replace_path
Минимальная рабочая конфигурация для проверки базового формата файлов""",
    "file_ops_test_lv1_title": "Lv1: Минимальный МОД (1 страна)",
    "file_ops_test_lv2_desc": """Lv1 + 2-я страна (BBB) + выбор закладки
Тест нескольких стран и закладок""",
    "file_ops_test_lv2_title": "Lv2: +2 страны +закладка",
    "file_ops_test_lv3_desc": """Lv2 + идеологии, определения state_category
Тест пользовательских идеологий/категорий регионов""",
    "file_ops_test_lv3_title": "Lv3: +идеологии +категории регионов",
    "file_ops_test_lv4_desc": """Lv3 + больше replace_path (очистка ванильных focus/events и т.д.)
Полный TC МОД""",
    "file_ops_test_lv4_title": "Lv4: +больше replace_path",
    "file_ops_test_output_dir": "Выберите папку для тестового экспорта",
    "file_ops_test_select_level": "Выберите уровень теста (от низкого к высокому, отлаживайте краши пошагово):",
    "file_ops_threshold_prompt": """Порог градации серого (0-255)
>= порог = суша, < порог = море
Рекомендуется: 1 для карт высот; ~90 для спутниковых изображений""",
    "file_ops_threshold_title": "Порог суши/моря",
    "file_ops_vanilla_loaded": "Ванильная карта загружена как референс: {0}",
    "file_ops_vanilla_not_found": """Ванильные файлы карты не найдены
Проверьте путь: {0}""",
}
