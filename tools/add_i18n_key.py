#!/usr/bin/env python3
"""add_i18n_key — 一条命令同步加 i18n key 到所有已存在的语言文件.

用法:
  py tools/add_i18n_key.py <file_stem> <key> "<zh_text>"
  py tools/add_i18n_key.py menu my_new_btn "新按钮"
  py tools/add_i18n_key.py menu my_new_btn "新按钮" --en "New Button" --ru "Новая кнопка"

行为:
  - 自动写入 ui/i18n/zh/<file_stem>.py / en/<file_stem>.py / ru/<file_stem>.py
  - 未指定 --en/--ru 时, 用 "[TODO] <zh_text>" 占位; 之后跑 audit missing 找出来翻译
  - key 已存在时跳过 (--force 覆盖)
  - 不修改文件 docstring/格式, 只在 STRINGS dict 末尾追加新 key (闭合 `}` 之前)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = PROJECT_ROOT / "ui" / "i18n"


def list_languages() -> list[str]:
    if not I18N_DIR.is_dir():
        return []
    return sorted(
        p.name for p in I18N_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(("_", "."))
    )


def _format_key_line(key: str, value: str) -> str:
    """格式化一行 STRINGS 条目, 4 空格缩进."""
    if "\n" in value:
        # 多行: 三引号; 把 """ 转义防止破坏闭合
        safe = value.replace('"""', '\\"\\"\\"')
        return f'    "{key}": """{safe}""",'
    safe = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'    "{key}": "{safe}",'


def _key_exists(src: str, key: str) -> bool:
    # 粗匹配; STRINGS 里 key 是双引号字符串
    return f'"{key}":' in src


def _write_new_file(path: Path, lang: str, file_stem: str, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f'''"""
{file_stem} — {lang} 翻译
"""

STRINGS: dict[str, str] = {{
{_format_key_line(key, value)}
}}
'''
    path.write_text(content, encoding="utf-8")


def _append_key_to_file(path: Path, key: str, value: str) -> bool:
    """在 STRINGS 闭合 `}` 之前插入新 key. 返回 True 表示写入, False 表示跳过."""
    src = path.read_text(encoding="utf-8")
    if _key_exists(src, key):
        return False
    new_line = _format_key_line(key, value)
    lines = src.split("\n")
    # 倒序找最后一个独占行 `}`, 它是 STRINGS dict 的闭合
    insert_at: int | None = None
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped == "}":
            insert_at = i
            break
    if insert_at is None:
        raise RuntimeError(f"找不到 STRINGS dict 闭合 `}}`: {path}")
    lines.insert(insert_at, new_line)
    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def add_key(
    file_stem: str,
    key: str,
    values: dict[str, str],
    force: bool = False,
) -> dict[str, str]:
    """对每个 (lang, value) 在 i18n/<lang>/<file_stem>.py 加 key.

    返回 {lang: status} 状态 dict, status ∈ {"written", "skipped_exists", "force_overwritten"}.
    """
    results: dict[str, str] = {}
    for lang, value in values.items():
        path = I18N_DIR / lang / f"{file_stem}.py"
        if not path.exists():
            _write_new_file(path, lang, file_stem, key, value)
            results[lang] = "created_file"
            continue
        src = path.read_text(encoding="utf-8")
        if _key_exists(src, key):
            if not force:
                results[lang] = "skipped_exists"
                continue
            # force 覆盖: 简单做法 — 删除旧行 + 追加新行
            new_lines = []
            for ln in src.split("\n"):
                if ln.lstrip().startswith(f'"{key}":'):
                    continue
                new_lines.append(ln)
            path.write_text("\n".join(new_lines), encoding="utf-8")
            _append_key_to_file(path, key, value)
            results[lang] = "force_overwritten"
            continue
        _append_key_to_file(path, key, value)
        results[lang] = "written"
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="同步加 i18n key 到所有语言",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file_stem", help="文件名 (不含 .py), 如 menu / dialogs")
    parser.add_argument("key", help="i18n key, 如 my_new_btn")
    parser.add_argument("zh", help="中文翻译 (必填)")
    parser.add_argument("--en", default=None, help="英文翻译; 默认 [TODO] <zh>")
    parser.add_argument("--ru", default=None, help="俄文翻译; 默认 [TODO] <zh>")
    parser.add_argument(
        "--force", action="store_true",
        help="key 已存在时覆盖 (默认跳过)",
    )
    args = parser.parse_args()

    available_langs = set(list_languages())
    if not available_langs:
        print("没找到任何语言目录, 检查 ui/i18n/", file=sys.stderr)
        return 2

    todo_prefix = "[TODO] "
    values: dict[str, str] = {}
    if "zh" in available_langs:
        values["zh"] = args.zh
    if "en" in available_langs:
        values["en"] = args.en if args.en is not None else todo_prefix + args.zh
    if "ru" in available_langs:
        values["ru"] = args.ru if args.ru is not None else todo_prefix + args.zh
    # 兜底: 其他语言也加 TODO 占位
    for lang in available_langs - {"zh", "en", "ru"}:
        values[lang] = todo_prefix + args.zh

    results = add_key(args.file_stem, args.key, values, force=args.force)
    print(f"key={args.key!r} → file_stem={args.file_stem!r}:")
    for lang in sorted(results.keys()):
        print(f"  [{lang}] {results[lang]}")
    print()
    todo_langs = [l for l, v in values.items() if v.startswith(todo_prefix)]
    if todo_langs:
        print(f"提示: 以下语言用了 [TODO] 占位, 跑 audit 找出后翻译: {todo_langs}")
        print(f"  py tools/i18n_audit.py missing <lang>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
