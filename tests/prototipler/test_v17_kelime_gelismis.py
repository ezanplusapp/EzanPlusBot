import math
import re
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

def metin_satirla(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> List[str]:
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

def kelime_basligi_satirla(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """
    Türkçe hero kelime başlığını satırlara böler.
    Tek satıra sığıyorsa tek satır; sığmıyorsa boşluklardan veya tirelerden böler.
    """
    bb = draw.textbbox((0, 0), text, font=font)
    if (bb[2] - bb[0]) <= max_w:
        return [text]
    
    # Boşluk varsa kelime bazlı böl
    if " " in text:
        return metin_satirla(text, font, max_w, draw)
    
    # Tire varsa tireden böl
    if "-" in text:
        parts = text.split("-")
        lines = []
        cur = ""
        for p in parts:
            cand = f"{cur}-{p}" if cur else p
            c_bb = draw.textbbox((0, 0), cand + "-", font=font)
            if (c_bb[2] - c_bb[0]) <= max_w:
                cur = cand
            else:
                if cur:
                    lines.append(cur + "-")
                cur = p
        if cur:
            lines.append(cur)
        return lines
        
    return [text]

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

def _play_store_vektor_ciz(draw: ImageDraw.ImageDraw, x: float, y: float, size: float):
    w = size
    h = size
    p_tl = (x, y)
    p_bl = (x, y + h)
    p_r = (x + w, y + h / 2)
    p_mid = (x + w * 0.52, y + h / 2)
    p_top_mid = (x + w * 0.72, y + h * 0.32)
    p_bot_mid = (x + w * 0.72, y + h * 0.68)
    draw.polygon([p_tl, p_bl, p_mid], fill="#00D3FF")
    draw.polygon([p_tl, p_top_mid, p_mid], fill="#00E676")
    draw.polygon([p_bl, p_bot_mid, p_mid], fill="#FFC800")
    draw.polygon([p_top_mid, p_r, p_bot_mid, p_mid], fill="#FF3A44")

def draw_bottom_cta_bar(im: Image.Image, format_tipi: str = "9:16") -> int:
    draw = ImageDraw.Draw(im)
    w, h = im.size
    is_916 = (format_tipi == "9:16")

    nav_w = 740 if is_916 else 680
    nav_h = 92 if is_916 else 80
    nav_x1 = (w - nav_w) // 2
    nav_x2 = nav_x1 + nav_w
    nav_y1 = (h - 140) if is_916 else (h - 110)
    nav_y2 = nav_y1 + nav_h
    btn_y = nav_y1 + nav_h // 2

    # Lüks yumuşak gölge
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([nav_x1 + 2, nav_y1 + 4, nav_x2 - 2, nav_y2 + 8], radius=32, fill=(15, 3, 6, 55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    im.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(im)
    # Beyaz Buton Gövdesi
    draw.rounded_rectangle([nav_x1, nav_y1, nav_x2, nav_y2], radius=30 if is_916 else 26, fill="#FFFFFF", outline="#EFE8DC", width=2)

    # 1. Logo
    logo_path = IKONLAR / "logo.png"
    logo_size = 52 if is_916 else 46
    logo_x = nav_x1 + (20 if is_916 else 16)
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=15, fill=255)
        im.paste(logo, (logo_x, btn_y - logo_size // 2), mask)

    # 2. CTA Yazısı
    pt_cta = 24 if is_916 else 21
    font_cta = font_al("Manrope.ttf", pt_cta, 700)
    txt_x = logo_x + logo_size + (16 if is_916 else 14)
    draw.text((txt_x, btn_y - (14 if is_916 else 12)), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill="#182230")

    # 3. Store İkonları
    ps_size = 28 if is_916 else 24
    ps_x = nav_x2 - (56 if is_916 else 48)
    ps_y = btn_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    # Apple İkonu
    apple_path = IKONLAR / "apple.png"
    ap_size = 26 if is_916 else 22
    if apple_path.exists():
        ap_img = Image.open(apple_path).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        ap_x = ps_x - ap_size - (18 if is_916 else 14)
        im.paste(ap_img, (ap_x, btn_y - ap_size // 2), ap_img)
    else:
        try:
            font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30 if is_916 else 26)
            bbox_ap = draw.textbbox((0, 0), "", font=font_apple)
            ap_w, ap_h = bbox_ap[2] - bbox_ap[0], bbox_ap[3] - bbox_ap[1]
            ap_y = btn_y - ap_h // 2 - bbox_ap[1]
            ap_x = ps_x - ap_w - 20
            draw.text((ap_x, ap_y), "", font=font_apple, fill="#000000")
        except Exception:
            pass

    return nav_y1

def ciz_kelime_v17(
    kelime_tr: str,
    kelime_ar: str,
    okunus: str,
    kok: str,
    lugat_anlami: str,
    hayat_dersi: str,
    ayet_ref: str,
    format_tipi: str = "9:16",
    dosya_adi: str = "kelime_v17.png"
) -> Path:
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    # Ezan Plus Soft Kırmızı
    center_rgb = (170, 34, 40)    # #AA2228
    outer_rgb = (126, 16, 22)     # #7E1016
    c_divider = "#C84048"

    C_HERO = "#FFFFFF"
    C_ARABIC = "#FFF8EE"
    C_ACCENT = "#FDE6BA"         # Saten Şampanya Altın
    C_BODY = "#FFFDF9"
    C_ITALIC = "#FFF8ED"
    C_REF = "#FDE6BA"

    im = create_paper_background(w, h, center_rgb, outer_rgb)
    draw = ImageDraw.Draw(im)

    # 1. Alt CTA barı ve koordinatını al
    cta_ust_y = draw_bottom_cta_bar(im, format_tipi)

    max_text_w = 880 if is_916 else 840

    # 2. Hero Başlıklar (BÜYÜTÜLMÜŞ & MİNİMUM SEKÎNET BOYUT TABANI)
    # Hedef başlangıç boyutu: 172pt (9:16) / 130pt (4:5)
    # Minimum taban (Sekînet seviyesi): 154pt (9:16) / 118pt (4:5)
    target_pt = 172 if is_916 else 130
    min_pt_floor = 154 if is_916 else 118
    
    pt_latin = target_pt
    f_latin = font_al("Lora.ttf", pt_latin, 700)
    lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
    
    # Satırlardan herhangi biri max_text_w'yi aşıyorsa (örneğin tek parça çok uzun kelime)
    # boyutu adım adım düşür ama min_pt_floor'un altına inme
    max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)
    while max_line_w > max_text_w and pt_latin > min_pt_floor:
        pt_latin -= 2
        f_latin = font_al("Lora.ttf", pt_latin, 700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
        max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)
    
    # Eğer min_pt_floor seviyesinde bile tek parça sığmıyorsa (örn. 15 harfli nadir kelime) sığana kadar küçült
    while max_line_w > max_text_w and pt_latin > 75:
        pt_latin -= 3
        f_latin = font_al("Lora.ttf", pt_latin, 700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
        max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)

    lh_latin = int(pt_latin * 1.08)
    first_l_bb = draw.textbbox((0, 0), lines_tr[0], font=f_latin)
    last_l_bb = draw.textbbox((0, 0), lines_tr[-1], font=f_latin)
    latin_block_h = (len(lines_tr) - 1) * lh_latin + (last_l_bb[3] - first_l_bb[1])

    # B) Arapça Hat
    pt_arabic = 180 if is_916 else 142
    f_arabic = font_al("amiri-700-arabic.ttf", pt_arabic)
    ar_prep_txt = ar_prep(kelime_ar)
    ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
    ar_w = ar_bb[2] - ar_bb[0]
    while ar_w > max_text_w and pt_arabic > 85:
        pt_arabic -= 3
        f_arabic = font_al("amiri-700-arabic.ttf", pt_arabic)
        ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
        ar_w = ar_bb[2] - ar_bb[0]

    # C) Diğer Tipografiler
    pt_tag = 16 if is_916 else 14
    f_tag = font_al("Manrope.ttf", pt_tag, 600)

    pt_origin = 29 if is_916 else 23
    f_origin = font_al("Lora.ttf", pt_origin, 400)
    origin_txt = f"Arapça: {okunus}   •   Kök: {kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    oh = o_bb[3] - o_bb[1]

    # D) Lügat Anlamı (Büyütülmüş)
    pt_body = 48 if is_916 else 37
    lh_body = 76 if is_916 else 58
    f_body = font_al("Lora.ttf", pt_body, 500)
    body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    if len(body_lines) > 3:
        pt_body = 42 if is_916 else 33
        lh_body = 66 if is_916 else 52
        f_body = font_al("Lora.ttf", pt_body, 500)
        body_lines = metin_satirla(lugat_anlami, f_body, max_text_w, draw)
    body_block_h = len(body_lines) * lh_body

    # E) Tefekkür / Hayat Dersi Alıntısı
    pt_italic = 37 if is_916 else 29
    lh_italic = 58 if is_916 else 46
    f_italic = font_al("Lora.ttf", pt_italic, 400)
    clean_alinti = hayat_dersi.strip("“”\" ")
    italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 40, draw)
    italic_block_h = len(italic_lines) * lh_italic

    # F) Ayet Referansı
    pt_ref = 18 if is_916 else 15
    f_ref = font_al("Manrope.ttf", pt_ref, 700)
    ref_txt = ayet_ref.upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    # 3. KESİN GÖRSEL SAFE AREA HESAPLAMASI (Bounding Box Tabanlı)
    gap_tr_ar = 68 if is_916 else 46       # Artırılmış ferah safe area!
    gap_ar_origin = 58 if is_916 else 42   # Kasralardan kök bilgisine net safe area

    top_y = 150 if is_916 else 95
    bottom_y = cta_ust_y - (45 if is_916 else 35)
    usable_h = bottom_y - top_y

    # Hero bloğunun gerçek toplam görsel yüksekliği:
    hero_visual_h = latin_block_h + gap_tr_ar + (ar_bb[3] - ar_bb[1]) + gap_ar_origin + (o_bb[3] - o_bb[1])
    fixed_content_h = 28 + hero_visual_h + body_block_h + italic_block_h + rh

    free_space = max(40, usable_h - fixed_content_h)

    # Kalan boşluğu orantılı paylaştır:
    pad_tag_hero = int(free_space * 0.16)
    pad_origin_div = int(free_space * 0.18)
    pad_div_body = int(free_space * 0.24)
    pad_body_quote = int(free_space * 0.26)
    pad_quote_ref = int(free_space * 0.16)

    cur_y = top_y

    # A) Kategori Rozeti
    tag_txt = "KUR'AN SÖZLÜĞÜ  •  KAVRAM VE HİKMET".upper()
    tag_bb = draw.textbbox((0, 0), tag_txt, font=f_tag)
    tag_w = tag_bb[2] - tag_bb[0]
    draw.text(((w - tag_w) / 2, cur_y), tag_txt, font=f_tag, fill=C_ACCENT)
    cur_y += 28 + pad_tag_hero

    # B) Türkçe Hero Kelime (Çoklu satır destekli)
    latin_start_y = cur_y
    for idx, line in enumerate(lines_tr):
        bb = draw.textbbox((0, 0), line, font=f_latin)
        lw = bb[2] - bb[0]
        line_y = latin_start_y + idx * lh_latin
        draw.text(((w - lw) / 2, line_y), line, font=f_latin, fill=C_HERO)

    latin_bottom = latin_start_y + (len(lines_tr) - 1) * lh_latin + last_l_bb[3]

    # C) Arapça Hat (KUSURSUZ SAFE AREA: latin_bottom ile ar_top arasında kesin gap_tr_ar)
    ar_y = latin_bottom - ar_bb[1] + gap_tr_ar
    draw.text(((w - ar_w) / 2, ar_y), ar_prep_txt, font=f_arabic, fill=C_ARABIC)
    ar_bottom = ar_y + ar_bb[3]

    # D) Okunuş & Kök Satırı (KUSURSUZ SAFE AREA: ar_bottom ile origin_top arasında kesin gap_ar_origin)
    cur_y = ar_bottom - o_bb[1] + gap_ar_origin
    draw.text(((w - ow) / 2, cur_y), origin_txt, font=f_origin, fill=C_ACCENT)
    cur_y += (o_bb[3] - o_bb[1]) + pad_origin_div

    # E) Narin Ayraç & Altın Elmas Noktası
    div_w = 460 if is_916 else 380
    div_x1 = (w - div_w) / 2
    div_x2 = div_x1 + div_w
    draw.line([(div_x1, cur_y), (div_x2, cur_y)], fill=c_divider, width=1)
    dot_r = 3.5 if is_916 else 3.0
    draw.ellipse([(w/2 - dot_r, cur_y - dot_r), (w/2 + dot_r, cur_y + dot_r)], fill=C_ACCENT)
    cur_y += pad_div_body

    # F) Anlam Arkası Zarif Editoryal Filigran Tırnak (" )
    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    pt_fili = 340 if is_916 else 250
    f_fili = font_al("Lora.ttf", pt_fili, 700)

    first_b_bb = draw.textbbox((0, 0), body_lines[0], font=f_body)
    first_bw = first_b_bb[2] - first_b_bb[0]
    first_bx = (w - first_bw) // 2

    fili_x = first_bx - (85 if is_916 else 65)
    fili_y = cur_y - (145 if is_916 else 105)

    fili_draw.text((fili_x, fili_y), "“", font=f_fili, fill=(253, 230, 186, 26))
    im.paste(fili_layer, (0, 0), fili_layer)

    # G) Lügat Anlamı (Hero Manâ)
    draw = ImageDraw.Draw(im)
    for line in body_lines:
        bb = draw.textbbox((0, 0), line, font=f_body)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_body, fill=C_BODY)
        cur_y += lh_body

    cur_y += pad_body_quote

    # H) Tefekkür & Hayat Dersi Alıntısı
    for line in italic_lines:
        bb = draw.textbbox((0, 0), line, font=f_italic)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_italic, fill=C_ITALIC)
        cur_y += lh_italic

    cur_y += pad_quote_ref

    # I) Ayet Referansı
    draw.text(((w - rw) / 2, cur_y), ref_txt, font=f_ref, fill=C_REF)

    # Kaydet
    out_path = ARTIFACTS / dosya_adi
    im.save(out_path, "PNG")
    print(f"Render tamam: {out_path.name} (pt_latin={pt_latin}, satırlar={lines_tr})")
    return out_path

if __name__ == "__main__":
    # 1. Sekînet (Standart tekil kelime - 9:16 ve 4:5)
    ciz_kelime_v17(
        kelime_tr="Sekînet",
        kelime_ar="السَّكِينَةُ",
        okunus="es-Sekîne",
        kok="S-K-N (Sükûn)",
        lugat_anlami="Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
        hayat_dersi="Dünya seni ne kadar sarsarsa sarssın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
        ayet_ref="Fetih Sûresi, 4. Âyet",
        format_tipi="9:16",
        dosya_adi="kelime_v17_sekinet_9_16.png"
    )
    ciz_kelime_v17(
        kelime_tr="Sekînet",
        kelime_ar="السَّكِينَةُ",
        okunus="es-Sekîne",
        kok="S-K-N (Sükûn)",
        lugat_anlami="Kalbin telaş, korku ve ıstıraptan arınarak ilahi bir huzur ve sükûnete kavuşması.",
        hayat_dersi="Dünya seni ne kadar sarsarsa sarssın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
        ayet_ref="Fetih Sûresi, 4. Âyet",
        format_tipi="4:5",
        dosya_adi="kelime_v17_sekinet_4_5.png"
    )
    # 2. Huşû (Kısa tekil kelime - 9:16)
    ciz_kelime_v17(
        kelime_tr="Huşû",
        kelime_ar="الْخُشُوعُ",
        okunus="el-Huşû'",
        kok="H-Ş-A (Boyun Eğmek)",
        lugat_anlami="Kalbin derin bir saygı, haşyet ve sevgiyle titremesi; bedenin bu teslimiyetle sükûnet bulması.",
        hayat_dersi="Huşu; bedenin secdede, kalbin ise bizzat Rabbinin huzurunda olması halidir.",
        ayet_ref="Mü'minûn Sûresi, 1-2. Âyetler",
        format_tipi="9:16",
        dosya_adi="kelime_v17_husu_9_16.png"
    )
    # 3. Sıla-i Rahim (Uzun / Birleşik kavram - 9:16 ve 4:5 - alt satıra inme testi)
    ciz_kelime_v17(
        kelime_tr="Sıla-i Rahim",
        kelime_ar="صِلَةُ الرَّحِمِ",
        okunus="Sılatü'r-Rahim",
        kok="V-S-L (Kavuşmak) ve R-H-M (Merhamet)",
        lugat_anlami="Akraba, anne-baba ve yakınlarla bağları koparmayıp sevgi, ziyaret ve ikramla köprü kurmak.",
        hayat_dersi="Akrabayla bağı kesmemek, rızkın bereketlenmesine ve ömrün manevi huzurla dolmasına vesiledir.",
        ayet_ref="İsrâ Sûresi, 26. Âyet",
        format_tipi="9:16",
        dosya_adi="kelime_v17_silairahim_9_16.png"
    )
    ciz_kelime_v17(
        kelime_tr="Sıla-i Rahim",
        kelime_ar="صِلَةُ الرَّحِمِ",
        okunus="Sılatü'r-Rahim",
        kok="V-S-L (Kavuşmak) ve R-H-M (Merhamet)",
        lugat_anlami="Akraba, anne-baba ve yakınlarla bağları koparmayıp sevgi, ziyaret ve ikramla köprü kurmak.",
        hayat_dersi="Akrabayla bağı kesmemek, rızkın bereketlenmesine ve ömrün manevi huzurla dolmasına vesiledir.",
        ayet_ref="İsrâ Sûresi, 26. Âyet",
        format_tipi="4:5",
        dosya_adi="kelime_v17_silairahim_4_5.png"
    )
    print("V17_GELISMIS_TESTLERI_BASARILI")
