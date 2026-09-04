"""
test_parcali_gecis.py — Uzun Ayet Çoklu Sayfa Geçiş Testi (Hadîd 20)
40 kelimelik Hadîd 20 ayetini 2 sayfalı dinamik crossfade geçişle render eder.
"""

import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio
import imageio_ffmpeg

from src.ayar import KOK_DIZIN
from src.uretim import ses
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

def _meal_parcala(meal_metin: str, parca_sayisi: int):
    if parca_sayisi <= 1:
        return [meal_metin.strip()]
    cumleler = [c.strip() for c in re.split(r'(?<=[.!?;\n])\s+', meal_metin.strip()) if c.strip()]
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

print("Test script hazırlandı.")
