"""Build smaller card images without changing article originals."""
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT = ASSETS / "card-thumbnails"
manifest = {}
for source in sorted(ASSETS.rglob("*")):
    if not source.is_file() or OUTPUT in source.parents or source.suffix.lower() not in {".webp", ".jpg", ".jpeg", ".png"}:
        continue
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.width < 400:
            continue
        variants = {}
        for width in (400, 640, 960):
            if width > image.width:
                continue
            relative = source.relative_to(ASSETS)
            target = OUTPUT / relative.parent / (relative.name + "-" + str(width) + ".webp")
            target.parent.mkdir(parents=True, exist_ok=True)
            resized = image.resize((width, max(1, round(image.height * width / image.width))), Image.Resampling.LANCZOS)
            resized.save(target, "WEBP", quality=76, method=6)
            variants[str(width)] = "/" + target.relative_to(ROOT).as_posix()
        manifest["/" + source.relative_to(ROOT).as_posix()] = variants
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "manifest.json").write_text(json.dumps(manifest, separators=(",", ":")) + "\n")
print("Built card thumbnails for", len(manifest), "images")
