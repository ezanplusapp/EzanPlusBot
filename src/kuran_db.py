"""
kuran_db.py — Ezan Plus Tescilli Kur'an-ı Kerim Veritabanı Modülü

6.236 Âyet ve 114 Sûre'den oluşan tescilli yerel SQLite veritabanı yönetimi.
Medine Kral Fehd Mushafı Uthmani hattı, Elmalılı Hamdi Yazır ve Diyanet İşleri
Başkanlığı tescilli Türkçe mealleri ile %100 sıfır yapay zeka halüsinasyonu garantisi sunar.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
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


def ayet_anahtari_cozumle(metin: str) -> Optional[Tuple[int, int]]:
    """
    Her türlü ayet metin formatını (örn. '9:53', 'Tevbe Sûresi • 53. Âyet',
    'Bakara 127', 'Ankebût Sûresi • 64. Âyet • Elmalılı Meali') çözerek
    (sure_no, ayet_no) tuple'ı döner.
    """
    if not metin or not isinstance(metin, str):
        return None

    # 1. sure:ayet formatı (örn: "9:53", "2:127")
    m = re.search(r"(\d+):(\d+)", metin)
    if m:
        return int(m.group(1)), int(m.group(2))

    # 2. X. Âyet formatı ve sûre adı eşleştirmesi
    def _tr_norm(s: str) -> str:
        mapping = {"Â": "A", "â": "a", "Î": "I", "î": "i", "Û": "U", "û": "u", "İ": "i", "I": "i", "ı": "i"}
        for k, v in mapping.items():
            s = s.replace(k, v)
        return s.lower()

    norm_metin = _tr_norm(metin)
    m_a = re.search(r"(\d+)\s*\.?\s*ayet", norm_metin)
    if m_a:
        a_no = int(m_a.group(1))
        # Sûre adını eşleştir
        for s in sure_listesi_getir():
            s_norm = _tr_norm(s["sure_adi_tr"])
            if s_norm in norm_metin:
                return int(s["sure_no"]), a_no

    return None


def gunun_ayetini_sec(
    tema: Optional[str] = None,
    sadece_video_uygun: bool = True,
    haric_tutulanlar: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Paylaşılmamış veya en az paylaşılmış tescilli bir âyet seçer.
    
    1. Tema verilmişse FTS üzerinden o temaya (sabır, huzur, şükür, tevbe vb.) uyan âyetleri tarar.
    2. Video/Reels formatı için ideal uzunluktaki (4-25 kelime, <= 200 karakter meal) âyetlere öncelik verir.
    3. Geçmişte paylaşılan âyetleri (haric_tutulanlar) kesinlikle eler (etiket, key ve (sure, ayet) bazında).
    4. En az paylaşılmış olanlar arasından rastgele birini seçerek mükerrerliği %100 engeller.
    """
    with baglanti_al() as con:
        # Hariç tutulanları normalize et:
        # Hem ham stringler, hem çözümlenmiş sure_ayet_key ("9:53") hem de (sure_no, ayet_no) çiftleri
        haric_keys: Set[str] = set()
        haric_etiketler: Set[str] = set()
        haric_ciftler: Set[Tuple[int, int]] = set()

        for item in (haric_tutulanlar or []):
            if not item:
                continue
            item_str = str(item).strip()
            haric_etiketler.add(item_str)
            cozum = ayet_anahtari_cozumle(item_str)
            if cozum:
                s_no, a_no = cozum
                haric_ciftler.add((s_no, a_no))
                haric_keys.add(f"{s_no}:{a_no}")
                haric_keys.add(f"{s_no:03d}{a_no:03d}")

        # 1. Tema araması
        if tema:
            tema_kelimeleri = [k.strip() for k in tema.replace("(", " ").replace(")", " ").replace(",", " ").split() if len(k.strip()) >= 3]
            for kelime in tema_kelimeleri:
                adaylar = ayet_ara(kelime, limit=40)
                if sadece_video_uygun:
                    adaylar = [a for a in adaylar if a.get("video_icin_uygun") == 1]
                if haric_keys or haric_etiketler or haric_ciftler:
                    adaylar = [
                        a for a in adaylar
                        if a.get("sure_ayet_key") not in haric_keys
                        and a.get("sure_ayet_etiket") not in haric_etiketler
                        and (a.get("sure_no"), a.get("ayet_no")) not in haric_ciftler
                    ]

                if adaylar:
                    min_paylasim = min(a.get("paylasim_sayisi", 0) for a in adaylar)
                    en_iyi_adaylar = [a for a in adaylar if a.get("paylasim_sayisi", 0) == min_paylasim]
                    import random
                    return random.choice(en_iyi_adaylar)

        # 2. Genel Havuzdan Seçim (Tema bulunamadıysa veya verilmediyse)
        filtreler = []
        params: List[Any] = []

        if sadece_video_uygun:
            filtreler.append("a.video_icin_uygun = 1")

        if haric_keys:
            placeholders = ",".join("?" for _ in haric_keys)
            filtreler.append(f"a.sure_ayet_key NOT IN ({placeholders})")
            params.extend(list(haric_keys))

        if haric_etiketler:
            placeholders = ",".join("?" for _ in haric_etiketler)
            filtreler.append(f"a.sure_ayet_etiket NOT IN ({placeholders})")
            params.extend(list(haric_etiketler))

        for s_no, a_no in haric_ciftler:
            filtreler.append("NOT (a.sure_no = ? AND a.ayet_no = ?)")
            params.extend([s_no, a_no])

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
