import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.ayar import KOK_DIZIN
from src.sablon_ciz import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_ARAPCA,
    FONT_BASLIK,
    FONT_UI,
)

IKONLAR = KOK_DIZIN / "assets" / "icons"
W, H = 1080, 1920

BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
ISLAM_YESILI = "#0D5C3A"
CANLI_YESIL = "#059669"
ALTIN = "#D97706"
METIN_ANA = "#182230"
METIN_MUTED = "#64748B"
METIN_LIGHT = "#94A3B8"
KART_BG = "#FFFFFF"
KART_KENARLIK = "#E5DFD3"

ar_words_15 = [
    "وَمَا", "هَٰذِهِ", "الْحَيَاةُ", "الدُّنْيَا", "إِلَّا",
    "لَهْوٌ", "وَلَعِبٌ ۚ", "وَإِنَّ", "الدَّارَ", "الْآخِرَةَ",
    "لَهِيَ", "الْحَيَوَانُ ۚ", "لَوْ", "كَانُوا", "يَعْلَمُونَ"
]

tr_words_15 = [
    "Ve mâ", "hâzihil", "hayâtud", "dunyâ", "illâ",
    "lehvun", "ve le'ıb(un),", "ve inned", "dâral", "âhirete",
    "lehiyel", "hayavân(u),", "lev", "kânû", "ya'lemûn(e)."
]

meal = "Bu dünya hayatı sadece bir eğlence ve oyundan ibarettir. Ahiret yurdu ise işte asıl hayat odur. Keşke bilselerdi!"
tef_metin = "Gelip geçici telaşlar ve kederler içinde boğulurken, asıl durağımızın ahiret olduğunu sık sık unutuyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir ferahlık ve teslimiyet sunuyor."

def uret_tasarim(takip_stili: str, cikti_yolu: Path):
    im = Image.new("RGB", (W, H), BG_KREM)
    draw = ImageDraw.Draw(im)

    # 1. Arka plan geometrileri
    draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
    draw.rectangle([0, 140, 26, 440], fill=ISLAM_YESILI)
    draw.rectangle([W - 26, 680, W, 880], fill=ALTIN)
    draw.arc([W - 680, -100, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
    draw.arc([-340, H - 700, 320, H - 60], start=0, end=180, fill=ISLAM_YESILI, width=28)

    # 2. Üst Logo + İsim
    logo_yolu = IKONLAR / "logo.png"
    logo_boyut = 124
    font_marka = font_al(FONT_UI, 52, agirlik=800)
    font_slogan = font_al(FONT_UI, 22, agirlik=600)
    bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
    mw = bbox_m[2] - bbox_m[0]
    bbox_s = draw.textbbox((0, 0), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan)
    sw = bbox_s[2] - bbox_s[0]
    toplam_ust_w = logo_boyut + 26 + max(mw, sw)
    ust_x1 = (W - toplam_ust_w) // 2
    ust_y = 96

    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA")
        logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
        maske = Image.new("L", (logo_boyut, logo_boyut), 0)
        draw_m = ImageDraw.Draw(maske)
        draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=32, fill=255)
        im.paste(logo, (ust_x1, ust_y), maske)

    tx = ust_x1 + logo_boyut + 26
    draw.text((tx, ust_y + 14), "Ezan Plus", font=font_marka, fill=METIN_ANA)
    draw.text((tx, ust_y + 74), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan, fill=METIN_MUTED)

    # 3. Dinamik Başlık
    b_y = 246
    font_baslik = font_al(FONT_UI, 48, agirlik=800)
    s1 = "Dünya Hayatı Sadece"
    s2 = "Bir Eğlence ve Oyundur"
    bbox_b1 = draw.textbbox((0, 0), s1, font=font_baslik)
    draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), s1, font=font_baslik, fill=METIN_ANA)
    bbox_b2 = draw.textbbox((0, 0), s2, font=font_baslik)
    draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), s2, font=font_baslik, fill=KIRMIZI)

    # 4. MERKEZİ KART (Instagram Safe Zone uyumlu: y = 380 .. 1636)
    kx1 = 54
    ky1 = 380
    kx2 = W - 54
    ky2 = 1636

    for g in range(8, 0, -2):
        yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

    # Kart Üst Bar (Sure + İmam Rozeti)
    c_y = ky1 + 30
    font_sure = font_al(FONT_UI, 24, agirlik=700)
    draw.text((kx1 + 40, c_y), "ANKEBÛT SÛRESİ • 64. ÂYET", font=font_sure, fill=KIRMIZI)

    rozet_ciz(
        draw,
        kx2 - 40 - 290,
        c_y - 6,
        "Kâri: Mişari Râşid el-Afâsî",
        font=font_al(FONT_UI, 18, agirlik=600),
        bg_renk="#F4F1EA",
        yazi_renk=METIN_MUTED,
        padding_x=16,
        padding_y=8,
        radius=12,
    )

    c_y += 48
    draw.line([(kx1 + 40, c_y), (kx2 - 40, c_y)], fill="#F1ECE1", width=2)
    c_y += 18 # 476px civarı

    # PARÇA 1: ARAPÇA METİN KUTUSU
    # Font 78px (1 punto küçültüldü). Kutu yüksekliği 356px yapılarak alt taşma tamamen engellendi!
    pt_ar = 78
    font_ar = font_al(FONT_ARAPCA, pt_ar)
    ar_box_x1 = kx1 + 24
    ar_box_x2 = kx2 - 24
    ar_box_w = ar_box_x2 - ar_box_x1 # 924px
    
    ar_satir_h = 96
    ar_box_y1 = c_y
    ar_box_h = 356
    ar_box_y2 = ar_box_y1 + ar_box_h

    # Arapça kartı arka planı: Çok yumuşak, sıcak fildişi doku
    yuvarlak_kose_ciz(draw, (ar_box_x1, ar_box_y1, ar_box_x2, ar_box_y2), radius=22, dolgu="#FAF8F5", kenarlik="#ECE5D8", kenarlik_kalinlik=1)

    # PARÇA 2: ARAPÇA OKUNUŞ KUTUSU
    tr_box_x1 = kx1 + 24
    tr_box_x2 = kx2 - 24
    tr_box_y1 = ar_box_y2 + 14
    tr_satir_h = 44
    pt_okunus = 34
    font_okunus = font_al(FONT_UI, pt_okunus, agirlik=600)
    tr_box_h = 160
    tr_box_y2 = tr_box_y1 + tr_box_h

    # Okunuş kartı arka planı: Çok hafif gri-krem doku
    yuvarlak_kose_ciz(draw, (tr_box_x1, tr_box_y1, tr_box_x2, tr_box_y2), radius=18, dolgu="#F8F9FA", kenarlik="#E9ECEF", kenarlik_kalinlik=1)

    # PARÇA 3: TÜRKÇE MEAL KUTUSU
    font_meal = font_al(FONT_BASLIK, 48, agirlik=600)
    meal_box_x1 = kx1 + 24
    meal_box_x2 = kx2 - 24
    meal_box_y1 = tr_box_y2 + 16
    
    meal_fmt = f"“{meal}”"
    meal_satirlar = metin_satirla(meal_fmt, font_meal, ar_box_w - 72, draw)
    meal_satir_h = 62
    meal_box_h = 24 + len(meal_satirlar) * meal_satir_h + 20 # ~230px
    meal_box_y2 = meal_box_y1 + meal_box_h

    # Meal kartı: Zarif alıntı kutusu, solunda lüks altın şerit
    yuvarlak_kose_ciz(draw, (meal_box_x1, meal_box_y1, meal_box_x2, meal_box_y2), radius=20, dolgu="#FFFDF9", kenarlik="#EDE8DF", kenarlik_kalinlik=1)
    draw.rounded_rectangle([meal_box_x1, meal_box_y1, meal_box_x1 + 6, meal_box_y2], radius=3, fill=ALTIN)

    # PARÇA 4: GÜNÜN HİKMETİ & TEFEKKÜRÜ KUTUSU
    # Kartın tabanına oturtulmuş, Instagram safe zone ile tam uyumlu
    font_tef_baslik = font_al(FONT_UI, 24, agirlik=700)
    font_tef = font_al(FONT_UI, 28, agirlik=500)
    tef_x1 = kx1 + 24
    tef_x2 = kx2 - 24
    tef_ic_w = (tef_x2 - tef_x1) - 64
    tef_satirlar = metin_satirla(tef_metin, font_tef, tef_ic_w, draw)
    tef_satir_h = 40
    tef_box_h = 22 * 2 + 30 + 12 + len(tef_satirlar) * tef_satir_h

    tef_box_y2 = ky2 - 54
    tef_box_y1 = tef_box_y2 - tef_box_h

    yuvarlak_kose_ciz(draw, (tef_x1, tef_box_y1, tef_x2, tef_box_y2), radius=22, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
    draw.rounded_rectangle([tef_x1, tef_box_y1, tef_x1 + 8, tef_box_y2], radius=4, fill=CANLI_YESIL)
    draw.text((tef_x1 + 32, tef_box_y1 + 22), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_tef_baslik, fill=CANLI_YESIL)

    ty = tef_box_y1 + 64
    for s in tef_satirlar:
        draw.text((tef_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
        ty += tef_satir_h

    # Dipnot
    kaynak_metin = "Mushaf-ı Şerif • Meal: Diyanet İşleri Başkanlığı • Tilavet: Hafs Rivayeti"
    font_kaynak = font_al(FONT_UI, 18, agirlik=600)
    bbox_k = draw.textbbox((0, 0), kaynak_metin, font=font_kaynak)
    draw.text(((W - (bbox_k[2] - bbox_k[0])) // 2, tef_box_y2 + 16), kaynak_metin, font=font_kaynak, fill=METIN_LIGHT)

    # MEAL METNİ ÇİZİMİ
    my = meal_box_y1 + 22
    for s in meal_satirlar:
        bbox = draw.textbbox((0, 0), s, font=font_meal)
        sw = bbox[2] - bbox[0]
        draw.text(((W - sw) // 2, my), s, font=font_meal, fill=METIN_ANA)
        my += meal_satir_h

    # KELİME SATIR GRUPLARI VE TAKİP (Aktif kelime: 3 = "الدُّنْيَا" / "dunyâ")
    aktif_idx = 3
    ar_gruplar = [
        (ar_words_15[0:5], 0),
        (ar_words_15[5:10], 5),
        (ar_words_15[10:15], 10),
    ]
    tr_gruplar = [
        (tr_words_15[0:5], 0),
        (tr_words_15[5:10], 5),
        (tr_words_15[10:15], 10),
    ]

    hedef_kart_w = 830

    # ARAPÇA KELİMELERİ ÇİZ
    cur_y = ar_box_y1 + 20
    for words, start_idx in ar_gruplar:
        harf_w_list = [draw.textbbox((0, 0), arapca_hazirla(w), font=font_ar)[2] - draw.textbbox((0, 0), arapca_hazirla(w), font=font_ar)[0] for w in words]
        toplam_harf_w = sum(harf_w_list)
        gap = max(24, (hedef_kart_w - toplam_harf_w) // (len(words) - 1)) if len(words) > 1 else 32
        gap = min(gap, 68)
        toplam_w = toplam_harf_w + (len(words) - 1) * gap
        cur_x = (W + toplam_w) // 2

        for j, w in enumerate(words):
            w_idx = start_idx + j
            width = harf_w_list[j]
            cur_x -= width
            gw = arapca_hazirla(w)

            if w_idx == aktif_idx:
                if takip_stili == "zumrut_kapsul":
                    # STİL 1: Soft Mint Zümrüt Kapsül (Sarı kutu tamamen yok!)
                    yuvarlak_kose_ciz(draw, (cur_x - 14, cur_y - 6, cur_x + width + 14, cur_y + pt_ar + 14), radius=16, dolgu="#E6F4EA", kenarlik="#A7F3D0", kenarlik_kalinlik=2)
                    draw.text((cur_x, cur_y), gw, font=font_ar, fill="#065F46")
                else:
                    # STİL 2: Minimalist Zarif Alt Çizgi (Kutu yok, lüks yakut kırmızısı vurgu)
                    draw.text((cur_x, cur_y), gw, font=font_ar, fill=KIRMIZI)
                    alt_cizgi_y = cur_y + pt_ar + 6
                    draw.rounded_rectangle([cur_x - 4, alt_cizgi_y, cur_x + width + 4, alt_cizgi_y + 4], radius=2, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, cur_y), gw, font=font_ar, fill=ISLAM_YESILI)
            else:
                draw.text((cur_x, cur_y), gw, font=font_ar, fill="#2E7D56")

            cur_x -= gap
        cur_y += ar_satir_h

    # TÜRKÇE OKUNUŞ KELİMELERİ ÇİZ
    cur_y = tr_box_y1 + 18
    for words, start_idx in tr_gruplar:
        kelime_w_list = [draw.textbbox((0, 0), w, font=font_okunus)[2] - draw.textbbox((0, 0), w, font=font_okunus)[0] for w in words]
        toplam_w_kelime = sum(kelime_w_list)
        gap = max(14, (hedef_kart_w - toplam_w_kelime) // (len(words) - 1)) if len(words) > 1 else 20
        gap = min(gap, 40)
        toplam_w = toplam_w_kelime + (len(words) - 1) * gap
        cur_x = (W - toplam_w) // 2

        for j, w_str in enumerate(words):
            w_idx = start_idx + j
            width = kelime_w_list[j]

            if w_idx == aktif_idx:
                if takip_stili == "zumrut_kapsul":
                    yuvarlak_kose_ciz(draw, (cur_x - 10, cur_y - 4, cur_x + width + 10, cur_y + pt_okunus + 8), radius=12, dolgu="#E6F4EA", kenarlik="#A7F3D0", kenarlik_kalinlik=1)
                    draw.text((cur_x, cur_y), w_str, font=font_okunus, fill="#065F46")
                else:
                    draw.text((cur_x, cur_y), w_str, font=font_okunus, fill=KIRMIZI)
                    alt_cizgi_y = cur_y + pt_okunus + 4
                    draw.rounded_rectangle([cur_x - 2, alt_cizgi_y, cur_x + width + 2, alt_cizgi_y + 3], radius=2, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, cur_y), w_str, font=font_okunus, fill="#1E293B")
            else:
                draw.text((cur_x, cur_y), w_str, font=font_okunus, fill="#94A3B8")

            cur_x += width + gap
        cur_y += tr_satir_h

    # 5. Alt İndirme Butonu
    nav_w = 680
    nav_h = 84
    nav_x1 = (W - nav_w) // 2
    nav_x2 = nav_x1 + nav_w
    nav_y1 = 1712
    nav_y2 = nav_y1 + nav_h
    yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=32, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)

    btn_x = nav_x1 + 38
    btn_y = nav_y1 + nav_h // 2
    draw.ellipse([btn_x - 22, btn_y - 22, btn_x + 22, btn_y + 22], fill=KIRMIZI)
    draw.polygon([(btn_x, btn_y - 11), (btn_x - 11, btn_y), (btn_x + 11, btn_y)], fill="#FFFFFF")
    draw.rectangle([btn_x - 8, btn_y, btn_x + 8, btn_y + 10], fill="#FFFFFF")
    draw.rectangle([btn_x - 3, btn_y + 3, btn_x + 3, btn_y + 10], fill=KIRMIZI)

    font_cta = font_al(FONT_UI, 22, agirlik=700)
    draw.text((btn_x + 34, btn_y - 13), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill=METIN_ANA)

    try:
        font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        draw.text((nav_x2 - 140, btn_y - 16), "\uf8ff", font=font_apple, fill="#000000")
    except Exception:
        pass

    # Play store
    w_ps = 28
    p_tl = (nav_x2 - 82, btn_y - 14)
    p_bl = (nav_x2 - 82, btn_y - 14 + w_ps)
    p_r = (nav_x2 - 82 + w_ps, btn_y)
    p_mid = (nav_x2 - 82 + w_ps * 0.52, btn_y)
    p_top_mid = (nav_x2 - 82 + w_ps * 0.72, btn_y - 14 + w_ps * 0.32)
    p_bot_mid = (nav_x2 - 82 + w_ps * 0.72, btn_y - 14 + w_ps * 0.68)
    draw.polygon([p_tl, p_bl, p_mid], fill="#00D3FF")
    draw.polygon([p_tl, p_top_mid, p_mid], fill="#00E676")
    draw.polygon([p_bl, p_bot_mid, p_mid], fill="#FFC800")
    draw.polygon([p_top_mid, p_r, p_bot_mid, p_mid], fill="#FF3A44")

    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    im.save(str(cikti_yolu), quality=95)
    print(f"Başarıyla kaydedildi: {cikti_yolu}")

if __name__ == "__main__":
    out_dir = KOK_DIZIN / "data" / "cikti"
    uret_tasarim("zumrut_kapsul", out_dir / "tasarim_secenek_A_zumrut_kapsul.png")
    uret_tasarim("zarif_alt_cizgi", out_dir / "tasarim_secenek_B_zarif_alt_cizgi.png")
