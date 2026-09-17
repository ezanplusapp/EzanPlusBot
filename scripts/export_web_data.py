#!/usr/bin/env python3
"""
scripts/export_web_data.py — Ezan Plus Web Veri Derleme Hattı

Bu betik:
1. data/kuran/kuran.db ve data/zamanlar/sure_{1..114}.json kaynaklarından:
   - public-legal/data/quran/surahs.json (114 Sûre Fihristi)
   - public-legal/data/quran/surah_{1..114}.json (Her sûrenin âyetleri, mealleri ve kelime zamanlamaları)
2. data/hadisler/hadisler.db kaynağından:
   - public-legal/data/hadith/riyazus_salihin.json (1.900 Sahih Hadis)
dosyalarını oluşturur ve EzanPlusBot/web/ dizinine kopyalar.
"""

import os
import json
import sqlite3
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KURAN_DB = BASE_DIR / "data" / "kuran" / "kuran.db"
ZAMAN_DIR = BASE_DIR / "data" / "zamanlar"
HADIS_DB = BASE_DIR / "data" / "hadisler" / "hadisler.db"

OUTPUT_DIRS = [
    Path("/Users/macbook/Dogukan/ezan-plus/EzanPlus/public-legal/data"),
    BASE_DIR / "web" / "data",
]

import re

SECAVENDLER = {"ۚ", "ۖ", "ۗ", "ۘ", "ۙ", "ۛ", "ۜ", "ؕ", "۞", "۩", "۝"}

def arapca_kelimeleri_ayristir(metin: str) -> list:
    """
    Arapça ayet metnini kelimelerine ayırır.
    Secavend işaretleri (ۚ ۖ ۗ ۘ ۙ ۛ ۜ ؕ ۞ ۩ ۝) telaffuz edilen birer kelime veya harf
    olmayıp mushaf içi kıraat/durak sembolleridir. Video karaoke metninde ve kelime
    senkronunda bağımsız uçuşan garip harfler oluşturmaması için listeden elenir.
    """
    ham = [w.strip() for w in metin.split() if w.strip()]
    sonuc = []
    for w in ham:
        if w in SECAVENDLER or re.fullmatch(r"[\u06D6-\u06ED\u0615\s]+", w):
            continue
        # Kelime sonuna yapışık durak işareti varsa temizle
        w_clean = re.sub(r"[\u06D6-\u06ED\u0615]+$", "", w).strip()
        if w_clean:
            sonuc.append(w_clean)
    return sonuc

TRANSLIT_FILE = BASE_DIR / "data" / "kuran" / "tr.transliteration"

TRANS_MAP = {
    'ḍ': 'd', 'Ḍ': 'D',
    'ż': 'z', 'Ż': 'Z',
    'ẓ': 'z', 'Ẓ': 'Z',
    'ẕ': 'z', 'Ẕ': 'Z',
    'ṭ': 't', 'Ṭ': 'T',
    'ṣ': 's', 'Ṣ': 'S',
    'ḥ': 'h', 'Ḥ': 'H',
    'ḫ': 'h', 'Ḫ': 'H',
    'ṯ': 's', 'Ṯ': 'S',
    'ŝ': 's', 'Ŝ': 'S',
    'ḏ': 'd', 'Ḏ': 'D',
    'ġ': 'g', 'Ġ': 'G',
    'ḳ': 'k', 'Ḳ': 'K',
    '`': "'",
    '’': "'",
    '‘': "'",
}

def clean_latin(text: str) -> str:
    for k, v in TRANS_MAP.items():
        text = text.replace(k, v)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def turkce_okunus_hizala(tr_list: list, ar_list: list) -> list:
    if not ar_list:
        return []
    if not tr_list:
        return [""] * len(ar_list)

    num_ar = len(ar_list)
    if len(tr_list) == num_ar:
        return list(tr_list)

    harfi_tarifler = {"es", "el", "al", "er", "en", "et", "ed", "ez", "ec", "eş", "eb", "ey", "il", "ul", "ül"}

    expanded = []
    if len(tr_list) < num_ar:
        for w in tr_list:
            if "-" in w and not w.startswith("-") and not w.endswith("-"):
                prefix = w.split("-")[0].lower().strip()
                if prefix not in harfi_tarifler:
                    parts = [p for p in w.split("-") if len(p.strip()) >= 2]
                    if len(parts) > 1 and len(expanded) + len(parts) <= num_ar:
                        expanded.extend(parts)
                        continue
            expanded.append(w)
    else:
        expanded = list(tr_list)

    if len(expanded) == num_ar:
        return expanded

    baglaclar = {"ve", "fe", "bi", "li", "vel", "fel", "bil", "lil", "ke", "kel"}

    merged = []
    i = 0
    while i < len(expanded):
        w = expanded[i]
        clean_w = w.lower().strip("',.:;!?\"”’")
        if clean_w in baglaclar and i + 1 < len(expanded) and len(expanded) - i > num_ar - len(merged):
            merged.append(f"{w} {expanded[i+1]}")
            i += 2
            continue
        merged.append(w)
        i += 1

    if len(merged) < num_ar:
        while len(merged) < num_ar:
            idx_space = -1
            max_len = 0
            for idx, tok in enumerate(merged):
                if " " in tok and len(tok) > max_len:
                    max_len = len(tok)
                    idx_space = idx
            if idx_space >= 0:
                parts = merged[idx_space].split(" ", 1)
                merged[idx_space] = parts[0]
                merged.insert(idx_space + 1, parts[1])
            else:
                merged.append("")
    elif len(merged) > num_ar:
        excess = " ".join(merged[num_ar - 1 :])
        merged = merged[: num_ar - 1] + [excess]

    return merged

def main():
    print("=== Ezan Plus Web Veri Derleme Hattı Başlatılıyor ===")
    
    # Hedef klasörleri hazırla
    for out in OUTPUT_DIRS:
        (out / "quran").mkdir(parents=True, exist_ok=True)
        (out / "hadith").mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # 0. Resmi Kur'an Latin Transkripsiyonunu Yükle (Dr. Muhammet Abay)
    # -------------------------------------------------------------
    print("0. 6.236 Âyetin Latin transkripsiyonu yükleniyor...")
    translit_map = {}
    if TRANSLIT_FILE.exists():
        with open(TRANSLIT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("#"):
                    continue
                parts = l.split("|")
                if len(parts) >= 3:
                    try:
                        s_idx = int(parts[0])
                        a_idx = int(parts[1])
                        t_text = "|".join(parts[2:])
                        translit_map[(s_idx, a_idx)] = clean_latin(t_text)
                    except ValueError:
                        continue
        print(f"   -> {len(translit_map)} Âyet için resmi Latin okunuş yüklendi.")

    # -------------------------------------------------------------
    # 1. 114 Sûre Fihristi (surahs.json)
    # -------------------------------------------------------------
    print("1. Sûre fihristi derleniyor...")
    con_kuran = sqlite3.connect(str(KURAN_DB))
    cur = con_kuran.cursor()

    cur.execute("""
        SELECT sure_no, sure_adi_tr, sure_adi_ar, sure_adi_en, ayet_sayisi, inis_yeri, inis_sirasi
        FROM sureler
        ORDER BY sure_no ASC
    """)
    sure_rows = cur.fetchall()

    # Başlangıç cüzü tespiti
    cur.execute("SELECT sure_no, MIN(cuz_no) FROM ayetler GROUP BY sure_no")
    cuz_map = dict(cur.fetchall())

    surahs_meta = []
    for s_no, tr, ar, en, ayet_sayisi, inis_yeri, inis_sirasi in sure_rows:
        surahs_meta.append({
            "no": s_no,
            "tr": tr,
            "ar": ar,
            "en": en,
            "ayets": ayet_sayisi,
            "yer": "Mekkî" if inis_yeri == "mekke" else "Medenî",
            "cuz": cuz_map.get(s_no, 1)
        })

    surahs_json_str = json.dumps(surahs_meta, ensure_ascii=False, separators=(',', ':'))
    for out in OUTPUT_DIRS:
        (out / "quran" / "surahs.json").write_text(surahs_json_str, encoding="utf-8")
    print(f"   -> 114 Sûre fihristi kaydedildi: {len(surahs_json_str)} bytes")

    # -------------------------------------------------------------
    # 2. Her Sûrenin Âyetleri, Mealleri, Okunuşları ve Kelime Zamanları
    # -------------------------------------------------------------
    print("2. 114 Sûrenin âyet, Latin okunuş ve kelime zamanlamaları derleniyor...")
    total_words_processed = 0

    for s_no, tr, ar, en, ayet_sayisi, inis_yeri, inis_sirasi in sure_rows:
        cur.execute("""
            SELECT ayet_no, cuz_no, arapca_metin, meal_diyanet, meal_elmalili
            FROM ayetler
            WHERE sure_no = ?
            ORDER BY ayet_no ASC
        """, (s_no,))
        ayet_rows = cur.fetchall()

        # Zaman dosyasını oku
        z_file = ZAMAN_DIR / f"sure_{s_no}.json"
        z_data = {}
        if z_file.exists():
            try:
                z_data = json.loads(z_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"   Uyarı: sure_{s_no}.json okunamadı: {e}")

        af = z_data.get("audio_files", [{}])[0]
        vt_map = {vt.get("verse_key"): vt for vt in af.get("verse_timings", [])}

        surah_ayahs = []
        for ayet_no, cuz_no, arapca, diyanet, elmalili in ayet_rows:
            vkey = f"{s_no}:{ayet_no}"
            vt = vt_map.get(vkey, {})
            raw_segments = vt.get("segments", [])
            words_clean = arapca_kelimeleri_ayristir(arapca)
            toplam_kelime = len(words_clean)

            norm_segments = []
            if raw_segments and len(raw_segments[0]) >= 2:
                ayah_start = raw_segments[0][1]
                ayah_end = vt.get("timestamp_to", ayah_start)
                for seg in raw_segments:
                    if len(seg) >= 3:
                        w_idx = int(seg[0]) - 1
                        s_sec = max(0.0, (seg[1] - ayah_start) / 1000.0)
                        e_sec = max(s_sec + 0.05, (seg[2] - ayah_start) / 1000.0)
                    elif len(seg) == 2:
                        w_idx = len(norm_segments)
                        s_sec = max(0.0, (seg[0] - ayah_start) / 1000.0)
                        e_sec = max(s_sec + 0.05, (ayah_end - ayah_start) / 1000.0)
                    else:
                        continue
                    w_idx = max(0, min(w_idx, toplam_kelime - 1))
                    norm_segments.append([w_idx, round(s_sec, 2), round(e_sec, 2)])
            else:
                # Fallback: sentetik zamanlama
                duration_ms = vt.get("duration", 0)
                toplam_sure = duration_ms / 1000.0 if duration_ms > 0 else 5.0
                pad_bas = min(0.6, toplam_sure * 0.05)
                pad_bit = min(1.0, toplam_sure * 0.08)
                kullanilabilir = max(1.0, toplam_sure - pad_bas - pad_bit)
                k_suresi = kullanilabilir / max(1, toplam_kelime)
                for i in range(toplam_kelime):
                    s_sec = pad_bas + i * k_suresi
                    e_sec = s_sec + k_suresi
                    norm_segments.append([i, round(s_sec, 2), round(e_sec, 2)])

            tr_full = translit_map.get((s_no, ayet_no), "")
            tr_raw = tr_full.split()
            tr_aligned = turkce_okunus_hizala(tr_raw, words_clean)

            words = []
            for i in range(toplam_kelime):
                matching = [seg for seg in norm_segments if seg[0] == i]
                if matching:
                    s = matching[0][1]
                    e = matching[-1][2]
                else:
                    s = 0.0
                    e = 0.0
                words.append({
                    "w": words_clean[i],
                    "t": tr_aligned[i] if i < len(tr_aligned) else "",
                    "s": s,
                    "e": e
                })

            total_words_processed += len(words)

            surah_ayahs.append({
                "a": ayet_no,
                "c": cuz_no,
                "ar": " ".join(words_clean),
                "ok": translit_map.get((s_no, ayet_no), ""),
                "diy": diyanet or "",
                "elm": elmalili or "",
                "audio": f"https://everyayah.com/data/Alafasy_128kbps/{s_no:03d}{ayet_no:03d}.mp3",
                "words": words,
                "segments": norm_segments
            })

        s_json = json.dumps(surah_ayahs, ensure_ascii=False, separators=(',', ':'))
        for out in OUTPUT_DIRS:
            (out / "quran" / f"surah_{s_no}.json").write_text(s_json, encoding="utf-8")

    print(f"   -> 114 Sûrenin tamamı derlendi. Toplam işlenen kelime: {total_words_processed}")

    # -------------------------------------------------------------
    # 3. 1.900 Riyâzü's-Sâlihîn Hadis Külliyatı (riyazus_salihin.json)
    # -------------------------------------------------------------
    print("3. 1.900 Riyâzü's-Sâlihîn Sahih Hadis külliyatı derleniyor...")
    con_hadis = sqlite3.connect(str(HADIS_DB))
    cur_h = con_hadis.cursor()

    cur_h.execute("""
        SELECT hadis_no, ravi, arapca_veciz, arapca_metin, hadis_metni, turkce_tam, kaynak_ref
        FROM hadisler
        ORDER BY hadis_no ASC
    """)
    hadis_rows = cur_h.fetchall()

    hadis_list = []
    for h_no, ravi, ar_veciz, ar_metin, metin, tam, kaynak in hadis_rows:
        kaynak_clean = (kaynak or "").strip()
        tam_clean = (tam or "").strip()
        metin_clean = (metin or "").strip()

        # Kaynak boşsa tam metin sonundaki parantez veya kaynak referansını ayıkla
        if not kaynak_clean and tam_clean:
            m = re.search(r'\((Buhârî|Müslim|Ebû Dâvûd|Tirmizî|Nesâî|İbni Mâce|İbn Mâce|Ahmed|Dârimî|Muvatta)[^)]*\)\s*$', tam_clean, re.IGNORECASE)
            if not m:
                m = re.search(r'(Buhârî|Müslim|Ebû Dâvûd|Tirmizî|Nesâî|İbni Mâce|İbn Mâce|Ahmed|Dârimî|Muvatta)[^.]*$', tam_clean, re.IGNORECASE)
            if m:
                kaynak_clean = m.group(0).strip(' ()')

        if not kaynak_clean:
            kaynak_clean = "İmam Nevevî, Riyâzü's-Sâlihîn"

        ar_clean = (ar_metin or ar_veciz or "").strip()

        hadis_list.append({
            "no": h_no,
            "ravi": (ravi or "").strip(),
            "ar": ar_clean,
            "metin": metin_clean,
            "tam": tam_clean,
            "kaynak": kaynak_clean
        })

    hadis_json_str = json.dumps(hadis_list, ensure_ascii=False, separators=(',', ':'))
    for out in OUTPUT_DIRS:
        (out / "hadith" / "riyazus_salihin.json").write_text(hadis_json_str, encoding="utf-8")

    print(f"   -> 1.900 Sahih Hadis derlendi: {len(hadis_list)} hadis, {len(hadis_json_str)} bytes (~{len(hadis_json_str)/1024:.1f} KB)")
    print("=== Veri Derleme Başarıyla Tamamlandı! ===")

if __name__ == "__main__":
    main()
