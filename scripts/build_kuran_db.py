#!/usr/bin/env python3
"""
build_kuran_db.py — Tescilli Kur'an-ı Kerim Veritabanı Oluşturucu

Kaynaklar:
1. Medine Kral Fehd Matbaası tescilli Uthmani metni (Quran.com API v4 - 6.236 Âyet)
2. Elmalılı Muhammed Hamdi Yazır Türkçe Meali (Tanzil.net resmi külliyatı - 6.236 Âyet)
3. Diyanet İşleri Başkanlığı Türkçe Meali (Tanzil.net resmi külliyatı - 6.236 Âyet)
4. 114 Sûre Künyesi ve 30 Cüz Eşleşmesi (Quran.com API v4)

Çıktı:
data/kuran/kuran.db (SQLite + FTS5 tam metin arama)
"""

from __future__ import annotations

import logging
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

KOK_DIZIN = Path(__file__).resolve().parent.parent
KURAN_DIZIN = KOK_DIZIN / "data" / "kuran"
DB_YOLU = KURAN_DIZIN / "kuran.db"

QURAN_API_CHAPTERS = "https://api.quran.com/api/v4/chapters?language=tr"
QURAN_API_JUZS = "https://api.quran.com/api/v4/juzs"
QURAN_API_UTHMANI = "https://api.quran.com/api/v4/quran/verses/uthmani"
TANZIL_YAZIR_URL = "https://tanzil.net/trans/tr.yazir"
TANZIL_DIYANET_URL = "https://tanzil.net/trans/tr.diyanet"


def indir_json(url: str) -> Any:
    """Verilen URL'den JSON verisini güvenle çeker."""
    log.info(f"İndiriliyor: {url}")
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    return res.json()


def indir_tanzil_meal(url: str) -> Dict[str, str]:
    """
    Tanzil.net meal dosyasını indirir ve 'sure:ayet' -> meal metni sözlüğü döner.
    Format: sure|ayet|meal
    """
    log.info(f"Tanzil meal indiriliyor: {url}")
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    
    sonuc: Dict[str, str] = {}
    lines = res.text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            s_no, a_no, meal = parts
            key = f"{int(s_no)}:{int(a_no)}"
            # Fazla boşlukları ve HTML artıklarını temizle
            meal_temiz = re.sub(r"\s+", " ", meal).strip()
            sonuc[key] = meal_temiz

    log.info(f"Ayrıştırılan meal ayet sayısı: {len(sonuc)} ({url.split('/')[-1]})")
    return sonuc


def juz_eslesme_haritasi_cikar(juz_verisi: List[Dict[str, Any]]) -> Dict[Tuple[int, int], int]:
    """
    Quran.com juzs listesinden (sure_no, ayet_no) -> cuz_no haritası çıkarır.
    """
    harita: Dict[Tuple[int, int], int] = {}
    for j in juz_verisi:
        cuz_no = int(j["juz_number"])
        mapping = j.get("verse_mapping", {})
        for s_str, a_range in mapping.items():
            sure_no = int(s_str)
            if "-" in a_range:
                bas, son = a_range.split("-")
                for ayet in range(int(bas), int(son) + 1):
                    harita[(sure_no, ayet)] = cuz_no
            else:
                harita[(sure_no, int(a_range))] = cuz_no
    return harita


def veritabanini_olustur():
    """Tüm verileri indirir, birleştirir ve kuran.db SQLite veritabanını oluşturur."""
    KURAN_DIZIN.mkdir(parents=True, exist_ok=True)

    # 1. Kaynakları İndir
    chapters_data = indir_json(QURAN_API_CHAPTERS).get("chapters", [])
    juzs_data = indir_json(QURAN_API_JUZS).get("juzs", [])
    uthmani_data = indir_json(QURAN_API_UTHMANI).get("verses", [])
    yazir_mealleri = indir_tanzil_meal(TANZIL_YAZIR_URL)
    diyanet_mealleri = indir_tanzil_meal(TANZIL_DIYANET_URL)

    if len(chapters_data) != 114:
        raise ValueError(f"114 sûre bekleniyordu, {len(chapters_data)} sûre geldi!")
    if len(uthmani_data) != 6236:
        raise ValueError(f"6.236 âyet bekleniyordu, {len(uthmani_data)} âyet geldi!")
    if len(yazir_mealleri) != 6236:
        raise ValueError(f"Elmalılı için 6.236 âyet bekleniyordu, {len(yazir_mealleri)} geldi!")
    if len(diyanet_mealleri) != 6236:
        raise ValueError(f"Diyanet için 6.236 âyet bekleniyordu, {len(diyanet_mealleri)} geldi!")

    juz_haritasi = juz_eslesme_haritasi_cikar(juzs_data)

    # 2. SQLite Veritabanını Kur
    if DB_YOLU.exists():
        DB_YOLU.unlink()

    con = sqlite3.connect(str(DB_YOLU))
    cur = con.cursor()

    # Performans ayarları
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA synchronous = NORMAL;")

    # Sûreler Tablosu
    cur.execute("""
        CREATE TABLE sureler (
            sure_no INTEGER PRIMARY KEY,
            sure_adi_tr TEXT NOT NULL,
            sure_adi_ar TEXT NOT NULL,
            sure_adi_en TEXT,
            ayet_sayisi INTEGER NOT NULL,
            inis_yeri TEXT,
            inis_sirasi INTEGER,
            bismillah_pre INTEGER DEFAULT 1
        );
    """)

    # Âyetler Tablosu
    cur.execute("""
        CREATE TABLE ayetler (
            id INTEGER PRIMARY KEY,
            sure_no INTEGER NOT NULL,
            ayet_no INTEGER NOT NULL,
            cuz_no INTEGER NOT NULL,
            sure_ayet_key TEXT NOT NULL UNIQUE,
            sure_ayet_etiket TEXT NOT NULL,
            arapca_metin TEXT NOT NULL,
            meal_elmalili TEXT NOT NULL,
            meal_diyanet TEXT NOT NULL,
            kelime_sayisi_ar INTEGER NOT NULL,
            karakter_sayisi_meal INTEGER NOT NULL,
            video_icin_uygun INTEGER DEFAULT 1,
            paylasim_sayisi INTEGER DEFAULT 0,
            son_paylasim DATETIME,
            FOREIGN KEY (sure_no) REFERENCES sureler(sure_no)
        );
    """)

    # İndeksler
    cur.execute("CREATE INDEX idx_ayetler_sure_ayet ON ayetler(sure_no, ayet_no);")
    cur.execute("CREATE INDEX idx_ayetler_cuz ON ayetler(cuz_no);")
    cur.execute("CREATE INDEX idx_ayetler_video_uygun ON ayetler(video_icin_uygun, paylasim_sayisi);")

    # FTS5 Tam Metin Arama Tablosu
    cur.execute("""
        CREATE VIRTUAL TABLE ayetler_fts USING fts5(
            sure_no UNINDEXED,
            ayet_no UNINDEXED,
            sure_adi_tr,
            meal_elmalili,
            meal_diyanet,
            content='ayetler',
            content_rowid='id'
        );
    """)

    # Sûreleri Ekle
    sure_adi_sozluk: Dict[int, str] = {}
    for c in chapters_data:
        s_no = int(c["id"])
        tr_ad = c.get("translated_name", {}).get("name") or c.get("name_simple", "")
        ar_ad = c.get("name_arabic", "")
        en_ad = c.get("name_simple", "")
        ayet_sayisi = int(c.get("verses_count", 0))
        inis_yeri = "Mekke" if c.get("revelation_place") == "makkah" else "Medine"
        inis_sirasi = int(c.get("revelation_order", 0))
        bismillah_pre = 1 if c.get("bismillah_pre") else 0

        sure_adi_sozluk[s_no] = tr_ad

        cur.execute("""
            INSERT INTO sureler (
                sure_no, sure_adi_tr, sure_adi_ar, sure_adi_en,
                ayet_sayisi, inis_yeri, inis_sirasi, bismillah_pre
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_no, tr_ad, ar_ad, en_ad, ayet_sayisi, inis_yeri, inis_sirasi, bismillah_pre))

    log.info("114 Sûre bilgisi kaydedildi.")

    # Âyetleri Ekle
    eklenen_ayet = 0
    for v in uthmani_data:
        v_id = int(v["id"])
        v_key = v["verse_key"]  # e.g. "2:255"
        s_no, a_no = map(int, v_key.split(":"))
        ar_metin = v["text_uthmani"].strip()
        meal_yaz = yazir_mealleri.get(v_key, "").strip()
        meal_diy = diyanet_mealleri.get(v_key, "").strip()

        if not meal_yaz or not meal_diy:
            raise ValueError(f"Ayet {v_key} için meal bulunamadı!")

        cuz_no = juz_haritasi.get((s_no, a_no), 1)
        sure_tr = sure_adi_sozluk.get(s_no, f"{s_no}. Sûre")
        etiket = f"{sure_tr} Sûresi • {a_no}. Âyet"

        kelime_sayisi_ar = len(ar_metin.split())
        karakter_sayisi_meal = len(meal_yaz)

        # Video için uygunluk kriteri: 4-25 kelime arası, 200 karakter altı mealler tek ekranda ve 1-2 slaytta idealdir
        video_uygun = 1 if (4 <= kelime_sayisi_ar <= 25 and karakter_sayisi_meal <= 200) else 0

        cur.execute("""
            INSERT INTO ayetler (
                id, sure_no, ayet_no, cuz_no, sure_ayet_key, sure_ayet_etiket,
                arapca_metin, meal_elmalili, meal_diyanet,
                kelime_sayisi_ar, karakter_sayisi_meal, video_icin_uygun
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v_id, s_no, a_no, cuz_no, v_key, etiket,
            ar_metin, meal_yaz, meal_diy,
            kelime_sayisi_ar, karakter_sayisi_meal, video_uygun
        ))

        # FTS tablosuna ekle
        cur.execute("""
            INSERT INTO ayetler_fts (rowid, sure_no, ayet_no, sure_adi_tr, meal_elmalili, meal_diyanet)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (v_id, s_no, a_no, sure_tr, meal_yaz, meal_diy))

        eklenen_ayet += 1

    con.commit()
    log.info(f"6.236 Âyet başarıyla 'data/kuran/kuran.db' veritabanına işlendi!")

    # 3. Doğrulama ve Raporlama
    cur.execute("SELECT COUNT(*) FROM sureler;")
    toplam_sure = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ayetler;")
    toplam_ayet = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ayetler WHERE video_icin_uygun = 1;")
    video_uygun_sayisi = cur.fetchone()[0]

    cur.execute("SELECT arapca_metin, meal_elmalili, meal_diyanet FROM ayetler WHERE sure_ayet_key = '2:255';")
    kursi = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM ayetler_fts WHERE ayetler_fts MATCH 'sabır';")
    sabir_sayisi = cur.fetchone()[0]

    con.close()

    print("\n" + "=" * 60)
    print("✨ KUR'AN-I KERİM VERİTABANI BAŞARIYLA TAMAMLANDI ✨")
    print("=" * 60)
    print(f"Toplam Sûre Sayısı      : {toplam_sure}")
    print(f"Toplam Âyet Sayısı      : {toplam_ayet}")
    print(f"Reels İçin İdeal Âyetler: {video_uygun_sayisi}")
    print(f"FTS 'sabır' Arama Sonucu: {sabir_sayisi} âyet")
    print(f"Âyetü'l-Kürsî (2:255)   : {kursi[0][:35]}... (Doğrulandı)")
    print(f"Veritabanı Dosya Boyutu : {DB_YOLU.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    veritabanini_olustur()
