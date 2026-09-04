"""
video_motoru.py — Ezan Plus 9:16 Dikey Reels & TikTok Video Motoru
Ezan Plus mobil uygulamasının kurumsal kimliğine (krem kağıt dokusu,
marka kırmızısı, zümrüt yeşili, altın detaylar ve ferah Klasik Mushaf Düzenine)
%100 sadık kalarak sesli tilavet eşliğinde 1080x1920 (9:16) MP4 videoları üretir.
"""

from __future__ import annotations

import logging
import math
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import imageio_ffmpeg

from .ayar import KOK_DIZIN, AYARLAR
from .sablon_ciz import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
)
from .ses_getir import ses_sure_hesapla

log = logging.getLogger(__name__)

CIKTI_DIZINI = KOK_DIZIN / AYARLAR.get("genel", {}).get("cikti_klasoru", "data/cikti")
IKONLAR = KOK_DIZIN / "assets" / "icons"
FONTLAR = KOK_DIZIN / "assets" / "fonts"

# Font Sabitleri
FONT_ARAPCA_NORMAL = FONTLAR / "amiri-400-arabic.ttf"
FONT_ARAPCA_BOLD = FONTLAR / "amiri-700-arabic.ttf"

GENISLIK_9_16 = 1080
YUKSEKLIK_9_16 = 1920
FPS = 30

# Ezan Plus Resmi Renk Paleti
BG_KREM = "#F4F1EA"
KIRMIZI = "#C0392B"
KOYU_KIRMIZI = "#962D22"
ISLAM_YESILI = "#0D5C3A"
CANLI_YESIL = "#059669"
ALTIN = "#D97706"
METIN_ANA = "#182230"
METIN_MUTED = "#64748B"
METIN_LIGHT = "#94A3B8"
YESIL_INACTIVE = "#2E7D56"
KART_BG = "#FFFFFF"
KART_KENARLIK = "#E5DFD3"


def _play_store_vektor_ciz(draw: ImageDraw.ImageDraw, x: float, y: float, size: float):
    """Google Play resmi 4 renkli üçgen logosunu vektörel çizer."""
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


def _statik_taban_ciz(
    sure_ayet: str,
    video_baslik_satir1: str,
    video_baslik_satir2: str,
    tefekkur_notu: str,
    hafiz_adi: str = "Mişari Râşid el-Afâsî",
) -> Tuple[Image.Image, int, int, int]:
    """
    Tüm karelerde sabit kalan arka plan, marka alanı, başlık, kart iskeleti,
    tefekkür kartı ve alt indirme butonunu çizer.
    Dönüş: (statik_resim, arapca_y_baslangic, tef_y1, kart_ic_genislik)
    """
    im = Image.new("RGB", (GENISLIK_9_16, YUKSEKLIK_9_16), BG_KREM)
    draw = ImageDraw.Draw(im)
    W, H = GENISLIK_9_16, YUKSEKLIK_9_16

    # 1. ARKA PLAN GEOMETRİSİ
    draw.rectangle([W - 240, 0, W, 32], fill=KIRMIZI)
    draw.rectangle([0, 140, 26, 440], fill=ISLAM_YESILI)
    draw.rectangle([W - 26, 680, W, 880], fill=ALTIN)
    draw.arc([W - 680, -100, W + 360, 940], start=0, end=360, fill="#E6DFC6", width=2)
    draw.arc([-340, H - 700, 320, H - 60], start=0, end=180, fill=ISLAM_YESILI, width=28)

    # 2. ÜST MARKA ALANI (124x124 Logo + Ezan Plus Büyütülmüş)
    logo_yolu = IKONLAR / "logo.png"
    logo_boyut = 124

    # Mobil uygulamanın açılış (splash) ekranındaki zarif serif font (Lora) - slogan kaldırıldı, alanı dolduracak boyutta
    font_marka = font_al(FONT_GOVDE, 80, agirlik=700)

    bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
    mw = bbox_m[2] - bbox_m[0]
    mh = bbox_m[3] - bbox_m[1]

    gap = 24
    toplam_ust_w = logo_boyut + gap + mw
    ust_x1 = (W - toplam_ust_w) // 2
    ust_y = 96

    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA")
        logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
        maske = Image.new("L", (logo_boyut, logo_boyut), 0)
        draw_m = ImageDraw.Draw(maske)
        draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=32, fill=255)
        im.paste(logo, (ust_x1, ust_y), maske)

    tx = ust_x1 + logo_boyut + gap
    # Logo yüksekliği ile dikeyde tam ortalama
    text_y = ust_y + (logo_boyut - mh) // 2 - bbox_m[1]
    draw.text((tx, text_y), "Ezan Plus", font=font_marka, fill=METIN_ANA)

    # 3. İÇERİKLE İLGİLİ VURUCU DİNAMİK BAŞLIK
    b_y = 246
    font_baslik = font_al(FONT_UI, 48, agirlik=800)
    bbox_b1 = draw.textbbox((0, 0), video_baslik_satir1, font=font_baslik)
    draw.text(((W - (bbox_b1[2] - bbox_b1[0])) // 2, b_y), video_baslik_satir1, font=font_baslik, fill=METIN_ANA)
    bbox_b2 = draw.textbbox((0, 0), video_baslik_satir2, font=font_baslik)
    draw.text(((W - (bbox_b2[2] - bbox_b2[0])) // 2, b_y + 58), video_baslik_satir2, font=font_baslik, fill=KIRMIZI)

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
    draw.text((kx1 + 40, c_y), sure_ayet.upper(), font=font_sure, fill=KIRMIZI)

    eq_x = kx2 - 40 - 290
    rozet_ciz(
        draw,
        eq_x,
        c_y - 6,
        f"Kâri: {hafiz_adi}",
        font=font_al(FONT_UI, 18, agirlik=600),
        bg_renk="#F4F1EA",
        yazi_renk=METIN_MUTED,
        padding_x=16,
        padding_y=8,
        radius=12,
    )

    c_y += 48
    draw.line([(kx1 + 40, c_y), (kx2 - 40, c_y)], fill="#F1ECE1", width=2)
    c_y += 34

    kart_ic_genislik = (kx2 - kx1) - 80
    arapca_y_baslangic = c_y

    # RESMİ KAYNAK VE RİVAYET DİPNOTU
    kaynak_metin = "Mushaf-ı Şerif • Meal: Elmalılı Hamdi Yazır • Tilavet: Hafs Rivayeti"
    font_kaynak = font_al(FONT_UI, 18, agirlik=600)
    bbox_k = draw.textbbox((0, 0), kaynak_metin, font=font_kaynak)
    kw = bbox_k[2] - bbox_k[0]
    draw.text(((W - kw) // 2, ky2 - 34), kaynak_metin, font=font_kaynak, fill=METIN_LIGHT)

    # 5. ALT BÖLÜM (App Store & Google Play İndirme Butonu)
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

    _play_store_vektor_ciz(draw, nav_x2 - 82, btn_y - 14, 28)

    return im, arapca_y_baslangic, 0, kart_ic_genislik


def arapca_kelimeleri_ayristir(metin: str) -> List[str]:
    """
    Arapça ayet metnini kelimelerine ayırır,
    secavend işaretlerini (ۚ ۖ ۗ ۘ ۙ ۛ ۜ) tek başına kelime yapmayıp
    önceki kelimenin sonuna ekler. Böylece kelime sayısı ve senkron bozulmaz.
    """
    secavendler = {"ۚ", "ۖ", "ۗ", "ۘ", "ۙ", "ۛ", "ۜ"}
    ham = [w.strip() for w in metin.split() if w.strip()]
    sonuc: List[str] = []
    for w in ham:
        if w in secavendler and sonuc:
            sonuc[-1] = f"{sonuc[-1]} {w}"
        else:
            sonuc.append(w)
    return sonuc


def turkce_okunus_hizala(tr_list: List[str], ar_list: List[str]) -> List[str]:
    """
    Türkçe Latin okunuşu ile Arapça kelimeleri 1:1 hizalar.
    Arapça'da bitişik yazılan 've' (و), 'fe' (ف), 'bi' (ب), 'li' (ل)
    bağlaçlarını Türkçe'deki sonraki kelimeyle birleştirerek
    Arapça kelime sayısına tam eşitler.
    """
    yeni_tr: List[str] = []
    i = 0
    while i < len(tr_list):
        w = tr_list[i]
        if (
            w.lower() in ["ve", "fe", "bi", "li"]
            and i + 1 < len(tr_list)
            and len(yeni_tr) < len(ar_list)
            and len(tr_list) - i > len(ar_list) - len(yeni_tr)
        ):
            ar_karsi = ar_list[len(yeni_tr)]
            if ar_karsi.startswith(("و", "ف", "ب", "ل")):
                yeni_tr.append(f"{w} {tr_list[i+1]}")
                i += 2
                continue
        yeni_tr.append(w)
        i += 1

    if len(yeni_tr) < len(ar_list):
        yeni_tr.extend([""] * (len(ar_list) - len(yeni_tr)))
    elif len(ar_list) < len(yeni_tr):
        birlestirilen = " ".join(yeni_tr[len(ar_list) - 1 :])
        yeni_tr = yeni_tr[: len(ar_list) - 1] + [birlestirilen]

    return yeni_tr


def zengin_metin_ciz_baseline(
    draw: ImageDraw.ImageDraw,
    text: str,
    x_center: int,
    y_start: int,
    max_w: int,
    font_norm: ImageFont.FreeTypeFont,
    font_bold: ImageFont.FreeTypeFont,
    fill_norm: str = "#475569",
    fill_bold: str = "#182230",
    line_height: int = 40,
) -> int:
    """
    HTML <b> veya Markdown ** etiketli kelimeleri aynı taban çizgisi (anchor='ls')
    üzerinde milimetrik hizada çizen zengin metin mizanpaj motoru.
    """
    import re
    # Markdown **bold** etiketlerini <b> formatına çevir
    formatted = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    tokens = re.split(r"(<b>.*?</b>)", formatted)
    words_data = []
    space_w = draw.textlength(" ", font=font_norm)

    for tok in tokens:
        if not tok:
            continue
        is_b = tok.startswith("<b>") and tok.endswith("</b>")
        content = tok[3:-4] if is_b else tok
        for w in content.split():
            f = font_bold if is_b else font_norm
            c = fill_bold if is_b else fill_norm
            w_px = draw.textlength(w, font=f)
            words_data.append((w, f, c, w_px))

    lines = []
    curr_line = []
    curr_w = 0

    for w_t in words_data:
        w_str, f, c, w_px = w_t
        needed = w_px if not curr_line else curr_w + space_w + w_px
        if needed <= max_w:
            curr_line.append(w_t)
            curr_w = needed
        else:
            lines.append((curr_line, curr_w))
            curr_line = [w_t]
            curr_w = w_px
    if curr_line:
        lines.append((curr_line, curr_w))

    ascent, descent = font_norm.getmetrics()
    cur_baseline_y = y_start + ascent

    for l_words, l_w in lines:
        cur_x = x_center - l_w / 2
        for w_str, f, c, w_px in l_words:
            draw.text((cur_x, cur_baseline_y), w_str, font=f, fill=c, anchor="ls")
            cur_x += w_px + space_w
        cur_baseline_y += line_height

    return int(cur_baseline_y)


def reels_videosu_uret(
    sure_ayet: str,
    turkce_meal: str,
    ses_yolu: Path,
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    video_baslik_satir1: Optional[str] = None,
    video_baslik_satir2: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    hafiz_adi: str = "Mişari Râşid el-Afâsî",
    cikti_adi: Optional[str] = None,
    kelime_zamanlari: Optional[List[Tuple[float, float]]] = None,
) -> Path:
    """
    Onaylanan Klasik Mushaf Düzeni & Akıcı Loading Dolum Efekti:
    - Kutusuz, ferah tilavet alanı (Arapça ve Okunuş doğrudan kart zemininde).
    - Arka plan kutusu YOK!
    - Her kelimenin okunuş süresi boyunca başından sonuna doğru akan canlı kırmızı dolum (loading efekti):
      * Latin okunuşta SOLDAN SAĞA dolum.
      * Arapça tilavette SAĞDAN SOLA dolum.
    - Kelime merkez koordinatlarıyla sıfır titreme (zero-jitter) stabilite garantisi.
    - Tilavet ile Meal arasında zarif altın ayraç.
    - Tırnaklı lüks Türkçe meal ve tabana dayalı Günün Hikmeti kutusu.
    """
    CIKTI_DIZINI.mkdir(parents=True, exist_ok=True)
    toplam_sure = ses_sure_hesapla(ses_yolu)
    toplam_kare = int(math.ceil(toplam_sure * FPS))
    log.info(f"Reels videosu render ediliyor: {sure_ayet}, Süre: {toplam_sure:.2f}s ({toplam_kare} kare)")

    s1 = video_baslik_satir1 or "Günün manevi ritmi,"
    s2 = video_baslik_satir2 or "kalbin ilahi sığınağı."
    tef = tefekkur_notu or "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır. Her secde kalbi yeniler."

    # 1. Taban Görseli Çiz
    taban_img, ar_y_start, tef_y1, kart_ic_w = _statik_taban_ciz(
        sure_ayet=sure_ayet,
        video_baslik_satir1=s1,
        video_baslik_satir2=s2,
        tefekkur_notu=tef,
        hafiz_adi=hafiz_adi,
    )

    # 2. Kelimeleri Ayrıştır ve Secavendleri Birleştir
    ar_str = (arapca_metin or "اتْلُ مَا أُوحِيَ إِلَيْكَ مِنَ الْكِتَابِ وَأَقِمِ الصَّلَاةَ").strip()
    tr_str = (arapca_okunus or "Utlu mâ ûhıye ileyke minel kitâbi ve ekımis-salâte").strip()

    ar_kelimeler = arapca_kelimeleri_ayristir(ar_str)
    tr_ham = [w.strip() for w in tr_str.split() if w.strip()]
    tr_kelimeler = turkce_okunus_hizala(tr_ham, ar_kelimeler)

    toplam_kelime = len(ar_kelimeler)
    meal_karakter = len(turkce_meal)

    # AUTO-FIT: Ferah, asil tipografi (Arapça 1 punto küçültüldü: 86 -> 78/82)
    if toplam_kelime > 22 or meal_karakter > 180:
        pt_ar_norm = 62
        pt_ar_bold = 62
        pt_okunus_norm = 28
        pt_okunus_bold = 28
        pt_meal = 44
        ar_satir_h = 88
        tr_satir_h = 42
        meal_satir_h = 58
        satir_sayisi = 4
        hedef_kart_w = 860
    else:
        pt_ar_norm = 78
        pt_ar_bold = 78
        pt_okunus_norm = 34
        pt_okunus_bold = 34
        pt_meal = 48
        ar_satir_h = 100
        tr_satir_h = 46
        meal_satir_h = 62
        satir_sayisi = 3
        hedef_kart_w = 840

    font_ar_norm = font_al(FONT_ARAPCA_NORMAL, pt_ar_norm)
    font_ar_bold = font_al(FONT_ARAPCA_BOLD, pt_ar_bold)
    font_okunus_norm = font_al(FONT_UI, pt_okunus_norm, agirlik=500)
    font_okunus_bold = font_al(FONT_UI, pt_okunus_bold, agirlik=800)
    font_meal = font_al(FONT_BASLIK, pt_meal, agirlik=600)

    # Satır grupları oluştur
    eleman_basi = math.ceil(toplam_kelime / satir_sayisi)
    ar_gruplar = []
    tr_gruplar = []
    cur_idx = 0
    while cur_idx < toplam_kelime:
        end_idx = min(cur_idx + eleman_basi, toplam_kelime)
        ar_gruplar.append((ar_kelimeler[cur_idx:end_idx], cur_idx))
        tr_gruplar.append((tr_kelimeler[cur_idx:end_idx], cur_idx))
        cur_idx = end_idx

    dummy_draw = ImageDraw.Draw(taban_img)

    # Ön Hesaplama: Arapça kelimelerin merkez X koordinatları (sıfır titreme / zero-jitter)
    ar_satir_bilgileri = []
    for words, start_idx in ar_gruplar:
        harf_w_list = [
            dummy_draw.textbbox((0, 0), arapca_hazirla(w), font=font_ar_norm)[2]
            - dummy_draw.textbbox((0, 0), arapca_hazirla(w), font=font_ar_norm)[0]
            for w in words
        ]
        toplam_harf_w = sum(harf_w_list)
        gap = max(24, (hedef_kart_w - toplam_harf_w) // (len(words) - 1)) if len(words) > 1 else 32
        gap = min(gap, 68)
        toplam_w = toplam_harf_w + (len(words) - 1) * gap

        kelime_yuvalari = []
        cur_x = (GENISLIK_9_16 + toplam_w) // 2
        for j, w in enumerate(words):
            width = harf_w_list[j]
            cur_x -= width
            slot_mid_x = cur_x + width // 2
            kelime_yuvalari.append((words[j], start_idx + j, slot_mid_x))
            cur_x -= gap
        ar_satir_bilgileri.append(kelime_yuvalari)

    # Ön Hesaplama: Türkçe Okunuş kelimelerinin merkez X koordinatları (sıfır titreme)
    tr_satir_bilgileri = []
    for words, start_idx in tr_gruplar:
        kelime_w_list = [
            dummy_draw.textbbox((0, 0), w, font=font_okunus_norm)[2]
            - dummy_draw.textbbox((0, 0), w, font=font_okunus_norm)[0]
            for w in words
        ]
        toplam_w_kelime = sum(kelime_w_list)
        gap = max(14, (hedef_kart_w - toplam_w_kelime) // (len(words) - 1)) if len(words) > 1 else 20
        gap = min(gap, 40)
        toplam_w = toplam_w_kelime + (len(words) - 1) * gap

        kelime_yuvalari = []
        cur_x = (GENISLIK_9_16 - toplam_w) // 2
        for j, w_str in enumerate(words):
            width = kelime_w_list[j]
            slot_mid_x = cur_x + width // 2
            kelime_yuvalari.append((w_str, start_idx + j, slot_mid_x))
            cur_x += width + gap
        tr_satir_bilgileri.append(kelime_yuvalari)

    # Loading efekti için yüksek kaliteli şeffaf kırmızı kelime bitmap önbelleği
    latin_red_cache = {}
    for satir in tr_satir_bilgileri:
        for w_str, idx, mid_x in satir:
            bbox = dummy_draw.textbbox((0, 0), w_str, font=font_okunus_bold)
            wt = bbox[2] - bbox[0]
            ht = bbox[3] - bbox[1]
            im_w = Image.new("RGBA", (wt + 4, ht + 10), (0, 0, 0, 0))
            d_w = ImageDraw.Draw(im_w)
            d_w.text((0, 0), w_str, font=font_okunus_bold, fill=KIRMIZI)
            latin_red_cache[idx] = (im_w, wt, ht)

    ar_red_cache = {}
    for satir in ar_satir_bilgileri:
        for w, idx, mid_x in satir:
            gw = arapca_hazirla(w)
            bbox = dummy_draw.textbbox((0, 0), gw, font=font_ar_bold)
            wt = bbox[2] - bbox[0]
            ht = bbox[3] - bbox[1]
            im_w = Image.new("RGBA", (wt + 4, ht + 24), (0, 0, 0, 0))
            d_w = ImageDraw.Draw(im_w)
            d_w.text((0, 0), gw, font=font_ar_bold, fill=KIRMIZI)
            ar_red_cache[idx] = (im_w, wt, ht, gw)

    # Meal satırlarını hesapla
    meal_fmt = f"“{turkce_meal.strip()}”"
    meal_satirlar = metin_satirla(meal_fmt, font_meal, kart_ic_w - 40, dummy_draw)

    # Ayraç ve Meali taban görseline kalıcı olarak çiz
    ayrac_y = ar_y_start + len(ar_gruplar) * ar_satir_h + 28 + len(tr_gruplar) * tr_satir_h + 36
    draw_taban = ImageDraw.Draw(taban_img)

    # 1. Dev Tırnak Filigranı (Mealin sol üst arkasında zarif altın)
    font_giant_quote = font_al(FONT_BASLIK, 160, agirlik=700)
    draw_taban.text((54 + 40, ayrac_y + 14), "“", font=font_giant_quote, fill="#F6ECDA")

    draw_taban.line([(GENISLIK_9_16 // 2 - 110, ayrac_y), (GENISLIK_9_16 // 2 + 110, ayrac_y)], fill=ALTIN, width=2)
    draw_taban.ellipse([GENISLIK_9_16 // 2 - 6, ayrac_y - 5, GENISLIK_9_16 // 2 + 6, ayrac_y + 7], fill=ALTIN)

    my = ayrac_y + 44
    for s in meal_satirlar:
        bbox = draw_taban.textbbox((0, 0), s, font=font_meal)
        sw = bbox[2] - bbox[0]
        draw_taban.text(((GENISLIK_9_16 - sw) // 2, my), s, font=font_meal, fill=METIN_ANA)
        my += meal_satir_h

    # 2. Günün Hikmeti & Tefekkür Bölümü (Kutusuz, Zarif Ayraçlı, Tok Başlıklı ve Vurgulu)
    ay_y = my + 24
    draw_taban.line([(GENISLIK_9_16 // 2 - 90, ay_y), (GENISLIK_9_16 // 2 + 90, ay_y)], fill="#E5DAC3", width=2)
    draw_taban.ellipse([GENISLIK_9_16 // 2 - 5, ay_y - 4, GENISLIK_9_16 // 2 + 5, ay_y + 6], fill=ALTIN)

    font_tef_baslik = font_al(FONT_UI, 26, agirlik=800)
    txt_b = "GÜNÜN HİKMETİ & TEFEKKÜRÜ"
    bw = draw_taban.textlength(txt_b, font=font_tef_baslik)
    bx = (GENISLIK_9_16 - bw) // 2
    draw_taban.ellipse([bx - 20, ay_y + 32, bx - 10, ay_y + 42], fill=ALTIN)
    draw_taban.text((bx, ay_y + 24), txt_b, font=font_tef_baslik, fill="#B45309")

    font_tef_norm = font_al(FONT_GOVDE, 26, agirlik=400)
    font_tef_bold = font_al(FONT_GOVDE, 26, agirlik=700)
    zengin_metin_ciz_baseline(
        draw_taban,
        tef,
        GENISLIK_9_16 // 2,
        ay_y + 72,
        kart_ic_w - 40,
        font_tef_norm,
        font_tef_bold,
        fill_norm="#475569",
        fill_bold="#182230",
        line_height=40,
    )

    if not cikti_adi:
        sure_kod = sure_ayet.replace(" ", "_").replace("•", "_").replace(".", "_").lower()
        cikti_adi = f"reels_{sure_kod}.mp4"

    gecici_sessiz_video = CIKTI_DIZINI / f"temp_{cikti_adi}"
    final_video = CIKTI_DIZINI / cikti_adi

    bar_x1 = 64
    bar_x2 = GENISLIK_9_16 - 64
    bar_y = 1670
    bar_w = bar_x2 - bar_x1

    eq_x = (GENISLIK_9_16 - 54) - 40 - 290
    eq_bar_x = eq_x - 34
    eq_base_y = 380 + 30 + 20

    writer = imageio.get_writer(
        str(gecici_sessiz_video),
        fps=FPS,
        codec="libx264",
        quality=9,
        pixelformat="yuv420p",
        macro_block_size=None,
    )

    try:
        for i in range(toplam_kare):
            ilerleme = (i + 1) / toplam_kare
            t_sec = i / FPS
            # Doğal telaffuz ve akustik artikülasyon mikro-avansı (240ms)
            t_eval = t_sec + 0.24

            # O an okunan aktif kelime indeksi ve kelime içi ilerleme (loading progress)
            aktif_idx = -1
            aktif_progress = 0.0

            if kelime_zamanlari and len(kelime_zamanlari) > 0:
                for w_i, (s_sec, e_sec) in enumerate(kelime_zamanlari):
                    dur = max(0.01, e_sec - s_sec)
                    if s_sec <= t_eval < e_sec:
                        aktif_idx = min(w_i, toplam_kelime - 1)
                        aktif_progress = min(1.0, max(0.0, (t_eval - s_sec) / dur))
                        break
                    elif t_eval < s_sec:
                        break
                    else:
                        aktif_idx = w_i
                        aktif_progress = 1.0
            elif toplam_kelime > 0:
                p_toplam = ilerleme * toplam_kelime
                aktif_idx = min(int(p_toplam), toplam_kelime - 1)
                aktif_progress = p_toplam - aktif_idx

            kare = taban_img.copy()
            draw_k = ImageDraw.Draw(kare)

            # A. CANLI SES DALGALARI
            for bar_idx in range(5):
                bh = 10 + int(14 * (0.5 + 0.5 * math.sin(t_sec * 8 + bar_idx * 1.3)))
                bx = eq_bar_x + bar_idx * 6
                by1 = eq_base_y - bh
                renk = CANLI_YESIL if bar_idx % 2 == 0 else ALTIN
                draw_k.rounded_rectangle([bx, by1, bx + 3, eq_base_y], radius=2, fill=renk)

            # B. DİNAMİK ARAPÇA ÇİZİMİ (Sağdan Sola Loading Akışı)
            cur_y = ar_y_start
            for satir in ar_satir_bilgileri:
                for w, w_idx, mid_x in satir:
                    im_w, wt, ht, gw = ar_red_cache[w_idx]
                    x_start = mid_x - wt // 2

                    if w_idx == aktif_idx and aktif_progress < 1.0:
                        # 1. Taban: Açık yeşil
                        draw_k.text((x_start, cur_y), gw, font=font_ar_bold, fill=YESIL_INACTIVE)
                        # 2. Sağdan sola loading dolumu
                        dolum_w = int(wt * aktif_progress)
                        if dolum_w > 0:
                            crop_x1 = max(0, wt - dolum_w)
                            cropped = im_w.crop((crop_x1, 0, im_w.width, im_w.height))
                            kare.paste(cropped, (x_start + crop_x1, cur_y), cropped)
                    elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                        # Tamamen okunmuş kelime
                        draw_k.text((x_start, cur_y), gw, font=font_ar_norm, fill=ISLAM_YESILI)
                    else:
                        # Henüz okunmamış kelime
                        draw_k.text((x_start, cur_y), gw, font=font_ar_norm, fill=YESIL_INACTIVE)
                cur_y += ar_satir_h

            # Arapça ile Türkçe okunuş arasına ferah nefes boşluğu (28px)
            cur_y += 28

            # C. DİNAMİK TÜRKÇE OKUNUŞ ÇİZİMİ (Soldan Sağa Loading Akışı)
            for satir in tr_satir_bilgileri:
                for w_str, w_idx, mid_x in satir:
                    im_w, wt, ht = latin_red_cache[w_idx]
                    x_start = mid_x - wt // 2

                    if w_idx == aktif_idx and aktif_progress < 1.0:
                        # 1. Taban: Açık gri
                        draw_k.text((x_start, cur_y), w_str, font=font_okunus_bold, fill=METIN_LIGHT)
                        # 2. Soldan sağa loading dolumu
                        dolum_w = int(wt * aktif_progress)
                        if dolum_w > 0:
                            cropped = im_w.crop((0, 0, dolum_w, im_w.height))
                            kare.paste(cropped, (x_start, cur_y), cropped)
                    elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                        # Tamamen okunmuş kelime
                        draw_k.text((x_start, cur_y), w_str, font=font_okunus_norm, fill=METIN_ANA)
                    else:
                        # Henüz okunmamış kelime
                        draw_k.text((x_start, cur_y), w_str, font=font_okunus_norm, fill=METIN_LIGHT)
                cur_y += tr_satir_h

            # D. İLERLEME ÇUBUĞU
            yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
            dolu_w = int(bar_w * ilerleme)
            if dolu_w > 6:
                yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
                draw_k.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

            # İlk kareyi kapak PNG olarak kaydet
            if i == 0:
                kapak_yolu = final_video.with_suffix(".png")
                kare.save(kapak_yolu, quality=95)

            frame_np = np.array(kare)
            writer.append_data(frame_np)

    finally:
        writer.close()

    # 3. FFmpeg ile MP3 Sesi Sessiz Videoya Birleştir
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        exe, "-y",
        "-i", str(gecici_sessiz_video),
        "-i", str(ses_yolu),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(final_video),
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if gecici_sessiz_video.exists():
        gecici_sessiz_video.unlink()

    log.info(f"Reels videosu başarıyla üretildi: {final_video}")
    return final_video
