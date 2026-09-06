#!/usr/bin/env python3
"""
download_all_timings.py — Ezan Plus Kur'an Tilaveti Kelime Zaman Damgası İndirici

Tüm 114 sûre ve 6.236 âyet için Şeyh Mişari Râşid el-Afâsî (Reciter ID: 7)
resmi stüdyo kelime başlangıç/bitiş zaman damgalarını QuranCDN'den indirir
ve yerel repoya (data/zamanlar/sure_{1..114}.json) kaydeder.

Bu sayede video render motoru harici hiçbir API'ye bağımlı kalmaz;
tamamen offline, sıfır gecikme ve %100 kararlılıkla çalışır.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

KOK_DIZIN = Path(__file__).resolve().parent.parent
ZAMAN_DIZINI = KOK_DIZIN / "data" / "zamanlar"
ZAMAN_DIZINI.mkdir(parents=True, exist_ok=True)

DB_YOLU = KOK_DIZIN / "data" / "kuran" / "kuran.db"

API_BASE_URL = "https://api.qurancdn.com/api/qdc/audio/reciters/7/audio_files"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def sure_bilgilerini_al() -> List[Tuple[int, str, int]]:
    """kuran.db üzerinden 114 sûrenin no, isim ve âyet sayısını döner."""
    if not DB_YOLU.exists():
        log.error(f"Kur'an veritabanı bulunamadı: {DB_YOLU}")
        sys.exit(1)

    con = sqlite3.connect(str(DB_YOLU))
    cur = con.cursor()
    cur.execute("SELECT sure_no, sure_adi_tr, ayet_sayisi FROM sureler ORDER BY sure_no")
    rows = cur.fetchall()
    con.close()
    return rows


def sure_dosyasi_gecerli_mi(sure_no: int, beklenen_ayet_sayisi: int) -> bool:
    """Mevcut dosyanın tüm ayetleri içerip içermediğini kontrol eder."""
    dosya = ZAMAN_DIZINI / f"sure_{sure_no}.json"
    if not dosya.exists() or dosya.stat().st_size < 100:
        return False

    try:
        data = json.loads(dosya.read_text(encoding="utf-8"))
        audio_files = data.get("audio_files", [])
        if not audio_files:
            return False
        verse_timings = audio_files[0].get("verse_timings", [])
        return len(verse_timings) >= beklenen_ayet_sayisi
    except Exception:
        return False


def sure_zamanlarini_indir(sure_no: int, sure_adi: str, ayet_sayisi: int, session: requests.Session) -> bool:
    """Belirtilen sûrenin zaman damgalarını QuranCDN'den indirir."""
    url = f"{API_BASE_URL}?chapter={sure_no}&segments=true"
    hedef_dosya = ZAMAN_DIZINI / f"sure_{sure_no}.json"

    for deneme in range(1, 4):
        try:
            res = session.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200:
                data = res.json()
                audio_files = data.get("audio_files", [])
                if not audio_files:
                    log.warning(f"Sûre {sure_no} ({sure_adi}): audio_files boş!")
                    time.sleep(1)
                    continue

                vt = audio_files[0].get("verse_timings", [])
                if len(vt) < ayet_sayisi:
                    log.warning(f"Sûre {sure_no} ({sure_adi}): Eksik âyet zamanı! (Beklenen: {ayet_sayisi}, Gelen: {len(vt)})")

                # Kompakt ve düzenli JSON kaydet
                hedef_dosya.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                log.info(f"✅ Sûre {sure_no:3d}/114: {sure_adi:<20} ({len(vt)}/{ayet_sayisi} âyet zamanı kaydedildi)")
                return True
            elif res.status_code == 429:
                log.warning(f"Sûre {sure_no} ({sure_adi}): Hız sınırı (429)! Bekleniyor (deneme {deneme})...")
                time.sleep(3 * deneme)
            else:
                log.warning(f"Sûre {sure_no} ({sure_adi}): HTTP {res.status_code} (deneme {deneme})")
                time.sleep(1.5)
        except Exception as e:
            log.warning(f"Sûre {sure_no} ({sure_adi}): Hata ({e}), tekrar deneniyor ({deneme}/3)...")
            time.sleep(1.5)

    log.error(f"❌ Sûre {sure_no} ({sure_adi}) indirilemedi!")
    return False


def main():
    log.info("Kur'an-ı Kerim Kelime Zaman Damgaları İndirme Motoru Başlatılıyor...")
    sureler = sure_bilgilerini_al()
    toplam_sure = len(sureler)
    toplam_hedef_ayet = sum(s[2] for s in sureler)
    log.info(f"Hedef: {toplam_sure} sûre, toplam {toplam_hedef_ayet} âyet")

    indirilecekler = []
    mevcut_sayisi = 0

    for sure_no, sure_adi, ayet_sayisi in sureler:
        if sure_dosyasi_gecerli_mi(sure_no, ayet_sayisi):
            mevcut_sayisi += 1
        else:
            indirilecekler.append((sure_no, sure_adi, ayet_sayisi))

    log.info(f"Mevcut ve geçerli sûre dosyası: {mevcut_sayisi}/{toplam_sure}")
    log.info(f"İndirilecek sûre sayısı: {len(indirilecekler)}")

    if indirilecekler:
        session = requests.Session()
        # Sunucuyu yormadan kontrollü 4 thread ile indir
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(sure_zamanlarini_indir, s_no, s_ad, a_sayi, session): (s_no, s_ad)
                for s_no, s_ad, a_sayi in indirilecekler
            }
            for future in as_completed(futures):
                future.result()

    # Genel Denetim ve Doğrulama
    log.info("\n--- GENEL KONTROL VE DOĞRULAMA ---")
    basarili_sure = 0
    toplam_kayitli_ayet = 0
    toplam_segment = 0

    for sure_no, sure_adi, ayet_sayisi in sureler:
        dosya = ZAMAN_DIZINI / f"sure_{sure_no}.json"
        if not dosya.exists():
            log.error(f"Eksik dosya: {dosya}")
            continue

        try:
            d = json.loads(dosya.read_text(encoding="utf-8"))
            vt = d.get("audio_files", [{}])[0].get("verse_timings", [])
            basarili_sure += 1
            toplam_kayitli_ayet += len(vt)
            for item in vt:
                toplam_segment += len(item.get("segments", []))
        except Exception as e:
            log.error(f"Dosya okuma hatası {dosya}: {e}")

    toplam_boyut_mb = sum(f.stat().st_size for f in ZAMAN_DIZINI.glob("sure_*.json")) / (1024 * 1024)

    log.info(f"Tamamlanan Sûre Sayısı: {basarili_sure} / {toplam_sure}")
    log.info(f"Doğrulanan Âyet Sayısı: {toplam_kayitli_ayet} / {toplam_hedef_ayet}")
    log.info(f"Toplam Kelime Segmenti: {toplam_segment:,} kelime")
    log.info(f"Yerel Disk Boyutu: {toplam_boyut_mb:.2f} MB")

    if basarili_sure == 114 and toplam_kayitli_ayet == toplam_hedef_ayet:
        log.info("🎉 TEBRİKLER! Kur'an-ı Kerim'in tamamı (6.236 âyet) kelime kelime repoya kaydedildi!")
    else:
        log.warning(f"Eksikler var! Başarılı: {basarili_sure}/114, Ayet: {toplam_kayitli_ayet}/{toplam_hedef_ayet}")


if __name__ == "__main__":
    main()
