import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
FONTLAR = KOK_DIZIN / "assets" / "fonts"
IKONLAR = KOK_DIZIN / "assets" / "icons"
CIKTI = KOK_DIZIN / "data" / "cikti"
ARTIFACTS = Path("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93")

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

def create_crimson_paper_background(w: int, h: int, center_rgb: tuple, outer_rgb: tuple) -> Image.Image:
    """Creates a velvety matte pastel crimson background with subtle studio vignette."""
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h * 0.45
    dist = np.sqrt(((x - cx) / (w * 0.72)) ** 2 + ((y - cy) / (h * 0.72)) ** 2)
    dist = np.clip(dist, 0, 1.2)
    
    # Linear interpolation between center and outer
    cr, cg, cb = center_rgb
    or_, og, ob = outer_rgb
    
    r = (cr - dist * (cr - or_)).astype(np.uint8)
    g = (cg - dist * (cg - og)).astype(np.uint8)
    b = (cb - dist * (cb - ob)).astype(np.uint8)
    
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr)

def draw_ezanplus_gold_seal(size: int, color_hex: str = "#E8C88A") -> Image.Image:
    """Extracts praying hands from logo.png and renders in fine gold/ivory for dark crimson backgrounds."""
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
    
    # Outer solid thin ring
    r_out = s * 0.47
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=c_rgb + (220,), width=int(2.0 * scale))
    
    # Middle delicate ring
    r_mid = s * 0.43
    d.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], outline=c_rgb + (110,), width=int(1.0 * scale))
    
    # 24 decorative border dots
    r_dots = s * 0.39
    for deg in range(0, 360, 15):
        rad = math.radians(deg)
        px = cx + r_dots * math.cos(rad)
        py = cy + r_dots * math.sin(rad)
        d.ellipse([px - 2.2 * scale, py - 2.2 * scale, px + 2.2 * scale, py + 2.2 * scale], fill=c_rgb + (200,))
        
    # Inner border
    r_in = s * 0.34
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=c_rgb + (150,), width=int(1.2 * scale))
    
    # Extract white praying hands
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
        target_h = int(s * 0.38)
        target_w = int(target_h * (hands_crop.width / hands_crop.height))
        hands_resized = hands_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
        seal.paste(hands_resized, (int(cx - target_w / 2), int(cy - target_h / 2)), hands_resized)
        
    return seal.resize((size, size), Image.Resampling.LANCZOS)

def draw_gold_seljuk_star(size: int, color_hex: str = "#E8C88A") -> Image.Image:
    """Intricate Seljuk 8-point geometric star rosette in warm gold."""
    scale = 4
    s = size * scale
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c_rgb = tuple(int(color_hex.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    
    cx, cy = s / 2, s / 2
    r_out = s * 0.46
    r_in = s * 0.28
    
    pts = []
    for i in range(16):
        ang = i * (math.pi / 8) - (math.pi / 2)
        r = r_out if (i % 2 == 0) else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    
    d.polygon(pts, outline=c_rgb + (230,), width=int(2.2 * scale))
    
    pts_inner = []
    for i in range(16):
        ang = i * (math.pi / 8) - (math.pi / 2)
        r = (r_out * 0.85) if (i % 2 == 0) else (r_in * 0.85)
        pts_inner.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts_inner, outline=c_rgb + (140,), width=int(1.0 * scale))
    
    r_c = s * 0.16
    d.ellipse([cx - r_c, cy - r_c, cx + r_c, cy + r_c], outline=c_rgb + (200,), width=int(1.8 * scale))
    
    r_d = s * 0.05
    d.ellipse([cx - r_d, cy - r_d, cx + r_d, cy + r_d], fill=c_rgb + (230,))
    
    return im.resize((size, size), Image.Resampling.LANCZOS)

def ciz_kizil_kuran_sozlugu(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    color_theme: str = "pastel_bordo", # "pastel_bordo", "gul_kurusu", "kiremit_bordo"
    arabic_first: bool = False,
    motif_type: str = "seal", # "seal", "seljuk", "minimal"
    dosya_adi: str = "kizil_kelime.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # Define color themes (Background Center & Outer vignette)
    if color_theme == "pastel_bordo":
        # Velvet Pastel Crimson (App red tone, refined & velvety)
        center_rgb = (118, 38, 44)   # #76262C
        outer_rgb = (88, 24, 29)     # #58181D
    elif color_theme == "gul_kurusu":
        # Dusty Rose / Soft Muted Crimson Pastel
        center_rgb = (135, 52, 58)   # #87343A
        outer_rgb = (102, 33, 38)    # #662126
    else: # kiremit_bordo
        # Warm Terracotta Crimson Pastel
        center_rgb = (128, 48, 42)   # #80302A
        outer_rgb = (96, 31, 26)     # #601F1A

    im = create_crimson_paper_background(w, h, center_rgb, outer_rgb)
    draw = ImageDraw.Draw(im)

    # Inverted Typography Palette (Luminous Ivories, Warm Golds & Champagne)
    C_HERO = "#FFFDF9"        # Pure luminous warm ivory
    C_ARABIC = "#FFF9ED"      # Radiant antique gold-ivory
    C_GOLD = "#E8C88A"        # Warm soft satin gold (accent)
    C_GOLD_DIM = "#D2AA68"    # Subtle champagne gold
    C_DIVIDER = "#9E555A"     # Soft muted crimson line
    C_DIVIDER_GLOW = "#E8C88A"# Center gold dot
    C_BODY = "#FDF4E7"        # Soft cream body text
    C_QUOTE = "#E8C88A"       # Warm gold quotation mark
    C_ITALIC = "#F7ECD9"      # Luminous italic reflection
    C_REF = "#E8C88A"         # Delicate gold citation
    C_BRAND = "#FFFDF9"       # Pure ivory brand signature

    # Font Sizes (Büyük Hero Kelime Standartları)
    if is_916:
        pt_tag = 16
        pt_latin = 126
        pt_arabic = 150
        pt_origin = 27
        pt_body = 40
        lh_body = 64
        pt_quote = 66
        pt_italic = 33
        lh_italic = 52
        pt_ref = 18
        pt_brand = 25
        max_text_w = 850
    else: # 4:5
        pt_tag = 14
        pt_latin = 102
        pt_arabic = 124
        pt_origin = 22
        pt_body = 33
        lh_body = 52
        pt_quote = 54
        pt_italic = 27
        lh_italic = 42
        pt_ref = 16
        pt_brand = 21
        max_text_w = 810

    f_tag = font_al("Manrope.ttf", pt_tag, 600)
    f_latin = font_al("Lora.ttf", pt_latin, 700)
    f_arabic = font_al("amiri-700-arabic.ttf", pt_arabic)
    f_origin = font_al("Lora.ttf", pt_origin, 400)
    f_body = font_al("Lora.ttf", pt_body, 500)
    f_quote = font_al("Lora.ttf", pt_quote, 700)
    f_italic = font_al("Lora.ttf", pt_italic, 400)
    f_ref = font_al("Manrope.ttf", pt_ref, 700)
    f_brand = font_al("Lora.ttf", pt_brand, 600)

    # Content
    ar_prep_txt = ar_prep(kelime_ar)
    ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
    ar_w = ar_bb[2] - ar_bb[0]

    latin_txt = kelime_tr
    l_bb = draw.textbbox((0, 0), latin_txt, font=f_latin)
    lw = l_bb[2] - l_bb[0]
    lh = l_bb[3] - l_bb[1]

    origin_txt = f"Arapça: {okunus}   •   Kök: {kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    oh = o_bb[3] - o_bb[1]

    gap_between = 24 if is_916 else 18
    gap_origin = 44 if is_916 else 32
    div_h = 24 if is_916 else 18

    body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    body_block_h = len(body_lines) * lh_body

    q_txt = "“"
    q_bb = draw.textbbox((0, 0), q_txt, font=f_quote)
    qh = q_bb[3] - q_bb[1]

    clean_alinti = alinti_metin.strip("“”\" ")
    italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 30, draw)
    italic_block_h = len(italic_lines) * lh_italic

    ref_txt = ayet_ref.upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    # Motif
    motif_img = None
    target_mh = 0
    target_mw = 0
    if motif_type == "seal":
        s_sz = 88 if is_916 else 66
        motif_img = draw_ezanplus_gold_seal(s_sz, color_hex="#E8C88A")
        target_mh, target_mw = s_sz, s_sz
    elif motif_type == "seljuk":
        s_sz = 82 if is_916 else 62
        motif_img = draw_gold_seljuk_star(s_sz, color_hex="#E8C88A")
        target_mh, target_mw = s_sz, s_sz
    else: # minimal
        target_mh = 14
        target_mw = 80

    brand_h = 32 if is_916 else 24
    hero_block_h = lh + gap_between + ar_bb[3] + gap_origin + oh
    quote_block_h = qh + 8 + italic_block_h + 14 + rh

    y_safe_top = 135 if is_916 else 65
    y_safe_bottom = h - (105 if is_916 else 52)
    avail_h = y_safe_bottom - y_safe_top

    total_fixed_h = 30 + hero_block_h + div_h + body_block_h + quote_block_h + target_mh + brand_h
    free_h = max(20, avail_h - total_fixed_h)

    p1 = int(free_h * (0.08 if is_916 else 0.07))
    p2 = int(free_h * (0.16 if is_916 else 0.14))
    p3 = int(free_h * (0.16 if is_916 else 0.14))
    p4 = int(free_h * (0.18 if is_916 else 0.16))
    p5 = int(free_h * (0.28 if is_916 else 0.34))
    p6 = int(free_h * (0.14 if is_916 else 0.15))

    # 1. Top Header Tag
    tag_y = y_safe_top + p1
    tag_str = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_str, font=f_tag)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, tag_y), tag_str, font=f_tag, fill=C_GOLD)

    cur_y = tag_y + (54 if is_916 else 40)

    # 2. Hero Word
    if arabic_first:
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_between
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_HERO)
        cur_y += lh + gap_origin
    else:
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_HERO)
        cur_y += lh + gap_between
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_origin

    # 3. Origin
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_GOLD)
    cur_y += oh + p2

    # 4. Divider Line
    div_w = 200
    draw.line([(w // 2 - div_w // 2, cur_y), (w // 2 + div_w // 2, cur_y)], fill=C_DIVIDER, width=1)
    dot_r = 4
    draw.ellipse([w // 2 - dot_r, cur_y - dot_r, w // 2 + dot_r, cur_y + dot_r], fill=C_DIVIDER_GLOW)
    cur_y += p3

    # 5. Definition
    for bl in body_lines:
        b_bb = draw.textbbox((0, 0), bl, font=f_body)
        bw = b_bb[2] - b_bb[0]
        draw.text(((w - bw) // 2, cur_y), bl, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += p4

    # 6. Quote Mark
    draw.text(((w - (q_bb[2] - q_bb[0])) // 2, cur_y), q_txt, font=f_quote, fill=C_QUOTE)
    cur_y += qh + (10 if is_916 else 6)

    # 7. Reflection
    for il in italic_lines:
        i_bb = draw.textbbox((0, 0), il, font=f_italic)
        iw = i_bb[2] - i_bb[0]
        draw.text(((w - iw) // 2, cur_y), il, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += (14 if is_916 else 10)

    # 8. Ayet Ref
    draw.text(((w - rw) // 2, cur_y), ref_txt, font=f_ref, fill=C_REF)
    cur_y += rh + p5

    # 9. Motif
    if motif_img:
        im.paste(motif_img, ((w - target_mw) // 2, cur_y), motif_img)
        cur_y += target_mh + p6
    else:
        orn_y = cur_y + (10 if is_916 else 6)
        draw.line([(w // 2 - 40, orn_y), (w // 2 + 40, orn_y)], fill=C_DIVIDER, width=1)
        draw.ellipse([w // 2 - 3, orn_y - 3, w // 2 + 3, orn_y + 3], fill=C_GOLD)
        cur_y = orn_y + (28 if is_916 else 18)

    # 10. Brand
    brand_str = "ezan plus"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, cur_y), brand_str, font=f_brand, fill=C_BRAND)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    
    art_p = ARTIFACTS / dosya_adi
    im.save(str(art_p), quality=96)
    print(f"Saved: {out_p} and {art_p}")
    return out_p

if __name__ == "__main__":
    # Theme 1: Pastel Bordo (Velvety App Crimson Tone) - Türkçe Başta
    ciz_kizil_kuran_sozlugu(color_theme="pastel_bordo", arabic_first=False, format_tipi="9:16", dosya_adi="bordo_pastel_turkce_basta_9_16.png")
    ciz_kizil_kuran_sozlugu(color_theme="pastel_bordo", arabic_first=False, format_tipi="4:5", dosya_adi="bordo_pastel_turkce_basta_4_5.png")

    # Theme 1: Pastel Bordo - Arapça Başta
    ciz_kizil_kuran_sozlugu(color_theme="pastel_bordo", arabic_first=True, format_tipi="9:16", dosya_adi="bordo_pastel_arapca_basta_9_16.png")
    ciz_kizil_kuran_sozlugu(color_theme="pastel_bordo", arabic_first=True, format_tipi="4:5", dosya_adi="bordo_pastel_arapca_basta_4_5.png")

    # Theme 2: Gül Kurusu / Pudra Bordo (Softer Muted Crimson Pastel)
    ciz_kizil_kuran_sozlugu(color_theme="gul_kurusu", arabic_first=False, format_tipi="9:16", dosya_adi="gul_kurusu_turkce_basta_9_16.png")
    ciz_kizil_kuran_sozlugu(color_theme="gul_kurusu", arabic_first=False, format_tipi="4:5", dosya_adi="gul_kurusu_turkce_basta_4_5.png")

    # Theme 3: Kiremit Bordo (Warm Earthy Crimson Pastel)
    ciz_kizil_kuran_sozlugu(color_theme="kiremit_bordo", arabic_first=False, format_tipi="9:16", dosya_adi="kiremit_bordo_turkce_basta_9_16.png")
    ciz_kizil_kuran_sozlugu(color_theme="kiremit_bordo", arabic_first=False, format_tipi="4:5", dosya_adi="kiremit_bordo_turkce_basta_4_5.png")
