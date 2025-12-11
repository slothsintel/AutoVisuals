# AutoVisuals Overlay Gallery with All Tab + Date Tabs and Theme Subtabs + All-Themes Under Date
# Includes scroll restore, overlay, and metadata-aware thumbnails

from __future__ import annotations
import argparse
import datetime
import html
import json
import os
import csv
from pathlib import Path
from typing import Dict, List

def escape(s: str) -> str:
    return html.escape(s, quote=True)

def collect_images(download_root: Path) -> Dict[str, Dict[str, List[Path]]]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    out: Dict[str, Dict[str, List[Path]]] = {}
    for day_dir in sorted(download_root.iterdir(), reverse=True):
        if not day_dir.is_dir():
            continue
        date = day_dir.name
        out[date] = {}
        for cat_dir in sorted(day_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            images = [
                p for p in sorted(cat_dir.iterdir())
                if p.suffix.lower() in exts
            ]
            if images:
                out[date][cat_dir.name] = images
    return out

def load_metadata(prompt_root: Path) -> Dict[str, Dict[str, str]]:
    meta = {}
    for date_dir in prompt_root.iterdir():
        if not date_dir.is_dir():
            continue
        for theme_dir in date_dir.iterdir():
            meta_file = theme_dir / "meta.csv"
            if not meta_file.exists():
                continue
            with open(meta_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    base_title = row.get("title", "").replace(" ", "_").strip()
                    if base_title:
                        meta[base_title] = {
                            "title": row.get("title", ""),
                            "keywords": row.get("keywords", ""),
                            "description": row.get("description", ""),
                            "category": row.get("category") or row.get("theme") or theme_dir.name
                        }
    return meta

def fuzzy_match(filename: str, metadata: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    for key in metadata:
        if filename.startswith(key):
            return metadata[key]
    return {}

def build_gallery(download_root, prompt_root, out_file):
    from datetime import datetime
    images = collect_images(Path(download_root))
    metadata = load_metadata(Path(prompt_root))
    now = datetime.now().isoformat(timespec="seconds")

    out_path = Path(out_file)
    parts: List[str] = []

    parts.append("""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>AutoVisuals Gallery</title>
<style>
body {
  background:#ffe4e1;
  color:black;
  font-family:sans-serif;
  margin:0;
  padding:1rem;
}
.tabs, .subtabs {
  display:flex;
  flex-wrap:wrap;
  gap:0.5rem;
  margin:1rem 0;
}
.tabs button, .subtabs button {
  padding:0.4rem 0.8rem;
  background:#d46a6a;
  border:none;
  border-radius:999px;
  color:white;
  cursor:pointer;
}
.tabs button.active, .subtabs button.active {
  background:#1e293b;
}
.grid {
  display:none;
  grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
  gap:0.6rem;
}
.card {
  background:#fef0f0;
  padding:0.5rem;
  border-radius:0.5rem;
}
.card img { width:100%; border-radius:0.5rem; }
.card .filename { margin-top:0.25rem; font-size:0.7rem; color:#240101; }
#overlay {
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.95);
  display:none;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  z-index:9999;
  padding:1rem;
  text-align:center;
}
#overlay.open { display:flex; }
#overlay img {
  max-width:90vw;
  max-height:70vh;
  border-radius:0.75rem;
  cursor: pointer;
}
#overlay .caption {
  margin-top:1rem;
  color:#e2e8f0;
  font-size:0.9rem;
}
#overlay .meta {
  margin-top:0.5rem;
  color:#94a3b8;
  font-size:0.8rem;
  max-width:90vw;
  white-space:pre-wrap;
}
#overlay .nav {
  display:flex;
  gap:1rem;
  margin-top:1rem;
}
.overlay-btn {
  padding:0.4rem 1rem;
  background:#1e293b;
  border:1px solid #3b82f6;
  border-radius:999px;
  color:white;
  cursor:pointer;
}
#overlay .close-btn {
  position:absolute;
  top:1rem;
  right:1rem;
  font-size:1.5rem;
  background:none;
  border:none;
  color:#f1f5f9;
  cursor:pointer;
  font-weight:bold;
}
#top-btn {
  position:fixed;
  bottom:20px;
  right:20px;
  background:#1e293b;
  color:#fff;
  border:none;
  padding:0.5rem 0.8rem;
  border-radius:999px;
  cursor:pointer;
  z-index:10000;
  font-size:0.9rem;
  border:1px solid #3b82f6;
}
</style>
<script>
let AV_IMAGES = [];
let AV_INDEX = 0;
let AV_SCROLL = 0;
function openOverlay(images, index) {
  AV_SCROLL = window.scrollY;
  AV_IMAGES = images;
  AV_INDEX = index;
  showImage(0);
  document.getElementById('overlay').classList.add('open');
}
function closeOverlay() {
  document.getElementById('overlay').classList.remove('open');
  window.scrollTo({ top: AV_SCROLL, behavior: 'instant' });
}
function showImage(delta) {
  let n = AV_INDEX + delta;
  if (n < 0 || n >= AV_IMAGES.length) return;
  AV_INDEX = n;
  const data = AV_IMAGES[n];
  document.getElementById('overlay-img').src = data.url;
  document.getElementById('caption').textContent = data.name;
  document.getElementById('metadata').textContent = `Filename: ${data.name}\nTitle: ${data.title}\nCategory: ${data.category}\nDescription: ${data.description}\nKeywords: ${data.keywords}`;
}
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
document.addEventListener('keydown', e => {
  if (!document.getElementById('overlay').classList.contains('open')) return;
  if (e.key === 'Escape') closeOverlay();
  if (e.key === ' ') { e.preventDefault(); closeOverlay(); }
  if (e.key === 'ArrowLeft') showImage(-1);
  if (e.key === 'ArrowRight') showImage(1);
});
document.addEventListener('click', e => {
  const overlay = document.getElementById('overlay');
  if (!overlay.classList.contains('open')) return;
  const bounds = overlay.getBoundingClientRect();
  const x = e.clientX;
  if (x < bounds.width * 0.3) showImage(-1);
  else if (x > bounds.width * 0.7) showImage(1);
});
document.addEventListener('wheel', e => {
  const overlay = document.getElementById('overlay');
  if (!overlay.classList.contains('open')) return;
  if (e.deltaY < 0) showImage(-1);
  else if (e.deltaY > 0) showImage(1);
});
function showAllTabs() {
  document.querySelectorAll('.dateblock').forEach(e => e.style.display = 'block');
  document.querySelectorAll('.grid').forEach(e => e.style.display = 'grid');
}
</script>
</head>
<body>
<div id='overlay'>
  <button class='close-btn' onclick='closeOverlay()'>×</button>
  <img id='overlay-img' src=''>
  <div class='caption' id='caption'></div>
  <div class='meta' id='metadata'></div>
  <div class='nav'>
    <button class='overlay-btn' onclick='showImage(-1)'>&larr; Prev</button>
    <button class='overlay-btn' onclick='closeOverlay()'>Back to Gallery</button>
    <button class='overlay-btn' onclick='showImage(1)'>Next &rarr;</button>
  </div>
</div>
<button id='top-btn' onclick='scrollToTop()'>↑ Top</button>
<h1>AutoVisuals Gallery</h1>
<p>Generated at """ + escape(now) + """</p>
<div class='tabs'>
<button onclick='showAllTabs()'>All</button>
""")

    for date, themes in images.items():
        parts.append(f"<button onclick=\"document.querySelectorAll('.dateblock').forEach(e=>e.style.display='none');document.getElementById('date-{date}').style.display='block'\">{escape(date)}</button>")
    parts.append("</div>")

    for date, themes in images.items():
        parts.append(f"<div id='date-{date}' class='dateblock' style='display:none;'>")
        parts.append("<div class='subtabs'>")
        for theme in themes:
            tab_id = f"{date}-{theme}".replace(" ", "_").replace("/", "-")
            parts.append(f"<button onclick=\"document.querySelectorAll('#date-{date} .grid').forEach(e=>e.style.display='none');document.getElementById('{tab_id}').style.display='grid'\">{escape(theme)}</button>")
        parts.append(f"<button onclick=\"document.querySelectorAll('#date-{date} .grid').forEach(e=>e.style.display='grid')\">All Themes</button>")
        parts.append("</div>")
        for theme, files in themes.items():
            tab_id = f"{date}-{theme}".replace(" ", "_").replace("/", "-")
            parts.append(f"<div class='grid' id='{tab_id}'>")
            img_data = []
            for p in files:
                rel = os.path.relpath(p, start=out_path.parent).replace("\\", "/")
                name = p.name
                stem_base = "_".join(Path(name).stem.split("_")[:-2])
                meta = fuzzy_match(stem_base, metadata)
                img_data.append({
                    "url": rel,
                    "name": name,
                    "title": meta.get("title", ""),
                    "keywords": meta.get("keywords", ""),
                    "description": meta.get("description", ""),
                    "category": meta.get("category", theme)
                })
            jdata = json.dumps(img_data)
            for i, p in enumerate(files):
                rel = os.path.relpath(p, start=out_path.parent).replace("\\", "/")
                name = p.name
                parts.append(f"""
<div class='card'>
  <a href='{escape(rel)}' onclick='event.preventDefault(); openOverlay({jdata}, {i});'>
    <img src='{escape(rel)}'>
  </a>
  <div class='filename'>{escape(name)}</div>
</div>
""")
            parts.append("</div>")
        parts.append("</div>")

    if images:
        first_date = next(iter(images))
        parts.append(f"<script>document.getElementById('date-{first_date}').style.display='block';</script>")
        first_theme = next(iter(images[first_date]))
        first_tab = f"{first_date}-{first_theme}".replace(" ", "_").replace("/", "-")
        parts.append(f"<script>document.getElementById('{first_tab}').style.display='grid';</script>")

    parts.append("</body></html>")
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return out_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-root", default="mj_downloads")
    parser.add_argument("--prompt-root", default="prompt")
    parser.add_argument("--out", default="mj_gallery.html")
    args = parser.parse_args()
    build_gallery(args.download_root, args.prompt_root, args.out)
    print("Gallery created at:", args.out)

if __name__ == "__main__":
    main()
