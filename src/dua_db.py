"""
dua_db.py — Ezan Plus Tescilli Dualar Külliyatı Modülü

Kur'an-ı Kerim'den peygamber duaları ve Kütüb-i Sitte'den sahih nebevi niyazları yönetir.
Sıfır yapay zeka halüsinasyonu garantisiyle, tescilli metin ve kaynakları sağlar.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ayar import KOK_DIZIN
from . import db

log = logging.getLogger(__name__)

DUALAR_DOSYASI = KOK_DIZIN / "data" / "dualar" / "dualar.json"


def dualari_yukle() -> List[Dict[str, Any]]:
    """Tescilli dualar JSON dosyasını okur."""
    if not DUALAR_DOSYASI.exists():
        log.error(f"Dualar dosyası bulunamadı: {DUALAR_DOSYASI}")
        return []
    with open(DUALAR_DOSYASI, "r", encoding="utf-8") as f:
        return json.load(f)


def dua_getir_id(dua_id: int) -> Optional[Dict[str, Any]]:
    """ID ile belirli bir duayı getirir."""
    dualar = dualari_yukle()
    for d in dualar:
        if d.get("id") == dua_id:
            return d
    return None


def dua_bul(sorgu: str) -> Optional[Dict[str, Any]]:
    """Başlık, kaynak veya ruh haline göre dua arar."""
    dualar = dualari_yukle()
    sorgu_temiz = sorgu.strip().lower()
    for d in dualar:
        if (
            sorgu_temiz in d.get("dua_basligi", "").lower()
            or sorgu_temiz in d.get("kimin_duasi", "").lower()
            or sorgu_temiz in d.get("kaynak_ref", "").lower()
            or sorgu_temiz in d.get("ruh_hali", "").lower()
        ):
            return d
    return None


def duayi_paylasildi_isaretle(dua_id: int):
    """Duayı JSON üzerinde paylaşıldı olarak işaretler."""
    dualar = dualari_yukle()
    for d in dualar:
        if d.get("id") == dua_id:
            d["paylasildi_mi"] = True
            break
    try:
        with open(DUALAR_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(dualar, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"Dua paylaşıldı işaretlenemedi: {e}")


def gunun_duasini_sec(
    ruh_hali: Optional[str] = None,
    haric_tutulanlar: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Ruh hâline uygun veya rastgele tescilli bir dua seçer.
    Son paylaşılanları (haric_tutulanlar) eler.
    """
    dualar = dualari_yukle()
    if not dualar:
        return None

    haric_set = set(haric_tutulanlar or [])

    # 1. Ruh hâli filtresi
    adaylar = []
    if ruh_hali:
        ruh_kelimeleri = [k.lower() for k in ruh_hali.replace("/", " ").replace("-", " ").split() if len(k) >= 3]
        for d in dualar:
            d_hali = d.get("ruh_hali", "").lower()
            d_baslik = d.get("dua_basligi", "").lower()
            d_kim = d.get("kimin_duasi", "").lower()
            if any(k in d_hali or k in d_baslik or k in d_kim for k in ruh_kelimeleri):
                adaylar.append(d)

    if not adaylar:
        adaylar = list(dualar)

    # Mükerrerleri filtrele
    if haric_set:
        temiz_adaylar = [d for d in adaylar if d.get("dua_basligi") not in haric_set and d.get("kaynak_ref") not in haric_set]
        if temiz_adaylar:
            adaylar = temiz_adaylar

    return random.choice(adaylar)
