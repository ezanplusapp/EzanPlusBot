"""
test_v15_resul_ve_bold.py — V15 Mizanpaj ve Tasarım Geliştirmeleri
1. Okunuş altı safe area düzeltmesi (artık kutu altına yapışmaz, 26px net nefes payı).
2. Meal kısmında önemli kelimelerin bold çizilmesi.
3. Resûlullah başlığı için 3 farklı tasarım seçeneği (Şeffaf/Çizgili, Sıcak Parşömen, Kırmızı Taç).
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from src.ayar import KOK_DIZIN
from src.uretim.kart import (
    font_al, arapca_satirla, metin_satirla, arapca_hazirla, yuvarlak_kose_ciz,
    _cta_butonu_ciz, FONT_ARAPCA, FONT_BASLIK, FONT_GOVDE, FONT_UI, FONT_BASKERVILLE,
    IKONLAR, CIKTI_DIZINI
)


def parse_markdown_bold(text: str) -> List[Tuple[str, bool]]:
    """Metindeki **bold** kısımları ayrıştırır."""
    parts = re.split(r'(\*\*.*?\*\*)', text)
    tokens = []
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            content = part[2:-2]
            for word in content.split():
                tokens.append((word, True))
        else:
            for word in part.split():
                tokens.append((word, False))
    return tokens


def wrap_mixed_tokens(tokens, font_reg, font_bold, max_w, draw):
    """Mixed regular/bold kelimeleri piksel genişliğine göre satırlara böler."""
    space_w = draw.textbbox((0, 0), ' ', font=font_reg)[2] - draw.textbbox((0, 0), ' ', font=font_reg)[0]
    lines = []
    current_line = []
    current_w = 0

    for word, is_bold in tokens:
        f = font_bold if is_bold else font_reg
        bb = draw.textbbox((0, 0), word, font=f)
        word_w = bb[2] - bb[0]

        needed_w = word_w if not current_line else (current_w + space_w + word_w)
        if needed_w <= max_w:
            current_line.append((word, is_bold, word_w))
            current_w = needed_w
        else:
            if current_line:
                lines.append((current_line, current_w))
                current_line = [(word, is_bold, word_w)]
                current_w = word_w
            else:
                lines.append(([(word, is_bold, word_w)], word_w))
                current_line = []
                current_w = 0
    if current_line:
        lines.append((current_line, current_w))
    return lines, space_w


def hadis_karti_v15(
    hadis_metni: str,
    kaynak_ravi: Optional[str] = None,
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    format_tipi: str = "4:5",
    tac_stili: str = "seffaf_cizgili",  # "seffaf_cizgili", "sicak_parcomen", "kirmizi_tac"
    cikti_adi: str = "test_v15.png"
) -> Path:
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    kirmizi_ton = "#C02128"

    im = Image.new("RGB", (w, h), "#F7F4EC")
    draw = ImageDraw.Draw(im)

    # Kenar payları
    kx1, kx2 = 64, w - 64
    ky1 = 140 if format_tipi == "9:16" else 64
    ky2 = h - (140 if format_tipi == "9:16" else 64)

    # Dış kart gölgesi
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([kx1 + 4, ky1 + 14, kx2 - 4, ky2 + 14], radius=38, fill=(30, 25, 20, 26))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    im.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(im)
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=36, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=2)

    # İç ince altın bordür ve 4 köşe altın nokta
    cp = 18
    draw.rounded_rectangle([kx1 + cp, ky1 + cp, kx2 - cp, ky2 - cp], radius=26, outline="#F0E7D8", width=1)
    for cx, cy in [(kx1 + cp, ky1 + cp), (kx2 - cp, ky1 + cp), (kx1 + cp, ky2 - cp), (kx2 - cp, ky2 - cp)]:
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="#C29B38")

    # 1. HEADER ALANI
    sol_x = kx1 + 44
    sag_x = kx2 - 44
    cur_y = ky1 + (34 if format_tipi == "9:16" else 28)
    header_h = 70
    mid_header_y = cur_y + header_h // 2
    logo_yolu = IKONLAR / "logo.png"

    # Logo
    logo_size = 68
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=16, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # Sağ Künye
    font_sub = font_al(FONT_UI, 13, agirlik=600)
    s_txt = "SAHİH HADİS-İ ŞERİF REHBERİ"
    s_bb = draw.textbbox((0, 0), s_txt, font=font_sub)
    w_sub = s_bb[2] - s_bb[0]

    font_marka = font_al(FONT_GOVDE, 39, agirlik=700)
    m_txt = "Ezan Plus"
    m_bb = draw.textbbox((0, 0), m_txt, font=font_marka)
    w_marka = m_bb[2] - m_bb[0]
    h_marka = m_bb[3] - m_bb[1]

    total_text_h = h_marka + 4 + (s_bb[3] - s_bb[1])
    start_y = mid_header_y - total_text_h // 2
    draw.text((sag_x - w_marka, start_y - m_bb[1]), m_txt, font=font_marka, fill="#1C1917")
    draw.text((sag_x - w_sub, start_y + h_marka + 8 - s_bb[1]), s_txt, font=font_sub, fill="#8C7A6B")

    # Ortada 42pt Rozet
    font_rozet = font_al(FONT_BASKERVILLE, 42, agirlik=700)
    r_txt = "HADİS-İ ŞERİF"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    pad_x = 40
    rozet_w = rw + pad_x * 2
    rozet_h = 70
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_header_y - rozet_h // 2

    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu=kirmizi_ton)
    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1
    draw.text((rx, ry + 1), r_txt, font=font_rozet, fill=(70, 10, 15, 100))
    draw.text((rx, ry), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç Hattı
    ayrac_y = cur_y + (88 if format_tipi == "9:16" else 84)
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 80, ayrac_y), (w // 2 + 80, ayrac_y)], fill="#C29B38", width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill="#C29B38")

    # 2. ALT ALANLAR & NEBEVİ ÖĞÜT & CTA BUTONU
    cta_cy = ky2 - (68 if format_tipi == "9:16" else 58)
    _cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=(74 if format_tipi == "9:16" else 66))

    alt_cizgi_y = cta_cy - (60 if format_tipi == "9:16" else 50)
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    box_w = (kx2 - kx1) - 64  # 888 px
    box_x1 = kx1 + 32
    box_x2 = kx2 - 32
    text_max_w = box_w - 44   # 844 px

    # GÜNÜN NEBEVÎ ÖĞÜDÜ
    tef_metin = (tefekkur_notu or "Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır. Hatalar tekrarlanmak için değil, ibret almak içindir.").strip()
    font_tef = font_al(FONT_BASLIK, 23 if format_tipi == "9:16" else 20)
    tef_line_h = 36 if format_tipi == "9:16" else 28
    tef_satirlar = metin_satirla(tef_metin, font_tef, box_w - 48, draw)
    kutu_h = (56 if format_tipi == "9:16" else 46) + (len(tef_satirlar) * tef_line_h) + (16 if format_tipi == "9:16" else 12)

    kutu_y2 = alt_cizgi_y - 14
    kutu_y1 = kutu_y2 - kutu_h

    yuvarlak_kose_ciz(draw, (box_x1, kutu_y1, box_x2, kutu_y2), radius=20, dolgu="#F9F6EE", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.rounded_rectangle([box_x1, kutu_y1, box_x1 + 6, kutu_y2], radius=3, fill="#C29B38")
    draw.ellipse([box_x1 + 24, kutu_y1 + (24 if format_tipi == "9:16" else 18), box_x1 + 32, kutu_y1 + (32 if format_tipi == "9:16" else 26)], fill="#C29B38")
    draw.text((box_x1 + 42, kutu_y1 + (18 if format_tipi == "9:16" else 14)), "GÜNÜN NEBEVÎ ÖĞÜDÜ", font=font_al(FONT_UI, 19 if format_tipi == "9:16" else 17, agirlik=700), fill="#B45309")

    ty = kutu_y1 + (56 if format_tipi == "9:16" else 46)
    for sat in tef_satirlar:
        draw.text((box_x1 + 24, ty), sat, font=font_tef, fill="#292524")
        ty += tef_line_h

    free_vertical = kutu_y1 - ayrac_y

    # 3. TÜRKÇE HADİS MEALİ (MIXED BOLD VE REGULAR DESTEĞİ)
    temiz_hadis = hadis_metni.strip("“”\"' ")
    hadis_len = len(re.sub(r'\*\*', '', temiz_hadis))
    if format_tipi == "9:16":
        font_hadis_boyut = 54 if hadis_len < 90 else (48 if hadis_len < 160 else 42)
    else:
        font_hadis_boyut = 50 if hadis_len < 90 else (46 if hadis_len < 160 else 41)

    font_hadis_reg = font_al(FONT_BASLIK, font_hadis_boyut, agirlik=400)
    font_hadis_bold = font_al(FONT_BASLIK, font_hadis_boyut, agirlik=700)

    meal_tokens = parse_markdown_bold(temiz_hadis)
    tr_wrapped_lines, space_w = wrap_mixed_tokens(meal_tokens, font_hadis_reg, font_hadis_bold, box_w - 30, draw)
    tr_line_h = int(font_hadis_boyut * 1.44)
    tr_toplam_h = len(tr_wrapped_lines) * tr_line_h

    # Kaynak Rozeti
    raw_kaynak = (kaynak_ravi or "Buhârî ve Müslim").strip()
    kaynak_metni = re.split(r'[\.;,]?\s*Ayrıca bkz?[\.:]?', raw_kaynak, flags=re.IGNORECASE)[0].strip() or raw_kaynak
    max_badge_w = box_w - 60
    font_k_pt = 24 if format_tipi == "9:16" else 22
    font_kaynak = font_al(FONT_BASLIK, font_k_pt)
    kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    while (kw + 52) > max_badge_w and font_k_pt > 16:
        font_k_pt -= 1
        font_kaynak = font_al(FONT_BASLIK, font_k_pt)
        kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    kaynak_h = 40 if format_tipi == "4:5" else 44

    # 4. SERLEVHA ÖLÇÜLERİ VE KUSURSUZ SAFE AREA
    tac_h = 48 if format_tipi == "9:16" else 42
    pad_ic_ust = 22 if format_tipi == "9:16" else 16
    pad_ic_alt = 30 if format_tipi == "9:16" else 26  # Alt safe area (kutu altına asla yapışmaz!)

    ok_gosterim = f"“ {ok_ham} ”" if (ok_ham := (arapca_okunus or "").strip("“”\"'{}[] ")) else ""
    font_okunus = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 18)
    ok_satirlar = metin_satirla(ok_gosterim, font_okunus, box_w - 60, draw) if ok_gosterim else []
    ok_line_h = 32 if format_tipi == "9:16" else 25
    ok_toplam_h = len(ok_satirlar) * ok_line_h if ok_satirlar else 0
    gap_ar_ok = (20 if format_tipi == "9:16" else 16) if ok_satirlar else 0

    ar_ham = (arapca_metin or "لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ").strip()
    ar_len = len(ar_ham)
    if format_tipi == "9:16":
        max_pt = 86 if ar_len < 60 else (78 if ar_len < 120 else 74)
        min_pt = 56
    else:
        max_pt = 66 if ar_len < 60 else (58 if ar_len < 120 else 49)
        min_pt = 44

    font_ar_boyut = min_pt
    ar_satirlar = []
    for test_pt in range(max_pt, min_pt - 1, -2):
        f_test = font_al(FONT_ARAPCA, test_pt)
        sats = arapca_satirla(ar_ham, f_test, text_max_w, draw)
        if not sats:
            continue
        max_line_w = max(draw.textbbox((0, 0), s, font=f_test)[2] - draw.textbbox((0, 0), s, font=f_test)[0] for s in sats)
        if max_line_w > text_max_w:
            continue
        max_allowed = 4 if format_tipi == "9:16" else 3
        if len(sats) > max_allowed:
            continue

        test_line_h = int(test_pt * (1.40 if format_tipi == "9:16" else 1.36))
        sim_ar_h = len(sats) * test_line_h + int(test_pt * 0.25)
        test_box_s_h = tac_h + pad_ic_ust + sim_ar_h + gap_ar_ok + ok_toplam_h + pad_ic_alt
        sim_kalan = free_vertical - (test_box_s_h + tr_toplam_h + kaynak_h)
        min_kalan = 50 if format_tipi == "9:16" else 35
        if sim_kalan >= min_kalan:
            font_ar_boyut = test_pt
            ar_satirlar = sats
            break

    if not ar_satirlar:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)
        ar_satirlar = arapca_satirla(ar_ham, font_ar, text_max_w, draw)
    else:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)

    ar_line_h = int(font_ar_boyut * (1.40 if format_tipi == "9:16" else 1.36))

    # Kutu Gerçek Yüksekliği ve Dikey Flex Dağılımı
    temp_ar_y = 100
    temp_last_ar_bottom = temp_ar_y
    for asat in ar_satirlar:
        as_bb = draw.textbbox((0, 0), asat, font=font_ar)
        as_w = as_bb[2] - as_bb[0]
        line_x = (w - as_w) // 2
        bb_actual = draw.textbbox((line_x, temp_ar_y), asat, font=font_ar)
        temp_last_ar_bottom = max(temp_last_ar_bottom, bb_actual[3])
        temp_ar_y += ar_line_h

    if ok_satirlar:
        temp_ok_y = max(temp_ar_y, temp_last_ar_bottom + (18 if format_tipi == "9:16" else 14))
        temp_ok_bottom = temp_ok_y
        for osat in ok_satirlar:
            o_bb = draw.textbbox(((w - 100)//2, temp_ok_bottom), osat, font=font_okunus)
            temp_ok_bottom = max(temp_ok_bottom + ok_line_h, o_bb[3])
        final_icerik_bottom = temp_ok_bottom
    else:
        final_icerik_bottom = temp_last_ar_bottom

    net_icerik_h = final_icerik_bottom - 100
    # Kutu yüksekliğini kesin formülle garanti ediyoruz
    box_s_h = tac_h + pad_ic_ust + net_icerik_h + pad_ic_alt

    toplam_icerik_h = box_s_h + tr_toplam_h + kaynak_h
    kalan_bosluk = max(35, free_vertical - toplam_icerik_h)

    if format_tipi == "9:16":
        pad_ust = int(kalan_bosluk * 0.26)
        gap_kutu_tr = int(kalan_bosluk * 0.36)
        gap_tr_kaynak = 30
    else:
        pad_ust = min(35, int(kalan_bosluk * 0.18))
        gap_kutu_tr = min(60, int(kalan_bosluk * 0.44))
        gap_tr_kaynak = 20

    box_s_y1 = ayrac_y + pad_ust
    box_s_y2 = box_s_y1 + box_s_h

    # SERLEVHA KUTUSUNU ÇİZ
    yuvarlak_kose_ciz(draw, (box_x1, box_s_y1, box_x2, box_s_y2), radius=24, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    intro_txt = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"

    # --- TAÇ STİLİ UYGULAMASI ---
    if tac_stili == "kirmizi_tac":
        # Eski Kırmızı Taç
        tac_mask = Image.new("L", (w, h), 0)
        tm_draw = ImageDraw.Draw(tac_mask)
        tm_draw.rounded_rectangle([box_x1, box_s_y1, box_x2, box_s_y1 + tac_h * 2], radius=24, fill=255)
        tm_draw.rectangle([0, box_s_y1 + tac_h, w, h], fill=0)

        tac_img = Image.new("RGB", (w, h), kirmizi_ton)
        im.paste(tac_img, (0, 0), tac_mask)
        draw.line([(box_x1, box_s_y1 + tac_h), (box_x2, box_s_y1 + tac_h)], fill="#C29B38", width=2)

        font_intro = font_al(FONT_GOVDE, 24 if format_tipi == "9:16" else 20, agirlik=700)
        in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
        in_w, in_h = in_bb[2] - in_bb[0], in_bb[3] - in_bb[1]
        in_x = (w - in_w) // 2 - in_bb[0]
        in_y = box_s_y1 + (tac_h - in_h) // 2 - in_bb[1] + 1
        draw.text((in_x, in_y + 1), intro_txt, font=font_intro, fill=(70, 10, 15, 120))
        draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#FFFFFF")

    elif tac_stili == "sicak_parcomen":
        # Seçenek 2: Sıcak Parşömen / Krem Zeminli Taç (Kırmızı yok, pastel & soft)
        tac_mask = Image.new("L", (w, h), 0)
        tm_draw = ImageDraw.Draw(tac_mask)
        tm_draw.rounded_rectangle([box_x1, box_s_y1, box_x2, box_s_y1 + tac_h * 2], radius=24, fill=255)
        tm_draw.rectangle([0, box_s_y1 + tac_h, w, h], fill=0)

        tac_img = Image.new("RGB", (w, h), "#F5EFE3")
        im.paste(tac_img, (0, 0), tac_mask)
        draw.line([(box_x1, box_s_y1 + tac_h), (box_x2, box_s_y1 + tac_h)], fill="#E2D7C3", width=1)
        draw.line([(w // 2 - 40, box_s_y1 + tac_h), (w // 2 + 40, box_s_y1 + tac_h)], fill="#C29B38", width=2)

        font_intro = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 19, agirlik=700)
        in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
        in_w, in_h = in_bb[2] - in_bb[0], in_bb[3] - in_bb[1]
        in_x = (w - in_w) // 2 - in_bb[0]
        in_y = box_s_y1 + (tac_h - in_h) // 2 - in_bb[1] + 1
        draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#8B1D24")

    else:  # "seffaf_cizgili" - Klasik Mushaf Tezhip & Zarif Çizgili (En Ferah & Asil)
        # Kırmızı zemin YOK! Kutu tek parça fildişi.
        font_intro = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 19, agirlik=700)
        in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
        in_w, in_h = in_bb[2] - in_bb[0], in_bb[3] - in_bb[1]
        in_x = (w - in_w) // 2 - in_bb[0]
        in_y = box_s_y1 + (tac_h - in_h) // 2 - in_bb[1] + 4

        line_w = 60
        y_cizgi = box_s_y1 + tac_h // 2 + 2
        draw.line([(in_x - line_w - 20, y_cizgi), (in_x - 20, y_cizgi)], fill="#C29B38", width=1)
        draw.ellipse([in_x - 14, y_cizgi - 3, in_x - 8, y_cizgi + 3], fill="#C29B38")

        draw.line([(in_x + in_w + 20, y_cizgi), (in_x + in_w + line_w + 20, y_cizgi)], fill="#C29B38", width=1)
        draw.ellipse([in_x + in_w + 8, y_cizgi - 3, in_x + in_w + 14, y_cizgi + 3], fill="#C29B38")

        draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#9B1B1B")
        draw.line([(box_x1 + 30, box_s_y1 + tac_h), (box_x2 - 30, box_s_y1 + tac_h)], fill="#F0E8D9", width=1)

    # Arapça Metin Çizimi
    ar_y = box_s_y1 + tac_h + pad_ic_ust
    last_ar_bottom = ar_y
    for asat in ar_satirlar:
        as_bb = draw.textbbox((0, 0), asat, font=font_ar)
        as_w = as_bb[2] - as_bb[0]
        line_x = (w - as_w) // 2
        draw.text((line_x, ar_y), asat, font=font_ar, fill="#9B1B1B")
        bb_actual = draw.textbbox((line_x, ar_y), asat, font=font_ar)
        last_ar_bottom = max(last_ar_bottom, bb_actual[3])
        ar_y += ar_line_h

    # Latin Okunuş Çizimi
    actual_ok_bottom = last_ar_bottom
    if ok_satirlar:
        ok_y = max(ar_y, last_ar_bottom + (18 if format_tipi == "9:16" else 14))
        for osat in ok_satirlar:
            o_bb = draw.textbbox((0, 0), osat, font=font_okunus)
            o_w = o_bb[2] - o_bb[0]
            draw.text(((w - o_w) // 2, ok_y), osat, font=font_okunus, fill="#5A4B42")
            o_actual = draw.textbbox(((w - o_w) // 2, ok_y), osat, font=font_okunus)
            actual_ok_bottom = max(actual_ok_bottom, o_actual[3])
            ok_y += ok_line_h

    # Safe Area Teşhis Çıktısı
    gercek_alt_pay = box_s_y2 - actual_ok_bottom
    print(f"[{tac_stili} | {format_tipi}] Okunuş altı gerçek safe area: {gercek_alt_pay} px (Hedef: ~{pad_ic_alt} px)")

    # 6. TÜRKÇE HADİS & TAŞMA KORUMALI TIRNAK FİLİGRANI
    tr_y = box_s_y2 + gap_kutu_tr
    first_tw = tr_wrapped_lines[0][1]
    first_tx = (w - first_tw) // 2

    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    font_fili_pt = 140 if format_tipi == "9:16" else 110
    font_fili = font_al(FONT_BASLIK, font_fili_pt, agirlik=700)
    fx = max(kx1 + 48, first_tx - 24)
    fy = max(box_s_y2 + 8, tr_y - (45 if format_tipi == "9:16" else 35))
    fili_draw.text((fx, fy), "“", font=font_fili, fill=(192, 33, 40, 24))
    im.paste(fili_layer, (0, 0), fili_layer)

    # TÜRKÇE MEAL ÇİZİMİ (BOLD VE REGULAR KELİMELER KUSURSUZ YANYANA)
    draw = ImageDraw.Draw(im)
    for line_tokens, line_w in tr_wrapped_lines:
        cur_x = (w - line_w) // 2
        for word, is_bold, word_w in line_tokens:
            f = font_hadis_bold if is_bold else font_hadis_reg
            fill_c = "#111827" if is_bold else "#1C1917"
            draw.text((cur_x, tr_y), word, font=f, fill=fill_c)
            cur_x += word_w + space_w
        tr_y += tr_line_h

    tr_y += gap_tr_kaynak

    # Kaynak Rozeti
    kx = (w - kw) // 2
    badge_x1 = max(kx1 + 24, kx - 26)
    badge_x2 = min(kx2 - 24, kx + kw + 26)
    yuvarlak_kose_ciz(draw, (badge_x1, tr_y - 6, badge_x2, tr_y + 34), radius=12, dolgu="#FFFDF9", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.text((kx, tr_y - 1), kaynak_metni, font=font_kaynak, fill="#B45309")

    cikti_yolu = CIKTI_DIZINI / cikti_adi
    im.save(str(cikti_yolu), quality=96)
    return cikti_yolu
