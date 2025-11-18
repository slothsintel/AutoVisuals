# 🦥 AutoVisuals  
### Automated Illustration & Prompt Generation Engine  
**A Sloths Visuals Project (by Slothsintel)**

<div align="center">
<img src="docs/logo.png" width="180" alt="AutoVisuals logo" />
</div>

---

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![Status](https://img.shields.io/badge/Project-Active-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20WSL%20%7C%20macOS-lightgrey.svg)]()

---

# 📘 Overview

**AutoVisuals** is a modular AI engine designed to automatically generate:

- 📝 Midjourney-ready prompts  
- 🏷 Stock-photo metadata (title, description, 45 keywords)  
- 🎨 High-quality creative themes  
- 🔄 Batch generation workflows  

Supports:

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
│  └─ logo.png
├─ README.md
└─ requirements.txt
```

---

# 🚀 Quick Start

## 1. Install dependencies
```
pip install openai anthropic google-generativeai
```

## 2. Export API key
```
export API_KEY="your-api-key"
```

## 3. Run AutoVisuals
```
python -m autovisuals.get_mj_prompt \
    -p openai \
    -l adobe_cat.csv \
    -m r \
    -t r \
    -d 3 \
    -r 5 \
    -o prompt
```

Outputs saved to:
```
autovisuals/prompt/<timestamp>/
```

---

# 🧠 Theme List Format

```
theme,weight
forest in fog,4
business teamwork,3
sunset over mountains,5
```

---

# 🖥 Example Output

### Midjourney Prompt
```
/imagine prompt futuristic cyber sloth sipping coffee in neon‑lit alley --ar 16:9 --s 20 --c 10 --raw --r 5
```

### Metadata JSON
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

```python
from autovisuals.get_mj_prompt import generate_for_theme
item = generate_for_theme("openai", "misty mountains sunrise", repeat=5)
print(item["prompt"])
```

---

# 🧰 WSL Setup

```
cd ~/projects/AutoVisuals
pip install -r requirements.txt
echo 'export API_KEY="sk-openai-xxxxx"' >> ~/.bashrc
source ~/.bashrc
```

---

# 🏗 Future Modules

- Batch pipelines  
- Prompt ranking  
- Midjourney API integration  
- Tagging, CMS export  
- GUI (AutoVisuals Studio)  

---

# 🤝 Contributing

Maintained by **Slothsintel**, **Sloths Visuals**, and **@drxilu**.

---

# 📄 License

MIT License.

---

# 🦥 About Sloths Visuals

A creative technology brand under **Slothsintel**, specialising in automated illustration pipelines.
