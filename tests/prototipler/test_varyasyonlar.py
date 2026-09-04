import os
from pathlib import Path
from typing import List
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
KART_BG = "#FFFFFF"
KART_KENARLIK = "#E5DFD3"

def render_tasarim(varyasyon_no: int, cikti_yolu: Path):
    im = Image.new("RGB", (W, H), BG_KREM)
    draw = ImageDraw.Draw(im)

    # Arka plan geometrileri
    draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
    draw.rectangle([0, 120, 28, 420], fill=ISLAM_YESILI)
    draw.rectangle([W - 28, 700, W, 900], fill=ALTIN)
    draw.arc([W - 700, -120, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
    draw.arc([-340, H - 720, 320, H - 80], start=0, end=180, fill=ISLAM_YESILI, width=28)

    # Üst Logo + Ad (Yan Yana & Ortalı)
    logo_yolu = IKONLAR / "logo.png"
    logo_boyut = 104
    font_marka = font_al(FONT_UI, 44, agirlik=800)
    font_slogan = font_al(FONT_UI, 20, agirlik=600)
    bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
    mw = bbox_m[2] - bbox_m[0]
    bbox_s = draw.textbbox((0, 0), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan)
    sw = bbox_s[2] - bbox_s[0]
    text_w = max(mw, sw)
    gap = 20
    toplam_ust_w = logo_boyut + gap + text_w
    ust_x1 = (W - toplam_ust_w) // 2
    ust_y = 75

    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA")
        logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
        maske = Image.new("L", (logo_boyut, logo_boyut), 0)
        draw_m = ImageDraw.Draw(maske)
        draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=26, fill=255)
        im.paste(logo, (ust_x1, ust_y), maske)

    tx = ust_x1 + logo_boyut + gap
    draw.text((tx, ust_y + 10), "Ezan Plus", font=font_marka, fill=METIN_ANA)
    draw.text((tx, ust_y + 60), "GÜNLÜK İBADET YARDIMCIN", font=font_slogan, fill=METIN_MUTED)

    # Dinamik Başlık
    b_y = 210
    font_baslik = font_al(FONT_UI, 48, agirlik=800)
    s1 = "Namaz, kötülüklerden koruyan"
    s2 = "en güçlü kalkandır."
    bbox_b1 = draw.textbbox((0, 0), s1, font=font_baslik)
    draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), s1, font=font_baslik, fill=METIN_ANA)
    bbox_b2 = draw.textbbox((0, 0), s2, font=font_baslik)
    draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), s2, font=font_baslik, fill=KIRMIZI)

    # Metin boyutları - Daha da büyütülmüş ve ferah
    font_ar = font_al(FONT_ARAPCA, 70)
    font_okunus = font_al(FONT_UI, 36, agirlik=600)
    font_meal = font_al(FONT_BASLIK, 54, agirlik=600)
    font_tef_baslik = font_al(FONT_UI, 24, agirlik=700)
    font_tef = font_al(FONT_UI, 28, agirlik=500)

    kx1 = 64
    ky1 = 350
    kx2 = W - 64
    genislik = (kx2 - kx1) - 88

    ar_kelimeler = [
        "اتْلُ", "مَا", "أُوحِيَ", "إِلَيْكَ", "مِنَ", "الْكِتَابِ",
        "وَأَقِمِ", "الصَّلَاةَ", "ۖ", "إِنَّ", "الصَّلَاةَ", "تَنْهَىٰ", "عَنِ", "الْفَحْشَاءِ", "وَالْمُنكَرِ"
    ]
    tr_okunus = [
        "Utlu", "mâ", "ûhıye", "ileyke", "minel", "kitâbi",
        "ve", "ekımis-salâte,", "—", "innes-salâte", "tenhâ", "‘anil", "fahşâi", "vel-munker."
    ]
    aktif_idx = 5

    meal = "“Sana vahyedilen kitabı oku ve namazı dosdoğru kıl. Şüphesiz ki namaz, insanı hayasızlıktan ve kötülükten alıkoyar.”"
    tef_metin = "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır. Her secde kalbi yeniler."

    meal_satirlar = metin_satirla(meal, font_meal, genislik, draw)
    tef_satirlar = metin_satirla(tef_metin, font_tef, genislik - 64, draw)

    # Günün hikmeti kutusunun dinamik yüksekliği
    tef_ic_pad_y = 28
    tef_kart_h = tef_ic_pad_y * 2 + 34 + 18 + len(tef_satirlar) * 44

    # Varyasyon 1: Kart boyutu içerikle dinamik biter + alt kısım dengeli
    # Varyasyon 2: Kart 1660'a kadar iner ama aralıklar flex/oransal dağıtılır
    if varyasyon_no == 1:
        # Önce yükseklikleri toplayalım
        # header: 90
        # arapça: 2 x 106 = 212 + 20 = 232
        # okunuş: 2 x 58 = 116 + 20 = 136
        # ayraç: 60
        # meal: len(meal_satirlar) * 76
        # aralık: 50
        # tef_kart_h
        # kart alt pad: 44
        tahmini_h = 90 + 232 + 136 + 60 + len(meal_satirlar) * 76 + 50 + tef_kart_h + 44
        ky2 = ky1 + tahmini_h
    else:
        ky2 = 1660

    # Kartı çiz
    for g in range(8, 0, -2):
        yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=40 + g, dolgu="#EAE5D8")
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=40, dolgu=KART_BG, kenarlik=KART_KENARLIK, kenarlik_kalinlik=2)

    c_y = ky1 + 38
    font_sure = font_al(FONT_UI, 24, agirlik=700)
    draw.text((kx1 + 44, c_y), "ANKEBÛT SÛRESİ • 45. ÂYET", font=font_sure, fill=KIRMIZI)

    rozet_ciz(
        draw,
        kx2 - 44 - 260,
        c_y - 6,
        "Mishary Rashid Alafasy",
        font=font_al(FONT_UI, 18, agirlik=600),
        bg_renk="#F4F1EA",
        yazi_renk=METIN_MUTED,
        padding_x=16,
        padding_y=8,
        radius=12,
    )

    c_y += 54
    draw.line([(kx1 + 44, c_y), (kx2 - 44, c_y)], fill="#F1ECE1", width=2)
    c_y += 52

    # Arapça Satırları
    ar_satir1 = ar_kelimeler[:8]
    ar_satir2 = ar_kelimeler[8:]

    def arapca_satir_ciz(words: List[str], start_idx: int, y: int):
        toplam_w = 0
        w_list = []
        for i, w in enumerate(words):
            w_idx = start_idx + i
            gorsel_w = arapca_hazirla(w)
            bbox = draw.textbbox((0, 0), gorsel_w, font=font_ar)
            width = bbox[2] - bbox[0]
            w_list.append((w_idx, gorsel_w, width))
            toplam_w += width + 20
        toplam_w -= 20

        cur_x = (W + toplam_w) // 2
        for w_idx, gorsel_w, width in w_list:
            cur_x -= width
            if w_idx == aktif_idx:
                yuvarlak_kose_ciz(draw, (cur_x - 12, y + 2, cur_x + width + 12, y + 84), radius=16, dolgu="#FEF3C7")
                draw.text((cur_x, y), gorsel_w, font=font_ar, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, y), gorsel_w, font=font_ar, fill=ISLAM_YESILI)
            else:
                draw.text((cur_x, y), gorsel_w, font=font_ar, fill="#2E7D56")
            cur_x -= 20

    arapca_satir_ciz(ar_satir1, 0, c_y)
    c_y += 106
    arapca_satir_ciz(ar_satir2, 8, c_y)
    c_y += 120

    # Okunuş Satırları
    tr_satir1 = tr_okunus[:8]
    tr_satir2 = tr_okunus[8:]

    def okunus_satir_ciz(words: List[str], start_idx: int, y: int):
        toplam_w = 0
        w_list = []
        for i, w in enumerate(words):
            w_idx = start_idx + i
            bbox = draw.textbbox((0, 0), w, font=font_okunus)
            width = bbox[2] - bbox[0]
            w_list.append((w_idx, w, width))
            toplam_w += width + 14
        toplam_w -= 14

        cur_x = (W - toplam_w) // 2
        for w_idx, w_str, width in w_list:
            if w_idx == aktif_idx:
                yuvarlak_kose_ciz(draw, (cur_x - 8, y - 2, cur_x + width + 8, y + 46), radius=12, dolgu="#FEF3C7")
                draw.text((cur_x, y), w_str, font=font_okunus, fill=KIRMIZI)
            elif w_idx < aktif_idx:
                draw.text((cur_x, y), w_str, font=font_okunus, fill=METIN_ANA)
            else:
                draw.text((cur_x, y), w_str, font=font_okunus, fill="#94A3B8")
            cur_x += width + 14

    okunus_satir_ciz(tr_satir1, 0, c_y)
    c_y += 58
    okunus_satir_ciz(tr_satir2, 8, c_y)
    c_y += 76

    # Ayraç
    draw.line([(W // 2 - 120, c_y), (W // 2 + 120, c_y)], fill=ALTIN, width=2)
    draw.ellipse([W // 2 - 7, c_y - 6, W // 2 + 7, c_y + 8], fill=ALTIN)
    c_y += 66

    # Türkçe Meal (54px)
    for s in meal_satirlar:
        bbox = draw.textbbox((0, 0), s, font=font_meal)
        sw = bbox[2] - bbox[0]
        draw.text(((W - sw) // 2, c_y), s, font=font_meal, fill=METIN_ANA)
        c_y += 76

    # Günün Hikmeti
    if varyasyon_no == 1:
        # Doğrudan mealin altına doğal ferah boşlukla yerleşir
        c_y += 40
        tef_y1 = c_y
        tef_y2 = tef_y1 + tef_kart_h
    else:
        # Kartın tabanına oturtulur ama aradaki boşluk oranlı olur
        tef_y2 = ky2 - 40
        tef_y1 = tef_y2 - tef_kart_h

    tef_x1 = kx1 + 36
    tef_x2 = kx2 - 36
    yuvarlak_kose_ciz(draw, (tef_x1, tef_y1, tef_x2, tef_y2), radius=26, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=2)
    draw.rounded_rectangle([tef_x1, tef_y1, tef_x1 + 8, tef_y2], radius=4, fill=CANLI_YESIL)

    draw.text((tef_x1 + 32, tef_y1 + 26), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_tef_baslik, fill=CANLI_YESIL)

    ty = tef_y1 + 78
    for s in tef_satirlar:
        draw.text((tef_x1 + 32, ty), s, font=font_tef, fill=METIN_ANA)
        ty += 44

    # Alt gezinme ve progress bar
    # Eğer kart dinamikse progress bar ve nav bar kartın altına göre konumlanabilir
    if varyasyon_no == 1:
        bar_y = ky2 + 36
        nav_y1 = bar_y + 44
        nav_y2 = nav_y1 + 80
    else:
        bar_y = 1685
        nav_y1 = 1740
        nav_y2 = 1820

    bar_x1 = 64
    bar_x2 = W - 64
    yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
    dolu_w = int((bar_x2 - bar_x1) * 0.40)
    yuvarlak_kose_ciz(draw, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
    draw.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

    nav_x1 = (W - 580) // 2
    nav_x2 = nav_x1 + 580
    yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=30, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)

    btn_x = nav_x1 + 44
    btn_y = nav_y1 + (nav_y2 - nav_y1) // 2
    draw.ellipse([btn_x - 26, btn_y - 26, btn_x + 26, btn_y + 26], fill=KIRMIZI)
    draw.polygon([(btn_x, btn_y - 13), (btn_x - 13, btn_y), (btn_x + 13, btn_y)], fill="#FFFFFF")
    draw.rectangle([btn_x - 9, btn_y, btn_x + 9, btn_y + 12], fill="#FFFFFF")
    draw.rectangle([btn_x - 3, btn_y + 4, btn_x + 3, btn_y + 12], fill=KIRMIZI)

    draw.text((btn_x + 44, btn_y - 12), "Ezan Plus • App Store & Google Play'de", font=font_al(FONT_UI, 21, agirlik=600), fill=METIN_ANA)

    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    im.save(str(cikti_yolu), quality=95)
    print(f"Varyasyon {varyasyon_no} kaydedildi: {cikti_yolu}")

if __name__ == "__main__":
    c1 = KOK_DIZIN / "data" / "cikti" / "varyasyon_1_dinamik.png"
    c2 = KOK_DIZIN / "data" / "cikti" / "varyasyon_2_sabit.png"
    render_tasarim(1, c1)
    render_tasarim(2, c2)
