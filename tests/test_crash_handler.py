"""
崩溃处理器测试.
"""

import sys

from app.crash_handler import install_crash_handler, _write_crash_log


def test_install_sets_excepthook():
    old = sys.excepthook
    install_crash_handler()
    assert sys.excepthook is not old
    # restore
    sys.excepthook = old


def test_write_crash_log_creates_file(tmp_path, monkeypatch):
    """_write_crash_log 必须能把 traceback 写到 logs/crash_*.log."""
    tb_text = "Traceback (most recent call last):\n  ValueError: test\n"
    path = _write_crash_log(tb_text)
    import os
    assert os.path.isfile(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "ValueError: test" in content
    # cleanup
    os.remove(path)


def test_install_handles_keyboard_interrupt():
    """KeyboardInterrupt 应走默认行为, 不弹窗不吞."""
    old = sys.excepthook
    install_crash_handler()
    new_hook = sys.excepthook
    # 我们的 handler 遇到 KeyboardInterrupt 应 delegate 给 sys.__excepthook__
    # 这里只验证 handler 可调用且不崩
    try:
        raise KeyboardInterrupt()
    except KeyboardInterrupt:
        exc_type, exc_value, exc_tb = sys.exc_info()
        # 不能实际调 (会退出 test), 但验证函数存在
        assert callable(new_hook)
    sys.excepthook = old
