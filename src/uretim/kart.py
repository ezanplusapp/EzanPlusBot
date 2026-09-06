"""
sablon_ciz.py — Ezan Plus Görsel Tasarım ve Çizim Motoru
Pillow kullanarak Ezan Plus kurumsal kimliğine %100 sadık,
1080x1350 px (4:5 dikey post) görsel şablonları üretir.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np

from ..ayar import KOK_DIZIN, AYARLAR, get_renk

log = logging.getLogger(__name__)

# Dizinler
FONTLAR = KOK_DIZIN / "assets" / "fonts"
IKONLAR = KOK_DIZIN / "assets" / "icons"
CIKTI_DIZINI = KOK_DIZIN / AYARLAR.get("genel", {}).get("cikti_klasoru", "data/cikti")
CIKTI_DIZINI.mkdir(parents=True, exist_ok=True)

# Font Yolları (Tam Türkçe ve Arapça Destekli)
FONT_ARAPCA = FONTLAR / "amiri-700-arabic.ttf"
FONT_BASLIK = FONTLAR / "IbarraRealNova.ttf"
FONT_GOVDE = FONTLAR / "Lora.ttf"
FONT_UI = FONTLAR / "Manrope.ttf"
FONT_BASKERVILLE = FONTLAR / "Baskerville-Bold.ttf"

# Boyutlar (4:5 Instagram Portrait)
GENISLIK = AYARLAR.get("boyutlar", {}).get("feed_genislik", 1080)
YUKSEKLIK = AYARLAR.get("boyutlar", {}).get("feed_yukseklik", 1350)


def font_al(yol: Path, boyut: int, agirlik: Optional[int] = None) -> ImageFont.FreeTypeFont:
    """Belirtilen boyutta ve kalınlıkta (weight) font yükler, bulunamazsa varsayılana döner."""
    try:
        f = ImageFont.truetype(str(yol), boyut)
        if agirlik is not None:
            try:
                f.set_variation_by_axes([agirlik])
            except Exception:
                pass
        return f
    except Exception as e:
        log.warning(f"Font yüklenemedi {yol}: {e}, varsayılan fonta geçiliyor.")
        return ImageFont.load_default()


_reshaper_config = {
    "delete_harakat": False,
    "support_ligatures": True,
}
_reshaper = arabic_reshaper.ArabicReshaper(configuration=_reshaper_config)


ARAPCA_HARF_HARITASI = {
    'ا': 'E', 'أ': 'E', 'إ': 'İ', 'آ': 'Â', 'ب': 'B', 'ت': 'T', 'ث': 'S',
    'ج': 'C', 'ح': 'H', 'خ': 'H', 'د': 'D', 'ذ': 'Z', 'ر': 'R', 'ز': 'Z',
    'س': 'S', 'ش': 'Ş', 'ص': 'S', 'ض': 'D', 'ط': 'T', 'ظ': 'Z', 'ع': 'A',
    'غ': 'G', 'ف': 'F', 'ق': 'K', 'ك': 'K', 'ل': 'L', 'م': 'M', 'ن': 'N',
    'ه': 'H', 'و': 'V', 'ي': 'Y', 'ى': 'Y', 'ء': "'"
}


def kok_latinize_et(kok: str) -> str:
    """Eğer kök metninde Arap harfleri varsa Lora/Latin fontunda kutu (missing glyph) olmaması için Latinize eder."""
    if not kok:
        return ""
    sonuc = []
    for ch in kok:
        if ch in ARAPCA_HARF_HARITASI:
            sonuc.append(ARAPCA_HARF_HARITASI[ch])
        elif 0x0600 <= ord(ch) <= 0x06FF:
            # Hareke veya ek karakterleri atla
            continue
        else:
            sonuc.append(ch)
    return "".join(sonuc)


def arapca_hazirla(metin: str) -> str:
    """Arapça metni sağdan sola, harf bitişmelerine ve tam harekelerine göre düzenler."""
    if not metin:
        return ""
    # Noktalama temizliği & Arapça hareke çakışması önleme (Amiri fontu glif kutusu [] koruması)
    metin = metin.strip()
    metin = re.sub(r'[:：\s-]+$', '', metin)  # Sonda kalan iki nokta veya tireyi temizle
    metin = re.sub(r'([\u0600-\u06FF])\s*:\s*', r'\1 - ', metin)  # Hareke + : çakışmasını önle
    metin = metin.replace(',', '،').replace(';', '؛')  # Latin noktalama işaretlerini Arapça karşılıklarına dönüştür
    yeniden_sekillendir = _reshaper.reshape(metin)
    return get_display(yeniden_sekillendir)



def arapca_satirla(metin: str, font: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Arapça metni kelime bazında doğru satırlara ayırır ve her satırı bağımsız RTL biçimlendirir."""
    if not metin:
        return []
    kelimeler = metin.strip().split()
    satirlar = []
    mevcut = []
    for k in kelimeler:
        deneme = " ".join(mevcut + [k])
        gorsel = arapca_hazirla(deneme)
        bbox = draw.textbbox((0, 0), gorsel, font=font)
        if (bbox[2] - bbox[0]) <= azami_genislik:
            mevcut.append(k)
        else:
            if mevcut:
                satirlar.append(arapca_hazirla(" ".join(mevcut)))
                mevcut = [k]
            else:
                satirlar.append(arapca_hazirla(k))
                mevcut = []
    if mevcut:
        satirlar.append(arapca_hazirla(" ".join(mevcut)))
    return satirlar


def metin_satirla(metin: str, font: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Metni belirtilen azami piksel genişliğine göre satırlara böler."""
    if not metin:
        return []

    paragraflar = metin.split("\n")
    sonuc_satirlar = []

    for para in paragraflar:
        kelimeler = para.strip().split()
        if not kelimeler:
            continue

        mevcut_satir = []
        for kelime in kelimeler:
            test_satir = " ".join(mevcut_satir + [kelime])
            bbox = draw.textbbox((0, 0), test_satir, font=font)
            w = bbox[2] - bbox[0]
            if w <= azami_genislik:
                mevcut_satir.append(kelime)
            else:
                if mevcut_satir:
                    sonuc_satirlar.append(" ".join(mevcut_satir))
                    mevcut_satir = [kelime]
                else:
                    sonuc_satirlar.append(kelime)
                    mevcut_satir = []

        if mevcut_satir:
            sonuc_satirlar.append(" ".join(mevcut_satir))

    return sonuc_satirlar


def kelime_basligi_satirla(metin: str, font: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """
    Türkçe hero kelime başlığını satırlara böler.
    Tek satıra sığıyorsa tek satır; sığmıyorsa boşluklardan veya tirelerden böler.
    """
    if not metin:
        return []
    bb = draw.textbbox((0, 0), metin, font=font)
    if (bb[2] - bb[0]) <= azami_genislik:
        return [metin]

    # Boşluk varsa kelime bazlı böl
    if " " in metin:
        return metin_satirla(metin, font, azami_genislik, draw)

    # Tire varsa tireden böl
    if "-" in metin:
        parts = metin.split("-")
        lines = []
        cur = ""
        for p in parts:
            cand = f"{cur}-{p}" if cur else p
            c_bb = draw.textbbox((0, 0), cand + "-", font=font)
            if (c_bb[2] - c_bb[0]) <= azami_genislik:
                cur = cand
            else:
                if cur:
                    lines.append(cur + "-")
                cur = p
        if cur:
            lines.append(cur)
        return lines

    return [metin]


def parse_markdown_bold(metin: str) -> List[Tuple[str, bool]]:
    """Metindeki **bold** kısımları ayrıştırarak (kelime, is_bold) listesi döner.
    Noktalama işaretlerini önceki kelimeye yapıştırarak 'kelime ,' boşluk hatasını önler."""
    parcalar = re.split(r'(\*\*.*?\*\*)', metin)
    tokenlar = []
    noktalama_regex = re.compile(r'^([,\.;:!?\)’”"]+)(.*)$')
    for parca in parcalar:
        if not parca:
            continue
        if parca.startswith('**') and parca.endswith('**'):
            icerik = parca[2:-2]
            for kelime in icerik.split():
                tokenlar.append((kelime, True))
        else:
            for kelime in parca.split():
                m = noktalama_regex.match(kelime)
                if m and tokenlar:
                    nokta, kalan = m.group(1), m.group(2)
                    onceki_kelime, onceki_bold = tokenlar[-1]
                    tokenlar[-1] = (onceki_kelime + nokta, onceki_bold)
                    if kalan:
                        tokenlar.append((kalan, False))
                else:
                    tokenlar.append((kelime, False))
    return tokenlar


def wrap_mixed_tokens(tokens: List[Tuple[str, bool]], font_reg: ImageFont.FreeTypeFont, font_bold: ImageFont.FreeTypeFont, azami_genislik: int, draw: ImageDraw.ImageDraw):
    """Mixed regular/bold kelimeleri piksel genişliğine göre satırlara böler."""
    space_w = draw.textbbox((0, 0), ' ', font=font_reg)[2] - draw.textbbox((0, 0), ' ', font=font_reg)[0]
    satirlar = []
    mevcut_satir = []
    mevcut_w = 0

    for kelime, is_bold in tokens:
        f = font_bold if is_bold else font_reg
        bb = draw.textbbox((0, 0), kelime, font=f)
        kelime_w = bb[2] - bb[0]

        # Noktalama ile başlıyorsa önceki kelimeye yapışık kabul et
        is_noktalama = bool(re.match(r'^[,\.;:!?\)’”"]', kelime))
        eklenecek_space = 0 if is_noktalama else space_w

        gereken_w = kelime_w if not mevcut_satir else (mevcut_w + eklenecek_space + kelime_w)
        if gereken_w <= azami_genislik:
            mevcut_satir.append((kelime, is_bold, kelime_w))
            mevcut_w = gereken_w
        else:
            if mevcut_satir:
                satirlar.append((mevcut_satir, mevcut_w))
                mevcut_satir = [(kelime, is_bold, kelime_w)]
                mevcut_w = kelime_w
            else:
                satirlar.append(([(kelime, is_bold, kelime_w)], kelime_w))
                mevcut_satir = []
                mevcut_w = 0
    if mevcut_satir:
        satirlar.append((mevcut_satir, mevcut_w))
    return satirlar, space_w


def yuvarlak_kose_ciz(
    draw: ImageDraw.ImageDraw,
    kutu: Tuple[int, int, int, int],
    radius: int,
    dolgu: str,
    kenarlik: Optional[str] = None,
    kenarlik_kalinlik: int = 1,
):
    """Yumuşak köşeli dikdörtgen çizer."""
    x1, y1, x2, y2 = kutu
    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=dolgu,
        outline=kenarlik if kenarlik else None,
        width=kenarlik_kalinlik if kenarlik else 0,
    )


def rozet_ciz(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    metin: str,
    font: ImageFont.FreeTypeFont,
    bg_renk: str,
    yazi_renk: str,
    padding_x: int = 24,
    padding_y: int = 10,
    radius: int = 16,
) -> int:
    """Başlık / Kategori hap rozeti (Pill badge) çizer ve rozetin genişliğini döner."""
    bbox = draw.textbbox((0, 0), metin, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    toplam_w = w + (padding_x * 2)
    toplam_h = h + (padding_y * 2)

    yuvarlak_kose_ciz(draw, (x, y, x + toplam_w, y + toplam_h), radius=radius, dolgu=bg_renk)
    draw.text((x + padding_x, y + padding_y - 2), metin, font=font, fill=yazi_renk)
    return toplam_w


def _kart_tabani_ve_ust_bar(
    kategori_rozet: str,
    rozet_bg: str,
    rozet_yazi: str,
    alt_baslik: str = "GÜNLÜK İBADET YARDIMCINIZ",
    format_tipi: str = "4:5",
) -> Tuple[Image.Image, ImageDraw.ImageDraw, int, int, int, int]:
    """Tüm postlarda ortak olan Ezan Plus kağıt zeminini ve kurumsal üst barını hazırlar."""
    genislik = 1080
    if format_tipi == "9:16":
        yukseklik = 1920
        kart_kenar_payi = 54
        kart_y1 = 180
        kart_y2 = 1740
    else:  # 4:5
        yukseklik = 1350
        kart_kenar_payi = 56
        kart_y1 = 80
        kart_y2 = 1270

    bg_krem = get_renk("bg_krem", "#F4F1EA")
    im = Image.new("RGB", (genislik, yukseklik), bg_krem)
    draw = ImageDraw.Draw(im)

    kart_x1 = kart_kenar_payi
    kart_x2 = genislik - kart_kenar_payi

    bg_kagit = get_renk("bg_kagit", "#FFFDF5")
    kenarlik_renk = get_renk("kenarlik", "#E5E0D0")
    yuvarlak_kose_ciz(
        draw,
        (kart_x1, kart_y1, kart_x2, kart_y2),
        radius=36,
        dolgu=bg_kagit,
        kenarlik=kenarlik_renk,
        kenarlik_kalinlik=2,
    )

    logo_yolu = IKONLAR / "logo.png"
    imleç_y = kart_y1 + 44
    sol_x = kart_x1 + 48

    if logo_yolu.exists():
        try:
            logo = Image.open(logo_yolu).convert("RGBA")
            logo = logo.resize((64, 64), Image.Resampling.LANCZOS)
            maske = Image.new("L", (64, 64), 0)
            draw_m = ImageDraw.Draw(maske)
            draw_m.rounded_rectangle([0, 0, 64, 64], radius=16, fill=255)
            im.paste(logo, (sol_x, imleç_y), maske)
        except Exception:
            pass

    font_marka = font_al(FONT_UI, 28)
    draw.text((sol_x + 80, imleç_y + 6), "EZAN PLUS", font=font_marka, fill=get_renk("kirmizi", "#C0392B"))
    font_alt_marka = font_al(FONT_UI, 18)
    draw.text((sol_x + 80, imleç_y + 38), alt_baslik, font=font_alt_marka, fill=get_renk("metin_soluk", "#64748B"))

    # Sağ Üst Kategori Rozeti
    font_rozet = font_al(FONT_UI, 20)
    bbox_r = draw.textbbox((0, 0), kategori_rozet, font=font_rozet)
    rw = bbox_r[2] - bbox_r[0] + 40
    rozet_x = kart_x2 - 48 - rw
    rozet_ciz(
        draw,
        rozet_x,
        imleç_y + 8,
        kategori_rozet,
        font=font_rozet,
        bg_renk=rozet_bg,
        yazi_renk=rozet_yazi,
        padding_x=20,
        padding_y=8,
        radius=14,
    )

    ayrac_y = imleç_y + 90
    draw.line([(kart_x1 + 48, ayrac_y), (kart_x2 - 48, ayrac_y)], fill="#F1ECE1", width=2)

    return im, draw, kart_x1, kart_y1, kart_x2, kart_y2


def _alt_bar_ciz(draw: ImageDraw.ImageDraw, kart_x1: int, kart_x2: int, kart_y2: int, sol_mesaj: str):
    """Ortak footer çizer."""
    alt_y = kart_y2 - 76
    draw.line([(kart_x1 + 48, alt_y), (kart_x2 - 48, alt_y)], fill="#F1ECE1", width=1)

    font_alt = font_al(FONT_UI, 20)
    draw.text((kart_x1 + 48, alt_y + 24), f"•  {sol_mesaj}", font=font_alt, fill=get_renk("metin_soluk", "#64748B"))

    alt_sag_metin = "@ezanplusapp"
    bbox_as = draw.textbbox((0, 0), alt_sag_metin, font=font_alt)
    asw = bbox_as[2] - bbox_as[0]
    draw.text((kart_x2 - 48 - asw, alt_y + 24), alt_sag_metin, font=font_alt, fill=get_renk("kirmizi", "#C0392B"))


def ayet_karti_ciz(
    sure_ayet: str,
    turkce_meal: str,
    arapca_metin: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    vurgulanan_kelime: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
    format_tipi: str = "4:5",
) -> Path:
    """
    Ezan Plus V16 Standartlarında Kur'an-ı Kerim Âyet Kartı (4:5 veya 9:16).
    - Baskerville Bold 42pt 'AYET-İ KERİME' İslam Yeşili rozeti (#1B4332)
    - Sıcak Parşömen Taç: Sûre ve Âyet künyesi
    - Heybetli Amiri 700 Arapça Hat
    - Ibarra Real Nova Mixed Bold Türkçe Meal
    - Tefekkür & Hikmet Kutusu
    - Vektörel Store İkonlu Ezan Plus CTA Butonu
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350

    im = Image.new("RGB", (w, h), "#FBF9F4")
    draw = ImageDraw.Draw(im)

    yesil_ton = "#1B4332"
    bordo_ton = "#8B1D24"
    altin_ton = "#C29B38"

    # 1. KART ÇERÇEVESİ (Safe Area Korumalı)
    if format_tipi == "9:16":
        kx1, ky1 = 64, 180
        kx2, ky2 = w - 64, 1740
    else:  # 4:5
        kx1, ky1 = 64, 70
        kx2, ky2 = w - 64, 1280

    for g in range(6, 0, -2):
        yuvarlak_kose_ciz(draw, (kx1 - g, ky1 - g, kx2 + g, ky2 + g), radius=36 + g, dolgu="#ECE6D8")
    yuvarlak_kose_ciz(draw, (kx1, ky1, kx2, ky2), radius=36, dolgu="#FFFDF9", kenarlik="#EAE4D5", kenarlik_kalinlik=2)

    # 2. HEADER: LOGO - ROZET - MARKA
    cur_y = ky1 + (32 if format_tipi == "9:16" else 26)
    sol_x = kx1 + 36
    sag_x = kx2 - 36
    mid_header_y = cur_y + 35

    # A) Logo (68x68 px)
    logo_size = 68
    logo_p = IKONLAR / "logo.png"
    if logo_p.exists():
        logo = Image.open(logo_p).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=18, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # B) Sağ Alan: Ezan Plus + KUR'AN-I KERİM MEÂLİ
    font_sub = font_al(FONT_UI, 13, agirlik=600)
    s_txt = "KUR'AN-I KERİM MEÂLİ"
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

    # C) Ortada: Baskerville Bold 42pt AYET-İ KERİME Rozeti
    font_rozet = font_al(FONT_BASKERVILLE, 42, agirlik=700)
    r_txt = "AYET-İ KERİME"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    pad_x = 40
    rozet_w = rw + pad_x * 2
    rozet_h = 70
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_header_y - rozet_h // 2

    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu=yesil_ton)
    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1
    draw.text((rx, ry + 1), r_txt, font=font_rozet, fill=(10, 40, 25, 100))
    draw.text((rx, ry), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç Hattı
    ayrac_y = cur_y + (88 if format_tipi == "9:16" else 84)
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 80, ayrac_y), (w // 2 + 80, ayrac_y)], fill=altin_ton, width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill=altin_ton)

    # 3. ALT ALANLAR & TEFEKKÜR KUTUSU & CTA BUTONU
    cta_cy = ky2 - (68 if format_tipi == "9:16" else 58)
    _cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=(74 if format_tipi == "9:16" else 66))

    alt_cizgi_y = cta_cy - (60 if format_tipi == "9:16" else 50)
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    box_w = (kx2 - kx1) - 64  # 888 px
    box_x1 = kx1 + 32
    box_x2 = kx2 - 32
    text_max_w = box_w - 44

    # Tefekkür & Ders Kutusu
    tef_metni = (tefekkur_notu or "Bu mübarek ayet, hayatın karmaşasında kalbimize huzur, yolumuza ilahi bir rehberlik ve sonsuz bir teslimiyet sunmaktadır.").strip()
    font_tef = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 19, agirlik=400)
    tef_line_h = 36 if format_tipi == "9:16" else 28
    tef_satirlar = metin_satirla(tef_metni, font_tef, box_w - 48, draw)
    kutu_h = (56 if format_tipi == "9:16" else 46) + (len(tef_satirlar) * tef_line_h) + (16 if format_tipi == "9:16" else 12)

    kutu_y2 = alt_cizgi_y - 14
    kutu_y1 = kutu_y2 - kutu_h

    yuvarlak_kose_ciz(draw, (box_x1, kutu_y1, box_x2, kutu_y2), radius=20, dolgu="#F0FDF4", kenarlik="#DCFCE7", kenarlik_kalinlik=1)
    draw.rounded_rectangle([box_x1, kutu_y1, box_x1 + 6, kutu_y2], radius=3, fill=yesil_ton)
    draw.ellipse([box_x1 + 24, kutu_y1 + (24 if format_tipi == "9:16" else 18), box_x1 + 32, kutu_y1 + (32 if format_tipi == "9:16" else 26)], fill=yesil_ton)
    draw.text((box_x1 + 42, kutu_y1 + (18 if format_tipi == "9:16" else 14)), "GÜNÜN HİKMETİ & TEFEKKÜRÜ", font=font_al(FONT_UI, 19 if format_tipi == "9:16" else 17, agirlik=700), fill=yesil_ton)

    fy = kutu_y1 + (56 if format_tipi == "9:16" else 46)
    for sat in tef_satirlar:
        draw.text((box_x1 + 24, fy), sat, font=font_tef, fill="#166534")
        fy += tef_line_h

    free_vertical = kutu_y1 - ayrac_y

    # 4. TÜRKÇE MEAL (HERO ELEMENT & MIXED BOLD)
    temiz_meal = turkce_meal.strip("“”\"' ")
    if vurgulanan_kelime and ("**" not in temiz_meal) and (vurgulanan_kelime in temiz_meal):
        temiz_meal = temiz_meal.replace(vurgulanan_kelime, f"**{vurgulanan_kelime}**")

    meal_len = len(re.sub(r'\*\*', '', temiz_meal))
    ar_ham = (arapca_metin or "").strip()
    ar_len = len(ar_ham)

    if format_tipi == "9:16":
        if meal_len < 45:
            font_meal_boyut = 66
        elif meal_len < 80:
            font_meal_boyut = 58
        elif meal_len < 140:
            font_meal_boyut = 50
        elif meal_len < 200:
            font_meal_boyut = 44
        else:
            font_meal_boyut = 40
    else:
        if meal_len < 45:
            font_meal_boyut = 62
        elif meal_len < 80:
            font_meal_boyut = 54
        elif meal_len < 140:
            font_meal_boyut = 46
        elif meal_len < 200:
            font_meal_boyut = 41
        else:
            font_meal_boyut = 38

    font_meal_reg = font_al(FONT_BASLIK, font_meal_boyut, agirlik=400)
    font_meal_bold = font_al(FONT_BASLIK, font_meal_boyut, agirlik=700)

    meal_tokens = parse_markdown_bold(temiz_meal)
    tr_wrapped_lines, space_w = wrap_mixed_tokens(meal_tokens, font_meal_reg, font_meal_bold, box_w - 30, draw)
    tr_line_h = int(font_meal_boyut * 1.44)
    tr_toplam_h = len(tr_wrapped_lines) * tr_line_h

    # Kaynak Rozeti
    kaynak_metni = sure_ayet.strip()
    font_k_pt = 24 if format_tipi == "9:16" else (24 if meal_len < 80 else 22)
    font_kaynak = font_al(FONT_BASLIK, font_k_pt)
    kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    kaynak_h = 42 if format_tipi == "4:5" else 46

    # 5. SERLEVHA KUTUSU (ARAPÇA METİN VE PARŞÖMEN TAÇ)
    MIN_VERTICAL_GAP = 28 if format_tipi == "9:16" else 24
    tac_h = 48 if format_tipi == "9:16" else (46 if meal_len < 80 else 42)
    pad_ic_ust = 40 if format_tipi == "9:16" else (34 if meal_len < 80 else 28)
    pad_ic_alt = 38 if format_tipi == "9:16" else (34 if meal_len < 80 else 28)

    # Arapça Metin Temizliği (Secavend ve durak işaretlerini ayıkla)
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", ar_ham).strip()
    if not ar_temiz:
        ar_temiz = ar_ham

    # Akıllı Arapça Autofit & Dinamik Ink Clearance (Ayet Motoru Standardı)
    if format_tipi == "9:16":
        start_pt = 114 if ar_len < 35 else (98 if ar_len < 65 else (84 if ar_len < 120 else 72))
        min_pt = 46
    else:
        start_pt = 98 if ar_len < 35 else (86 if ar_len < 65 else (72 if ar_len < 120 else 52))
        min_pt = 40

    hedef_satir_sayilari = [1, 2] if ar_len < 65 else [2, 3, 4]
    font_ar_boyut = min_pt
    ar_satirlar = []
    found_ar = False

    if ar_len > 0:
        for target_l in hedef_satir_sayilari:
            for test_pt in range(start_pt, min_pt - 1, -2):
                f_test = font_al(FONT_ARAPCA, test_pt)
                sats = arapca_satirla(ar_temiz, f_test, text_max_w, draw)
                if not sats or len(sats) > target_l:
                    continue

                max_line_w = max(draw.textbbox((0, 0), s, font=f_test)[2] - draw.textbbox((0, 0), s, font=f_test)[0] for s in sats)
                if max_line_w > text_max_w:
                    continue

                # Yetim kelime önleme: Son satırda tek kelime kalmışsa reddet
                if len(sats) >= 2 and len(sats[-1].split()) == 1 and len(sats[-1].strip()) < 16:
                    if test_pt > min_pt + 4:
                        continue

                # Gerçek mürekkep yüksekliği simülasyonu
                sim_prev_ink = 0
                for s_idx, s in enumerate(sats):
                    bb = draw.textbbox((0, 0), s, font=f_test)
                    top_ink, bottom_ink = bb[1], bb[3]
                    l_y = -top_ink if s_idx == 0 else (sim_prev_ink + MIN_VERTICAL_GAP - top_ink)
                    sim_prev_ink = l_y + bottom_ink

                sim_total_ar_h = sim_prev_ink
                sim_box_h = tac_h + pad_ic_ust + sim_total_ar_h + pad_ic_alt
                sim_kalan = free_vertical - (sim_box_h + tr_toplam_h + kaynak_h)
                min_kalan = 40 if format_tipi == "9:16" else 28

                if sim_kalan >= min_kalan:
                    font_ar_boyut = test_pt
                    ar_satirlar = sats
                    found_ar = True
                    break
            if found_ar:
                break

        if not ar_satirlar:
            font_ar = font_al(FONT_ARAPCA, font_ar_boyut)
            ar_satirlar = arapca_satirla(ar_temiz, font_ar, text_max_w, draw)
        else:
            font_ar = font_al(FONT_ARAPCA, font_ar_boyut)

        ar_offsets = []
        prev_ink_bottom = 0
        for s_idx, asat in enumerate(ar_satirlar):
            bb = draw.textbbox((0, 0), asat, font=font_ar)
            top_ink, bottom_ink = bb[1], bb[3]
            l_y = -top_ink if s_idx == 0 else (prev_ink_bottom + MIN_VERTICAL_GAP - top_ink)
            ar_offsets.append(l_y)
            prev_ink_bottom = l_y + bottom_ink
        total_ar_h = prev_ink_bottom
    else:
        font_ar = font_al(FONT_ARAPCA, min_pt)
        ar_offsets = []
        total_ar_h = 0

    kutu_icerik_h = pad_ic_ust + total_ar_h + pad_ic_alt
    kutu_toplam_h = tac_h + kutu_icerik_h

    # 6. DİKEY FLEX DAĞILIMI (DENGELİ MERKEZLEME VE EŞİT NEFES ALANI)
    kalan_bosluk = free_vertical - (kutu_toplam_h + tr_toplam_h + kaynak_h)
    if kalan_bosluk < 40:
        kalan_bosluk = 40

    gap_ust = max(24, min(70 if format_tipi == "4:5" else 105, int(kalan_bosluk * 0.22)))
    gap_kutu_tr = max(32, min(56 if format_tipi == "4:5" else 82, int((kalan_bosluk - gap_ust) * 0.40)))
    gap_kaynak_alt = kalan_bosluk - (gap_ust + gap_kutu_tr)

    box_y1 = ayrac_y + gap_ust
    box_y2 = box_y1 + kutu_toplam_h

    # Kutu Çizimi
    yuvarlak_kose_ciz(draw, (box_x1, box_y1, box_x2, box_y2), radius=22, dolgu="#FAF8F3", kenarlik="#E2D7C3", kenarlik_kalinlik=1)

    # Sıcak Parşömen Taç
    yuvarlak_kose_ciz(draw, (box_x1, box_y1, box_x2, box_y1 + tac_h + 10), radius=22, dolgu="#F5EFE3")
    draw.rectangle([box_x1, box_y1 + tac_h, box_x2, box_y1 + tac_h + 10], fill="#FAF8F3")
    draw.line([(box_x1 + 16, box_y1 + tac_h), (box_x2 - 16, box_y1 + tac_h)], fill="#E2D7C3", width=1)
    draw.ellipse([w // 2 - 4, box_y1 + tac_h - 4, w // 2 + 4, box_y1 + tac_h + 4], fill=altin_ton)

    intro_txt = f"{sure_ayet} • Kelâm-ı İlâhî"
    font_intro = font_al(FONT_BASLIK, 21 if format_tipi == "9:16" else (20 if meal_len < 80 else 18), agirlik=700)
    intro_bb = draw.textbbox((0, 0), intro_txt, font=font_intro)
    draw.text(((w - (intro_bb[2] - intro_bb[0])) // 2, box_y1 + (tac_h - (intro_bb[3] - intro_bb[1])) // 2 - intro_bb[1]), intro_txt, font=font_intro, fill=yesil_ton)

    # Arapça Hat Çizimi (Gerçek Mürekkep Hizalaması)
    if ar_satirlar:
        content_base_y = box_y1 + tac_h + pad_ic_ust
        for s_idx, s in enumerate(ar_satirlar):
            bb = draw.textbbox((0, 0), s, font=font_ar)
            line_w = bb[2] - bb[0]
            line_x = (w - line_w) // 2
            line_y = content_base_y + ar_offsets[s_idx]
            draw.text((line_x, line_y), s, font=font_ar, fill=yesil_ton)

    # 7. TÜRKÇE MEAL ÇİZİMİ (Ortalanmış ve Tırnak Filigranlı)
    meal_y = box_y2 + gap_kutu_tr
    font_fili_pt = int(font_meal_boyut * 2.3)
    font_fili = font_al(FONT_BASLIK, font_fili_pt, agirlik=700)
    draw.text((w // 2 - 120, meal_y - int(font_fili_pt * 0.45)), "“", font=font_fili, fill="#EFE8DA")

    cur_my = meal_y
    for l_tokens, l_w in tr_wrapped_lines:
        line_start_x = (w - l_w) // 2
        cur_tok_x = line_start_x
        for tok_text, is_bold, word_w in l_tokens:
            f_tok = font_meal_bold if is_bold else font_meal_reg
            f_color = "#111827" if is_bold else "#1C1917"
            draw.text((cur_tok_x, cur_my), tok_text, font=f_tok, fill=f_color)
            cur_tok_x += word_w + space_w
        cur_my += tr_line_h

    # 8. MUTEBER KAYNAK ROZETİ
    kaynak_y = cur_my + int(gap_kaynak_alt * 0.40)
    badge_w = kw + 56
    bx1 = (w - badge_w) // 2
    bx2 = bx1 + badge_w
    by1 = kaynak_y
    by2 = by1 + kaynak_h

    yuvarlak_kose_ciz(draw, (bx1, by1, bx2, by2), radius=kaynak_h // 2, dolgu="#F3EEE3", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.ellipse([bx1 + 18, by1 + kaynak_h // 2 - 4, bx1 + 26, by1 + kaynak_h // 2 + 4], fill=yesil_ton)
    draw.text((bx1 + 34, by1 + (kaynak_h - (draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[3] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[1])) // 2 - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[1]), kaynak_metni, font=font_kaynak, fill=yesil_ton)

    if not cikti_dosya_adi:
        cikti_dosya_adi = f"ayet_v16_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=95)
    log.info(f"V16 Âyet kartı başarıyla çizildi: {cikti_yolu} ({format_tipi})")
    return cikti_yolu


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


def _cta_butonu_ciz(im: Image.Image, draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int = 670, h: int = 74):
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

    logo_yolu = IKONLAR / "logo.png"
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

    apple_yolu = IKONLAR / "apple.png"
    ap_size = 25
    ap_x = ps_x - ap_size - 18
    ap_y = btn_mid_y - ap_size // 2
    if apple_yolu.exists():
        apple_img = Image.open(apple_yolu).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        im.paste(apple_img, (ap_x, ap_y), apple_img)


def hadis_karti_ciz(
    hadis_metni: str,
    kaynak_ravi: Optional[str] = None,
    kaynak: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
    format_tipi: str = "4:5",
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    ravi: Optional[str] = None,
    tac_stili: str = "sicak_parcomen",
    vurgulanan_kelime: Optional[str] = None,
) -> Path:
    """
    Ezan Plus Sahih Hadis şablonu (V16 Mimarisi - Proportional Layout & Sıcak Parşömen Taç).
    1080x1350 (4:5 Feed) ve 1080x1920 (9:16 Story) tam destekler.
    tac_stili: 'sicak_parcomen' (varsayılan & önerilen), 'seffaf_cizgili', 'kirmizi_tac'
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    kirmizi_ton = "#C02128"  # Logodaki Ezan Plus kırmızısının birebir aynısı (RGB: 192, 33, 40)

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

    # 1. HEADER ALANI (SOL: 68x68 LOGO | ORTA: BASKERVILLE BOLD 42pt ROZET | SAĞ: EZAN PLUS BLOĞU)
    sol_x = kx1 + 44
    sag_x = kx2 - 44
    cur_y = ky1 + (34 if format_tipi == "9:16" else 28)
    header_h = 70
    mid_header_y = cur_y + header_h // 2
    logo_yolu = IKONLAR / "logo.png"

    # A) EN SOLDA LOGO
    logo_size = 68
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=16, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # B) EN SAĞDA "EZAN PLUS" + "SAHİH HADİS-İ ŞERİF REHBERİ"
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

    # C) ORTADA: BASKERVILLE BOLD 42pt ROZET
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

    # Genişletilmiş ferah kutu kenarları
    box_w = (kx2 - kx1) - 64  # 888 px
    box_x1 = kx1 + 32
    box_x2 = kx2 - 32
    text_max_w = box_w - 44   # 844 px

    # GÜNÜN NEBEVÎ ÖĞÜDÜ (4:5'te ferah ve kompakt safe area)
    tef_metin = (tefekkur_notu or "Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır. Hatalar tekrarlanmak için değil, ibret almak içindir.").strip()
    font_tef = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 19, agirlik=400)
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

    # 3. TÜRKÇE HADİS MEALİ (HERO ELEMENT & MIXED BOLD VURGU)
    temiz_hadis = hadis_metni.strip("“”\"' ")
    if vurgulanan_kelime and ("**" not in temiz_hadis) and (vurgulanan_kelime in temiz_hadis):
        temiz_hadis = temiz_hadis.replace(vurgulanan_kelime, f"**{vurgulanan_kelime}**")

    hadis_len = len(re.sub(r'\*\*', '', temiz_hadis))
    ar_ham = (arapca_metin or "لاَ يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ").strip()
    ar_len = len(ar_ham)

    # 1. Meal Punto Seçimi (Ters Orantılı: Kısa hadislerde daha heybetli 58-66pt!)
    if format_tipi == "9:16":
        if hadis_len < 40:
            font_hadis_boyut = 66
        elif hadis_len < 75:
            font_hadis_boyut = 60
        elif hadis_len < 120:
            font_hadis_boyut = 54
        elif hadis_len < 180:
            font_hadis_boyut = 48
        else:
            font_hadis_boyut = 42
    else:
        if hadis_len < 40:
            font_hadis_boyut = 62
        elif hadis_len < 75:
            font_hadis_boyut = 56
        elif hadis_len < 120:
            font_hadis_boyut = 50
        elif hadis_len < 180:
            font_hadis_boyut = 45
        else:
            font_hadis_boyut = 41

    font_hadis_reg = font_al(FONT_BASLIK, font_hadis_boyut, agirlik=400)
    font_hadis_bold = font_al(FONT_BASLIK, font_hadis_boyut, agirlik=700)

    meal_tokens = parse_markdown_bold(temiz_hadis)
    tr_wrapped_lines, space_w = wrap_mixed_tokens(meal_tokens, font_hadis_reg, font_hadis_bold, box_w - 30, draw)
    tr_line_h = int(font_hadis_boyut * 1.44)
    tr_toplam_h = len(tr_wrapped_lines) * tr_line_h

    raw_kaynak = (kaynak_ravi or kaynak or "Buhârî ve Müslim").strip()
    kaynak_metni = re.split(r'[\.;,]?\s*Ayrıca bkz?[\.:]?', raw_kaynak, flags=re.IGNORECASE)[0].strip()
    if not kaynak_metni:
        kaynak_metni = raw_kaynak

    max_badge_w = box_w - 60
    font_k_pt = 24 if format_tipi == "9:16" else (24 if hadis_len < 60 else 22)
    font_kaynak = font_al(FONT_BASLIK, font_k_pt)
    kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    while (kw + 52) > max_badge_w and font_k_pt > 16:
        font_k_pt -= 1
        font_kaynak = font_al(FONT_BASLIK, font_k_pt)
        kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    kaynak_h = 42 if format_tipi == "4:5" else 46

    # 4. SERLEVHA KUTUSU SAFE AREA & AKILLI ARAPÇA MİZANPAJ (Ayet Standardı)
    MIN_VERTICAL_GAP = 28 if format_tipi == "9:16" else 24
    tac_h = 48 if format_tipi == "9:16" else (46 if hadis_len < 75 else 42)
    pad_ic_ust = 40 if format_tipi == "9:16" else (34 if hadis_len < 75 else 28)
    pad_ic_alt = 38 if format_tipi == "9:16" else (34 if hadis_len < 75 else 28)

    if arapca_okunus:
        ok_ham = arapca_okunus.strip("“”\"'{}[] ")
    elif ravi:
        temiz_ravi = ravi.strip("“”\"'{}[] ")
        if re.match(r"^hz\.?\s*", temiz_ravi, re.IGNORECASE):
            temiz_ravi = re.sub(r"^hz\.?\s*", "", temiz_ravi, flags=re.IGNORECASE).strip()
        ok_ham = f"Hz. {temiz_ravi} rivayet etti"
    else:
        ok_ham = "Sahih Hadis-i Şerif"
    ok_gosterim = f"“{ok_ham}”" if ok_ham else ""
    font_ok_pt = 28 if format_tipi == "9:16" else (26 if hadis_len < 75 else 20)
    font_okunus = font_al(FONT_GOVDE, font_ok_pt)
    ok_satirlar = metin_satirla(ok_gosterim, font_okunus, box_w - 60, draw) if ok_gosterim else []
    ok_line_h = (40 if format_tipi == "9:16" else 36) if hadis_len < 75 else (32 if format_tipi == "9:16" else 26)
    ok_toplam_h = len(ok_satirlar) * ok_line_h if ok_satirlar else 0
    gap_ar_ok = (28 if format_tipi == "9:16" else 22) if ok_satirlar else 0

    # Arapça Metin Temizliği (Secavend ve durak işaretlerini ayıkla)
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", ar_ham).strip()
    if not ar_temiz:
        ar_temiz = ar_ham

    # Ayet motoru standartlarında satır hedefli autofit (Önce 2 satır, sığmazsa 3 satır)
    if format_tipi == "9:16":
        start_pt = 114 if ar_len < 35 else (98 if ar_len < 65 else (84 if ar_len < 120 else 72))
        min_pt = 50
    else:
        start_pt = 98 if ar_len < 35 else (86 if ar_len < 65 else (72 if ar_len < 120 else 54))
        min_pt = 42

    hedef_satir_sayilari = [1, 2] if ar_len < 65 else [2, 3]
    font_ar_boyut = min_pt
    ar_satirlar = []
    found_ar = False

    for target_l in hedef_satir_sayilari:
        for test_pt in range(start_pt, min_pt - 1, -2):
            f_test = font_al(FONT_ARAPCA, test_pt)
            sats = arapca_satirla(ar_temiz, f_test, text_max_w, draw)
            if not sats or len(sats) > target_l:
                continue

            max_line_w = max(draw.textbbox((0, 0), s, font=f_test)[2] - draw.textbbox((0, 0), s, font=f_test)[0] for s in sats)
            if max_line_w > text_max_w:
                continue

            # Yetim kelime önleme: Son satırda tek kelime kalmışsa reddet
            if len(sats) >= 2 and len(sats[-1].split()) == 1 and len(sats[-1].strip()) < 16:
                if test_pt > min_pt + 4:
                    continue

            # Gerçek mürekkep yüksekliği ve satır arası net clearance simülasyonu
            sim_prev_ink = 0
            for s_idx, s in enumerate(sats):
                bb = draw.textbbox((0, 0), s, font=f_test)
                top_ink, bottom_ink = bb[1], bb[3]
                l_y = -top_ink if s_idx == 0 else (sim_prev_ink + MIN_VERTICAL_GAP - top_ink)
                sim_prev_ink = l_y + bottom_ink

            sim_total_ar_h = sim_prev_ink
            sim_box_h = tac_h + pad_ic_ust + sim_total_ar_h + gap_ar_ok + ok_toplam_h + pad_ic_alt
            sim_kalan = free_vertical - (sim_box_h + tr_toplam_h + kaynak_h)
            min_kalan = 40 if format_tipi == "9:16" else 28

            if sim_kalan >= min_kalan:
                font_ar_boyut = test_pt
                ar_satirlar = sats
                found_ar = True
                break
        if found_ar:
            break

    if not ar_satirlar:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)
        ar_satirlar = arapca_satirla(ar_temiz, font_ar, text_max_w, draw)
    else:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)

    # Her satırın Y offsetini gerçek mürekkep sınırlarına göre hesapla
    ar_offsets = []
    prev_ink_bottom = 0
    for s_idx, asat in enumerate(ar_satirlar):
        bb = draw.textbbox((0, 0), asat, font=font_ar)
        top_ink, bottom_ink = bb[1], bb[3]
        l_y = -top_ink if s_idx == 0 else (prev_ink_bottom + MIN_VERTICAL_GAP - top_ink)
        ar_offsets.append(l_y)
        prev_ink_bottom = l_y + bottom_ink

    total_ar_h = prev_ink_bottom

    # Okunuş Satırları Offsetleri
    ok_offsets = []
    if ok_satirlar:
        cur_ok_off = total_ar_h + gap_ar_ok
        for osat in ok_satirlar:
            ok_offsets.append(cur_ok_off)
            cur_ok_off += ok_line_h
        total_content_h = cur_ok_off
    else:
        total_content_h = total_ar_h

    box_s_h = tac_h + pad_ic_ust + total_content_h + pad_ic_alt

    # 5. DİKEY FLEX DAĞILIMI (DENGELİ MERKEZLEME VE EŞİT NEFES ALANLARI)
    toplam_icerik_h = box_s_h + tr_toplam_h + kaynak_h
    kalan_bosluk = max(40, free_vertical - toplam_icerik_h)

    if format_tipi == "9:16":
        gap_ust = max(24, min(170, int(kalan_bosluk * 0.23)))
        kalan_orta_alt = kalan_bosluk - gap_ust
        gap_kutu_tr = max(36, min(260, int(kalan_orta_alt * 0.44)))
        gap_alt_toplam = max(40, kalan_orta_alt - gap_kutu_tr)
        gap_tr_kaynak = max(26, min(80, int(gap_alt_toplam * 0.36)))
    else:  # 4:5
        gap_ust = max(20, min(65, int(kalan_bosluk * 0.20)))
        kalan_orta_alt = kalan_bosluk - gap_ust
        gap_kutu_tr = max(28, min(65, int(kalan_orta_alt * 0.44)))
        gap_alt_toplam = max(30, kalan_orta_alt - gap_kutu_tr)
        gap_tr_kaynak = max(20, min(38, int(gap_alt_toplam * 0.40)))

    box_s_y1 = ayrac_y + gap_ust
    box_s_y2 = box_s_y1 + box_s_h

    # SERLEVHA KUTUSUNU ÇİZ
    yuvarlak_kose_ciz(draw, (box_x1, box_s_y1, box_x2, box_s_y2), radius=24, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    intro_txt = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"

    # --- TAÇ STİLİ UYGULAMASI ---
    if tac_stili == "kirmizi_tac":
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

    else:  # "seffaf_cizgili" - Klasik Mushaf Tezhip & Zarif Çizgili (En Ferah & Asil Tasarım)
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

    # Arapça Metin Çizimi (Tamamı ve Harekeli, Gerçek Mürekkep Hizalaması)
    content_base_y = box_s_y1 + tac_h + pad_ic_ust
    for s_idx, asat in enumerate(ar_satirlar):
        as_bb = draw.textbbox((0, 0), asat, font=font_ar)
        as_w = as_bb[2] - as_bb[0]
        line_x = (w - as_w) // 2
        line_y = content_base_y + ar_offsets[s_idx]
        draw.text((line_x, line_y), asat, font=font_ar, fill="#9B1B1B")

    # Latin Okunuş Çizimi (Safe area garantili)
    if ok_satirlar:
        for o_idx, osat in enumerate(ok_satirlar):
            o_bb = draw.textbbox((0, 0), osat, font=font_okunus)
            o_w = o_bb[2] - o_bb[0]
            ok_x = (w - o_w) // 2
            ok_y = content_base_y + ok_offsets[o_idx]
            draw.text((ok_x, ok_y), osat, font=font_okunus, fill="#5A4B42")

    # 6. TÜRKÇE HADİS & ZARİF PARŞÖMEN TIRNAK FİLİGRANI
    tr_y = box_s_y2 + gap_kutu_tr

    # Asil ve narin parşömen tırnak filigranı (Metinle çakışmayan, huzurlu krem tonu)
    font_fili_pt = int(font_hadis_boyut * 2.3)
    font_fili = font_al(FONT_BASLIK, font_fili_pt, agirlik=700)
    draw.text((w // 2 - 120, tr_y - int(font_fili_pt * 0.45)), "“", font=font_fili, fill="#EFE8DA")

    # TÜRKÇE MEAL ÇİZİMİ (BOLD VE REGULAR KELİMELER KUSURSUZ YANYANA)
    for line_tokens, line_w in tr_wrapped_lines:
        cur_x = (w - line_w) // 2
        for word, is_bold, word_w in line_tokens:
            f = font_hadis_bold if is_bold else font_hadis_reg
            fill_c = "#111827" if is_bold else "#1C1917"
            draw.text((cur_x, tr_y), word, font=f, fill=fill_c)
            cur_x += word_w + space_w
        tr_y += tr_line_h

    tr_y += gap_tr_kaynak

    # Kaynak Rozeti (Kart sınırlarına tam kilitli, asla taşmaz)
    kx = (w - kw) // 2
    badge_x1 = max(kx1 + 24, kx - 26)
    badge_x2 = min(kx2 - 24, kx + kw + 26)
    yuvarlak_kose_ciz(draw, (badge_x1, tr_y - 6, badge_x2, tr_y + 34), radius=12, dolgu="#FFFDF9", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.text((kx, tr_y - 1), kaynak_metni, font=font_kaynak, fill="#B45309")

    if not cikti_dosya_adi:
        cikti_dosya_adi = f"hadis_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=96)
    return cikti_yolu


def dua_karti_ciz(
    dua_basligi: str,
    turkce_anlam: str,
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    kimin_duasi: Optional[str] = None,
    kaynak_ref: Optional[str] = None,
    fazilet_notu: Optional[str] = None,
    okunus_veya_fazilet: Optional[str] = None,
    kaynak_fazilet: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
    format_tipi: str = "4:5",
    tac_stili: str = "sicak_parcomen",
    vurgulanan_kelime: Optional[str] = None,
) -> Path:
    """
    Ezan Plus Günün Duası & Manevi Niyaz şablonu (V16 Mimarisi - Proportional Layout & Sıcak Parşömen Taç).
    1080x1350 (4:5 Feed) ve 1080x1920 (9:16 Story) tam destekler.
    tac_stili: 'sicak_parcomen' (varsayılan), 'seffaf_cizgili', 'kirmizi_tac'
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    yesil_ton = "#1B4332"  # İslam Yeşili kurumsal dua rozeti (RGB: 27, 67, 50)

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

    # 1. HEADER ALANI (SOL: 68x68 LOGO | ORTA: BASKERVILLE BOLD 42pt ROZET | SAĞ: EZAN PLUS BLOĞU)
    sol_x = kx1 + 44
    sag_x = kx2 - 44
    cur_y = ky1 + (34 if format_tipi == "9:16" else 28)
    header_h = 70
    mid_header_y = cur_y + header_h // 2
    logo_yolu = IKONLAR / "logo.png"

    # A) EN SOLDA LOGO
    logo_size = 68
    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=16, fill=255)
        im.paste(logo, (sol_x, mid_header_y - logo_size // 2), mask)

    # B) EN SAĞDA "EZAN PLUS" + "MANEVİ REHBER & DUALAR"
    font_sub = font_al(FONT_UI, 13, agirlik=600)
    s_txt = "MANEVİ REHBER & DUALAR"
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

    # C) ORTADA: BASKERVILLE BOLD 42pt ROZET
    font_rozet = font_al(FONT_BASKERVILLE, 42, agirlik=700)
    r_txt = "GÜNÜN DUASI"
    r_bb = draw.textbbox((0, 0), r_txt, font=font_rozet)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    pad_x = 40
    rozet_w = rw + pad_x * 2
    rozet_h = 70
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_header_y - rozet_h // 2

    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu=yesil_ton)

    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1
    draw.text((rx, ry + 1), r_txt, font=font_rozet, fill=(10, 40, 25, 100))
    draw.text((rx, ry), r_txt, font=font_rozet, fill="#FFFFFF")

    # Ayraç Hattı
    ayrac_y = cur_y + (88 if format_tipi == "9:16" else 84)
    draw.line([(kx1 + 44, ayrac_y), (kx2 - 44, ayrac_y)], fill="#EAE4D5", width=1)
    draw.line([(w // 2 - 80, ayrac_y), (w // 2 + 80, ayrac_y)], fill="#C29B38", width=2)
    draw.ellipse([w // 2 - 5, ayrac_y - 5, w // 2 + 5, ayrac_y + 5], fill="#C29B38")

    # 2. ALT ALANLAR & FAZİLET KUTUSU & CTA BUTONU
    cta_cy = ky2 - (68 if format_tipi == "9:16" else 58)
    _cta_butonu_ciz(im, draw, w // 2, cta_cy, w=670, h=(74 if format_tipi == "9:16" else 66))

    alt_cizgi_y = cta_cy - (60 if format_tipi == "9:16" else 50)
    draw.line([(kx1 + 44, alt_cizgi_y), (kx2 - 44, alt_cizgi_y)], fill="#EFE9DC", width=1)

    # Genişletilmiş ferah kutu kenarları
    box_w = (kx2 - kx1) - 64  # 888 px
    box_x1 = kx1 + 32
    box_x2 = kx2 - 32
    text_max_w = box_w - 44   # 844 px

    # FAZİLET & HİKMET KUTUSU
    ham_fazilet = (fazilet_notu or okunus_veya_fazilet or kaynak_fazilet or "Bu mübarek niyaz, kalbe ferahlık ve işlerde kolaylık için sabah-akşam ihlasla tekrar edilir.").strip()
    # Kaynak bilgisi fazilet metninde varsa ayıkla
    if " • " in ham_fazilet:
        faz_parcalar = ham_fazilet.split(" • ", 1)
        if not kaynak_ref:
            kaynak_ref = faz_parcalar[0].strip()
        fazilet_metni = faz_parcalar[1].strip()
    else:
        fazilet_metni = ham_fazilet

    font_faz = font_al(FONT_GOVDE, 22 if format_tipi == "9:16" else 19, agirlik=400)
    faz_line_h = 36 if format_tipi == "9:16" else 28
    faz_satirlar = metin_satirla(fazilet_metni, font_faz, box_w - 48, draw)
    kutu_h = (56 if format_tipi == "9:16" else 46) + (len(faz_satirlar) * faz_line_h) + (16 if format_tipi == "9:16" else 12)

    kutu_y2 = alt_cizgi_y - 14
    kutu_y1 = kutu_y2 - kutu_h

    yuvarlak_kose_ciz(draw, (box_x1, kutu_y1, box_x2, kutu_y2), radius=20, dolgu="#F9F6EE", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.rounded_rectangle([box_x1, kutu_y1, box_x1 + 6, kutu_y2], radius=3, fill="#C29B38")
    draw.ellipse([box_x1 + 24, kutu_y1 + (24 if format_tipi == "9:16" else 18), box_x1 + 32, kutu_y1 + (32 if format_tipi == "9:16" else 26)], fill="#C29B38")
    draw.text((box_x1 + 42, kutu_y1 + (18 if format_tipi == "9:16" else 14)), "DUANIN FAZİLETİ & NE ZAMAN OKUNMALI?", font=font_al(FONT_UI, 19 if format_tipi == "9:16" else 17, agirlik=700), fill="#B45309")

    fy = kutu_y1 + (56 if format_tipi == "9:16" else 46)
    for sat in faz_satirlar:
        draw.text((box_x1 + 24, fy), sat, font=font_faz, fill="#292524")
        fy += faz_line_h

    free_vertical = kutu_y1 - ayrac_y

    # 3. TÜRKÇE DUA ANLAMI (HERO ELEMENT & MIXED BOLD VURGU)
    temiz_anlam = turkce_anlam.strip("“”\"' ")
    if vurgulanan_kelime and ("**" not in temiz_anlam) and (vurgulanan_kelime in temiz_anlam):
        temiz_anlam = temiz_anlam.replace(vurgulanan_kelime, f"**{vurgulanan_kelime}**")

    anlam_len = len(re.sub(r'\*\*', '', temiz_anlam))
    ar_ham = (arapca_metin or "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً").strip()
    ar_len = len(ar_ham)

    # 1. Dua Anlamı Punto Seçimi (Ters Orantılı: Kısa dualarda 56-66pt heybetli punto!)
    if format_tipi == "9:16":
        if anlam_len < 45:
            font_anlam_boyut = 66
        elif anlam_len < 75:
            font_anlam_boyut = 60
        elif anlam_len < 130:
            font_anlam_boyut = 52
        elif anlam_len < 190:
            font_anlam_boyut = 46
        else:
            font_anlam_boyut = 41
    else:
        if anlam_len < 45:
            font_anlam_boyut = 60
        elif anlam_len < 75:
            font_anlam_boyut = 54
        elif anlam_len < 130:
            font_anlam_boyut = 48
        elif anlam_len < 190:
            font_anlam_boyut = 43
        else:
            font_anlam_boyut = 39

    font_anlam_reg = font_al(FONT_BASLIK, font_anlam_boyut, agirlik=400)
    font_anlam_bold = font_al(FONT_BASLIK, font_anlam_boyut, agirlik=700)

    anlam_tokens = parse_markdown_bold(temiz_anlam)
    tr_wrapped_lines, space_w = wrap_mixed_tokens(anlam_tokens, font_anlam_reg, font_anlam_bold, box_w - 30, draw)
    tr_line_h = int(font_anlam_boyut * 1.44)
    tr_toplam_h = len(tr_wrapped_lines) * tr_line_h

    raw_kaynak = (kaynak_ref or "Kur'an-ı Kerim").strip()
    kaynak_metni = re.split(r'[\.;,]?\s*Ayrıca bkz?[\.:]?', raw_kaynak, flags=re.IGNORECASE)[0].strip()
    if not kaynak_metni:
        kaynak_metni = raw_kaynak

    max_badge_w = box_w - 60
    font_k_pt = 24 if format_tipi == "9:16" else (24 if anlam_len < 70 else 22)
    font_kaynak = font_al(FONT_BASLIK, font_k_pt)
    kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    while (kw + 52) > max_badge_w and font_k_pt > 16:
        font_k_pt -= 1
        font_kaynak = font_al(FONT_BASLIK, font_k_pt)
        kw = draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[2] - draw.textbbox((0, 0), kaynak_metni, font=font_kaynak)[0]
    kaynak_h = 42 if format_tipi == "4:5" else 46

    # 4. SERLEVHA KUTUSU SAFE AREA & AKILLI ARAPÇA MİZANPAJ (Ayet Standardı)
    MIN_VERTICAL_GAP = 28 if format_tipi == "9:16" else 24
    tac_h = 48 if format_tipi == "9:16" else (46 if anlam_len < 75 else 42)
    pad_ic_ust = 40 if format_tipi == "9:16" else (34 if anlam_len < 75 else 28)
    pad_ic_alt = 38 if format_tipi == "9:16" else (34 if anlam_len < 75 else 28)

    ok_gosterim = f"“{ok_ham}”" if (ok_ham := (arapca_okunus or "").strip("“”\"'{}[] ")) else ""
    font_ok_pt = 28 if format_tipi == "9:16" else (26 if anlam_len < 75 else 20)
    font_okunus = font_al(FONT_GOVDE, font_ok_pt)
    ok_satirlar = metin_satirla(ok_gosterim, font_okunus, box_w - 60, draw) if ok_gosterim else []
    ok_line_h = (40 if format_tipi == "9:16" else 36) if anlam_len < 75 else (32 if format_tipi == "9:16" else 26)
    ok_toplam_h = len(ok_satirlar) * ok_line_h if ok_satirlar else 0
    gap_ar_ok = (28 if format_tipi == "9:16" else 22) if ok_satirlar else 0

    # Arapça Metin Temizliği (Secavend ve durak işaretlerini ayıkla)
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", ar_ham).strip()
    if not ar_temiz:
        ar_temiz = ar_ham

    # Safe area bazlı Arapça autofit (Kısa dualarda 88-114pt heybetli hat, yetim kelime önleme)
    if format_tipi == "9:16":
        start_pt = 114 if ar_len < 35 else (98 if ar_len < 65 else (84 if ar_len < 120 else 72))
        min_pt = 50
    else:
        start_pt = 98 if ar_len < 35 else (86 if ar_len < 65 else (72 if ar_len < 120 else 54))
        min_pt = 42

    hedef_satir_sayilari = [1, 2] if ar_len < 65 else [2, 3]
    font_ar_boyut = min_pt
    ar_satirlar = []
    found_ar = False

    for target_l in hedef_satir_sayilari:
        for test_pt in range(start_pt, min_pt - 1, -2):
            f_test = font_al(FONT_ARAPCA, test_pt)
            sats = arapca_satirla(ar_temiz, f_test, text_max_w, draw)
            if not sats or len(sats) > target_l:
                continue

            max_line_w = max(draw.textbbox((0, 0), s, font=f_test)[2] - draw.textbbox((0, 0), s, font=f_test)[0] for s in sats)
            if max_line_w > text_max_w:
                continue

            # Yetim kelime önleme: Son satırda tek kelime kalmışsa reddet
            if len(sats) >= 2 and len(sats[-1].split()) == 1 and len(sats[-1].strip()) < 16:
                if test_pt > min_pt + 4:
                    continue

            # Gerçek mürekkep yüksekliği ve satır arası net clearance simülasyonu
            sim_prev_ink = 0
            for s_idx, s in enumerate(sats):
                bb = draw.textbbox((0, 0), s, font=f_test)
                top_ink, bottom_ink = bb[1], bb[3]
                l_y = -top_ink if s_idx == 0 else (sim_prev_ink + MIN_VERTICAL_GAP - top_ink)
                sim_prev_ink = l_y + bottom_ink

            sim_total_ar_h = sim_prev_ink
            sim_box_h = tac_h + pad_ic_ust + sim_total_ar_h + gap_ar_ok + ok_toplam_h + pad_ic_alt
            sim_kalan = free_vertical - (sim_box_h + tr_toplam_h + kaynak_h)
            min_kalan = 40 if format_tipi == "9:16" else 28

            if sim_kalan >= min_kalan:
                font_ar_boyut = test_pt
                ar_satirlar = sats
                found_ar = True
                break
        if found_ar:
            break

    if not ar_satirlar:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)
        ar_satirlar = arapca_satirla(ar_temiz, font_ar, text_max_w, draw)
    else:
        font_ar = font_al(FONT_ARAPCA, font_ar_boyut)

    # Her satırın Y offsetini gerçek mürekkep sınırlarına göre hesapla
    ar_offsets = []
    prev_ink_bottom = 0
    for s_idx, asat in enumerate(ar_satirlar):
        bb = draw.textbbox((0, 0), asat, font=font_ar)
        top_ink, bottom_ink = bb[1], bb[3]
        l_y = -top_ink if s_idx == 0 else (prev_ink_bottom + MIN_VERTICAL_GAP - top_ink)
        ar_offsets.append(l_y)
        prev_ink_bottom = l_y + bottom_ink

    total_ar_h = prev_ink_bottom

    # Okunuş Satırları Offsetleri
    ok_offsets = []
    if ok_satirlar:
        cur_ok_off = total_ar_h + gap_ar_ok
        for osat in ok_satirlar:
            ok_offsets.append(cur_ok_off)
            cur_ok_off += ok_line_h
        total_content_h = cur_ok_off
    else:
        total_content_h = total_ar_h

    box_s_h = tac_h + pad_ic_ust + total_content_h + pad_ic_alt

    # 5. DİKEY FLEX DAĞILIMI (DENGELİ MERKEZLEME VE EŞİT NEFES ALANLARI)
    toplam_icerik_h = box_s_h + tr_toplam_h + kaynak_h
    kalan_bosluk = max(40, free_vertical - toplam_icerik_h)

    if format_tipi == "9:16":
        gap_ust = max(24, min(170, int(kalan_bosluk * 0.23)))
        kalan_orta_alt = kalan_bosluk - gap_ust
        gap_kutu_tr = max(36, min(260, int(kalan_orta_alt * 0.44)))
        gap_alt_toplam = max(40, kalan_orta_alt - gap_kutu_tr)
        gap_tr_kaynak = max(26, min(80, int(gap_alt_toplam * 0.36)))
    else:  # 4:5
        gap_ust = max(20, min(65, int(kalan_bosluk * 0.20)))
        kalan_orta_alt = kalan_bosluk - gap_ust
        gap_kutu_tr = max(28, min(65, int(kalan_orta_alt * 0.44)))
        gap_alt_toplam = max(30, kalan_orta_alt - gap_kutu_tr)
        gap_tr_kaynak = max(20, min(38, int(gap_alt_toplam * 0.40)))

    box_s_y1 = ayrac_y + gap_ust
    box_s_y2 = box_s_y1 + box_s_h

    # SERLEVHA KUTUSUNU ÇİZ
    yuvarlak_kose_ciz(draw, (box_x1, box_s_y1, box_x2, box_s_y2), radius=24, dolgu="#FFFEFA", kenarlik="#E5DAC3", kenarlik_kalinlik=1)

    if kimin_duasi:
        intro_txt = f"{kimin_duasi}'ın Niyazı:"
    else:
        intro_txt = "Kur'an ve Sünnet'ten Manevî Niyaz:"

    # --- TAÇ STİLİ UYGULAMASI (Sıcak Parşömen) ---
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
    draw.text((in_x, in_y), intro_txt, font=font_intro, fill="#1B4332")

    # Arapça Metin Çizimi (Tamamı ve Harekeli, İslam Yeşili, Gerçek Mürekkep Hizalaması)
    content_base_y = box_s_y1 + tac_h + pad_ic_ust
    for s_idx, asat in enumerate(ar_satirlar):
        as_bb = draw.textbbox((0, 0), asat, font=font_ar)
        as_w = as_bb[2] - as_bb[0]
        line_x = (w - as_w) // 2
        line_y = content_base_y + ar_offsets[s_idx]
        draw.text((line_x, line_y), asat, font=font_ar, fill="#1B4332")

    # Latin Okunuş Çizimi (Safe area garantili)
    if ok_satirlar:
        for o_idx, osat in enumerate(ok_satirlar):
            o_bb = draw.textbbox((0, 0), osat, font=font_okunus)
            o_w = o_bb[2] - o_bb[0]
            ok_x = (w - o_w) // 2
            ok_y = content_base_y + ok_offsets[o_idx]
            draw.text((ok_x, ok_y), osat, font=font_okunus, fill="#5A4B42")

    # 6. TÜRKÇE DUA ANLAMI & ZARİF PARŞÖMEN TIRNAK FİLİGRANI
    tr_y = box_s_y2 + gap_kutu_tr

    # Asil ve narin parşömen tırnak filigranı (Metinle çakışmayan, huzurlu krem tonu)
    font_fili_pt = int(font_anlam_boyut * 2.3)
    font_fili = font_al(FONT_BASLIK, font_fili_pt, agirlik=700)
    draw.text((w // 2 - 120, tr_y - int(font_fili_pt * 0.45)), "“", font=font_fili, fill="#EFE8DA")

    # TÜRKÇE ANLAM ÇİZİMİ (BOLD VE REGULAR KELİMELER KUSURSUZ YANYANA)
    for line_tokens, line_w in tr_wrapped_lines:
        cur_x = (w - line_w) // 2
        for word, is_bold, word_w in line_tokens:
            f = font_anlam_bold if is_bold else font_anlam_reg
            fill_c = "#111827" if is_bold else "#1C1917"
            draw.text((cur_x, tr_y), word, font=f, fill=fill_c)
            cur_x += word_w + space_w
        tr_y += tr_line_h

    tr_y += gap_tr_kaynak

    # Kaynak Rozeti (Kart sınırlarına tam kilitli, asla taşmaz)
    kx = (w - kw) // 2
    badge_x1 = max(kx1 + 24, kx - 26)
    badge_x2 = min(kx2 - 24, kx + kw + 26)
    yuvarlak_kose_ciz(draw, (badge_x1, tr_y - 6, badge_x2, tr_y + 34), radius=12, dolgu="#FFFDF9", kenarlik="#E5DAC3", kenarlik_kalinlik=1)
    draw.text((kx, tr_y - 1), kaynak_metni, font=font_kaynak, fill="#B45309")

    if not cikti_dosya_adi:
        cikti_dosya_adi = f"dua_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=96)
    return cikti_yolu


def create_paper_background(w: int, h: int, center_rgb: tuple, outer_rgb: tuple) -> Image.Image:
    """Hafif organik vignetting ve mat parşömen hissi veren zemin üretir."""
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h * 0.45
    dist = np.sqrt(((x - cx) / (w * 0.72)) ** 2 + ((y - cy) / (h * 0.72)) ** 2)
    dist = np.clip(dist, 0, 1.2)

    cr, cg, cb = center_rgb
    or_, og, ob = outer_rgb

    r = (cr - dist * (cr - or_)).astype(np.uint8)
    g = (cg - dist * (cg - og)).astype(np.uint8)
    b = (cb - dist * (cb - ob)).astype(np.uint8)

    arr = np.stack([r, g, b], axis=-1)
    return Image.fromarray(arr)


# 5 Belirgin ve Zengin Renk Paleti (Ezan Plus Kur'an Sözlüğü)
KELIME_PALETLERI: Dict[str, dict] = {
    "yakut_kirmizi": {
        "ad": "Ezan Yakut Kırmızısı (İmza Kırmızı)",
        "center_rgb": (166, 33, 39),   # #A62127
        "outer_rgb": (105, 12, 18),    # #690C12
        "c_divider": "#C83840",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF8EE",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FFE8E3",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF8ED",
        "c_ref": "#FDE6BA",
        "fili_rgba": (253, 230, 186, 26),
    },
    "gece_safiri": {
        "ad": "Derin Gece Safiri (Midnight Navy)",
        "center_rgb": (28, 56, 92),    # #1C385C
        "outer_rgb": (12, 26, 46),     # #0C1A2E
        "c_divider": "#365D8F",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F0F6FF",
        "c_accent": "#F6D89B",
        "c_body_reg": "#DCE8F8",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#F0F5FD",
        "c_ref": "#F6D89B",
        "fili_rgba": (246, 216, 155, 26),
    },
    "mescid_zumrudu": {
        "ad": "Mescid Zümrüdü (Ravza Yeşili)",
        "center_rgb": (24, 72, 56),    # #184838
        "outer_rgb": (10, 36, 28),     # #0A241C
        "c_divider": "#32735C",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F2FAF6",
        "c_accent": "#FCE7B8",
        "c_body_reg": "#D8ECE3",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#F2F9F5",
        "c_ref": "#FCE7B8",
        "fili_rgba": (252, 231, 184, 26),
    },
    "sicak_kehribar": {
        "ad": "Sıcak Kiremit / Kehribar (Terracotta)",
        "center_rgb": (158, 68, 36),   # #9E4424
        "outer_rgb": (92, 33, 14),     # #5C210E
        "c_divider": "#BD5B35",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF9F2",
        "c_accent": "#FDE4B0",
        "c_body_reg": "#FCE6DC",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF6EE",
        "c_ref": "#FDE4B0",
        "fili_rgba": (253, 228, 176, 26),
    },
    "asil_murdum": {
        "ad": "Asil Mürdüm / Ametist (Royal Plum)",
        "center_rgb": (88, 32, 68),    # #582044
        "outer_rgb": (44, 12, 34),     # #2C0C22
        "c_divider": "#7C3563",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF5F8",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FCE4F0",
        "c_body_bold": "#FFFFFF",
        "c_italic": "#FFF5FA",
        "c_ref": "#FDE6BA",
        "fili_rgba": (253, 230, 186, 26),
    },
}

# Farklı isim varyasyonları ve Türkçe/İngilizce takma adları destekleyen harita
KELIME_PALET_ALIASES: Dict[str, str] = {
    "yakut_kirmizi": "yakut_kirmizi",
    "kirmizi": "yakut_kirmizi",
    "crimson": "yakut_kirmizi",
    "ruby": "yakut_kirmizi",
    "gece_safiri": "gece_safiri",
    "gece_mavisi": "gece_safiri",
    "mavi": "gece_safiri",
    "safir": "gece_safiri",
    "navy": "gece_safiri",
    "mescid_zumrudu": "mescid_zumrudu",
    "zumrut_yesili": "mescid_zumrudu",
    "yesil": "mescid_zumrudu",
    "zumrut": "mescid_zumrudu",
    "ravza": "mescid_zumrudu",
    "ravza_yesili": "mescid_zumrudu",
    "emerald": "mescid_zumrudu",
    "sicak_kehribar": "sicak_kehribar",
    "kehribar": "sicak_kehribar",
    "kiremit": "sicak_kehribar",
    "terracotta": "sicak_kehribar",
    "amber": "sicak_kehribar",
    "asil_murdum": "asil_murdum",
    "derin_mor": "asil_murdum",
    "mor": "asil_murdum",
    "murdum": "asil_murdum",
    "plum": "asil_murdum",
    "ametist": "asil_murdum",
}


def _kelime_cta_butonu_ciz(im: Image.Image, format_tipi: str = "9:16") -> int:
    """Ezan Plus İndirin alt butonunu çizer ve butonun üst Y koordinatını döner (İncelen zarif yükseklik)."""
    draw = ImageDraw.Draw(im)
    w, h = im.size
    is_916 = (format_tipi == "9:16")

    nav_w = 710 if is_916 else 650
    nav_h = 72 if is_916 else 62
    nav_x1 = (w - nav_w) // 2
    nav_x2 = nav_x1 + nav_w
    nav_y1 = (h - 130) if is_916 else (h - 96)
    nav_y2 = nav_y1 + nav_h
    btn_y = nav_y1 + nav_h // 2

    # Lüks yumuşak gölge
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([nav_x1 + 2, nav_y1 + 3, nav_x2 - 2, nav_y2 + 6], radius=24 if is_916 else 20, fill=(15, 3, 6, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    im.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(im)
    # Beyaz Buton Gövdesi
    draw.rounded_rectangle([nav_x1, nav_y1, nav_x2, nav_y2], radius=22 if is_916 else 18, fill="#FFFFFF", outline="#EFE8DC", width=1)

    # 1. Logo
    logo_path = IKONLAR / "logo.png"
    logo_size = 40 if is_916 else 34
    logo_x = nav_x1 + (18 if is_916 else 14)
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=11, fill=255)
        im.paste(logo, (logo_x, btn_y - logo_size // 2), mask)

    # 2. CTA Yazısı (Dikeyde tam ortalı)
    pt_cta = 22 if is_916 else 18
    font_cta = font_al(FONT_UI, pt_cta, agirlik=700)
    txt_x = logo_x + logo_size + (14 if is_916 else 12)
    txt_bb = draw.textbbox((0, 0), "Ezan Plus • Ücretsiz İndirin", font=font_cta)
    txt_h = txt_bb[3] - txt_bb[1]
    draw.text((txt_x, btn_y - txt_h // 2 - txt_bb[1]), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill="#182230")

    # 3. Store İkonları
    ps_size = 22 if is_916 else 19
    ps_x = nav_x2 - (48 if is_916 else 42)
    ps_y = btn_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    # Apple İkonu
    apple_path = IKONLAR / "apple.png"
    ap_size = 20 if is_916 else 17
    if apple_path.exists():
        ap_img = Image.open(apple_path).convert("RGBA").resize((ap_size, ap_size), Image.Resampling.LANCZOS)
        ap_x = ps_x - ap_size - (15 if is_916 else 12)
        im.paste(ap_img, (ap_x, btn_y - ap_size // 2), ap_img)
    else:
        try:
            font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24 if is_916 else 20)
            bbox_ap = draw.textbbox((0, 0), "", font=font_apple)
            ap_w, ap_h = bbox_ap[2] - bbox_ap[0], bbox_ap[3] - bbox_ap[1]
            ap_y = btn_y - ap_h // 2 - bbox_ap[1]
            ap_x = ps_x - ap_w - 15
            draw.text((ap_x, ap_y), "", font=font_apple, fill="#000000")
        except Exception:
            pass

    return nav_y1


def kelime_karti_ciz(
    kelime_tr: str,
    kelime_ar: str,
    okunus: str,
    kok: str,
    lugat_anlami: str,
    kuran_boyutu: str,
    hayat_dersi: str,
    ayet_ref: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
    format_tipi: str = "4:5",
    palet: str = "yakut_kirmizi",
) -> Path:
    """
    Ezan Plus Kur'an Sözlüğü & İslami Kavramlar V17 Şablonu (1080x1350 4:5 veya 1080x1920 9:16).
    Zengin kadifemsi parşömen zemin, devasa saf beyaz hero kelime,
    tam harekeli heybetli hat, safe area garantili kök analizi, lüks filigran tırnak,
    anlam kısmında mixed bold vurgusu ve inceltilmiş alt store indirme butonu.
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")

    palet_anahtar = KELIME_PALET_ALIASES.get(palet.lower().strip() if isinstance(palet, str) else "", palet)
    secili_palet = KELIME_PALETLERI.get(palet_anahtar, KELIME_PALETLERI["yakut_kirmizi"])

    im = create_paper_background(w, h, secili_palet["center_rgb"], secili_palet["outer_rgb"])
    draw = ImageDraw.Draw(im)

    # 1. Alt CTA Barı Çizimi & Üst Güvenli Sınır
    cta_ust_y = _kelime_cta_butonu_ciz(im, format_tipi)

    max_text_w = 880 if is_916 else 840

    # 2. Hero Başlıklar (BÜYÜTÜLMÜŞ & MİNİMUM SEKÎNET BOYUT TABANI)
    target_pt = 172 if is_916 else 130
    min_pt_floor = 154 if is_916 else 118

    pt_latin = target_pt
    f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
    lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)

    # Çoklu satırlı kavramlarda dikey sıkışmayı önlemek için akıllı ölçeklendirme
    if len(lines_tr) >= 3:
        target_pt = 118 if is_916 else 88
        min_pt_floor = 96 if is_916 else 72
        pt_latin = target_pt
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
    elif len(lines_tr) == 2:
        target_pt = 138 if is_916 else 104
        min_pt_floor = 114 if is_916 else 86
        pt_latin = target_pt
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)

    max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)
    while max_line_w > max_text_w and pt_latin > min_pt_floor:
        pt_latin -= 2
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
        max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)

    while max_line_w > max_text_w and pt_latin > 75:
        pt_latin -= 3
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
        max_line_w = max(draw.textbbox((0, 0), l, font=f_latin)[2] - draw.textbbox((0, 0), l, font=f_latin)[0] for l in lines_tr)

    lh_latin = int(pt_latin * 1.08)
    first_l_bb = draw.textbbox((0, 0), lines_tr[0], font=f_latin)
    last_l_bb = draw.textbbox((0, 0), lines_tr[-1], font=f_latin)
    latin_block_h = (len(lines_tr) - 1) * lh_latin + (last_l_bb[3] - first_l_bb[1])

    # Arapça Hat
    if len(lines_tr) >= 3:
        pt_arabic = 130 if is_916 else 102
    elif len(lines_tr) == 2:
        pt_arabic = 148 if is_916 else 116
    else:
        pt_arabic = 180 if is_916 else 142

    f_arabic = font_al(FONT_ARAPCA, pt_arabic)
    ar_prep_txt = arapca_hazirla(kelime_ar)
    ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
    ar_w = ar_bb[2] - ar_bb[0]
    while ar_w > max_text_w and pt_arabic > 85:
        pt_arabic -= 3
        f_arabic = font_al(FONT_ARAPCA, pt_arabic)
        ar_bb = draw.textbbox((0, 0), ar_prep_txt, font=f_arabic)
        ar_w = ar_bb[2] - ar_bb[0]

    # Tipografi Tanımları
    pt_tag = 16 if is_916 else 14
    f_tag = font_al(FONT_UI, pt_tag, agirlik=600)

    pt_origin = 29 if is_916 else 23
    f_origin = font_al(FONT_GOVDE, pt_origin, agirlik=400)
    temiz_kok = kok_latinize_et(kok)
    origin_txt = f"Arapça: {okunus}   •   Kök: {temiz_kok}"
    o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
    ow = o_bb[2] - o_bb[0]
    oh = o_bb[3] - o_bb[1]

    # Ekrandan taşmayı önlemek için dinamik autofit
    while ow > max_text_w and pt_origin > 17:
        pt_origin -= 1
        f_origin = font_al(FONT_GOVDE, pt_origin, agirlik=400)
        o_bb = draw.textbbox((0, 0), origin_txt, font=f_origin)
        ow = o_bb[2] - o_bb[0]
        oh = o_bb[3] - o_bb[1]

    origin_lines = [origin_txt]
    if ow > max_text_w:
        origin_lines = [f"Arapça: {okunus}", f"Kök: {temiz_kok}"]
        pt_origin = 23 if is_916 else 19
        f_origin = font_al(FONT_GOVDE, pt_origin, agirlik=400)
        origin_line_h = int(pt_origin * 1.35)
        origin_total_h = len(origin_lines) * origin_line_h
    else:
        origin_total_h = oh

    # Lügat Anlamı (MIXED BOLD VE REGULAR VURGUSU)
    pt_body = 48 if is_916 else 37
    lh_body = 76 if is_916 else 58
    f_body_reg = font_al(FONT_GOVDE, pt_body, agirlik=400)
    f_body_bold = font_al(FONT_GOVDE, pt_body, agirlik=700)

    islenmis_anlam = lugat_anlami
    if "**" not in islenmis_anlam:
        if ";" in islenmis_anlam:
            parcalar = islenmis_anlam.split(";")
            islenmis_anlam = f"{parcalar[0]}; **{parcalar[1].strip()}**"
        else:
            islenmis_anlam = re.sub(r'(\b\w+\b\s+\b\w+\b\s+\b\w+\b[\.!]?)$', r'**\1**', islenmis_anlam)

    body_tokens = parse_markdown_bold(islenmis_anlam)
    body_wrapped, body_space_w = wrap_mixed_tokens(body_tokens, f_body_reg, f_body_bold, max_text_w, draw)

    if len(body_wrapped) > 3:
        pt_body = 42 if is_916 else 33
        lh_body = 66 if is_916 else 52
        f_body_reg = font_al(FONT_GOVDE, pt_body, agirlik=400)
        f_body_bold = font_al(FONT_GOVDE, pt_body, agirlik=700)
        body_wrapped, body_space_w = wrap_mixed_tokens(body_tokens, f_body_reg, f_body_bold, max_text_w, draw)

    body_block_h = len(body_wrapped) * lh_body

    # Alıntı / Hayat Dersi (Tefekkür)
    pt_italic = 37 if is_916 else 29
    lh_italic = 58 if is_916 else 46
    f_italic = font_al(FONT_GOVDE, pt_italic, agirlik=400)
    alinti_metin = hayat_dersi if hayat_dersi else kuran_boyutu
    clean_alinti = alinti_metin.strip("“”\" ")
    italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 40, draw)
    italic_block_h = len(italic_lines) * lh_italic

    # Ayet Referansı
    pt_ref = 18 if is_916 else 15
    f_ref = font_al(FONT_UI, pt_ref, agirlik=700)
    ref_txt = (ayet_ref or "Kur'an-ı Kerim").upper()
    r_bb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    rw = r_bb[2] - r_bb[0]
    rh = r_bb[3] - r_bb[1]

    # 3. Dinamik Dikey Flex Mizanpaj & KESİN GÖRSEL SAFE AREA
    gap_tr_ar = 68 if is_916 else (42 if len(lines_tr) >= 2 else 46)
    gap_ar_origin = 56 if is_916 else (38 if len(lines_tr) >= 2 else 42)

    top_y = 150 if is_916 else 95
    # CTA butonu üst sınırından kesin nefes payı ile referans satırının azami tavanı
    ref_y_max = cta_ust_y - (44 if is_916 else 34) - rh
    usable_h = ref_y_max - top_y

    hero_visual_h = latin_block_h + gap_tr_ar + (ar_bb[3] - ar_bb[1]) + gap_ar_origin + origin_total_h
    fixed_content_h = 28 + hero_visual_h + body_block_h + italic_block_h + rh

    # Taşma önleyici otomatik sığdırma döngüsü (Auto-fit safe area guarantee)
    while (fixed_content_h > usable_h - 20) and (pt_body > (32 if is_916 else 25)):
        pt_body -= 2
        lh_body = int(pt_body * (1.50 if is_916 else 1.48))
        f_body_reg = font_al(FONT_GOVDE, pt_body, agirlik=400)
        f_body_bold = font_al(FONT_GOVDE, pt_body, agirlik=700)
        body_wrapped, body_space_w = wrap_mixed_tokens(body_tokens, f_body_reg, f_body_bold, max_text_w, draw)
        body_block_h = len(body_wrapped) * lh_body

        pt_italic -= 1
        lh_italic = int(pt_italic * (1.50 if is_916 else 1.48))
        f_italic = font_al(FONT_GOVDE, pt_italic, agirlik=400)
        italic_lines = metin_satirla(f"“{clean_alinti}”", f_italic, max_text_w - 40, draw)
        italic_block_h = len(italic_lines) * lh_italic

        if gap_tr_ar > (44 if is_916 else 30):
            gap_tr_ar -= 2
        if gap_ar_origin > (38 if is_916 else 26):
            gap_ar_origin -= 2

        hero_visual_h = latin_block_h + gap_tr_ar + (ar_bb[3] - ar_bb[1]) + gap_ar_origin + origin_total_h
        fixed_content_h = 28 + hero_visual_h + body_block_h + italic_block_h + rh

    free_space = max(30, usable_h - fixed_content_h)

    pad_tag_hero = int(free_space * 0.12)
    pad_origin_div = int(free_space * 0.14)
    pad_div_body = int(free_space * 0.22)
    pad_body_quote = int(free_space * 0.22)
    pad_quote_ref = max(30 if is_916 else 22, int(free_space * 0.14))

    cur_y = top_y

    # A) Kategori Rozeti
    tag_txt = "KUR'AN SÖZLÜĞÜ  •  KAVRAM VE HİKMET".upper()
    tag_bb = draw.textbbox((0, 0), tag_txt, font=f_tag)
    tag_w = tag_bb[2] - tag_bb[0]
    draw.text(((w - tag_w) / 2, cur_y), tag_txt, font=f_tag, fill=secili_palet["c_accent"])
    cur_y += 28 + pad_tag_hero

    # B) Türkçe Hero Kelime (Çoklu satır destekli)
    latin_start_y = cur_y
    for idx, line in enumerate(lines_tr):
        bb = draw.textbbox((0, 0), line, font=f_latin)
        lw = bb[2] - bb[0]
        line_y = latin_start_y + idx * lh_latin
        draw.text(((w - lw) / 2, line_y), line, font=f_latin, fill=secili_palet["c_hero"])

    latin_bottom = latin_start_y + (len(lines_tr) - 1) * lh_latin + last_l_bb[3]

    # C) Arapça Hat
    ar_y = latin_bottom - ar_bb[1] + gap_tr_ar
    draw.text(((w - ar_w) / 2, ar_y), ar_prep_txt, font=f_arabic, fill=secili_palet["c_arabic"])
    ar_bottom = ar_y + ar_bb[3]

    # D) Okunuş & Kök Satırı (Taşma korumalı, tek veya çift satır)
    cur_y = ar_bottom + gap_ar_origin
    for o_line in origin_lines:
        ol_bb = draw.textbbox((0, 0), o_line, font=f_origin)
        ol_w = ol_bb[2] - ol_bb[0]
        ol_h = ol_bb[3] - ol_bb[1]
        draw.text(((w - ol_w) / 2, cur_y - ol_bb[1]), o_line, font=f_origin, fill=secili_palet["c_accent"])
        cur_y += ol_h + (8 if is_916 else 6)
    cur_y += pad_origin_div

    # E) Narin Ayraç & Altın Elmas Noktası
    div_w = 460 if is_916 else 380
    div_x1 = (w - div_w) / 2
    div_x2 = div_x1 + div_w
    draw.line([(div_x1, cur_y), (div_x2, cur_y)], fill=secili_palet["c_divider"], width=1)
    dot_r = 3.5 if is_916 else 3.0
    draw.ellipse([(w/2 - dot_r, cur_y - dot_r), (w/2 + dot_r, cur_y + dot_r)], fill=secili_palet["c_accent"])
    cur_y += pad_div_body

    # F) Anlam Arkası Zarif Editoryal Filigran Tırnak (" )
    fili_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fili_draw = ImageDraw.Draw(fili_layer)
    pt_fili = 340 if is_916 else 250
    f_fili = font_al(FONT_GOVDE, pt_fili, agirlik=700)

    first_line_w = body_wrapped[0][1]
    first_bx = (w - first_line_w) // 2

    fili_x = first_bx - (85 if is_916 else 65)
    fili_y = cur_y - (145 if is_916 else 105)

    fili_draw.text((fili_x, fili_y), "“", font=f_fili, fill=secili_palet["fili_rgba"])
    im.paste(fili_layer, (0, 0), fili_layer)

    # G) Lügat Anlamı (BOLD VE REGULAR VURGULU)
    draw = ImageDraw.Draw(im)
    for line_tokens, line_w in body_wrapped:
        line_cur_x = (w - line_w) // 2
        for word, is_bold, word_w in line_tokens:
            f = f_body_bold if is_bold else f_body_reg
            c = secili_palet["c_body_bold"] if is_bold else secili_palet["c_body_reg"]
            draw.text((line_cur_x, cur_y), word, font=f, fill=c)
            line_cur_x += word_w + body_space_w
        cur_y += lh_body

    cur_y += pad_body_quote

    # H) Tefekkür & Hayat Dersi Alıntısı
    for line in italic_lines:
        bb = draw.textbbox((0, 0), line, font=f_italic)
        draw.text(((w - (bb[2] - bb[0])) / 2, cur_y), line, font=f_italic, fill=secili_palet["c_italic"])
        cur_y += lh_italic

    # I) Ayet Referansı (Akış içinde, garantili güvenli koordinatta çizilir)
    ref_y = min(cur_y + pad_quote_ref, ref_y_max)
    draw.text(((w - rw) / 2, ref_y), ref_txt, font=f_ref, fill=secili_palet["c_ref"])

    # 4. Kaydet
    if not cikti_dosya_adi:
        cikti_dosya_adi = f"kelime_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=96)
    log.info(f"V17 Kur'an Sözlüğü kartı kaydedildi: {cikti_yolu.name} (Palet: {secili_palet['ad']})")
    return cikti_yolu
