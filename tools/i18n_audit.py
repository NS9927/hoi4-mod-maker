#!/usr/bin/env python3
"""i18n_audit — 翻译进度和一致性检查工具.

子命令:
  summary             所有语言的翻译完成度 (以 en 为 baseline)
  missing <lang>      列出 <lang> 缺失的 key + en 原文 (可直接 paste 给 LLM 翻译)
  check-placeholders  检查所有语言的 {placeholder} 与 en 是否一致 (catch 静默 KeyError)

用法:
  py tools/i18n_audit.py summary
  py tools/i18n_audit.py missing ru
  py tools/i18n_audit.py check-placeholders
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = PROJECT_ROOT / "ui" / "i18n"
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")


def load_lang(lang: str) -> dict[str, str]:
    """加载 ui/i18n/<lang>/*.py 的所有 STRINGS dict 合并."""
    lang_dir = I18N_DIR / lang
    if not lang_dir.is_dir():
        return {}
    out: dict[str, str] = {}
    for py_file in sorted(lang_dir.glob("*.py")):
        if py_file.stem == "__init__":
            continue
        spec = importlib.util.spec_from_file_location(
            f"_audit_{lang}_{py_file.stem}", py_file
        )
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            print(f"[WARN] 加载失败 {py_file}: {exc}", file=sys.stderr)
            continue
        strings = getattr(mod, "STRINGS", None)
        if isinstance(strings, dict):
            out.update(strings)
    return out


def list_languages() -> list[str]:
    return sorted(
        p.name for p in I18N_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(("_", "."))
    )


def _pick_baseline(langs: list[str], exclude: str | None = None) -> str:
    """选 baseline 语言: 优先 en, 否则 zh, 否则第一个."""
    for candidate in ("en", "zh"):
        if candidate in langs and candidate != exclude:
            return candidate
    for l in langs:
        if l != exclude:
            return l
    return langs[0] if langs else ""


def cmd_summary() -> int:
    langs = list_languages()
    if not langs:
        print("没有找到任何语言目录", file=sys.stderr)
        return 1
    all_data = {l: load_lang(l) for l in langs}
    baseline = _pick_baseline(langs)
    base_n = len(all_data[baseline])
    print(f"=== i18n Summary (baseline: {baseline}, {base_n} keys) ===")
    for l in langs:
        n = len(all_data[l])
        pct = 100.0 * n / base_n if base_n else 0.0
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        marker = "  " if l != baseline else "* "
        print(f"{marker}{l:6s} |{bar}| {n:>5}/{base_n} ({pct:5.1f}%)")
    return 0


def cmd_missing(target_lang: str) -> int:
    langs = list_languages()
    if target_lang not in langs:
        print(
            f"语言 {target_lang!r} 未找到. 可用: {langs}", file=sys.stderr
        )
        return 2
    baseline = _pick_baseline(langs, exclude=target_lang)
    if not baseline:
        print("找不到 baseline 语言", file=sys.stderr)
        return 2
    base = load_lang(baseline)
    tgt = load_lang(target_lang)
    missing = sorted(set(base) - set(tgt))
    print(f"=== {target_lang} 缺失 {len(missing)} key (baseline: {baseline}) ===")
    if not missing:
        return 0
    # 输出便于直接 paste 给 LLM 翻译
    for k in missing:
        v = base[k]
        # 单行优先; 多行用 repr 让 \n 可见
        if "\n" in v:
            print(f"  {k}: {v!r}")
        else:
            print(f"  {k}: {v!r}")
    extra = sorted(set(tgt) - set(base))
    if extra:
        print()
        print(f"=== {target_lang} 比 baseline 多 {len(extra)} key (可能需删) ===")
        for k in extra:
            print(f"  {k}")
    return 0 if not missing else 1


def cmd_check_placeholders() -> int:
    langs = list_languages()
    baseline = _pick_baseline(langs)
    if not baseline:
        return 2
    base = load_lang(baseline)
    mismatches: list[tuple[str, str, list[str], list[str]]] = []
    for l in langs:
        if l == baseline:
            continue
        data = load_lang(l)
        for key in set(base) & set(data):
            base_phs = sorted(PLACEHOLDER_RE.findall(base[key]))
            tgt_phs = sorted(PLACEHOLDER_RE.findall(data[key]))
            if base_phs != tgt_phs:
                mismatches.append((l, key, base_phs, tgt_phs))
    print(
        f"=== Placeholder 一致性 (baseline: {baseline}): "
        f"{len(mismatches)} 个不一致 ==="
    )
    LIMIT = 50
    for l, k, b, t in mismatches[:LIMIT]:
        print(f"  [{l}] {k}")
        print(f"    {baseline}: {b}")
        print(f"    {l}: {t}")
    if len(mismatches) > LIMIT:
        print(f"  ... 还有 {len(mismatches) - LIMIT} 个未显示")
    return 0 if not mismatches else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="i18n 审计工具", formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("summary", help="所有语言的翻译完成度")
    p_miss = sub.add_parser("missing", help="列出某语言缺失的 key")
    p_miss.add_argument("lang", help="目标语言 code (如 ru)")
    sub.add_parser("check-placeholders", help="检查 placeholder 跨语言一致性")
    args = parser.parse_args()
    if args.mode == "summary":
        return cmd_summary()
    if args.mode == "missing":
        return cmd_missing(args.lang)
    if args.mode == "check-placeholders":
        return cmd_check_placeholders()
    return 1


if __name__ == "__main__":
    sys.exit(main())
