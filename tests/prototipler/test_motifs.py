import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
FONTLAR = KOK_DIZIN / "assets" / "fonts"
IKONLAR = KOK_DIZIN / "assets" / "icons"
CIKTI = KOK_DIZIN / "data" / "cikti"
CIKTI.mkdir(parents=True, exist_ok=True)

_reshaper = arabic_reshaper.ArabicReshaper({"delete_harakat": False, "support_ligatures": True})
def ar_prep(text: str) -> str:
    return get_display(_reshaper.reshape(text))

def font_al(name: str, size: int, weight: int = 400):
    p = FONTLAR / name
    f = ImageFont.truetype(str(p), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

def metin_satirla(text: str, font, max_w: int, draw: ImageDraw.ImageDraw):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        cand = " ".join(cur + [w])
        bb = draw.textbbox((0, 0), cand, font=font)
        if (bb[2] - bb[0]) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def create_subtle_paper_background(w: int, h: int) -> Image.Image:
    """Creates a warm, luxurious parchment background with gentle studio vignette."""
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h * 0.45
    dist = np.sqrt(((x - cx) / (w * 0.70)) ** 2 + ((y - cy) / (h * 0.70)) ** 2)
    dist = np.clip(dist, 0, 1.2)
    
    # Outer vignette color: #ECE0D1 (236, 224, 209)
    # Center color: #FBF6EE (251, 246, 238)
    r = (251 - dist * 15).astype(np.uint8)
    g = (246 - dist * 22).astype(np.uint8)
    b = (238 - dist * 29).astype(np.uint8)
    
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr)

def draw_seljuk_star(size: int, color_rgb: tuple = (140, 74, 47), line_width: int = 2) -> Image.Image:
    """Draws an ultra-crisp 8-pointed Islamic/Seljuk geometric star motif with high-res supersampling."""
    scale = 4
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    cx, cy = s / 2, s / 2
    r_outer = s * 0.46
    r_inner = s * 0.28
    
    points = []
    for i in range(16):
        angle = i * (math.pi / 8) - (math.pi / 2)
        r = r_outer if (i % 2 == 0) else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    
    d.polygon(points, outline=color_rgb + (220,), width=line_width * scale)
    
    r_c = s * 0.14
    d.ellipse([cx - r_c, cy - r_c, cx + r_c, cy + r_c], outline=color_rgb + (180,), width=line_width * scale)
    r_d = s * 0.04
    d.ellipse([cx - r_d, cy - r_d, cx + r_d, cy + r_d], fill=color_rgb + (220,))
    
    return im.resize((size, size), Image.Resampling.LANCZOS)

def draw_praying_hands_seal(size: int, color_hex: str = "#8C4A2F") -> Image.Image:
    """Extracts praying hands from logo.png and embeds into an elegant publishing seal."""
    logo_path = IKONLAR / "logo.png"
    if not logo_path.exists():
        return None
    
    logo_raw = Image.open(logo_path).convert("RGBA")
    scale = 4
    s = size * scale
    seal = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(seal)
    
    c_rgb = tuple(int(color_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    cx, cy = s / 2, s / 2
    
    # Outer thin ring
    r_ring = s * 0.46
    d.ellipse([cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring], outline=c_rgb + (190,), width=int(1.8 * scale))
    
    # Inner delicate dotted ring
    r_dots = s * 0.40
    for a_deg in range(0, 360, 15):
        rad = math.radians(a_deg)
        px = cx + r_dots * math.cos(rad)
        py = cy + r_dots * math.sin(rad)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=c_rgb + (160,))
    
    # Extract white hands from logo
    arr = np.array(logo_raw)
    white_mask = (arr[:, :, 0] > 180) & (arr[:, :, 1] > 180) & (arr[:, :, 2] > 180)
    
    hands_rgba = np.zeros_like(arr)
    hands_rgba[white_mask, 0] = c_rgb[0]
    hands_rgba[white_mask, 1] = c_rgb[1]
    hands_rgba[white_mask, 2] = c_rgb[2]
    hands_rgba[white_mask, 3] = 255
    
    hands_img = Image.fromarray(hands_rgba)
    bbox = hands_img.getbbox()
    if bbox:
        hands_crop = hands_img.crop(bbox)
        target_h = int(s * 0.44)
        target_w = int(target_h * (hands_crop.width / hands_crop.height))
        hands_resized = hands_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
        seal.paste(hands_resized, (int(cx - target_w / 2), int(cy - target_h / 2)), hands_resized)
        
    return seal.resize((size, size), Image.Resampling.LANCZOS)

def draw_delicate_crescent_star(size: int, color_hex: str = "#8C4A2F") -> Image.Image:
    """Draws a delicate Islamic crescent and 8-point star motif."""
    scale = 4
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c_rgb = tuple(int(color_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    
    cx, cy = s / 2, s / 2
    r_outer = s * 0.38
    r_inner = s * 0.30
    
    # Outer circle
    # Crescent drawn by outer circle minus inner shifted circle
    cresc = Image.new("L", (s, s), 0)
    cd = ImageDraw.Draw(cresc)
    cd.ellipse([cx - r_outer - s*0.08, cy - r_outer, cx + r_outer - s*0.08, cy + r_outer], fill=255)
    cd.ellipse([cx - r_inner + s*0.03, cy - r_inner, cx + r_inner + s*0.03, cy + r_inner], fill=0)
    
    cresc_col = Image.new("RGBA", (s, s), c_rgb + (220,))
    im.paste(cresc_col, (0, 0), cresc)
    
    # Small 8-point star inside crescent opening
    star_cx = cx + s * 0.16
    star_cy = cy
    star_r_out = s * 0.12
    star_r_in = s * 0.06
    s_pts = []
    for i in range(16):
        angle = i * (math.pi / 8)
        r = star_r_out if (i % 2 == 0) else star_r_in
        s_pts.append((star_cx + r * math.cos(angle), star_cy + r * math.sin(angle)))
    d.polygon(s_pts, fill=c_rgb + (220,))
    
    return im.resize((size, size), Image.Resampling.LANCZOS)

print("Test motifs module ready.")
