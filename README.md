# 🦥 AutoVisuals  
### Automated Illustration & Prompt Generation Engine

<img src='docs/autovisuals_hex_icon_simple.svg' align="right" height="800" />

[![Static Badge](https://img.shields.io/badge/Build-Passing-%23a9f378)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)]()

[![Status](https://img.shields.io/badge/Project-Active-brightgreen.svg)]()

[![Static Badge](https://img.shields.io/badge/Sloths%20Visuals-Powered-%23f378d0)]()

[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL%20%7C%20macOS-lightgrey.svg)]()

[![Static Badge](https://img.shields.io/badge/Chatbot-OpenAI%20%7C%20Anthropic%20%7C%20Gemini%20%7C%20Llama%20%7C%20DeepSeek-purple)]()



**AutoVisuals** designed by **Sloths Visuals (SlothsIntel)**, is a fully automated pipeline for generating **Midjourney-ready prompts**, sending them to **Discord**, automatically **downloading and splitting MJ images**, and building a beautiful **HTML gallery** with zoom navigation, for business design, internal datasets, Adobe Stock, or other illustration stocks.

---

# 📊 Contents
- [Features](#Features)
- [Installation](#Installation)
  - [From pip](#From-pip)
  - [From conda](#From-conda)
  - [From source(advanced)](#From-source-advanced)
- [Required Environment Variables](#RequiredEnvironment-Variables)
- [Usage](#Usage)
  - [Pipeline](#Pipeline)
  - [Subcommand](#Subcommand)
- [Free Providers Included](#Free-Providers-Included)
- [Theme List Format](#Theme-List-Format)
- [Future Modules](#Future-Modules)
- [Contribution](#Contribution)
- [License](#License)
- [About Sloths Visuals](#About-Sloths-Visuals)

---

# ⭐ Features

## 🔮 Prompt & Metadata Generator
- Generates output: **category**, **theme**, **title**, **description**, **45 keywords**, and **/imagine prompt**.
- Supports output formats: **txt**, **csv**, and **json**.

## 🤖 Discord Automation
- Sends each prompt line to any Discord channel via **webhook**.
- Confirms each prompt in your private server with [one click]().
- Downloads MJ bot images via **Discord bot token**.
- Auto-splits 2×2 grids into 4 tiles.

## 🖼️ HTML Gallery Builder
- Builds a techno-tidy responsive gallery:
  - Date → Category → Images  
- Zoom mode includes:
  - **Prev/Next navigation**.
  - **Back to Gallery**.

## 🚀 Full Pipeline Command
Run `autovisuals pipeline` to get a pipeline of `generate` → `send` → `download` → `split` → `gallery`.

## 📊 Status Summary
Run `autovisuals status` to show how many prompts/images exist per date/category.

---

# 🧩 Installation

## From pip

## From conda

## From source (advanced)

Clone the repository.
```shell
git clone https://github.com/slothsintel/AutoVisuals
cd AutoVisuals
```

Install environment.

```shell
pip install -r requirements.txt
```

Add to PATH.
```shell
echo 'export PATH="$HOME/AutoVisuals/scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

# 🔐 Required Environment Variables

For prompt generation, where to get [openai api]():
```shell
export API_KEY="your LLM API key"
```

For Discord prompt sending, where to get [discord webhook]():
```shell
export WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

For Discord image downloading, where to get[discord bot token]() and [mj channel id]():
```shell
export DISCORD_BOT_TOKEN="your-bot-token"
export MJ_CHANNEL_ID="123456789012345678"
```

---

# 🧠 Usage

## Pipeline

Pipeline command `autovisuals pipeline` to `generate` → `send` → `download` → `gallery`.

Option

```
-h, --help        show this help message and exit.
-p, --provider    chatbot provider, choose openai by default, anthropic, gemini, llama, or deepseek.
-l, --list        list of visuals list, choose autovisuals/data/adobe_cat.csv by default or others.
-m, --mode        mode to generate prompts by themes, choose r(random) by default or m(manual).
-t, --title       title to generate prompts, choose r(weight random) by default or m(manual) input.
-d, --records     number of prompts for each theme and title, 3 by default.
-r, --repeat      number of times to repeat each prompt for diversity, 5 by default.
-o, --out         prompt output directory, prompt/<date>/<theme> by default.
-w, --webhook     webhook URL, need to export it as environment variable.
--download-dir    images download directory, mj_downloads/<date>/<theme> by default.
--gallery-out     gallery file output directory, mj_gallery.html by default.
--idle-seconds    downloader idle timeout in seconds to proccess gallery, 180 by default.
```

## Subcommand

Subcommand `autovisuals generate` to generate prompts + metadata.

Option
```
-h, --help        show this help message and exit.
-p, --provider    chatbot provider, choose openai by default, anthropic, gemini, llama, or deepseek.
-l, --list        list of visuals list, choose autovisuals/data/adobe_cat.csv by default or others.
-m, --mode        mode to generate prompts by themes, choose r(random) by default or m(manual).
-t, --title       title to generate prompts, choose r(weight random) by default or m(manual) input.
-d, --records     number of prompts for each theme and title, 3 by default.
-r, --repeat      number of times to repeat each prompt for diversity, 5 by default.
-o, --out         prompt output directory, prompt/<date>/<theme> by default.
```

Subcommand `autovisuals discord` to send prompts to Discord webhook

Option
```
-h, --help        show this help message and exit.
-o, --out         prompt output directory, prompt/<date>/<theme> by default.
--category        specific category slug to send, true by default.
--all-categories  send prompts for all categories for latest date, true by default.
```

Subcommand `autovisuals download` to download Midjourney images

Option
```
-h, --help        show this help message and exit.
-t, --token       discord bot token, need to export it as environment variable.
-c, --channel-id  discord channel id, need to export it as environment variable.
-o, --out OUT     images download directory, mj_downloads/<date>/<theme> by default.
--limit LIMIT     stop after N images, no limit by default.
--idle-seconds    downloader idle timeout in seconds to proccess gallery, 180 by default.
```

Subcommand `autovisuals gallery` to build HTML gallery

Option
```
-h, --help        show this help message and exit.
--download-dir    images download directory, mj_downloads/<date>/<theme> by default.
--prompt-dir      prompt output directory, prompt/<date>/<theme> by default.
--out OUT         gallery file output directory, mj_gallery.html by default.
```

Additional command `autovisuals status` to Show a tidy summary of prompts + images per date/theme

Example
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

# 🤝 Contribution

Maintained by **Sloths Visuals** of [**Sloths Intel**](https://github.com/slothsintel), and [**@drxilu**](https://github.com/drxilu).

---

# 📄 License

MIT License.

---

# 🦥 About Sloths Visuals

A creative visualisation brand under **Sloths Intel**, specialising in data visulisation and automated illustration pipelines.
