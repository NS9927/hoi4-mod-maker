"""
pytest 全局配置.
- 把项目根加入 sys.path 让 import 生效 (项目没用 src/ 布局).
- Qt 测试走 offscreen 模式, 不弹窗.
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Qt 无头
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
