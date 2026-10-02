"""
hatim.py — Ezan Plus YouTube 30 Cüz Hatim-i Şerif (Mukabele) 16:9 Video Motoru

16:9 Yatay formatta (1920x1080 / 4K) Kur'an-ı Kerim tilaveti, kelime kelime
senkron karaoke, resmi Elmalılı Hamdi Yazır meali ve cüz/sayfa takibi ile
yüksek performanslı YouTube video üretimi gerçekleştirir.
"""

from __future__ import annotations

import logging
import math
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from ..ayar import KOK_DIZIN
from ..kuran_db import ayet_getir, cuz_ayetleri_getir, sure_bilgisi_getir
from .kart import arapca_hazirla
from .ses import (
    ayet_kelime_zamanlari_getir,
    ayet_sesi_indir,
    ses_sure_hesapla,
)
from .video import (
    akilli_sayfa_araliklari,
    arapca_kelimeleri_ayristir,
    kelime_zamanlarini_hizala,
    latin_okunus_temizle,
    turkce_okunus_hizala,
    _meal_parcala,
)

log = logging.getLogger(__name__)

# Dizinler
FONTS_DIR = KOK_DIZIN / "assets" / "fonts"
ICONS_DIR = KOK_DIZIN / "assets" / "icons"
HATIM_CIKTI_DIR = KOK_DIZIN / "data" / "cikti" / "hatim"
HATIM_CIKTI_DIR.mkdir(parents=True, exist_ok=True)

# 16:9 Tuval Boyutları ve FPS
W_16_9 = 1920
H_16_9 = 1080
FPS = 30

# Kurumsal Renk Paleti
BG_KREM = (251, 249, 244)        # #FBF9F4 Klasik Mushaf Krem Zemin
KART_BEYAZ = (255, 253, 249)     # #FFFDF9 Kart Tabanı
KENARLIK = (234, 228, 213)       # #EAE4D5 Zarif İnce Kenarlık
ALTIN = (194, 155, 56)           # #C29B38 Sıcak Altın
ALTIN_PARLAK = (212, 175, 55)    # #D4AF37
METIN_KOYU = (24, 34, 48)        # #182230 Antik Koyu Mürekkep
METIN_GRI = (148, 163, 184)      # #94A3B8 Henüz Okunmamış Arduvaz Grisi
METIN_MUTED = (100, 116, 139)    # #64748B İkincil Metin
KIRMIZI_VURGU = (192, 57, 43)    # #C0392B Aktif Okunan Kelime
KIRMIZI_BANT = (155, 27, 27)     # #9B1B1B Sol Kırmızı Sütun Ayracı
YESIL_ROZET = (27, 67, 50)       # #1B4332 İslam Yeşili Cüz Rozeti
YESIL_ACIK = (45, 106, 79)       # #2D6A4F
KETEN_MEAL_BG = (250, 245, 242)  # #FAF5F2 Keten Meal Arka Planı
KETEN_MEAL_BORDER = (238, 220, 215)


def font_al(font_adi: str, boyut: int) -> ImageFont.FreeTypeFont:
    """Belirtilen fontu assets/fonts dizininden yükler."""
    yol = FONTS_DIR / font_adi
    if yol.exists():
        try:
            return ImageFont.truetype(str(yol), boyut)
        except Exception as e:
            log.warning(f"Font yükleme hatası ({yol}): {e}")
    return ImageFont.load_default()


def arapca_kelime_satirla(
    kelimeler: List[str], max_w: int, font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw
) -> List[List[str]]:
    """Arapça kelimeleri azami genişliğe göre dengeli satırlara böler."""
    satirlar: List[List[str]] = []
    mevcut_satir: List[str] = []
    for k in kelimeler:
        deneme = mevcut_satir + [k]
        toplam_w = sum(
            draw.textbbox((0, 0), arapca_hazirla(w), font=font)[2]
            - draw.textbbox((0, 0), arapca_hazirla(w), font=font)[0]
            for w in deneme
        )
        bosluk_w = (len(deneme) - 1) * 20
        if toplam_w + bosluk_w > max_w and mevcut_satir:
            satirlar.append(mevcut_satir)
            mevcut_satir = [k]
        else:
            mevcut_satir = deneme
    if mevcut_satir:
        satirlar.append(mevcut_satir)
    return satirlar


def arapca_satir_ciz(
    draw: ImageDraw.ImageDraw,
    satir_kelimeler: List[str],
    baslangic_idx: int,
    aktif_idx: int,
    center_x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    gap: int = 18,
):
    """Arapça kelimeleri sağdan sola dizer ve 3 durumlu renklendirme uygular."""
    w_list = [
        draw.textbbox((0, 0), arapca_hazirla(w), font=font)[2]
        - draw.textbbox((0, 0), arapca_hazirla(w), font=font)[0]
        for w in satir_kelimeler
    ]
    toplam_w = sum(w_list) + (len(satir_kelimeler) - 1) * gap
    cur_x = center_x + toplam_w // 2  # RTL başlangıç sağ sınır

    for i, w in enumerate(satir_kelimeler):
        idx = baslangic_idx + i
        wt = w_list[i]
        x_pos = cur_x - wt
        gw = arapca_hazirla(w)

        if idx < aktif_idx:
            renk = METIN_KOYU
        elif idx == aktif_idx:
            renk = KIRMIZI_VURGU
        else:
            renk = METIN_GRI

        draw.text((x_pos, y), gw, font=font, fill=renk)
        cur_x -= (wt + gap)


class Hatim16x9Sayfa:
    """16:9 Split-Screen tek bir sayfanın statik tabanını ve dinamik karesini çizer."""

    def __init__(
        self,
        sure_no: int,
        ayet_no: int,
        cuz_no: int,
        sayfa_no: int,
        sure_adi_tr: str,
        toplam_sure_ayet: int,
        ar_kelimeler: List[str],
        tr_kelimeler: List[str],
        kelime_offset: int,
        meal_metni: str,
        tefekkur_notu: str,
        cuz_ilerleme_yuzdesi: float = 0.0,
        juz_toplam_sure_str: str = "52:14",
    ):
        self.sure_no = sure_no
        self.ayet_no = ayet_no
        self.cuz_no = cuz_no
        self.sayfa_no = sayfa_no
        self.sure_adi_tr = sure_adi_tr
        self.toplam_sure_ayet = toplam_sure_ayet
        self.ar_kelimeler = ar_kelimeler
        self.tr_kelimeler = tr_kelimeler
        self.kelime_offset = kelime_offset
        self.meal_metni = meal_metni
        self.tefekkur_notu = tefekkur_notu
        self.cuz_ilerleme_yuzdesi = cuz_ilerleme_yuzdesi
        self.juz_toplam_sure_str = juz_toplam_sure_str

        # Fontlar
        self.f_logo = font_al("Lora.ttf", 32)
        self.f_sub = font_al("Manrope.ttf", 16)
        self.f_badge = font_al("Baskerville-Bold.ttf", 26)
        self.f_sag1 = font_al("Manrope.ttf", 22)
        self.f_sag2 = font_al("Manrope.ttf", 16)
        self.f_kart_baslik = font_al("Manrope.ttf", 18)
        self.f_latin = font_al("Manrope.ttf", 23)
        self.f_zaman = font_al("Manrope.ttf", 18)
        self.f_tef = font_al("Lora.ttf", 21)

        # Kart Ölçüleri
        self.kart_y1 = 155
        self.kart_y2 = 940
        self.kart_w = 855
        self.sol_x1 = 80
        self.sol_x2 = self.sol_x1 + self.kart_w
        self.sag_x1 = W_16_9 - 80 - self.kart_w
        self.sag_x2 = self.sag_x1 + self.kart_w

        # Arapça font boyutu belirleme
        n_words = len(ar_kelimeler)
        if n_words <= 8:
            self.pt_ar = 66
            self.ar_line_gap = 135
        elif n_words <= 14:
            self.pt_ar = 60
            self.ar_line_gap = 120
        else:
            self.pt_ar = 54
            self.ar_line_gap = 110

        self.f_ar = font_al("amiri-700-arabic.ttf", self.pt_ar)

        # Statik arka planı önceden çizip sakla (kare çiziminde devasa hız kazandırır)
        self.statik_im = self._statik_taban_olustur()

    def _statik_taban_olustur(self) -> Image.Image:
        im = Image.new("RGB", (W_16_9, H_16_9), BG_KREM)
        draw = ImageDraw.Draw(im)

        # 1. ÜST BİLGİ BARI
        logo_p = ICONS_DIR / "logo.png"
        if logo_p.exists():
            logo = Image.open(logo_p).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
            mask = Image.new("L", (60, 60), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, 60, 60], radius=14, fill=255)
            im.paste(logo, (80, 45), mask)

        draw.text((155, 55), "Ezan Plus", font=self.f_logo, fill=METIN_KOYU)
        draw.text((157, 92), "HATİM-İ ŞERİF • 4K ULTRA HD", font=self.f_sub, fill=ALTIN)

        # Orta: Cüz & Sûre Rozeti
        badge_text = f"{self.cuz_no}. CÜZ  •  {self.sure_adi_tr.upper()} SÛRESİ  ({self.ayet_no}. ÂYET)"
        bbox_b = draw.textbbox((0, 0), badge_text, font=self.f_badge)
        bw = bbox_b[2] - bbox_b[0]
        bx = (W_16_9 - bw) // 2
        draw.rounded_rectangle([bx - 24, 50, bx + bw + 24, 102], radius=10, fill=YESIL_ROZET)
        draw.text((bx, 62), badge_text, font=self.f_badge, fill=(255, 255, 255))

        # Sağ: Sayfa ve Tilavet Künyesi
        draw.text((W_16_9 - 80 - 160, 52), f"SAYFA {self.sayfa_no}", font=self.f_sag1, fill=METIN_KOYU)
        draw.text((W_16_9 - 80 - 160, 84), f"Âyet {self.ayet_no} / {self.toplam_sure_ayet}", font=self.f_sag2, fill=METIN_MUTED)

        draw.line([(80, 130), (W_16_9 - 80, 130)], fill=KENARLIK, width=1)

        # 2. SOL KART: MUSHAF İSKELETİ
        draw.rounded_rectangle([self.sol_x1, self.kart_y1, self.sol_x2, self.kart_y2], radius=24, fill=KART_BEYAZ, outline=KENARLIK, width=2)
        draw.rounded_rectangle([self.sol_x1 + 12, self.kart_y1 + 12, self.sol_x2 - 12, self.kart_y2 - 12], radius=16, outline=ALTIN, width=1)

        draw.text((self.sol_x1 + 40, self.kart_y1 + 32), "KUR'AN-I KERİM TİLAVETİ", font=self.f_kart_baslik, fill=ALTIN)
        draw.text((self.sol_x2 - 210, self.kart_y1 + 32), "HÂFIZ MİŞARÎ EL-AFÂSÎ", font=self.f_kart_baslik, fill=METIN_GRI)
        draw.line([(self.sol_x1 + 40, self.kart_y1 + 65), (self.sol_x2 - 40, self.kart_y1 + 65)], fill=KENARLIK, width=1)

        # Altın Odak Elması ve Ayraç
        sep_y = self.kart_y1 + 490
        draw.line([(self.sol_x1 + 60, sep_y), (self.sol_x2 - 60, sep_y)], fill=KENARLIK, width=1)
        draw.polygon(
            [
                ((self.sol_x1 + self.sol_x2) // 2, sep_y - 7),
                ((self.sol_x1 + self.sol_x2) // 2 + 7, sep_y),
                ((self.sol_x1 + self.sol_x2) // 2, sep_y + 7),
                ((self.sol_x1 + self.sol_x2) // 2 - 7, sep_y),
            ],
            fill=ALTIN,
        )

        draw.text((self.sol_x1 + 40, self.kart_y1 + 520), "LATİN HARFLİ TİLAVET AKIŞI", font=self.f_kart_baslik, fill=METIN_MUTED)

        # 3. SAĞ KART: MEAL & TEFEKKÜR İSKELETİ
        draw.rounded_rectangle([self.sag_x1, self.kart_y1, self.sag_x2, self.kart_y2], radius=24, fill=KART_BEYAZ, outline=KENARLIK, width=2)
        draw.rounded_rectangle([self.sag_x1 + 12, self.kart_y1 + 12, self.sag_x2 - 12, self.kart_y2 - 12], radius=16, outline=KENARLIK, width=1)

        draw.text((self.sag_x1 + 40, self.kart_y1 + 32), "ÂYET-İ KERÎME MEÂLİ", font=self.f_kart_baslik, fill=YESIL_ACIK)
        draw.text((self.sag_x2 - 190, self.kart_y1 + 32), "ELMALILI HAMDİ YAZIR", font=self.f_kart_baslik, fill=METIN_GRI)
        draw.line([(self.sag_x1 + 40, self.kart_y1 + 65), (self.sag_x2 - 40, self.kart_y1 + 65)], fill=KENARLIK, width=1)

        # Keten Meal Kutusu
        meal_band_y1 = self.kart_y1 + 100
        meal_band_y2 = self.kart_y1 + 470
        draw.rounded_rectangle([self.sag_x1 + 30, meal_band_y1, self.sag_x2 - 30, meal_band_y2], radius=16, fill=KETEN_MEAL_BG, outline=KETEN_MEAL_BORDER, width=1)
        draw.rounded_rectangle([self.sag_x1 + 30, meal_band_y1, self.sag_x1 + 38, meal_band_y2], radius=4, fill=KIRMIZI_BANT)

        # Türkçe Meali Çiz
        f_meal = font_al("IbarraRealNova.ttf", 34 if len(self.meal_metni) < 220 else 28)
        temiz_meal = self.meal_metni.strip("“”\"' ")
        formatli_meal = f"“{temiz_meal}”"

        # Otomatik satır sarma
        kelimeler_meal = formatli_meal.split()
        satirlar_meal: List[str] = []
        cur_satir = ""
        max_meal_w = self.kart_w - 140
        for km in kelimeler_meal:
            test_satir = f"{cur_satir} {km}".strip()
            if draw.textlength(test_satir, font=f_meal) > max_meal_w and cur_satir:
                satirlar_meal.append(cur_satir)
                cur_satir = km
            else:
                cur_satir = test_satir
        if cur_satir:
            satirlar_meal.append(cur_satir)

        line_h = 44 if len(self.meal_metni) < 220 else 38
        cur_my = meal_band_y1 + max(25, (370 - len(satirlar_meal) * line_h) // 2)
        for sm in satirlar_meal:
            draw.text((self.sag_x1 + 65, cur_my), sm, font=f_meal, fill=METIN_KOYU)
            cur_my += line_h

        # Hikmet & Tefekkür Notu
        tef_y1 = self.kart_y1 + 505
        draw.text((self.sag_x1 + 40, tef_y1), "HİKMET VE TEFEKKÜR NOTU", font=self.f_kart_baslik, fill=ALTIN)
        tef_kelimeler = self.tefekkur_notu.split()
        cur_t_line = ""
        t_lines = []
        for kw in tef_kelimeler:
            test_tl = f"{cur_t_line} {kw}".strip()
            if draw.textlength(test_tl, font=self.f_tef) > (self.kart_w - 80) and cur_t_line:
                t_lines.append(cur_t_line)
                cur_t_line = kw
            else:
                cur_t_line = test_tl
        if cur_t_line:
            t_lines.append(cur_t_line)

        cur_ty = tef_y1 + 36
        for tl in t_lines[:3]:
            draw.text((self.sag_x1 + 40, cur_ty), tl, font=self.f_tef, fill=METIN_MUTED)
            cur_ty += 30

        # Mobil Uygulama CTA Kutusu
        cta_box_y = self.kart_y2 - 110
        draw.rounded_rectangle([self.sag_x1 + 40, cta_box_y, self.sag_x2 - 40, cta_box_y + 70], radius=12, fill=(245, 243, 238))
        f_cta_baslik = font_al("Manrope.ttf", 18)
        f_cta_alt = font_al("Manrope.ttf", 14)
        draw.text((self.sag_x1 + 65, cta_box_y + 15), "Ezan Plus Mobil Uygulamasını İndirin", font=f_cta_baslik, fill=METIN_KOYU)
        draw.text((self.sag_x1 + 65, cta_box_y + 40), "Namaz Vakitleri • Sahih Külliyat • Hatim Takibi", font=f_cta_alt, fill=ALTIN)
        draw.text((self.sag_x2 - 190, cta_box_y + 24), "App Store & Google Play", font=f_cta_alt, fill=METIN_MUTED)

        # 4. ALT İLERLEME VE KONTROL BARI
        draw.line([(80, 975), (W_16_9 - 80, 975)], fill=KENARLIK, width=1)
        draw.text(
            (80, 995),
            f"{self.cuz_no}. CÜZ İLERLEMESİ:  %{int(self.cuz_ilerleme_yuzdesi * 100)} (Sayfa {self.sayfa_no})",
            font=self.f_zaman,
            fill=METIN_MUTED,
        )
        draw.text((W_16_9 - 80 - 170, 995), f"TOPLAM SÜRE: {self.juz_toplam_sure_str}", font=self.f_zaman, fill=METIN_MUTED)

        return im

    def kare_ciz(self, aktif_idx: int, ayah_progress: float = 0.0) -> Image.Image:
        """Belirtilen aktif kelimeye göre dinamik kareyi çizer."""
        im = self.statik_im.copy()
        draw = ImageDraw.Draw(im)

        # 1. Arapça Hat (Sol Kart)
        satirlar_ar = arapca_kelime_satirla(self.ar_kelimeler, self.kart_w - 90, self.f_ar, draw)
        cur_ar_y = self.kart_y1 + 115
        cur_idx = self.kelime_offset
        for s_ar in satirlar_ar:
            arapca_satir_ciz(
                draw,
                s_ar,
                cur_idx,
                aktif_idx,
                (self.sol_x1 + self.sol_x2) // 2,
                cur_ar_y,
                self.f_ar,
                gap=18,
            )
            cur_idx += len(s_ar)
            cur_ar_y += self.ar_line_gap

        # 2. Latin Okunuş Akışı (Sol Kart)
        tr_line_w = self.kart_w - 80
        tr_satirlar: List[List[Tuple[str, int]]] = []
        cur_tr_line: List[Tuple[str, int]] = []
        cur_line_len = 0.0

        for j, tw in enumerate(self.tr_kelimeler):
            global_w_idx = self.kelime_offset + j
            w_len = draw.textlength(tw + " ", font=self.f_latin)
            if cur_line_len + w_len > tr_line_w and cur_tr_line:
                tr_satirlar.append(cur_tr_line)
                cur_tr_line = [(tw, global_w_idx)]
                cur_line_len = w_len
            else:
                cur_tr_line.append((tw, global_w_idx))
                cur_line_len += w_len
        if cur_tr_line:
            tr_satirlar.append(cur_tr_line)

        cur_try = self.kart_y1 + 560
        for tr_satir in tr_satirlar[:3]:
            cur_tx = self.sol_x1 + 40
            for tw, idx in tr_satir:
                if idx < aktif_idx:
                    renk = METIN_KOYU
                elif idx == aktif_idx:
                    renk = KIRMIZI_VURGU
                else:
                    renk = METIN_GRI
                draw.text((cur_tx, cur_try), tw, font=self.f_latin, fill=renk)
                cur_tx += draw.textlength(tw + " ", font=self.f_latin)
            cur_try += 42

        # 3. İlerleme Çubuğu (Alt Bar)
        bar_x1 = 480
        bar_x2 = W_16_9 - 80 - 200
        bar_y = 1004
        draw.rounded_rectangle([bar_x1, bar_y, bar_x2, bar_y + 8], radius=4, fill=(225, 220, 208))

        pct = max(0.0, min(1.0, self.cuz_ilerleme_yuzdesi))
        dolu_w = int((bar_x2 - bar_x1) * pct)
        if dolu_w > 0:
            draw.rounded_rectangle([bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 8], radius=4, fill=KIRMIZI_BANT)
            draw.ellipse([bar_x1 + dolu_w - 7, bar_y - 3, bar_x1 + dolu_w + 7, bar_y + 11], fill=ALTIN)

        return im


def hatim_ayet_klibi_uret(
    sure_no: int,
    ayet_no: int,
    cikti_mp4: Optional[Path] = None,
    cuz_ilerleme_yuzdesi: float = 0.0,
    fps: int = FPS,
) -> Path:
    """Tek bir âyet için 16:9 stüdyo klibini üretir."""
    ayet = ayet_getir(sure_no, ayet_no)
    if not ayet:
        raise ValueError(f"Âyet veritabanında bulunamadı: {sure_no}:{ayet_no}")

    sure_bilgi = sure_bilgisi_getir(sure_no)
    toplam_sure_ayet = sure_bilgi["ayet_sayisi"] if sure_bilgi else 286
    sure_adi_tr = ayet.get("sure_adi_tr", "Bakara")
    cuz_no = ayet.get("cuz_no", 1)
    sayfa_no = ayet.get("sayfa_no", 1)
    ar_str = ayet.get("arapca_metin", "")
    meal_str = ayet.get("meal_elmalili", "")

    # Ses dosyasını al
    ses_yolu = ayet_sesi_indir(sure_no, ayet_no)
    toplam_sure = ses_sure_hesapla(ses_yolu)

    # Kelimeler ve zaman damgaları
    ar_kelimeler = arapca_kelimeleri_ayristir(ar_str)
    kelime_zamanlari = ayet_kelime_zamanlari_getir(sure_no, ayet_no)
    hizali_zamanlar = kelime_zamanlarini_hizala(kelime_zamanlari, len(ar_kelimeler), toplam_sure)

    # Latin okunuş transkripsiyonu
    latin_raw = latin_okunus_temizle(meal_str)  # fallback
    # Kelime sayısı kadar latin okunuş dengesi
    tr_kelimeler = ar_kelimeler[:]

    # Tefekkür Notu
    tefekkur_notu = (
        f"{sure_adi_tr} Sûresi, Medine/Mekke döneminde nâzil olmuştur. "
        "Her âyet-i kerîme, müminin kalbine şifa, zihnine tefekkür ve istikamet aşılayan ilahî bir rehberdir."
    )

    # Sayfalandırma denetimi: 16:9 ekranda 14 kelimeye kadar tek sayfa idealdir
    sayfa = Hatim16x9Sayfa(
        sure_no=sure_no,
        ayet_no=ayet_no,
        cuz_no=cuz_no,
        sayfa_no=sayfa_no,
        sure_adi_tr=sure_adi_tr,
        toplam_sure_ayet=toplam_sure_ayet,
        ar_kelimeler=ar_kelimeler,
        tr_kelimeler=tr_kelimeler,
        kelime_offset=0,
        meal_metni=meal_str,
        tefekkur_notu=tefekkur_notu,
        cuz_ilerleme_yuzdesi=cuz_ilerleme_yuzdesi,
    )

    if cikti_mp4 is None:
        cikti_mp4 = HATIM_CIKTI_DIR / f"ayet_{sure_no:03d}_{ayet_no:03d}.mp4"

    total_frames = int(toplam_sure * fps)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W_16_9}x{H_16_9}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",  # Video stdin
        "-i", str(ses_yolu),  # Audio input
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(cikti_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / fps + 0.05  # 50ms ince görsel avans

            # Aktif kelimeyi bul
            aktif_idx = 0
            for w_i, s_t, e_t in hizali_zamanlar:
                if s_t <= t_sec:
                    aktif_idx = w_i
                if s_t <= t_sec <= e_t:
                    aktif_idx = w_i
                    break

            kare = sayfa.kare_ciz(aktif_idx=aktif_idx, ayah_progress=f_idx / max(1, total_frames))
            proc.stdin.write(kare.tobytes())

        _, stderr = proc.communicate(timeout=60)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg render hatası (kod {proc.returncode}): {stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        proc.kill()
        raise RuntimeError(f"FFmpeg render hatası: {e}")

    log.info(f"Hatim 16:9 Âyet klibi üretildi: {cikti_mp4} ({toplam_sure:.2f}s)")
    return cikti_mp4


def cuz_hatim_videosu_uret(
    cuz_no: int,
    cikti_mp4: Optional[Path] = None,
    ayet_limiti: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Belirtilen cüzün tüm âyetlerini sırasıyla üretir, FFmpeg stream copy
    ile birleştirir ve YouTube Bölüm (Chapter) zaman damgalarını içeren
    .txt dosyasını oluşturur.
    Dönüş: (cikti_mp4, bolumler_txt)
    """
    cuz_ayetler = cuz_ayetleri_getir(cuz_no)
    if not cuz_ayetler:
        raise ValueError(f"{cuz_no}. Cüz için âyet bulunamadı!")

    if ayet_limiti is not None and ayet_limiti > 0:
        cuz_ayetler = cuz_ayetler[:ayet_limiti]

    toplam_ayet_sayisi = len(cuz_ayetler)
    log.info(f"{cuz_no}. Cüz Üretimi Başlıyor: Toplam {toplam_ayet_sayisi} âyet işlenecek.")

    cuz_dizini = HATIM_CIKTI_DIR / f"cuz_{cuz_no:02d}"
    cuz_dizini.mkdir(parents=True, exist_ok=True)

    klip_yollari: List[Path] = []
    bolum_zamanlari: List[Tuple[float, str]] = []
    kumulatif_zaman = 0.0

    for i, a in enumerate(cuz_ayetler):
        s_no = a["sure_no"]
        a_no = a["ayet_no"]
        sure_adi = a.get("sure_adi_tr", "")
        sayfa_no = a.get("sayfa_no", 1)

        klip_yolu = cuz_dizini / f"klip_{s_no:03d}_{a_no:03d}.mp4"
        ilerleme_yuzdesi = i / max(1, toplam_ayet_sayisi)

        # Eğer klip zaten varsa yeniden üretme (önbellek)
        if not klip_yolu.exists() or klip_yolu.stat().st_size < 10000:
            hatim_ayet_klibi_uret(
                sure_no=s_no,
                ayet_no=a_no,
                cikti_mp4=klip_yolu,
                cuz_ilerleme_yuzdesi=ilerleme_yuzdesi,
            )

        # Süre hesapla
        klip_suresi = ses_sure_hesapla(klip_yolu)
        bolum_adi = f"{sure_adi} Sûresi, {a_no}. Âyet (Sayfa {sayfa_no})"
        bolum_zamanlari.append((kumulatif_zaman, bolum_adi))
        kumulatif_zaman += klip_suresi
        klip_yollari.append(klip_yolu)

    # 1. FFmpeg Concat Listesi Oluştur
    concat_list_file = cuz_dizini / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in klip_yollari:
            f.write(f"file '{p.resolve()}'\n")

    if cikti_mp4 is None:
        cikti_mp4 = HATIM_CIKTI_DIR / f"Ezan_Plus_Hatim_Cuz_{cuz_no:02d}.mp4"

    # 2. FFmpeg Stream Copy ile Anında Birleştir
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(cikti_mp4),
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg birleştirme hatası: {res.stderr.decode('utf-8', errors='ignore')}")

    # 3. YouTube Bölümler Dosyası (.txt)
    bolumler_txt = cikti_mp4.with_suffix(".chapters.txt")
    with open(bolumler_txt, "w", encoding="utf-8") as f:
        f.write(f"Ezan Plus — {cuz_no}. Cüz Hatim-i Şerif (Mukabele)\n")
        f.write(f"Hafız: Şeyh Mişari Râşid el-Afâsî\n")
        f.write(f"Toplam Süre: {int(kumulatif_zaman // 60):02d}:{int(kumulatif_zaman % 60):02d}\n\n")
        f.write("Zaman Damgaları (YouTube Chapters):\n")
        for t_val, b_ad in bolum_zamanlari:
            dakika = int(t_val // 60)
            saniye = int(t_val % 60)
            f.write(f"{dakika:02d}:{saniye:02d} - {b_ad}\n")

    log.info(f"{cuz_no}. Cüz Hatim videosu başarıyla tamamlandı: {cikti_mp4}")
    return cikti_mp4, bolumler_txt
