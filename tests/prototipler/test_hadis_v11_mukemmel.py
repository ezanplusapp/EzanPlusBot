import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.ayar import KOK_DIZIN
from src.uretim.kart import (
    FONTLAR,
    IKONLAR,
    CIKTI_DIZINI,
    font_al,
    arapca_hazirla,
    arapca_satirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    _cta_butonu_ciz,
    FONT_BASKERVILLE,
    FONT_ARAPCA,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
)

def hadis_karti_ciz_v11(
    hadis_metni: str,
    kaynak_ravi: str,
    tefekkur_notu: str,
    arapca_metin: str,
    arapca_okunus: str,
    format_tipi: str = "4:5",
    cikti_dosya_adi: str = "hadis_v11_test.png",
) -> Path:
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    kirmizi_ton = "#E2585D"  # Soft pastel kırmızı

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

    # 1. HEADER (SOL: 66x66 LOGO | ORTA: BASKERVILLE BOLD 36pt | SAĞ: EZAN PLUS)
    sol_x = kx1 + 44
    sag_x = kx2 - 44
    cur_y = ky1 + 34
    header_h = 66
    mid_header_y = cur_y + header_h // 2
    logo_yolu = IKONLAR / "logo.png"

    # Logo
    logo_size = 66
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=16, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # Sağ Marka Yazısı
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

    # Orta Rozet (Baskerville Bold 36pt)
    font_rozet = font_al(FONT_BASKERVILLE, 36, agirlik=700)
    r_txt = "HADİS-İ ŞERİF"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    pad_x = 44
    rozet_w = rw + pad_x * 2
    rozet_h = 66
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_header_y - rozet_h // 2

    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu=kirmizi_ton)
    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1
    draw.text((rx, ry + 1), r_txt, font=font_rozet, fill=(70, 10, 15, 100))
    draw.text((rx, ry), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç
    ayrac_y = cur_y + 86
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 80, ayrac_y), (w // 2 + 80, ayrac_y)], fill="#C29B38", width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill="#C29B38")

    # 2. ALT ALAN: CTA BUTONU & NEBEVÎ ÖĞÜT
    cta_cy = ky2 - 68
    _cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=74)

    alt_cizgi_y = cta_cy - 60
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    box_w = (kx2 - kx1) - 80
    box_x1 = kx1 + 40
    box_x2 = kx2 - 40

    tef_metin = tefekkur_notu.strip()
    font_tef = font_al(FONT_BASLIK, 24 if format_tipi == "9:16" else 23)
    tef_satirlar = metin_satirla(tef_metin, font_tef, box_w - 48, draw)
    tef_line_h = 38 if format_tipi == "9:16" else 36
    kutu_h = 56 + (len(tef_satirlar) * tef_line_h) + 16

    kutu_y2 = alt_cizgi_y - 18
    kutu_y1 = kutu_y2 - kutu_h

    yuvarlak_kose_ciz(draw, (box_x1, kutu_y1, box_x2, kutu_y2), radius=22, dolgu="#F9F6EE", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.rounded_rectangle([box_x1, kutu_y1, box_x1 + 6, kutu_y2], radius=3, fill="#C29B38")
    draw.ellipse([box_x1 + 24, kutu_y1 + 24, box_x1 + 32, kutu_y1 + 32], fill="#C29B38")
    draw.text((box_x1 + 42, kutu_y1 + 18), "GÜNÜN NEBEVÎ ÖĞÜDÜ", font=font_al(FONT_UI, 19, agirlik=700), fill="#B45309")

    ty = kutu_y1 + 56
    for sat in tef_satirlar:
        draw.text((box_x1 + 24, ty), sat, font=font_tef, fill="#292524")
        ty += tef_line_h

    # 3. İÇERİK METİNLERİ VE GEREKEN BOYUTLAR
    # A) Arapça Hazırlığı
    ar_ham = arapca_metin.strip()
    if len(ar_ham) < 40:
        font_ar_boyut = 64 if format_tipi == "9:16" else 62
    elif len(ar_ham) < 90:
        font_ar_boyut = 54 if format_tipi == "9:16" else 52
    else:
        font_ar_boyut = 46 if format_tipi == "9:16" else 44
    font_ar = font_al(FONT_ARAPCA, font_ar_boyut)
    ar_satirlar = arapca_satirla(ar_ham, font_ar, box_w - 60, draw)
    ar_line_h = int(font_ar_boyut * 1.44)
    ar_toplam_h = len(ar_satirlar) * ar_line_h

    # B) Latin Okunuş Hazırlığı
    ok_ham = arapca_okunus.strip("“”\"'{}[] ")
    if ok_ham:
        ok_gosterim = f"“ {ok_ham} ”"
    else:
        ok_gosterim = ""
    font_okunus = font_al(FONT_GOVDE, 24 if format_tipi == "9:16" else 22)
    ok_satirlar = metin_satirla(ok_gosterim, font_okunus, box_w - 64, draw) if ok_gosterim else []
    ok_line_h = 36 if format_tipi == "9:16" else 32
    ok_toplam_h = len(ok_satirlar) * ok_line_h if ok_satirlar else 0

    # C) Dinamik Serlevha Kutu Yüksekliği
    tac_h = 48
    pad_ic_ust = 26
    gap_ar_ok = 26 if ok_satirlar else 0
    pad_ic_alt = 26
    box_s_h = tac_h + pad_ic_ust + ar_toplam_h + gap_ar_ok + ok_toplam_h + pad_ic_alt
    box_s_h = max(260, box_s_h)

    # D) Türkçe Hadis ve Kaynak Hazırlığı
    temiz_hadis = hadis_metni.strip("“”\"' ")
    hadis_len = len(temiz_hadis)
    if format_tipi == "9:16":
        font_hadis_boyut = 54 if hadis_len < 90 else (48 if hadis_len < 160 else 40)
    else:
        font_hadis_boyut = 50 if hadis_len < 90 else (44 if hadis_len < 160 else 36)
    font_hadis = font_al(FONT_BASLIK, font_hadis_boyut)
    tr_satirlar = metin_satirla(temiz_hadis, font_hadis, box_w - 30, draw)
    tr_line_h = int(font_hadis_boyut * 1.44)
    tr_toplam_h = len(tr_satirlar) * tr_line_h

    kaynak_metni = kaynak_ravi.strip()
    font_kaynak = font_al(FONT_BASLIK, 24 if format_tipi == "9:16" else 23)
    kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    kaynak_h = 44

    # E) Dikey Alan Dağıtımı (Optik Dengeli Flex Ortalama)
    free_vertical = kutu_y1 - ayrac_y
    toplam_icerik_h = box_s_h + tr_toplam_h + kaynak_h
    kalan_bosluk = max(40, free_vertical - toplam_icerik_h)

    if format_tipi == "9:16":
        pad_ust = int(kalan_bosluk * 0.26)
        gap_kutu_tr = int(kalan_bosluk * 0.36)
        gap_tr_kaynak = 30
    else:
        pad_ust = min(40, int(kalan_bosluk * 0.18))
        gap_kutu_tr = min(75, int(kalan_bosluk * 0.40))
        gap_tr_kaynak = 20

    box_s_y1 = ayrac_y + pad_ust
    box_s_y2 = box_s_y1 + box_s_h

    # SERLEVHA KUTUSUNU ÇİZ
    yuvarlak_kose_ciz(draw, (box_x1, box_s_y1, box_x2, box_s_y2), radius=26, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    # Kutu Üst Kırmızı Taç
    tac_mask = Image.new("L", (w, h), 0)
    tm_draw = ImageDraw.Draw(tac_mask)
    tm_draw.rounded_rectangle([box_x1, box_s_y1, box_x2, box_s_y1 + tac_h * 2], radius=26, fill=255)
    tm_draw.rectangle([0, box_s_y1 + tac_h, w, h], fill=0)

    tac_img = Image.new("RGB", (w, h), kirmizi_ton)
    im.paste(tac_img, (0, 0), tac_mask)
    draw.line([(box_x1, box_s_y1 + tac_h), (box_x2, box_s_y1 + tac_h)], fill="#C29B38", width=2)

    intro_txt = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"
    font_intro = font_al(FONT_GOVDE, 24 if format_tipi == "9:16" else 23, agirlik=700)
    in_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
    in_w = in_bb[2] - in_bb[0]
    in_h = in_bb[3] - in_bb[1]
    in_x = (w - in_w) // 2 - in_bb[0]
    in_y = box_s_y1 + (tac_h - in_h) // 2 - in_bb[1] + 2

    draw.text((in_x, in_y + 1), intro_txt, font=font_intro, fill=(70, 10, 15, 120))
    draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#FFFFFF")

    # Arapça Metin Çizimi
    ar_y = box_s_y1 + tac_h + pad_ic_ust
    for asat in ar_satirlar:
        as_bb = draw.textbbox((0, 0), asat, font=font_ar)
        as_w = as_bb[2] - as_bb[0]
        draw.text(((w - as_w) // 2, ar_y), asat, font=font_ar, fill="#9B1B1B")
        ar_y += ar_line_h

    # Latin Okunuş Çizimi
    if ok_satirlar:
        ok_y = ar_y + gap_ar_ok - 8
        for osat in ok_satirlar:
            o_bb = draw.textbbox((0, 0), osat, font=font_okunus)
            o_w = o_bb[2] - o_bb[0]
            draw.text(((w - o_w) // 2, ok_y), osat, font=font_okunus, fill="#5A4B42")
            ok_y += ok_line_h

    # 4. TÜRKÇE HADİS & KART İÇİNE HAPSEDİLMİŞ TIRNAK FİLİGRANI
    tr_y = box_s_y2 + gap_kutu_tr
    first_tw = draw.textbbox((0, 0), tr_satirlar[0], font=font_hadis)[2] - draw.textbbox((0, 0), tr_satirlar[0], font=font_hadis)[0]
    first_tx = (w - first_tw) // 2

    # Tırnak Filigranı
    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    font_fili = font_al(FONT_BASLIK, 175 if format_tipi == "9:16" else 165, agirlik=700)
    fx = max(kx1 + 48, first_tx - 28)
    fy = tr_y - 82
    fili_draw.text((fx, fy), "“", font=font_fili, fill=(226, 88, 93, 34))
    im.paste(fili_layer, (0, 0), fili_layer)

    draw = ImageDraw.Draw(im)
    for sat in tr_satirlar:
        tw = draw.textbbox((0, 0), sat, font=font_hadis)[2] - draw.textbbox((0, 0), sat, font=font_hadis)[0]
        draw.text(((w - tw) // 2, tr_y), sat, font=font_hadis, fill="#1C1917")
        tr_y += tr_line_h

    tr_y += gap_tr_kaynak

    # Kaynak Rozeti
    kx = (w - kw) // 2
    yuvarlak_kose_ciz(draw, (kx - 26, tr_y - 6, kx + kw + 26, tr_y + 38), radius=12, dolgu="#FFFDF9", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.text((kx, tr_y), kaynak_metni, font=font_kaynak, fill="#B45309")

    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=96)
    print(f"Kaydedildi: {cikti_yolu}")
    return cikti_yolu

if __name__ == "__main__":
    hadis_karti_ciz_v11(
        hadis_metni="Allah Teâlâ kıskanır. Allah’ın kıskanması, haram kıldığı şeyi kulun işlemesindendir.",
        kaynak_ravi="Buhârî, Nikâh 107; Müslim, Tevbe 36. Ayrıca bk. Tirmizî, Radâ 4",
        tefekkur_notu="Allah’ın gayreti ve koruma arzusu, kulunun kendi çizdiği sınırları aşarak ruhunu kirletmesini istememesindendir. Günahlardan kaçınmak, Rabbimizin bize olan sevgisine ve merhametine sadakatle karşılık vermektir.",
        arapca_metin="إِنَّ اللَّهَ تَعَالَى يَغَارُ ، وَغَيْرَةُ اللَّهِ تَعَالَى ، أنْ يَأْتِيَ الْمَرْءُ مَا حَرَّمَ اللَّهُ عَلَيْهِ",
        arapca_okunus="İnne'llâhe te'âlâ yeğâru, ve ğayretu'llâhi te'âlâ en ye'tiye'l-mer'u mâ harrame'llâhu 'aleyh.",
        cikti_dosya_adi="test_v11_hadis65_v2.png"
    )

    hadis_karti_ciz_v11(
        hadis_metni="Allah Teâlâ kıskanır. Allah’ın kıskanması, haram kıldığı şeyi kulun işlemesindendir.",
        kaynak_ravi="Buhârî, Nikâh 107; Müslim, Tevbe 36. Ayrıca bk. Tirmizî, Radâ 4",
        tefekkur_notu="Allah’ın gayreti ve koruma arzusu, kulunun kendi çizdiği sınırları aşarak ruhunu kirletmesini istememesindendir. Günahlardan kaçınmak, Rabbimizin bize olan sevgisine ve merhametine sadakatle karşılık vermektir.",
        arapca_metin="إِنَّ اللَّهَ تَعَالَى يَغَارُ ، وَغَيْرَةُ اللَّهِ تَعَالَى ، أنْ يَأْتِيَ الْمَرْءُ مَا حَرَّمَ اللَّهُ عَلَيْهِ",
        arapca_okunus="İnne'llâhe te'âlâ yeğâru, ve ğayretu'llâhi te'âlâ en ye'tiye'l-mer'u mâ harrame'llâhu 'aleyh.",
        format_tipi="9:16",
        cikti_dosya_adi="test_v11_hadis65_9_16_v2.png"
    )

hadis_karti_ciz_v11(
    hadis_metni="Mümin, bir delikten iki defa sokulmaz (aynı hataya iki kez düşmez).",
    kaynak_ravi="Buhârî, Edeb 83; Müslim, Zühd 63",
    tefekkur_notu="Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır. Hatalar tekrarlanmak için değil, ibret almak içindir.",
    arapca_metin="لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ",
    arapca_okunus="Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn.",
    format_tipi="4:5",
    cikti_dosya_adi="test_v11_kisa_harekeli.png"
)
