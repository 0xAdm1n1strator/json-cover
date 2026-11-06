---
name: article-json-cover
description: >-
  When the user wants an article/tutorial cover as a dark code-editor JSON
  screenshot (“JSON封面”, “代码截图封面”, “按文章出封面”), distill the article into short JSON
  and render a crisp HD/4K cover (black bg, bright blue keys, coral values)—not
  AI-drawn code and not a portrait.
---
# Article → JSON code-screenshot cover

Turn an **article/tutorial** into a short JSON card, then render a **dark code-editor screenshot** cover (16:9 HD/4K). For WeChat/Page/README covers.

**Not for:** portrait covers, AI-painted fake code glyphs, JSON unrelated to the article.

## Inputs

1. Article body (paste / `.md` / `.html` / Page text)
2. Optional crop reference (“大概这样就行”)
3. Optional `--bg` (default `#000000`) and size (default 4K + 1920×1080 preview)

## Steps

### 1. Distill cover JSON from the article

After reading the piece, write a **short, scannable** JSON grounded in facts—no invented plugins/ports/commands. Suggested shape (~10–14 lines):

```json
{
  "title": "article title",
  "app": "main product/tool",
  "goal": "one-line goal in plain words",
  "plugin": "key plugin or omit",
  "install": {
    "steps": ["step1", "step2", "step3"]
  }
}
```

Rules:

- Use real names from the article
- At most 3–4 `steps`, verb-led
- No long paragraphs; cover ≠ full manual
- Show the JSON to the user once unless they said “直接出图”

### 2. Render with the script (never text-to-image for code)

From this skill directory:

```bash
python3 scripts/render_json_cover.py \
  --json cover.json \
  --out /workspace/covers/cover-4k.png \
  --width 3840 --height 2160 \
  --bg "#000000"

python3 scripts/render_json_cover.py \
  --from-png /workspace/covers/cover-4k.png \
  --out /workspace/covers/cover-hd.png \
  --resize 1920x1080
```

Uses local Chrome/Chromium headless on real HTML so text stays sharp. Needs `google-chrome` or `chromium`, Python 3, and Pillow for `--resize`.

Default look (ask before changing):

| Item | Default |
|---|---|
| Background | `#000000` |
| Keys | `#6ad4ff` |
| String values | `#ffb0a3` |
| Punctuation | `#f0f3f6` |
| Line numbers | `#8b949e` |
| Layout | large type, tight crop ~11 lines, no window chrome |

### 3. Deliver

- Attach 1920×1080 in chat
- Provide 4K path; copy to Desktop when a machine is connected
- One line on which article facts the JSON mirrors; iterate via the script, not GenerateImage

## Common tweak phrases

- 「裁剪 / 放大字体」→ larger font, less padding, fewer lines
- 「字体颜色要分明 / 再亮色」→ brighter key/value colors
- 「背景用黑色」→ `--bg #000000`
- 「内容要跟文章有关」→ re-distill JSON; never reuse unrelated identity cards

## Forbidden

- GenerateImage / T2I “drawing” code (blurry / hallucinated glyphs)
- Cover JSON unrelated to the article
- Dumping the whole tutorial into JSON
