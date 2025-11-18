# 🦥 AutoVisuals  
### Automated Illustration & Prompt Generation Engine  
**A Sloths Visuals Project (by Sloths Intel)**

<div align="center">
<img src="docs/logo_dark.svg" width="180" alt="AutoVisuals logo" />
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

Supports by default:

- OpenAI (GPT‑5.1)  
- Anthropic (Claude 3.x)  
- Google Gemini (1.5 Flash)

---

# 📁 Project Structure

```
AutoVisuals/
├─ autovisuals/
│  ├─ __init__.py
│  ├─ get_mj_prompt.py
│  ├─ pipelines/
│  └─ data/
│     └─ adobe_cat.csv
│
├─ scripts/
├─ docs/
│  └─ logo_dark.svg
├─ README.md
└─ requirements.txt
```

---

# 🚀 Quick Start

## 1. Install dependencies
```
conda create -n visuals python>=3.14
```
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
python -m autovisuals.get_mj_prompt [options]

### ---- Providers ----
-p openai
-p anthropic
-p gemini

### ---- Theme mode ----
-m r          # random theme (weighted)
-m m          # manual theme (you will be prompted)

### ---- Title mode ----
-t r          # random title
-t m          # manual title (only valid when -m m)

### ---- Records count ----
-d 5          # generate 5 records

### ---- Repeats value ----
-r 5          # style repeat value

# ---- Theme list CSV ----
-l adobe_cat.csv
-l custom_list.csv

# ---- Output folder ----
-o prompt
-o results

## 4. Quick examples
### 1) 5 random records using OpenAI
```
python -m autovisuals.get_mj_prompt -p openai -m r -t r -d 5
```
### 2) Manual theme + manual title
```
python -m autovisuals.get_mj_prompt -m m -t m
```
### 3) Use a custom theme list
```
python -m autovisuals.get_mj_prompt -l my_themes.csv
```
### 4) Save to custom output directory
```
python -m autovisuals.get_mj_prompt -o results
```

## 5. Help
python -m autovisuals.get_mj_prompt --help


---

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
## Metadata CSV
```csv
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

```python
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
source ~/.bashrc
```

---

# 🏗 Future Modules
 
- Midjourney/Discord API integration  
- Illustration Scaling  
- GUI (AutoVisuals Studio)  

---

# 🤝 Contributing

Maintained by **Sloths Visuals** by [**Sloths Intel**](https://github.com/slothsintel), and [**@drxilu**](https://github.com/drxilu).

---

# 📄 License

MIT License.

---

# 🦥 About Sloths Visuals

A creative visualisation brand under **Sloths Intel**, specialising in data visulisation and automated illustration pipelines.
