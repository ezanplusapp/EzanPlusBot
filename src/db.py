"""
db.py — Ezan Plus Bot SQLite Veritabanı Modülü
İçeriklerin kaydedilmesi, mükerrer kontrolü, onay durumları ve yayın takibi.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .ayar import KOK_DIZIN, AYARLAR

log = logging.getLogger(__name__)

DB_REL_PATH = AYARLAR.get("genel", {}).get("db_yolu", "data/bot.db")
DB_YOLU = KOK_DIZIN / DB_REL_PATH


def baglanti_al() -> sqlite3.Connection:
    """SQLite veritabanı bağlantısı oluşturur."""
    DB_YOLU.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_YOLU))
    con.row_factory = sqlite3.Row
    return con


def tabloları_hazirla():
    """Gerekli tabloları oluşturur."""
    with baglanti_al() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS paylasimlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori TEXT NOT NULL,
                format TEXT NOT NULL,
                baslik TEXT,
                arapca_metin TEXT,
                turkce_metin TEXT NOT NULL,
                kaynak TEXT,
                tefekkur TEXT,
                caption TEXT,
                etiketler TEXT,
                gorsel_yollari TEXT,
                video_yolu TEXT,
                ses_yolu TEXT,
                durum TEXT DEFAULT 'taslak',
                telegram_mesaj_id INTEGER,
                instagram_post_id TEXT,
                threads_post_id TEXT,
                tiktok_post_id TEXT,
                youtube_post_id TEXT,
                olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                yayin_zamani TIMESTAMP,
                hata_mesaji TEXT
            )
        """)
        # Migration: youtube_post_id yoksa ekle
        try:
            con.execute("ALTER TABLE paylasimlar ADD COLUMN youtube_post_id TEXT")
        except sqlite3.OperationalError:
            pass
        # Hızlı mükerrer arama için index
        con.execute("CREATE INDEX IF NOT EXISTS idx_kaynak ON paylasimlar(kaynak)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_durum ON paylasimlar(durum)")
        con.commit()


def kaynak_daha_once_paylasildi_mi(kaynak: str) -> bool:
    """Belirtilen ayet veya hadis kaynağının daha önce paylaşılıp paylaşılmadığını denetler."""
    if not kaynak:
        return False
    with baglanti_al() as con:
        cur = con.execute("SELECT COUNT(*) FROM paylasimlar WHERE kaynak = ?", (kaynak.strip(),))
        sayi = cur.fetchone()[0]
        return sayi > 0


def paylasim_ekle(
    kategori: str,
    format_tipi: str,
    turkce_metin: str,
    baslik: Optional[str] = None,
    arapca_metin: Optional[str] = None,
    kaynak: Optional[str] = None,
    tefekkur: Optional[str] = None,
    caption: Optional[str] = None,
    etiketler: Optional[str] = None,
    gorsel_yollari: Optional[List[str]] = None,
    video_yolu: Optional[str] = None,
    ses_yolu: Optional[str] = None,
    durum: str = "taslak",
) -> int:
    """Yeni bir içerik kaydı oluşturur ve id'sini döner."""
    gorsel_json = json.dumps(gorsel_yollari or [], ensure_ascii=False)
    with baglanti_al() as con:
        cur = con.execute(
            """
            INSERT INTO paylasimlar (
                kategori, format, baslik, arapca_metin, turkce_metin,
                kaynak, tefekkur, caption, etiketler, gorsel_yollari,
                video_yolu, ses_yolu, durum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kategori,
                format_tipi,
                baslik,
                arapca_metin,
                turkce_metin,
                kaynak,
                tefekkur,
                caption,
                etiketler,
                gorsel_json,
                video_yolu,
                ses_yolu,
                durum,
            ),
        )
        con.commit()
        return cur.lastrowid


def durum_guncelle(
    paylasim_id: int,
    yeni_durum: str,
    hata_mesaji: Optional[str] = None,
    instagram_post_id: Optional[str] = None,
    telegram_mesaj_id: Optional[int] = None,
    youtube_post_id: Optional[str] = None,
    tiktok_post_id: Optional[str] = None,
):
    """Paylaşımın durumunu günceller."""
    with baglanti_al() as con:
        updates = ["durum = ?"]
        params = [yeni_durum]

        if hata_mesaji is not None:
            updates.append("hata_mesaji = ?")
            params.append(hata_mesaji)
        if instagram_post_id is not None:
            updates.append("instagram_post_id = ?")
            params.append(instagram_post_id)
        if telegram_mesaj_id is not None:
            updates.append("telegram_mesaj_id = ?")
            params.append(telegram_mesaj_id)
        if youtube_post_id is not None:
            updates.append("youtube_post_id = ?")
            params.append(youtube_post_id)
        if tiktok_post_id is not None:
            updates.append("tiktok_post_id = ?")
            params.append(tiktok_post_id)
        if yeni_durum == "yayinlandi":
            updates.append("yayin_zamani = CURRENT_TIMESTAMP")

        params.append(paylasim_id)
        con.execute(f"UPDATE paylasimlar SET {', '.join(updates)} WHERE id = ?", params)
        con.commit()


def paylasim_getir(paylasim_id: int) -> Optional[Dict[str, Any]]:
    """Tek bir paylaşım kaydını döner."""
    with baglanti_al() as con:
        cur = con.execute("SELECT * FROM paylasimlar WHERE id = ?", (paylasim_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("gorsel_yollari"):
            d["gorsel_yollari"] = json.loads(d["gorsel_yollari"])
        return d


# Modül yüklendiğinde tablolar hazır olsun
tabloları_hazirla()
