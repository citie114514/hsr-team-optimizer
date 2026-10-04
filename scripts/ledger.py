#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""崩铁单变量迭代账本。

零依赖（仅 Python 标准库）。账本默认落在当前目录的 hsr-ledger.json。

用法：
    python ledger.py init --mode "虚构叙事 立界开篇" \\
        --nodes 节点一,节点二,节点三 --star-line 100000
    python ledger.py add --change "银狼原头 → 6.6速新头" \\
        --hypothesis "战前速度 183.9→190.5，固定动作伤害 +1.7%" \\
        --scores 节点二=29640 --verdict 部分成立 --note "伤害涨了但轮次没多"
    python ledger.py add --baseline --scores 节点一=28000,节点二=27040,节点三=24480
    python ledger.py show
    python ledger.py show --json
    python ledger.py stop --reason "已满星"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

DEFAULT_FILE = "hsr-ledger.json"

VERDICTS = ("成立", "不成立", "部分成立", "噪声内", "组合改动")


# --------------------------------------------------------------------------- io

def load(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(f"账本不存在：{path}\n先跑：python ledger.py init --mode ... --nodes ... --star-line ...")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ------------------------------------------------------------------------ parse

def parse_scores(raw: str | None) -> dict:
    """'节点一=28000,节点二=27040' -> {'节点一': 28000, ...}"""
    out: dict[str, int] = {}
    if not raw:
        return out
    for chunk in raw.replace("，", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            sys.exit(f"分数格式错误：{chunk!r}，应为 节点名=数字")
        key, _, val = chunk.partition("=")
        key = key.strip()
        try:
            out[key] = int(float(val.strip()))
        except ValueError:
            sys.exit(f"分数不是数字：{chunk!r}")
    return out


def fmt_scores(scores: dict, nodes: list[str]) -> str:
    if not scores:
        return "—"
    ordered = [n for n in nodes if n in scores] + [k for k in scores if k not in nodes]
    return " / ".join(f"{k} {scores[k]:,}" for k in ordered)


# --------------------------------------------------------------------- commands

def cmd_init(args) -> None:
    nodes = [n.strip() for n in args.nodes.replace("，", ",").split(",") if n.strip()]
    if not nodes:
        sys.exit("--nodes 不能为空")
    data = {
        "mode": args.mode,
        "nodes": nodes,
        "star_line": args.star_line,
        "started": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "finished": None,
        "stop_reason": None,
        "rounds": [],
    }
    save(args.file, data)
    print(f"已初始化 {args.file}")
    print(f"  模式：{args.mode}")
    print(f"  节点：{' / '.join(nodes)}")
    print(f"  满星线：{args.star_line:,}" if args.star_line else "  满星线：（未设置）")


def cmd_add(args) -> None:
    data = load(args.file)
    nodes = data["nodes"]
    scores = parse_scores(args.scores)
    unknown = [k for k in scores if k not in nodes]
    if unknown:
        print(f"⚠ 未知节点 {unknown}，已加入（原节点：{nodes}）", file=sys.stderr)
        nodes.extend(unknown)
    if args.verdict and args.verdict not in VERDICTS:
        sys.exit(f"--verdict 只能是：{' / '.join(VERDICTS)}")

    total = sum(scores.values()) if scores else None
    if total is None and data["rounds"]:
        # 未提供分数时沿用上一轮的未变节点
        pass

    entry = {
        "round": 0 if args.baseline else len([r for r in data["rounds"] if not r["baseline"]]) + 1,
        "baseline": bool(args.baseline),
        "change": "基线（不改）" if args.baseline else args.change,
        "hypothesis": args.hypothesis,
        "scores": scores,
        "total": total,
        "verdict": args.verdict,
        "note": args.note,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["rounds"].append(entry)
    save(args.file, data)

    label = "基线" if args.baseline else f"第 {entry['round']} 轮"
    print(f"已记录{label}：{fmt_scores(scores, nodes)}" + (f" = {total:,}" if total else ""))
    if data.get("star_line") and total:
        gap = data["star_line"] - total
        print(f"  距满星线还差 {gap:,}" if gap > 0 else f"  ✅ 已超过满星线 {abs(gap):,}")


def cmd_show(args) -> None:
    data = load(args.file)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    nodes = data["nodes"]
    print(f"# {data['mode']}")
    print()
    if data.get("star_line"):
        print(f"- 满星线：{data['star_line']:,}")
    print(f"- 节点：{' / '.join(nodes)}")
    print(f"- 起始：{data['started']}")
    if data.get("finished"):
        print(f"- 结束：{data['finished']}（{data.get('stop_reason') or '未说明'}）")
    print()

    print("| 轮次 | 改动 | 假设 | 实测 | 结论 | 备注 |")
    print("|---|---|---|---|---|---|")
    prev_total = None
    for r in data["rounds"]:
        label = "0（基线）" if r["baseline"] else str(r["round"])
        measured = fmt_scores(r["scores"], nodes)
        if r.get("total") is not None:
            measured += f" = {r['total']:,}"
            if prev_total is not None:
                delta = r["total"] - prev_total
                pct = delta / prev_total * 100 if prev_total else 0
                measured += f"（{delta:+,} / {pct:+.1f}%）"
            prev_total = r["total"]
        print(
            "| {} | {} | {} | {} | {} | {} |".format(
                label,
                r.get("change") or "—",
                r.get("hypothesis") or "—",
                measured,
                r.get("verdict") or "—",
                r.get("note") or "",
            )
        )
    print()

    best = max(
        (r for r in data["rounds"] if r.get("total")),
        key=lambda r: r["total"],
        default=None,
    )
    if best:
        where = "基线" if best["baseline"] else f"第 {best['round']} 轮"
        print(f"当前最高：{best['total']:,}（{where}）")


def cmd_stop(args) -> None:
    data = load(args.file)
    data["finished"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["stop_reason"] = args.reason
    save(args.file, data)
    print(f"已收尾：{args.reason}")


# -------------------------------------------------------------------------- cli

def main() -> None:
    # Windows 控制台默认 GBK，中文会变乱码；强制 UTF-8 输出。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    p = argparse.ArgumentParser(description="崩铁单变量迭代账本")
    p.add_argument("--file", default=DEFAULT_FILE, help=f"账本路径（默认 {DEFAULT_FILE}）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="初始化本期账本")
    s.add_argument("--mode", required=True, help="模式 + 期数")
    s.add_argument("--nodes", required=True, help="节点名，逗号分隔")
    s.add_argument("--star-line", type=int, default=None, help="满星总分线")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add", help="追加一轮")
    s.add_argument("--baseline", action="store_true", help="标记为基线轮（第 0 轮）")
    s.add_argument("--change", default="", help="本轮唯一改动")
    s.add_argument("--hypothesis", default="", help="预期影响哪个指标、幅度多少")
    s.add_argument("--scores", default="", help="节点分，形如 节点一=28000,节点二=27040")
    s.add_argument("--verdict", default="", help=" / ".join(VERDICTS))
    s.add_argument("--note", default="", help="备注")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("show", help="打印账本")
    s.add_argument("--json", action="store_true", help="输出原始 JSON")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("stop", help="收尾并记录停止原因")
    s.add_argument("--reason", required=True, help="已满星 / 连续3轮增益<1% / 资源耗尽")
    s.set_defaults(func=cmd_stop)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
