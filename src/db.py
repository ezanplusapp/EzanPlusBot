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
from contextlib import contextmanager
DB_YOLU = KOK_DIZIN / DB_REL_PATH


@contextmanager
def baglanti_al():
    """SQLite veritabanı bağlantısı oluşturur ve işlem bitiminde güvenle kapatır."""
    DB_YOLU.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_YOLU))
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


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
        # Migration: youtube_post_id, facebook_post_id ve instagram_story_post_id yoksa ekle
        try:
            con.execute("ALTER TABLE paylasimlar ADD COLUMN youtube_post_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            con.execute("ALTER TABLE paylasimlar ADD COLUMN facebook_post_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            con.execute("ALTER TABLE paylasimlar ADD COLUMN instagram_story_post_id TEXT")
        except sqlite3.OperationalError:
            pass
        # Ayarlar tablosu (R2, entegrasyonlar vb. için esnek yapılandırma)
        con.execute("""
            CREATE TABLE IF NOT EXISTS ayarlar (
                anahtar TEXT PRIMARY KEY,
                deger TEXT
            )
        """)
        # Hızlı mükerrer arama için index
        con.execute("CREATE INDEX IF NOT EXISTS idx_kaynak ON paylasimlar(kaynak)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_durum ON paylasimlar(durum)")
        con.commit()


def ayar_getir(anahtar: str, varsayilan: str = "") -> str:
    """Veritabanındaki ayarlar tablosundan bir değeri çeker."""
    try:
        with baglanti_al() as con:
            row = con.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,)).fetchone()
            if row and row["deger"] is not None:
                return str(row["deger"]).strip()
    except Exception as e:
        log.debug(f"Veritabanından ayar çekilemedi ({anahtar}): {e}")
    return varsayilan


def ayar_kaydet(anahtar: str, deger: str) -> None:
    """Veritabanındaki ayarlar tablosuna bir değer kaydeder / günceller."""
    try:
        with baglanti_al() as con:
            con.execute(
                "INSERT INTO ayarlar (anahtar, deger) VALUES (?, ?) ON CONFLICT(anahtar) DO UPDATE SET deger=excluded.deger",
                (anahtar, deger),
            )
    except Exception as e:
        log.error(f"Veritabanına ayar kaydedilemedi ({anahtar}): {e}")



YAYIN_GECMISI_DOSYASI = KOK_DIZIN / "data" / "yayin_gecmisi.json"


def yayin_gecmisi_yukle() -> List[Dict[str, Any]]:
    """Git dostu JSON dosyasından yayın geçmişini yükler."""
    if not YAYIN_GECMISI_DOSYASI.exists():
        return []
    try:
        with open(YAYIN_GECMISI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Yayın geçmişi JSON okunamadı: {e}")
        return []


def yayin_gecmisi_kaydet(kayit: Dict[str, Any]):
    """Yeni yayınlanan içeriği Git dostu JSON geçmişine ekler veya günceller."""
    gecmis = yayin_gecmisi_yukle()
    kaynak = (kayit.get("kaynak") or kayit.get("baslik") or "").strip()
    if not kaynak:
        return

    veri = {
        "id": kayit.get("id"),
        "kategori": kayit.get("kategori", "ayet"),
        "kaynak": kaynak,
        "baslik": kayit.get("baslik"),
        "yayin_zamani": kayit.get("yayin_zamani") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "instagram_post_id": kayit.get("instagram_post_id"),
        "instagram_story_post_id": kayit.get("instagram_story_post_id"),
        "threads_post_id": kayit.get("threads_post_id"),
        "youtube_post_id": kayit.get("youtube_post_id"),
        "facebook_post_id": kayit.get("facebook_post_id"),
        "tiktok_post_id": kayit.get("tiktok_post_id"),
    }

    # Eğer kaynak zaten varsa güncelle, yoksa sona ekle
    bulundu = False
    for idx, item in enumerate(gecmis):
        if item.get("kaynak") == kaynak or (kayit.get("id") and item.get("id") == kayit.get("id")):
            gecmis[idx].update({k: v for k, v in veri.items() if v is not None})
            bulundu = True
            break

    if not bulundu:
        gecmis.append(veri)

    YAYIN_GECMISI_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    with open(YAYIN_GECMISI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)
    log.info(f"Yayın geçmişi JSON güncellendi: {kaynak}")


def yayin_gecmisinden_sil(paylasim_id: int) -> bool:
    """Paylaşım ID'sine göre JSON geçmişinden kaydı temizler."""
    gecmis = yayin_gecmisi_yukle()
    yeni_gecmis = [item for item in gecmis if item.get("id") != paylasim_id]
    if len(yeni_gecmis) != len(gecmis):
        try:
            with open(YAYIN_GECMISI_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(yeni_gecmis, f, ensure_ascii=False, indent=2)
            log.info(f"Paylaşım #{paylasim_id} JSON yayın geçmişinden silindi.")
            return True
        except Exception as e:
            log.warning(f"Yayın geçmişi silme hatası: {e}")
    return False



def son_paylasilan_kaynaklar(limit: int = 90, kategori: Optional[str] = None) -> List[str]:
    """Son paylaşılan ayet/hadis/dua/kelime kaynaklarını döner (hem SQLite hem JSON geçmişinden)."""
    kaynaklar = set()
    # 1. JSON geçmişinden al
    for item in yayin_gecmisi_yukle():
        if kategori and item.get("kategori") != kategori:
            continue
        k = item.get("kaynak") or item.get("baslik")
        if k:
            kaynaklar.add(k.strip())
        b = item.get("baslik")
        if b:
            kaynaklar.add(b.strip())

    # 2. SQLite'tan al
    try:
        with baglanti_al() as con:
            if kategori:
                cur = con.execute(
                    "SELECT DISTINCT kaynak, baslik FROM paylasimlar WHERE durum = 'yayinlandi' AND kategori = ? ORDER BY id DESC LIMIT ?",
                    (kategori, limit),
                )
            else:
                cur = con.execute(
                    "SELECT DISTINCT kaynak, baslik FROM paylasimlar WHERE durum = 'yayinlandi' ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
            for row in cur.fetchall():
                if row[0]:
                    kaynaklar.add(row[0].strip())
                if len(row) > 1 and row[1]:
                    kaynaklar.add(row[1].strip())
    except Exception:
        pass

    return sorted(list(kaynaklar))


def kaynak_daha_once_paylasildi_mi(kaynak: str) -> bool:
    """Belirtilen ayet veya hadis kaynağının daha önce paylaşılıp paylaşılmadığını denetler."""
    if not kaynak:
        return False
    
    k_temiz = kaynak.strip().lower()

    # 1. JSON geçmişinde ara
    for item in yayin_gecmisi_yukle():
        k = (item.get("kaynak") or item.get("baslik") or "").strip().lower()
        if k and (k in k_temiz or k_temiz in k):
            return True

    # 2. SQLite'ta ara
    with baglanti_al() as con:
        cur = con.execute("SELECT COUNT(*) FROM paylasimlar WHERE durum = 'yayinlandi' AND kaynak LIKE ?", (f"%{kaynak.strip()}%",))
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
    instagram_story_post_id: Optional[str] = None,
    telegram_mesaj_id: Optional[int] = None,
    youtube_post_id: Optional[str] = None,
    tiktok_post_id: Optional[str] = None,
    threads_post_id: Optional[str] = None,
    facebook_post_id: Optional[str] = None,
    yayin_zamani: Optional[str] = None,
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
        if instagram_story_post_id is not None:
            updates.append("instagram_story_post_id = ?")
            params.append(instagram_story_post_id)
        if telegram_mesaj_id is not None:
            updates.append("telegram_mesaj_id = ?")
            params.append(telegram_mesaj_id)
        if youtube_post_id is not None:
            updates.append("youtube_post_id = ?")
            params.append(youtube_post_id)
        if tiktok_post_id is not None:
            updates.append("tiktok_post_id = ?")
            params.append(tiktok_post_id)
        if threads_post_id is not None:
            updates.append("threads_post_id = ?")
            params.append(threads_post_id)
        if facebook_post_id is not None:
            updates.append("facebook_post_id = ?")
            params.append(facebook_post_id)
        if yayin_zamani is not None:
            updates.append("yayin_zamani = ?")
            params.append(yayin_zamani)
        elif yeni_durum == "yayinlandi":
            updates.append("yayin_zamani = CURRENT_TIMESTAMP")

        params.append(paylasim_id)
        con.execute(f"UPDATE paylasimlar SET {', '.join(updates)} WHERE id = ?", params)
        con.commit()

    if yeni_durum == "yayinlandi":
        try:
            k = paylasim_getir(paylasim_id)
            if k:
                yayin_gecmisi_kaydet(k)
                kat = k.get("kategori")
                if kat == "ayet":
                    from . import kuran_db
                    kaynak_str = k.get("kaynak") or k.get("baslik") or ""
                    cozum = kuran_db.ayet_anahtari_cozumle(kaynak_str)
                    if cozum:
                        kuran_db.ayeti_paylasildi_isaretle(cozum[0], cozum[1])
                elif kat == "hadis":
                    from . import hadis_db
                    hadis_db.hadisi_paylasildi_isaretle_metin(
                        baslik=k.get("baslik"),
                        kaynak=k.get("kaynak"),
                        metin=k.get("turkce_metin"),
                    )
                elif kat == "dua":
                    from . import dua_db
                    dua_db.duayi_paylasildi_isaretle_baslik(k.get("baslik") or k.get("kaynak") or "")
                elif kat == "kelime":
                    from . import kelime_db
                    kavram = k.get("baslik", "").replace("Kur'an Sözlüğü •", "").strip()
                    kelime_db.kelimeyi_paylasildi_isaretle_kavram(kavram)
        except Exception as e:
            log.warning(f"JSON yayın geçmişi veya külliyat kaydedilemedi: {e}")
    elif yeni_durum == "yayindan_kaldirildi":
        try:
            yayin_gecmisinden_sil(paylasim_id)
        except Exception as e:
            log.warning(f"JSON yayın geçmişinden silinemedi: {e}")
            log.warning(f"JSON yayın geçmişi kaydedilemedi: {e}")


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


def zamanlanmis_paylasimlari_getir() -> List[Dict[str, Any]]:
    """Yayın saati gelmiş (yayin_zamani <= simdi) ve durumu 'zamanlandi' olan kayıtları döner."""
    simdi_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with baglanti_al() as con:
        cur = con.execute(
            "SELECT * FROM paylasimlar WHERE durum = 'zamanlandi' AND (yayin_zamani <= ? OR yayin_zamani <= CURRENT_TIMESTAMP) ORDER BY yayin_zamani ASC",
            (simdi_str,),
        )
        sonuclar = []
        for row in cur.fetchall():
            d = dict(row)
            if d.get("gorsel_yollari"):
                try:
                    d["gorsel_yollari"] = json.loads(d["gorsel_yollari"])
                except Exception:
                    pass
            sonuclar.append(d)
        return sonuclar


def paylasim_guncelle(paylasim_id: int, **kwargs) -> bool:
    """Paylaşım tablosundaki belirtilen sütunları (caption, turkce_metin, video_yolu vb.) günceller."""
    if not kwargs:
        return False
    with baglanti_al() as con:
        sutunlar = []
        params = []
        for k, v in kwargs.items():
            if k == "gorsel_yollari" and isinstance(v, list):
                sutunlar.append(f"{k} = ?")
                params.append(json.dumps(v))
            else:
                sutunlar.append(f"{k} = ?")
                params.append(v)
        params.append(paylasim_id)
        con.execute(f"UPDATE paylasimlar SET {', '.join(sutunlar)} WHERE id = ?", params)
        con.commit()
    return True


# Modül yüklendiğinde tablolar hazır olsun
tabloları_hazirla()
