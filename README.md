# 🦥 AutoVisuals  
### Automated Illustration & Prompt Generation Engine  
[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)]()
[![Status](https://img.shields.io/badge/Project-Active-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL%20%7C%20macOS-lightgrey.svg)]()
[![Static Badge](https://img.shields.io/badge/Chatbot-OpenAI%20%7C%20Anthropic%20%7C%20Gemini%20%7C%20Llama%20%7C%20DeepSeek-purple)]()
[![Static Badge](https://img.shields.io/badge/Build-Passing-%23a9f378)]()
[![Static Badge](https://img.shields.io/badge/Sloths%20Visuals-Powered-%23f378d0)]()
<div align="center">
<img src="docs/autovisuals_hex_icon_simple.svg" width="180" alt="AutoVisuals logo" />
</div>

<div align="center">

**AutoVisuals** designed by **Sloths Visuals (SlothsIntel)**, is a fully automated pipeline for generating **Midjourney-ready prompts**, sending them to **Discord**, automatically **downloading and splitting MJ images**, and building a beautiful **HTML gallery** with zoom navigation, for business design, internal datasets, Adobe Stock, or other illustration stocks.

</div>

---

# ⭐ Features

### 🔮 Prompt & Metadata Generator
- Generates output: **category**, **theme**, **title**, **description**, **45 keywords**, and **/imagine prompt**.
- Supports output formats: **txt**, **csv**, and **json**

### 🤖 Discord Automation
- Sends each prompt line to any Discord channel via **webhook**.
- Confirms each prompt in your private server with [one click]().
- Downloads MJ bot images via **Discord bot token**.
- Auto-splits 2×2 grids into 4 tiles.

### 🖼️ HTML Gallery Builder
- Builds a techno-tidy responsive gallery:
  - Date → Category → Images  
- Zoom mode includes:
  - **Prev/Next navigation**  
  - **Back to Gallery**

### 🚀 Full Pipeline Command
Run
```
autovisuals pipeline
```
Return:
```
generate → send → download → split → gallery
```

### 📊 Status Summary
Run
```
autovisuals status
```
Shows how many prompts/images exist per date/category.

---

# 🧩 Installation

####  Clone the repository
```bash
git clone https://github.com/slothsintel/AutoVisuals
cd AutoVisuals
```

### Install environment
```bash
pip install -r requirements.txt
```

### Add to PATH
```bash
echo 'export PATH="$HOME/AutoVisuals/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

# 🔐 Required Environment Variables

### For prompt generation, where to get [openai api]():
```
export API_KEY="your LLM API key"
```

### For Discord prompt sending, where to get [discord webhook]():
```
export WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### For Discord image downloading, where to get[discord bot token]() and [mj channel id]():
```
export DISCORD_BOT_TOKEN="your-bot-token"
export MJ_CHANNEL_ID="123456789012345678"
```

---

# 🧠 Usage

---

Run

```
autovisuals -h
```

Output

```
usage: autovisuals [-h] {generate,discord,download,gallery,pipeline,status} ...

AutoVisuals – automatic prompt & gallery pipeline.

positional arguments:
  {generate,discord,download,gallery,pipeline,status}
    generate            Generate prompts + metadata.
    discord             Send prompts to Discord webhook.
    download            Download Midjourney images.
    gallery             Build HTML gallery.
    pipeline            Full pipeline: generate → send → download → gallery.
    status              Show a tiny summary of prompts + images per date/category.

options:
  -h, --help            show this help message and exit
```

---

Run

```
autovisuals generate -h
```

Output

```
usage: autovisuals generate [-h] [-p PROVIDER] [-l LIST] [-m MODE] [-t TITLE] [-d RECORDS] [-r REPEAT] [-o OUT]

options:
  -h, --help            show this help message and exit
  -p, --provider PROVIDER
  -l, --list LIST
  -m, --mode MODE
  -t, --title TITLE
  -d, --records RECORDS
  -r, --repeat REPEAT
  -o, --out OUT
```

---

Run

```
autovisuals discord -h
```

Output

```
usage: autovisuals discord [-h] [-w WEBHOOK] [--category CATEGORY] [--all-categories]

options:
  -h, --help            show this help message and exit
  -w, --webhook WEBHOOK
                        Webhook URL (or WEBHOOK_URL env).
  --category CATEGORY   Specific category slug to send.
  --all-categories      Send prompts for all categories for latest date.
```

---

Run

```
autovisuals download -h
```

Outputs

```
usage: autovisuals download [-h] [-t TOKEN] [-c CHANNEL_ID] [-o OUT] [--limit LIMIT] [--idle-seconds IDLE_SECONDS]

options:
  -h, --help            show this help message and exit
  -t, --token TOKEN     Discord bot token (or DISCORD_BOT_TOKEN).
  -c, --channel-id CHANNEL_ID
                        Discord channel id (or MJ_CHANNEL_ID).
  -o, --out OUT         Download root folder.
  --limit LIMIT         Stop after N images (default: no limit).
  --idle-seconds IDLE_SECONDS
                        Auto-stop after this many seconds of inactivity (default: 180). Use 0 to disable.
```
---

Run

```
autovisuals gallery -h
```

Outputs

```
usage: autovisuals gallery [-h] [--download-dir DOWNLOAD_DIR] [--prompt-dir PROMPT_DIR] [--out OUT]

options:
  -h, --help            show this help message and exit
  --download-dir DOWNLOAD_DIR
                        MJ image root.
  --prompt-dir PROMPT_DIR
                        Prompt root.
  --out OUT             Gallery HTML output file.
```
---

Run all above in a pipeline

```
autovisuals pipeline -h
```

Outputs

```
usage: autovisuals pipeline [-h] [-p PROVIDER] [-l LIST] [-m MODE] [-t TITLE] [-d RECORDS] [-r REPEAT] [-o OUT] [-w WEBHOOK]
                            [--download-dir DOWNLOAD_DIR] [--gallery-out GALLERY_OUT] [--idle-seconds IDLE_SECONDS]

options:
  -h, --help            show this help message and exit
  -p, --provider PROVIDER
  -l, --list LIST
  -m, --mode MODE
  -t, --title TITLE
  -d, --records RECORDS
  -r, --repeat REPEAT
  -o, --out OUT         Prompt output root (used also as prompt_dir for gallery).
  -w, --webhook WEBHOOK
                        Webhook URL (or WEBHOOK_URL env).
  --download-dir DOWNLOAD_DIR
                        Download directory for images.
  --gallery-out GALLERY_OUT
                        Output gallery HTML file.
  --idle-seconds IDLE_SECONDS
                        Downloader idle timeout in seconds (default: 180).
```
---

# 📊 Status Command

Fast overview of prompts & images:

```
autovisuals status
```

Example:

```
DATE         CATEGORY             PROMPTS   IMAGES
2025-11-21   business                  3        12
2025-11-21   nature                    3        12
---------------------------------------------------
TOTAL                                6        24
```

---

# 🌟 Free Providers Included

AutoVisuals now includes two **completely free** API providers:

## 🦙 Llama (Llama 4 Maverick)
- No API key required  
- High performance  
- Good for bulk generation  
- Endpoint: https://api.llama-api.com/chat/completions

## 🧠 DeepSeek (DeepSeek V3)
- No API key required  
- Extremely fast  
- Stable JSON outputs  
- Endpoint: https://api.deepseek.com/free/chat/completions

---

# 🧰 Theme List Format
Each themes and its weights are in the same row, seperated by comma.
```
theme,weight
forest in fog,4
business teamwork,3
sunset over mountains,5
......
```

---

# 🏗 Future Modules
   
- Illustration Scaling  
- GUI (AutoVisuals Studio)  

---

# 🤝 Contributing

Maintained by **Sloths Visuals** of [**Sloths Intel**](https://github.com/slothsintel), and [**@drxilu**](https://github.com/drxilu).

---

# 📄 License

MIT License.

---

# 🦥 About Sloths Visuals

A creative visualisation brand under **Sloths Intel**, specialising in data visulisation and automated illustration pipelines.
