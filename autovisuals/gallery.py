"""
AutoVisuals gallery builder.

Scans a download root like:

    <download_root>/
        YYYY-MM-DD/
            <category>/
                *.png / *.jpg / *.jpeg / *.webp

and matches it with prompt metadata:

    <prompt_root>/
        YYYY-MM-DD/
            <category>/
                prompt.txt
                meta.json

Outputs:

  1) <out_file> (default: PROJECT_ROOT/mj_gallery.html)
  2) <out_file_parent>/mj_zoom/YYYY-MM-DD/<category>/<image-stem>.html

Main gallery thumbnails link to per-image zoom pages that show a big image
and navigation controls:

  [Prev]  [Back to Gallery]  [Next]

Zoom pages also support:

  - Keyboard ← / → arrows for prev/next
  - Mouse wheel up/down for prev/next (with debounce)
"""

from pathlib import Path
from html import escape
import datetime
import os


def _get_project_root() -> Path:
    # gallery.py is in AutoVisuals/autovisuals/
    here = Path(__file__).resolve().parent
    return here.parent


PROJECT_ROOT = _get_project_root()


def build_gallery(
    download_root: str | Path = "mj_downloads",
    prompt_root: str | Path = "prompt",
    out_file: str | Path = "mj_gallery.html",
) -> Path:
    # Resolve roots (accept absolute or relative)
    download_root = Path(download_root)
    if not download_root.is_absolute():
        download_root = PROJECT_ROOT / download_root
    download_root = download_root.resolve()

    prompt_root = Path(prompt_root)
    if not prompt_root.is_absolute():
        prompt_root = PROJECT_ROOT / prompt_root
    prompt_root = prompt_root.resolve()

    out_path = Path(out_file)
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    out_path = out_path.resolve()

    if not download_root.exists():
        raise FileNotFoundError(f"Download root not found: {download_root}")

    zoom_root = out_path.parent / "mj_zoom"
    zoom_root.mkdir(parents=True, exist_ok=True)

    title = "AutoVisuals Midjourney Gallery"
    now = datetime.datetime.now().isoformat(timespec="seconds")

    # by_date[date][category] = [image paths]
    by_date: dict[str, dict[str, list[Path]]] = {}

    # Newest dates first (by folder name)
    for day_dir in sorted(download_root.iterdir(), reverse=True):
        if not day_dir.is_dir():
            continue
        date_str = day_dir.name

        for cat_dir in sorted(day_dir.iterdir()):
            if not cat_dir.is_dir():
                continue
            slug = cat_dir.name

            # Newest images first inside each category (by mtime)
            imgs = [
                p
                for p in sorted(
                    cat_dir.iterdir(),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )
                if p.is_file()
                and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            ]
            if not imgs:
                continue
            by_date.setdefault(date_str, {})[slug] = imgs

    if not by_date:
        raise RuntimeError(f"No images found under {download_root}")

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang='en'>")
    parts.append("<head>")
    parts.append("<meta charset='UTF-8'>")
    parts.append(f"<title>{escape(title)}</title>")
    parts.append(
        """
<style>
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #020617;
  color: #e5e7eb;
  margin: 0;
  padding: 1.5rem;
}
h1 { margin-bottom: 0.25rem; }
h2 { margin-top: 2rem; margin-bottom: 0.75rem; }
h3 { margin-top: 1rem; margin-bottom: 0.35rem; }
p.meta {
  color: #9ca3af;
  font-size: 0.875rem;
}
.section-day {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #1f2937;
}
.section-theme { margin-bottom: 1.5rem; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}
.card {
  background: #020617;
  border-radius: 0.75rem;
  padding: 0.5rem;
  box-shadow: 0 8px 24px rgba(0,0,0,0.45);
  border: 1px solid #1e293b;
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
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: #0f172a;
  border: 1px solid #1d4ed8;
  font-size: 0.7rem;
  color: #bfdbfe;
  margin-left: 0.4rem;
}
.links {
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}
.links a {
  color: #60a5fa;
  text-decoration: none;
}
.links a:hover { text-decoration: underline; }
</style>
<script>
// no script needed in main gallery for now
</script>
"""
    )
    parts.append("</head>")
    parts.append("<body>")
    parts.append(f"<h1>{escape(title)}</h1>")
    parts.append(f"<p class='meta'>Generated at {escape(now)}</p>")
    parts.append(
        f"<p class='meta'>Source images root: {escape(str(download_root))}</p>"
    )

    # Newest dates first (keys are already sorted in that direction above,
    # but we'll be explicit here too).
    for date_str, categories in sorted(by_date.items(), reverse=True):
        parts.append("<section class='section-day'>")
        parts.append(f"<h2>{escape(date_str)}</h2>")

        for slug, files in sorted(categories.items()):
            cat_title = slug.replace("-", " ").title()

            cat_prompt_dir = prompt_root / date_str / slug
            prompt_path = cat_prompt_dir / "prompt.txt"
            meta_path = cat_prompt_dir / "meta.json"

            has_prompt = prompt_path.exists()
            has_meta = meta_path.exists()

            links_html = ""
            if has_prompt or has_meta:
                bits = []
                if has_prompt:
                    prompt_rel = os.path.relpath(prompt_path, start=out_path.parent)
                    bits.append(
                        f"Prompt: <a href='{escape(str(prompt_rel))}' target='_blank'>prompt.txt</a>"
                    )
                if has_meta:
                    meta_rel = os.path.relpath(meta_path, start=out_path.parent)
                    if bits:
                        bits.append("·")
                    bits.append(
                        f"<a href='{escape(str(meta_rel))}' target='_blank'>meta.json</a>"
                    )
                links_html = f"<p class='links'>{' '.join(bits)}</p>"

            parts.append("<div class='section-theme'>")
            parts.append(
                f"<h3>{escape(cat_title)}"
                f"<span class='badge'>{len(files)} image(s)</span></h3>"
            )
            if links_html:
                parts.append(links_html)

            parts.append("<div class='grid'>")

            # Navigation within each category's list of files
            for idx, img_path in enumerate(files):
                zoom_dir = zoom_root / date_str / slug
                zoom_dir.mkdir(parents=True, exist_ok=True)
                zoom_page = zoom_dir / f"{img_path.stem}.html"

                prev_path = files[idx - 1] if idx > 0 else None
                next_path = files[idx + 1] if idx < len(files) - 1 else None

                img_rel_from_zoom = os.path.relpath(img_path, start=zoom_page.parent)
                gallery_rel_from_zoom = os.path.relpath(
                    out_path, start=zoom_page.parent
                )

                prev_rel = None
                next_rel = None
                if prev_path is not None:
                    prev_zoom = zoom_dir / f"{prev_path.stem}.html"
                    prev_rel = os.path.relpath(prev_zoom, start=zoom_page.parent)
                if next_path is not None:
                    next_zoom = zoom_dir / f"{next_path.stem}.html"
                    next_rel = os.path.relpath(next_zoom, start=zoom_page.parent)

                # Build zoom page HTML (with keyboard + wheel navigation)
                zoom_html: list[str] = []
                zoom_html.append("<!DOCTYPE html>")
                zoom_html.append("<html lang='en'>")
                zoom_html.append("<head>")
                zoom_html.append("<meta charset='UTF-8'>")
                zoom_html.append(
                    f"<title>{escape(cat_title)} – {escape(img_path.name)}</title>"
                )
                zoom_html.append(
                    """
<style>
body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #020617;
  color: #e5e7eb;
  margin: 0;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.header {
  width: 100%;
  max-width: 960px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 0.5rem;
}
.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  font-size: 0.85rem;
  text-decoration: none;
  border: 1px solid #1e293b;
  background: #020617;
  color: #9ca3af;
  min-width: 80px;
  text-align: center;
}
.nav-btn:hover {
  background: #111827;
  color: #e5e7eb;
  border-color: #1d4ed8;
}
.nav-btn.disabled {
  opacity: 0.35;
  pointer-events: none;
}
.back-btn {
  border-color: #1d4ed8;
  color: #bfdbfe;
}
.zoom-wrapper {
  width: 100%;
  max-width: 1280px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.zoom-img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 0.75rem;
  box-shadow: 0 20px 40px rgba(0,0,0,0.65);
}
.filename {
  margin-top: 0.75rem;
  font-size: 0.8rem;
  color: #9ca3af;
  word-break: break-all;
}
</style>
<script>
document.addEventListener('DOMContentLoaded', function () {
  const prevLink = document.getElementById('prev-link');
  const nextLink = document.getElementById('next-link');

  function go(direction) {
    const target = direction < 0 ? prevLink : nextLink;
    if (!target) return;
    if (target.tagName !== 'A') return;
    if (target.classList.contains('disabled')) return;
    window.location.href = target.href;
  }

  // Keyboard navigation: ← / →
  window.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      go(-1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      go(1);
    }
  });

  // Mouse wheel (scroll up/down)
  let lastScroll = 0;
  window.addEventListener('wheel', function (e) {
    const now = Date.now();
    // debounce ~400ms
    if (now - lastScroll < 400) return;

    if (Math.abs(e.deltaY) < 20) return; // ignore tiny scrolls

    if (e.deltaY > 0) {
      // scroll down → next
      go(1);
    } else {
      // scroll up → prev
      go(-1);
    }
    lastScroll = now;
  }, { passive: true });
});
</script>
"""
                )
                zoom_html.append("</head>")
                zoom_html.append("<body>")
                zoom_html.append("<div class='header'>")

                # Prev button
                if prev_rel:
                    zoom_html.append(
                        f"<a id='prev-link' class='nav-btn' href='{escape(prev_rel)}'>&larr; Prev</a>"
                    )
                else:
                    zoom_html.append(
                        "<span id='prev-link' class='nav-btn disabled'>&larr; Prev</span>"
                    )

                # Back to gallery
                zoom_html.append(
                    f"<a class='nav-btn back-btn' href='{escape(gallery_rel_from_zoom)}'>Back to Gallery</a>"
                )

                # Next button
                if next_rel:
                    zoom_html.append(
                        f"<a id='next-link' class='nav-btn' href='{escape(next_rel)}'>Next &rarr;</a>"
                    )
                else:
                    zoom_html.append(
                        "<span id='next-link' class='nav-btn disabled'>Next &rarr;</span>"
                    )

                zoom_html.append("</div>")  # header

                zoom_html.append("<div class='zoom-wrapper'>")
                zoom_html.append(
                    f"<img class='zoom-img' src='{escape(img_rel_from_zoom)}' "
                    f"alt='{escape(img_path.name)}' />"
                )
                zoom_html.append(f"<div class='filename'>{escape(img_path.name)}</div>")
                zoom_html.append("</div>")
                zoom_html.append("</body></html>")

                zoom_page.write_text("\n".join(zoom_html), encoding="utf-8")

                # In main gallery: thumbnail → zoom page
                zoom_rel_from_gallery = os.path.relpath(
                    zoom_page, start=out_path.parent
                )
                img_rel_from_gallery = os.path.relpath(
                    img_path, start=out_path.parent
                )

                thumb_img = (
                    f"<img src='{escape(img_rel_from_gallery)}' "
                    f"alt='{escape(img_path.name)}' loading='lazy' />"
                )
                thumb_html = (
                    f"<a href='{escape(zoom_rel_from_gallery)}' "
                    f"target='_blank'>{thumb_img}</a>"
                )

                parts.append("<div class='card'>")
                parts.append(thumb_html)
                parts.append(
                    f"<span>{escape(str(img_path.relative_to(out_path.parent)))}</span>"
                )
                parts.append("</div>")

            parts.append("</div>")  # .grid
            parts.append("</div>")  # .section-theme

        parts.append("</section>")

    parts.append("</body></html>")

    out_path.write_text("\n".join(parts), encoding="utf-8")
    return out_path
