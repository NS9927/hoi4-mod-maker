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

    # ── QFluentWidgets 主题初始化 ────────────────────────────
    from qfluentwidgets import setTheme, setThemeColor, Theme
    setTheme(Theme.DARK)
    setThemeColor("#6c6cf0")

    # Fusion 风格 + 暗色 QPalette → 原生 Qt 控件也继承暗色背景
    app.setStyle('Fusion')
    from PyQt5.QtGui import QPalette, QColor
    _p = QPalette()
    _p.setColor(QPalette.ColorRole.Window, QColor("#1e1e2e"))
    _p.setColor(QPalette.ColorRole.WindowText, QColor("#f0f0ff"))
    _p.setColor(QPalette.ColorRole.Base, QColor("#252535"))
    _p.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a3a"))
    _p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#252535"))
    _p.setColor(QPalette.ColorRole.ToolTipText, QColor("#f0f0ff"))
    _p.setColor(QPalette.ColorRole.Text, QColor("#f0f0ff"))
    _p.setColor(QPalette.ColorRole.Button, QColor("#2a2a3a"))
    _p.setColor(QPalette.ColorRole.ButtonText, QColor("#f0f0ff"))
    _p.setColor(QPalette.ColorRole.BrightText, QColor("#ff0000"))
    _p.setColor(QPalette.ColorRole.Link, QColor("#8080ff"))
    _p.setColor(QPalette.ColorRole.Highlight, QColor("#6c6cf0"))
    _p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(_p)

    # 全局基础字体: 必须在 stylesheet 前设置, 作为所有 widget 的 fallback.
    # Segoe UI 优先: 西里尔/拉丁字母按正常 metrics 渲染.
    # YaHei/Noto SC 兜底中文字符. 若放 YaHei 在前, 西里尔字母会按 CJK 全角宽度
    # 渲染 (字母间距异常大 + 文本截断) — 这是俄语界面的关键 bug.
    from PyQt5.QtGui import QFont
    _base_font = QFont("Segoe UI", 9)
    _base_font.setFamilies(["Segoe UI", "Microsoft YaHei", "Noto Sans SC"])
    app.setFont(_base_font)

    # 字体强制覆盖 CSS — 追加到任意 stylesheet 之后, 防止 qdarktheme 等主题库
    # 内置的字体设置覆盖我们的 fallback.
    # 注: Qt stylesheet 不支持 !important, 通配 * 优先级太低.
    # 必须用 QWidget 选择器 + 显式枚举常见 widget class 才能稳定覆盖.
    _FONT_OVERRIDE_CSS = """
QWidget, QMainWindow, QDialog, QMessageBox,
QPushButton, QLabel, QLineEdit, QTextEdit, QPlainTextEdit,
QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
QListWidget, QListView, QTreeWidget, QTreeView, QTableWidget, QTableView,
QGroupBox, QCheckBox, QRadioButton, QProgressBar,
QTabWidget, QTabBar, QMenuBar, QMenu, QToolBar, QToolButton,
QStatusBar, QHeaderView, QScrollBar, QToolTip {
    font-family: "Segoe UI", "Microsoft YaHei", "Noto Sans SC", sans-serif;
}
"""

    # 基础暗色 QSS (原生 Qt 控件背景) + 字体覆盖
    from ui.styles import DARK_STYLESHEET
    app.setStyleSheet(DARK_STYLESHEET + _FONT_OVERRIDE_CSS)


    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
