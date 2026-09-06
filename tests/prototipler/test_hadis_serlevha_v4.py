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


def cta_butonu_ciz(im: Image.Image, draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int = 650, h: int = 76):
    """Alt CTA butonunu (Ezan Plus logo + Ücretsiz İndirin + Store İkonları) çizer."""
    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = x1 + w
    y2 = y1 + h

    # Buton gölgesi (ultra hafif)
    btn_shadow = Image.new("RGBA", (im.width, im.height), (0, 0, 0, 0))
    bs_draw = ImageDraw.Draw(btn_shadow)
    bs_draw.rounded_rectangle([x1, y1 + 3, x2, y2 + 3], radius=h // 2, fill=(30, 20, 15, 18))
    btn_shadow = btn_shadow.filter(ImageFilter.GaussianBlur(6))
    im.paste(btn_shadow, (0, 0), btn_shadow)

    # Buton gövdesi
    yuvarlak_kose_ciz(draw, (x1, y1, x2, y2), radius=h // 2, dolgu="#FFFFFF", kenarlik="#E2D9C8", kenarlik_kalinlik=2)

    # 1. Ezan Plus Logo
    logo_yolu = Path("assets/icons/logo.png")
    logo_size = 46
    btn_mid_y = cy
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=13, fill=255)
        im.paste(logo, (x1 + 16, btn_mid_y - logo_size // 2), mask)

    # 2. Buton Metni
    font_cta = font_al(FONT_UI, 21, agirlik=700)
    tx = x1 + 16 + logo_size + 14
    # Dikey ortalama
    t_bb = draw.textbbox((0, 0), "Ezan Plus • Ücretsiz İndirin", font=font_cta)
    t_h = t_bb[3] - t_bb[1]
    draw.text((tx, btn_mid_y - t_h // 2 - t_bb[1]), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill="#182230")

    # 3. Store İkonları (Sağ tarafta)
    ps_size = 24
    ps_x = x2 - 42
    ps_y = btn_mid_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    # Apple İkonu
    apple_yolu = Path("assets/icons/apple.png")
    ap_size = 25
    ap_x = ps_x - ap_size - 18
    ap_y = btn_mid_y - ap_size // 2
    if apple_yolu.exists():
        apple_img = Image.open(apple_yolu).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        im.paste(apple_img, (ap_x, ap_y), apple_img)
    else:
        try:
            font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            bbox_ap = draw.textbbox((0, 0), "", font=font_apple)
            draw.text((ap_x, btn_mid_y - (bbox_ap[3] - bbox_ap[1]) // 2 - bbox_ap[1]), "", font=font_apple, fill="#000000")
        except Exception:
            pass


def render_hadis_karti(
    cikti_yolu: str,
    kirmizi_ton: str,
    logo_font_secimi: str = "lora_bold",  # 'lora_bold', 'manrope_bold', 'manrope_caps'
    intro_font_secimi: str = "lora_bold",  # 'lora_bold', 'manrope_bold'
):
    w, h = 1080, 1350
    im = Image.new("RGB", (w, h), "#F7F4EC")
    draw = ImageDraw.Draw(im)

    kx1, kx2 = 64, w - 64
    ky1, ky2 = 64, h - 64

    # Dış kart gölgesi
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([kx1 + 4, ky1 + 14, kx2 - 4, ky2 + 14], radius=38, fill=(30, 25, 20, 26))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    im.paste(shadow, (0, 0), shadow)

    # Ana Kart Gövdesi
    draw = ImageDraw.Draw(im)
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=36, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=2)

    # İç İnce Çerçeve & Köşe Varak Noktaları
    cp = 18
    draw.rounded_rectangle([kx1 + cp, ky1 + cp, kx2 - cp, ky2 - cp], radius=26, outline="#F0E7D8", width=1)
    for cx, cy in [(kx1 + cp, ky1 + cp), (kx2 - cp, ky1 + cp), (kx1 + cp, ky2 - cp), (kx2 - cp, ky2 - cp)]:
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="#C29B38")

    # 1. ÜST HEADER ALANI
    sol_x = kx1 + 44
    cur_y = ky1 + 38
    logo_yolu = Path("assets/icons/logo.png")
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((56, 56), Image.Resampling.LANCZOS)
        logo_bg = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
        lb_draw = ImageDraw.Draw(logo_bg)
        lb_draw.rounded_rectangle([0, 0, 60, 60], radius=17, fill="#FFFDF9", outline="#C29B38", width=2)
        mask = Image.new("L", (56, 56), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 56, 56], radius=14, fill=255)
        logo_bg.paste(logo, (2, 2), mask)
        im.paste(logo_bg, (sol_x, cur_y), logo_bg)

    # Ezan Plus Logo Yazısı Fontu (Reels ana fontu / bold)
    tx = sol_x + 74
    if logo_font_secimi == "lora_bold":
        # Reels V12 ana marka fontu: Lora Bold Title Case
        font_marka = font_al(FONT_GOVDE, 30, agirlik=700)
        draw.text((tx, cur_y + 4), "Ezan Plus", font=font_marka, fill="#1C1917")
        font_alt = font_al(FONT_UI, 13, agirlik=600)
        draw.text((tx, cur_y + 38), "SAHİH HADİS-İ ŞERİF REHBERİ", font=font_alt, fill="#8C7A6B")
    elif logo_font_secimi == "manrope_bold":
        # Manrope Bold Title Case
        font_marka = font_al(FONT_UI, 27, agirlik=800)
        draw.text((tx, cur_y + 4), "Ezan Plus", font=font_marka, fill="#1C1917")
        font_alt = font_al(FONT_UI, 13, agirlik=600)
        draw.text((tx, cur_y + 38), "SAHİH HADİS-İ ŞERİF REHBERİ", font=font_alt, fill="#8C7A6B")
    else:  # manrope_caps
        # Manrope Bold Spaced Caps
        font_marka = font_al(FONT_UI, 22, agirlik=800)
        draw.text((tx, cur_y + 6), "E Z A N   P L U S", font=font_marka, fill=kirmizi_ton)
        font_alt = font_al(FONT_UI, 13, agirlik=600)
        draw.text((tx, cur_y + 36), "SAHİH HADİS-İ ŞERİF REHBERİ", font=font_alt, fill="#8C7A6B")

    # Sağ Rozet: "HADİS-İ ŞERİF" (Pastel Soft Kırmızı)
    rozet_w = 180
    rozet_x = kx2 - 44 - rozet_w
    yuvarlak_kose_ciz(draw, (rozet_x, cur_y + 8, rozet_x + rozet_w, cur_y + 48), radius=14, dolgu=kirmizi_ton, kenarlik="#C29B38", kenarlik_kalinlik=1)
    font_rozet = font_al(FONT_UI, 16, agirlik=700)
    r_txt = "HADİS-İ ŞERİF"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    draw.text((rozet_x + (rozet_w - rw) // 2, cur_y + 15), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç Hattı
    ayrac_y = cur_y + 78
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 60, ayrac_y), (w // 2 + 60, ayrac_y)], fill="#C29B38", width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill="#C29B38")

    # 2. ALT ALANLAR & NEBEVİ ÖĞÜT
    # En alttaki CTA butonun y konumu
    cta_cy = ky2 - 68
    cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=74)

    # İnce alt ayırıcı çizgi
    alt_cizgi_y = cta_cy - 60
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    # Nebevi Öğüt Kutusu
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

    # 3. ORTA SERLEVHA KUTUSU (ARAPÇA & OKUNUŞ) & TÜRKÇE HADİS
    free_vertical = kutu_y1 - ayrac_y
    pad_ust = int((free_vertical - 486) * 0.24)
    gap = int((free_vertical - 486) * 0.38)
    box_y1 = ayrac_y + pad_ust
    box_h = 246
    box_y2 = box_y1 + box_h

    # Kutu ana gövdesi: Fildişi, altın çerçeveli
    yuvarlak_kose_ciz(draw, (box_x1, box_y1, box_x2, box_y2), radius=26, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    # Üst Taç Şeridi: Pastel Soft Kırmızı Kemer Bandı!
    tac_h = 48
    tac_mask = Image.new("L", (w, h), 0)
    tm_draw = ImageDraw.Draw(tac_mask)
    tm_draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y1 + tac_h * 2], radius=26, fill=255)
    tm_draw.rectangle([0, box_y1 + tac_h, w, h], fill=0)  # Altını kes

    tac_img = Image.new("RGB", (w, h), kirmizi_ton)
    im.paste(tac_img, (0, 0), tac_mask)

    # Altına ince altın şerit
    draw.line([(box_x1, box_y1 + tac_h), (box_x2, box_y1 + tac_h)], fill="#C29B38", width=2)

    # İntro Başlık Metni: BOLD & Hafif Gölgeli
    intro_txt = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"
    if intro_font_secimi == "lora_bold":
        font_intro = font_al(FONT_GOVDE, 23, agirlik=700)
    else:
        font_intro = font_al(FONT_UI, 22, agirlik=700)

    in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
    in_w = in_bb[2] - in_bb[0]
    in_h = in_bb[3] - in_bb[1]
    in_x = (w - in_w) // 2
    in_y = box_y1 + (tac_h - in_h) // 2 - in_bb[1] - 1

    # 1px Yumuşak Alt Gölgelendirme (Kontrast için)
    draw.text((in_x, in_y + 1), intro_txt, font=font_intro, fill=(70, 10, 15, 120))
    # Ana Beyaz Metin
    draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#FFFFFF")

    # Arapça Hat: Zengin kurumsal kırmızı (#9B1B1B)
    ar_ham = "لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ"
    font_ar = font_al(FONT_ARAPCA, 58)
    ar_gorsel = arapca_harekeli(ar_ham)
    ar_bb = draw.textbbox((0, 0), ar_gorsel, font=font_ar)
    ar_w = ar_bb[2] - ar_bb[0]
    draw.text(((w - ar_w) // 2, box_y1 + 68), ar_gorsel, font=font_ar, fill="#9B1B1B")

    # Okunuş
    okunus_txt = "“ Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn ”"
    font_okunus = font_al(FONT_GOVDE, 22)
    ok_bb = draw.textbbox((0, 0), okunus_txt, font=font_okunus)
    ok_w = ok_bb[2] - ok_bb[0]
    draw.text(((w - ok_w) // 2, box_y1 + 190), okunus_txt, font=font_okunus, fill="#5A4B42")

    # 4. TÜRKÇE HADİS & KAYNAK
    tr_y = box_y2 + gap
    tr_ham = "“ Mümin, aynı delikten iki defa ısırılmaz.\n(Aynı hataya iki kez düşmez.) ”"
    font_hadis = font_al(FONT_BASLIK, 52)
    tr_satirlar = metin_satirla(tr_ham, font_hadis, box_w, draw)
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

    # Kaydet
    im.save(cikti_yolu, quality=96)
    print(f"Başarıyla kaydedildi: {cikti_yolu}")


if __name__ == "__main__":
    import sys
    # Render edilecek 3 varyasyon:
    # 1. Pastel Soft Kırmızı (#D34549) + Reels Lora Bold Marka
    render_hadis_karti(
        "/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v4_ton1_lora_bold.png",
        kirmizi_ton="#D34549",
        logo_font_secimi="lora_bold",
        intro_font_secimi="lora_bold"
    )

    # 2. Pastel Canlı Kırmızı (#DA4C51) + Reels Lora Bold Marka
    render_hadis_karti(
        "/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v4_ton2_pastel_canli.png",
        kirmizi_ton="#DA4C51",
        logo_font_secimi="lora_bold",
        intro_font_secimi="lora_bold"
    )

    # 3. Pastel Soft Kırmızı (#D34549) + Manrope Bold Marka
    render_hadis_karti(
        "/Users/macbook/.gemini/antigravity/brain/6b30e296-9caa-49e5-be7a-db124c169b93/hadis_v4_ton3_manrope_bold.png",
        kirmizi_ton="#D34549",
        logo_font_secimi="manrope_bold",
        intro_font_secimi="manrope_bold"
    )
