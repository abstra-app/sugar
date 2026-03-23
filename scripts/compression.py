#!/usr/bin/env python3
"""Measure token compression ratio between .sugar and .html snapshots.

Usage:
    python scripts/compression.py [--encoding cl100k_base] [--verbose]
"""

import argparse
import pathlib
import sys

import tiktoken

SNAPSHOTS_DIR = pathlib.Path(__file__).parent.parent / "abstra_sugar" / "snapshots"


def count_tokens(text: str, enc: tiktoken.Encoding) -> int:
    return len(enc.encode(text))


def main():
    parser = argparse.ArgumentParser(description="Sugar compression ratio")
    parser.add_argument(
        "--encoding", default="cl100k_base",
        help="tiktoken encoding (default: cl100k_base)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    enc = tiktoken.get_encoding(args.encoding)

    total_sugar = 0
    total_html = 0
    total_sugar_chars = 0
    total_html_chars = 0
    rows = []

    for sugar_file in sorted(SNAPSHOTS_DIR.glob("*.sugar")):
        html_file = sugar_file.with_suffix(".html")
        if not html_file.exists():
            continue

        sugar_text = sugar_file.read_text()
        html_text = html_file.read_text()

        sugar_tokens = count_tokens(sugar_text, enc)
        html_tokens = count_tokens(html_text, enc)
        sugar_chars = len(sugar_text)
        html_chars = len(html_text)

        ratio = html_tokens / sugar_tokens if sugar_tokens else 0

        rows.append({
            "name": sugar_file.stem,
            "sugar_tok": sugar_tokens,
            "html_tok": html_tokens,
            "ratio": ratio,
            "sugar_chars": sugar_chars,
            "html_chars": html_chars,
        })

        total_sugar += sugar_tokens
        total_html += html_tokens
        total_sugar_chars += sugar_chars
        total_html_chars += html_chars

    if not rows:
        print("No snapshot pairs found.")
        sys.exit(1)

    # header
    name_w = max(len(r["name"]) for r in rows)
    print(f"{'Snapshot':<{name_w}}  {'Sugar':>7}  {'HTML':>7}  {'Ratio':>6}  {'Saved':>6}")
    print(f"{'-' * name_w}  {'-' * 7}  {'-' * 7}  {'-' * 6}  {'-' * 6}")

    for r in rows:
        saved = (1 - 1 / r["ratio"]) * 100 if r["ratio"] > 0 else 0
        print(
            f"{r['name']:<{name_w}}  "
            f"{r['sugar_tok']:>7}  "
            f"{r['html_tok']:>7}  "
            f"{r['ratio']:>5.2f}x  "
            f"{saved:>5.1f}%"
        )

    print(f"{'-' * name_w}  {'-' * 7}  {'-' * 7}  {'-' * 6}  {'-' * 6}")
    overall_ratio = total_html / total_sugar if total_sugar else 0
    overall_saved = (1 - 1 / overall_ratio) * 100 if overall_ratio > 0 else 0
    char_ratio = total_html_chars / total_sugar_chars if total_sugar_chars else 0
    print(
        f"{'TOTAL':<{name_w}}  "
        f"{total_sugar:>7}  "
        f"{total_html:>7}  "
        f"{overall_ratio:>5.2f}x  "
        f"{overall_saved:>5.1f}%"
    )

    if args.verbose:
        print(f"\nCharacter counts: {total_sugar_chars:,} sugar → {total_html_chars:,} html ({char_ratio:.2f}x)")
        print(f"Encoding: {args.encoding}")
        print(f"Snapshots: {len(rows)}")


if __name__ == "__main__":
    main()
