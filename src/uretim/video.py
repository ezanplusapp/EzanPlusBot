"""
video_motoru.py — Ezan Plus 9:16 Dikey Reels & TikTok Video Motoru
Ezan Plus mobil uygulamasının kurumsal kimliğine (krem kağıt dokusu,
marka kırmızısı, zümrüt yeşili, altın detaylar ve ferah Klasik Mushaf Düzenine)
%100 sadık kalarak sesli tilavet eşliğinde 1080x1920 (9:16) MP4 videoları üretir.
"""

from __future__ import annotations

import logging
import math
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import imageio_ffmpeg

from ..ayar import KOK_DIZIN, AYARLAR
from .kart import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
)
from .ses import ses_sure_hesapla

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
    Arapça'da bitişik yazılan 've' (و), 'fe' (ف), 'bi' (ب), 'li' (ل), 'ke' (ك)
    bağlaçlarını ve harf-i tariflerini Türkçe'deki sonraki kelimeyle birleştirerek
    Arapça kelime sayısına tam eşitler.
    """
    baglaclar = ["ve", "fe", "bi", "li", "vel", "fel", "bil", "lil", "ke", "kel"]
    yeni_tr: List[str] = []
    i = 0
    while i < len(tr_list):
        w = tr_list[i]
        if (
            w.lower() in baglaclar
            and i + 1 < len(tr_list)
            and len(yeni_tr) < len(ar_list)
            and len(tr_list) - i > len(ar_list) - len(yeni_tr)
        ):
            ar_karsi = ar_list[len(yeni_tr)]
            if ar_karsi.startswith(("و", "ف", "ب", "ل", "ك")):
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


def _meal_parcala(meal_metin: str, parca_sayisi: int) -> List[str]:
    """
    Türkçe meali anlam ve cümle bütünlüğünü bozmadan parça sayısına böler.
    Öncelikle nokta, ünlem, soru işareti, noktalı virgül gibi cümle sonlarına bakar;
    cümle sayısı yetersizse virgüllere veya kelime bloklarına böler.
    """
    if parca_sayisi <= 1:
        return [meal_metin.strip()]
    cumleler = [c.strip() for c in re.split(r"(?<=[.!?;\n])\s+", meal_metin.strip()) if c.strip()]
    if len(cumleler) >= parca_sayisi:
        parcalar = []
        hedef_len = len(meal_metin) / parca_sayisi
        cur = []
        cur_len = 0
        for c in cumleler:
            cur.append(c)
            cur_len += len(c)
            if cur_len >= hedef_len and len(parcalar) < parca_sayisi - 1:
                parcalar.append(" ".join(cur).strip())
                cur = []
                cur_len = 0
        if cur:
            parcalar.append(" ".join(cur).strip())
        return parcalar
    else:
        # Virgüllere göre bölmeyi dene
        yan_cumleler = [c.strip() for c in re.split(r"(?<=[,])\s+", meal_metin.strip()) if c.strip()]
        if len(yan_cumleler) >= parca_sayisi:
            parcalar = []
            hedef_len = len(meal_metin) / parca_sayisi
            cur = []
            cur_len = 0
            for c in yan_cumleler:
                cur.append(c)
                cur_len += len(c)
                if cur_len >= hedef_len and len(parcalar) < parca_sayisi - 1:
                    parcalar.append(" ".join(cur).strip())
                    cur = []
                    cur_len = 0
            if cur:
                parcalar.append(" ".join(cur).strip())
            return parcalar
        else:
            kelimeler = meal_metin.split()
            adim = math.ceil(len(kelimeler) / parca_sayisi)
            return [" ".join(kelimeler[i:i + adim]) for i in range(0, len(kelimeler), adim)]


class _SayfaVerisi:
    """
    Reels videosundaki tek bir sayfanın mizanpaj, font, slot ve taban görselini yönetir.
    """
    def __init__(
        self,
        p_idx: int,
        sayfa_sayisi: int,
        start_w: int,
        end_w: int,
        page_ar: List[str],
        page_tr: List[str],
        page_meal: str,
        sure_ayet: str,
        s1: str,
        s2: str,
        tef: str,
        hafiz_adi: str,
    ):
        self.p_idx = p_idx
        self.start_w = start_w
        self.end_w = end_w
        self.page_ar = page_ar
        self.page_tr = page_tr
        self.page_meal = page_meal

        # Sayfa başlığı: Tek sayfada yalın, çoklu sayfada (1/2) vb. rozet
        if sayfa_sayisi > 1:
            page_title = f"{sure_ayet} ({p_idx + 1}/{sayfa_sayisi})"
        else:
            page_title = sure_ayet

        # Tipografi parametreleri
        if len(page_ar) > 16:
            self.pt_ar = 68
            self.pt_okunus = 28
            self.pt_meal = 38
            self.ar_h = 76
            self.tr_h = 34
            self.meal_h = 46
            self.satir_s = 4
            self.hedef_kart_w = 820
        else:
            self.pt_ar = 76
            self.pt_okunus = 32
            self.pt_meal = 44
            self.ar_h = 92
            self.tr_h = 40
            self.meal_h = 56
            self.satir_s = 3
            self.hedef_kart_w = 840

        self.font_ar_norm = font_al(FONT_ARAPCA_NORMAL, self.pt_ar)
        self.font_ar_bold = font_al(FONT_ARAPCA_BOLD, self.pt_ar)
        self.font_okunus_norm = font_al(FONT_UI, self.pt_okunus, agirlik=500)
        self.font_okunus_bold = font_al(FONT_UI, self.pt_okunus, agirlik=800)
        self.font_meal = font_al(FONT_BASLIK, self.pt_meal, agirlik=600)

        # 1. Taban görseli oluştur
        self.taban_img, self.ar_y_start, _, self.kart_ic_w = _statik_taban_ciz(
            sure_ayet=page_title,
            video_baslik_satir1=s1,
            video_baslik_satir2=s2,
            tefekkur_notu=tef,
            hafiz_adi=hafiz_adi,
        )
        draw_t = ImageDraw.Draw(self.taban_img)

        # 2. Satır grupları oluştur
        eleman_basi = math.ceil(len(page_ar) / self.satir_s)
        ar_gruplar = []
        tr_gruplar = []
        cur_i = 0
        while cur_i < len(page_ar):
            end_i = min(cur_i + eleman_basi, len(page_ar))
            global_s = start_w + cur_i
            ar_gruplar.append((page_ar[cur_i:end_i], global_s))
            tr_gruplar.append((page_tr[cur_i:end_i], global_s))
            cur_i = end_i

        # Arapça kelime slotları (merkez X koordinatları)
        self.ar_satir_bilgileri = []
        for words, g_start in ar_gruplar:
            harf_w_list = [
                draw_t.textbbox((0, 0), arapca_hazirla(w), font=self.font_ar_norm)[2]
                - draw_t.textbbox((0, 0), arapca_hazirla(w), font=self.font_ar_norm)[0]
                for w in words
            ]
            toplam_harf_w = sum(harf_w_list)
            gap = max(16, (self.hedef_kart_w - toplam_harf_w) // (len(words) - 1)) if len(words) > 1 else 28
            gap = min(gap, 48)
            toplam_w = toplam_harf_w + (len(words) - 1) * gap

            kelime_yuvalari = []
            cur_x = (GENISLIK_9_16 + toplam_w) // 2
            for j, w in enumerate(words):
                width = harf_w_list[j]
                cur_x -= width
                slot_mid_x = cur_x + width // 2
                kelime_yuvalari.append((words[j], g_start + j, slot_mid_x))
                cur_x -= gap
            self.ar_satir_bilgileri.append(kelime_yuvalari)

        # Türkçe Latin okunuş slotları
        self.tr_satir_bilgileri = []
        for words, g_start in tr_gruplar:
            kelime_w_list = [
                draw_t.textbbox((0, 0), w, font=self.font_okunus_norm)[2]
                - draw_t.textbbox((0, 0), w, font=self.font_okunus_norm)[0]
                for w in words
            ]
            toplam_w_kelime = sum(kelime_w_list)
            gap = max(10, (self.hedef_kart_w - toplam_w_kelime) // (len(words) - 1)) if len(words) > 1 else 14
            gap = min(gap, 28)
            toplam_w = toplam_w_kelime + (len(words) - 1) * gap

            kelime_yuvalari = []
            cur_x = (GENISLIK_9_16 - toplam_w) // 2
            for j, w_str in enumerate(words):
                width = kelime_w_list[j]
                slot_mid_x = cur_x + width // 2
                kelime_yuvalari.append((w_str, g_start + j, slot_mid_x))
                cur_x += width + gap
            self.tr_satir_bilgileri.append(kelime_yuvalari)

        # Kırmızı dolum önbellekleri
        self.latin_red_cache = {}
        for satir in self.tr_satir_bilgileri:
            for w_str, idx, mid_x in satir:
                bbox = draw_t.textbbox((0, 0), w_str, font=self.font_okunus_bold)
                wt = bbox[2] - bbox[0]
                ht = bbox[3] - bbox[1]
                im_w = Image.new("RGBA", (wt + 4, ht + 10), (0, 0, 0, 0))
                d_w = ImageDraw.Draw(im_w)
                d_w.text((0, 0), w_str, font=self.font_okunus_bold, fill=KIRMIZI)
                self.latin_red_cache[idx] = (im_w, wt, ht)

        self.ar_red_cache = {}
        for satir in self.ar_satir_bilgileri:
            for w, idx, mid_x in satir:
                gw = arapca_hazirla(w)
                bbox = draw_t.textbbox((0, 0), gw, font=self.font_ar_bold)
                wt = bbox[2] - bbox[0]
                ht = bbox[3] - bbox[1]
                im_w = Image.new("RGBA", (wt + 4, ht + 24), (0, 0, 0, 0))
                d_w = ImageDraw.Draw(im_w)
                d_w.text((0, 0), gw, font=self.font_ar_bold, fill=KIRMIZI)
                self.ar_red_cache[idx] = (im_w, wt, ht, gw)

        # 3. Ayraç & Meal Çizimi (Taban görseline kalıcı)
        cur_y = self.ar_y_start + len(self.ar_satir_bilgileri) * self.ar_h + 18 + len(self.tr_satir_bilgileri) * self.tr_h
        ayrac_y = cur_y + 24
        font_giant_quote = font_al(FONT_BASLIK, 140, agirlik=700)
        draw_t.text((54 + 40, ayrac_y + 10), "“", font=font_giant_quote, fill="#F6ECDA")

        draw_t.line([(GENISLIK_9_16 // 2 - 110, ayrac_y), (GENISLIK_9_16 // 2 + 110, ayrac_y)], fill=ALTIN, width=2)
        draw_t.ellipse([GENISLIK_9_16 // 2 - 6, ayrac_y - 5, GENISLIK_9_16 // 2 + 6, ayrac_y + 7], fill=ALTIN)

        meal_satirlar = metin_satirla(f"“{page_meal}”", self.font_meal, self.kart_ic_w - 40, draw_t)
        my = ayrac_y + 32
        for s in meal_satirlar:
            bbox = draw_t.textbbox((0, 0), s, font=self.font_meal)
            sw = bbox[2] - bbox[0]
            draw_t.text(((GENISLIK_9_16 - sw) // 2, my), s, font=self.font_meal, fill=METIN_ANA)
            my += self.meal_h

        # 4. Günün Hikmeti & Tefekkür (Çoklu sayfada sabit Y=1390 ile sıfır ghosting, tek sayfada my+24)
        if sayfa_sayisi > 1:
            ay_y = 1390
        else:
            ay_y = my + 24

        draw_t.line([(GENISLIK_9_16 // 2 - 90, ay_y), (GENISLIK_9_16 // 2 + 90, ay_y)], fill="#E5DAC3", width=2)
        draw_t.ellipse([GENISLIK_9_16 // 2 - 5, ay_y - 4, GENISLIK_9_16 // 2 + 5, ay_y + 6], fill=ALTIN)

        font_tef_baslik = font_al(FONT_UI, 24, agirlik=800)
        txt_b = "GÜNÜN HİKMETİ & TEFEKKÜRÜ"
        bw = draw_t.textlength(txt_b, font=font_tef_baslik)
        bx = (GENISLIK_9_16 - bw) // 2
        draw_t.ellipse([bx - 18, ay_y + 28, bx - 10, ay_y + 36], fill=ALTIN)
        draw_t.text((bx, ay_y + 20), txt_b, font=font_tef_baslik, fill="#B45309")

        font_tef_norm = font_al(FONT_GOVDE, 24, agirlik=400)
        font_tef_bold = font_al(FONT_GOVDE, 24, agirlik=700)
        zengin_metin_ciz_baseline(
            draw_t,
            tef,
            GENISLIK_9_16 // 2,
            ay_y + 56,
            self.kart_ic_w - 40,
            font_tef_norm,
            font_tef_bold,
            fill_norm="#475569",
            fill_bold="#182230",
            line_height=34,
        )

    def kare_ciz(self, t_sec: float, aktif_idx: int, aktif_progress: float) -> Image.Image:
        """Sayfanın belirtilen andaki karesini döndürür."""
        kare = self.taban_img.copy()
        draw_k = ImageDraw.Draw(kare)

        # Arapça Kelimeler (Sağdan sola loading akışı)
        cur_y = self.ar_y_start
        for satir in self.ar_satir_bilgileri:
            for w, w_idx, mid_x in satir:
                im_w, wt, ht, gw = self.ar_red_cache[w_idx]
                x_start = mid_x - wt // 2

                if w_idx == aktif_idx and aktif_progress < 1.0:
                    draw_k.text((x_start, cur_y), gw, font=self.font_ar_bold, fill=YESIL_INACTIVE)
                    dolum_w = int(wt * aktif_progress)
                    if dolum_w > 0:
                        crop_x1 = max(0, wt - dolum_w)
                        cropped = im_w.crop((crop_x1, 0, im_w.width, im_w.height))
                        kare.paste(cropped, (x_start + crop_x1, cur_y), cropped)
                elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                    draw_k.text((x_start, cur_y), gw, font=self.font_ar_norm, fill=ISLAM_YESILI)
                else:
                    draw_k.text((x_start, cur_y), gw, font=self.font_ar_norm, fill=YESIL_INACTIVE)
            cur_y += self.ar_h

        cur_y += 18
        # Türkçe Okunuş Kelimeler (Soldan sağa loading akışı)
        for satir in self.tr_satir_bilgileri:
            for w_str, w_idx, mid_x in satir:
                im_w, wt, ht = self.latin_red_cache[w_idx]
                x_start = mid_x - wt // 2

                if w_idx == aktif_idx and aktif_progress < 1.0:
                    draw_k.text((x_start, cur_y), w_str, font=self.font_okunus_bold, fill=METIN_LIGHT)
                    dolum_w = int(wt * aktif_progress)
                    if dolum_w > 0:
                        cropped = im_w.crop((0, 0, dolum_w, im_w.height))
                        kare.paste(cropped, (x_start, cur_y), cropped)
                elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                    draw_k.text((x_start, cur_y), w_str, font=self.font_okunus_norm, fill=METIN_ANA)
                else:
                    draw_k.text((x_start, cur_y), w_str, font=self.font_okunus_norm, fill=METIN_LIGHT)
            cur_y += self.tr_h

        return kare


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
    - UZUN AYET DESTEĞİ (1. YOL): 20 kelimeyi aşan uzun ayetlerde metni küçültüp sıkıştırmak yerine,
      sayfalar arası sinematik yumuşak crossfade (erime) geçişi ile 2-3 slayt halinde sunar.
    """
    CIKTI_DIZINI.mkdir(parents=True, exist_ok=True)
    toplam_sure = ses_sure_hesapla(ses_yolu)
    toplam_kare = int(math.ceil(toplam_sure * FPS))
    log.info(f"Reels videosu render ediliyor: {sure_ayet}, Süre: {toplam_sure:.2f}s ({toplam_kare} kare)")

    s1 = video_baslik_satir1 or "Günün manevi ritmi,"
    s2 = video_baslik_satir2 or "kalbin ilahi sığınağı."
    tef = tefekkur_notu or "Namaz sadece bir ibadet değil; günün karmaşasında ruhu arındıran, insanı kötülükten ve günahtan koruyan ilahi bir sığınaktır. Her secde kalbi yeniler."

    # 1. Kelimeleri Ayrıştır ve Hizala
    ar_str = (arapca_metin or "اتْلُ مَا أُوحِيَ إِلَيْكَ مِنَ الْكِتَابِ وَأَقِمِ الصَّلَاةَ").strip()
    tr_str = (arapca_okunus or "Utlu mâ ûhıye ileyke minel kitâbi ve ekımis-salâte").strip()

    ar_kelimeler = arapca_kelimeleri_ayristir(ar_str)
    tr_ham = [w.strip() for w in tr_str.split() if w.strip()]
    tr_kelimeler = turkce_okunus_hizala(tr_ham, ar_kelimeler)

    toplam_kelime = len(ar_kelimeler)

    # 2. Sayfa Sayısını ve Aralıkları Belirle (1. Yol — Çoklu Sayfa Motoru)
    if toplam_kelime <= 20:
        sayfa_sayisi = 1
    elif toplam_kelime <= 40:
        sayfa_sayisi = 2
    else:
        sayfa_sayisi = math.ceil(toplam_kelime / 18)

    meal_parcalari = _meal_parcala(turkce_meal, sayfa_sayisi)

    kelimeler_per_sayfa = math.ceil(toplam_kelime / sayfa_sayisi)
    sayfa_araliklari = []
    cur_w = 0
    for s_idx in range(sayfa_sayisi):
        end_w = min(cur_w + kelimeler_per_sayfa, toplam_kelime)
        sayfa_araliklari.append((cur_w, end_w))
        cur_w = end_w

    # 3. Sayfa Verilerini Hazırla
    sayfalar: List[_SayfaVerisi] = []
    for p_idx, (w_s, w_e) in enumerate(sayfa_araliklari):
        s = _SayfaVerisi(
            p_idx=p_idx,
            sayfa_sayisi=sayfa_sayisi,
            start_w=w_s,
            end_w=w_e,
            page_ar=ar_kelimeler[w_s:w_e],
            page_tr=tr_kelimeler[w_s:w_e],
            page_meal=meal_parcalari[p_idx],
            sure_ayet=sure_ayet,
            s1=s1,
            s2=s2,
            tef=tef,
            hafiz_adi=hafiz_adi,
        )
        sayfalar.append(s)

    # 4. Çoklu Sayfa Geçiş Pencerelerini Hesapla
    # Her geçiş: (t_trans_start, t_trans_end, sayfa_left_idx, sayfa_right_idx)
    gecisler = []
    TRANS_DURATION = 0.45  # 0.45 saniye sinematik erime geçişi

    if sayfa_sayisi > 1:
        for p in range(sayfa_sayisi - 1):
            w_last = sayfa_araliklari[p][1] - 1
            w_first = sayfa_araliklari[p + 1][0]
            if kelime_zamanlari and w_last < len(kelime_zamanlari) and w_first < len(kelime_zamanlari):
                t_p_end = kelime_zamanlari[w_last][1]
                t_next_start = kelime_zamanlari[w_first][0]
            else:
                t_p_end = (p + 1) * (toplam_sure / sayfa_sayisi)
                t_next_start = t_p_end

            t_switch = (t_p_end + t_next_start) / 2.0
            t_trans_s = max(0.0, t_switch - TRANS_DURATION / 2.0)
            t_trans_e = min(toplam_sure, t_switch + TRANS_DURATION / 2.0)
            gecisler.append((t_trans_s, t_trans_e, p, p + 1))

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
            t_eval = t_sec + 0.24

            # O an okunan kelime indeksi ve dolum yüzdesi
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

            # Sayfa Seçimi & Yumuşak Erime (Crossfade)
            kare: Optional[Image.Image] = None
            if sayfa_sayisi == 1:
                kare = sayfalar[0].kare_ciz(t_sec, aktif_idx, aktif_progress)
            else:
                # Geçiş aralığında mıyız?
                in_transition = False
                for t_s, t_e, p_from, p_to in gecisler:
                    if t_s <= t_sec <= t_e:
                        alpha = (t_sec - t_s) / max(0.001, (t_e - t_s))
                        kare_from = sayfalar[p_from].kare_ciz(t_sec, sayfa_araliklari[p_from][1], 1.0)
                        kare_to = sayfalar[p_to].kare_ciz(t_sec, sayfa_araliklari[p_to][0] - 1, 0.0)
                        kare = Image.blend(kare_from, kare_to, alpha)
                        in_transition = True
                        break

                if not in_transition:
                    # Hangi sayfa aktif?
                    active_p = 0
                    for p_idx, (w_s, w_e) in enumerate(sayfa_araliklari):
                        if w_s <= aktif_idx < w_e:
                            active_p = p_idx
                            break
                        elif aktif_idx >= w_e:
                            active_p = min(p_idx + 1, sayfa_sayisi - 1)
                    kare = sayfalar[active_p].kare_ciz(t_sec, aktif_idx, aktif_progress)

            draw_k = ImageDraw.Draw(kare)

            # A. CANLI SES DALGALARI
            for bar_idx in range(5):
                bh = 10 + int(14 * (0.5 + 0.5 * math.sin(t_sec * 8 + bar_idx * 1.3)))
                bx = eq_bar_x + bar_idx * 6
                by1 = eq_base_y - bh
                renk = CANLI_YESIL if bar_idx % 2 == 0 else ALTIN
                draw_k.rounded_rectangle([bx, by1, bx + 3, eq_base_y], radius=2, fill=renk)

            # B. İLERLEME ÇUBUĞU
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

    # 5. FFmpeg ile MP3 Sesi Sessiz Videoya Birleştir
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
