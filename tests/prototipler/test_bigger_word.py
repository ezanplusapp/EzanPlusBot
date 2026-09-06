import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

from test_v2_concepts import (
    font_al,
    ar_prep,
    metin_satirla,
    create_subtle_paper_background,
    draw_ornate_seljuk_star as draw_seljuk_star,
    draw_ezanplus_publishing_seal,
)

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
CIKTI = KOK_DIZIN / "data" / "cikti"
ARTIFACTS = Path("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93")

def render_large_word_card(
    kelime_tr: str = "Sekînet",
    kelime_ar: str = "السَّكِينَةُ",
    okunus: str = "es-Sekîne",
    kok: str = "S-K-N (Sükûn)",
    lugat_anlami: str = "Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
    alinti_metin: str = "Dünya seni ne kadar sarsarsa sarsın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
    ayet_ref: str = "Fetih Sûresi, 4. Âyet",
    format_tipi: str = "9:16",
    scale_profile: str = "balanced_large", # "balanced_large", "hero_latin", "hero_arabic"
    arabic_first: bool = True,
    motif_type: str = "seal", # "seal", "seljuk"
    dosya_adi: str = "large_word_test.png"
):
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    im = create_subtle_paper_background(w, h)
    draw = ImageDraw.Draw(im)

    C_TITLE = "#362214"
    C_ARABIC = "#26160C"
    C_ACCENT = "#8C4A2F"
    C_DIVIDER = "#D7C2AB"
    C_BODY = "#2E241E"
    C_QUOTE = "#A65B36"
    C_ITALIC = "#3E3027"
    C_REF = "#8C4A2F"

    # Font Sizes based on profile
    if is_916:
        pt_tag = 16
        pt_origin = 27
        pt_body = 40
        lh_body = 64
        pt_quote = 66
        pt_italic = 33
        lh_italic = 52
        pt_ref = 18
        pt_brand = 25
        max_text_w = 850

        if scale_profile == "balanced_large":
            pt_latin = 112
            pt_arabic = 145
        elif scale_profile == "hero_latin":
            pt_latin = 128
            pt_arabic = 120
        elif scale_profile == "hero_arabic":
            pt_latin = 96
            pt_arabic = 165
        elif scale_profile == "super_hero":
            pt_latin = 126
            pt_arabic = 150
    else: # 4:5
        pt_tag = 14
        pt_origin = 22
        pt_body = 33
        lh_body = 52
        pt_quote = 54
        pt_italic = 27
        lh_italic = 42
        pt_ref = 16
        pt_brand = 21
        max_text_w = 810

        if scale_profile == "balanced_large":
            pt_latin = 92
            pt_arabic = 118
        elif scale_profile == "hero_latin":
            pt_latin = 104
            pt_arabic = 98
        elif scale_profile == "hero_arabic":
            pt_latin = 76
            pt_arabic = 135
        elif scale_profile == "super_hero":
            pt_latin = 102
            pt_arabic = 124

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

    # Safe gaps
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
    if motif_type == "seal":
        s_sz = 88 if is_916 else 66
        motif_img = draw_ezanplus_publishing_seal(s_sz, color_hex="#8C4A2F")
    else:
        s_sz = 82 if is_916 else 62
        motif_img = draw_seljuk_star(s_sz, color_rgb=(140, 74, 47))
    target_mh, target_mw = s_sz, s_sz

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

    # Draw Header Tag
    tag_y = y_safe_top + p1
    tag_str = "E Z A N   P L U S   •   K U R ' Â N   S Ö Z L Ü Ğ Ü"
    t_bb = draw.textbbox((0, 0), tag_str, font=f_tag)
    tw = t_bb[2] - t_bb[0]
    draw.text(((w - tw) // 2, tag_y), tag_str, font=f_tag, fill=C_ACCENT)

    cur_y = tag_y + (54 if is_916 else 40)

    # Hero Word
    if arabic_first:
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_between
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_origin
    else:
        draw.text(((w - lw) // 2, cur_y - l_bb[1]), latin_txt, font=f_latin, fill=C_TITLE)
        cur_y += lh + gap_between
        draw.text(((w - ar_w) // 2 - ar_bb[0], cur_y - ar_bb[1]), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
        cur_y += ar_bb[3] + gap_origin

    # Origin
    draw.text(((w - ow) // 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += oh + p2

    # Divider
    div_w = 200
    draw.line([(w // 2 - div_w // 2, cur_y), (w // 2 + div_w // 2, cur_y)], fill=C_DIVIDER, width=1)
    dot_r = 4
    draw.ellipse([w // 2 - dot_r, cur_y - dot_r, w // 2 + dot_r, cur_y + dot_r], fill=C_ACCENT)
    cur_y += p3

    # Definition
    for bl in body_lines:
        b_bb = draw.textbbox((0, 0), bl, font=f_body)
        bw = b_bb[2] - b_bb[0]
        draw.text(((w - bw) // 2, cur_y), bl, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += p4

    # Quote
    draw.text(((w - (q_bb[2] - q_bb[0])) // 2, cur_y), q_txt, font=f_quote, fill=C_QUOTE)
    cur_y += qh + (10 if is_916 else 6)

    # Reflection
    for il in italic_lines:
        i_bb = draw.textbbox((0, 0), il, font=f_italic)
        iw = i_bb[2] - i_bb[0]
        draw.text(((w - iw) // 2, cur_y), il, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += (14 if is_916 else 10)

    # Ayet Ref
    draw.text(((w - rw) // 2, cur_y), ref_txt, font=f_ref, fill=C_REF)
    cur_y += rh + p5

    # Motif
    if motif_img:
        im.paste(motif_img, ((w - target_mw) // 2, cur_y), motif_img)
        cur_y += target_mh + p6

    # Brand
    brand_str = "ezan plus"
    br_bb = draw.textbbox((0, 0), brand_str, font=f_brand)
    br_w = br_bb[2] - br_bb[0]
    draw.text(((w - br_w) // 2, cur_y), brand_str, font=f_brand, fill=C_TITLE)

    out_p = CIKTI / dosya_adi
    im.save(str(out_p), quality=96)
    
    # Also save to artifacts
    art_p = ARTIFACTS / dosya_adi
    im.save(str(art_p), quality=96)
    print(f"Saved: {out_p} and {art_p}")
    return out_p

if __name__ == "__main__":
    # 1. Balanced Large (Both Arabic & Latin significantly enlarged)
    # Arabic First
    render_large_word_card(scale_profile="balanced_large", arabic_first=True, format_tipi="9:16", dosya_adi="buyuk_kelime_dengeli_arapca_basta_9_16.png")
    render_large_word_card(scale_profile="balanced_large", arabic_first=True, format_tipi="4:5", dosya_adi="buyuk_kelime_dengeli_arapca_basta_4_5.png")

    # Latin First (Just like the reference 'mucize')
    render_large_word_card(scale_profile="balanced_large", arabic_first=False, format_tipi="9:16", dosya_adi="buyuk_kelime_dengeli_turkce_basta_9_16.png")
    render_large_word_card(scale_profile="balanced_large", arabic_first=False, format_tipi="4:5", dosya_adi="buyuk_kelime_dengeli_turkce_basta_4_5.png")

    # 2. Hero Latin (Turkish word ultra huge, similar to reference layout)
    render_large_word_card(scale_profile="hero_latin", arabic_first=False, format_tipi="9:16", dosya_adi="buyuk_kelime_turkce_dev_9_16.png")
    render_large_word_card(scale_profile="hero_latin", arabic_first=False, format_tipi="4:5", dosya_adi="buyuk_kelime_turkce_dev_4_5.png")

    # 3. Hero Arabic (Arabic Calligraphy ultra huge)
    render_large_word_card(scale_profile="hero_arabic", arabic_first=True, format_tipi="9:16", dosya_adi="buyuk_kelime_arapca_dev_9_16.png")
    render_large_word_card(scale_profile="hero_arabic", arabic_first=True, format_tipi="4:5", dosya_adi="buyuk_kelime_arapca_dev_4_5.png")

    # 4. Super Hero (Both Latin & Arabic Max Bold & Grandeur)
    render_large_word_card(scale_profile="super_hero", arabic_first=False, format_tipi="9:16", dosya_adi="buyuk_kelime_super_hero_turkce_basta_9_16.png")
    render_large_word_card(scale_profile="super_hero", arabic_first=False, format_tipi="4:5", dosya_adi="buyuk_kelime_super_hero_turkce_basta_4_5.png")
    render_large_word_card(scale_profile="super_hero", arabic_first=True, format_tipi="9:16", dosya_adi="buyuk_kelime_super_hero_arapca_basta_9_16.png")
    render_large_word_card(scale_profile="super_hero", arabic_first=True, format_tipi="4:5", dosya_adi="buyuk_kelime_super_hero_arapca_basta_4_5.png")
