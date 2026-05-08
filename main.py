"""
HOI4 幻想世界 MOD 制作工具 — 主入口
"""
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.crash_handler import install_crash_handler
from ui.main_window import MainWindow


def main():
    # 全局崩溃处理器 (弹窗显示原因 + 写 logs/crash_*.log)
    install_crash_handler()

    # 加载用户语言设置
    import json
    config_path = os.path.join(os.path.expanduser("~"), ".hoi4_map_maker.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            lang = config.get("language")
            if lang:
                from ui.i18n import set_language, available_languages
                if lang in available_languages():
                    set_language(lang)
        except Exception:
            pass

    # 高DPI支持
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("HOI4 MOD 制作工具")
    app.setOrganizationName("HOI4ModTools")

    # 用 PyQtDarkTheme 专业暗色主题, 失败时退回手写 QSS, 保证软件能起来
    try:
        import qdarktheme
        app.setStyleSheet(qdarktheme.load_stylesheet(
            "dark",
            custom_colors={"primary": "#6c6cf0"},
        ))
    except Exception as e:
        # qdarktheme 缺失或资源加载失败 -> 退回 ui/styles.py 自带暗色主题
        print(f"[warn] qdarktheme 不可用, 退回内置主题: {e}", file=sys.stderr)
        from ui.styles import DARK_STYLESHEET
        app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
