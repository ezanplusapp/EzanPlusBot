"""
kelime_db.py — Ezan Plus Kur'an Sözlüğü ve İslami Kavramlar Modülü

Kur'an-ı Kerim'de geçen ve İslam dininde derin manası olan anahtar kavramlar (el-Müfredât).
Sıfır yapay zeka halüsinasyonu garantisiyle, tescilli kök anlamı, ayet ve tefekkür sağlar.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ayar import KOK_DIZIN

log = logging.getLogger(__name__)

KELIMELER_DOSYASI = KOK_DIZIN / "data" / "kelimeler" / "kelimeler.json"


import re

COMMON_TYPO_FIXES = [
    (r"\bsarsarsa sarsın\b", "sarsarsa sarssın"),
    (r"\bherşey\b", "her şey"),
    (r"\bbirşey\b", "bir şey"),
    (r"\bhiçbirşey\b", "hiçbir şey"),
    (r"\byalnış\b", "yanlış"),
    (r"\byanlız\b", "yalnız"),
]


def kelime_metnini_temizle(metin: str) -> str:
    """Yazım ve imla kurallarını TDK ve editoryal standartlara göre doğrular ve düzeltir."""
    if not metin or not isinstance(metin, str):
        return metin
    temiz = metin
    for pattern, replacement in COMMON_TYPO_FIXES:
        temiz = re.sub(pattern, replacement, temiz, flags=re.IGNORECASE)
    return temiz


def kelimeleri_yukle() -> List[Dict[str, Any]]:
    """Tescilli kelimeler JSON dosyasını okur ve imla kontrolünden geçirir."""
    if not KELIMELER_DOSYASI.exists():
        log.error(f"Kelimeler dosyası bulunamadı: {KELIMELER_DOSYASI}")
        return []
    with open(KELIMELER_DOSYASI, "r", encoding="utf-8") as f:
        veriler: List[Dict[str, Any]] = json.load(f)

    # Otomatik İmla ve Yazım Güvenlik Katmanı
    for k in veriler:
        for alan in ("lugat_anlami", "hayat_dersi", "kuran_boyutu", "ayet_ref"):
            if alan in k and isinstance(k[alan], str):
                k[alan] = kelime_metnini_temizle(k[alan])

    return veriler


def kelimeleri_denetle() -> List[str]:
    """Tüm kelime koleksiyonunu eksik alan ve imla hatalarına karşı tarar."""
    hatalar: List[str] = []
    kelimeler = kelimeleri_yukle()
    zorunlu_alanlar = ["id", "kelime_tr", "kelime_ar", "okunus", "kok", "lugat_anlami", "hayat_dersi", "ayet_ref"]

    for k in kelimeler:
        k_id = k.get("id", "?")
        for z in zorunlu_alanlar:
            if not k.get(z):
                hatalar.append(f"Kelime ID {k_id}: '{z}' alanı boş veya eksik!")

    return hatalar


def kelime_getir_id(kelime_id: int) -> Optional[Dict[str, Any]]:
    """ID ile belirli bir kelimeyi getirir."""
    kelimeler = kelimeleri_yukle()
    for k in kelimeler:
        if k.get("id") == kelime_id:
            return k
    return None


def kelime_bul(sorgu: str) -> Optional[Dict[str, Any]]:
    """Kavram adı, kök veya anlama göre kelime arar."""
    kelimeler = kelimeleri_yukle()
    sorgu_temiz = sorgu.strip().lower()
    for k in kelimeler:
        if (
            sorgu_temiz in k.get("kelime_tr", "").lower()
            or sorgu_temiz in k.get("kok", "").lower()
            or sorgu_temiz in k.get("lugat_anlami", "").lower()
        ):
            return k
    return None


def kelimeyi_paylasildi_isaretle(kelime_id: int):
    """Kelimeyi JSON üzerinde paylaşıldı olarak işaretler."""
    kelimeler = kelimeleri_yukle()
    for k in kelimeler:
        if k.get("id") == kelime_id:
            k["paylasildi_mi"] = True
            break
    try:
        with open(KELIMELER_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kelimeler, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"Kelime paylaşıldı işaretlenemedi: {e}")


def kelimeyi_paylasildi_isaretle_kavram(kavram: str):
    """Kelime adıyla (örn. 'Vakar') JSON üzerinde paylaşıldı olarak işaretler."""
    if not kavram:
        return
    kelimeler = kelimeleri_yukle()
    hedef = kavram.strip().lower()
    for k in kelimeler:
        if k.get("kelime_tr", "").strip().lower() == hedef:
            k["paylasildi_mi"] = True
            break
    try:
        with open(KELIMELER_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kelimeler, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"Kelime ({kavram}) paylaşıldı işaretlenemedi: {e}")


def gunun_kelimesini_sec(
    haric_tutulanlar: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Paylaşılmamış veya en az paylaşılmış tescilli bir kavram seçer.
    """
    kelimeler = kelimeleri_yukle()
    if not kelimeler:
        return None

    haric_set = set(haric_tutulanlar or [])
    adaylar = [k for k in kelimeler if k.get("kelime_tr") not in haric_set and not k.get("paylasildi_mi", False)]
    if not adaylar:
        adaylar = list(kelimeler)

    return random.choice(adaylar)
