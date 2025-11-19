"""
Simple HTML gallery builder for AutoVisuals downloads.

Scans a download root (e.g. mj_downloads/ YYYY-MM-DD/*.png)
and writes a static HTML file with all images.
"""

from pathlib import Path
from html import escape
import datetime


def build_gallery(
    download_root: str | Path = "mj_downloads",
    out_file: str | Path = "mj_gallery.html",
) -> Path:
    download_root = Path(download_root)
    out_path = Path(out_file)

    if not download_root.exists():
        raise FileNotFoundError(f"Download root not found: {download_root}")

    # Collect images grouped by date folder
    images_by_day: dict[str, list[Path]] = {}

    for day_dir in sorted(download_root.iterdir()):
        if not day_dir.is_dir():
            continue
        day_str = day_dir.name
        files = [
            p
            for p in sorted(day_dir.iterdir())
            if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
        ]
        if files:
            images_by_day[day_str] = files

    if not images_by_day:
        raise RuntimeError(f"No images found under {download_root}")

    # Build HTML
    title = "AutoVisuals Midjourney Gallery"
    now = datetime.datetime.now().isoformat(timespec="seconds")

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang='en'>")
    parts.append("<head>")
    parts.append(f"<meta charset='UTF-8'>")
    parts.append(f"<title>{escape(title)}</title>")
    parts.append(
        """
<style>
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #0f172a;
  color: #e5e7eb;
  margin: 0;
  padding: 1.5rem;
}
h1 {
  margin-bottom: 0.25rem;
}
h2 {
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}
p.meta {
  color: #9ca3af;
  font-size: 0.875rem;
}
.gallery-day {
  margin-bottom: 2rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}
.card {
  background: #111827;
  border-radius: 0.75rem;
  padding: 0.5rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}
.card img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 0.5rem;
}
.card span {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.75rem;
  color: #9ca3af;
  word-break: break-all;
}
</style>
"""
    )
    parts.append("</head>")
    parts.append("<body>")
    parts.append(f"<h1>{escape(title)}</h1>")
    parts.append(f"<p class='meta'>Generated at {escape(now)}</p>")

    for day, files in images_by_day.items():
        parts.append("<section class='gallery-day'>")
        parts.append(f"<h2>{escape(day)}</h2>")
        parts.append("<div class='grid'>")
        for img_path in files:
            rel = img_path.relative_to(download_root.parent if download_root.parent != Path(".") else Path("."))
            parts.append("<div class='card'>")
            parts.append(f"<img src='{escape(str(rel))}' alt='{escape(img_path.name)}' loading='lazy' />")
            parts.append(f"<span>{escape(str(rel))}</span>")
            parts.append("</div>")
        parts.append("</div>")
        parts.append("</section>")

    parts.append("</body>")
    parts.append("</html>")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    return out_path
