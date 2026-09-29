"""
arsiv.py — Ezan Plus Kalıcı İçerik ve Medya Arşivi Motoru

Üretilen her içeriğin (video, çift format görsel, ses, altyazı ve caption)
benzersiz bir kimlikle (unique_id) ve tasarım versiyonuyla (v1, v2...)
GitHub reposundaki kalıcı depoya (data/arsiv/) kaydedilmesini ve
daha önce üretilmiş içeriklerin tekrar render edilmeden arşivden
doğrudan getirilmesini sağlar.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ayar import KOK_DIZIN, AKTIF_TASARIM_VERSIYONU

log = logging.getLogger(__name__)

ARSIV_KOK_DIZIN = KOK_DIZIN / "data" / "arsiv"


def arsiv_dizini_getir(kategori: str, versiyon: str = AKTIF_TASARIM_VERSIYONU) -> Path:
    """Belirtilen versiyon ve kategoriye ait arşiv dizinini hazırlar ve döner."""
    kat_temiz = "ayet" if kategori in ("reels", "ayet", "kuran") else kategori.lower()
    hedef = ARSIV_KOK_DIZIN / versiyon.lower() / kat_temiz
    hedef.mkdir(parents=True, exist_ok=True)
    return hedef


def unique_id_olustur(kategori: str, **kwargs) -> str:
    """Kategoriye ve içeriğe özel standart, deterministik unique_id üretir."""
    kat_temiz = "ayet" if kategori in ("reels", "ayet", "kuran") else kategori.lower()
    
    if kat_temiz == "ayet":
        sure_no = kwargs.get("sure_no")
        ayet_no = kwargs.get("ayet_no")
        if sure_no and ayet_no:
            return f"ayet_{sure_no}_{ayet_no}"
        kaynak = kwargs.get("kaynak", "")
        import re
        m = re.search(r"(\d+)[:\s,\.]+(\d+)", kaynak)
        if m:
            return f"ayet_{m.group(1)}_{m.group(2)}"
        return f"ayet_{int(time.time())}"

    elif kat_temiz == "hadis":
        hadis_id = kwargs.get("hadis_id")
        if hadis_id is not None:
            return f"hadis_{hadis_id}"
        return f"hadis_{int(time.time())}"

    elif kat_temiz == "dua":
        dua_id = kwargs.get("dua_id")
        if dua_id is not None:
            return f"dua_{dua_id}"
        return f"dua_{int(time.time())}"

    elif kat_temiz == "kelime":
        kelime_id = kwargs.get("kelime_id")
        if kelime_id is not None:
            return f"kelime_{kelime_id}"
        return f"kelime_{int(time.time())}"

    return f"{kat_temiz}_{int(time.time())}"


def arsivde_var_mi(
    unique_id: str,
    kategori: str,
    versiyon: str = AKTIF_TASARIM_VERSIYONU,
) -> Optional[Dict[str, Any]]:
    """
    Belirtilen unique_id ve tasarım versiyonu arşivde mevcut mu kontrol eder.
    Varsa ve tüm medya dosyaları diskte eksiksiz ise arşiv kaydını döner.
    Eksik dosya veya farklı tasarım versiyonunda None döner.
    """
    if not unique_id:
        return None

    dizin = arsiv_dizini_getir(kategori=kategori, versiyon=versiyon)
    json_yolu = dizin / f"{unique_id}.json"

    if not json_yolu.exists():
        return None

    try:
        with open(json_yolu, "r", encoding="utf-8") as f:
            kayit: Dict[str, Any] = json.load(f)

        # Versiyon uyuşmazlığı denetimi
        if kayit.get("tasarim_versiyonu") != versiyon:
            log.info(f"Arşiv kaydı bulundu fakat versiyon uyuşmuyor: {kayit.get('tasarim_versiyonu')} != {versiyon}")
            return None

        # Medya dosyalarının fiziki varlık denetimi
        medyalar = kayit.get("medya_yollari", {})
        if not medyalar:
            return None

        for tip, dosya_adi in medyalar.items():
            dosya_yolu = dizin / dosya_adi
            if not dosya_yolu.exists() or dosya_yolu.stat().st_size == 0:
                log.warning(f"Arşiv medya dosyası eksik veya boş: {dosya_yolu}")
                return None

        # Tam mutlak yolları ekleyerek kaydı hazırla
        kayit["dizin"] = str(dizin)
        kayit["medya_mutlak_yollari"] = {
            tip: str(dizin / dosya_adi) for tip, dosya_adi in medyalar.items()
        }
        if "video" in medyalar:
            kayit["video_yolu"] = str(dizin / medyalar["video"])
        if "gorsel_4_5" in medyalar and "gorsel_9_16" in medyalar:
            kayit["gorsel_yollari"] = [
                str(dizin / medyalar["gorsel_4_5"]),
                str(dizin / medyalar["gorsel_9_16"]),
            ]
        elif "gorsel" in medyalar:
            kayit["gorsel_yollari"] = [str(dizin / medyalar["gorsel"])]

        log.info(f"🎯 [REPO ARŞİVİNDE BULUNDU] {unique_id} ({versiyon}) depodan eksiksiz yüklendi.")
        return kayit

    except Exception as e:
        log.warning(f"Arşiv kaydı okunurken hata oluştu ({unique_id}): {e}")
        return None


def arsive_kaydet(
    unique_id: str,
    kategori: str,
    medya_kaynaklari: Dict[str, str],
    meta: Dict[str, Any],
    versiyon: str = AKTIF_TASARIM_VERSIYONU,
) -> Dict[str, Any]:
    """
    Üretilen medya dosyalarını ve meta verilerini kalıcı data/arsiv/{versiyon}/{kategori}/ altına kopyalar ve kaydeder.
    
    medya_kaynaklari örneği:
      - Video için: {"video": "/path/to/reels.mp4"}
      - Görsel için: {"gorsel_4_5": "/path/to/4_5.png", "gorsel_9_16": "/path/to/9_16.png"}
    """
    dizin = arsiv_dizini_getir(kategori=kategori, versiyon=versiyon)
    arsivlenen_medyalar: Dict[str, str] = {}
    mutlak_yollar: Dict[str, str] = {}

    for tip, kaynak_yol_str in medya_kaynaklari.items():
        if not kaynak_yol_str:
            continue
        kaynak_yol = Path(kaynak_yol_str)
        if not kaynak_yol.exists():
            log.warning(f"Arşivlenecek medya dosyası bulunamadı: {kaynak_yol}")
            continue

        uzanti = kaynak_yol.suffix.lower()
        if tip == "video":
            hedef_ad = f"{unique_id}{uzanti}"
        else:
            hedef_ad = f"{unique_id}_{tip}{uzanti}"

        hedef_yol = dizin / hedef_ad
        try:
            shutil.copy2(kaynak_yol, hedef_yol)
            arsivlenen_medyalar[tip] = hedef_ad
            mutlak_yollar[tip] = str(hedef_yol)
            log.info(f"📦 Arşivlendi: {hedef_yol.relative_to(KOK_DIZIN)}")
        except Exception as e:
            log.error(f"Arşiv kopyalama hatası ({kaynak_yol} -> {hedef_yol}): {e}")

    # Meta veri JSON dosyasını oluştur
    meta_kayit = {
        "unique_id": unique_id,
        "kategori": kategori,
        "tasarim_versiyonu": versiyon,
        "olusturma_tarihi": time.strftime("%Y-%m-%d %H:%M:%S"),
        "medya_yollari": arsivlenen_medyalar,
        "baslik": meta.get("baslik"),
        "kaynak": meta.get("kaynak"),
        "turkce_metin": meta.get("turkce_metin"),
        "arapca_metin": meta.get("arapca_metin"),
        "arapca_okunus": meta.get("arapca_okunus"),
        "tefekkur": meta.get("tefekkur"),
        "caption": meta.get("caption"),
        "ekstra": meta.get("ekstra", {}),
    }

    json_yolu = dizin / f"{unique_id}.json"
    with open(json_yolu, "w", encoding="utf-8") as f:
        json.dump(meta_kayit, f, ensure_ascii=False, indent=2)

    meta_kayit["dizin"] = str(dizin)
    meta_kayit["medya_mutlak_yollari"] = mutlak_yollar
    return meta_kayit


def arsiv_istatistikleri() -> Dict[str, Any]:
    """Arşivdeki kayıtlı içeriklerin sayılarını versiyon ve kategori bazında döner."""
    if not ARSIV_KOK_DIZIN.exists():
        return {}
    istatistik = {}
    for ver_dir in ARSIV_KOK_DIZIN.iterdir():
        if ver_dir.is_dir() and not ver_dir.name.startswith("."):
            ver_name = ver_dir.name
            istatistik[ver_name] = {}
            for kat_dir in ver_dir.iterdir():
                if kat_dir.is_dir() and not kat_dir.name.startswith("."):
                    json_sayisi = len(list(kat_dir.glob("*.json")))
                    istatistik[ver_name][kat_dir.name] = json_sayisi
    return istatistik
