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

def ciz_nihai_yalin_kelime(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    variation: str = "A", # "A" = Latin first, "B" = Arabic first
    footer_style: str = "book", # "book", "icon", "minimal"
    dosya_adi: str = "kelime_final.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # Warm vintage paper background
    BG_RGB = (245, 237, 226) # #F5EDE2
    im = Image.new("RGB", (w, h), BG_RGB)
    draw = ImageDraw.Draw(im)

    # Color Palette
    C_TITLE = "#362214"      # Deep antique espresso
    C_ARABIC = "#26160C"     # Rich dark calligraphy ink
    C_ACCENT = "#8C4A2F"     # Warm terracotta / rust
    C_DIVIDER = "#D7C2AB"    # Soft antique line
    C_BODY = "#2E241E"       # Deep warm charcoal
    C_QUOTE = "#A65B36"      # Terracotta quotation
    C_ITALIC = "#3E3027"     # Poetic dark espresso
    C_REF = "#8C4A2F"        # Refined terracotta citation

    # Font Sizes
    if is_916:
        pt_tag = 16
        pt_latin = 84
        pt_arabic = 118
        pt_origin = 26
        pt_body = 40
        lh_body = 64
        pt_quote = 66
        pt_italic = 33
        lh_italic = 52
        pt_ref = 18
        pt_brand = 24
        max_text_w = 830
    else:
        pt_tag = 14
        pt_latin = 70
        pt_arabic = 98
        pt_origin = 22
        pt_body = 33
        lh_body = 52
        pt_quote = 54
        pt_italic = 27
        lh_italic = 42
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

    # Content Measurement
    ar_prep_txt = ar_prep(kelime_ar)
    ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
    ar_w = ar_bb[2] - ar_bb[0]

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
    gap_ar_to_origin = 38 if is_916 else 28

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

    # Load book motif
    book_p = IKONLAR / "antique_books_cutout.png"
    bm = None
    target_mh = 0
    target_mw = 0
    if footer_style == "book" and book_p.exists():
        bm_raw = Image.open(book_p).convert("RGBA")
        c_crop = bm_raw.crop(bm_raw.getbbox())
        target_mw = 350 if is_916 else 260
        target_mh = int(target_mw * (c_crop.height / c_crop.width))
        bm = c_crop.resize((target_mw, target_mh), Image.Resampling.LANCZOS)
    elif footer_style == "icon":
        target_mh = 48 if is_916 else 38
    else:
        target_mh = 16

    brand_h = 32 if is_916 else 24
    hero_block_h = lh + gap_between_ar_latin + ar_bb[3] + gap_ar_to_origin + oh
    quote_block_h = qh + 8 + italic_block_h + 12 + rh

    y_safe_top = 130 if is_916 else 70
    y_safe_bottom = h - (100 if is_916 else 50)
    avail_h = y_safe_bottom - y_safe_top

    total_fixed_h = 30 + hero_block_h + div_h + body_block_h + quote_block_h + target_mh + brand_h
    free_h = max(20, avail_h - total_fixed_h)

    p1 = int(free_h * (0.10 if is_916 else 0.08))
    p2 = int(free_h * (0.16 if is_916 else 0.14))
    p3 = int(free_h * (0.16 if is_916 else 0.14))
    p4 = int(free_h * (0.18 if is_916 else 0.16))
    p5 = int(free_h * (0.32 if is_916 else 0.36))
    p6 = int(free_h * (0.08 if is_916 else 0.12))

    # --- DRAWING ---
    # 1. Top Header Tag
    tag_y = y_safe_top + p1
    tag_str = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_str, font=f_tag)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, tag_y), tag_str, font=f_tag, fill=C_ACCENT)

    cur_y = tag_y + (50 if is_916 else 38)

    # 2. Hero Word
    if variation == "B":
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_between_ar_latin

        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_ar_to_origin
    else:
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_between_ar_latin

        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_ar_to_origin

    # 3. Origin Line (Safe area preserved!)
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += oh + p2

    # 4. Delicate Divider Line
    div_w = 200
    draw.line([(w // 2 - div_w // 2, cur_y), (w // 2 + div_w // 2, cur_y)], fill=C_DIVIDER, width=1)
    dot_r = 4
    draw.ellipse([w // 2 - dot_r, cur_y - dot_r, w // 2 + dot_r, cur_y + dot_r], fill=C_ACCENT)
    cur_y += p3

    # 5. Definition / Lügat Manası
    for bl in body_lines:
        b_bb = draw.textbbox((0, 0), bl, font=f_body)
        bw = b_bb[2] - b_bb[0]
        draw.text(((w - bw) // 2, cur_y), bl, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += p4

    # 6. Quotation Mark
    draw.text(((w - (q_bb[2] - q_bb[0])) // 2, cur_y), q_txt, font=f_quote, fill=C_QUOTE)
    cur_y += qh + (10 if is_916 else 6)

    # 7. Poetic Reflection / Ayah
    for il in italic_lines:
        i_bb = draw.textbbox((0, 0), il, font=f_italic)
        iw = i_bb[2] - i_bb[0]
        draw.text(((w - iw) // 2, cur_y), il, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += (14 if is_916 else 10)

    # 8. Ayet Citation
    draw.text(((w - rw) // 2, cur_y), ref_txt, font=f_ref, fill=C_REF)
    cur_y += rh + p5

    # 9. Bottom Footer
    if footer_style == "book" and bm:
        im.paste(bm, ((w - target_mw) // 2, cur_y), bm)
        cur_y += target_mh + p6
    elif footer_style == "icon":
        # Discreet circular red Ezan Plus logo
        logo_path = IKONLAR / "logo.png"
        if logo_path.exists():
            ls = 44 if is_916 else 36
            logo = Image.open(logo_path).convert("RGBA").resize((ls, ls), Image.Resampling.LANCZOS)
            mask = Image.new("L", (ls, ls), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, ls, ls], radius=12, fill=255)
            im.paste(logo, ((w - ls) // 2, cur_y), mask)
            cur_y += ls + p6
    else:
        # Pure typographic flourish
        orn_y = cur_y + (10 if is_916 else 6)
        draw.line([(w // 2 - 36, orn_y), (w // 2 + 36, orn_y)], fill=C_DIVIDER, width=1)
        draw.ellipse([w // 2 - 3, orn_y - 3, w // 2 + 3, orn_y + 3], fill=C_ACCENT)
        cur_y = orn_y + (24 if is_916 else 16)

    # Brand Signature: "ezan plus"
    brand_str = "ezan plus"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, cur_y), brand_str, font=f_brand, fill=C_TITLE)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    print(f"Generated: {out_p}")
    return out_p

if __name__ == "__main__":
    # 1. Option 1: Latin First + Antique Books (Exact user reference vibe)
    ciz_nihai_yalin_kelime(variation="A", footer_style="book", format_tipi="9:16", dosya_adi="secenek1_yalin_9_16.png")
    ciz_nihai_yalin_kelime(variation="A", footer_style="book", format_tipi="4:5", dosya_adi="secenek1_yalin_4_5.png")

    # 2. Option 2: Arabic First + Antique Books
    ciz_nihai_yalin_kelime(variation="B", footer_style="book", format_tipi="9:16", dosya_adi="secenek2_arapca_basta_9_16.png")
    ciz_nihai_yalin_kelime(variation="B", footer_style="book", format_tipi="4:5", dosya_adi="secenek2_arapca_basta_4_5.png")

    # 3. Option 3: Latin First + Discreet Ezan Plus Brand Logo (App-centric minimalist)
    ciz_nihai_yalin_kelime(variation="A", footer_style="icon", format_tipi="9:16", dosya_adi="secenek3_marka_logolu_9_16.png")
    ciz_nihai_yalin_kelime(variation="A", footer_style="icon", format_tipi="4:5", dosya_adi="secenek3_marka_logolu_4_5.png")
