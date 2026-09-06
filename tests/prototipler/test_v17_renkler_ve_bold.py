import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict
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

def parse_markdown_bold(metin: str) -> List[Tuple[str, bool]]:
    parcalar = re.split(r'(\*\*.*?\*\*)', metin)
    tokenlar = []
    for parca in parcalar:
        if not parca:
            continue
        if parca.startswith("**") and parca.endswith("**"):
            ic_metin = parca[2:-2]
            for kelime in ic_metin.split():
                tokenlar.append((kelime, True))
        else:
            for kelime in parca.split():
                tokenlar.append((kelime, False))
    return tokenlar

def wrap_mixed_tokens(tokens: List[Tuple[str, bool]], font_reg: ImageFont.FreeTypeFont, font_bold: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw):
    space_w = draw.textbbox((0, 0), ' ', font=font_reg)[2] - draw.textbbox((0, 0), ' ', font=font_reg)[0]
    satirlar = []
    mevcut_satir = []
    mevcut_w = 0

    for kelime, is_bold in tokens:
        f = font_bold if is_bold else font_reg
        bb = draw.textbbox((0, 0), kelime, font=f)
        kelime_w = bb[2] - bb[0]

        gereken_w = kelime_w if not mevcut_satir else (mevcut_w + space_w + kelime_w)
        if gereken_w <= azami_genislik:
            mevcut_satir.append((kelime, is_bold, kelime_w))
            mevcut_w = gereken_w
        else:
            if mevcut_satir:
                satirlar.append((mevcut_satir, mevcut_w))
                mevcut_satir = [(kelime, is_bold, kelime_w)]
                mevcut_w = kelime_w
            else:
                satirlar.append(([(kelime, is_bold, kelime_w)], kelime_w))
                mevcut_satir = []
                mevcut_w = 0
    if mevcut_satir:
        satirlar.append((mevcut_satir, mevcut_w))
    return satirlar, space_w

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

def kelime_basligi_satirla(metin: str, font: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw) -> List[str]:
    bb = draw.textbbox((0, 0), metin, font=font)
    if (bb[2] - bb[0]) <= azami_genislik:
        return [metin]
    if " " in metin:
        return metin_satirla(metin, font, azami_genislik, draw)
    if "-" in metin:
        parts = metin.split("-")
        lines = []
        cur = ""
        for p in parts:
            cand = f"{cur}-{p}" if cur else p
            c_bb = draw.textbbox((0, 0), cand + "-", font=font)
            if (c_bb[2] - c_bb[0]) <= azami_genislik:
                cur = cand
            else:
                if cur:
                    lines.append(cur + "-")
                cur = p
        if cur:
            lines.append(cur)
        return lines
    return [metin]

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
    """İncelen ve zarafeti artırılan alt CTA indirme kutucuğu."""
    draw = ImageDraw.Draw(im)
    w, h = im.size
    is_916 = (format_tipi == "9:16")

    # Yükseklik azaltıldı: 9:16'da 72px (eski: 92px), 4:5'te 62px (eski: 80px)
    nav_w = 710 if is_916 else 650
    nav_h = 72 if is_916 else 62
    nav_x1 = (w - nav_w) // 2
    nav_x2 = nav_x1 + nav_w
    nav_y1 = (h - 130) if is_916 else (h - 96)
    nav_y2 = nav_y1 + nav_h
    btn_y = nav_y1 + nav_h // 2

    # Lüks yumuşak gölge
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([nav_x1 + 2, nav_y1 + 3, nav_x2 - 2, nav_y2 + 6], radius=24 if is_916 else 20, fill=(15, 3, 6, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    im.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(im)
    # Beyaz Buton Gövdesi
    draw.rounded_rectangle([nav_x1, nav_y1, nav_x2, nav_y2], radius=22 if is_916 else 18, fill="#FFFFFF", outline="#EFE8DC", width=1)

    # 1. Logo (Orantılı küçültüldü)
    logo_path = IKONLAR / "logo.png"
    logo_size = 40 if is_916 else 34
    logo_x = nav_x1 + (18 if is_916 else 14)
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=11, fill=255)
        im.paste(logo, (logo_x, btn_y - logo_size // 2), mask)

    # 2. CTA Yazısı (Dikeyde tam ortalı)
    pt_cta = 22 if is_916 else 18
    font_cta = font_al("Manrope.ttf", pt_cta, 700)
    txt_x = logo_x + logo_size + (14 if is_916 else 12)
    txt_bb = draw.textbbox((0, 0), "Ezan Plus • Ücretsiz İndirin", font=font_cta)
    txt_h = txt_bb[3] - txt_bb[1]
    draw.text((txt_x, btn_y - txt_h // 2 - txt_bb[1]), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill="#182230")

    # 3. Store İkonları
    ps_size = 22 if is_916 else 19
    ps_x = nav_x2 - (48 if is_916 else 42)
    ps_y = btn_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    # Apple İkonu
    apple_path = IKONLAR / "apple.png"
    ap_size = 20 if is_916 else 17
    if apple_path.exists():
        ap_img = Image.open(apple_path).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        ap_x = ps_x - ap_size - (15 if is_916 else 12)
        im.paste(ap_img, (ap_x, btn_y - ap_size // 2), ap_img)

    return nav_y1

# 5 Belirgin ve Farklı Renk Paleti Tanımı
PALETLER: Dict[str, dict] = {
    "yakut_kirmizi": {
        "ad": "1. Ezan Yakut Kırmızısı (İmza Kırmızı)",
        "center_rgb": (166, 33, 39),   # #A62127
        "outer_rgb": (105, 12, 18),    # #690C12
        "c_divider": "#C83840",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF8EE",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FFE8E3",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF8ED",
        "c_ref": "#FDE6BA",
        "fili_rgba": (253, 230, 186, 26),
    },
    "gece_safiri": {
        "ad": "2. Derin Gece Safiri (Midnight Navy)",
        "center_rgb": (28, 56, 92),    # #1C385C
        "outer_rgb": (12, 26, 46),     # #0C1A2E
        "c_divider": "#365D8F",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F0F6FF",
        "c_accent": "#F6D89B",
        "c_body_reg": "#DCE8F8",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#F0F5FD",
        "c_ref": "#F6D89B",
        "fili_rgba": (246, 216, 155, 26),
    },
    "mescid_zumrudu": {
        "ad": "3. Mescid Zümrüdü (Ravza Yeşili)",
        "center_rgb": (24, 72, 56),    # #184838
        "outer_rgb": (10, 36, 28),     # #0A241C
        "c_divider": "#32735C",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F2FAF6",
        "c_accent": "#FCE7B8",
        "c_body_reg": "#D8ECE3",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#F2F9F5",
        "c_ref": "#FCE7B8",
        "fili_rgba": (252, 231, 184, 26),
    },
    "sicak_kehribar": {
        "ad": "4. Sıcak Kiremit / Kehribar (Terracotta)",
        "center_rgb": (158, 68, 36),   # #9E4424
        "outer_rgb": (92, 33, 14),     # #5C210E
        "c_divider": "#BD5B35",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF9F2",
        "c_accent": "#FDE4B0",
        "c_body_reg": "#FCE6DC",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF6EE",
        "c_ref": "#FDE4B0",
        "fili_rgba": (253, 228, 176, 26),
    },
    "asil_murdum": {
        "ad": "5. Asil Mürdüm / Ametist (Royal Plum)",
        "center_rgb": (88, 32, 68),    # #582044
        "outer_rgb": (44, 12, 34),     # #2C0C22
        "c_divider": "#7C3563",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF5F8",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FCE4F0",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF5FA",
        "c_ref": "#FDE6BA",
        "fili_rgba": (253, 230, 186, 26),
    }
}

def ciz_kelime_palet(
    kelime_tr: str,
    kelime_ar: str,
    okunus: str,
    kok: str,
    lugat_anlami: str,
    hayat_dersi: str,
    ayet_ref: str,
    palet_key: str = "yakut_kirmizi",
    format_tipi: str = "9:16",
    dosya_adi: str = "kelime_test.png"
) -> Path:
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    palet = PALETLER.get(palet_key, PALETLER["yakut_kirmizi"])
    im = create_paper_background(w, h, palet["center_rgb"], palet["outer_rgb"])
    draw = ImageDraw.Draw(im)

    # 1. Alt CTA barı (inceltilmiş)
    cta_ust_y = draw_bottom_cta_bar(im, format_tipi)

    max_text_w = 880 if is_916 else 840

    # 2. Hero Başlıklar (Büyütülmüş & Minimum Sekînet Tabanı)
    target_pt = 172 if is_916 else 130
    min_pt_floor = 154 if is_916 else 118

    pt_latin = target_pt
    f_latin = font_al("Lora.ttf", pt_latin, 700)
    lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)

    max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)
    while max_line_w > max_text_w and pt_latin > min_pt_floor:
        pt_latin -= 2
        f_latin = font_al("Lora.ttf", pt_latin, 700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
        max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)

    lh_latin = int(pt_latin * 1.08)
    first_l_bb = draw.textbbox((0, 0), lines_tr[0], font=f_latin)
    last_l_bb = draw.textbbox((0, 0), lines_tr[-1], font=f_latin)
    latin_block_h = (len(lines_tr) - 1) * lh_latin + (last_l_bb[3] - first_l_bb[1])

    # Arapça Hat
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

    # Tipografi Tanımları
    pt_tag = 16 if is_916 else 14
    f_tag = font_al("Manrope.ttf", pt_tag, 600)

    pt_origin = 29 if is_916 else 23
    f_origin = font_al("Lora.ttf", pt_origin, 400)
    origin_txt = f"Arapça: {okunus}   •   Kök: {kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    oh = o_bb[3] - o_bb[1]

    # Lügat Anlamı (MIXED BOLD VE REGULAR VURGUSU)
    pt_body = 48 if is_916 else 37
    lh_body = 76 if is_916 else 58
    f_body_reg = font_al("Lora.ttf", pt_body, 400)
    f_body_bold = font_al("Lora.ttf", pt_body, 700)

    # Eğer metinde ** yoksa otomatik olarak vurucu kısmı bold yap
    islenmis_anlam = lugat_anlami
    if "**" not in islenmis_anlam:
        if ";" in islenmis_anlam:
            parcalar = islenmis_anlam.split(";")
            islenmis_anlam = f"{parcalar[0]}; **{parcalar[1].strip()}**"
        else:
            islenmis_anlam = re.sub(r'(\b\w+\b\s+\b\w+\b\s+\b\w+\b[\.!]?)$', r'**\1**', islenmis_anlam)

    body_tokens = parse_markdown_bold(islenmis_anlam)
    body_wrapped, body_space_w = wrap_mixed_tokens(body_tokens, f_body_reg, f_body_bold, max_text_w, draw)

    if len(body_wrapped) > 3:
        pt_body = 42 if is_916 else 33
        lh_body = 66 if is_916 else 52
        f_body_reg = font_al("Lora.ttf", pt_body, 400)
        f_body_bold = font_al("Lora.ttf", pt_body, 700)
        body_wrapped, body_space_w = wrap_mixed_tokens(body_tokens, f_body_reg, f_body_bold, max_text_w, draw)

    body_block_h = len(body_wrapped) * lh_body

    # Tefekkür / Hayat Dersi Alıntısı
    pt_italic = 37 if is_916 else 29
    lh_italic = 58 if is_916 else 46
    f_italic = font_al("Lora.ttf", pt_italic, 400)
    clean_alinti = hayat_dersi.strip("“”\" ")
    italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 40, draw)
    italic_block_h = len(italic_lines) * lh_italic

    # Ayet Referansı
    pt_ref = 18 if is_916 else 15
    f_ref = font_al("Manrope.ttf", pt_ref, 700)
    ref_txt = ayet_ref.upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    # 3. KESİN GÖRSEL SAFE AREA HESAPLAMASI
    gap_tr_ar = 68 if is_916 else 46
    gap_ar_origin = 58 if is_916 else 42

    top_y = 150 if is_916 else 95
    bottom_y = cta_ust_y - (45 if is_916 else 35)
    usable_h = bottom_y - top_y

    hero_visual_h = latin_block_h + gap_tr_ar + (ar_bb[3] - ar_bb[1]) + gap_ar_origin + (o_bb[3] - o_bb[1])
    fixed_content_h = 28 + hero_visual_h + body_block_h + italic_block_h + rh

    free_space = max(40, usable_h - fixed_content_h)

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
    draw.text(((w - tag_w) / 2, cur_y), tag_txt, font=f_tag, fill=palet["c_accent"])
    cur_y += 28 + pad_tag_hero

    # B) Türkçe Hero Kelime
    latin_start_y = cur_y
    for idx, line in enumerate(lines_tr):
        bb = draw.textbbox((0, 0), line, font=f_latin)
        lw = bb[2] - bb[0]
        line_y = latin_start_y + idx * lh_latin
        draw.text(((w - lw) / 2, line_y), line, font=f_latin, fill=palet["c_hero"])

    latin_bottom = latin_start_y + (len(lines_tr) - 1) * lh_latin + last_l_bb[3]

    # C) Arapça Hat
    ar_y = latin_bottom - ar_bb[1] + gap_tr_ar
    draw.text(((w - ar_w) / 2, ar_y), ar_prep_txt, font=f_arabic, fill=palet["c_arabic"])
    ar_bottom = ar_y + ar_bb[3]

    # D) Okunuş & Kök Satırı
    cur_y = ar_bottom - o_bb[1] + gap_ar_origin
    draw.text(((w - ow) / 2, cur_y), origin_txt, font=f_origin, fill=palet["c_accent"])
    cur_y += (o_bb[3] - o_bb[1]) + pad_origin_div

    # E) Narin Ayraç & Altın Elmas Noktası
    div_w = 460 if is_916 else 380
    div_x1 = (w - div_w) / 2
    div_x2 = div_x1 + div_w
    draw.line([(div_x1, cur_y), (div_x2, cur_y)], fill=palet["c_divider"], width=1)
    dot_r = 3.5 if is_916 else 3.0
    draw.ellipse([(w/2 - dot_r, cur_y - dot_r), (w/2 + dot_r, cur_y + dot_r)], fill=palet["c_accent"])
    cur_y += pad_div_body

    # F) Zarif Filigran Tırnak
    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    pt_fili = 340 if is_916 else 250
    f_fili = font_al("Lora.ttf", pt_fili, 700)

    first_line_w = body_wrapped[0][1]
    first_bx = (w - first_line_w) // 2
    fili_x = first_bx - (85 if is_916 else 65)
    fili_y = cur_y - (145 if is_916 else 105)

    fili_draw.text((fili_x, fili_y), "“", font=f_fili, fill=palet["fili_rgba"])
    im.paste(fili_layer, (0, 0), fili_layer)

    # G) Lügat Anlamı (BOLD VE REGULAR VURGULU)
    draw = ImageDraw.Draw(im)
    for line_tokens, line_w in body_wrapped:
        line_cur_x = (w - line_w) // 2
        for word, is_bold, word_w in line_tokens:
            f = f_body_bold if is_bold else f_body_reg
            c = palet["c_body_bold"] if is_bold else palet["c_body_reg"]
            draw.text((line_cur_x, cur_y), word, font=f, fill=c)
            line_cur_x += word_w + body_space_w
        cur_y += lh_body

    cur_y += pad_body_quote

    # H) Tefekkür & Hayat Dersi Alıntısı
    for line in italic_lines:
        bb = draw.textbbox((0, 0), line, font=f_italic)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_italic, fill=palet["c_italic"])
        cur_y += lh_italic

    cur_y += pad_quote_ref

    # I) Ayet Referansı
    draw.text(((w - rw) / 2, cur_y), ref_txt, font=f_ref, fill=palet["c_ref"])

    # Kaydet
    out_path = ARTIFACTS / dosya_adi
    im.save(out_path, "PNG")
    print(f"Render tamam: {out_path.name} (Palet: {palet['ad']})")
    return out_path

if __name__ == "__main__":
    # 5 Palet için Sekînet Render Testi (9:16)
    palet_anahtarlari = ["yakut_kirmizi", "gece_safiri", "mescid_zumrudu", "sicak_kehribar", "asil_murdum"]
    
    for p_key in palet_anahtarlari:
        ciz_kelime_palet(
            kelime_tr="Sekînet",
            kelime_ar="السَّكِينَةُ",
            okunus="es-Sekîne",
            kok="S-K-N (Sükûn)",
            lugat_anlami="Kalbin telaş, korku ve ıstıraptan arınarak **ilahi bir huzur ve sükûnete** kavuşması.",
            hayat_dersi="Dünya seni ne kadar sarsarsa sarssın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
            ayet_ref="Fetih Sûresi, 4. Âyet",
            palet_key=p_key,
            format_tipi="9:16",
            dosya_adi=f"palet_{p_key}_9_16.png"
        )
        ciz_kelime_palet(
            kelime_tr="Sekînet",
            kelime_ar="السَّكِينَةُ",
            okunus="es-Sekîne",
            kok="S-K-N (Sükûn)",
            lugat_anlami="Kalbin telaş, korku ve ıstıraptan arınarak **ilahi bir huzur ve sükûnete** kavuşması.",
            hayat_dersi="Dünya seni ne kadar sarsarsa sarssın; kalbine hakiki dinginliği sadece Allah'a teslimiyet indirebilir.",
            ayet_ref="Fetih Sûresi, 4. Âyet",
            palet_key=p_key,
            format_tipi="4:5",
            dosya_adi=f"palet_{p_key}_4_5.png"
        )
    print("TUM_5_PALET_TESTLERI_TAMAMLANDI")
