#!/usr/bin/env python3
"""Render a dark code-editor JSON screenshot cover via Chrome headless."""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_BG = "#000000"
DEFAULT_KEY = "#6ad4ff"
DEFAULT_VAL = "#ffb0a3"
DEFAULT_PUNCT = "#f0f3f6"
DEFAULT_GUTTER = "#8b949e"


def find_chrome() -> str:
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit("Chrome/Chromium not found in PATH")


def load_json(path: str) -> object:
    if path == "-":
        return json.load(sys.stdin)
    text = Path(path).read_text(encoding="utf-8")
    return json.loads(text)


def json_to_html_lines(obj: object, indent: int = 0) -> list[tuple[str, str]]:
    """Return list of (gutter_ignored, html_line) for pretty JSON with spans."""
    sp = "  " * indent
    lines: list[str] = []

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    def key_span(k: str) -> str:
        return f'<span class="k">"{esc(k)}"</span>'

    def str_span(v: str) -> str:
        return f'<span class="v">"{esc(v)}"</span>'

    def punct(p: str) -> str:
        return f'<span class="p">{esc(p)}</span>'

    def emit_value(value: object, level: int, trailing: str) -> None:
        pad = "  " * level
        if isinstance(value, dict):
            lines.append(f"{pad}{punct('{')}")
            items = list(value.items())
            for i, (k, v) in enumerate(items):
                comma = "," if i < len(items) - 1 else ""
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}  {key_span(k)}{punct(':')} ")
                    # attach opening on same conceptual block: rewrite last differently
                    lines[-1] = f"{pad}  {key_span(k)}{punct(':')} {punct('{') if isinstance(v, dict) else punct('[')}"
                    if isinstance(v, dict):
                        inner = list(v.items())
                        # reopen properly
                        lines[-1] = f"{pad}  {key_span(k)}{punct(':')} {punct('{')}"
                        for j, (ik, iv) in enumerate(inner):
                            ic = "," if j < len(inner) - 1 else ""
                            if isinstance(iv, (dict, list)):
                                emit_pair(ik, iv, level + 2, ic)
                            else:
                                lines.append(
                                    f"{pad}    {key_span(ik)}{punct(':')} {format_scalar(iv)}{punct(ic)}"
                                )
                        lines.append(f"{pad}  {punct('}')}{punct(comma)}")
                    else:
                        lines[-1] = f"{pad}  {key_span(k)}{punct(':')} {punct('[')}"
                        for j, item in enumerate(v):
                            ic = "," if j < len(v) - 1 else ""
                            if isinstance(item, (dict, list)):
                                emit_value(item, level + 2, ic)
                            else:
                                lines.append(f"{pad}    {format_scalar(item)}{punct(ic)}")
                        lines.append(f"{pad}  {punct(']')}{punct(comma)}")
                else:
                    lines.append(
                        f"{pad}  {key_span(k)}{punct(':')} {format_scalar(v)}{punct(comma)}"
                    )
            lines.append(f"{pad}{punct('}')}{punct(trailing)}")
        elif isinstance(value, list):
            lines.append(f"{pad}{punct('[')}")
            for i, item in enumerate(value):
                comma = "," if i < len(value) - 1 else ""
                if isinstance(item, (dict, list)):
                    emit_value(item, level + 1, comma)
                else:
                    lines.append(f"{pad}  {format_scalar(item)}{punct(comma)}")
            lines.append(f"{pad}{punct(']')}{punct(trailing)}")
        else:
            lines.append(f"{pad}{format_scalar(value)}{punct(trailing)}")

    def emit_pair(k: str, v: object, level: int, trailing: str) -> None:
        pad = "  " * level
        if isinstance(v, dict):
            lines.append(f"{pad}{key_span(k)}{punct(':')} {punct('{')}")
            items = list(v.items())
            for i, (ik, iv) in enumerate(items):
                ic = "," if i < len(items) - 1 else ""
                if isinstance(iv, (dict, list)):
                    emit_pair(ik, iv, level + 1, ic)
                else:
                    lines.append(
                        f"{pad}  {key_span(ik)}{punct(':')} {format_scalar(iv)}{punct(ic)}"
                    )
            lines.append(f"{pad}{punct('}')}{punct(trailing)}")
        elif isinstance(v, list):
            lines.append(f"{pad}{key_span(k)}{punct(':')} {punct('[')}")
            for i, item in enumerate(v):
                ic = "," if i < len(v) - 1 else ""
                if isinstance(item, (dict, list)):
                    emit_value(item, level + 1, ic)
                else:
                    lines.append(f"{pad}  {format_scalar(item)}{punct(ic)}")
            lines.append(f"{pad}{punct(']')}{punct(trailing)}")
        else:
            lines.append(
                f"{pad}{key_span(k)}{punct(':')} {format_scalar(v)}{punct(trailing)}"
            )

    def format_scalar(v: object) -> str:
        if isinstance(v, bool):
            return f'<span class="v">{"true" if v else "false"}</span>'
        if v is None:
            return '<span class="v">null</span>'
        if isinstance(v, (int, float)):
            return f'<span class="n">{v}</span>'
        return str_span(str(v))

    # root must be object for covers
    if not isinstance(obj, dict):
        raise SystemExit("cover JSON root must be an object")
    lines.append(punct("{"))
    items = list(obj.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        emit_pair(k, v, 1, comma)
    lines.append(punct("}"))
    return lines


def build_html(
    obj: object,
    width: int,
    height: int,
    bg: str,
    key_c: str,
    val_c: str,
    punct_c: str,
    gutter_c: str,
    font_px: int | None,
) -> str:
    lines = json_to_html_lines(obj)
    n = len(lines)
    # auto font: fit ~11–14 lines comfortably
    if font_px is None:
        font_px = max(48, min(100, int(height / max(n + 2, 8) / 1.45)))
    gutter = "<br>".join(str(i) for i in range(1, n + 1))
    code = "\n".join(lines)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{width}px;height:{height}px;overflow:hidden;background:{bg};
font-family:"Cascadia Code","Consolas","JetBrains Mono","Microsoft YaHei Mono",monospace}}
.editor{{width:{width}px;height:{height}px;background:{bg};position:relative;
padding:{int(height*0.07)}px {int(width*0.04)}px {int(height*0.05)}px {int(width*0.08)}px;
display:flex;align-items:center}}
.wrap{{position:relative;width:100%}}
.gutter{{position:absolute;left:-{int(width*0.045)}px;top:0;color:{gutter_c};
font-size:{font_px}px;line-height:1.42;text-align:right;width:{int(font_px*1.4)}px;font-weight:500}}
.code{{font-size:{font_px}px;line-height:1.42;white-space:pre;font-weight:600;letter-spacing:0.5px}}
.k{{color:{key_c}}}.v{{color:{val_c}}}.n{{color:{key_c}}}.p{{color:{punct_c}}}
</style></head><body><div class="editor"><div class="wrap">
<div class="gutter">{gutter}</div>
<div class="code">{code}</div>
</div></div></body></html>"""


def screenshot(chrome: str, html_path: Path, out: Path, width: int, height: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        "--force-device-scale-factor=1",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def resize_png(src: Path, dest: Path, size: str) -> None:
    from PIL import Image

    w, h = size.lower().split("x")
    im = Image.open(src)
    im.resize((int(w), int(h)), Image.Resampling.LANCZOS).save(dest, "PNG", optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", help="JSON file or - for stdin")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--width", type=int, default=3840)
    ap.add_argument("--height", type=int, default=2160)
    ap.add_argument("--bg", default=DEFAULT_BG)
    ap.add_argument("--key-color", default=DEFAULT_KEY)
    ap.add_argument("--value-color", default=DEFAULT_VAL)
    ap.add_argument("--punct-color", default=DEFAULT_PUNCT)
    ap.add_argument("--gutter-color", default=DEFAULT_GUTTER)
    ap.add_argument("--font-px", type=int, default=None)
    ap.add_argument("--from-png", help="only resize an existing PNG")
    ap.add_argument("--resize", help="WxH when using --from-png or after render")
    args = ap.parse_args()

    out = Path(args.out)
    if args.from_png:
        if not args.resize:
            raise SystemExit("--from-png requires --resize WxH")
        resize_png(Path(args.from_png), out, args.resize)
        print(out)
        return

    if not args.json:
        raise SystemExit("--json is required unless --from-png")

    obj = load_json(args.json)
    chrome = find_chrome()
    page = build_html(
        obj,
        args.width,
        args.height,
        args.bg,
        args.key_color,
        args.value_color,
        args.punct_color,
        args.gutter_color,
        args.font_px,
    )
    with tempfile.TemporaryDirectory() as td:
        html_path = Path(td) / "cover.html"
        html_path.write_text(page, encoding="utf-8")
        screenshot(chrome, html_path, out, args.width, args.height)

    if args.resize:
        hd = out.with_name(out.stem.replace("-4k", "") + "-hd.png") if "4k" in out.stem else out.with_name(out.stem + "-hd.png")
        # if --resize given with render, write second file next to out when out is 4k-ish
        resize_png(out, Path(str(out).replace("-4k", "-hd")) if "-4k" in str(out) else out.with_name(out.stem + "-hd.png"), args.resize)

    print(out)


if __name__ == "__main__":
    main()
