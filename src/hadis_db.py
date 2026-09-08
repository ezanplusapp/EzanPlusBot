"""
hadis_db.py — Ezan Plus Sahih Hadis Külliyatı Veritabanı Modülü

İmam Nevevî'nin Riyâzü's-Sâlihîn külliyatı (Buhârî, Müslim, Ebû Dâvûd, Tirmizî,
Nesâî ve İbn Mâce'den derlenen 1900 sahih hadis) veritabanı yönetimi.
Sıfır yapay zeka halüsinasyonu garantisiyle, tescilli metin ve kaynakları sağlar.
"""

from __future__ import annotations

import html
import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .ayar import KOK_DIZIN

log = logging.getLogger(__name__)

from contextlib import contextmanager

HADISLER_DIZINI = KOK_DIZIN / "data" / "hadisler"
DB_YOLU = HADISLER_DIZINI / "hadisler.db"
RAW_JSON_YOLU = HADISLER_DIZINI / "riyazus_salihin.json"


@contextmanager
def baglanti_al():
    """Hadis veritabanı bağlantısı oluşturur ve işlem bitiminde kapatır."""
    HADISLER_DIZINI.mkdir(parents=True, exist_ok=True)
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


def _html_temizle_ve_ayristir(raw_tr: str) -> List[str]:
    """HTML etiketlerini temizleyip satırlara böler."""
    if not raw_tr:
        return []
    m = html.unescape(raw_tr)
    m = re.sub(r'<br\s*/?>', '\n', m)
    m = re.sub(r'</p>', '\n\n', m)
    m = re.sub(r'<[^>]+>', '', m).replace('\r', '')
    return [s.strip() for s in m.split('\n') if s.strip()]


def _hadis_kaydi_parse(h: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ham JSON kaydını ayrıştırarak temiz alanlara dönüştürür."""
    raw_tr = h.get("turkish", "")
    raw_ar = h.get("arabic", "")
    hid = h.get("hadith_id", "")

    if not raw_tr or not hid:
        return None

    lines = _html_temizle_ve_ayristir(raw_tr)
    if not lines:
        return None

    # 1. Kaynak tespiti (son satırlarda Buhârî, Müslim vs. araması)
    kaynak_satiri = ""
    metin_satirlari = []
    kaynak_pattern = re.compile(
        r'^(Buhârî|Müslim|Ebû Dâvûd|Tirmizî|Nesâî|İbni Mâce|Muvatta|Ahmed)',
        re.IGNORECASE,
    )

    for line in reversed(lines):
        if not kaynak_satiri and kaynak_pattern.search(line):
            kaynak_satiri = line
        else:
            metin_satirlari.insert(0, line)

    # 2. Râvi tespiti (ilk satır)
    ravi = ""
    if metin_satirlari:
        ilk_satir = metin_satirlari[0]
        if any(w in ilk_satir for w in ["radıyallahu", "şöyle dedi", "rivayet edildiğine göre", "buyurdu"]):
            ravi_match = re.search(r'^([^,]+?(?:radıyallahu anh(?:â|üm|ümâ)?|şöyle dedi|anlattı))', ilk_satir)
            if ravi_match:
                ravi = ravi_match.group(1).strip()
            else:
                ravi = ilk_satir.split(",")[0].strip()
            # İlk satır yalnızca tanıtımsa gövdeden ayır
            if len(metin_satirlari) > 1 and len(ilk_satir.split()) < 25:
                metin_satirlari = metin_satirlari[1:]

    govde = " ".join(metin_satirlari).strip()

    # 3. Tırnak içi ana lafız tespiti
    tirnak_match = re.search(r'“([^”]+)”', govde)
    if tirnak_match and len(tirnak_match.group(1).split()) >= 4:
        ana_metin = tirnak_match.group(1).strip()
    else:
        ana_metin = govde

    # 4. Arapça metin temizliği ve veciz lafzın çıkarılması
    ar_temiz = html.unescape(raw_ar) if raw_ar else ""
    ar_temiz = re.sub(r'<[^>]+>', '', ar_temiz).strip()
    ar_clean = re.sub(r'[\u200e\u200f\u200b\u202a-\u202e\ufeff]', '', ar_temiz).replace('\r', ' ').strip()

    tirnak = re.search(r'[\"“«]([^\"”»]{15,})[\"”»]', ar_clean)
    if tirnak and len(tirnak.group(1).strip().split()) >= 3 and not tirnak.group(1).strip().startswith('بفتح'):
        ar_veciz = re.sub(r'\s+', ' ', tirnak.group(1).strip())
    else:
        matches = list(re.finditer(r'(?:قالَ?|يقُولُ?|صَلّى\s*اللهُ?\s*عَلَيْهِ\s*وسَلَّم|صلى\s*الله\s*عليه\s*وسلم)\s*[:\.]\s*', ar_clean))
        if matches:
            last_match = matches[-1]
            sonraki = ar_clean[last_match.end():].strip()
        else:
            sonraki = ar_clean

        sonraki = re.sub(r'^سمعت\s*رسول\s*الله\s*(?:صلى|صَلّى)\s*اللهُ?\s*عَلَيْهِ\s*وسَلَّم\s*(?:يقول|يقُولُ)\s*[:\.]\s*', '', sonraki)
        sonraki = re.split(r'متفقٌ?\s*عليه|رَوَاهُ|رواه|وفي رواية|و\s*«', sonraki)[0].strip()
        sonraki = sonraki.strip('«»\"“”\' \t\r\n:،.()')
        sonraki = re.sub(r'\s+', ' ', sonraki)
        ar_veciz = sonraki if len(sonraki.split()) >= 3 else ar_clean

    # Kelime sayısı ve kart uygunluğu
    kelime_sayisi = len(ana_metin.split())
    ar_kelime = len(ar_veciz.split())
    # 4:5 infografik kart için ideal: Türkçe 10-65 kelime, Arapça en az 3 kelime / 15 karakter
    kart_icin_uygun = 1 if (10 <= kelime_sayisi <= 65 and ar_kelime >= 3 and len(ar_veciz) >= 15) else 0

    return {
        "hadis_no": int(hid) if str(hid).isdigit() else 0,
        "kulliyat": "Riyâzü’s-Sâlihîn",
        "ravi": ravi,
        "arapca_metin": ar_temiz,
        "arapca_veciz": ar_veciz,
        "turkce_tam": govde,
        "hadis_metni": ana_metin,
        "kaynak_ref": kaynak_satiri,
        "kelime_sayisi": kelime_sayisi,
        "kart_icin_uygun": kart_icin_uygun,
    }


def veritabanini_hazirla():
    """Tabloları kurar ve eğer boşsa JSON külliyatından veritabanını doldurur."""
    with baglanti_al() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS hadisler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hadis_no INTEGER,
                kulliyat TEXT DEFAULT 'Riyâzü’s-Sâlihîn',
                ravi TEXT,
                arapca_metin TEXT,
                arapca_veciz TEXT,
                turkce_tam TEXT,
                hadis_metni TEXT NOT NULL,
                kaynak_ref TEXT,
                kelime_sayisi INTEGER,
                kart_icin_uygun INTEGER DEFAULT 0,
                paylasim_sayisi INTEGER DEFAULT 0,
                son_paylasim TIMESTAMP
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_hadis_kart ON hadisler(kart_icin_uygun)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_hadis_paylasim ON hadisler(paylasim_sayisi)")
        con.commit()

        # Kayıt var mı kontrolü
        cur = con.execute("SELECT COUNT(*) FROM hadisler")
        count = cur.fetchone()[0]
        if count > 0:
            log.info(f"Hadis veritabanı hazır: {count} kayıt mevcut.")
            return

        if not RAW_JSON_YOLU.exists():
            log.error(f"Külliyat JSON dosyası bulunamadı: {RAW_JSON_YOLU}")
            return

        log.info("Riyâzü's-Sâlihîn külliyatı SQLite veritabanına aktarılıyor...")
        with open(RAW_JSON_YOLU, "r", encoding="utf-8") as f:
            ham_veri = json.load(f)

        eklenen = 0
        for h in ham_veri:
            kayit = _hadis_kaydi_parse(h)
            if not kayit:
                continue
            con.execute("""
                INSERT INTO hadisler (
                    hadis_no, kulliyat, ravi, arapca_metin, arapca_veciz,
                    turkce_tam, hadis_metni, kaynak_ref, kelime_sayisi, kart_icin_uygun
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kayit["hadis_no"],
                kayit["kulliyat"],
                kayit["ravi"],
                kayit["arapca_metin"],
                kayit["arapca_veciz"],
                kayit["turkce_tam"],
                kayit["hadis_metni"],
                kayit["kaynak_ref"],
                kayit["kelime_sayisi"],
                kayit["kart_icin_uygun"],
            ))
            eklenen += 1

        con.commit()
        log.info(f"Riyâzü's-Sâlihîn külliyatı başarıyla aktarıldı: {eklenen} hadis.")


def gunun_hadisini_sec(tema: Optional[str] = None, sadece_kart_uygun: bool = True) -> Optional[Dict[str, Any]]:
    """
    Paylaşılmamış veya en az paylaşılmış sahih bir hadis seçer.
    Kart mizanpajına tam oturan uzunluktaki hadislere öncelik verir.
    """
    veritabanini_hazirla()
    with baglanti_al() as con:
        filtreler = []
        parametreler: List[Any] = []

        if sadece_kart_uygun:
            filtreler.append("kart_icin_uygun = 1")
            filtreler.append("arapca_veciz != ''")
            filtreler.append("kaynak_ref != ''")

        if tema:
            filtreler.append("(turkce_tam LIKE ? OR hadis_metni LIKE ?)")
            parametreler.extend([f"%{tema}%", f"%{tema}%"])

        where_clause = " AND ".join(filtreler) if filtreler else "1=1"

        sorgu = f"""
            SELECT * FROM hadisler
            WHERE {where_clause}
            ORDER BY paylasim_sayisi ASC, RANDOM()
            LIMIT 1
        """
        cur = con.execute(sorgu, parametreler)
        row = cur.fetchone()

        if not row and tema:
            return gunun_hadisini_sec(tema=None, sadece_kart_uygun=sadece_kart_uygun)

        if row:
            return dict(row)
        return None


def hadisi_paylasildi_isaretle(hadis_id: int):
    """Hadisin paylaşım sayısını artırır ve son paylaşım tarihini günceller."""
    with baglanti_al() as con:
        con.execute("""
            UPDATE hadisler
            SET paylasim_sayisi = paylasim_sayisi + 1,
                son_paylasim = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (hadis_id,))
        con.commit()
        log.info(f"Hadis #{hadis_id} paylaşıldı olarak işaretlendi.")


def toplam_hadis_sayisi() -> int:
    """Veritabanındaki toplam sahih hadis sayısını döner."""
    veritabanini_hazirla()
    with baglanti_al() as con:
        cur = con.execute("SELECT COUNT(*) FROM hadisler")
        return cur.fetchone()[0]


def hadis_getir_no(hadis_no: int) -> Optional[Dict[str, Any]]:
    """Belirli bir hadis numarasına göre kaydı döner."""
    veritabanini_hazirla()
    with baglanti_al() as con:
        cur = con.execute("SELECT * FROM hadisler WHERE hadis_no = ? LIMIT 1", (hadis_no,))
        row = cur.fetchone()
        return dict(row) if row else None
