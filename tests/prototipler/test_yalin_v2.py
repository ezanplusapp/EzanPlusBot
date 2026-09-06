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

# Create seamless transparent book motif
def get_seamless_book_motif(bg_color_rgb):
    motif_path = Path("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/antique_books_motif_1788650839341.jpg")
    if not motif_path.exists():
        return None
    bm = Image.open(motif_path).convert("RGBA")
    # Crop books area: x: 100 to 920, y: 220 to 880
    bm_crop = bm.crop((100, 220, 924, 880))
    w_c, h_c = bm_crop.size

    # Seamless background color blending
    # Original image background near edges is roughly (237, 229, 219)
    np_crop = np.array(bm_crop).astype(float)
    # Target background
    tgt_r, tgt_g, tgt_b = bg_color_rgb

    # Radial gradient alpha mask from center of books
    cx, cy = w_c / 2.0, h_c * 0.55
    rx, ry = w_c * 0.44, h_c * 0.42

    y_idx, x_idx = np.ogrid[:h_c, :w_c]
    dist = np.sqrt(((x_idx - cx) / rx) ** 2 + ((y_idx - cy) / ry) ** 2)
    # Inside 0.7: alpha = 1.0; between 0.7 and 1.0: fade to 0.0
    alpha = np.clip((1.0 - dist) / 0.32, 0.0, 1.0)
    # Also tint the edge colors towards the target background
    edge_blend = np.clip((dist - 0.5) / 0.5, 0.0, 1.0)
    for c_i, tgt in enumerate([tgt_r, tgt_g, tgt_b]):
        np_crop[:, :, c_i] = np_crop[:, :, c_i] * (1.0 - edge_blend * 0.75) + tgt * (edge_blend * 0.75)

    np_crop[:, :, 3] = np_crop[:, :, 3] * alpha
    result = Image.fromarray(np_crop.astype(np.uint8), mode="RGBA")
    return result

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

def ciz_kusursuz_yalin_kart(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    variation: str = "A", # "A" = Latin first, "B" = Arabic first, "C" = Pure Zen Framed
    dosya_adi: str = "perfect_yalin.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # Pure warm antique book parchment background (exactly matching literary aesthetics)
    BG_RGB = (245, 237, 226) # #F5EDE2
    im = Image.new("RGB", (w, h), BG_RGB)
    draw = ImageDraw.Draw(im)

    # Palette
    C_TITLE = "#362214"      # Deep antique espresso
    C_ARABIC = "#26160C"     # Rich dark calligraphy ink
    C_ACCENT = "#8C4A2F"     # Warm terracotta
    C_DIVIDER = "#D7C2AB"    # Soft antique line
    C_BODY = "#2E241E"       # Deep warm charcoal
    C_QUOTE = "#A65B36"      # Terracotta quotation
    C_ITALIC = "#3E3027"     # Poetic dark espresso
    C_REF = "#8C4A2F"        # Refined terracotta citation

    # Font Sizes
    if is_916:
        pt_tag = 16
        pt_latin = 82
        pt_arabic = 114
        pt_origin = 26
        pt_body = 38
        lh_body = 62
        pt_quote = 66
        pt_italic = 32
        lh_italic = 50
        pt_ref = 18
        pt_brand = 24
        max_text_w = 830
    else:
        pt_tag = 14
        pt_latin = 68
        pt_arabic = 96
        pt_origin = 22
        pt_body = 32
        lh_body = 50
        pt_quote = 52
        pt_italic = 26
        lh_italic = 40
        pt_ref = 16
        pt_brand = 20
        max_text_w = 800

    f_tag = font_al("Manrope.ttf", pt_tag, 600)
    f_latin = font_al("Lora.ttf", pt_latin, 700)
    f_arabic = font_al("amiri-700-arabic.ttf", pt_arabic)
    f_origin = font_al("Lora.ttf", pt_origin, 400)
    f_body = font_al("Lora.ttf", pt_body, 500)
    f_quote = font_al("Lora.ttf", pt_quote, 700)
    f_italic = font_al("Lora.ttf", pt_italic, 400)
    f_ref = font_al("Manrope.ttf", pt_ref, 700)
    f_brand = font_al("Lora.ttf", pt_brand, 600)

    # Optional delicate inner frame for variation C
    if variation == "C":
        frame_pad = 48 if is_916 else 36
        draw.rectangle([frame_pad, frame_pad, w - frame_pad, h - frame_pad], outline="#E2CDB6", width=1)
        # 4 subtle corner squares
        cs = 8
        for cx, cy in [
            (frame_pad, frame_pad),
            (w - frame_pad, frame_pad),
            (frame_pad, h - frame_pad),
            (w - frame_pad, h - frame_pad)
        ]:
            draw.rectangle([cx - cs//2, cy - cs//2, cx + cs//2, cy + cs//2], fill="#C29B38")

    # Content Measurement for Dynamic Vertical Flex
    # 1. Title + Arabic + Origin
    ar_prep_txt = ar_prep(kelime_ar)
    ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
    ar_w = ar_bb[2] - ar_bb[0]
    ar_h = ar_bb[3] - ar_bb[1]

    latin_txt = kelime_tr.lower() if variation == "A" else kelime_tr
    l_bb = draw.textbbox((0, 0), latin_txt, font=f_latin)
    lw = l_bb[2] - l_bb[0]
    lh = l_bb[3] - l_bb[1]

    origin_txt = f"Arapça: {okunus}   •   Kök: {kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    oh = o_bb[3] - o_bb[1]

    # Safe areas
    gap_between_ar_latin = 22 if is_916 else 16
    gap_ar_to_origin = 36 if is_916 else 26

    # 2. Divider
    div_h = 24 if is_916 else 18

    # 3. Body text
    body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    body_block_h = len(body_lines) * lh_body

    # 4. Quote + Italic + Ref
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

    # 5. Bottom motif & Brand
    has_motif = (variation in ["A", "B"])
    bm = get_seamless_book_motif(BG_RGB) if has_motif else None
    if bm:
        target_mw = 350 if is_916 else 260
        aspect = bm.height / bm.width
        target_mh = int(target_mw * aspect)
        bm_resized = bm.resize((target_mw, target_mh), Image.Resampling.LANCZOS)
    else:
        target_mh = 0

    brand_h = 32 if is_916 else 24

    # TOTAL CONTENT HEIGHT
    hero_block_h = lh + gap_between_ar_latin + ar_bb[3] + gap_ar_to_origin + oh
    quote_block_h = qh + 8 + italic_block_h + 12 + rh

    # DYNAMIC VERTICAL DISTRIBUTION (FLEX)
    # Available height between safe margins:
    y_safe_top = 130 if is_916 else 70
    y_safe_bottom = h - (100 if is_916 else 50)
    avail_h = y_safe_bottom - y_safe_top

    # Fixed elements total height:
    total_fixed_h = 30 + hero_block_h + div_h + body_block_h + quote_block_h + target_mh + brand_h
    free_h = max(30, avail_h - total_fixed_h)

    # Flex weights:
    # 1. Top space: %16
    # 2. Hero to Divider: %18
    # 3. Divider to Body: %16
    # 4. Body to Quote: %20
    # 5. Quote to Motif: %24
    # 6. Motif to Brand: %6
    p1 = int(free_h * (0.12 if is_916 else 0.10))
    p2 = int(free_h * (0.18 if is_916 else 0.16))
    p3 = int(free_h * (0.16 if is_916 else 0.16))
    p4 = int(free_h * (0.18 if is_916 else 0.16))
    p5 = int(free_h * (0.28 if is_916 else 0.32))
    p6 = int(free_h * (0.08 if is_916 else 0.10))

    # --- RENDERING ---
    # Top Tag
    tag_y = y_safe_top + p1
    tag_str = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_str, font=f_tag)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, tag_y), tag_str, font=f_tag, fill=C_ACCENT)

    cur_y = tag_y + (48 if is_916 else 36)

    # HERO WORD
    if variation == "B":
        # Arabic FIRST
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_between_ar_latin

        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_ar_to_origin
    else:
        # Latin FIRST (Matching Reference Layout)
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_between_ar_latin

        # Arabic Calligraphy
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        # CRITICAL SAFE AREA: Use exact ar_bb[3] to guarantee kasra & descenders never collide
        cur_y += ar_bb[3] + gap_ar_to_origin

    # Origin Line
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += oh + p2

    # Delicate Divider
    div_w = 200
    draw.line([(w // 2 - div_w // 2, cur_y), (w // 2 + div_w // 2, cur_y)], fill=C_DIVIDER, width=1)
    dot_r = 4
    draw.ellipse([w // 2 - dot_r, cur_y - dot_r, w // 2 + dot_r, cur_y + dot_r], fill=C_ACCENT)
    cur_y += p3

    # Definition / Lügat Manası
    for bl in body_lines:
        b_bb = draw.textbbox((0, 0), bl, font=f_body)
        bw = b_bb[2] - b_bb[0]
        draw.text(((w - bw) // 2, cur_y), bl, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += p4

    # Quotation Mark
    draw.text(((w - (q_bb[2] - q_bb[0])) // 2, cur_y), q_txt, font=f_quote, fill=C_QUOTE)
    cur_y += qh + (10 if is_916 else 6)

    # Reflection / Poetic Sentence
    for il in italic_lines:
        i_bb = draw.textbbox((0, 0), il, font=f_italic)
        iw = i_bb[2] - i_bb[0]
        draw.text(((w - iw) // 2, cur_y), il, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += (14 if is_916 else 10)

    # Ayet Citation
    draw.text(((w - rw) // 2, cur_y), ref_txt, font=f_ref, fill=C_REF)
    cur_y += rh + p5

    # Bottom Artwork
    if bm:
        im.paste(bm_resized, ((w - target_mw) // 2, cur_y), bm_resized)
        cur_y += target_mh + p6
    else:
        # Elegant small gold emblem for variation C
        orn_y = cur_y + (16 if is_916 else 10)
        draw.line([(w // 2 - 36, orn_y), (w // 2 + 36, orn_y)], fill=C_DIVIDER, width=1)
        draw.ellipse([w // 2 - 3, orn_y - 3, w // 2 + 3, orn_y + 3], fill=C_ACCENT)
        cur_y = orn_y + (28 if is_916 else 20)

    # Brand Signature: "ezan plus"
    brand_str = "ezan plus 🪶"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, cur_y), brand_str, font=f_brand, fill=C_TITLE)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    print(f"Generated: {out_p}")
    return out_p

if __name__ == "__main__":
    # Generate 9:16
    ciz_kusursuz_yalin_kart(variation="A", format_tipi="9:16", dosya_adi="kelime_v17_yalin_A_9_16.png")
    ciz_kusursuz_yalin_kart(variation="B", format_tipi="9:16", dosya_adi="kelime_v17_yalin_B_9_16.png")
    ciz_kusursuz_yalin_kart(variation="C", format_tipi="9:16", dosya_adi="kelime_v17_yalin_C_9_16.png")

    # Generate 4:5
    ciz_kusursuz_yalin_kart(variation="A", format_tipi="4:5", dosya_adi="kelime_v17_yalin_A_4_5.png")
    ciz_kusursuz_yalin_kart(variation="B", format_tipi="4:5", dosya_adi="kelime_v17_yalin_B_4_5.png")
    ciz_kusursuz_yalin_kart(variation="C", format_tipi="4:5", dosya_adi="kelime_v17_yalin_C_4_5.png")
