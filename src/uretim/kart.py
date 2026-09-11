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


def arapca_glif_temizle(metin: str) -> str:
    """
    Amiri ve Uthmani fontlarında bulunmayan, render esnasında dikey dikdörtgen
    (tofu / glif eksik kutusu) hatasına yol açan tüm Latin karakterleri temizler ve dönüştürür.
    """
    if not metin:
        return ""
    # 1. Latin noktalama işaretlerini resmi Arapça Unicode karşılıklarına dönüştür
    metin = metin.replace(',', '،').replace(';', '؛').replace('?', '؟')
    # 2. Amiri fontunda bulunmayan Latin tırnak, ayraç ve sembolleri temizle
    metin = re.sub(r'[«»""\'\'“”‘’()\[\]{}<>]', '', metin)
    # 3. İki nokta, tire, alt çizgi, artı vb. sembolleri temizle
    metin = re.sub(r'[:：\-_–—+=/\\|*^~`]', ' ', metin)
    # 4. Sadece geçerli Arapça blokları ve izin verilen noktalama karakterlerini muhafaza et
    temiz = []
    for ch in metin:
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF or 
            0x0750 <= cp <= 0x077F or 
            0x08A0 <= cp <= 0x08FF or 
            0xFB50 <= cp <= 0xFDFF or 
            0xFE70 <= cp <= 0xFEFF or 
            cp in (0x20, 0x00A0) or
            ch in ('،', '؛', '؟')):
            temiz.append(ch)
    metin = "".join(temiz)
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin


def arapca_hazirla(metin: str) -> str:
    """Arapça metni sağdan sola, harf bitişmelerine ve tam harekelerine göre düzenler."""
    if not metin:
        return ""
    metin = arapca_glif_temizle(metin)
    if not metin:
        return ""
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
    Noktalama işaretlerini önceki kelimeye yapıştırarak 'kelime ,' boşluk hatasını önler.
    Kapanmamış veya artık kalan '**' işaretlerini temizleyerek ekranda ham yıldız çıkmasını önler."""
    if metin.count('**') % 2 != 0:
        metin = metin + '**'

    parcalar = re.split(r'(\*\*.*?\*\*)', metin)
    tokenlar = []
    noktalama_regex = re.compile(r'^([,\.;:!?\)’”"]+)(.*)$')
    for parca in parcalar:
        if not parca:
            continue
        if parca.startswith('**') and parca.endswith('**'):
            icerik = parca[2:-2].replace('**', '').replace('*', '')
            for kelime in icerik.split():
                kelime = kelime.replace('*', '')
                if kelime:
                    tokenlar.append((kelime, True))
        else:
            for kelime in parca.split():
                is_b = False
                if '*' in kelime:
                    kelime = kelime.replace('*', '')
                    is_b = True
                m = noktalama_regex.match(kelime)
                if m and tokenlar:
                    nokta, kalan = m.group(1), m.group(2)
                    onceki_kelime, onceki_bold = tokenlar[-1]
                    tokenlar[-1] = (onceki_kelime + nokta, onceki_bold)
                    if kalan:
                        tokenlar.append((kalan, is_b))
                else:
                    if kelime:
                        tokenlar.append((kelime, is_b))
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


# ==============================================================================
# V19 SABİT SOFT PASTEL RENK PALETLERİ & KETEN PARŞÖMEN STANDARDI
# ==============================================================================
KETEN_CENTER = (244, 240, 232)
KETEN_OUTER = (230, 224, 212)

_DUA_HANDS_MASK_CACHE: Optional[Image.Image] = None

def extract_dua_hands_mask() -> Optional[Image.Image]:
    """Logo maskesinden dua eden eller silüetini narin filigran olarak çıkarır ve önbelleğe alır."""
    global _DUA_HANDS_MASK_CACHE
    if _DUA_HANDS_MASK_CACHE is not None:
        return _DUA_HANDS_MASK_CACHE
    logo_p = IKONLAR / "logo.png"
    if not logo_p.exists():
        return None
    try:
        logo = Image.open(logo_p)
        arr = np.array(logo).astype(float)
        gb_mean = (arr[:, :, 1] + arr[:, :, 2]) / 2.0
        alpha = np.clip((gb_mean - 55) / (195 - 55) * 255.0, 0, 255).astype(np.uint8)
        alpha[0:15, :] = 0
        alpha[-15:, :] = 0
        alpha[:, 0:15] = 0
        alpha[:, -15:] = 0
        mask_img = Image.fromarray(alpha)
        bbox = mask_img.getbbox()
        if bbox:
            mask_img = mask_img.crop(bbox)
        _DUA_HANDS_MASK_CACHE = mask_img
        return _DUA_HANDS_MASK_CACHE
    except Exception as e:
        log.warning(f"Dua hands mask çıkarılamadı: {e}")
        return None


def draw_kart_header_bar(
    im: Image.Image,
    draw: ImageDraw.ImageDraw,
    cfg: Dict[str, Any],
    top_y: int = 225,
    rozet_text: str = "HADİS-İ ŞERİF",
    sol_x: int = 65,
    sag_x: int = 1080 - 65,
) -> int:
    """Kartlar için kurumsal simetrik 3'lü Header Künyesi çizer ve ayraç y koordinatını döner."""
    w = 1080
    mid_y = top_y + 35

    # 1. Sol: 68x68 Yuvarlak Köşeli Logo
    logo_size = 68
    logo_p = IKONLAR / "logo.png"
    if logo_p.exists():
        try:
            logo = Image.open(logo_p).convert("RGBA").resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (logo_size, logo_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, logo_size, logo_size], radius=18, fill=255)
            im.paste(logo, (sol_x, mid_y - logo_size // 2), mask)
        except Exception:
            pass

    # 2. Sağ: Kurumsal Künye
    f_sub = font_al(FONT_UI, 13, agirlik=700)
    s_txt = cfg.get("sub_txt", "SAHİH HADİS-İ ŞERİF REHBERİ")
    s_bb = draw.textbbox((0, 0), s_txt, font=f_sub)
    w_sub = s_bb[2] - s_bb[0]

    f_marka = font_al(FONT_GOVDE, 39, agirlik=700)
    m_txt = "Ezan Plus"
    m_bb = draw.textbbox((0, 0), m_txt, font=f_marka)
    w_m = m_bb[2] - m_bb[0]
    h_m = m_bb[3] - m_bb[1]

    start_y = mid_y - (h_m + 4 + s_bb[3] - s_bb[1]) // 2
    draw.text((sag_x - w_m, start_y - m_bb[1]), m_txt, font=f_marka, fill="#FFFFFF")
    draw.text((sag_x - w_sub, start_y + h_m + 8 - s_bb[1]), s_txt, font=f_sub, fill=cfg.get("sub_color", "#DCECE5"))

    # 3. Orta: Baskerville Bold 42pt Fildişi Rozet
    f_rozet = font_al(FONT_BASKERVILLE, 42, agirlik=700)
    r_bb = draw.textbbox((0, 0), rozet_text, font=f_rozet)
    rw, rh = r_bb[2] - r_bb[0], r_bb[3] - r_bb[1]
    rozet_w = rw + 84
    rozet_h = 70
    rozet_x = (w - rozet_w) // 2
    rozet_y = mid_y - rozet_h // 2
    yuvarlak_kose_ciz(draw, (rozet_x, rozet_y, rozet_x + rozet_w, rozet_y + rozet_h), radius=rozet_h // 2, dolgu="#FFFDF9")
    rx = rozet_x + (rozet_w - rw) // 2 - r_bb[0]
    ry = rozet_y + (rozet_h - rh) // 2 - r_bb[1] + 1
    draw.text((rx, ry), rozet_text, font=f_rozet, fill=cfg["badge_color"])

    # İnce Altın Ayraç Çizgisi ve Merkez Nokta
    ayrac_y = top_y + 88
    line_col = f"#{int(cfg['center_rgb'][0]*1.4):02x}{int(cfg['center_rgb'][1]*1.4):02x}{int(cfg['center_rgb'][2]*1.4):02x}"
    draw.line([(sol_x, ayrac_y), (sag_x, ayrac_y)], fill=line_col, width=1)
    draw.ellipse([w // 2 - 4, ayrac_y - 4, w // 2 + 4, ayrac_y + 4], fill="#FFFDF9")
    return ayrac_y


HADIS_SABIT_PALET: Dict[str, Any] = {
    "ad": "Sisli Adaçayı Zümrüdü",
    "center_rgb": (34, 66, 52),     # #224234 (Sisli Adaçayı)
    "outer_rgb": (18, 40, 32),      # #122820
    "badge_color": "#224234",
    "bold_color": "#1B4D38",
    "accent_gold": "#D4AF37",
    "sub_txt": "SAHİH HADİS-İ ŞERİF REHBERİ",
    "sub_color": "#DCECE5",
    "rozet_txt": "HADİS-İ ŞERİF",
    "fili_txt": "قال رسول الله",
}

DUA_SABIT_PALET: Dict[str, Any] = {
    "ad": "Selçuklu Petrol Zümrüdü",
    "center_rgb": (14, 48, 50),     # #0E3032 (Selçuklu Petrol Zümrüdü)
    "outer_rgb": (6, 26, 28),       # #061A1C
    "badge_color": "#0E3032",
    "bold_color": "#0F4144",
    "accent_gold": "#D4AF37",
    "sub_txt": "GÜNÜN DUASI & MÜNACAT REHBERİ",
    "sub_color": "#D2EAEB",
    "rozet_txt": "GÜNÜN DUASI",
    "fili_txt": "ادعوني استجب لكم",
}


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
    Ezan Plus Sahih Hadis şablonu (V20 Mimarisi - Sisli Adaçayı & Keten Parşömen Flex Mizanpaj).
    1080x1350 (4:5 Feed) ve 1080x1920 (9:16 Story) tam destekler.
    Bounding-box garantili sıfır hareke çakışması, erimeden tamamen izole edilmiş tefekkür,
    kısa metinlerde devasa 142pt/108pt tipografi, uzun metinlerde ise anlamı öne çıkaran geniş Keten bandı içerir.
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")
    cfg = HADIS_SABIT_PALET
    max_w = 930 if is_916 else 920

    from .ses import turkce_kisaltmalari_genislet
    hadis_metni = turkce_kisaltmalari_genislet(hadis_metni)
    if ravi:
        ravi = turkce_kisaltmalari_genislet(ravi)

    # 1. Taban Kadife Parşömen
    im = create_paper_background(w, h, cfg["center_rgb"], cfg["outer_rgb"]).convert("RGBA")
    draw = ImageDraw.Draw(im)

    # 2. Header & CTA Butonu
    top_header_y = 215 if is_916 else 55
    ayrac_y = draw_kart_header_bar(im, draw, cfg, top_y=top_header_y, rozet_text=cfg["rozet_txt"])
    cta_ust_y = _kelime_cta_butonu_ciz(im, format_tipi)

    # 3. Taç Başlık
    pt_tac = 34 if is_916 else 28
    f_tac = font_al(FONT_GOVDE, pt_tac, agirlik=700)
    if ravi and ravi.strip():
        tac_txt = f"“ Resûlullah (s.a.v.) Buyurdu • {ravi.strip()} ”"
    else:
        tac_txt = "“ Resûlullah (s.a.v.) Buyurdu ”"
    t_bb = draw.textbbox((0, 0), tac_txt, font=f_tac)
    tac_h = t_bb[3] - t_bb[1]
    start_tac_y = ayrac_y + (30 if is_916 else 18)
    tac_bottom_y = start_tac_y + tac_h

    # 4. Üst Bölüm: Arapça ve Latin Okunuş Boyutlandırma
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", arapca_metin).strip() if arapca_metin else ""
    words_ar = ar_temiz.split() if ar_temiz else []
    ar_word_count = len(words_ar)

    if ar_word_count <= 4:
        pt_ar = 142 if is_916 else 120
        pt_ok = 46 if is_916 else 36
    elif ar_word_count <= 8:
        pt_ar = 110 if is_916 else 94
        pt_ok = 40 if is_916 else 32
    elif ar_word_count <= 14:
        pt_ar = 94 if is_916 else 80
        pt_ok = 34 if is_916 else 28
    else:
        pt_ar = 84 if is_916 else 72
        pt_ok = 30 if is_916 else 24

    ok_ham = (arapca_okunus or "").strip("“”\"'{}[] ")
    ok_gosterim = f"“ {ok_ham} ”" if ok_ham else ""

    # Dikey Emniyet Tavanı (Okunuş erimeye asla değemez)
    hard_max_ok_bottom = 815 if is_916 else 595

    while pt_ar >= 64:
        f_ar = font_al(FONT_ARAPCA, pt_ar)
        ar_satirlar = arapca_satirla(ar_temiz, f_ar, max_w, draw) if ar_temiz else []
        f_ok = font_al(FONT_GOVDE, pt_ok, agirlik=400)
        ok_lines = metin_satirla(ok_gosterim, f_ok, max_w, draw) if ok_gosterim else []

        gap_tac_ar = 34 if is_916 else 22
        ar_line_gap = 18 if is_916 else 12
        cur_calc_y = tac_bottom_y + gap_tac_ar
        for s in ar_satirlar:
            bb = draw.textbbox((0, 0), s, font=f_ar)
            cur_calc_y += (bb[3] - bb[1]) + ar_line_gap
        gap_ar_ok = 26 if is_916 else 16
        cur_calc_y += gap_ar_ok
        ok_line_step = int(pt_ok * 1.30)
        cur_calc_y += len(ok_lines) * ok_line_step

        if cur_calc_y <= hard_max_ok_bottom:
            break
        pt_ar -= 3
        pt_ok = max(28 if is_916 else 22, int(pt_ar * 0.38))

    f_ar = font_al(FONT_ARAPCA, pt_ar)
    ar_satirlar = arapca_satirla(ar_temiz, f_ar, max_w, draw) if ar_temiz else []
    f_ok = font_al(FONT_GOVDE, pt_ok, agirlik=400)
    ok_lines = metin_satirla(ok_gosterim, f_ok, max_w, draw) if ok_gosterim else []

    gap_tac_ar = 34 if is_916 else 22
    ar_line_gap = 18 if is_916 else 12
    gap_ar_ok = 26 if is_916 else 16
    ok_line_step = int(pt_ok * 1.30)

    top_text_bottom = tac_bottom_y + gap_tac_ar
    for s in ar_satirlar:
        bb = draw.textbbox((0, 0), s, font=f_ar)
        top_text_bottom += (bb[3] - bb[1]) + ar_line_gap
    top_text_bottom += gap_ar_ok + len(ok_lines) * ok_line_step

    # 5. Dinamik Flex Keten Bandı (Anlam Odaklı Genişleme)
    if is_916:
        fade_len = 70
        fade_1_start = max(740, min(835, int(top_text_bottom + 38)))
        fade_1_end = fade_1_start + fade_len
        fade_2_start = 1430
        fade_2_end = fade_2_start + fade_len
        tefekkur_start_y = fade_2_end + 25
    else:
        fade_len = 55
        fade_1_start = max(490, min(610, int(top_text_bottom + 28)))
        fade_1_end = fade_1_start + fade_len
        fade_2_start = 1040
        fade_2_end = fade_2_start + fade_len
        tefekkur_start_y = fade_2_end + 20

    # 6. Keten Zemin & Cosine Tül Degrade
    band_h = fade_2_end - fade_1_start
    keten_img = create_paper_background(w, band_h, KETEN_CENTER, KETEN_OUTER).convert("RGBA")
    mask_arr = np.ones((band_h, w), dtype=float) * 255.0

    fade_top_len = fade_1_end - fade_1_start
    fade_bot_len = fade_2_end - fade_2_start

    for y_i in range(fade_top_len):
        f = 0.5 * (1.0 - np.cos(np.pi * (y_i / fade_top_len)))
        mask_arr[y_i, :] *= f

    for y_i in range(fade_bot_len):
        f = 0.5 * (1.0 - np.cos(np.pi * (y_i / fade_bot_len)))
        mask_arr[band_h - 1 - y_i, :] *= f

    mask_img = Image.fromarray(np.clip(mask_arr, 0, 255).astype(np.uint8), mode="L")
    im.paste(keten_img, (0, fade_1_start), mask_img)

    # 7. Odak Elmasları
    draw = ImageDraw.Draw(im)
    def draw_subtle_diamond(cx: int, cy: int, r: int = 7, fill: str = cfg["accent_gold"]):
        draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)

    diamond_r = 7 if is_916 else 6
    draw_subtle_diamond(w // 2, fade_1_start - 16, r=diamond_r, fill=cfg["accent_gold"])
    draw_subtle_diamond(w // 2, fade_2_end + 16, r=diamond_r, fill=cfg["accent_gold"])

    # 8. Üst Filigran (Arapça Arkası)
    fili_top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(fili_top)
    font_size_fili = 290 if is_916 else 225
    f_dev_ar = font_al(FONT_ARAPCA, font_size_fili)
    fili_str = arapca_hazirla(cfg["fili_txt"])
    dbb = fdraw.textbbox((0, 0), fili_str, font=f_dev_ar)
    dw = dbb[2] - dbb[0]
    fili_y = 350 if is_916 else 230
    fdraw.text(((w - dw) / 2, fili_y), fili_str, font=f_dev_ar, fill=(255, 255, 255, 13))
    im.paste(fili_top, (0, 0), fili_top)

    # 9. Orta Filigran (Dua Eden Eller)
    hands_mask = extract_dua_hands_mask()
    if hands_mask is not None:
        fili_meal = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        center_meal_y = (fade_1_end + fade_2_start) // 2
        target_w = 480 if is_916 else 380
        aspect = hands_mask.height / hands_mask.width
        target_h = int(target_w * aspect)
        hands_resized = hands_mask.resize((target_w, target_h), Image.Resampling.LANCZOS)
        color_layer = Image.new("RGBA", (target_w, target_h), (180, 83, 9, 20 if is_916 else 18))
        fili_meal.paste(color_layer, ((w - target_w) // 2, center_meal_y - target_h // 2), hands_resized)
        im.paste(fili_meal, (0, 0), fili_meal)

    draw = ImageDraw.Draw(im)

    # 10. Üst Metin Çizimi
    draw.text(((w - (t_bb[2] - t_bb[0])) / 2, start_tac_y - t_bb[1]), tac_txt, font=f_tac, fill="#FFFDF9")

    cur_y = tac_bottom_y + gap_tac_ar
    for s in ar_satirlar:
        bb = draw.textbbox((0, 0), s, font=f_ar)
        sw = bb[2] - bb[0]
        draw.text(((w - sw) / 2 - bb[0], cur_y - bb[1]), s, font=f_ar, fill="#FFFDF9")
        cur_y += (bb[3] - bb[1]) + ar_line_gap

    cur_y += gap_ar_ok
    for ol in ok_lines:
        ob = draw.textbbox((0, 0), ol, font=f_ok)
        draw.text(((w - (ob[2] - ob[0])) / 2 - ob[0], cur_y - ob[1]), ol, font=f_ok, fill="#EADBC8")
        cur_y += ok_line_step

    # 11. Orta Bölüm: Hero Türkçe Hadis Metni (Anlam Odaklı İri Tipografi)
    solid_meal_h = fade_2_start - fade_1_end
    temiz_hadis = hadis_metni.strip("“”\"' ")
    if vurgulanan_kelime and ("**" not in temiz_hadis) and (vurgulanan_kelime in temiz_hadis):
        temiz_hadis = temiz_hadis.replace(vurgulanan_kelime, f"**{vurgulanan_kelime}**")

    raw_tokens_hadis = re.sub(r'\*\*', '', temiz_hadis)
    tr_len = len(temiz_hadis)
    tr_words = raw_tokens_hadis.split()

    if len(tr_words) <= 5 or tr_len <= 35:
        pt_hero = 108 if is_916 else 90
    elif len(tr_words) <= 10 or tr_len <= 65:
        pt_hero = 96 if is_916 else 78
    elif len(tr_words) <= 18 or tr_len <= 115:
        pt_hero = 84 if is_916 else 70
    elif len(tr_words) <= 26 or tr_len <= 160:
        pt_hero = 78 if is_916 else 64
    else:
        pt_hero = 70 if is_916 else 56

    while pt_hero >= 44:
        f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
        f_hero_r = font_al(FONT_BASLIK, pt_hero, agirlik=400)
        tokens = parse_markdown_bold(temiz_hadis)
        hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_r, f_hero_b, max_w - 40, draw)
        step_hero = int(pt_hero * 1.30)
        hero_h = len(hero_wrapped) * step_hero
        if hero_h <= solid_meal_h - (24 if is_916 else 14):
            break
        pt_hero -= 2

    f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
    f_hero_r = font_al(FONT_BASLIK, pt_hero, agirlik=400)
    tokens = parse_markdown_bold(temiz_hadis)
    hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_r, f_hero_b, max_w - 40, draw)
    step_hero = int(pt_hero * 1.30)
    hero_h = len(hero_wrapped) * step_hero

    cur_meal_y = fade_1_end + (solid_meal_h - hero_h) // 2

    for line_tokens, line_w in hero_wrapped:
        line_x = (w - line_w) // 2
        for word, is_b, word_w in line_tokens:
            f = f_hero_b if is_b else f_hero_r
            c = cfg["bold_color"] if is_b else "#1C1917"
            draw.text((line_x, cur_meal_y), word, font=f, fill=c)
            line_x += word_w + hero_space_w
        cur_meal_y += step_hero

    # 12. Alt Bölüm: Tefekkür & Tescilli Kaynak (Erime Dışında Sabit Kadife Zemin)
    bot_y = tefekkur_start_y
    clean_tef = (tefekkur_notu or "Müslümanın basiretli, uyanık ve tecrübelerinden ders çıkaran bir duruşu olmalıdır.").strip().strip('“”" ')
    pt_tef = 30 if is_916 else 25
    f_tef = font_al(FONT_GOVDE, pt_tef, agirlik=400)
    tef_lines = metin_satirla(f"“{clean_tef}”", f_tef, max_w - 40, draw)

    step_tef = int(pt_tef * 1.34)
    for tl in tef_lines:
        tlb = draw.textbbox((0, 0), tl, font=f_tef)
        draw.text(((w - (tlb[2] - tlb[0])) / 2, bot_y), tl, font=f_tef, fill="#FFF5F2")
        bot_y += step_tef
    bot_y += 16 if is_916 else 10

    kaynak_txt = (kaynak_ravi or kaynak or "Riyâzü's-Sâlihîn").strip().upper()
    pt_kaynak = 17 if is_916 else 15
    f_kaynak = font_al(FONT_UI, pt_kaynak, agirlik=700)
    kb = draw.textbbox((0, 0), kaynak_txt, font=f_kaynak)
    draw.text(((w - (kb[2] - kb[0])) / 2, bot_y), kaynak_txt, font=f_kaynak, fill="#EADBC8")

    if not cikti_dosya_adi:
        cikti_dosya_adi = f"hadis_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.convert("RGB").save(str(cikti_yolu), quality=98)
    return cikti_yolu


# ==============================================================================
# 8 MANEVİ RUH HALİ RENK PALETLERİ (Ezan Plus Günün Duası V18)
# ==============================================================================
DUA_RENK_PALETLERI: Dict[str, dict] = {
    # 1. İç Sıkıntısı ve Daralma Hissi -> Gece Safiri (Kalbe ferahlık & İnşirah)
    "gece_safiri": {
        "ad": "Gece Safiri (İnşirah & Ferahlık)",
        "center_rgb": (24, 52, 88),     # #183458
        "outer_rgb": (10, 22, 40),      # #0A1628
        "c_divider": "#355F8D",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF9EE",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#DFE9F4",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#B8CCE0",
        "fili_rgba": (253, 230, 186, 22),
    },
    # 2. Gelecek Endişesi ve Kaygı -> Okyanus Huzuru (Teal / Derin Deniz)
    "okyanus_huzuru": {
        "ad": "Okyanus Huzuru (Sükunet & Güven)",
        "center_rgb": (18, 68, 80),     # #124450
        "outer_rgb": (8, 32, 42),       # #08202A
        "c_divider": "#2C7588",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F2FAF9",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#D8EEF0",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#B2DCE0",
        "fili_rgba": (253, 230, 186, 22),
    },
    # 3. Hastalık ve Şifa Talebi -> Mescid Zümrüdü (Ravza Şifası)
    "mescid_zumrudu": {
        "ad": "Mescid Zümrüdü (Ravza Şifası)",
        "center_rgb": (22, 72, 54),     # #164836
        "outer_rgb": (8, 34, 24),       # #082218
        "c_divider": "#327A5E",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F2FAF6",
        "c_accent": "#FCE7B8",
        "c_body_reg": "#D6EDE2",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#B2DBC6",
        "fili_rgba": (252, 231, 184, 22),
    },
    # 4. Şükür ve Sevinç Anı -> Sıcak Kehribar (Hamd & Minnet)
    "sicak_kehribar": {
        "ad": "Sıcak Kehribar (Hamd & Minnet)",
        "center_rgb": (156, 68, 34),    # #9C4422
        "outer_rgb": (86, 30, 12),      # #561E0C
        "c_divider": "#BC5B34",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF9F0",
        "c_accent": "#FDE4B0",
        "c_body_reg": "#FCE6DA",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#E8C8B6",
        "fili_rgba": (253, 228, 176, 22),
    },
    # 5. Tevekkül ve Teslimiyet İhtiyacı -> Derin Moka / Sahra
    "derin_kahve": {
        "ad": "Derin Moka / Sahra (Tevekkül & Teslimiyet)",
        "center_rgb": (82, 50, 38),     # #523226
        "outer_rgb": (42, 22, 14),      # #2A160E
        "c_divider": "#986250",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF8F2",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#F6E6DC",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#DAC2B4",
        "fili_rgba": (253, 230, 186, 22),
    },
    # 6. Tevbe ve Günahlardan Arınma Niyazı -> Asil Mürdüm (Ametist & Mağfiret)
    "asil_murdum": {
        "ad": "Asil Mürdüm (Tevbe & Mağfiret)",
        "center_rgb": (88, 32, 70),     # #582046
        "outer_rgb": (42, 12, 34),      # #2A0C22
        "c_divider": "#823768",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF5F8",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FCE4F0",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#E0BACF",
        "fili_rgba": (253, 230, 186, 22),
    },
    # 7. Geçim Darlığı ve Helal Rızık Arayışı -> Yakut Kırmızı (Bereket & Rızık)
    "yakut_kirmizi": {
        "ad": "Yakut Kırmızı (Bereket & Rızık)",
        "center_rgb": (150, 26, 32),    # #961A20
        "outer_rgb": (80, 12, 16),      # #500C10
        "c_divider": "#BA3A40",
        "c_hero": "#FFFFFF",
        "c_arabic": "#FFF8F2",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#FDE4E6",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#E8BBC0",
        "fili_rgba": (253, 230, 186, 22),
    },
    # 8. Öfke ve Kararsızlık Durumu -> Huzur Mavisi (İtidal & Sekînet)
    "huzur_mavisi": {
        "ad": "Huzur Mavisi (İtidal & Sekînet)",
        "center_rgb": (28, 44, 70),     # #1C2C46
        "outer_rgb": (12, 20, 32),      # #0C1420
        "c_divider": "#385880",
        "c_hero": "#FFFFFF",
        "c_arabic": "#F4F8FC",
        "c_accent": "#FDE6BA",
        "c_body_reg": "#DEE8F4",
        "c_body_bold": "#FFFFFF",
        "c_sub": "#B8CADE",
        "fili_rgba": (253, 230, 186, 22),
    },
}


def dua_palet_sec(ruh_hali: Optional[str] = None, dua_basligi: Optional[str] = None) -> Dict[str, Any]:
    """Ruh haline veya dua başlığına göre en uygun renk paletini döner."""
    metin = f"{ruh_hali or ''} {dua_basligi or ''}".lower()
    if any(k in metin for k in ["sıkıntı", "daralma", "inşirah", "ferahlık"]):
        return DUA_RENK_PALETLERI["gece_safiri"]
    if any(k in metin for k in ["şifa", "hastalık", "dert", "ağrı"]):
        return DUA_RENK_PALETLERI["mescid_zumrudu"]
    if any(k in metin for k in ["şükür", "sevinç", "hamd", "nimet"]):
        return DUA_RENK_PALETLERI["sicak_kehribar"]
    if any(k in metin for k in ["endişe", "kaygı", "korku", "sınav", "iş", "çaresiz"]):
        return DUA_RENK_PALETLERI["okyanus_huzuru"]
    if any(k in metin for k in ["tevekkül", "teslimiyet", "namaz"]):
        return DUA_RENK_PALETLERI["derin_kahve"]
    if any(k in metin for k in ["tevbe", "arınma", "günah", "mağfiret", "af"]):
        return DUA_RENK_PALETLERI["asil_murdum"]
    if any(k in metin for k in ["rızık", "geçim", "borç", "bereket", "darlık"]):
        return DUA_RENK_PALETLERI["yakut_kirmizi"]
    if any(k in metin for k in ["öfke", "kararsızlık", "vesvese", "itidal"]):
        return DUA_RENK_PALETLERI["huzur_mavisi"]
    return DUA_RENK_PALETLERI["gece_safiri"]


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
    ruh_hali: Optional[str] = None,
    palet_adi: Optional[str] = None,
) -> Path:
    """
    Ezan Plus Günün Duası şablonu (V20 Mimarisi - Selçuklu Petrol Zümrüdü & Keten Parşömen Flex Mizanpaj).
    1080x1350 (4:5 Feed) ve 1080x1920 (9:16 Story) tam destekler.
    Bounding-box emniyetli sıfır çakışma, erimeden izole edilmiş fazilet notu,
    kısa dualarda devasa 142pt/108pt tipografi, uzun münacatlarda ise anlamı öne çıkaran geniş Keten bandı içerir.
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")
    cfg = DUA_SABIT_PALET
    max_w = 930 if is_916 else 920

    from .ses import turkce_kisaltmalari_genislet
    turkce_anlam = turkce_kisaltmalari_genislet(turkce_anlam)
    dua_basligi = turkce_kisaltmalari_genislet(dua_basligi)
    if kimin_duasi:
        kimin_duasi = turkce_kisaltmalari_genislet(kimin_duasi)

    # 1. Taban Kadife Parşömen
    im = create_paper_background(w, h, cfg["center_rgb"], cfg["outer_rgb"]).convert("RGBA")
    draw = ImageDraw.Draw(im)

    # 2. Header & CTA Butonu
    top_header_y = 215 if is_916 else 55
    ayrac_y = draw_kart_header_bar(im, draw, cfg, top_y=top_header_y, rozet_text=cfg["rozet_txt"])
    cta_ust_y = _kelime_cta_butonu_ciz(im, format_tipi)

    # 3. Taç Başlık (Niyaz Künyesi)
    pt_tac = 34 if is_916 else 28
    f_tac = font_al(FONT_GOVDE, pt_tac, agirlik=700)
    tac_txt = f"“ {(kimin_duasi or dua_basligi).strip()} ”"
    t_bb = draw.textbbox((0, 0), tac_txt, font=f_tac)
    tac_h = t_bb[3] - t_bb[1]
    start_tac_y = ayrac_y + (30 if is_916 else 18)
    tac_bottom_y = start_tac_y + tac_h

    # 4. Üst Bölüm: Arapça ve Latin Okunuş Boyutlandırma
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", arapca_metin).strip() if arapca_metin else ""
    words_ar = ar_temiz.split() if ar_temiz else []
    ar_word_count = len(words_ar)

    if ar_word_count <= 4:
        pt_ar = 142 if is_916 else 120
        pt_ok = 46 if is_916 else 36
    elif ar_word_count <= 8:
        pt_ar = 110 if is_916 else 94
        pt_ok = 40 if is_916 else 32
    elif ar_word_count <= 14:
        pt_ar = 94 if is_916 else 80
        pt_ok = 34 if is_916 else 28
    else:
        pt_ar = 84 if is_916 else 72
        pt_ok = 30 if is_916 else 24

    ok_ham = (arapca_okunus or "").strip("“”\"'{}[] ")
    ok_gosterim = f"“ {ok_ham} ”" if ok_ham else ""

    # Dikey Emniyet Tavanı (Okunuş erimeye asla değemez)
    hard_max_ok_bottom = 815 if is_916 else 595

    while pt_ar >= 64:
        f_ar = font_al(FONT_ARAPCA, pt_ar)
        ar_satirlar = arapca_satirla(ar_temiz, f_ar, max_w, draw) if ar_temiz else []
        f_ok = font_al(FONT_GOVDE, pt_ok, agirlik=400)
        ok_lines = metin_satirla(ok_gosterim, f_ok, max_w, draw) if ok_gosterim else []

        gap_tac_ar = 34 if is_916 else 22
        ar_line_gap = 18 if is_916 else 12
        cur_calc_y = tac_bottom_y + gap_tac_ar
        for s in ar_satirlar:
            bb = draw.textbbox((0, 0), s, font=f_ar)
            cur_calc_y += (bb[3] - bb[1]) + ar_line_gap
        gap_ar_ok = 26 if is_916 else 16
        cur_calc_y += gap_ar_ok
        ok_line_step = int(pt_ok * 1.30)
        cur_calc_y += len(ok_lines) * ok_line_step

        if cur_calc_y <= hard_max_ok_bottom:
            break
        pt_ar -= 3
        pt_ok = max(28 if is_916 else 22, int(pt_ar * 0.38))

    f_ar = font_al(FONT_ARAPCA, pt_ar)
    ar_satirlar = arapca_satirla(ar_temiz, f_ar, max_w, draw) if ar_temiz else []
    f_ok = font_al(FONT_GOVDE, pt_ok, agirlik=400)
    ok_lines = metin_satirla(ok_gosterim, f_ok, max_w, draw) if ok_gosterim else []

    gap_tac_ar = 34 if is_916 else 22
    ar_line_gap = 18 if is_916 else 12
    gap_ar_ok = 26 if is_916 else 16
    ok_line_step = int(pt_ok * 1.30)

    top_text_bottom = tac_bottom_y + gap_tac_ar
    for s in ar_satirlar:
        bb = draw.textbbox((0, 0), s, font=f_ar)
        top_text_bottom += (bb[3] - bb[1]) + ar_line_gap
    top_text_bottom += gap_ar_ok + len(ok_lines) * ok_line_step

    # 5. Dinamik Flex Keten Bandı (Anlam Odaklı Genişleme)
    if is_916:
        fade_len = 70
        fade_1_start = max(740, min(835, int(top_text_bottom + 38)))
        fade_1_end = fade_1_start + fade_len
        fade_2_start = 1430
        fade_2_end = fade_2_start + fade_len
        tefekkur_start_y = fade_2_end + 25
    else:
        fade_len = 55
        fade_1_start = max(490, min(610, int(top_text_bottom + 28)))
        fade_1_end = fade_1_start + fade_len
        fade_2_start = 1040
        fade_2_end = fade_2_start + fade_len
        tefekkur_start_y = fade_2_end + 20

    # 6. Keten Zemin & Cosine Tül Degrade
    band_h = fade_2_end - fade_1_start
    keten_img = create_paper_background(w, band_h, KETEN_CENTER, KETEN_OUTER).convert("RGBA")
    mask_arr = np.ones((band_h, w), dtype=float) * 255.0

    fade_top_len = fade_1_end - fade_1_start
    fade_bot_len = fade_2_end - fade_2_start

    for y_i in range(fade_top_len):
        f = 0.5 * (1.0 - np.cos(np.pi * (y_i / fade_top_len)))
        mask_arr[y_i, :] *= f

    for y_i in range(fade_bot_len):
        f = 0.5 * (1.0 - np.cos(np.pi * (y_i / fade_bot_len)))
        mask_arr[band_h - 1 - y_i, :] *= f

    mask_img = Image.fromarray(np.clip(mask_arr, 0, 255).astype(np.uint8), mode="L")
    im.paste(keten_img, (0, fade_1_start), mask_img)

    # 7. Odak Elmasları
    draw = ImageDraw.Draw(im)
    def draw_subtle_diamond(cx: int, cy: int, r: int = 7, fill: str = cfg["accent_gold"]):
        draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)

    diamond_r = 7 if is_916 else 6
    draw_subtle_diamond(w // 2, fade_1_start - 16, r=diamond_r, fill=cfg["accent_gold"])
    draw_subtle_diamond(w // 2, fade_2_end + 16, r=diamond_r, fill=cfg["accent_gold"])

    # 8. Üst Filigran (Arapça Arkası)
    fili_top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(fili_top)
    font_size_fili = 290 if is_916 else 225
    f_dev_ar = font_al(FONT_ARAPCA, font_size_fili)
    fili_str = arapca_hazirla(cfg["fili_txt"])
    dbb = fdraw.textbbox((0, 0), fili_str, font=f_dev_ar)
    dw = dbb[2] - dbb[0]
    fili_y = 350 if is_916 else 230
    fdraw.text(((w - dw) / 2, fili_y), fili_str, font=f_dev_ar, fill=(255, 255, 255, 13))
    im.paste(fili_top, (0, 0), fili_top)

    # 9. Orta Filigran (Dua Eden Eller)
    hands_mask = extract_dua_hands_mask()
    if hands_mask is not None:
        fili_meal = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        center_meal_y = (fade_1_end + fade_2_start) // 2
        target_w = 480 if is_916 else 380
        aspect = hands_mask.height / hands_mask.width
        target_h = int(target_w * aspect)
        hands_resized = hands_mask.resize((target_w, target_h), Image.Resampling.LANCZOS)
        color_layer = Image.new("RGBA", (target_w, target_h), (180, 83, 9, 20 if is_916 else 18))
        fili_meal.paste(color_layer, ((w - target_w) // 2, center_meal_y - target_h // 2), hands_resized)
        im.paste(fili_meal, (0, 0), fili_meal)

    draw = ImageDraw.Draw(im)

    # 10. Üst Metin Çizimi
    draw.text(((w - (t_bb[2] - t_bb[0])) / 2, start_tac_y - t_bb[1]), tac_txt, font=f_tac, fill="#FFFDF9")

    cur_y = tac_bottom_y + gap_tac_ar
    for s in ar_satirlar:
        bb = draw.textbbox((0, 0), s, font=f_ar)
        sw = bb[2] - bb[0]
        draw.text(((w - sw) / 2 - bb[0], cur_y - bb[1]), s, font=f_ar, fill="#FFFDF9")
        cur_y += (bb[3] - bb[1]) + ar_line_gap

    cur_y += gap_ar_ok
    for ol in ok_lines:
        ob = draw.textbbox((0, 0), ol, font=f_ok)
        draw.text(((w - (ob[2] - ob[0])) / 2 - ob[0], cur_y - ob[1]), ol, font=f_ok, fill="#EADBC8")
        cur_y += ok_line_step

    # 11. Orta Bölüm: Hero Türkçe Dua Niyazı (Anlam Odaklı İri Tipografi)
    solid_meal_h = fade_2_start - fade_1_end
    temiz_anlam = turkce_anlam.strip("“”\"' ")
    if vurgulanan_kelime and ("**" not in temiz_anlam) and (vurgulanan_kelime in temiz_anlam):
        temiz_anlam = temiz_anlam.replace(vurgulanan_kelime, f"**{vurgulanan_kelime}**")

    raw_tokens_dua = re.sub(r'\*\*', '', temiz_anlam)
    tr_len = len(temiz_anlam)
    tr_words = raw_tokens_dua.split()

    if len(tr_words) <= 5 or tr_len <= 35:
        pt_hero = 108 if is_916 else 90
    elif len(tr_words) <= 10 or tr_len <= 65:
        pt_hero = 96 if is_916 else 78
    elif len(tr_words) <= 18 or tr_len <= 115:
        pt_hero = 84 if is_916 else 70
    elif len(tr_words) <= 26 or tr_len <= 160:
        pt_hero = 78 if is_916 else 64
    else:
        pt_hero = 70 if is_916 else 56

    while pt_hero >= 44:
        f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
        f_hero_r = font_al(FONT_BASLIK, pt_hero, agirlik=400)
        tokens = parse_markdown_bold(temiz_anlam)
        hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_r, f_hero_b, max_w - 40, draw)
        step_hero = int(pt_hero * 1.30)
        hero_h = len(hero_wrapped) * step_hero
        if hero_h <= solid_meal_h - (24 if is_916 else 14):
            break
        pt_hero -= 2

    f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
    f_hero_r = font_al(FONT_BASLIK, pt_hero, agirlik=400)
    tokens = parse_markdown_bold(temiz_anlam)
    hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_r, f_hero_b, max_w - 40, draw)
    step_hero = int(pt_hero * 1.30)
    hero_h = len(hero_wrapped) * step_hero

    cur_meal_y = fade_1_end + (solid_meal_h - hero_h) // 2

    for line_tokens, line_w in hero_wrapped:
        line_x = (w - line_w) // 2
        for word, is_b, word_w in line_tokens:
            f = f_hero_b if is_b else f_hero_r
            c = cfg["bold_color"] if is_b else "#1C1917"
            draw.text((line_x, cur_meal_y), word, font=f, fill=c)
            line_x += word_w + hero_space_w
        cur_meal_y += step_hero

    # 12. Alt Bölüm: Fazilet Notu & Kaynak (Erime Dışında Sabit Kadife Zemin)
    bot_y = tefekkur_start_y
    clean_faz = (fazilet_notu or okunus_veya_fazilet or kaynak_fazilet or "Bu mübarek niyaz, kalbe ferahlık ve işlerde kolaylık için sabah-akşam ihlasla tekrar edilir.").strip().strip('“”" ')
    pt_faz = 30 if is_916 else 25
    f_faz = font_al(FONT_GOVDE, pt_faz, agirlik=400)
    faz_lines = metin_satirla(f"“{clean_faz}”", f_faz, max_w - 40, draw)

    step_faz = int(pt_faz * 1.34)
    for fl in faz_lines:
        flb = draw.textbbox((0, 0), fl, font=f_faz)
        draw.text(((w - (flb[2] - flb[0])) / 2, bot_y), fl, font=f_faz, fill="#FFF5F2")
        bot_y += step_faz
    bot_y += 16 if is_916 else 10

    raw_kaynak = (kaynak_ref or "Kur'an-ı Kerim").strip()
    ref_txt = re.split(r'[\.;,]?\s*Ayrıca bkz?[\.:]?', raw_kaynak, flags=re.IGNORECASE)[0].strip() or raw_kaynak
    ref_txt = ref_txt.upper()

    pt_ref = 17 if is_916 else 15
    f_ref = font_al(FONT_UI, pt_ref, agirlik=700)
    rb = draw.textbbox((0, 0), ref_txt, font=f_ref)
    draw.text(((w - (rb[2] - rb[0])) / 2, bot_y), ref_txt, font=f_ref, fill="#EADBC8")

    if not cikti_dosya_adi:
        cikti_dosya_adi = f"dua_{format_tipi.replace(':', '_')}.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.convert("RGB").save(str(cikti_yolu), quality=98)
    return cikti_yolu


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
    kelime_tr = (kelime_tr or "Kur'an Sözlüğü").strip()
    if not kelime_tr:
        kelime_tr = "Kur'an Sözlüğü"

    target_pt = 172 if is_916 else 130
    min_pt_floor = 154 if is_916 else 118

    pt_latin = target_pt
    f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
    lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw)
    if not lines_tr:
        lines_tr = [kelime_tr]

    # Çoklu satırlı kavramlarda dikey sıkışmayı önlemek için akıllı ölçeklendirme
    if len(lines_tr) >= 3:
        target_pt = 118 if is_916 else 88
        min_pt_floor = 96 if is_916 else 72
        pt_latin = target_pt
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw) or [kelime_tr]
    elif len(lines_tr) == 2:
        target_pt = 138 if is_916 else 104
        min_pt_floor = 114 if is_916 else 86
        pt_latin = target_pt
        f_latin = font_al(FONT_GOVDE, pt_latin, agirlik=700)
        lines_tr = kelime_basligi_satirla(kelime_tr, f_latin, max_text_w, draw) or [kelime_tr]

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
