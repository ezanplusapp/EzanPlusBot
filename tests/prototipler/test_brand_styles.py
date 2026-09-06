import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

from test_motifs import (
    font_al,
    ar_prep,
    metin_satirla,
    create_subtle_paper_background,
    draw_seljuk_star,
    draw_praying_hands_seal,
    draw_delicate_crescent_star,
)

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
FONTLAR = KOK_DIZIN / "assets" / "fonts"
IKONLAR = KOK_DIZIN / "assets" / "icons"
CIKTI = KOK_DIZIN / "data" / "cikti"

def ciz_ezanplus_kuran_sozlugu(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    arabic_first: bool = False,
    style_option: str = "seljuk_star", # "seljuk_star", "brand_seal", "crescent_star", "pure_typography", "mushaf_frame"
    dosya_adi: str = "ezanplus_kelime.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # 1. Subtle tactile paper background
    im = create_subtle_paper_background(w, h)
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
    C_GOLD = "#B45309"       # Warm kehribar

    # Font Sizes
    if is_916:
        pt_tag = 16
        pt_latin = 84
        pt_arabic = 120
        pt_origin = 26
        pt_body = 40
        lh_body = 64
        pt_quote = 66
        pt_italic = 33
        lh_italic = 52
        pt_ref = 18
        pt_brand = 25
        max_text_w = 840
    else:
        pt_tag = 14
        pt_latin = 68
        pt_arabic = 98
        pt_origin = 22
        pt_body = 33
        lh_body = 52
        pt_quote = 54
        pt_italic = 27
        lh_italic = 42
        pt_ref = 16
        pt_brand = 21
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

    # Optional: Mushaf Frame Style
    if style_option == "mushaf_frame":
        fx1, fy1 = 50, (90 if is_916 else 50)
        fx2, fy2 = w - 50, h - (90 if is_916 else 50)
        draw.rectangle([fx1, fy1, fx2, fy2], outline="#DFD2BD", width=1)
        draw.rectangle([fx1 + 6, fy1 + 6, fx2 - 6, fy2 - 6], outline="#EFE5D5", width=1)
        # Corner dots
        for cx, cy in [(fx1 + 3, fy1 + 3), (fx2 - 3, fy1 + 3), (fx1 + 3, fy2 - 3), (fx2 - 3, fy2 - 3)]:
            draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=C_ACCENT)

    # Content Measurement
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

    # Safe areas
    gap_between_ar_latin = 22 if is_916 else 16
    gap_ar_to_origin = 40 if is_916 else 30

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

    # Target motif setup
    motif_img = None
    target_mh = 0
    target_mw = 0
    motif_size = 64 if is_916 else 50

    if style_option == "seljuk_star":
        motif_img = draw_seljuk_star(motif_size, color_rgb=(140, 74, 47), line_width=2)
        target_mh = motif_size
        target_mw = motif_size
    elif style_option == "brand_seal":
        motif_img = draw_praying_hands_seal(motif_size + 14, color_hex="#8C4A2F")
        target_mh = motif_size + 14
        target_mw = motif_size + 14
    elif style_option == "crescent_star":
        motif_img = draw_delicate_crescent_star(motif_size, color_hex="#8C4A2F")
        target_mh = motif_size
        target_mw = motif_size
    elif style_option == "mushaf_frame":
        motif_img = draw_seljuk_star(motif_size - 10, color_rgb=(180, 83, 9), line_width=2)
        target_mh = motif_size - 10
        target_mw = motif_size - 10
    else: # pure_typography
        target_mh = 16
        target_mw = 80

    brand_h = 32 if is_916 else 24
    hero_block_h = lh + gap_between_ar_latin + ar_bb[3] + gap_ar_to_origin + oh
    quote_block_h = qh + 8 + italic_block_h + 14 + rh

    y_safe_top = 140 if is_916 else 70
    y_safe_bottom = h - (110 if is_916 else 55)
    avail_h = y_safe_bottom - y_safe_top

    total_fixed_h = 30 + hero_block_h + div_h + body_block_h + quote_block_h + target_mh + brand_h
    free_h = max(20, avail_h - total_fixed_h)

    # Harmonious distribution ratios
    p1 = int(free_h * (0.09 if is_916 else 0.08))
    p2 = int(free_h * (0.16 if is_916 else 0.14))
    p3 = int(free_h * (0.16 if is_916 else 0.14))
    p4 = int(free_h * (0.18 if is_916 else 0.16))
    p5 = int(free_h * (0.28 if is_916 else 0.34))
    p6 = int(free_h * (0.13 if is_916 else 0.14))

    # --- DRAWING ---
    # 1. Top Header Tag
    tag_y = y_safe_top + p1
    tag_str = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_str, font=f_tag)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, tag_y), tag_str, font=f_tag, fill=C_ACCENT)

    cur_y = tag_y + (54 if is_916 else 40)

    # 2. Hero Word (Latin + Calligraphy or Calligraphy + Latin)
    if arabic_first:
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_between_ar_latin

        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_ar_to_origin
    else:
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_between_ar_latin

        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_ar_to_origin

    # 3. Origin Line (Ample Safe Area!)
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += oh + p2

    # 4. Delicate Divider Line with Central Rosette/Dot
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

    # 9. Brand Tailored Motif (Instead of books!)
    if motif_img:
        im.paste(motif_img, ((w - target_mw) // 2, cur_y), motif_img)
        cur_y += target_mh + p6
    else: # pure_typography
        orn_y = cur_y + (10 if is_916 else 6)
        draw.line([(w // 2 - 40, orn_y), (w // 2 + 40, orn_y)], fill=C_DIVIDER, width=1)
        draw.ellipse([w // 2 - 3, orn_y - 3, w // 2 + 3, orn_y + 3], fill=C_ACCENT)
        cur_y = orn_y + (28 if is_916 else 18)

    # 10. Brand Signature: "ezan plus"
    brand_str = "ezan plus"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, cur_y), brand_str, font=f_brand, fill=C_TITLE)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    print(f"Generated: {out_p}")
    return out_p

if __name__ == "__main__":
    # Style 1: Seljuk 8-pointed Geometric Star (Classical Islamic Art)
    ciz_ezanplus_kuran_sozlugu(style_option="seljuk_star", format_tipi="9:16", dosya_adi="stil1_selcuklu_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="seljuk_star", format_tipi="4:5", dosya_adi="stil1_selcuklu_4_5.png")

    # Style 2: Praying Hands Brand Seal (Ezan Plus Duacı Eller Kurumsal Mührü)
    ciz_ezanplus_kuran_sozlugu(style_option="brand_seal", format_tipi="9:16", dosya_adi="stil2_muhur_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="brand_seal", format_tipi="4:5", dosya_adi="stil2_muhur_4_5.png")

    # Style 3: Crescent & Star Islamic Finial (Zarif Hilal & Yıldız)
    ciz_ezanplus_kuran_sozlugu(style_option="crescent_star", format_tipi="9:16", dosya_adi="stil3_hilal_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="crescent_star", format_tipi="4:5", dosya_adi="stil3_hilal_4_5.png")

    # Style 4: Pure Literary Typography (Sadece Tipografi ve Asil Ayraç)
    ciz_ezanplus_kuran_sozlugu(style_option="pure_typography", format_tipi="9:16", dosya_adi="stil4_tipografi_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="pure_typography", format_tipi="4:5", dosya_adi="stil4_tipografi_4_5.png")

    # Style 5: Mushaf Frame Style (Klasik Mushaf Sayfası Çerçeveli)
    ciz_ezanplus_kuran_sozlugu(style_option="mushaf_frame", format_tipi="9:16", dosya_adi="stil5_mushaf_cerceveli_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="mushaf_frame", format_tipi="4:5", dosya_adi="stil5_mushaf_cerceveli_4_5.png")

    # Arabic Calligraphy First Variations
    ciz_ezanplus_kuran_sozlugu(style_option="seljuk_star", arabic_first=True, format_tipi="9:16", dosya_adi="stil1_arapca_basta_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="seljuk_star", arabic_first=True, format_tipi="4:5", dosya_adi="stil1_arapca_basta_4_5.png")
    ciz_ezanplus_kuran_sozlugu(style_option="brand_seal", arabic_first=True, format_tipi="9:16", dosya_adi="stil2_arapca_basta_9_16.png")
    ciz_ezanplus_kuran_sozlugu(style_option="brand_seal", arabic_first=True, format_tipi="4:5", dosya_adi="stil2_arapca_basta_4_5.png")
