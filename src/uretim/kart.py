"""
sablon_ciz.py — Ezan Plus Görsel Tasarım ve Çizim Motoru
Pillow kullanarak Ezan Plus kurumsal kimliğine %100 sadık,
1080x1350 px (4:5 dikey post) görsel şablonları üretir.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

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


def arapca_hazirla(metin: str) -> str:
    """Arapça metni sağdan sola ve harf bitişmelerine göre düzenler."""
    if not metin:
        return ""
    yeniden_sekillendir = arabic_reshaper.reshape(metin)
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
) -> Tuple[Image.Image, ImageDraw.ImageDraw, int, int, int, int]:
    """Tüm postlarda ortak olan Ezan Plus kağıt zeminini ve kurumsal üst barını hazırlar."""
    bg_krem = get_renk("bg_krem", "#F4F1EA")
    im = Image.new("RGB", (GENISLIK, YUKSEKLIK), bg_krem)
    draw = ImageDraw.Draw(im)

    kart_kenar_payi = 56
    kart_x1 = kart_kenar_payi
    kart_y1 = 80
    kart_x2 = GENISLIK - kart_kenar_payi
    kart_y2 = YUKSEKLIK - 80

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
    # Temiz nokta simgesi
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
    tarih_metni: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
) -> Path:
    """Ezan Plus Günün Ayeti şablonu (1080x1350 px)."""
    im, draw, kart_x1, kart_y1, kart_x2, kart_y2 = _kart_tabani_ve_ust_bar(
        kategori_rozet="AYET-İ KERİME",
        rozet_bg="#ECFDF5",
        rozet_yazi=get_renk("yesil", "#0D5C3A"),
        alt_baslik="GÜNLÜK İBADET YARDIMCINIZ",
    )

    imleç_y = kart_y1 + 170
    icerik_genislik = (kart_x2 - kart_x1) - 96

    # Arapça Metin
    if arapca_metin:
        arapca_duz = arapca_hazirla(arapca_metin.strip())
        font_ar = font_al(FONT_ARAPCA, 48)
        ar_satirlar = metin_satirla(arapca_duz, font_ar, icerik_genislik, draw)
        for satir in ar_satirlar:
            bbox_s = draw.textbbox((0, 0), satir, font=font_ar)
            sw = bbox_s[2] - bbox_s[0]
            draw.text(((GENISLIK - sw) // 2, imleç_y), satir, font=font_ar, fill=get_renk("yesil", "#0D5C3A"))
            imleç_y += 76
        imleç_y += 30

        # Süsleme
        ayrac_metin = "✦ ✦ ✦"
        font_ayrac = font_al(FONT_UI, 18)
        bbox_a = draw.textbbox((0, 0), ayrac_metin, font=font_ayrac)
        aw = bbox_a[2] - bbox_a[0]
        draw.text(((GENISLIK - aw) // 2, imleç_y), ayrac_metin, font=font_ayrac, fill=get_renk("altin", "#D97706"))
        imleç_y += 50

    # Türkçe Meal
    font_meal_boyut = 42 if len(turkce_meal) < 160 else 35
    font_tr = font_al(FONT_BASLIK, font_meal_boyut)

    tirnak_tr = f'"{turkce_meal.strip()}"'
    tr_satirlar = metin_satirla(tirnak_tr, font_tr, icerik_genislik, draw)

    for satir in tr_satirlar:
        bbox_t = draw.textbbox((0, 0), satir, font=font_tr)
        tw = bbox_t[2] - bbox_t[0]
        draw.text(((GENISLIK - tw) // 2, imleç_y), satir, font=font_tr, fill=get_renk("metin_ana", "#0F172A"))
        imleç_y += int(font_meal_boyut * 1.5)

    imleç_y += 34

    # Kaynak Rozeti
    if sure_ayet:
        font_kaynak = font_al(FONT_UI, 24)
        k_metin = sure_ayet.upper()
        bbox_k = draw.textbbox((0, 0), k_metin, font=font_kaynak)
        kw = bbox_k[2] - bbox_k[0]
        kx = (GENISLIK - kw) // 2
        yuvarlak_kose_ciz(
            draw,
            (kx - 24, imleç_y - 6, kx + kw + 24, imleç_y + 36),
            radius=12,
            dolgu="#F5F3EF",
        )
        draw.text((kx, imleç_y), k_metin, font=font_kaynak, fill=get_renk("koyu_kirmizi", "#962D22"))
        imleç_y += 74

    # Tefekkür Notu
    if tefekkur_notu:
        kutu_y1 = imleç_y + 10
        font_tef_baslik = font_al(FONT_UI, 20)
        font_tef = font_al(FONT_UI, 22)

        tef_satirlar = metin_satirla(tefekkur_notu.strip(), font_tef, icerik_genislik - 48, draw)
        kutu_h = 50 + (len(tef_satirlar) * 34)

        kutu_x1 = kart_x1 + 48
        kutu_x2 = kart_x2 - 48
        kutu_y2 = min(kutu_y1 + kutu_h, kart_y2 - 110)

        yuvarlak_kose_ciz(
            draw,
            (kutu_x1, kutu_y1, kutu_x2, kutu_y2),
            radius=20,
            dolgu="#F0FDF4",
            kenarlik="#DCFCE7",
            kenarlik_kalinlik=1,
        )
        draw.rounded_rectangle([kutu_x1, kutu_y1, kutu_x1 + 6, kutu_y2], radius=3, fill=get_renk("yesil", "#0D5C3A"))
        draw.text((kutu_x1 + 24, kutu_y1 + 16), "GÜNÜN DERSİ & TEFEKKÜR", font=font_tef_baslik, fill=get_renk("yesil", "#0D5C3A"))

        tef_y = kutu_y1 + 48
        for satir in tef_satirlar:
            if tef_y + 30 > kutu_y2:
                break
            draw.text((kutu_x1 + 24, tef_y), satir, font=font_tef, fill="#166534")
            tef_y += 34

    _alt_bar_ciz(draw, kart_x1, kart_x2, kart_y2, "Ezan Plus uygulamasında sesli dinleyin")

    if not cikti_dosya_adi:
        cikti_dosya_adi = "ornek_ayet.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=95)
    return cikti_yolu


def hadis_karti_ciz(
    hadis_metni: str,
    kaynak_ravi: str,
    tefekkur_notu: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
) -> Path:
    """Ezan Plus Günün Hadisi şablonu (1080x1350 px)."""
    im, draw, kart_x1, kart_y1, kart_x2, kart_y2 = _kart_tabani_ve_ust_bar(
        kategori_rozet="HADİS-İ ŞERİF",
        rozet_bg="#FFF1F2",
        rozet_yazi=get_renk("kirmizi", "#C0392B"),
        alt_baslik="SAHİH HADİS REHBERİ",
    )

    imleç_y = kart_y1 + 180
    icerik_genislik = (kart_x2 - kart_x1) - 96

    # İntro Başlık
    font_intro = font_al(FONT_BASLIK, 34)
    intro_metin = "Resûlullah sallallahu aleyhi ve sellem şöyle buyurdu:"
    bbox_in = draw.textbbox((0, 0), intro_metin, font=font_intro)
    in_w = bbox_in[2] - bbox_in[0]
    draw.text(((GENISLIK - in_w) // 2, imleç_y), intro_metin, font=font_intro, fill=get_renk("koyu_kirmizi", "#962D22"))
    imleç_y += 70

    # Hadis Metni
    font_hadis_boyut = 40 if len(hadis_metni) < 200 else 34
    font_hadis = font_al(FONT_BASLIK, font_hadis_boyut)

    tirnakli_hadis = f'"{hadis_metni.strip()}"'
    hadis_satirlar = metin_satirla(tirnakli_hadis, font_hadis, icerik_genislik, draw)

    for satir in hadis_satirlar:
        bbox_h = draw.textbbox((0, 0), satir, font=font_hadis)
        hw = bbox_h[2] - bbox_h[0]
        draw.text(((GENISLIK - hw) // 2, imleç_y), satir, font=font_hadis, fill=get_renk("metin_ana", "#0F172A"))
        imleç_y += int(font_hadis_boyut * 1.5)

    imleç_y += 36

    # Kaynak
    if kaynak_ravi:
        font_kaynak = font_al(FONT_UI, 24)
        k_metin = kaynak_ravi
        bbox_k = draw.textbbox((0, 0), k_metin, font=font_kaynak)
        kw = bbox_k[2] - bbox_k[0]
        kx = (GENISLIK - kw) // 2
        yuvarlak_kose_ciz(
            draw,
            (kx - 24, imleç_y - 6, kx + kw + 24, imleç_y + 36),
            radius=12,
            dolgu="#FFF7ED",
            kenarlik="#FFEDD5",
            kenarlik_kalinlik=1,
        )
        draw.text((kx, imleç_y), k_metin, font=font_kaynak, fill=get_renk("altin", "#D97706"))
        imleç_y += 76

    # Tefekkür / Hikmet
    if tefekkur_notu:
        kutu_y1 = imleç_y + 10
        font_tef_baslik = font_al(FONT_UI, 20)
        font_tef = font_al(FONT_UI, 22)

        tef_satirlar = metin_satirla(tefekkur_notu.strip(), font_tef, icerik_genislik - 48, draw)
        kutu_h = 50 + (len(tef_satirlar) * 34)

        kutu_x1 = kart_x1 + 48
        kutu_x2 = kart_x2 - 48
        kutu_y2 = min(kutu_y1 + kutu_h, kart_y2 - 110)

        yuvarlak_kose_ciz(
            draw,
            (kutu_x1, kutu_y1, kutu_x2, kutu_y2),
            radius=20,
            dolgu="#FEF2F2",
            kenarlik="#FEE2E2",
            kenarlik_kalinlik=1,
        )
        draw.rounded_rectangle([kutu_x1, kutu_y1, kutu_x1 + 6, kutu_y2], radius=3, fill=get_renk("kirmizi", "#C0392B"))
        draw.text((kutu_x1 + 24, kutu_y1 + 16), "GÜNÜN HİKMETİ & ÖĞÜDÜ", font=font_tef_baslik, fill=get_renk("kirmizi", "#C0392B"))

        tef_y = kutu_y1 + 48
        for satir in tef_satirlar:
            if tef_y + 30 > kutu_y2:
                break
            draw.text((kutu_x1 + 24, tef_y), satir, font=font_tef, fill="#991B1B")
            tef_y += 34

    _alt_bar_ciz(draw, kart_x1, kart_x2, kart_y2, "6 Sahih Hadis Kaynağı Ezan Plus'ta")

    if not cikti_dosya_adi:
        cikti_dosya_adi = "ornek_hadis.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=95)
    return cikti_yolu


def dua_karti_ciz(
    dua_basligi: str,
    turkce_anlam: str,
    arapca_metin: Optional[str] = None,
    okunus_veya_fazilet: Optional[str] = None,
    cikti_dosya_adi: Optional[str] = None,
) -> Path:
    """Ezan Plus Günün Duası & Hâline Uygun Dua şablonu (1080x1350 px)."""
    im, draw, kart_x1, kart_y1, kart_x2, kart_y2 = _kart_tabani_ve_ust_bar(
        kategori_rozet="GÜNÜN DUASI",
        rozet_bg="#FEF3C7",
        rozet_yazi=get_renk("altin", "#D97706"),
        alt_baslik="MANEVİ REHBER & DUALAR",
    )

    imleç_y = kart_y1 + 160
    icerik_genislik = (kart_x2 - kart_x1) - 96

    # Dua Başlığı (Örn: "Huzursuzluk ve İç Sıkıntısı Anında Okunacak Dua")
    font_baslik = font_al(FONT_BASLIK, 38)
    b_satirlar = metin_satirla(dua_basligi, font_baslik, icerik_genislik, draw)
    for satir in b_satirlar:
        bbox_b = draw.textbbox((0, 0), satir, font=font_baslik)
        bw = bbox_b[2] - bbox_b[0]
        draw.text(((GENISLIK - bw) // 2, imleç_y), satir, font=font_baslik, fill=get_renk("altin", "#D97706"))
        imleç_y += 50
    imleç_y += 24

    # Arapça Dua (Varsa)
    if arapca_metin:
        arapca_duz = arapca_hazirla(arapca_metin.strip())
        font_ar = font_al(FONT_ARAPCA, 44)
        ar_satirlar = metin_satirla(arapca_duz, font_ar, icerik_genislik, draw)
        for satir in ar_satirlar:
            bbox_s = draw.textbbox((0, 0), satir, font=font_ar)
            sw = bbox_s[2] - bbox_s[0]
            draw.text(((GENISLIK - sw) // 2, imleç_y), satir, font=font_ar, fill=get_renk("yesil", "#0D5C3A"))
            imleç_y += 70
        imleç_y += 24

    # Türkçe Anlamı
    font_anlam_boyut = 38 if len(turkce_anlam) < 180 else 32
    font_anlam = font_al(FONT_BASLIK, font_anlam_boyut)

    tirnakli_anlam = f'"{turkce_anlam.strip()}"'
    anlam_satirlar = metin_satirla(tirnakli_anlam, font_anlam, icerik_genislik, draw)

    for satir in anlam_satirlar:
        bbox_a = draw.textbbox((0, 0), satir, font=font_anlam)
        aw = bbox_a[2] - bbox_a[0]
        draw.text(((GENISLIK - aw) // 2, imleç_y), satir, font=font_anlam, fill=get_renk("metin_ana", "#0F172A"))
        imleç_y += int(font_anlam_boyut * 1.5)

    imleç_y += 30

    # Okunuş veya Fazilet Kutusu
    if okunus_veya_fazilet:
        kutu_y1 = imleç_y + 10
        font_faz_baslik = font_al(FONT_UI, 20)
        font_faz = font_al(FONT_UI, 22)

        faz_satirlar = metin_satirla(okunus_veya_fazilet.strip(), font_faz, icerik_genislik - 48, draw)
        kutu_h = 50 + (len(faz_satirlar) * 34)

        kutu_x1 = kart_x1 + 48
        kutu_x2 = kart_x2 - 48
        kutu_y2 = min(kutu_y1 + kutu_h, kart_y2 - 110)

        yuvarlak_kose_ciz(
            draw,
            (kutu_x1, kutu_y1, kutu_x2, kutu_y2),
            radius=20,
            dolgu="#FFFBEB",
            kenarlik="#FDE68A",
            kenarlik_kalinlik=1,
        )
        draw.rounded_rectangle([kutu_x1, kutu_y1, kutu_x1 + 6, kutu_y2], radius=3, fill=get_renk("altin", "#D97706"))
        draw.text((kutu_x1 + 24, kutu_y1 + 16), "DUANIN OKUNUŞU & FAZİLETİ", font=font_faz_baslik, fill=get_renk("altin", "#D97706"))

        faz_y = kutu_y1 + 48
        for satir in faz_satirlar:
            if faz_y + 30 > kutu_y2:
                break
            draw.text((kutu_x1 + 24, faz_y), satir, font=font_faz, fill="#92400E")
            faz_y += 34

    _alt_bar_ciz(draw, kart_x1, kart_x2, kart_y2, "Yüzlerce kategorize dua Ezan Plus'ta")

    if not cikti_dosya_adi:
        cikti_dosya_adi = "ornek_dua.png"
    cikti_yolu = CIKTI_DIZINI / cikti_dosya_adi
    im.save(str(cikti_yolu), quality=95)
    return cikti_yolu
