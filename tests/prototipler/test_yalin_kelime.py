import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

# Load sample book motif if exists
motif_path = Path("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/antique_books_motif_1788650839341.jpg")
book_motif = None
if motif_path.exists():
    try:
        bm = Image.open(motif_path).convert("RGBA")
        # Crop the center book area
        bw, bh = bm.size
        # Book is roughly in center y: 250 to 850, x: 120 to 900
        bm_crop = bm.crop((120, 240, 904, 860))
        # Create a soft alpha mask for edges
        mask = Image.new("L", bm_crop.size, 255)
        m_draw = ImageDraw.Draw(mask)
        # soft vignette
        w_c, h_c = bm_crop.size
        for r in range(40):
            alpha = int(255 * (r / 40.0))
            m_draw.rectangle([r, r, w_c - r, h_c - r], outline=alpha, width=1)
        # Blur the mask slightly
        mask = mask.filter(ImageFilter.GaussianBlur(12))
        bm_crop.putalpha(mask)
        book_motif = bm_crop
    except Exception as e:
        print("Motif load error:", e)

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

def ciz_yalin_kart(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    hayat_dersi: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    variation: str = "v1_latin_first", # "v1_latin_first", "v2_arabic_first", "v3_pure_zen"
    dosya_adi: str = "test_yalin.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # Warm vintage paper background
    bg_color = (245, 237, 226) # #F5EDE2 warm parchment
    im = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(im)

    # Color Palette
    C_TITLE = "#382415"      # Deep warm antique brown
    C_ARABIC = "#26170D"     # Rich deep ink
    C_ACCENT = "#8C4A2F"     # Terracotta / warm sienna
    C_DIVIDER = "#D7C2AB"    # Soft warm line
    C_BODY = "#2E241E"       # Warm charcoal/espresso body
    C_QUOTE = "#A65B36"      # Terracotta quote mark
    C_ITALIC = "#42332A"     # Deep warm reflection
    C_REF = "#8C4A2F"        # Citation

    # Fonts
    if is_916:
        pt_header = 15
        pt_latin = 78
        pt_arabic = 112
        pt_origin = 25
        pt_body = 38
        line_h_body = 60
        pt_quote = 64
        pt_italic = 31
        line_h_italic = 48
        pt_ref = 18
        pt_brand = 22
    else:
        pt_header = 14
        pt_latin = 68
        pt_arabic = 96
        pt_origin = 22
        pt_body = 32
        line_h_body = 50
        pt_quote = 54
        pt_italic = 26
        line_h_italic = 40
        pt_ref = 16
        pt_brand = 19

    f_header = font_al("Manrope.ttf", pt_header, 600)
    f_latin = font_al("Lora.ttf", pt_latin, 700)
    f_arabic = font_al("amiri-700-arabic.ttf", pt_arabic)
    f_origin = font_al("Lora.ttf", pt_origin, 400)
    f_body = font_al("Lora.ttf", pt_body, 500)
    f_quote = font_al("Lora.ttf", pt_quote, 700)
    f_italic = font_al("Lora.ttf", pt_italic, 400) # Lora looks graceful
    f_ref = font_al("Manrope.ttf", pt_ref, 700)
    f_brand = font_al("Lora.ttf", pt_brand, 600)

    # Top boundary & Bottom boundary
    y_start = 140 if is_916 else 76
    y_end = h - (120 if is_916 else 64)

    # 1. Top Header Tag: E Z A N  P L U S  •  K U R ' Â N  S Ö Z L Ü Ğ Ü
    tag_text = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_text, font=f_header)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, y_start), tag_text, font=f_header, fill=C_ACCENT)

    cur_y = y_start + (50 if is_916 else 36)

    # Content Box Width for text wrap
    max_text_w = 820 if is_916 else 800

    # Layout depending on variation:
    if variation == "v1_latin_first":
        # A) Turkish Word (e.g. sekînet)
        latin_txt = kelime_tr.lower()
        l_bb = draw.textbbox((0, 0), latin_txt, font=f_latin)
        lw = l_bb[2] - l_bb[0]
        lh = l_bb[3] - l_bb[1]
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + (16 if is_916 else 12)

        # B) Arabic Calligraphy
        ar_prep_txt = ar_prep(kelime_ar)
        ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
        ar_w = ar_bb[2] - ar_bb[0]
        # Precise drawing with safe area
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        # CRITICAL SAFE AREA FIX: Calculate exact bottom based on bbox[3]
        cur_y += ar_bb[3] + (32 if is_916 else 24)

    elif variation == "v2_arabic_first":
        # A) Arabic Calligraphy FIRST (Hero)
        ar_prep_txt = ar_prep(kelime_ar)
        ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
        ar_w = ar_bb[2] - ar_bb[0]
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + (28 if is_916 else 20)

        # B) Turkish Word
        latin_txt = kelime_tr
        l_bb = draw.textbbox((0, 0), latin_txt, font=f_latin)
        lw = l_bb[2] - l_bb[0]
        lh = l_bb[3] - l_bb[1]
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + (16 if is_916 else 12)

    else: # v3_pure_zen (Turkish title in elegant title case, then Arabic)
        latin_txt = kelime_tr.title()
        l_bb = draw.textbbox((0, 0), latin_txt, font=f_latin)
        lw = l_bb[2] - l_bb[0]
        lh = l_bb[3] - l_bb[1]
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + (14 if is_916 else 10)

        ar_prep_txt = ar_prep(kelime_ar)
        ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
        ar_w = ar_bb[2] - ar_bb[0]
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + (30 if is_916 else 22)

    # C) Origin & Pronunciation Line (Safe area guaranteed!)
    origin_txt = f"Arapça: {okunus}   •   Kök: {kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += (o_bb[3] - o_bb[1]) + (32 if is_916 else 24)

    # D) Delicate Divider Line with Center Dot (Reference Style)
    div_w = 200
    div_y = cur_y
    draw.line([(w // 2 - div_w // 2, div_y), (w // 2 + div_w // 2, div_y)], fill=C_DIVIDER, width=1)
    dot_r = 4
    draw.ellipse([w // 2 - dot_r, div_y - dot_r, w // 2 + dot_r, div_y + dot_r], fill=C_ACCENT)
    cur_y += (36 if is_916 else 28)

    # E) Definition / Lügat Manası (Centered, generous line height)
    body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    for bl in body_lines:
        b_bb = draw.textbbox((0, 0), bl, font=f_body)
        bw = b_bb[2] - b_bb[0]
        draw.text(((w - bw) // 2, cur_y), bl, font=f_body, fill=C_BODY)
        cur_y += line_h_body

    cur_y += (24 if is_916 else 16)

    # F) Quotation Mark (Terracotta / Antique Amber)
    q_txt = "“"
    q_bb = draw.textbbox((0, 0), q_txt, font=f_quote)
    qw = q_bb[2] - q_bb[0]
    draw.text(((w - qw) // 2, cur_y), q_txt, font=f_quote, fill=C_QUOTE)
    cur_y += (q_bb[3] - q_bb[1]) + (10 if is_916 else 6)

    # G) Poetic Reflection / Life Lesson (Tefekkür)
    # Wrap reflection
    italic_lines = metin_satirla(f"“{hayat_dersi.strip('“”\"')}”", f_italic, max_text_w - 40, draw)
    for il in italic_lines:
        i_bb = draw.textbbox((0, 0), il, font=f_italic)
        iw = i_bb[2] - i_bb[0]
        draw.text(((w - iw) // 2, cur_y), il, font=f_italic, fill=C_ITALIC)
        cur_y += line_h_italic

    cur_y += (14 if is_916 else 10)

    # H) Ayet Reference (Discreet citation)
    ref_txt = ayet_ref.upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]
    draw.text(((w - rw) // 2, cur_y), ref_txt, font=f_ref, fill=C_ACCENT)

    # 4. BOTTOM AREA: BRANDING & ARTISTIC ELEMENT
    if (variation in ["v1_latin_first", "v2_arabic_first"]) and book_motif:
        # Scale and paste book motif
        target_mw = 340 if is_916 else 270
        aspect = book_motif.height / book_motif.width
        target_mh = int(target_mw * aspect)
        bm_resized = book_motif.resize((target_mw, target_mh), Image.Resampling.LANCZOS)
        
        # Bottom placement
        brand_y = y_end - (24 if is_916 else 16)
        bm_y = brand_y - target_mh - (18 if is_916 else 12)
        im.paste(bm_resized, ((w - target_mw) // 2, bm_y), bm_resized)
    else:
        # Minimalist geometric crest / feather leaf
        brand_y = y_end - (30 if is_916 else 20)
        # Small gold ornament
        orn_y = brand_y - 28
        draw.line([(w // 2 - 40, orn_y), (w // 2 + 40, orn_y)], fill=C_DIVIDER, width=1)
        draw.ellipse([w // 2 - 3, orn_y - 3, w // 2 + 3, orn_y + 3], fill=C_ACCENT)

    # Brand Signature: "ezanplus" with delicate feather/leaf symbol
    brand_str = "ezan plus"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, brand_y), brand_str, font=f_brand, fill=C_TITLE)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    print(f"Generated: {out_p}")
    return out_p

if __name__ == "__main__":
    # Generate 9:16 variations
    ciz_yalin_kart(format_tipi="9:16", variation="v1_latin_first", dosya_adi="yalin_kelime_v1_9_16.png")
    ciz_yalin_kart(format_tipi="9:16", variation="v2_arabic_first", dosya_adi="yalin_kelime_v2_9_16.png")
    ciz_yalin_kart(format_tipi="9:16", variation="v3_pure_zen", dosya_adi="yalin_kelime_v3_9_16.png")

    # Generate 4:5 variations
    ciz_yalin_kart(format_tipi="4:5", variation="v1_latin_first", dosya_adi="yalin_kelime_v1_4_5.png")
    ciz_yalin_kart(format_tipi="4:5", variation="v2_arabic_first", dosya_adi="yalin_kelime_v2_4_5.png")
    ciz_yalin_kart(format_tipi="4:5", variation="v3_pure_zen", dosya_adi="yalin_kelime_v3_4_5.png")
