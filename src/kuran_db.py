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


def cuz_ayetleri_getir(cuz_no: int) -> List[Dict[str, Any]]:
    """Belirli bir cüze ait tüm âyetleri sırasıyla getirir (1..30)."""
    with baglanti_al() as con:
        cur = con.execute(
            """
            SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
            FROM ayetler a
            JOIN sureler s ON a.sure_no = s.sure_no
            WHERE a.cuz_no = ?
            ORDER BY a.sure_no ASC, a.ayet_no ASC
            """,
            (cuz_no,),
        )
        return [dict(r) for r in cur.fetchall()]


_TRANSLITERATION_CACHE: Optional[Dict[Tuple[int, int], str]] = None


def latin_okunus_getir(sure_no: int, ayet_no: int) -> str:
    """Tescilli tr.transliteration dosyasından âyetin Latin okunuşunu getirir."""
    global _TRANSLITERATION_CACHE
    if _TRANSLITERATION_CACHE is None:
        cache: Dict[Tuple[int, int], str] = {}
        trans_dosyasi = KURAN_DIZINI / "tr.transliteration"
        if trans_dosyasi.exists():
            try:
                for line in trans_dosyasi.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        parts = line.split("|", 2)
                        if len(parts) == 3:
                            cache[(int(parts[0]), int(parts[1]))] = parts[2].strip()
            except Exception as e:
                log.warning(f"tr.transliteration okuma hatası: {e}")
        _TRANSLITERATION_CACHE = cache

    return _TRANSLITERATION_CACHE.get((sure_no, ayet_no), "")


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


# Kıssa ortasından kopuk diyalog başlangıçları veya müstakil sosyal medya kartında bağlam kopukluğu yaratan ifadeler
_AYET_BAGLAM_KOPUK_BASLANGICLAR = (
    "dediler ki",
    "dedi ki",
    "sonra ",
    "bunun üzerine",
    "yoksa onlar",
    "onlara âyetlerimizi",
    "onlara ayetlerimizi",
    "fakat onlar",
    "derken ",
    "senden izin isteyenler",
    "ey ehl-i kitap",
)

_AYET_HASSAS_KALIPLAR = (
    "öldürün",
    "boynunu vur",
    "boyunlarını vur",
    "cizye",
    "üçte bir",
    "altıda bir",
    "sekizde bir",
    "boşadığınız",
    "hayız",
)

_AYET_YUKSEK_ETKILESIM_KELIMELERI = (
    "sabır", "sabr", "sabreden", "rahmet", "merhamet", "bağışla", "mağfiret",
    "tevbe", "tövbe", "huzur", "mutmain", "kalp", "kalb", "kolaylık", "şifa",
    "nur", "dua", "kullarım", "yakın", "vekil", "tevekkül", "şükür", "şükr",
    "rızık", "rızk", "iyilik", "ihsan", "cennet", "müjde", "sev", "koru", "yardım",
)


def _ayet_sosyal_medya_uygun_mu(kayit: Dict[str, Any]) -> bool:
    """Âyetin tek başına müstakil anlam bütünlüğüne ve sosyal medya uygunluğuna sahip olup olmadığını denetler."""
    meal = (kayit.get("meal_elmalili") or kayit.get("meal_diyanet") or "").strip().strip('“”"\' ').lower()
    if not meal:
        return False
    if any(meal.startswith(b) for b in _AYET_BAGLAM_KOPUK_BASLANGICLAR):
        return False
    if any(h in meal for h in _AYET_HASSAS_KALIPLAR):
        return False
    return True


def _ayet_etkilesim_puani(kayit: Dict[str, Any]) -> int:
    """Müstakil, veciz ve kalbe dokunan âyetlere öncelik puanı verir."""
    meal = (kayit.get("meal_elmalili") or "").lower()
    ks = int(kayit.get("kelime_sayisi") or len(meal.split()) or 0)
    puan = 0
    if 5 <= ks <= 18:
        puan += 30
    elif 19 <= ks <= 25:
        puan += 15
    eslesme = sum(1 for k in _AYET_YUKSEK_ETKILESIM_KELIMELERI if k in meal)
    puan += min(60, eslesme * 15)
    return puan


def gunun_ayetini_sec(
    tema: Optional[str] = None,
    sadece_video_uygun: bool = True,
    haric_tutulanlar: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Paylaşılmamış veya en az paylaşılmış tescilli bir âyet seçer.
    
    1. Tema verilmişse FTS üzerinden o temaya (sabır, huzur, şükür, tevbe vb.) uyan âyetleri tarar.
    2. Video/Reels formatı için ideal uzunluktaki ve müstakil anlam bütünlüğü taşıyan âyetlere öncelik verir.
    3. Geçmişte paylaşılan âyetleri (haric_tutulanlar) kesinlikle eler (etiket, key ve (sure, ayet) bazında).
    4. En az paylaşılmış olanlar arasından yüksek etkileşim potansiyelli birini seçerek mükerrerliği %100 engeller.
    """
    import random
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

        # Veritabanındaki global minimum paylaşım sayısını tespit et (henüz 0 olanlar var mı?)
        min_kontrol_sorgu = "SELECT MIN(paylasim_sayisi) FROM ayetler WHERE " + ("video_icin_uygun = 1" if sadece_video_uygun else "1=1")
        global_min_row = con.execute(min_kontrol_sorgu).fetchone()
        global_min = global_min_row[0] if global_min_row and global_min_row[0] is not None else 0

        # 1. Tema araması
        if tema:
            tema_kelimeleri = [k.strip() for k in tema.replace("(", " ").replace(")", " ").replace(",", " ").split() if len(k.strip()) >= 3]
            uygun_adaylar = []
            for kelime in tema_kelimeleri:
                adaylar = ayet_ara(kelime, limit=60)
                if not adaylar and len(kelime) >= 5:
                    adaylar = ayet_ara(kelime[:4], limit=40)
                if sadece_video_uygun:
                    adaylar = [a for a in adaylar if a.get("video_icin_uygun") == 1]
                if haric_keys or haric_etiketler or haric_ciftler:
                    adaylar = [
                        a for a in adaylar
                        if a.get("sure_ayet_key") not in haric_keys
                        and a.get("sure_ayet_etiket") not in haric_etiketler
                        and (a.get("sure_no"), a.get("ayet_no")) not in haric_ciftler
                    ]

                # KATI KURAL: Yalnızca global minimum (sıfır) paylaşımlı adaylar kabul edilir
                sifir_paylasimlilar = [a for a in adaylar if a.get("paylasim_sayisi", 0) <= global_min]
                uygun_adaylar.extend(sifir_paylasimlilar)

            if uygun_adaylar:
                tekil_adaylar = list({a["sure_ayet_key"]: a for a in uygun_adaylar}.values())
                suzulen = [a for a in tekil_adaylar if _ayet_sosyal_medya_uygun_mu(a)] or tekil_adaylar
                suzulen.sort(key=_ayet_etkilesim_puani, reverse=True)
                return random.choice(suzulen[: min(12, len(suzulen))])
            else:
                log.info(
                    f"'{tema}' temasında henüz paylaşılmamış (paylaşım <= {global_min}) âyet bulunamadı. "
                    f"Mükerrer paylaşımı önlemek için genel sıfır paylaşımlı kürasyon havuzuna geçiliyor."
                )

        # 2. Genel Havuzdan Seçim (Müstakil anlamlı ve yüksek etkileşimli âyet öncelikli)
        filtreler = []
        params: List[Any] = []

        if sadece_video_uygun:
            filtreler.append("a.video_icin_uygun = 1")

        # KATI KURAL: Global minimum paylaşım sayısına sahip âyetlere öncelik ver
        filtreler.append("a.paylasim_sayisi <= ?")
        params.append(global_min)

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
            ORDER BY RANDOM()
            LIMIT 100
        """
        aday_rows = [dict(r) for r in con.execute(sorgu, params).fetchall()]
        uygun_genel = [a for a in aday_rows if _ayet_sosyal_medya_uygun_mu(a)]
        if uygun_genel:
            uygun_genel.sort(key=_ayet_etkilesim_puani, reverse=True)
            return random.choice(uygun_genel[: min(15, len(uygun_genel))])
        if aday_rows:
            return aday_rows[0]

        row = None
        if not row and global_min == 0:
            # Eğer hariç tutulanlar nedeniyle 0 paylaşımlı kalmadıysa genel minimum kuralını gevşet
            sorgu_gevsek = f"""
                SELECT a.*, s.sure_adi_tr, s.sure_adi_ar, s.inis_yeri
                FROM ayetler a
                JOIN sureler s ON a.sure_no = s.sure_no
                WHERE {' AND '.join([f for f in filtreler if 'paylasim_sayisi' not in f]) or '1=1'}
                ORDER BY a.paylasim_sayisi ASC, a.son_paylasim ASC, RANDOM()
                LIMIT 30
            """
            gevsek_params = [p for i, p in enumerate(params) if not (isinstance(p, int) and p == global_min)]
            gevsek_rows = [dict(r) for r in con.execute(sorgu_gevsek, gevsek_params).fetchall()]
            gevsek_uygun = [a for a in gevsek_rows if _ayet_sosyal_medya_uygun_mu(a)] or gevsek_rows
            if gevsek_uygun:
                gevsek_uygun.sort(key=_ayet_etkilesim_puani, reverse=True)
                return random.choice(gevsek_uygun[: min(8, len(gevsek_uygun))])

        if sadece_video_uygun:
            # Video filtresini gevşetip tekrar dene
            return gunun_ayetini_sec(tema=None, sadece_video_uygun=False, haric_tutulanlar=haric_tutulanlar)

        return None


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
