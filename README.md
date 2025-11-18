# AutoVisuals – Automated Visual Metadata & Prompt Generation

![Logo](logo.png)

AutoVisuals is a tool designed to automate the creation of stock-style metadata and Midjourney prompts for a wide range of visual themes. It streamlines the process of generating high-quality, consistent metadata and prompts for use in creative projects, datasets, or generative AI workflows.

---

## Features

- **Automated Metadata Generation:** Quickly produce categories, titles, descriptions, and keywords for any visual theme.
- **Midjourney Prompt Creation:** Generates detailed prompts ready for use with Midjourney, including subject, style, lighting, and camera hints.
- **Multi-Provider Support:** Compatible with OpenAI, Anthropic, and Gemini models.
- **Flexible Theme Selection:** Choose themes randomly (weighted by CSV) or manually.
- **Multiple Output Formats:** Save results as JSON, CSV, and plain text.
- **Command-Line Interface:** Simple and customisable via CLI arguments.

---

## Installation

Ensure you have **Python 3.14** installed.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/slothsintel/AutoVisuals.git
   cd AutoVisuals
   ```

2. **Install dependencies:**
   ```bash
   pip install openai anthropic google-generativeai
   ```

---

## Usage

Set your API key as an environment variable (choose the appropriate key for your provider):

```bash
export API_KEY="sk-openai-xxxxx"    # For OpenAI GPT-5.1
export API_KEY="sk-ant-xxxxx"       # For Anthropic Claude 3
export API_KEY="AIza-xxxxx"         # For Gemini 1.5
```

Run the script with your chosen options:

```bash
python -m autovisuals.get_mj_prompt -p openai -l adobe_cat.csv -m r -t r -d 10 -r 5 -o prompt
```

**Arguments:**
- `-p`, `--provider` : AI provider (`openai`, `anthropic`, `gemini`)
- `-l`, `--list` : Path to theme list CSV (`theme,weight`)
- `-m`, `--mode` : Theme mode (`random` or `manual`)
- `-t`, `--title` : Title mode (`random` or `manual`)
- `-d`, `--records` : Number of records to generate
- `-r`, `--repeat` : Value for Midjourney `--r` flag
- `-o`, `--out` : Output root folder (default: `prompt/`)

**Example:**
```bash
python -m autovisuals.get_mj_prompt -p openai -l adobe_cat.csv -m r -t r -d 10 -r 5 -o prompt
```

---

## Theme List CSV Format

The theme list CSV should contain themes and their weights, e.g.:

```csv
theme,weight
animals,5
business,13
graphic resources,25
...
```

---

## Output

Results are saved in a timestamped subfolder within your output directory, in three formats:
- `meta.json` : Full metadata for each record
- `meta.csv` : CSV summary
- `prompt.txt` : Midjourney prompts, one per line

---

## Contributing

Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request.

---

## Licence

This project is licensed under the MIT Licence. See the [LICENCE](LICENCE) file for details.

---

## Acknowledgements

AutoVisuals uses the OpenAI, Anthropic, and Gemini APIs for prompt and metadata generation.

---

## Contact

For questions or support, please open an issue on GitHub.
