# 🦥 AutoVisuals  
### Automated Illustration & Prompt Generation Engine  
<div align="center">
<img src="docs/logo_light.svg" width="180" alt="AutoVisuals logo" />
</div>

<div align="center">

**A Sloths Intel project (by Sloths Visuals)......**

</div>

---

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)]()
[![Status](https://img.shields.io/badge/Project-Active-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL%20%7C%20macOS-lightgrey.svg)]()

---

# 📘 Overview

**AutoVisuals** is a modular AI engine designed to automatically generate:

- 🎨 High-quality creative themes 
- 🏷 Adobe Stock style metadata
- 📝 Midjourney-ready prompts   
- 🔄 Batch generation workflows  

Supported chatbots:

- OpenAI (GPT‑5.1)  
- Anthropic (Claude 3.x)  
- Google Gemini (1.5 Flash)
- Deepseek ()
- Meta Llama ()

---

# 📁 Project Structure

<div style="overflow-x: auto;">

<pre>
AutoVisuals/
├─ autovisuals/
│  ├─ __init__.py
│  ├─ get_mj_prompt.py
│  ├─ pipelines/
│  │   └─ (future batch modules)
│  └─ data/
│      └─ adobe_cat.csv
│
├─ scripts/
│  ├─ run_get_mj_prompt.py
│  └─ run_batch_generation.py
│
├─ docs/
│  ├─ logo_light.svg
│  ├─ logo_dark.svg
│  └─ index.html
│
├─ requirements.txt
└─ README.md
</pre>

</div>

---

# 🚀 Quick Start

## 1. Install dependencies
first
```
conda create -n visuals python>=3.14
```
then
```
pip install openai anthropic google-generativeai
```
or
```
pip install -r requirements.txt
```
## 2. Export API key
```
export API_KEY="your-api-key"
```

## 3. Usage
### Basic command
```
python -m autovisuals.get_mj_prompt [options]
```

### Providers
```
-p openai
-p anthropic
-p gemini
-p llama
-p deepseek
```

### Theme mode
```
-m r          # random theme (weighted)
-m m          # manual theme (you will be prompted)
```

### Title mode
```
-t r          # random title
-t m          # manual title (only valid when -m m)
```

### Records count
```
-d 5          # generate 5 records
```

### Repeats value
```
-r 5          # style repeat value
```

### Theme list CSV
```
-l adobe_cat.csv
-l custom_list.csv
```
### Output folder
```
-o prompt
-o results
```

## 4. Quick examples
### 1. 5 random records using OpenAI
```
autovisuals generate -p openai -m r -t r -d 5
```
### 2. Manual theme + manual title
```
autovisuals generate -m m -t m
```
### 3. Use a custom theme list
```
autovisuals generate -l my_themes.csv
```
### 4. Save to custom output directory
```
autovisuals generate -o results
```

## 5. Help
```
autovisuals generate --help
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

# 🧠 Theme List Format
Each themes and its weights are in the same row, seperated by comma.
```
theme,weight
forest in fog,4
business teamwork,3
sunset over mountains,5
```

---

# 🖥 Example Output

## Midjourney Prompt
```
/imagine prompt futuristic cyber sloth sipping coffee in neon‑lit alley --ar 16:9 --s 20 --c 10 --raw --r 5
```

## Metadata JSON
```json
{
  "category": "nature",
  "theme": "forest in fog",
  "prompt": "futuristic forest scene...",
  "title": "Mysterious Forest Fog",
  "description": "A soft atmospheric forest scene.",
  "keywords": ["forest", "...", "generative ai"]
}
```
---

# 🧩 Use Inside Python

```
python
from autovisuals.get_mj_prompt import generate_for_theme
item = generate_for_theme("openai", "misty mountains sunrise", repeat=5)
print(item["prompt"])
```

---

# 🧰 WSL/Linux/MacOS setup

```
cd ~/projects/AutoVisuals
pip install -r requirements.txt
echo 'export API_KEY="your_api_key"' >> ~/.bashrc
echo 'export PATH="$HOME/AutoVisuals/scripts:$PATH""' >> ~/.bashrc
source ~/.bashrc
```

---

# 🏗 Future Modules
 
- Midjourney/Discord API integration  
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
