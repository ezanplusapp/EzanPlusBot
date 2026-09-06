import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
FONTLAR = KOK_DIZIN / "assets" / "fonts"
IKONLAR = KOK_DIZIN / "assets" / "icons"
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

def create_paper_background(w: int, h: int, center_rgb: tuple, outer_rgb: tuple) -> Image.Image:
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h * 0.45
    dist = np.sqrt(((x - cx) / (w * 0.72)) ** 2 + ((y - cy) / (h * 0.72)) ** 2)
    dist = np.clip(dist, 0, 1.2)
    
    cr, cg, cb = center_rgb
    or_, og, ob = outer_rgb
    
    r = (cr - dist * (cr - or_)).astype(np.uint8)
    g = (cg - dist * (cg - og)).astype(np.uint8)
    b = (cb - dist * (cb - ob)).astype(np.uint8)
    
    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr)

def draw_seal_custom(size: int, color_hex: str = "#FFFFFF") -> Image.Image:
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
    
    r_out = s * 0.47
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=c_rgb + (220,), width=int(2.0 * scale))
    
    r_mid = s * 0.43
    d.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], outline=c_rgb + (110,), width=int(1.0 * scale))
    
    r_dots = s * 0.39
    for deg in range(0, 360, 15):
        rad = math.radians(deg)
        px = cx + r_dots * math.cos(rad)
        py = cy + r_dots * math.sin(rad)
        d.ellipse([px - 2.2 * scale, py - 2.2 * scale, px + 2.2 * scale, py + 2.2 * scale], fill=c_rgb + (200,))
        
    r_in = s * 0.34
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=c_rgb + (150,), width=int(1.2 * scale))
    
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

PALETLER = {
    # 1. Kadife Yakut / Soft Velvet Crimson (Net kırmızı ama gözü yormayan yumuşak kadife doku)
    "kadife_kirmizi": {
        "ad": "Kadife Kırmızı (Soft Crimson)",
        "center": (180, 42, 48),     # #B42A30
        "outer": (138, 22, 28),      # #8A161C
        "divider": "#D65259"
    },
    # 2. Ezan Plus Soft Marka Kırmızısı (Marka kırmızısının soft mat hali)
    "ezan_soft_kirmizi": {
        "ad": "Ezan Plus Soft Kırmızı",
        "center": (168, 32, 38),     # #A82026
        "outer": (126, 16, 22),      # #7E1016
        "divider": "#C44147"
    },
    # 3. Soft Nar Kırmızısı (Daha aydınlık, pudramsı kırmızı)
    "soft_nar_kirmizi": {
        "ad": "Soft Nar Kırmızısı (Pastel Rouge)",
        "center": (192, 54, 60),     # #C0363C
        "outer": (148, 28, 34),      # #941C22
        "divider": "#E26269"
    },
    # 4. Sıcak Karmin Kırmızı (Hafif sıcaklık barındıran zengin kırmızı)
    "sicak_karmin": {
        "ad": "Sıcak Karmin Kırmızı (Warm Carmine)",
        "center": (178, 48, 44),     # #B2302C
        "outer": (136, 26, 24),      # #881A18
        "divider": "#D45852"
    }
}

def ciz_kirmizi_soft(
    palet_key: str,
    format_tipi: str = "9:16",
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    dosya_adi: str = "output.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    palet = PALETLER[palet_key]
    center_rgb = palet["center"]
    outer_rgb = palet["outer"]
    c_divider = palet["divider"]

    C_HERO = "#FFFFFF"
    C_ARABIC = "#FFF8EE"
    C_ACCENT = "#FDE6BA"         # Soft satin champagne gold
    C_BODY = "#FFFDF9"
    C_QUOTE = "#FDE6BA"
    C_ITALIC = "#FFF8ED"
    C_REF = "#FDE6BA"
    C_SEAL = "#FDE6BA"
    C_BRAND = "#FFFFFF"

    im = create_paper_background(w, h, center_rgb, outer_rgb)
    draw = ImageDraw.Draw(im)

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

    body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    body_block_h = len(body_lines) * lh_body

    clean_alinti = alinti_metin.strip("“”\" ")
    italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 30, draw)
    italic_block_h = len(italic_lines) * lh_italic

    ref_txt = ayet_ref.upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]

    if is_916:
        y_tag = 210
        cur_y = 295
    else:
        y_tag = 135
        cur_y = 195

    # 1. Tag
    tag_txt = "KUR'AN SÖZLÜĞÜ  •  KAVRAM VE HİKMET".upper()
    tag_bb = draw.textbbox((0, 0), tag_txt, font=f_tag)
    tag_w = tag_bb[2] - tag_bb[0]
    draw.text(((w - tag_w) / 2, y_tag), tag_txt, font=f_tag, fill=C_ACCENT)

    # 2. Turkish Hero
    draw.text(((w - lw) / 2, cur_y), latin_txt, font=f_latin, fill=C_HERO)
    cur_y += lh + gap_between

    # 3. Arabic Hero
    draw.text(((w - ar_w) / 2, cur_y), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
    
    # 4. Origin line (Kasra safe area)
    cur_y += ar_bb[3] + gap_origin
    draw.text(((w - ow) / 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += oh + (40 if is_916 else 28)

    # 5. Fine Divider
    div_w = 420 if is_916 else 360
    div_x1 = (w - div_w) / 2
    div_x2 = div_x1 + div_w
    draw.line([(div_x1, cur_y), (div_x2, cur_y)], fill=c_divider, width=1)
    # Gold diamond/dot in middle
    dot_r = 3.5 if is_916 else 3
    draw.ellipse([(w/2 - dot_r, cur_y - dot_r), (w/2 + dot_r, cur_y + dot_r)], fill=C_ACCENT)
    cur_y += (42 if is_916 else 30)

    # 6. Body Definition
    for line in body_lines:
        bb = draw.textbbox((0, 0), line, font=f_body)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += (36 if is_916 else 24)

    # 7. Quote Block
    for line in italic_lines:
        bb = draw.textbbox((0, 0), line, font=f_italic)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += (18 if is_916 else 14)

    # 8. Ayet Ref
    draw.text(((w - rw) / 2, cur_y), ref_txt, font=f_ref, fill=C_REF)

    # 9. Bottom Branding & Seal
    seal_size = 68 if is_916 else 54
    seal_img = draw_seal_custom(seal_size, color_hex=C_SEAL)
    
    if is_916:
        seal_y = 1640
        brand_y = seal_y + seal_size + 14
    else:
        seal_y = 1170
        brand_y = seal_y + seal_size + 10

    if seal_img:
        im.paste(seal_img, (int((w - seal_size) / 2), seal_y), seal_img)

    brand_txt = "ezan plus"
    b_bb = draw.textbbox((0, 0), brand_txt, font=f_brand)
    draw.text(((w - (b_bb[2] - b_bb[0])) / 2, brand_y), brand_txt, font=f_brand, fill=C_BRAND)

    # Save
    out_path = ARTIFACTS / dosya_adi
    im.save(out_path, "PNG")
    print(f"Rendered: {out_path.name}")
    return out_path

if __name__ == "__main__":
    for key in PALETLER:
        ciz_kirmizi_soft(key, format_tipi="9:16", dosya_adi=f"{key}_9_16.png")
        ciz_kirmizi_soft(key, format_tipi="4:5", dosya_adi=f"{key}_4_5.png")
    print("ALL_DONE")
