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

**AutoVisuals** is a fully automated pipeline for generating **Midjourney-ready prompts**, sending them to **Discord**, automatically **downloading and splitting MJ images**, and building a beautiful **HTML gallery** with zoom navigation.

Designed for **Sloths Visuals (SlothsIntel)**, this tool allows one-click production of consistent, stock-ready illustration batches for Adobe Stock or internal datasets.

</div>

---

# ⭐ Features

### 🔮 Prompt & Metadata Generator
- Generates **category**, **theme**, **title**, **description**, **45 keywords**, and **/imagine prompt**.
- Supports multiple LLM providers:
  - OpenAI GPT-5.1  
  - Claude 3 Sonnet  
  - Gemini 1.5  
  - Llama 4 Maverick (free)  
  - DeepSeek-V3 (free)
- Auto-attaches `[av:id]` tags for later category mapping.

### 🤖 Discord Automation
- Sends each prompt line to any Discord channel via **webhook**.
- Confirms each prompt in your private server with [one click]().
- Downloads MJ bot images via **Discord bot token**.
- Auto-splits 2×2 grids into 4 tiles.  
- Auto-categorises images using `[av:id]`.

### 🖼️ HTML Gallery Builder
- Builds a polished responsive gallery:
  - Date → Category → Images  
- Zoom mode includes:
  - **Prev/Next buttons**  
  - **Mouse wheel navigation (up = prev, down = next)**  
  - **Keyboard ← → arrows**  
  - **Back to Gallery button**

### 🚀 Full Pipeline Command
```
autovisuals pipeline
```
Runs:
```
generate → send → download → split → gallery
```

### 📊 Status Summary
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

### Add to PATH (WSL recommended)
```bash
echo 'export PATH="$PATH:/mnt/c/Users/xilu/OneDrive/bus/slothsintel/slothsvisuals/AutoVisuals/scripts"' >> ~/.bashrc
source ~/.bashrc
```

---

# 🔐 Required Environment Variables

### For prompt generation:
```
export API_KEY="your LLM API key"
```

### For Discord prompt sending:
```
export WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### For Discord image downloading:
```
export DISCORD_BOT_TOKEN="your-bot-token"
export MJ_CHANNEL_ID="123456789012345678"
```

---

# 🧠 Usage

---

## 1️⃣ Generate prompts & metadata

```
autovisuals generate -d 3 -p openai
```

Outputs:

```
prompt/YYYY-MM-DD/category/
   ├── meta.json
   ├── meta.csv
   └── prompt.txt
```

---

## 2️⃣ Send prompts to Discord

```
autovisuals discord --all-categories
```

or send latest category:

```
autovisuals discord
```

---

## 3️⃣ Download Midjourney images

```
autovisuals download
```

The downloader:
- Watches your MJ channel  
- Automatically fetches new images  
- Splits 2×2 → 4 images  
- Categorises using `[av:id]`  

Idle timeout default: **180 seconds**

---

## 4️⃣ Generate HTML gallery

```
autovisuals gallery
```

Outputs:

```
mj_gallery.html
mj_zoom/date/category/image.html
```

With:
- Clickable thumbnails  
- Zoom view  
- Keyboard ← →  
- Mouse wheel navigation  
- Smooth UX  

---

## 5️⃣ Full Pipeline

```
autovisuals pipeline
```

Runs everything:

```
(1) generate  
(2) send to discord  
(3) download & split  
(4) build gallery  
```

Zero manual file work.

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
