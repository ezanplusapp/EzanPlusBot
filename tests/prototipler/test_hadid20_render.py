"""
test_hadid20_render.py — Hadîd 20 Çoklu Sayfa (Multi-Page) Reels Render Testi
"""

import math
import re
import time
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio
import imageio_ffmpeg

from src.ayar import KOK_DIZIN
from src.uretim.kart import (
    font_al,
    arapca_hazirla,
    metin_satirla,
    yuvarlak_kose_ciz,
    rozet_ciz,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
)
from src.uretim.ses import ayet_kelime_zamanlari_getir, ses_sure_hesapla
from src.uretim.video import (
    _statik_taban_ciz,
    zengin_metin_ciz_baseline,
    arapca_kelimeleri_ayristir,
    turkce_okunus_hizala,
    FONT_ARAPCA_NORMAL,
    FONT_ARAPCA_BOLD,
    GENISLIK_9_16,
    YUKSEKLIK_9_16,
    FPS,
    CANLI_YESIL,
    ISLAM_YESILI,
    YESIL_INACTIVE,
    KIRMIZI,
    ALTIN,
    METIN_ANA,
    METIN_LIGHT,
)

def _meal_parcala(meal_metin: str, parca_sayisi: int) -> List[str]:
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
        kelimeler = meal_metin.split()
        adim = math.ceil(len(kelimeler) / parca_sayisi)
        return [" ".join(kelimeler[i:i + adim]) for i in range(0, len(kelimeler), adim)]


class SayfaVerisi:
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
        toplam_sure: float,
        kelime_zamanlari: List[Tuple[float, float]],
    ):
        self.p_idx = p_idx
        self.start_w = start_w
        self.end_w = end_w
        self.page_ar = page_ar
        self.page_tr = page_tr
        self.page_meal = page_meal

        # Sayfa başlığı
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

        # Taban görseli oluştur
        self.taban_img, self.ar_y_start, _, self.kart_ic_w = _statik_taban_ciz(
            sure_ayet=page_title,
            video_baslik_satir1=s1,
            video_baslik_satir2=s2,
            tefekkur_notu=tef,
            hafiz_adi=hafiz_adi,
        )
        draw_t = ImageDraw.Draw(self.taban_img)

        # 1. Günün Hikmeti & Tefekkür (Çoklu sayfada sabit koordinat)
        ay_y = 1390
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

        # Arapça kelime slotları
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

    def kare_ciz(self, t_sec: float, aktif_idx: int, aktif_progress: float) -> Image.Image:
        kare = self.taban_img.copy()
        draw_k = ImageDraw.Draw(kare)

        # Arapça Kelimeler
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
        # Türkçe Okunuş Kelimeler
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


def main():
    ses_yolu = Path("assets/audio/057020.mp3")
    kelime_zamanlari = ayet_kelime_zamanlari_getir(57, 20)
    toplam_sure = ses_sure_hesapla(ses_yolu)
    toplam_kare = int(math.ceil(toplam_sure * FPS))

    ar_full = "اعْلَمُوا أَنَّمَا الْحَيَاةُ الدُّنْيَا لَعِبٌ وَلَهْوٌ وَزِينَةٌ وَتَفَاخُرٌ بَيْنَكُمْ وَتَكَاثُرٌ فِي الْأَمْوَالِ وَالْأَوْلَادِ كَمَثَلِ غَيْثٍ أَعْجَبَ الْكُفَّارَ نَبَاتُهُ ثُمَّ يَهِيجُ فَتَرَاهُ مُصْفَرًّا ثُمَّ يَكُونُ حُطَامًا وَفِي الْآخِرَةِ عَذَابٌ شَدِيدٌ وَمَغْفِرَةٌ مِّنَ اللَّهِ وَرِضْوَانٌ وَمَا الْحَيَاةُ الدُّنْيَا إِلَّا مَتَاعُ الْغُرُورِ"
    tr_full = "I’lemû ennemel hayâtud dunyâ la’ibun ve lehvun ve zînetun ve tefâhurun beynekum ve tekâsurun fîl emvâli vel evlâdi, ke meseli gaysin a’cebel kuffâre nebâtuhu summe yehîcu fe terâhu musferran summe yekûnu hutâmâ, ve fîl âhirati azâbun şedîdun ve magfiratun minallâhi ve ridvân, ve mel hayâtud dunyâ illâ metâul gurûr"
    tr_meal = "Bilin ki, dünya hayatı ancak bir oyun, bir eğlence, bir süs, aranızda bir övünüş ve mallarda, evlatlarda bir çoğalıştan ibarettir. Tıpkı bir yağmurun bitirdiği ekin gibidir ki, ekicilerin hoşuna gider, sonra kurur da sen onu sapsarı görürsün; sonra da çerçöp olur. Ahirette ise şiddetli bir azap, Allah'tan bir mağfiret ve rıza vardır. Dünya hayatı aldatıcı bir menfaatten başka bir şey değildir."
    tef = "Dünya hayatı geçici bir süs ve aldatıcı bir seraptır; asıl kalıcı olan ve ebedi huzuru getiren ise ahiret yurdudur."

    ar_kelimeler = arapca_kelimeleri_ayristir(ar_full)
    tr_ham = [w.strip() for w in tr_full.split() if w.strip()]
    tr_kelimeler = turkce_okunus_hizala(tr_ham, ar_kelimeler)
    toplam_kelime = len(ar_kelimeler)

    sayfa_sayisi = 2
    meal_parcalari = _meal_parcala(tr_meal, sayfa_sayisi)

    sayfa_araliklari = [(0, 20), (20, 39)]
    sayfalar = []
    for p_idx, (w_s, w_e) in enumerate(sayfa_araliklari):
        s = SayfaVerisi(
            p_idx=p_idx,
            sayfa_sayisi=sayfa_sayisi,
            start_w=w_s,
            end_w=w_e,
            page_ar=ar_kelimeler[w_s:w_e],
            page_tr=tr_kelimeler[w_s:w_e],
            page_meal=meal_parcalari[p_idx],
            sure_ayet="Hadîd Sûresi • 20. Âyet",
            s1="Dünya hayatı geçici bir oyundur,",
            s2="ebedi olan ise ahiret yurdudur.",
            tef=tef,
            hafiz_adi="Mişari Râşid el-Afâsî",
            toplam_sure=toplam_sure,
            kelime_zamanlari=kelime_zamanlari,
        )
        sayfalar.append(s)

    # Geçiş zamanları: sayfa 0 -> sayfa 1
    t_p0_end = kelime_zamanlari[19][1]
    t_p1_start = kelime_zamanlari[20][0]
    t_switch = (t_p0_end + t_p1_start) / 2.0
    TRANS_DURATION = 0.45
    t_trans_s = t_switch - TRANS_DURATION / 2.0
    t_trans_e = t_switch + TRANS_DURATION / 2.0

    print(f"Switch center: {t_switch:.2f}s (Trans: {t_trans_s:.2f}s .. {t_trans_e:.2f}s)")

    cikti_gecici = Path("data/cikti/temp_test_hadid20.mp4")
    cikti_final = Path("data/cikti/reels_hadid20_multipage.mp4")

    writer = imageio.get_writer(
        str(cikti_gecici),
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

    t_start_render = time.time()
    for i in range(toplam_kare):
        ilerleme = (i + 1) / toplam_kare
        t_sec = i / FPS
        t_eval = t_sec + 0.24

        aktif_idx = -1
        aktif_progress = 0.0

        if kelime_zamanlari and len(kelime_zamanlari) > 0:
            for w_i, (s_s, e_s) in enumerate(kelime_zamanlari):
                dur = max(0.01, e_s - s_s)
                if s_s <= t_eval < e_s:
                    aktif_idx = min(w_i, toplam_kelime - 1)
                    aktif_progress = min(1.0, max(0.0, (t_eval - s_s) / dur))
                    break
                elif t_eval < s_s:
                    break
                else:
                    aktif_idx = w_i
                    aktif_progress = 1.0

        # Sayfa seçimi & Crossfade
        if t_sec < t_trans_s:
            kare = sayfalar[0].kare_ciz(t_sec, aktif_idx, aktif_progress)
        elif t_sec > t_trans_e:
            kare = sayfalar[1].kare_ciz(t_sec, aktif_idx, aktif_progress)
        else:
            alpha = (t_sec - t_trans_s) / (t_trans_e - t_trans_s)
            kare_p0 = sayfalar[0].kare_ciz(t_sec, 20, 1.0)
            kare_p1 = sayfalar[1].kare_ciz(t_sec, 19, 0.0)
            kare = Image.blend(kare_p0, kare_p1, alpha)

        draw_k = ImageDraw.Draw(kare)

        # Equalizer
        for bar_idx in range(5):
            bh = 10 + int(14 * (0.5 + 0.5 * math.sin(t_sec * 8 + bar_idx * 1.3)))
            bx = eq_bar_x + bar_idx * 6
            by1 = eq_base_y - bh
            renk = CANLI_YESIL if bar_idx % 2 == 0 else ALTIN
            draw_k.rounded_rectangle([bx, by1, bx + 3, eq_base_y], radius=2, fill=renk)

        # Progress bar
        yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x2, bar_y + 10), radius=5, dolgu="#E2E8F0")
        dolu_w = int(bar_w * ilerleme)
        if dolu_w > 6:
            yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 10), radius=5, dolgu=KIRMIZI)
            draw_k.ellipse([bar_x1 + dolu_w - 9, bar_y - 4, bar_x1 + dolu_w + 9, bar_y + 14], fill=ALTIN, outline="#FFFFFF", width=3)

        if i == 0:
            kare.save(cikti_final.with_suffix(".png"), quality=95)

        writer.append_data(np.array(kare))
        if (i + 1) % 300 == 0 or i == toplam_kare - 1:
            print(f"Render: {i+1}/{toplam_kare} kare ({(i+1)/toplam_kare*100:.1f}%)")

    writer.close()
    render_time = time.time() - t_start_render
    print(f"Video render tamamlandı: {render_time:.2f} saniye")

    # Ses birleştir
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        exe, "-y",
        "-i", str(cikti_gecici),
        "-i", str(ses_yolu),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(cikti_final),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cikti_gecici.exists():
        cikti_gecici.unlink()

    print(f"Final video hazır: {cikti_final}")

if __name__ == "__main__":
    main()
