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
            if config.get("language") in ("zh", "en"):
                from ui.i18n import set_language
                set_language(config["language"])
        except Exception:
            pass

    # 高DPI支持
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("HOI4 MOD 制作工具")
    app.setOrganizationName("HOI4ModTools")

    # 用 PyQtDarkTheme 专业暗色主题, 替代手写 QSS
    import qdarktheme
    app.setStyleSheet(qdarktheme.load_stylesheet(
        "dark",
        custom_colors={"primary": "#6c6cf0"},
    ))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
