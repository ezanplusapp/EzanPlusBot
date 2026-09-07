"""
ses_getir.py — Ezan Plus Kur'an Tilaveti ve Ses Yöneticisi
EveryAyah API üzerinden telifsiz, yüksek kaliteli hafız seslerini indirir,
birden fazla ayeti birleştirir ve ses süresini hesaplar.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional
import requests
import imageio_ffmpeg

from ..ayar import KOK_DIZIN

log = logging.getLogger(__name__)

SES_DIZINI = KOK_DIZIN / "assets" / "audio"
SES_DIZINI.mkdir(parents=True, exist_ok=True)

# EveryAyah Hafız Klasörü (Mishary Rashid Alafasy 128kbps)
HAFIZ_URL_TABAN = "https://everyayah.com/data/Alafasy_128kbps"


def ayet_sesi_indir(sure_no: int, ayet_no: int) -> Path:
    """Belirtilen sure ve ayetin MP3 ses dosyasını indirir."""
    # EveryAyah dosya adı formatı: 3 haneli sure + 3 haneli ayet (Örn: 094005.mp3)
    dosya_adi = f"{sure_no:03d}{ayet_no:03d}.mp3"
    hedef_yol = SES_DIZINI / dosya_adi

    if hedef_yol.exists() and hedef_yol.stat().st_size > 1000:
        log.info(f"Ayet sesi zaten mevcut: {hedef_yol}")
        return hedef_yol

    url = f"{HAFIZ_URL_TABAN}/{dosya_adi}"
    log.info(f"Ayet sesi indiriliyor: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()

    hedef_yol.write_bytes(res.content)
    return hedef_yol


def ses_sure_hesapla(ses_yolu: Path) -> float:
    """FFmpeg kullanarak ses dosyasının tam süresini (saniye) döner."""
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-i", str(ses_yolu)]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    # Duration: 00:00:04.56 çıktısını ara
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if not m:
        log.warning(f"Süre okunamadı: {ses_yolu}, varsayılan 5.0 sn veriliyor.")
        return 5.0

    saat, dakika, saniye = m.groups()
    toplam_sn = (int(saat) * 3600) + (int(dakika) * 60) + float(saniye)
    return toplam_sn


def ayet_seslerini_birlestir(sure_no: int, ayet_listesi: List[int], cikti_adi: Optional[str] = None) -> Path:
    """
    Birden fazla ayetin ses dosyasını sırayla indirir ve tek bir MP3 dosyasında birleştirir.
    """
    indirilen_yollar: List[Path] = []
    for ayet_no in ayet_listesi:
        yol = ayet_sesi_indir(sure_no, ayet_no)
        indirilen_yollar.append(yol)

    if len(indirilen_yollar) == 1:
        return indirilen_yollar[0]

    if not cikti_adi:
        ayet_str = "_".join(str(a) for a in ayet_listesi)
        cikti_adi = f"birlestirilmis_{sure_no}_{ayet_str}.mp3"

    cikti_yolu = SES_DIZINI / cikti_adi
    exe = imageio_ffmpeg.get_ffmpeg_exe()

    # FFmpeg concat demuxer için liste dosyası oluştur
    liste_yolu = SES_DIZINI / "concat_listesi.txt"
    with open(liste_yolu, "w", encoding="utf-8") as f:
        for p in indirilen_yollar:
            f.write(f"file '{p.absolute()}'\n")

    cmd = [
        exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(liste_yolu),
        "-c", "copy",
        str(cikti_yolu),
    ]

    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if liste_yolu.exists():
        liste_yolu.unlink()

    return cikti_yolu


_ZAMAN_CACHE: Dict[int, dict] = {}


def ayet_kelime_zamanlari_getir(sure_no: int, ayet_no: int) -> List[Tuple[int, float, float]]:
    """
    Şeyh Mişari Râşid el-Afâsî için yerel repodaki (data/zamanlar/sure_{sure_no}.json)
    tescilli kelime başlangıç/bitiş zaman damgalarını döner.
    114 sûrenin tamamı yerel repoda saklandığı için harici API bağımlılığı ve gecikmesi yoktur.
    Dönen her eleman: (kelime_indeksi_0_tabanli, baslangic_sn, bitis_sn)
    """
    global _ZAMAN_CACHE
    if sure_no in _ZAMAN_CACHE:
        data = _ZAMAN_CACHE[sure_no]
    else:
        zaman_klasoru = KOK_DIZIN / "data" / "zamanlar"
        cache_dosyasi = zaman_klasoru / f"sure_{sure_no}.json"
        data = None
        if cache_dosyasi.exists():
            try:
                import json
                data = json.loads(cache_dosyasi.read_text(encoding="utf-8"))
                _ZAMAN_CACHE[sure_no] = data
            except Exception as e:
                log.warning(f"Zaman önbelleği okunamadı: {e}")

        if not data:
            url = f"https://api.qurancdn.com/api/qdc/audio/reciters/7/audio_files?chapter={sure_no}&segments=true"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    import json
                    cache_dosyasi.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                    _ZAMAN_CACHE[sure_no] = data
                    log.info(f"QuranCDN zaman damgaları indirildi ve önbelleğe alındı (Sûre: {sure_no})")
                else:
                    log.warning(f"QuranCDN zaman damgaları yanıt kodu: {res.status_code}")
            except Exception as e:
                log.warning(f"QuranCDN zaman damgaları alınamadı ({url}): {e}")
                return []

    if not data:
        return []

    af = data.get("audio_files", [{}])[0]
    verse_key = f"{sure_no}:{ayet_no}"
    for vt in af.get("verse_timings", []):
        if vt.get("verse_key") == verse_key:
            segments = vt.get("segments", [])
            if segments and len(segments[0]) >= 2:
                # EveryAyah bağımsız ayet ses dosyası daima ilk kelimenin telaffuzuyla başlar (segments[0][1]).
                # timestamp_from kaba sûre imleci olduğundan segment başlangıcından 1.7 saniyeye kadar sapabilir.
                ayah_start = segments[0][1]
            else:
                ayah_start = vt.get("timestamp_from", 0)

            ayah_end = vt.get("timestamp_to", ayah_start)
            zamanlar = []
            for seg in segments:
                if len(seg) >= 3:
                    w_idx = int(seg[0]) - 1  # 1-based -> 0-based
                    s_sec = max(0.0, (seg[1] - ayah_start) / 1000.0)
                    e_sec = max(s_sec + 0.05, (seg[2] - ayah_start) / 1000.0)
                elif len(seg) == 2:
                    w_idx = len(zamanlar)
                    s_sec = max(0.0, (seg[1] - ayah_start) / 1000.0)
                    e_sec = max(s_sec + 0.05, (ayah_end - ayah_start) / 1000.0)
                else:
                    continue
                zamanlar.append((w_idx, round(s_sec, 3), round(e_sec, 3)))
            return zamanlar

    return []

