"""
src/uretim/multipage.py — Ezan Plus V20 Çok Sayfalı Dinamik Video Motoru

Özellikler:
- 1080x1920 (9:16) Tam Dikey 30 FPS MP4 video çıktısı.
- 100% Bold Ibarra Real Nova Serif tipografisi ile kelime kelime video karaoke dolumu.
- Çok sayfalı içeriklerde 0.45s sinematik erime (crossfade) geçişi.
- Sayfa geçişlerinden bağımsız, kesintisiz çalışan alt ilerleme çubuğu (Y=1858).
- Telifsiz arşiv Ney fon müziği miksajı (Hadis: Segâh, Dua: Ferahfezâ).
- Tescilli 1:1 Arapça & Türkçe sayfa bütünlüğü (Arapça eksik kalmaz).
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..ayar import KOK_DIZIN
from .kart import (
    FONT_ARAPCA,
    FONT_BASLIK,
    FONT_GOVDE,
    FONT_UI,
    HADIS_SABIT_PALET,
    DUA_SABIT_PALET,
    KETEN_CENTER,
    KETEN_OUTER,
    arapca_hazirla,
    arapca_glif_temizle,
    arapca_satirla,
    create_paper_background,
    draw_kart_header_bar,
    extract_dua_hands_mask,
    font_al,
    metin_satirla,
    wrap_mixed_tokens,
    yuvarlak_kose_ciz,
    _kelime_cta_butonu_ciz,
)
from .ses import ses_sure_hesapla, turkce_kisaltmalari_genislet

log = logging.getLogger(__name__)

FPS = 30
METIN_LIGHT = "#94A3B8"  # Bekleyen kelimeler: Zarif Açık Arduvaz Grisi
METIN_ANA = "#182230"    # Okunmuş kelimeler: Asil Antik Koyu Mürekkep
KIRMIZI_HADIS = "#C0392B"  # Hadis Aktif Kelime: Ezan Plus Canlı Kırmızısı
KEHRIBAR_DUA = "#B45309"   # Dua Aktif Kelime: Sıcak Asil Kehribar


def build_v20_base_layout(
    kategori: str = "hadis",
    format_tipi: str = "9:16",
    custom_meal: Optional[str] = None,
    custom_ar: Optional[str] = None,
    custom_ok: Optional[str] = None,
    custom_tac: Optional[str] = None,
    custom_tef: Optional[str] = None,
    custom_kaynak: Optional[str] = None,
) -> Dict[str, Any]:
    """
    V20 Parşömen Mizanpajı:
    - Keten zemin bandı ve yumuşak Cosine tül degrade geçişi (sıfır çizgi).
    - Odak elmasları (üstte ve altta zarif altın elmaslar).
    - 100% Bold Ibarra Real Nova Türkçe meal kelime sarımı.
    """
    w = 1080
    h = 1920 if format_tipi == "9:16" else 1350
    is_916 = (format_tipi == "9:16")
    is_hadis = (kategori == "hadis")
    cfg = HADIS_SABIT_PALET if is_hadis else DUA_SABIT_PALET
    max_w = 930 if is_916 else 920

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

    if is_hadis:
        tac_txt = custom_tac or "“ Resûlullah (s.a.v.) Buyurdu ”"
        ar_metin = custom_ar or "مَنْ لَا يَرْحَمِ النَّاسَ لَا يَرْحَمْهُ اللَّهُ"
        ok_ham = custom_ok or "Men lâ yerhamin-nâse lâ yerhamhullâh"
        meal_txt = custom_meal or "İnsanlara merhamet etmeyene, Allah da merhamet etmez."
        tef_txt = custom_tef or "İslam ahlakı; insanlara şefkatle muamele etmeyi ve merhameti esas almayı öğütler."
        kaynak_txt = custom_kaynak or "RİYÂZÜ'S-SÂLİHÎN"
    else:
        tac_txt = custom_tac or "“ Günün Duası • Manevi Niyaz ”"
        ar_metin = custom_ar or "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ"
        ok_ham = custom_ok or "Rabbenâ âtinâ fid-dünyâ haseneten ve fîl-âhirati haseneten ve kınâ azâben-nâr"
        meal_txt = custom_meal or "Ey Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver. Ve bizi cehennem azabından koru."
        tef_txt = custom_tef or "Hem dünya hem ahiret saadetini birleştiren en kapsamlı münacattır."
        kaynak_txt = custom_kaynak or "TESCİLLİ DUALAR KÜLLİYATI"

    t_bb = draw.textbbox((0, 0), tac_txt, font=f_tac)
    tac_w = t_bb[2] - t_bb[0]
    while tac_w > (max_w - 40) and pt_tac > 20:
        pt_tac -= 2
        f_tac = font_al(FONT_GOVDE, pt_tac, agirlik=700)
        t_bb = draw.textbbox((0, 0), tac_txt, font=f_tac)
        tac_w = t_bb[2] - t_bb[0]
    tac_h = t_bb[3] - t_bb[1]
    start_tac_y = ayrac_y + (30 if is_916 else 18)
    tac_bottom_y = start_tac_y + tac_h

    # 4. Üst Bölüm: Arapça ve Latin Okunuş
    secavend_regex = re.compile(r"[\u06D6-\u06DA\u06D8\u06D9\u06DB\u06DE\u06E9\s]*[ۚۖۗۘۙۚۜؕ۞۩۝]")
    ar_temiz = secavend_regex.sub("", ar_metin).strip()
    words_ar = ar_temiz.split()
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

    ok_gosterim = f"“ {ok_ham} ”" if ok_ham else ""
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

    # 5. Dinamik Flex Keten Bandı
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

    # 6. Keten Zemin & Cosine Tül Degrade (Sıfır çizgi)
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

    # 9. Dua Eden Eller Filigranı (Dua kategorisi için)
    if not is_hadis:
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

    # 10. Üst Metin Çizimi (Taç, Arapça, Latin)
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

    # 11. Alt Bölüm: Tefekkür & Tescilli Kaynak
    clean_tef = tef_txt.strip().strip('“”" ')
    if not is_hadis and "•" in clean_tef:
        parcalar = clean_tef.split("•", 1)
        if len(parcalar[0].strip()) < 45:
            clean_tef = parcalar[1].strip()

    pt_tef = 30 if is_916 else 25
    f_tef = font_al(FONT_GOVDE, pt_tef, agirlik=400)
    tef_lines = metin_satirla(f"“{clean_tef}”", f_tef, max_w - 40, draw)
    step_tef = int(pt_tef * 1.34)
    tef_block_h = len(tef_lines) * step_tef
    gap_tef_kaynak = 16 if is_916 else 10

    f_kaynak = font_al(FONT_UI, 17 if is_916 else 15, agirlik=700)
    kb = draw.textbbox((0, 0), kaynak_txt, font=f_kaynak)
    kaynak_w = kb[2] - kb[0]
    pt_k = 17 if is_916 else 15
    while kaynak_w > (max_w - 40) and pt_k > 13:
        pt_k -= 1
        f_kaynak = font_al(FONT_UI, pt_k, agirlik=700)
        kb = draw.textbbox((0, 0), kaynak_txt, font=f_kaynak)
        kaynak_w = kb[2] - kb[0]

    total_bot_h = tef_block_h + gap_tef_kaynak + (kb[3] - kb[1])
    usable_top = fade_2_end + (30 if is_916 else 22)
    usable_bot = cta_ust_y - (18 if is_916 else 12)
    bot_y = usable_top + max(0, (usable_bot - usable_top - total_bot_h) // 2)

    for tl in tef_lines:
        tlb = draw.textbbox((0, 0), tl, font=f_tef)
        draw.text(((w - (tlb[2] - tlb[0])) / 2, bot_y), tl, font=f_tef, fill="#FFF5F2")
        bot_y += step_tef
    bot_y += gap_tef_kaynak

    draw.text(((w - (kb[2] - kb[0])) / 2, bot_y), kaynak_txt, font=f_kaynak, fill="#EADBC8")

    # 12. Orta Bölüm: 100% Bold Ibarra Real Nova Türkçe Meal
    solid_meal_h = fade_2_start - fade_1_end
    temiz_meal = turkce_kisaltmalari_genislet(meal_txt.strip("“”\"' "))
    raw_tokens = re.sub(r'\*\*', '', temiz_meal)
    tr_len = len(temiz_meal)
    tr_words = raw_tokens.split()

    if len(tr_words) <= 4 or tr_len <= 30:
        pt_hero = 108 if is_916 else 90
    elif len(tr_words) <= 9 or tr_len <= 60:
        pt_hero = 94 if is_916 else 78
    elif len(tr_words) <= 16 or tr_len <= 110:
        pt_hero = 82 if is_916 else 68
    elif len(tr_words) <= 25 or tr_len <= 155:
        pt_hero = 74 if is_916 else 60
    elif len(tr_words) <= 35 or tr_len <= 220:
        pt_hero = 64 if is_916 else 52
    else:
        pt_hero = 54 if is_916 else 44

    while pt_hero >= 34:
        f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
        tokens = [(tok_str, True) for tok_str in tr_words]
        hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_b, f_hero_b, max_w - 40, draw)
        step_hero = int(pt_hero * 1.32)
        hero_h = len(hero_wrapped) * step_hero
        if hero_h <= solid_meal_h - (24 if is_916 else 14):
            break
        pt_hero -= 2

    f_hero_b = font_al(FONT_BASLIK, pt_hero, agirlik=700)
    tokens = [(tok_str, True) for tok_str in tr_words]
    hero_wrapped, hero_space_w = wrap_mixed_tokens(tokens, f_hero_b, f_hero_b, max_w - 40, draw)
    step_hero = int(pt_hero * 1.32)
    hero_h = len(hero_wrapped) * step_hero

    cur_meal_y = fade_1_end + (solid_meal_h - hero_h) // 2

    flattened_words = []
    w_idx = 0
    c_y = cur_meal_y
    for line_tokens, line_w in hero_wrapped:
        line_x = (w - line_w) // 2
        for word, is_b, word_w in line_tokens:
            flattened_words.append({
                "idx": w_idx,
                "text": word,
                "is_b": True,
                "x": line_x,
                "y": c_y,
                "w": word_w,
                "font": f_hero_b
            })
            line_x += word_w + hero_space_w
            w_idx += 1
        c_y += step_hero

    return {
        "im_base": im,
        "kategori": kategori,
        "flattened_words": flattened_words,
        "pt_hero": pt_hero,
        "fade_1_end": fade_1_end,
        "fade_2_start": fade_2_start,
    }


def pre_render_active_words(flattened_words: List[Dict[str, Any]], kategori: str = "hadis") -> Dict[int, Dict[str, Any]]:
    """Her kelimenin aktif renkli (kırmızı veya kehribar) şeffaf RGBA görselini önceden hazırlar."""
    cache = {}
    active_color = KIRMIZI_HADIS if kategori == "hadis" else KEHRIBAR_DUA

    dummy = Image.new("RGBA", (10, 10))
    d_dummy = ImageDraw.Draw(dummy)

    for w in flattened_words:
        idx = w["idx"]
        txt = w["text"]
        f = w["font"]

        bb = d_dummy.textbbox((0, 0), txt, font=f)
        wt = int(d_dummy.textlength(txt, font=f))
        ht = bb[3] - bb[1]

        im_w = Image.new("RGBA", (wt + 20, bb[3] + 20), (0, 0, 0, 0))
        d_w = ImageDraw.Draw(im_w)
        d_w.text((0, 0), txt, font=f, fill=active_color)

        cache[idx] = {
            "img": im_w,
            "wt": wt,
            "ht": ht,
            "bb": bb
        }
    return cache


class V20Sayfa:
    """Tek bir sayfanın statik tabanını, kelime mizanpajını ve çizimini yönetir."""

    def __init__(
        self,
        page_idx: int,
        kategori: str,
        ar_metin: str,
        ok_ham: str,
        meal_metin: str,
        words_data: List[Dict[str, Any]],
        tac_txt: Optional[str] = None,
        tef_txt: Optional[str] = None,
        kaynak_txt: Optional[str] = None,
        format_tipi: str = "9:16"
    ):
        self.page_idx = page_idx
        self.kategori = kategori
        self.words_data = words_data

        if words_data:
            self.t_start = float(words_data[0].get("start", 0.0))
            self.t_end = float(words_data[-1].get("end", 5.0))
        else:
            self.t_start = 0.0
            self.t_end = 5.0

        self.layout = build_v20_base_layout(
            kategori=kategori,
            format_tipi=format_tipi,
            custom_meal=meal_metin,
            custom_ar=ar_metin,
            custom_ok=ok_ham,
            custom_tac=tac_txt,
            custom_tef=tef_txt,
            custom_kaynak=kaynak_txt
        )
        self.im_base = self.layout["im_base"]
        self.flattened_words = self.layout["flattened_words"]
        self.word_cache = pre_render_active_words(self.flattened_words, kategori=kategori)

    def render(self, t_sec: float, force_complete: bool = False, force_unread: bool = False) -> Image.Image:
        frame = self.im_base.copy()
        draw = ImageDraw.Draw(frame)

        if force_complete:
            for w in self.flattened_words:
                draw.text((w["x"], w["y"]), w["text"], font=w["font"], fill=METIN_ANA)
            return frame

        if force_unread:
            for w in self.flattened_words:
                draw.text((w["x"], w["y"]), w["text"], font=w["font"], fill=METIN_LIGHT)
            return frame

        aktif_idx = -1
        aktif_prog = 0.0

        if self.words_data and t_sec < float(self.words_data[0].get("start", 0.0)):
            aktif_idx = -1
            aktif_prog = 0.0
        elif self.words_data and t_sec >= float(self.words_data[-1].get("end", 0.0)):
            aktif_idx = len(self.words_data)
            aktif_prog = 1.0
        else:
            for i, wd in enumerate(self.words_data):
                s = float(wd.get("start", 0.0))
                e = float(wd.get("end", s + 0.5))
                if s <= t_sec <= e:
                    aktif_idx = i
                    dur = max(0.01, e - s)
                    aktif_prog = min(1.0, max(0.0, (t_sec - s) / dur))
                    break
                elif i < len(self.words_data) - 1 and e < t_sec < float(self.words_data[i+1].get("start", e)):
                    aktif_idx = i
                    aktif_prog = 1.0
                    break

        for w in self.flattened_words:
            idx = w["idx"]
            txt = w["text"]
            f = w["font"]
            x = w["x"]
            y = w["y"]

            if idx not in self.word_cache:
                draw.text((x, y), txt, font=f, fill=METIN_LIGHT)
                continue

            c_info = self.word_cache[idx]
            wt = c_info["wt"]
            im_w = c_info["img"]

            if idx == aktif_idx and aktif_prog < 1.0:
                draw.text((x, y), txt, font=f, fill=METIN_LIGHT)
                dolum_w = int(wt * aktif_prog)
                if dolum_w > 0:
                    cropped = im_w.crop((0, 0, dolum_w, im_w.height))
                    frame.paste(cropped, (x, y), cropped)
            elif idx < aktif_idx or (idx == aktif_idx and aktif_prog >= 1.0):
                draw.text((x, y), txt, font=f, fill=METIN_ANA)
            else:
                draw.text((x, y), txt, font=f, fill=METIN_LIGHT)

        return frame


class V20MultiPageVideoEngine:
    """Çok sayfalı Hadis ve Dua dinamik video üretim motoru."""

    def __init__(
        self,
        kategori: str,
        sayfalar: List[V20Sayfa],
        crossfade_dur: float = 0.45
    ):
        self.kategori = kategori
        self.sayfalar = sayfalar
        self.sayfa_sayisi = len(sayfalar)
        self.crossfade_dur = crossfade_dur

        self.gecisler: List[Tuple[float, float, int, int]] = []
        for p in range(self.sayfa_sayisi - 1):
            p_from = p
            p_to = p + 1
            t_end_prev = self.sayfalar[p_from].t_end
            t_start_next = self.sayfalar[p_to].t_start

            gap = t_start_next - t_end_prev
            if gap >= self.crossfade_dur:
                t_s = t_end_prev + (gap - self.crossfade_dur) / 2
                t_e = t_s + self.crossfade_dur
            else:
                dur = min(self.crossfade_dur, max(0.20, gap)) if gap > 0.1 else self.crossfade_dur
                t_s = max(0.0, t_end_prev - dur * 0.3)
                t_e = t_s + dur

            self.gecisler.append((t_s, t_e, p_from, p_to))

    def render_frame(self, t_sec: float, total_sec: float) -> Image.Image:
        """Belirtilen andaki video karesini (crossfade dahil) döndürür."""
        if self.sayfa_sayisi == 1:
            kare = self.sayfalar[0].render(t_sec)
        else:
            in_transition = False
            kare = None
            for t_s, t_e, p_from, p_to in self.gecisler:
                if t_s <= t_sec <= t_e:
                    alpha = (t_sec - t_s) / max(0.001, (t_e - t_s))
                    kare_from = self.sayfalar[p_from].render(t_sec, force_complete=True)
                    kare_to = self.sayfalar[p_to].render(t_sec, force_unread=True)
                    kare = Image.blend(kare_from, kare_to, alpha)
                    in_transition = True
                    break

            if not in_transition or kare is None:
                active_p = 0
                for t_s, t_e, p_from, p_to in self.gecisler:
                    if t_sec < t_s:
                        active_p = p_from
                        break
                    else:
                        active_p = p_to
                kare = self.sayfalar[active_p].render(t_sec)

        # Alt İlerleme Çubuğu (Y = 1858) - Sayfa geçişlerinden bağımsız
        draw_k = ImageDraw.Draw(kare)
        bar_x1, bar_x2 = 90, 1080 - 90
        bar_y = 1858
        bar_w = bar_x2 - bar_x1
        progress = min(1.0, max(0.0, t_sec / max(0.1, total_sec)))

        bar_bg = "#233B32" if self.kategori == "hadis" else "#14303A"
        yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x2, bar_y + 8), radius=4, dolgu=bar_bg)
        dolu_w = int(bar_w * progress)
        if dolu_w > 4:
            fill_color = KIRMIZI_HADIS if self.kategori == "hadis" else "#C29B38"
            yuvarlak_kose_ciz(draw_k, (bar_x1, bar_y, bar_x1 + dolu_w, bar_y + 8), radius=4, dolgu=fill_color)
            draw_k.ellipse(
                [bar_x1 + dolu_w - 7, bar_y - 3, bar_x1 + dolu_w + 7, bar_y + 11],
                fill="#FFF8EE",
                outline=fill_color,
                width=2
            )

        return kare

    def export_video(
        self,
        cikti_mp4: Path,
        mp3_path: Path,
        fon_ney_path: Optional[Path] = None,
        ney_volume: float = 0.48
    ) -> Path:
        """Çok sayfalı dinamik videoyu 30 FPS hızında render eder ve ses miksajını yapar."""
        cikti_mp4.parent.mkdir(parents=True, exist_ok=True)
        total_sec = ses_sure_hesapla(mp3_path)
        video_sec = total_sec + 0.5
        total_frames = int(math.ceil(video_sec * FPS))

        log.info(f"Video Render Başlıyor: {cikti_mp4.name} | Sayfa: {self.sayfa_sayisi} | Süre: {video_sec:.2f}s ({total_frames} kare)")

        temp_video = cikti_mp4.with_name(f"temp_silent_{cikti_mp4.name}")
        writer = imageio.get_writer(
            str(temp_video),
            fps=FPS,
            codec="libx264",
            quality=9,
            pixelformat="yuv420p",
            macro_block_size=None,
        )

        try:
            for i in range(total_frames):
                t_sec = i / FPS
                frame_im = self.render_frame(t_sec, total_sec)

                if i == 0:
                    cover_p = cikti_mp4.with_suffix(".png")
                    frame_im.save(cover_p, quality=95)

                frame_np = np.array(frame_im)
                writer.append_data(frame_np)

                if (i + 1) % 90 == 0 or i == total_frames - 1:
                    log.debug(f"Render İlerleme: %{int((i+1)/total_frames*100)} ({i+1}/{total_frames} kare)")
        finally:
            writer.close()

        # FFmpeg ile Spiker Sesi + Telifsiz Ney Fon Müziği Miksajı
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if fon_ney_path and fon_ney_path.exists():
            fon_name = fon_ney_path.name.lower()
            if "segah" in fon_name:
                fon_offset = 2.90
            elif "ferahfeza" in fon_name:
                fon_offset = 2.60
            else:
                fon_offset = 0.0

            log.info(f"Ney fon müziği miksleniyor: {fon_ney_path.name} (volume={ney_volume}, offset={fon_offset}s, attack=0.15s)")
            cmd = [
                exe, "-y",
                "-i", str(temp_video),
                "-i", str(mp3_path),
                "-i", str(fon_ney_path),
                "-filter_complex",
                f"[1:a]volume=1.0[v];[2:a]atrim=start={fon_offset},asetpts=PTS-STARTPTS,volume={ney_volume},afade=t=in:st=0:d=0.15,afade=t=out:st={total_sec-1.0}:d=1.2[m];[v][m]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(cikti_mp4)
            ]
        else:
            cmd = [
                exe, "-y",
                "-i", str(temp_video),
                "-i", str(mp3_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(cikti_mp4)
            ]

        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if temp_video.exists():
            temp_video.unlink()

        log.info(f"Çok Sayfalı Dinamik Video Başarıyla Üretildi: {cikti_mp4} ({cikti_mp4.stat().st_size} bayt)")
        return cikti_mp4


def akilli_v20_sayfalari_olustur(
    kategori: str,
    meal_metin: str,
    ar_metin: str,
    ok_ham: str,
    words_data: List[Dict[str, Any]],
    tac_txt: Optional[str] = None,
    tef_txt: Optional[str] = None,
    kaynak_txt: Optional[str] = None,
) -> List[V20Sayfa]:
    """
    Türkçe meal ve zaman damgalarını analiz ederek metni en uygun sayfa sayısına
    ve cümle/nefes sınırlarına göre böler.
    14 kelime ve altında tek sayfa; üzerindeyse mantıklı cümle/durak noktalarından böler.
    """
    ar_metin = arapca_glif_temizle(ar_metin) if ar_metin else ""
    meal_metin = turkce_kisaltmalari_genislet(meal_metin) if meal_metin else ""
    total_words = len(words_data)

    # 1. Tek Sayfa Durumu
    if total_words <= 14:
        clean_meal = meal_metin
        if len(clean_meal.split()) != total_words and words_data:
            clean_meal = " ".join(w.get("text", "") for w in words_data)
        return [
            V20Sayfa(
                page_idx=0,
                kategori=kategori,
                ar_metin=ar_metin,
                ok_ham=ok_ham,
                meal_metin=clean_meal,
                words_data=words_data,
                tac_txt=tac_txt,
                tef_txt=tef_txt,
                kaynak_txt=kaynak_txt,
            )
        ]

    # 2. Çok Sayfalı Durum: Sayfa Sayısı Hesaplama
    hedef_sayfa = max(2, math.ceil(total_words / 12))

    # Cümle sonları (. ! ? ;) ve nefes durakları tespiti
    split_indices = []
    sentence_end_chars = {".", "!", "?", ";", "…"}

    for i, w in enumerate(words_data[:-1]):
        txt = w.get("text", "")
        end_time = float(w.get("end", 0.0))
        next_start = float(words_data[i + 1].get("start", end_time))
        pause = next_start - end_time

        has_punct = any(txt.endswith(c) for c in sentence_end_chars)
        is_long_pause = (pause >= 0.25)

        if has_punct or is_long_pause:
            split_indices.append((i + 1, has_punct, pause))

    # İdeal sayfa bölümleri seçimi
    page_splits = []
    if split_indices:
        step = total_words / hedef_sayfa
        cur_pos = 0
        for p in range(1, hedef_sayfa):
            target_idx = int(round(p * step))
            best = min(split_indices, key=lambda x: abs(x[0] - target_idx))
            if best[0] > cur_pos and best[0] < total_words - 2:
                page_splits.append(best[0])
                cur_pos = best[0]

    # Eğer noktalama bulunamadıysa matematiksel ortadan böl
    if not page_splits:
        step = total_words // hedef_sayfa
        page_splits = [step * p for p in range(1, hedef_sayfa)]

    # Sayfa kelime dilimlerini oluştur
    page_slices = []
    last_idx = 0
    for sp in page_splits:
        page_slices.append((last_idx, sp))
        last_idx = sp
    page_slices.append((last_idx, total_words))

    # Arapça ve Latin okunuş parçalama
    ar_words = ar_metin.split()
    ok_words = ok_ham.split()
    meal_tokens = meal_metin.split()

    sayfalar = []
    for p_idx, (s_idx, e_idx) in enumerate(page_slices):
        p_words_data = words_data[s_idx:e_idx]
        if len(meal_tokens) == total_words:
            p_meal = " ".join(meal_tokens[s_idx:e_idx])
        else:
            p_meal = " ".join(w.get("text", "") for w in p_words_data)

        # Arapça ve Latin parçalarını oranlayarak seç
        r_start = s_idx / total_words
        r_end = e_idx / total_words

        ar_s = int(round(r_start * len(ar_words)))
        ar_e = int(round(r_end * len(ar_words)))
        if p_idx == len(page_slices) - 1:
            ar_e = len(ar_words)
        p_ar = " ".join(ar_words[ar_s:ar_e]) if ar_words else ar_metin

        ok_s = int(round(r_start * len(ok_words)))
        ok_e = int(round(r_end * len(ok_words)))
        if p_idx == len(page_slices) - 1:
            ok_e = len(ok_words)
        p_ok = " ".join(ok_words[ok_s:ok_e]) if ok_words else ok_ham

        sayfa = V20Sayfa(
            page_idx=p_idx,
            kategori=kategori,
            ar_metin=p_ar,
            ok_ham=p_ok,
            meal_metin=p_meal,
            words_data=p_words_data,
            tac_txt=tac_txt,
            tef_txt=tef_txt,
            kaynak_txt=kaynak_txt,
        )
        sayfalar.append(sayfa)

    return sayfalar


def hadis_videosu_uret(
    hadis_metni: str,
    kaynak_ref: str,
    ses_yolu: Path,
    words_data: List[Dict[str, Any]],
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    ravi: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    cikti_yolu: Optional[Path] = None,
    ney_volume: float = 0.48,
) -> Path:
    """
    Riyâzü's-Sâlihîn Hadis-i Şerif videosunu V20 Çok Sayfalı Dinamik Video Motoruyla üretir.
    - 100% Bold Ibarra Real Nova Türkçe meal karaoke dolumu.
    - Arka planda Solo Segâh Ney Fon Müziği.
    - Çok sayfalı geçişler (0.45s crossfade).
    """
    if cikti_yolu is None:
        cikti_yolu = KOK_DIZIN / "data" / "cikti" / f"hadis_v20_{int(Path(ses_yolu).stem.split('_')[-1] if '_' in Path(ses_yolu).stem else 0)}.mp4"

    from .ses import hadis_metninden_kaynaklari_temizle
    hadis_metni = hadis_metninden_kaynaklari_temizle(hadis_metni)

    tac_txt = "“ Resûlullah (s.a.v.) Buyurdu ”"
    tef_txt = tefekkur_notu or "İslam ahlakı; hayatın her anında şefkat, adalet ve samimiyetle yaşamayı öğütler."
    ar_txt = arapca_metin or "مَنْ لَا يَرْحَمِ النَّاسَ لَا يَرْحَمْهُ اللَّهُ"
    ok_txt = arapca_okunus or ""

    kaynak_full = (kaynak_ref or "Riyâzü's-Sâlihîn").strip()
    if ravi and ravi.strip() and ravi.strip().lower() not in kaynak_full.lower():
        kaynak_full = f"{kaynak_full} • RÂVİ: {ravi.strip().upper()}"

    sayfalar = akilli_v20_sayfalari_olustur(
        kategori="hadis",
        meal_metin=hadis_metni,
        ar_metin=ar_txt,
        ok_ham=ok_txt,
        words_data=words_data,
        tac_txt=tac_txt,
        tef_txt=tef_txt,
        kaynak_txt=kaynak_full,
    )

    fon_ney = KOK_DIZIN / "assets" / "audio" / "fon" / "ney_segah.mp3"
    engine = V20MultiPageVideoEngine(kategori="hadis", sayfalar=sayfalar, crossfade_dur=0.45)
    return engine.export_video(
        cikti_mp4=Path(cikti_yolu),
        mp3_path=Path(ses_yolu),
        fon_ney_path=fon_ney if fon_ney.exists() else None,
        ney_volume=ney_volume
    )


def dua_videosu_uret(
    turkce_anlam: str,
    dua_basligi: str,
    ses_yolu: Path,
    words_data: List[Dict[str, Any]],
    arapca_metin: Optional[str] = None,
    arapca_okunus: Optional[str] = None,
    tefekkur_notu: Optional[str] = None,
    kaynak_ref: Optional[str] = None,
    cikti_yolu: Optional[Path] = None,
    ney_volume: float = 0.48,
) -> Path:
    """
    Günün Duası / Manevi Niyaz videosunu V20 Çok Sayfalı Dinamik Video Motoruyla üretir.
    - 100% Bold Ibarra Real Nova Türkçe meal karaoke dolumu (Kehribar ton).
    - Arka planda Solo Ferahfezâ Ney Fon Müziği.
    - Dua eden eller filigranı ve çok sayfalı geçişler (0.45s crossfade).
    """
    if cikti_yolu is None:
        cikti_yolu = KOK_DIZIN / "data" / "cikti" / f"dua_v20_{int(Path(ses_yolu).stem.split('_')[-1] if '_' in Path(ses_yolu).stem else 0)}.mp4"

    tac_txt = f"“ {dua_basligi} ”"
    clean_tef = tefekkur_notu or "Dua; kulun Rabbi ile en samimi, en derin ve en huzurlu buluşma anıdır."
    if "•" in clean_tef:
        parcalar = clean_tef.split("•", 1)
        if len(parcalar[0].strip()) < 45:
            clean_tef = parcalar[1].strip()
    tef_txt = clean_tef
    ar_txt = arapca_metin or "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ"
    ok_txt = arapca_okunus or ""
    kaynak_txt = kaynak_ref or dua_basligi

    sayfalar = akilli_v20_sayfalari_olustur(
        kategori="dua",
        meal_metin=turkce_anlam,
        ar_metin=ar_txt,
        ok_ham=ok_txt,
        words_data=words_data,
        tac_txt=tac_txt,
        tef_txt=tef_txt,
        kaynak_txt=kaynak_txt,
    )

    fon_ney = KOK_DIZIN / "assets" / "audio" / "fon" / "ney_ferahfeza.mp3"
    engine = V20MultiPageVideoEngine(kategori="dua", sayfalar=sayfalar, crossfade_dur=0.45)
    return engine.export_video(
        cikti_mp4=Path(cikti_yolu),
        mp3_path=Path(ses_yolu),
        fon_ney_path=fon_ney if fon_ney.exists() else None,
        ney_volume=ney_volume
    )
