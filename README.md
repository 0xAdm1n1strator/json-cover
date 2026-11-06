# json-cover

文章 → 短 JSON → 暗色代码截图风高清封面。

从**文章/教程正文**提炼短 JSON，再用本机 Chrome 无头截屏，生成**暗色代码编辑器截图风**高清封面（16:9）。

字是真渲染的，不是文生图糊字。

## 效果

默认：纯黑底、键亮蓝 `#6ad4ff`、值珊瑚红 `#ffb0a3`、大字紧裁约 11 行。

示例见 [`examples/dsh-workbuddy-cover-hd.png`](examples/dsh-workbuddy-cover-hd.png)（DSH 接 WorkBuddy 保姆教程）。

## 依赖

- Python 3.10+
- Google Chrome 或 Chromium（`google-chrome` / `chromium` 在 PATH 里）
- 可选：Pillow（`--resize` 缩预览图时需要）`pip install pillow`

## 用法

```bash
# 1) 准备封面 JSON（从文章提炼，字段贴事实）
cat > cover.json << 'JSON'
{
  "title": "DSH 接 WorkBuddy 保姆教程",
  "app": "DeepSeek Harness",
  "goal": "用本机转发接上 WorkBuddy",
  "plugin": "github:Ianzhyh/workbuddy-to-dsh",
  "install": {
    "steps": ["安装插件", "重启 DSH", "打开设置 → WorkBuddy"]
  }
}
JSON

# 2) 出 4K
python3 scripts/render_json_cover.py \
  --json cover.json \
  --out cover-4k.png \
  --width 3840 --height 2160 \
  --bg "#000000" \
  --font-px 92

# 3) 出 1080p 预览
python3 scripts/render_json_cover.py \
  --from-png cover-4k.png \
  --out cover-hd.png \
  --resize 1920x1080
```

### 常用参数

| 参数 | 含义 | 默认 |
|---|---|---|
| `--bg` | 背景色 | `#000000` |
| `--key-color` | JSON 键颜色 | `#6ad4ff` |
| `--value-color` | 字符串值颜色 | `#ffb0a3` |
| `--punct-color` | 括号/冒号 | `#f0f3f6` |
| `--font-px` | 字号 | 按行数自适应 |

## 给 Agent 用（Cursor / Grok Bot Skill）

仓库根目录的 [`SKILL.md`](SKILL.md) 可直接当 Agent Skill：用户说「按文章出 JSON 封面」「代码截图封面」时，先提炼 JSON，再跑本脚本出图。

## 原则

1. 封面 JSON **必须跟文章有关**，禁止塞无关人设/identity 卡  
2. **禁止**用文生图画代码（字体会糊、会编造符号）  
3. `steps` 最多 3–4 条；封面不是说明书全文  

## License

MIT
