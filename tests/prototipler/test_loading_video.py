import math
import subprocess
from pathlib import Path
from typing import List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
import imageio_ffmpeg
from src.ayar import KOK_DIZIN
from src.sablon_ciz import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_BASLIK,
    FONT_UI,
)
from src.ses_getir import ses_sure_hesapla, ayet_kelime_zamanlari_getir
from src.video_motoru import _statik_taban_ciz, arapca_kelimeleri_ayristir, turkce_okunus_hizala

FONTLAR = KOK_DIZIN / "assets" / "fonts"
FONT_ARAPCA_NORMAL = FONTLAR / "amiri-400-arabic.ttf"
FONT_ARAPCA_BOLD = FONTLAR / "amiri-700-arabic.ttf"

GENISLIK_9_16 = 1080
YUKSEKLIK_9_16 = 1920
FPS = 30

KIRMIZI = "#C0392B"
ISLAM_YESILI = "#0D5C3A"
CANLI_YESIL = "#059669"
ALTIN = "#D97706"
METIN_ANA = "#182230"
METIN_MUTED = "#64748B"
METIN_LIGHT = "#94A3B8"
YESIL_INACTIVE = "#2E7D56"
GRI_INACTIVE = "#94A3B8"

sure_no = 29
ayet_no = 64
sure_ayet = "Ankebût Sûresi • 64. Âyet"
turkce_meal = "Bu dünya hayatı sadece bir eğlence ve oyundan ibarettir. Ahiret yurdu ise işte asıl hayat odur. Keşke bilselerdi!"
arapca_metin = "وَمَا هَٰذِهِ الْحَيَاةُ الدُّنْيَا إِلَّا لَهْوٌ وَلَعِبٌ ۚ وَإِنَّ الدَّارَ الْآخِرَةَ لَهِيَ الْحَيَوَANُ ۚ لَوْ كَانُوا يَعْلَمُونَ"
arapca_okunus = "Ve mâ hâzihil hayâtud dunyâ illâ lehvun ve le'ıb(un), ve inned dâral âhirete lehiyel hayavân(u), lev kânû ya'lemûn(e)."
video_b1 = "Dünya Hayatı Sadece"
video_b2 = "Bir Eğlence ve Oyundur"
tefekkur = "Gelip geçici telaşlar ve kederler içinde boğulurken, asıl durağımızın ahiret olduğunu sık sık unutuyoruz. Bu ayet, gözümüzde büyüttüğümüz dünya dertlerinin bir sahneden ibaret olduğunu hatırlatarak kalbimize sonsuz bir ferahlık ve teslimiyet sunuyor."

ses_yolu = KOK_DIZIN / "assets" / "audio" / "029064.mp3"
kelime_zamanlari = ayet_kelime_zamanlari_getir(sure_no, ayet_no)

toplam_sure = ses_sure_hesapla(ses_yolu)
toplam_kare = int(math.ceil(toplam_sure * FPS))
print(f"Loading animasyonlu video render ediliyor: {toplam_sure:.2f}s ({toplam_kare} kare)")

taban_img, ar_y_start, tef_y1, kart_ic_w = _statik_taban_ciz(
    sure_ayet=sure_ayet,
    video_baslik_satir1=video_b1,
    video_baslik_satir2=video_b2,
    tefekkur_notu=tefekkur,
    hafiz_adi="Mişari Râşid el-Afâsî",
)

ar_kelimeler = arapca_kelimeleri_ayristir(arapca_metin)
tr_ham = [w.strip() for w in arapca_okunus.split() if w.strip()]
tr_kelimeler = turkce_okunus_hizala(tr_ham, ar_kelimeler)
toplam_kelime = len(ar_kelimeler)

pt_ar_norm = 78
pt_ar_bold = 82
pt_okunus_norm = 34
pt_okunus_bold = 36
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

# Ön Hesaplama: Arapça kelimelerin merkez X koordinatları
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

# Ön Hesaplama: Türkçe Okunuş kelimelerinin merkez X koordinatları
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

# Meal
meal_fmt = f"“{turkce_meal.strip()}”"
meal_satirlar = metin_satirla(meal_fmt, font_meal, kart_ic_w - 40, dummy_draw)
ayrac_y = ar_y_start + len(ar_gruplar) * ar_satir_h + 28 + len(tr_gruplar) * tr_satir_h + 36
draw_taban = ImageDraw.Draw(taban_img)
draw_taban.line([(GENISLIK_9_16 // 2 - 110, ayrac_y), (GENISLIK_9_16 // 2 + 110, ayrac_y)], fill=ALTIN, width=2)
draw_taban.ellipse([GENISLIK_9_16 // 2 - 6, ayrac_y - 5, GENISLIK_9_16 // 2 + 6, ayrac_y + 7], fill=ALTIN)

my = ayrac_y + 44
for s in meal_satirlar:
    bbox = draw_taban.textbbox((0, 0), s, font=font_meal)
    sw = bbox[2] - bbox[0]
    draw_taban.text(((GENISLIK_9_16 - sw) // 2, my), s, font=font_meal, fill=METIN_ANA)
    my += meal_satir_h

# Pre-render word bitmaps for loading fill
# Latin bitmaps
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

# Arabic bitmaps
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

cikti_video = KOK_DIZIN / "data" / "cikti" / "reels_29_64_v10_loading_efekti.mp4"
temp_video = KOK_DIZIN / "data" / "cikti" / "temp_reels_29_64_v10_loading.mp4"

writer = imageio.get_writer(
    str(temp_video),
    fps=FPS,
    codec="libx264",
    quality=9,
    pixelformat="yuv420p",
    macro_block_size=None,
)

bar_x1 = 64
bar_x2 = GENISLIK_9_16 - 64
bar_y = 1670
bar_w = bar_x2 - bar_x1

eq_x = (GENISLIK_9_16 - 54) - 40 - 290
eq_bar_x = eq_x - 34
eq_base_y = 380 + 30 + 20

try:
    for i in range(toplam_kare):
        ilerleme = (i + 1) / toplam_kare
        t_sec = i / FPS
        t_eval = t_sec + 0.24

        # Kelimelerin aktiflik durumu ve progress oranları
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
                    # Bu kelime henüz başlamadı
                    break
                else:
                    # Bu kelime bitti, sonrakine bak
                    aktif_idx = w_i
                    aktif_progress = 1.0

        kare = taban_img.copy()
        draw_k = ImageDraw.Draw(kare)

        # Equalizer
        for bar_idx in range(5):
            bh = 10 + int(14 * (0.5 + 0.5 * math.sin(t_sec * 8 + bar_idx * 1.3)))
            bx = eq_bar_x + bar_idx * 6
            by1 = eq_base_y - bh
            renk = CANLI_YESIL if bar_idx % 2 == 0 else ALTIN
            draw_k.rounded_rectangle([bx, by1, bx + 3, eq_base_y], radius=2, fill=renk)

        # Arapça Çizimi (Loading fill sağdan sola)
        cur_y = ar_y_start
        for satir in ar_satir_bilgileri:
            for w, w_idx, mid_x in satir:
                im_w, wt, ht, gw = ar_red_cache[w_idx]
                x_start = mid_x - wt // 2

                if w_idx == aktif_idx and aktif_progress < 1.0:
                    # 1. Taban yeşil
                    draw_k.text((x_start, cur_y - 2), gw, font=font_ar_bold, fill=YESIL_INACTIVE)
                    # 2. Sağdan sola loading crop
                    dolum_w = int(wt * aktif_progress)
                    if dolum_w > 0:
                        crop_x1 = max(0, im_w.width - dolum_w)
                        cropped = im_w.crop((crop_x1, 0, im_w.width, im_w.height))
                        kare.paste(cropped, (x_start + crop_x1, cur_y - 2), cropped)
                elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                    # Tamamen okunmuş kelime
                    draw_k.text((x_start, cur_y), gw, font=font_ar_norm, fill=ISLAM_YESILI)
                else:
                    # Henüz okunmamış
                    draw_k.text((x_start, cur_y), gw, font=font_ar_norm, fill=YESIL_INACTIVE)
            cur_y += ar_satir_h

        # Türkçe Okunuş Çizimi (Loading fill soldan sağa)
        cur_y += 28
        for satir in tr_satir_bilgileri:
            for w_str, w_idx, mid_x in satir:
                im_w, wt, ht = latin_red_cache[w_idx]
                x_start = mid_x - wt // 2

                if w_idx == aktif_idx and aktif_progress < 1.0:
                    # 1. Taban gri
                    draw_k.text((x_start, cur_y - 2), w_str, font=font_okunus_bold, fill=GRI_INACTIVE)
                    # 2. Soldan sağa loading crop
                    dolum_w = int(wt * aktif_progress)
                    if dolum_w > 0:
                        cropped = im_w.crop((0, 0, dolum_w, im_w.height))
                        kare.paste(cropped, (x_start, cur_y - 2), cropped)
                elif w_idx < aktif_idx or (w_idx == aktif_idx and aktif_progress >= 1.0):
                    # Tamamen okunmuş kelime
                    draw_k.text((x_start, cur_y), w_str, font=font_okunus_norm, fill=METIN_ANA)
                else:
                    # Henüz okunmamış
                    draw_k.text((x_start, cur_y), w_str, font=font_okunus_norm, fill=GRI_INACTIVE)
            cur_y += tr_satir_h

        # İlerleme çubuğu
        yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
        dolu_w = int(bar_w * ilerleme)
        if dolu_w > 6:
            yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
            draw_k.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

        frame_np = np.array(kare)
        writer.append_data(frame_np)

finally:
    writer.close()

exe = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [
    exe, "-y",
    "-i", str(temp_video),
    "-i", str(ses_yolu),
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    str(cikti_video),
]
subprocess.run(cmd, check=True)
if temp_video.exists():
    temp_video.unlink()

print(f"Loading animasyonlu video tamamlandı: {cikti_video}")
