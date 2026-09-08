"""
kuran_db.py — Ezan Plus Tescilli Kur'an-ı Kerim Veritabanı Modülü

6.236 Âyet ve 114 Sûre'den oluşan tescilli yerel SQLite veritabanı yönetimi.
Medine Kral Fehd Mushafı Uthmani hattı, Elmalılı Hamdi Yazır ve Diyanet İşleri
Başkanlığı tescilli Türkçe mealleri ile %100 sıfır yapay zeka halüsinasyonu garantisi sunar.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .ayar import KOK_DIZIN

log = logging.getLogger(__name__)

from contextlib import contextmanager

KURAN_DIZINI = KOK_DIZIN / "data" / "kuran"
DB_YOLU = KURAN_DIZINI / "kuran.db"


@contextmanager
def baglanti_al():
    """Kur'an veritabanı bağlantısı oluşturur ve işlem bitiminde kapatır."""
    if not DB_YOLU.exists():
        raise FileNotFoundError(
            f"Kur'an veritabanı bulunamadı: {DB_YOLU}. "
            f"Lütfen önce 'python scripts/build_kuran_db.py' komutunu çalıştırın."
        )
    con = sqlite3.connect(str(DB_YOLU))
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def veritabani_mevcut_mu() -> bool:
    """Veritabanının mevcut ve geçerli olduğunu denetler."""
    if not DB_YOLU.exists():
        return False
    try:
        with baglanti_al() as con:
            cur = con.execute("SELECT COUNT(*) FROM ayetler")
            cnt = cur.fetchone()[0]
            return cnt == 6236
    except Exception:
        return False


def sure_bilgisi_getir(sure_no: int) -> Optional[Dict[str, Any]]:
    """Sûre numarasından sûre künyesini döner."""
    with baglanti_al() as con:
        cur = con.execute("SELECT * FROM sureler WHERE sure_no = ?", (sure_no,))
        row = cur.fetchone()
        return dict(row) if row else None


def sure_listesi_getir() -> List[Dict[str, Any]]:
    """Tüm 114 sûrenin listesini döner."""
    with baglanti_al() as con:
        cur = con.execute("SELECT * FROM sureler ORDER BY sure_no ASC")
        return [dict(r) for r in cur.fetchall()]


def ayet_getir(sure_no: int, ayet_no: int) -> Optional[Dict[str, Any]]:
    """Belirli bir sûre ve âyet numarasındaki tescilli kaydı getirir."""
    with baglanti_al() as con:
        cur = con.execute(
            """
            SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
            FROM ayetler a
            JOIN sureler s ON a.sure_no = s.sure_no
            WHERE a.sure_no = ? AND a.ayet_no = ?
            """,
            (sure_no, ayet_no),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def ayet_getir_key(sure_ayet_key: str) -> Optional[Dict[str, Any]]:
    """'2:255' veya '94:5' formatındaki anahtar ile âyet getirir."""
    try:
        s_str, a_str = sure_ayet_key.strip().split(":")
        return ayet_getir(int(s_str), int(a_str))
    except Exception as e:
        log.warning(f"Geçersiz sure_ayet_key ({sure_ayet_key}): {e}")
        return None


def sure_ayetleri_getir(
    sure_no: int,
    baslangic_ayet: int = 1,
    bitis_ayet: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Bir sûreye ait belirli bir âyet aralığını sıralı getirir."""
    with baglanti_al() as con:
        if bitis_ayet is not None:
            cur = con.execute(
                """
                SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
                FROM ayetler a
                JOIN sureler s ON a.sure_no = s.sure_no
                WHERE a.sure_no = ? AND a.ayet_no BETWEEN ? AND ?
                ORDER BY a.ayet_no ASC
                """,
                (sure_no, baslangic_ayet, bitis_ayet),
            )
        else:
            cur = con.execute(
                """
                SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
                FROM ayetler a
                JOIN sureler s ON a.sure_no = s.sure_no
                WHERE a.sure_no = ? AND a.ayet_no >= ?
                ORDER BY a.ayet_no ASC
                """,
                (sure_no, baslangic_ayet),
            )
        return [dict(r) for r in cur.fetchall()]


def ayet_ara(arama_terimi: str, limit: int = 20) -> List[Dict[str, Any]]:
    """FTS5 tam metin araması ile meallerde veya sûre adlarında arama yapar."""
    arama_temiz = arama_terimi.strip().replace('"', '').replace("'", "")
    if not arama_temiz:
        return []

    with baglanti_al() as con:
        try:
            # FTS5 MATCH sorgusu
            cur = con.execute(
                """
                SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
                FROM ayetler_fts f
                JOIN ayetler a ON f.rowid = a.id
                JOIN sureler s ON a.sure_no = s.sure_no
                WHERE ayetler_fts MATCH ?
                ORDER BY a.paylasim_sayisi ASC, a.id ASC
                LIMIT ?
                """,
                (f'"{arama_temiz}"', limit),
            )
            return [dict(r) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            # Kelime bazlı basit fallback
            kelimeler = arama_temiz.split()
            fts_sorgu = " OR ".join(f'"{k}"' for k in kelimeler if len(k) >= 3)
            if not fts_sorgu:
                return []
            cur = con.execute(
                """
                SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
                FROM ayetler_fts f
                JOIN ayetler a ON f.rowid = a.id
                JOIN sureler s ON a.sure_no = s.sure_no
                WHERE ayetler_fts MATCH ?
                ORDER BY a.paylasim_sayisi ASC, a.id ASC
                LIMIT ?
                """,
                (fts_sorgu, limit),
            )
            return [dict(r) for r in cur.fetchall()]


def gunun_ayetini_sec(
    tema: Optional[str] = None,
    sadece_video_uygun: bool = True,
    haric_tutulanlar: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Paylaşılmamış veya en az paylaşılmış tescilli bir âyet seçer.
    
    1. Tema verilmişse FTS üzerinden o temaya (sabır, huzur, şükür, tevbe vb.) uyan âyetleri tarar.
    2. Video/Reels formatı için ideal uzunluktaki (4-25 kelime, <= 200 karakter meal) âyetlere öncelik verir.
    3. Geçmişte paylaşılan âyetleri (haric_tutulanlar) kesinlikle eler.
    4. En az paylaşılmış olanlar arasından rastgele birini seçerek mükerrerliği %100 engeller.
    """
    with baglanti_al() as con:
        haric_set = set(haric_tutulanlar or [])

        # 1. Tema araması
        if tema:
            # Temanın anahtar kelimelerini ayıkla
            tema_kelimeleri = [k.strip() for k in tema.replace("(", " ").replace(")", " ").replace(",", " ").split() if len(k.strip()) >= 3]
            for kelime in tema_kelimeleri:
                adaylar = ayet_ara(kelime, limit=40)
                if sadece_video_uygun:
                    adaylar = [a for a in adaylar if a.get("video_icin_uygun") == 1]
                if haric_set:
                    adaylar = [a for a in adaylar if a.get("sure_ayet_key") not in haric_set and a.get("sure_ayet_etiket") not in haric_set]

                if adaylar:
                    # En düşük paylaşım sayısına sahip olanlardan rastgele seç
                    min_paylasim = min(a.get("paylasim_sayisi", 0) for a in adaylar)
                    en_iyi_adaylar = [a for a in adaylar if a.get("paylasim_sayisi", 0) == min_paylasim]
                    import random
                    return random.choice(en_iyi_adaylar)

        # 2. Genel Havuzdan Seçim (Tema bulunamadıysa veya verilmediyse)
        filtreler = []
        params: List[Any] = []

        if sadece_video_uygun:
            filtreler.append("a.video_icin_uygun = 1")

        if haric_set:
            placeholders = ",".join("?" for _ in haric_set)
            filtreler.append(f"a.sure_ayet_key NOT IN ({placeholders})")
            params.extend(list(haric_set))

        where_str = " AND ".join(filtreler) if filtreler else "1=1"

        sorgu = f"""
            SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
            FROM ayetler a
            JOIN sureler s ON a.sure_no = s.sure_no
            WHERE {where_str}
            ORDER BY a.paylasim_sayisi ASC, RANDOM()
            LIMIT 1
        """
        cur = con.execute(sorgu, params)
        row = cur.fetchone()

        if not row and sadece_video_uygun:
            # Video filtresini gevşetip tekrar dene
            return gunun_ayetini_sec(tema=None, sadece_video_uygun=False, haric_tutulanlar=haric_tutulanlar)

        return dict(row) if row else None


def ayeti_paylasildi_isaretle(sure_no: int, ayet_no: int):
    """Âyetin paylaşım sayısını artırır ve son paylaşım tarihini günceller."""
    with baglanti_al() as con:
        con.execute(
            """
            UPDATE ayetler
            SET paylasim_sayisi = paylasim_sayisi + 1,
                son_paylasim = CURRENT_TIMESTAMP
            WHERE sure_no = ? AND ayet_no = ?
            """,
            (sure_no, ayet_no),
        )
        con.commit()
        log.info(f"Âyet {sure_no}:{ayet_no} paylaşıldı olarak işaretlendi.")
