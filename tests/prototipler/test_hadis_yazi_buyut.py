from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display
from src.uretim.kart import (
    font_al,
    metin_satirla,
    yuvarlak_kose_ciz,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
    FONT_ARAPCA,
)

reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False, "support_ligatures": True})

def arapca_harekeli(text):
    if not text:
        return ""
    return get_display(reshaper.reshape(text))

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

def cta_butonu_ciz(im: Image.Image, draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int = 670, h: int = 74):
    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = x1 + w
    y2 = y1 + h

    btn_shadow = Image.new("RGBA", (im.width, im.height), (0, 0, 0, 0))
    bs_draw = ImageDraw.Draw(btn_shadow)
    bs_draw.rounded_rectangle([x1, y1 + 3, x2, y2 + 3], radius=h // 2, fill=(30, 20, 15, 18))
    btn_shadow = btn_shadow.filter(ImageFilter.GaussianBlur(6))
    im.paste(btn_shadow, (0, 0), btn_shadow)

    yuvarlak_kose_ciz(draw, (x1, y1, x2, y2), radius=h // 2, dolgu="#FFFFFF", kenarlik="#E2D9C8", kenarlik_kalinlik=2)

    logo_yolu = Path("assets/icons/logo.png")
    logo_size = 46
    btn_mid_y = cy
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=13, fill=255)
        im.paste(logo, (x1 + 16, btn_mid_y - logo_size // 2), mask)

    font_cta = font_al(FONT_UI, 21, agirlik=700)
    tx = x1 + 16 + logo_size + 14
    t_bb = draw.textbbox((0, 0), "Ezan Plus • Ücretsiz İndirin", font=font_cta)
    t_h = t_bb[3] - t_bb[1]
    draw.text((tx, btn_mid_y - t_h // 2 - t_bb[1]), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill="#182230")

    ps_size = 24
    ps_x = x2 - 42
    ps_y = btn_mid_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    apple_yolu = Path("assets/icons/apple.png")
    ap_size = 25
    ap_x = ps_x - ap_size - 18
    ap_y = btn_mid_y - ap_size // 2
    if apple_yolu.exists():
        apple_img = Image.open(apple_yolu).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        im.paste(apple_img, (ap_x, ap_y), apple_img)

def render(cikti_yolu, yazi_pt=32):
    w, h = 1080, 1350
    kirmizi_ton = "#E2585D"
    im = Image.new("RGB", (w, h), "#F7F4EC")
    draw = ImageDraw.Draw(im)

    kx1, kx2 = 64, w - 64
    ky1, ky2 = 64, h - 64

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([kx1 + 4, ky1 + 14, kx2 - 4, ky2 + 14], radius=38, fill=(30, 25, 20, 26))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    im.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(im)
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=36, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=2)

    cp = 18
    draw.rounded_rectangle([kx1 + cp, ky1 + cp, kx2 - cp, ky2 - cp], radius=26, outline="#F0E7D8", width=1)
    for cx, cy in [(kx1 + cp, ky1 + cp), (kx2 - cp, ky1 + cp), (kx1 + cp, ky2 - cp), (kx2 - cp, ky2 - cp)]:
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="#C29B38")

    # 1. HEADER ALANI
    sol_x = kx1 + 44
    sag_x = kx2 - 44
    cur_y = ky1 + 34
    header_h = 62
    mid_header_y = cur_y + header_h // 2
    logo_yolu = Path("assets/icons/logo.png")

    # A) EN SOLDA LOGO
    logo_size = 58
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=15, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # B) EN SAĞDA "EZAN PLUS" + "SAHİH HADİS-İ ŞERİF REHBERİ" (Aynı genişlikte blok)
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

    # C) ORTADA: YAZISI GERÇEKTEN BÜYÜTÜLMÜŞ "HADİS-İ ŞERİF" ROZETİ!
    font_rozet = font_al(FONT_UI, yazi_pt, agirlik=800)
    r_txt = "HADİS-İ ŞERİF"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    # Rozet boyutunu yazının büyüklüğüne göre tam dengeli saralım:
    pad_x = 44
    rozet_w = rw + pad_x * 2
    rozet_h = max(56, rh + 22)
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_header_y - rozet_h // 2

    # GOLD ÇERÇEVE YOK! Saf pastel soft kırmızı zemin
    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu=kirmizi_ton)

    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1  # Optik dengeleme

    draw.text((rx, ry + 1), r_txt, font=font_rozet, fill=(70, 10, 15, 100))
    draw.text((rx, ry), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç Hattı
    ayrac_y = cur_y + 82
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 80, ayrac_y), (w // 2 + 80, ayrac_y)], fill="#C29B38", width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill="#C29B38")

    # 2. ALT ALANLAR & NEBEVİ ÖĞÜT
    cta_cy = ky2 - 68
    cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=74)

    alt_cizgi_y = cta_cy - 60
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    box_w = (kx2 - kx1) - 80
    box_x1 = kx1 + 40
    box_x2 = kx2 - 40
    kutu_y2 = alt_cizgi_y - 18
    kutu_h = 162
    kutu_y1 = kutu_y2 - kutu_h
    yuvarlak_kose_ciz(draw, (box_x1, kutu_y1, box_x2, kutu_y2), radius=22, dolgu="#F9F6EE", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.rounded_rectangle([box_x1, kutu_y1, box_x1 + 6, kutu_y2], radius=3, fill="#C29B38")
    draw.ellipse([box_x1 + 24, kutu_y1 + 24, box_x1 + 32, kutu_y1 + 32], fill="#C29B38")
    draw.text((box_x1 + 42, kutu_y1 + 18), "GÜNÜN NEBEVÎ ÖĞÜDÜ", font=font_al(FONT_UI, 19, agirlik=700), fill="#B45309")

    tef_metin = "Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır. Hatalar tekrarlanmak için değil, ibret almak içindir."
    font_tef = font_al(FONT_BASLIK, 23)
    tef_satirlar = metin_satirla(tef_metin, font_tef, box_w - 48, draw)
    ty = kutu_y1 + 56
    for sat in tef_satirlar:
        draw.text((box_x1 + 24, ty), sat, font=font_tef, fill="#292524")
        ty += 36

    # 3. ORTA SERLEVHA KUTUSU (ARAPÇA & OKUNUŞ)
    free_vertical = kutu_y1 - ayrac_y
    pad_ust = int((free_vertical - 486) * 0.24)
    gap = int((free_vertical - 486) * 0.38)
    box_y1 = ayrac_y + pad_ust
    box_h = 246
    box_y2 = box_y1 + box_h

    yuvarlak_kose_ciz(draw, (box_x1, box_y1, box_x2, box_y2), radius=26, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    tac_h = 48
    tac_mask = Image.new("L", (w, h), 0)
    tm_draw = ImageDraw.Draw(tac_mask)
    tm_draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y1 + tac_h * 2], radius=26, fill=255)
    tm_draw.rectangle([0, box_y1 + tac_h, w, h], fill=0)

    tac_img = Image.new("RGB", (w, h), kirmizi_ton)
    im.paste(tac_img, (0, 0), tac_mask)
    draw.line([(box_x1, box_y1 + tac_h), (box_x2, box_y1 + tac_h)], fill="#C29B38", width=2)

    intro_txt = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"
    font_intro = font_al(FONT_GOVDE, 23, agirlik=700)
    in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
    in_w = in_bb[2] - in_bb[0]
    in_h = in_bb[3] - in_bb[1]
    in_x = (w - in_w) // 2 - in_bb[0]
    in_y = box_y1 + (tac_h - in_h) // 2 - in_bb[1] + 2

    draw.text((in_x, in_y + 1), intro_txt, font=font_intro, fill=(70, 10, 15, 120))
    draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#FFFFFF")

    ar_ham = "لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ"
    font_ar = font_al(FONT_ARAPCA, 58)
    ar_gorsel = arapca_harekeli(ar_ham)
    ar_bb = draw.textbbox((0, 0), ar_gorsel, font=font_ar)
    ar_w = ar_bb[2] - ar_bb[0]
    draw.text(((w - ar_w) // 2, box_y1 + 68), ar_gorsel, font=font_ar, fill="#9B1B1B")

    okunus_txt = "“ Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn ”"
    font_okunus = font_al(FONT_GOVDE, 22)
    ok_bb = draw.textbbox((0, 0), okunus_txt, font=font_okunus)
    ok_w = ok_bb[2] - ok_bb[0]
    draw.text(((w - ok_w) // 2, box_y1 + 190), okunus_txt, font=font_okunus, fill="#5A4B42")

    # 4. TÜRKÇE HADİS: ARKA PLANDA ZARİF KIRMIZI DEV TIRNAK FİLİGRANI!
    tr_y = box_y2 + gap
    tr_ham = "Mümin, aynı delikten iki defa ısırılmaz.\n(Aynı hataya iki kez düşmez.)"
    font_hadis = font_al(FONT_BASLIK, 52)
    tr_satirlar = metin_satirla(tr_ham, font_hadis, box_w, draw)
    first_tw = draw.textbbox((0, 0), tr_satirlar[0], font=font_hadis)[2] - draw.textbbox((0, 0), tr_satirlar[0], font=font_hadis)[0]
    first_tx = (w - first_tw) // 2

    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    font_fili = font_al(FONT_BASLIK, 165, agirlik=700)
    f_bb = fili_draw.textbbox((0, 0), "“", font=font_fili)
    fw = f_bb[2] - f_bb[0]
    fx = first_tx - fw + 10
    fy = tr_y - 82
    fili_draw.text((fx, fy), "“", font=font_fili, fill=(226, 88, 93, 34))
    im.paste(fili_layer, (0, 0), fili_layer)

    draw = ImageDraw.Draw(im)
    for sat in tr_satirlar:
        tw = draw.textbbox((0, 0), sat, font=font_hadis)[2] - draw.textbbox((0, 0), sat, font=font_hadis)[0]
        draw.text(((w - tw) // 2, tr_y), sat, font=font_hadis, fill="#1C1917")
        tr_y += 72
    tr_y += 24

    kaynak_txt = "Buhârî, Edeb, 83 • Müslim, Zühd, 63"
    font_kaynak = font_al(FONT_BASLIK, 23)
    kw = draw.textbbox((0, 0), kaynak_txt, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_txt, font=font_kaynak)[0]
    kx = (w - kw) // 2
    yuvarlak_kose_ciz(draw, (kx - 26, tr_y - 6, kx + kw + 26, tr_y + 36), radius=12, dolgu="#FFFDF9", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.text((kx, tr_y), kaynak_txt, font=font_kaynak, fill="#B45309")

    im.save(cikti_yolu, quality=96)
    print("Kaydedildi:", cikti_yolu)


if __name__ == "__main__":
    # Render 3 font boyutu:
    # 1. 28pt (Büyük & Dengeli)
    render("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v8_yazi_28pt.png", yazi_pt=28)

    # 2. 32pt (Heybetli & Tok)
    render("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v8_yazi_32pt.png", yazi_pt=32)

    # 3. 36pt (Dopdolu & Manşet Gücünde)
    render("/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v8_yazi_36pt.png", yazi_pt=36)
