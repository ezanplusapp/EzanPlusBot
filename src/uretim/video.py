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
    parse_markdown_bold,
    wrap_mixed_tokens,
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

    # 2. ÜST MARKA ALANI (114x114 Logo + Ezan Plus Lora)
    logo_yolu = IKONLAR / "logo.png"
    logo_boyut = 114
    font_marka = font_al(FONT_GOVDE, 76, agirlik=700)
    bbox_m = draw.textbbox((0, 0), "Ezan Plus", font=font_marka)
    mw = bbox_m[2] - bbox_m[0]
    mh = bbox_m[3] - bbox_m[1]
    gap = 22
    ust_x1 = (W - (logo_boyut + gap + mw)) // 2
    ust_y = 80

    if logo_yolu.exists():
        logo = Image.open(logo_yolu).convert("RGBA")
        logo = logo.resize((logo_boyut, logo_boyut), Image.Resampling.LANCZOS)
        maske = Image.new("L", (logo_boyut, logo_boyut), 0)
        draw_m = ImageDraw.Draw(maske)
        draw_m.rounded_rectangle([0, 0, logo_boyut, logo_boyut], radius=30, fill=255)
        im.paste(logo, (ust_x1, ust_y), maske)

    tx = ust_x1 + logo_boyut + gap
    draw.text((tx, ust_y + (logo_boyut - mh) // 2 - bbox_m[1]), "Ezan Plus", font=font_marka, fill=METIN_ANA)

    # 3. KANCA BAŞLIĞI (Stil 3: Editoryal Lora Serif - Seçenek 2 Boşluklu)
    b_y = 222
    s1_temiz = video_baslik_satir1.strip().strip("“”\"'")
    s2_temiz = video_baslik_satir2.strip().strip("“”\"'")

    # 1. Satır: 44pt Lora (Tırnaksız Anons/Çağrı)
    f1 = font_al(FONT_GOVDE, 44, agirlik=500)
    w1 = draw.textlength(s1_temiz, font=f1)
    draw.text(((W - w1) // 2, b_y), s1_temiz, font=f1, fill=METIN_ANA)

    # 2. Satır: 55pt Lora Bold (0.45px kontur tokluğu, baştaki tırnaktan sonra 1 boşluk)
    f2 = font_al(FONT_GOVDE, 55, agirlik=700)
    s2_formatli = f"“ {s2_temiz}”"
    w2 = draw.textlength(s2_formatli, font=f2)
    draw.text(((W - w2) // 2, b_y + 56), s2_formatli, font=f2, fill=KIRMIZI, stroke_width=0.45, stroke_fill=KIRMIZI)

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
    c_y += 70

    kart_ic_genislik = (kx2 - kx1) - 80
    arapca_y_baslangic = c_y

    # RESMİ KAYNAK VE RİVAYET DİPNOTU
    kaynak_metin = "Mushaf-ı Şerif • Meal: Elmalılı Hamdi Yazır • Tilavet: Hafs Rivayeti"
    font_kaynak = font_al(FONT_UI, 18, agirlik=600)
    bbox_k = draw.textbbox((0, 0), kaynak_metin, font=font_kaynak)
    kw = bbox_k[2] - bbox_k[0]
    draw.text(((W - kw) // 2, ky2 - 34), kaynak_metin, font=font_kaynak, fill=METIN_LIGHT)

    # 5. ALT BÖLÜM (Ezan Plus Logo + Store İndirme Butonu)
    nav_w = 700
    nav_h = 88
    nav_x1 = (W - nav_w) // 2
    nav_x2 = nav_x1 + nav_w
    nav_y1 = 1710
    nav_y2 = nav_y1 + nav_h
    btn_y = nav_y1 + nav_h // 2

    yuvarlak_kose_ciz(draw, (nav_x1, nav_y1, nav_x2, nav_y2), radius=34, dolgu="#FFFFFF", kenarlik="#E5DFD3", kenarlik_kalinlik=2)

    # Ezan Plus Logosu (50x50 px)
    logo_btn_size = 50
    if logo_yolu.exists():
        logo_btn = Image.open(logo_yolu).convert("RGBA").resize((logo_btn_size, logo_btn_size), Image.Resampling.LANCZOS)
        btn_mask = Image.new("L", (logo_btn_size, logo_btn_size), 0)
        ImageDraw.Draw(btn_mask).rounded_rectangle([0, 0, logo_btn_size, logo_btn_size], radius=15, fill=255)
        im.paste(logo_btn, (nav_x1 + 20, btn_y - logo_btn_size // 2), btn_mask)

    # CTA Metni
    font_cta = font_al(FONT_UI, 24, agirlik=700)
    draw.text((nav_x1 + 20 + logo_btn_size + 16, btn_y - 14), "Ezan Plus • Ücretsiz İndirin", font=font_cta, fill=METIN_ANA)

    # Store İkonları
    ps_size = 28
    ps_x = nav_x2 - 58
    ps_y = btn_y - ps_size // 2
    _play_store_vektor_ciz(draw, ps_x, ps_y, ps_size)

    try:
        font_apple = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
        bbox_ap = draw.textbbox((0, 0), "", font=font_apple)
        ap_w, ap_h = bbox_ap[2] - bbox_ap[0], bbox_ap[3] - bbox_ap[1]
        ap_y = btn_y - ap_h // 2 - bbox_ap[1]
        ap_x = ps_x - ap_w - 24
        draw.text((ap_x, ap_y), "", font=font_apple, fill="#000000")
    except Exception:
        pass

    return im, arapca_y_baslangic, 0, kart_ic_genislik


def arapca_kelimeleri_ayristir(metin: str) -> List[str]:
    """
    Arapça ayet metnini kelimelerine ayırır.
    Secavend işaretleri (ۚ ۖ ۗ ۘ ۙ ۛ ۜ ؕ ۞ ۩ ۝) telaffuz edilen birer kelime veya harf
    olmayıp mushaf içi kıraat/durak sembolleridir. Video karaoke metninde ve kelime
    senkronunda bağımsız uçuşan garip harfler oluşturmaması için listeden elenir.
    """
    secavendler = {"ۚ", "ۖ", "ۗ", "ۘ", "ۙ", "ۛ", "ۜ", "ؕ", "۞", "۩", "۝"}
    ham = [w.strip() for w in metin.split() if w.strip()]
    sonuc: List[str] = []
    for w in ham:
        if w in secavendler:
            continue
        # Kelime sonuna yapışık durak işareti varsa temizle
        w_clean = re.sub(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9]+$", "", w).strip()
        if w_clean:
            sonuc.append(w_clean)
    return sonuc


def turkce_okunus_hizala(tr_list: List[str], ar_list: List[str]) -> List[str]:
    """
    Türkçe Latin okunuşu ile Arapça kelimeleri 1:1 hizalar.
    Arapça'da bitişik yazılan 've' (و), 'fe' (ف), 'bi' (ب), 'li' (ل), 'ke' (ك)
    bağlaçlarını ve harf-i tariflerini Türkçe'deki sonraki kelimeyle birleştirerek
    Arapça kelime sayısına tam eşitler.
    Tire ile bağlanmış bileşikleri açar, hiçbir kelimenin boş kalmamasını ve
    karaoke takibinin vaktinden önce bitmemesini garanti eder.
    """
    if not ar_list:
        return []
    if not tr_list:
        return [""] * len(ar_list)

    # 1. Anlamlı tireli bileşikleri aç (Örn: 'entes-semîul' -> ['entes', 'semîul'])
    expanded = []
    for w in tr_list:
        if "-" in w and not w.startswith("-") and not w.endswith("-"):
            parts = [p for p in w.split("-") if len(p.strip()) >= 2]
            if len(parts) > 1:
                expanded.extend(parts)
            else:
                expanded.append(w)
        else:
            expanded.append(w)

    baglaclar = {"ve", "fe", "bi", "li", "vel", "fel", "bil", "lil", "ke", "kel"}
    num_ar = len(ar_list)

    # 2. Bağlaç birleştirme geçişi
    merged: List[str] = []
    i = 0
    while i < len(expanded):
        w = expanded[i]
        clean_w = w.lower().strip("',.:;!?\"”’")
        if clean_w in baglaclar and i + 1 < len(expanded):
            rem_tokens_if_merged = len(expanded) - (i + 2)
            rem_ar = num_ar - (len(merged) + 1)
            ar_target = ar_list[min(len(merged), num_ar - 1)]
            if ar_target.startswith(("و", "ف", "ب", "ل", "ك")) and rem_tokens_if_merged >= rem_ar:
                merged.append(f"{w} {expanded[i+1]}")
                i += 2
                continue

        merged.append(w)
        i += 1

    # 3. Sayıyı tam num_ar'a eşitle (Eksikse boşluklu olanları böl, fazlaysa son kelimeye ekle)
    if len(merged) < num_ar:
        while len(merged) < num_ar:
            idx_space = -1
            max_len = 0
            for idx, tok in enumerate(merged):
                if " " in tok and len(tok) > max_len:
                    max_len = len(tok)
                    idx_space = idx
            if idx_space >= 0:
                parts = merged[idx_space].split(" ", 1)
                merged[idx_space] = parts[0]
                merged.insert(idx_space + 1, parts[1])
            else:
                merged.append(merged[-1] if merged else "")
    elif len(merged) > num_ar:
        excess = " ".join(merged[num_ar - 1 :])
        merged = merged[: num_ar - 1] + [excess]

    return merged


def kelime_zamanlarini_hizala(
    kelime_zamanlari: Optional[List[Tuple[float, float]]],
    toplam_kelime: int,
    toplam_sure: float,
) -> List[Tuple[float, float]]:
    """
    Kelimelerin zaman damgalarını toplam_kelime sayısına 1:1 milisaniye
    hassasiyetinde eşitler ve doğrular.
    Eğer zaman damgaları yoksa veya eksikse, toplam ses süresine göre
    akıllı ve doğal bir akış üretir.
    """
    if toplam_kelime <= 0:
        return []

    if not kelime_zamanlari or len(kelime_zamanlari) == 0:
        pad_baslangic = min(0.6, toplam_sure * 0.05)
        pad_bitis = min(1.0, toplam_sure * 0.08)
        kullanilabilir_sure = max(1.0, toplam_sure - pad_baslangic - pad_bitis)
        kelime_suresi = kullanilabilir_sure / toplam_kelime
        hizali = []
        for i in range(toplam_kelime):
            s = pad_baslangic + i * kelime_suresi
            e = s + kelime_suresi
            hizali.append((round(s, 3), round(e, 3)))
        return hizali

    n_src = len(kelime_zamanlari)
    if n_src == toplam_kelime:
        return kelime_zamanlari

    # Boyut uyuşmazlığı varsa (örn. 40 segmente karşılık 39 kelime veya tersi):
    # Zaman çizelgesini toplam_kelime'ye oranlayarak kesintisiz enterpolasyon yap
    src_sinirlar = [kelime_zamanlari[0][0]]
    for s, e in kelime_zamanlari:
        src_sinirlar.append(e)

    hizali = []
    for i in range(toplam_kelime):
        idx_s = i * (n_src / toplam_kelime)
        idx_e = (i + 1) * (n_src / toplam_kelime)
        s_int = int(idx_s)
        s_frac = idx_s - s_int
        if s_int + 1 < len(src_sinirlar):
            t_s = src_sinirlar[s_int] + s_frac * (src_sinirlar[s_int + 1] - src_sinirlar[s_int])
        else:
            t_s = src_sinirlar[-1]

        e_int = int(idx_e)
        e_frac = idx_e - e_int
        if e_int + 1 < len(src_sinirlar):
            t_e = src_sinirlar[e_int] + e_frac * (src_sinirlar[e_int + 1] - src_sinirlar[e_int])
        else:
            t_e = src_sinirlar[-1]

        t_e = max(t_s + 0.1, t_e)
        hizali.append((round(t_s, 3), round(t_e, 3)))

    return hizali



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


def akilli_sayfa_araliklari(
    ar_kelimeler: List[str],
    raw_ar: str,
    zamanlar: Optional[List[Tuple[float, float]]],
    sayfa_sayisi: int,
) -> List[Tuple[int, int]]:
    """
    Uzun ayetlerde sayfa aralıklarını rastgele kelime sayısına göre değil;
    Kur'an'daki tescilli secavend duraklarına (ۚ ۖ ۗ ۘ ۙ ۛ ۜ ؕ ۞ ۩ ۝) ve
    kıraat nefes duraklama sürelerine göre en doğal geçiş anlarından böler.
    """
    N = len(ar_kelimeler)
    if sayfa_sayisi <= 1 or N <= 1:
        return [(0, N)]

    secavendler = {"ۚ", "ۖ", "ۗ", "ۘ", "ۙ", "ۛ", "ۜ", "ؕ", "۞", "۩", "۝"}
    raw_tokens = raw_ar.split()
    secavend_after = {}
    c_i = 0
    for tok in raw_tokens:
        if tok in secavendler:
            if c_i > 0:
                secavend_after[c_i - 1] = tok
        else:
            c_i += 1

    split_points = []
    for k in range(1, sayfa_sayisi):
        target = int(round(k * (N / sayfa_sayisi)))
        best_w = target - 1
        best_score = -9999.0

        min_w = max(2, target - 5)
        max_w = min(N - 2, target + 5)

        for w in range(min_w, max_w + 1):
            score = 0.0
            # 1. Secavend puanı
            if w in secavend_after:
                sec = secavend_after[w]
                if sec in {"ۗ", "ۚ", "ۙ", "ۖ"}:
                    score += 160.0
                elif sec == "ۘ":  # Lâ durağında durma
                    score -= 50.0
                else:
                    score += 90.0

            # 2. Nefes duraklama süresi puanı
            if zamanlar and w + 1 < len(zamanlar):
                pause = zamanlar[w + 1][0] - zamanlar[w][1]
                if pause > 0.3:
                    score += min(120.0, pause * 65.0)

            # 3. İdeal merkezden sapma cezası
            score -= 3.5 * abs(w - (target - 1))

            if score > best_score:
                best_score = score
                best_w = w

        split_points.append(best_w + 1)

    ranges = []
    cur = 0
    for sp in split_points:
        ranges.append((cur, sp))
        cur = sp
    ranges.append((cur, N))
    return ranges


def _meal_parcala(
    meal_metin: str,
    parca_sayisi: int,
    split_ratios: Optional[List[float]] = None,
) -> List[str]:
    """
    Türkçe meali anlam, cümle ve dua bütünlüğünü bozmadan,
    asla **bold** vurgu bloklarının veya doğrudan duaların ortasından kesmeden
    parça sayısına böler. Arapça sayfa oranlarıyla (split_ratios) 1:1 uyumlu çalışır.
    """
    if parca_sayisi <= 1:
        return [meal_metin.strip()]

    metin = meal_metin.strip()
    L = len(metin)

    # 1. Bold (**...**) alanlarını tespit et — Bu alanların içi KESİNLİKLE bölünemez
    bold_spans = [m.span() for m in re.finditer(r"\*\*.*?\*\*", metin)]

    def is_inside_bold(pos: int) -> bool:
        for s, e in bold_spans:
            if s <= pos < e:
                return True
        return False

    # 2. Aday noktalama işaretlerini öncelik katmanlarına ayır
    tier1 = []  # Cümle sonları [. ! ? \n]
    tier2 = []  # Diyalog / doğrudan dua / iki nokta / noktalı virgül / tire [: ; —]
    tier3 = []  # Yan cümle virgülleri [,]

    for m in re.finditer(r"([.!?\n])\s+", metin):
        if not is_inside_bold(m.start()):
            tier1.append(m.end())

    for m in re.finditer(r"([;:])\s+|(\s+—\s+)", metin):
        if not is_inside_bold(m.start()):
            tier2.append(m.end())

    for m in re.finditer(r"([,])\s+", metin):
        if not is_inside_bold(m.start()):
            tier3.append(m.end())

    if not split_ratios:
        split_ratios = [k / parca_sayisi for k in range(1, parca_sayisi)]

    target_positions = [int(round(r * L)) for r in split_ratios]

    chosen_splits = []
    last_split = 0
    for t_pos in target_positions:
        all_candidates = []
        for p in tier1:
            if p > last_split + 20 and p < L - 20:
                all_candidates.append((p, 1, abs(p - t_pos)))
        for p in tier2:
            if p > last_split + 20 and p < L - 20:
                all_candidates.append((p, 2, abs(p - t_pos)))
        for p in tier3:
            if p > last_split + 20 and p < L - 20:
                all_candidates.append((p, 3, abs(p - t_pos)))

        if not all_candidates:
            spaces = [
                m.end()
                for m in re.finditer(r"\s+", metin)
                if not is_inside_bold(m.start())
                and m.end() > last_split + 15
                and m.end() < L - 15
            ]
            if spaces:
                best_candidate = min(spaces, key=lambda p: abs(p - t_pos))
            else:
                best_candidate = t_pos
        else:
            def _puanla(c):
                p, tier, dist = c
                tier_penalty = {1: 0, 2: 25, 3: 45}[tier]
                return dist + tier_penalty

            best = min(all_candidates, key=_puanla)
            best_candidate = best[0]

        chosen_splits.append(best_candidate)
        last_split = best_candidate

    parcalar = []
    cur = 0
    for sp in chosen_splits:
        p_str = metin[cur:sp].strip()
        p_str = re.sub(r"[,;:]$", "", p_str).strip()
        if p_str.count("**") % 2 != 0:
            p_str = p_str + "**"
        parcalar.append(p_str)
        cur = sp

    son_parca = metin[cur:].strip()
    if son_parca.count("**") % 2 != 0:
        son_parca = "**" + son_parca
    parcalar.append(son_parca)

    return parcalar


def _tefekkur_yukseklik_hesapla(
    draw: ImageDraw.ImageDraw,
    tef_text: str,
    max_w: int,
    font_norm: ImageFont.FreeTypeFont,
    font_bold: ImageFont.FreeTypeFont,
    line_height: int = 34,
) -> int:
    """Tefekkür bloğunun toplam piksel yüksekliğini (ayraç çizgisinden en alta) hesaplar."""
    formatted = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", tef_text)
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
            w_px = draw.textlength(w, font=f)
            words_data.append((w, f, w_px))

    lines_count = 0
    curr_w = 0
    for w_str, f, w_px in words_data:
        needed = w_px if curr_w == 0 else curr_w + space_w + w_px
        if needed <= max_w:
            curr_w = needed
        else:
            lines_count += 1
            curr_w = w_px
    if curr_w > 0:
        lines_count += 1

    lines_count = max(1, lines_count)
    return 56 + lines_count * line_height


class _SayfaVerisi:
    """
    Reels videosundaki tek bir sayfanın mizanpaj, font, slot ve taban görselini yönetir.
    """
    @staticmethod
    def uygun_pt_bul(page_ar: List[str], max_text_w: int = 840) -> int:
        """Belirtilen kelime grubu için en heybetli ve taşmayan Arapça puntoyu belirler."""
        n_kelime = len(page_ar)
        if n_kelime <= 4:
            start_pt = 138
        elif n_kelime <= 7:
            start_pt = 114
        elif n_kelime <= 10:
            start_pt = 94
        else:
            start_pt = 76

        im_temp = Image.new("RGB", (100, 100))
        d_temp = ImageDraw.Draw(im_temp)

        # 1. Heybetli Tek Satır Tercihi: Eğer 110pt ve üzerinde tek satıra rahatça sığıyorsa doğrudan tek satır yap
        for pt in range(start_pt, 108, -2):
            font = font_al(FONT_ARAPCA_NORMAL, pt)
            font_bold = font_al(FONT_ARAPCA_BOLD, pt)
            w_sizes = [
                max(
                    d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[0],
                    d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[0],
                )
                for w in page_ar
            ]
            if sum(w_sizes) + (n_kelime - 1) * 20 <= max_text_w:
                return pt

        # 2. Çoklu Satır Arama: 2 ve 3 satır dengeli mizanpaj
        # 2 ve üzeri satıra bölünen âyetlerde dikey taşmayı önlemek için tavan 114pt'dir
        multiline_start_pt = min(114, start_pt)
        for max_l in [2, 3]:
            for pt in range(multiline_start_pt, 48, -2):
                font = font_al(FONT_ARAPCA_NORMAL, pt)
                font_bold = font_al(FONT_ARAPCA_BOLD, pt)
                w_sizes = [
                    max(
                        d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[0],
                        d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[0],
                    )
                    for w in page_ar
                ]
                lines = []
                cur_line = []
                cur_w = 0
                fits = True
                min_gap = 18
                for idx, w_px in enumerate(w_sizes):
                    needed = w_px + (min_gap if cur_line else 0)
                    if cur_w + needed <= max_text_w:
                        cur_line.append(idx)
                        cur_w += needed
                    else:
                        if not cur_line:
                            fits = False
                            break
                        lines.append(cur_line)
                        cur_line = [idx]
                        cur_w = w_px
                if cur_line:
                    lines.append(cur_line)
                if fits and len(lines) <= max_l:
                    return pt
        return 56

    @staticmethod
    def satirlari_dengeli_bol(page_ar: List[str], pt: int, max_text_w: int = 840) -> List[List[int]]:
        """Arapça kelimeleri satırlara dengeli dağıtır (satırlar arası asimetriyi ve sıkışıklığı önler)."""
        im_temp = Image.new("RGB", (100, 100))
        d_temp = ImageDraw.Draw(im_temp)
        font = font_al(FONT_ARAPCA_NORMAL, pt)
        font_bold = font_al(FONT_ARAPCA_BOLD, pt)
        w_sizes = [
            max(
                d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font)[0],
                d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[2] - d_temp.textbbox((0, 0), arapca_hazirla(w), font=font_bold)[0],
            )
            for w in page_ar
        ]
        n = len(page_ar)
        if n <= 1:
            return [[0]]

        # 1. Tek bir satıra rahatça sığıyorsa doğrudan 1 satır yap (Kısa âyetler için heybetli tek satır)
        toplam_tek_w = sum(w_sizes) + (n - 1) * 18
        if toplam_tek_w <= max_text_w:
            return [list(range(n))]

        for n_lines in [2, 3]:
            best_diff = 999999
            best_part = None
            if n_lines == 2:
                for split_idx in range(1, n):
                    l0 = w_sizes[:split_idx]
                    l1 = w_sizes[split_idx:]
                    w0 = sum(l0) + (len(l0) - 1) * 18
                    w1 = sum(l1) + (len(l1) - 1) * 18
                    if w0 <= max_text_w and w1 <= max_text_w:
                        diff = abs(w0 - w1)
                        if diff < best_diff:
                            best_diff = diff
                            best_part = [list(range(split_idx)), list(range(split_idx, n))]
                if best_part:
                    return best_part
            elif n_lines == 3:
                for i in range(1, n - 1):
                    for j in range(i + 1, n):
                        l0 = w_sizes[:i]
                        l1 = w_sizes[i:j]
                        l2 = w_sizes[j:]
                        w0 = sum(l0) + (len(l0) - 1) * 18
                        w1 = sum(l1) + (len(l1) - 1) * 18
                        w2 = sum(l2) + (len(l2) - 1) * 18
                        if w0 <= max_text_w and w1 <= max_text_w and w2 <= max_text_w:
                            diff = max(w0, w1, w2) - min(w0, w1, w2)
                            if diff < best_diff:
                                best_diff = diff
                                best_part = [list(range(i)), list(range(i, j)), list(range(j, n))]
                if best_part:
                    return best_part

        # Fallback greedy
        lines = []
        cur_line = []
        cur_w = 0
        for idx, w_px in enumerate(w_sizes):
            needed = w_px + (18 if cur_line else 0)
            if cur_w + needed <= max_text_w:
                cur_line.append(idx)
                cur_w += needed
            else:
                lines.append(cur_line)
                cur_line = [idx]
                cur_w = w_px
        if cur_line:
            lines.append(cur_line)
        return lines

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
        pt_ar_override: Optional[int] = None,
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

        # Dinamik Orantılı Tipografi ve Mizanpaj Ölçekleme (Piksel Genişliği ve Satır Sınırı Analizi)
        # Kart: 54..1026 = 972px. MAX_TEXT_W = 840px seçilerek ferah nefes alanı ve asil büyük punto sağlanır.
        MAX_TEXT_W = 840

        if pt_ar_override is not None:
            chosen_pt = pt_ar_override
        else:
            chosen_pt = _SayfaVerisi.uygun_pt_bul(page_ar, MAX_TEXT_W)

        chosen_lines = _SayfaVerisi.satirlari_dengeli_bol(page_ar, chosen_pt, MAX_TEXT_W)

        self.pt_ar = chosen_pt
        self.pt_okunus = max(26, int(self.pt_ar * 0.36))
        self.ar_h = int(self.pt_ar * 1.44)
        self.tr_h = int(self.pt_okunus * 1.32)

        # 2. Türkçe Meal Ölçeği (Hero Element: Okunaklı, tok ve asil editoryal punto)
        temiz_meal = page_meal.strip("“”\"' ")
        meal_metinsiz = temiz_meal.replace("**", "")
        meal_len = len(meal_metinsiz)
        if meal_len < 45:
            self.pt_meal = 66
        elif meal_len < 80:
            self.pt_meal = 58
        elif meal_len < 130:
            self.pt_meal = 50
        elif meal_len < 185:
            self.pt_meal = 44
        else:
            self.pt_meal = 38
        self.meal_h = int(self.pt_meal * 1.36)

        # 3. Günün Hikmeti & Tefekkür Ölçeği
        tef_len = len(tef)
        self.pt_tef = 28 if tef_len < 120 else 24
        self.tef_line_h = int(self.pt_tef * 1.42)

        self.font_ar_norm = font_al(FONT_ARAPCA_NORMAL, self.pt_ar)
        self.font_ar_bold = font_al(FONT_ARAPCA_BOLD, self.pt_ar)
        self.font_okunus_norm = font_al(FONT_UI, self.pt_okunus, agirlik=500)
        self.font_okunus_bold = font_al(FONT_UI, self.pt_okunus, agirlik=800)
        self.font_meal_reg = font_al(FONT_BASLIK, self.pt_meal, agirlik=400)
        self.font_meal_bold = font_al(FONT_BASLIK, self.pt_meal, agirlik=700)
        self.font_meal = self.font_meal_reg
        self.font_tef_norm = font_al(FONT_GOVDE, self.pt_tef, agirlik=400)
        self.font_tef_bold = font_al(FONT_GOVDE, self.pt_tef, agirlik=700)
        self.font_tef_baslik = font_al(FONT_UI, max(22, int(self.pt_tef * 0.9)), agirlik=800)

        # 1. Taban görseli oluştur
        self.taban_img, self.ar_y_start, _, self.kart_ic_w = _statik_taban_ciz(
            sure_ayet=page_title,
            video_baslik_satir1=s1,
            video_baslik_satir2=s2,
            tefekkur_notu=tef,
            hafiz_adi=hafiz_adi,
        )
        # Tek sayfalı kısa âyetlerde üst çizgiye çok yapışmaması için hafif nefes payı
        if sayfa_sayisi == 1 and len(page_ar) <= 4:
            self.ar_y_start += 24

        draw_t = ImageDraw.Draw(self.taban_img)

        # 2. Satır grupları oluştur ve slotları milimetrik hesapla
        self.ar_satir_bilgileri = []
        self.tr_satir_bilgileri = []

        for line_indices in chosen_lines:
            sub_ar = [page_ar[i] for i in line_indices]
            sub_tr = [page_tr[i] if i < len(page_tr) else "" for i in line_indices]
            g_start = start_w + line_indices[0]

            # Arapça kelime genişlikleri
            harf_w_list = [
                draw_t.textbbox((0, 0), arapca_hazirla(w), font=self.font_ar_norm)[2]
                - draw_t.textbbox((0, 0), arapca_hazirla(w), font=self.font_ar_norm)[0]
                for w in sub_ar
            ]
            toplam_harf_w = sum(harf_w_list)
            gap = max(16, (MAX_TEXT_W - toplam_harf_w) // (len(sub_ar) - 1)) if len(sub_ar) > 1 else 28
            gap = min(gap, 42)
            toplam_w = toplam_harf_w + (len(sub_ar) - 1) * gap

            kelime_yuvalari = []
            cur_x = (GENISLIK_9_16 + toplam_w) // 2
            for j, w in enumerate(sub_ar):
                width = harf_w_list[j]
                cur_x -= width
                slot_mid_x = cur_x + width // 2
                kelime_yuvalari.append((w, g_start + j, slot_mid_x))
                cur_x -= gap
            self.ar_satir_bilgileri.append(kelime_yuvalari)

            # Türkçe Latin okunuş slotları
            tr_w_list = [
                draw_t.textbbox((0, 0), w, font=self.font_okunus_norm)[2]
                - draw_t.textbbox((0, 0), w, font=self.font_okunus_norm)[0]
                for w in sub_tr
            ]
            toplam_tr_w = sum(tr_w_list)
            gap_tr = max(10, (MAX_TEXT_W - toplam_tr_w) // (len(sub_tr) - 1)) if len(sub_tr) > 1 else 16
            gap_tr = min(gap_tr, 30)
            toplam_tr_full = toplam_tr_w + (len(sub_tr) - 1) * gap_tr

            cur_tr_x = (GENISLIK_9_16 - toplam_tr_full) // 2
            tr_yuvalari = []
            for j, w_str in enumerate(sub_tr):
                width = tr_w_list[j]
                slot_mid_x = cur_tr_x + width // 2
                tr_yuvalari.append((w_str, g_start + j, slot_mid_x))
                cur_tr_x += width + gap_tr
            self.tr_satir_bilgileri.append(tr_yuvalari)

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

        # Arapça satırların Y koordinatlarını dinamik bounding box ile hesapla
        # Her satırın gerçek piksel mürekkep sınırları (harfler ve alt/üst harekeler) ölçülür.
        # İki satır arasında MUTLAKA en az MIN_VERTICAL_GAP (28px) net boşluk bırakılır.
        # Böylece alt satırın şedde/fethaları ile üst satırın kesra/tenvinleri ASLA çakışmaz!
        self.ar_satir_y_list = []
        MIN_VERTICAL_GAP = 28
        prev_ink_bottom = self.ar_y_start

        for s_idx, satir in enumerate(self.ar_satir_bilgileri):
            line_top_ink = min(draw_t.textbbox((0, 0), self.ar_red_cache[w_idx][3], font=self.font_ar_bold)[1] for _, w_idx, _ in satir)
            line_bottom_ink = max(draw_t.textbbox((0, 0), self.ar_red_cache[w_idx][3], font=self.font_ar_bold)[3] for _, w_idx, _ in satir)

            if s_idx == 0:
                line_y = self.ar_y_start
            else:
                line_y = prev_ink_bottom + MIN_VERTICAL_GAP - line_top_ink

            self.ar_satir_y_list.append(line_y)
            prev_ink_bottom = line_y + line_bottom_ink

        # 3. Dinamik Flex Mizanpaj (Üste dayalı tilavet, alta dayalı tefekkür, kalan alanı esnek paylaşan meal)
        # A) ALTA DAYALI GÜNÜN HİKMETİ & TEFEKKÜRÜ
        font_tef_baslik = self.font_tef_baslik
        font_tef_norm = self.font_tef_norm
        font_tef_bold = self.font_tef_bold

        tef_h = _tefekkur_yukseklik_hesapla(
            draw_t, tef, self.kart_ic_w - 60, font_tef_norm, font_tef_bold, line_height=self.tef_line_h
        )
        y_bottom_safe = 1566
        ay_y = y_bottom_safe - tef_h - 16

        # B) LATİN OKUNUŞ: TİLAVET BÜTÜNLÜĞÜ İÇİN DOĞRUDAN ARAPÇA METNİN HEMEN ALTINA YERLEŞTİRİLİR
        # (Arapça ile okunuş arasında kopukluk / devasa boşluk kalmaması sağlanır)
        gap_ar_tr = max(24, int(self.pt_ar * 0.24))
        self.tr_y_start = prev_ink_bottom + gap_ar_tr
        okunus_blok_h = len(self.tr_satir_bilgileri) * self.tr_h
        tr_bottom = self.tr_y_start + okunus_blok_h

        # C) ORTA ALAN: OKUNUŞ BİTİŞİ İLE TEFEKKÜR ARASINDA ALTIN AYRAÇ VE MEAL DENGELİ ORTALANIR
        temiz_meal = page_meal.strip("“”\"' ")
        meal_metin = f"“{temiz_meal}”"
        meal_tokens = parse_markdown_bold(meal_metin)
        meal_wrapped_lines, space_w = wrap_mixed_tokens(
            meal_tokens, self.font_meal_reg, self.font_meal_bold, self.kart_ic_w - 60, draw_t
        )

        gap_ayrac_meal = max(28, int(self.pt_meal * 0.50))
        meal_blok_h = len(meal_wrapped_lines) * self.meal_h

        kalan_orta = ay_y - tr_bottom
        self.net_serbest_meal = kalan_orta - (meal_blok_h + gap_ayrac_meal)

        # Dinamik Auto-Fit: Kalan alan daraldığında meal puntosunu kademeli küçülterek çakışmayı %100 önle
        while self.net_serbest_meal < 20 and self.pt_meal > 32:
            self.pt_meal -= 2
            self.meal_h = int(self.pt_meal * 1.34)
            self.font_meal_reg = font_al(FONT_BASLIK, self.pt_meal, agirlik=400)
            self.font_meal_bold = font_al(FONT_BASLIK, self.pt_meal, agirlik=700)
            gap_ayrac_meal = max(22, int(self.pt_meal * 0.46))
            meal_wrapped_lines, space_w = wrap_mixed_tokens(
                meal_tokens, self.font_meal_reg, self.font_meal_bold, self.kart_ic_w - 60, draw_t
            )
            meal_blok_h = len(meal_wrapped_lines) * self.meal_h
            self.net_serbest_meal = kalan_orta - (meal_blok_h + gap_ayrac_meal)

        serbest_meal = max(16, self.net_serbest_meal)
        self.serbest_meal = serbest_meal
        ayrac_y = tr_bottom + int(serbest_meal * 0.40)

        # Tırnak filigranı & Altın ayraç
        font_giant_quote = font_al(FONT_BASLIK, 150, agirlik=700)
        draw_t.text((54 + 40, ayrac_y + 6), "“", font=font_giant_quote, fill="#F6ECDA")

        ayrac_w = getattr(self, "ayrac_w", 220)
        draw_t.line([(GENISLIK_9_16 // 2 - ayrac_w // 2, ayrac_y), (GENISLIK_9_16 // 2 + ayrac_w // 2, ayrac_y)], fill=ALTIN, width=2)
        draw_t.ellipse([GENISLIK_9_16 // 2 - 6, ayrac_y - 5, GENISLIK_9_16 // 2 + 6, ayrac_y + 7], fill=ALTIN)

        # Meal Metni Çizimi (Ayracın hemen altından başlar - Mixed Bold)
        my = ayrac_y + gap_ayrac_meal
        for satir_tokens, line_w in meal_wrapped_lines:
            cur_x = (GENISLIK_9_16 - line_w) // 2
            for tok_text, is_bold, word_w in satir_tokens:
                f_tok = self.font_meal_bold if is_bold else self.font_meal_reg
                f_color = "#111827" if is_bold else METIN_ANA
                draw_t.text((cur_x, my), tok_text, font=f_tok, fill=f_color)
                cur_x += word_w + space_w
            my += self.meal_h

        # D) Günün Hikmeti & Tefekkür Çizimi (Alta dayalı sabit)
        draw_t.line([(GENISLIK_9_16 // 2 - 100, ay_y), (GENISLIK_9_16 // 2 + 100, ay_y)], fill="#E5DAC3", width=2)
        draw_t.ellipse([GENISLIK_9_16 // 2 - 5, ay_y - 4, GENISLIK_9_16 // 2 + 5, ay_y + 6], fill=ALTIN)

        txt_b = "GÜNÜN HİKMETİ & TEFEKKÜRÜ"
        bw = draw_t.textlength(txt_b, font=font_tef_baslik)
        bx = (GENISLIK_9_16 - bw) // 2
        draw_t.ellipse([bx - 18, ay_y + 28, bx - 10, ay_y + 36], fill=ALTIN)
        draw_t.text((bx, ay_y + 20), txt_b, font=font_tef_baslik, fill="#B45309")

        zengin_metin_ciz_baseline(
            draw_t,
            tef,
            GENISLIK_9_16 // 2,
            ay_y + 64,
            self.kart_ic_w - 60,
            font_tef_norm,
            font_tef_bold,
            fill_norm="#475569",
            fill_bold="#182230",
            line_height=self.tef_line_h,
        )

    def kare_ciz(self, t_sec: float, aktif_idx: int, aktif_progress: float) -> Image.Image:
        """Sayfanın belirtilen andaki karesini döndürür."""
        kare = self.taban_img.copy()
        draw_k = ImageDraw.Draw(kare)

        # Arapça Kelimeler (Sağdan sola loading akışı)
        for s_idx, satir in enumerate(self.ar_satir_bilgileri):
            cur_y = self.ar_satir_y_list[s_idx]
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

        # Türkçe Okunuş Kelimeler (Ayracın hemen üstünde, self.tr_y_start'tan başlar)
        cur_y = self.tr_y_start
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
    pt_ar_override: Optional[int] = None,
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
    kelime_zamanlari = kelime_zamanlarini_hizala(kelime_zamanlari, toplam_kelime, toplam_sure)

    # 2. Sayfa Sayısını ve Aralıkları Belirle (Akıllı Kıraat & Çoklu Sayfa Motoru)
    # 14 kelimeye kadar olan âyetler (Bakara 127 gibi) tek sayfada ferahça ve kesintisiz sunulur;
    # 15 kelime ve üzeri uzun âyetlerde metin secavend duraklarına ve hafızın nefes
    # aralıklarına göre anlam bütünlüğü korunarak 2-3 sayfaya bölünür.
    if toplam_kelime <= 14:
        sayfa_sayisi = 1
    elif toplam_kelime <= 28:
        sayfa_sayisi = 2
    else:
        sayfa_sayisi = math.ceil(toplam_kelime / 14)

    sayfa_araliklari = akilli_sayfa_araliklari(ar_kelimeler, ar_str, kelime_zamanlari, sayfa_sayisi)
    split_ratios = [w_e / max(1, toplam_kelime) for _, w_e in sayfa_araliklari[:-1]]
    meal_parcalari = _meal_parcala(turkce_meal, sayfa_sayisi, split_ratios=split_ratios)

    # 3. Sayfa Verilerini Hazırla (Tüm sayfalar için birleşik Arapça punto ile tutarlı boyut)
    page_ar_list = [ar_kelimeler[w_s:w_e] for w_s, w_e in sayfa_araliklari]
    uygun_ptler = [_SayfaVerisi.uygun_pt_bul(words, max_text_w=840) for words in page_ar_list]
    if pt_ar_override:
        birlesik_pt = pt_ar_override
    else:
        birlesik_pt = min(uygun_ptler) if uygun_ptler else 76

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
            pt_ar_override=birlesik_pt,
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

            # Nefes payı analizi: Geçişi iki sayfa arasındaki duraklama anına denk getir
            pause = t_next_start - t_p_end
            if pause >= TRANS_DURATION:
                # Geniş nefes aralığında geçişi duraklamanın ortasına yerleştir
                t_trans_s = t_p_end + (pause - TRANS_DURATION) / 2.0
                t_trans_e = t_trans_s + TRANS_DURATION
            else:
                # Kısa veya bitişik okumada iki kelimenin arayüzünü baz al
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
            t_eval = t_sec  # Tam 1:1 mikrosaniye ses-görüntü senkronu

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
                    # Zaman bazlı aktif sayfa seçimi (ASLA aktif_idx kelime sayacına bağlanamaz!)
                    active_p = 0
                    for t_s, t_e, p_from, p_to in gecisler:
                        if t_sec < t_s:
                            active_p = p_from
                            break
                        else:
                            active_p = p_to
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
