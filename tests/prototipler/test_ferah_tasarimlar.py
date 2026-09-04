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

FONTLAR = KOK_DIZIN / "assets" / "fonts"
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

def uret_ferah_tasarim(varyasyon: int, cikti_yolu: Path):
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
    kart_w = kx2 - kx1 # 972px
    kart_ic_w = kart_w - 80 # 892px

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
    c_y += 34 # 492px civarı

    # TIPOGRAFİ AYARLARI
    # Kullanıcı isteği:
    # 1. "Arapça fontu 1 punto küçültelim": 78px
    # 2. "mevcut kelimede sadece punto kalınlaşsın ve kırmızı renk olsun mesela arkaplan ekleme"
    # 3. "arapça okunuş bölümün arkaplanında kutucuk olmasın, her bölümde bir kutucuk çok fazla boğdu tasarımı"
    
    font_ar_normal = font_al(FONTLAR / "amiri-400-arabic.ttf", 78)
    font_ar_aktif = font_al(FONTLAR / "amiri-700-arabic.ttf", 82)

    font_okunus_normal = font_al(FONT_UI, 34, agirlik=500)
    font_okunus_aktif = font_al(FONT_UI, 36, agirlik=800)

    font_meal = font_al(FONT_BASLIK, 48, agirlik=600)

    ar_satir_h = 100
    tr_satir_h = 46

    # KELİME SATIR GRUPLARI (Aktif kelime: 3 = "الدُّنْيَا" / "dunyâ")
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

    hedef_kart_w = 840

    # ARAPÇA KELİMELERİ ÇİZ (KUTUCUK YOK, TAMAMEN FERAH)
    cur_y = c_y
    for words, start_idx in ar_gruplar:
        harf_w_list = []
        for j, w in enumerate(words):
            w_idx = start_idx + j
            gw = arapca_hazirla(w)
            fnt = font_ar_aktif if w_idx == aktif_idx else font_ar_normal
            bbox = draw.textbbox((0, 0), gw, font=fnt)
            harf_w_list.append(bbox[2] - bbox[0])

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
                # Sadece punto kalınlaşır (Amiri Bold 82px) ve kırmızı renk olur. KUTU YOK!
                draw.text((cur_x, cur_y - 2), gw, font=font_ar_aktif, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, cur_y), gw, font=font_ar_normal, fill=ISLAM_YESILI)
            else:
                draw.text((cur_x, cur_y), gw, font=font_ar_normal, fill="#2E7D56")

            cur_x -= gap
        cur_y += ar_satir_h

    # Arapça ile Okunuş arasında ferah nefes boşluğu (28px)
    cur_y += 28

    # TÜRKÇE OKUNUŞ KELİMELERİ ÇİZ (KUTUCUK YOK, TAMAMEN FERAH)
    for words, start_idx in tr_gruplar:
        kelime_w_list = []
        for j, w_str in enumerate(words):
            w_idx = start_idx + j
            fnt = font_okunus_aktif if w_idx == aktif_idx else font_okunus_normal
            bbox = draw.textbbox((0, 0), w_str, font=fnt)
            kelime_w_list.append(bbox[2] - bbox[0])

        toplam_w_kelime = sum(kelime_w_list)
        gap = max(14, (hedef_kart_w - toplam_w_kelime) // (len(words) - 1)) if len(words) > 1 else 20
        gap = min(gap, 40)
        toplam_w = toplam_w_kelime + (len(words) - 1) * gap
        cur_x = (W - toplam_w) // 2

        for j, w_str in enumerate(words):
            w_idx = start_idx + j
            width = kelime_w_list[j]

            if w_idx == aktif_idx:
                # Sadece punto kalınlaşır (Manrope Bold 36px) ve kırmızı renk olur. KUTU YOK!
                draw.text((cur_x, cur_y - 2), w_str, font=font_okunus_aktif, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, cur_y), w_str, font=font_okunus_normal, fill="#1E293B")
            else:
                draw.text((cur_x, cur_y), w_str, font=font_okunus_normal, fill="#94A3B8")

            cur_x += width + gap
        cur_y += tr_satir_h

    # MEAL VE GÜNÜN HİKMETİ
    meal_fmt = f"“{meal}”"
    meal_satirlar = metin_satirla(meal_fmt, font_meal, kart_ic_w - 40, draw)
    meal_satir_h = 62

    # GÜNÜN HİKMETİ & TEFEKKÜRÜ (Kartın tabanına oturtulmuş)
    font_tef_baslik = font_al(FONT_UI, 24, agirlik=700)
    font_tef = font_al(FONT_UI, 28, agirlik=500)
    tef_x1 = kx1 + 32
    tef_x2 = kx2 - 32
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

    # VARYASYON 1: "Klasik Mushaf Düzeni"
    # Arapça kutusuz, Okunuş kutusuz, Meal kutusuz. Ortada zarif altın ayraç.
    if varyasyon == 1:
        ayrac_y = cur_y + 36
        draw.line([(W // 2 - 110, ayrac_y), (W // 2 + 110, ayrac_y)], fill=ALTIN, width=2)
        draw.ellipse([W // 2 - 6, ayrac_y - 5, W // 2 + 6, ayrac_y + 7], fill=ALTIN)
        
        my = ayrac_y + 44
        for s in meal_satirlar:
            bbox = draw.textbbox((0, 0), s, font=font_meal)
            sw = bbox[2] - bbox[0]
            draw.text(((W - sw) // 2, my), s, font=font_meal, fill=METIN_ANA)
            my += meal_satir_h

    # VARYASYON 2: "Kitap Alıntısı Vurgusu (Solda Zarif İnce Altın Şerit, Kutu Yok)"
    elif varyasyon == 2:
        ayrac_y = cur_y + 30
        draw.line([(W // 2 - 90, ayrac_y), (W // 2 + 90, ayrac_y)], fill="#E2E8F0", width=1)
        
        meal_top_y = ayrac_y + 36
        meal_total_h = len(meal_satirlar) * meal_satir_h
        draw.rounded_rectangle([kx1 + 44, meal_top_y, kx1 + 49, meal_top_y + meal_total_h], radius=2, fill=ALTIN)
        
        my = meal_top_y + 6
        for s in meal_satirlar:
            draw.text((kx1 + 72, my), s, font=font_meal, fill=METIN_ANA)
            my += meal_satir_h

    # VARYASYON 3: "Zarif Tırnak Rozeti (Editorial Serif)"
    # Mealin başında üstte zarif bir altın tırnak rozeti (" “ ") bulunur, metin ortalıdır, kutu yoktur.
    elif varyasyon == 3:
        ayrac_y = cur_y + 30
        draw.line([(W // 2 - 120, ayrac_y), (W // 2 + 120, ayrac_y)], fill="#ECE5D8", width=1)
        
        # Minik altın tırnak rozeti
        quote_x = W // 2
        quote_y = ayrac_y + 26
        rozet_ciz(draw, quote_x - 30, quote_y, "MEAL", font=font_al(FONT_UI, 16, agirlik=700), bg_renk="#FEF3C7", yazi_renk=ALTIN, padding_x=14, padding_y=4, radius=10)

        my = quote_y + 48
        for s in meal_satirlar:
            bbox = draw.textbbox((0, 0), s, font=font_meal)
            sw = bbox[2] - bbox[0]
            draw.text(((W - sw) // 2, my), s, font=font_meal, fill=METIN_ANA)
            my += meal_satir_h

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
    print(f"Ferah Varyasyon {varyasyon} kaydedildi: {cikti_yolu}")

if __name__ == "__main__":
    out_dir = KOK_DIZIN / "data" / "cikti"
    uret_ferah_tasarim(1, out_dir / "tasarim_ferah_v1_mushaf.png")
    uret_ferah_tasarim(2, out_dir / "tasarim_ferah_v2_alinti_seridi.png")
    uret_ferah_tasarim(3, out_dir / "tasarim_ferah_v3_rozetli.png")
