from pathlib import Path
import base64
import json
import re
import xml.etree.ElementTree as ET
from io import BytesIO

from PIL import Image
import cairosvg

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "brand-assets/catalog/brand-catalog.json"
catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
brands = [b for b in catalog.get("brands", []) if b.get("asset_status") == "available" and b.get("logo_path")]
failures = []
print(f"Auditing {len(brands)} catalogued logo assets...")

for brand in brands:
    logo = (CATALOG_PATH.parent / brand["logo_path"]).resolve()
    try:
        if not logo.is_file():
            raise ValueError(f"file missing: {logo}")
        raw = logo.read_bytes()
        if len(raw) < 100:
            raise ValueError(f"file too small: {len(raw)} bytes")
        root = ET.fromstring(raw)
        if root.tag.split("}")[-1].lower() != "svg":
            raise ValueError("root element is not SVG")

        for element in root.iter():
            for key, value in element.attrib.items():
                if key.split("}")[-1] in ("href", "src"):
                    v = value.strip()
                    if v.startswith(("http://", "https://", "//")):
                        raise ValueError(f"external image/resource reference: {v[:100]}")
                    if v.startswith("data:image/"):
                        header, payload = v.split(",", 1)
                        if ";base64" not in header:
                            raise ValueError("embedded image is not base64 encoded")
                        decoded = base64.b64decode(payload, validate=True)
                        if not decoded:
                            raise ValueError("embedded image is empty")
        png = cairosvg.svg2png(bytestring=raw, output_width=256, output_height=256)
        image = Image.open(BytesIO(png)).convert("RGBA")
        alpha = image.getchannel("A")
        if alpha.getbbox() is None:
            raise ValueError("SVG renders fully transparent/blank")
        print(f"OK  {brand['id']}: {logo.name} ({len(raw)} bytes)")
    except Exception as exc:
        failures.append((brand["id"], str(exc)))
        print(f"FAIL {brand['id']}: {exc}")

print(f"Logo audit: {len(brands) - len(failures)}/{len(brands)} passed.")
if failures:
    raise SystemExit("Logo audit failed: " + "; ".join(f"{name}: {reason}" for name, reason in failures))
