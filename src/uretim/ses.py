"""
ses_getir.py — Ezan Plus Kur'an Tilaveti ve Ses Yöneticisi
EveryAyah API üzerinden telifsiz, yüksek kaliteli hafız seslerini indirir,
birden fazla ayeti birleştirir ve ses süresini hesaplar.
"""

from __future__ import annotations

import re
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
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    son_hata = None
    for deneme in range(1, 3):
        try:
            log.info(f"Ayet sesi indiriliyor (Deneme {deneme}/2): {url}")
            res = requests.get(url, headers=headers, timeout=25)
            res.raise_for_status()
            hedef_yol.write_bytes(res.content)
            return hedef_yol
        except Exception as e:
            son_hata = e
            log.warning(f"Ayet sesi indirme hatası (Deneme {deneme}/2): {e}")
            if deneme < 2:
                import time
                time.sleep(2)

    raise RuntimeError(f"Ayet sesi indirilemedi ({url}): {son_hata}")


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


# =========================================================
#  Fish Audio — Türkçe Hadis ve Dua Seslendirme Motoru
# =========================================================

DEFAULT_FISH_VOICE_ID = "a6d624c6b8de45d2b89eb0da9a691872"  # Mazlum Kiper (Usta Belgesel & Tiyatro)


def turkce_kisaltmalari_genislet(metin: str) -> str:
    """
    Dini ve edebi metinlerdeki yaygın kısaltmaları (Hz., s.a.v., r.a., a.s., c.c. vb.)
    yapay zeka spikerinin (Fish Audio) "hetz", "sav" gibi yapay veya mekanik sesler
    çıkarmasını önlemek ve metin-ses uyumunu kusursuzlaştırmak için tam Türkçe telaffuzlarına genişletir.
    """
    if not metin:
        return ""
    import re

    # 1. Hazreti Kısaltması (Hz. / Hz / hz. / hz)
    # Hz. Peygamber, Hz. Ali, Hz Âişe, Hz. Ebû Bekir, Hz.Peygamber (boşluksuz)
    metin = re.sub(r'\b[Hh]z\.?\s+', 'Hazreti ', metin)
    metin = re.sub(r'\b[Hh]z\.(?=[A-ZÇĞİÖŞÜÂÎÛ])', 'Hazreti ', metin)
    metin = re.sub(r'\b[Hh]z\.?[\'’](?=[a-zçğıöşüâîû])', "Hazreti'", metin)

    # 2. Salavat-ı Şerife (s.a.v., sav, s.a.s., sas)
    # Ekli durumlar: (s.a.v.)'e -> sallallahu aleyhi vesellem'e
    metin = re.sub(r'\(\s*[sS]\.?[aA]\.?[vVsS]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"sallallahu aleyhi vesellem'\1", metin)
    metin = re.sub(r'\(\s*[sS]\.?[aA]\.?[vVsS]\.?\s*\)', 'sallallahu aleyhi vesellem', metin)
    metin = re.sub(r'\b[sS]\.[aA]\.[vVsS]\.?[\'’]([a-zçğıöşüâîû]+)', r"sallallahu aleyhi vesellem'\1", metin)
    metin = re.sub(r'\b[sS]\.[aA]\.[vVsS]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'sallallahu aleyhi vesellem', metin)
    metin = re.sub(r'\b[sS][aA][vV]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'sallallahu aleyhi vesellem', metin)
    metin = re.sub(r'\b[sS][aA][sS]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'sallallahu aleyhi vesellem', metin)

    # 3. Sahabi Duası (r.a., ra, r.anh, r.anhâ, r.anhüm, r.anhüma)
    # Ekli parantezli durumlar: (r.a.)'dan, (r.a)'den
    metin = re.sub(r'\(\s*[rR]\.?\s*anhümâ\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anhüma'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anhüm\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anhüm'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anhâ\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anhâ'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anha\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anhâ'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anh\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anh'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?[aA]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anh'\1", metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR][aA]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anh'\1", metin, flags=re.IGNORECASE)

    # Eksiz parantezli durumlar
    metin = re.sub(r'\(\s*[rR]\.?\s*anhümâ\s*\)', 'radıyallahu anhüma', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anhüm\s*\)', 'radıyallahu anhüm', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anhâ\s*\)', 'radıyallahu anhâ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anha\s*\)', 'radıyallahu anhâ', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?\s*anh\s*\)', 'radıyallahu anh', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]\.?[aA]\.?\s*\)', 'radıyallahu anh', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR][aA]\.?\s*\)', 'radıyallahu anh', metin, flags=re.IGNORECASE)

    # Parantezsiz durumlar
    metin = re.sub(r'\b[rR]\.[aA]\.?[\'’]([a-zçğıöşüâîû]+)', r"radıyallahu anh'\1", metin)
    metin = re.sub(r'\b[rR]\.[aA]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'radıyallahu anh', metin)
    metin = re.sub(r'\b[rR][aA]\.(?=\s|[,\.;:!?\'’\"]|$)', 'radıyallahu anh', metin)

    # 4. Peygamber Duası (a.s., as)
    metin = re.sub(r'\(\s*[aA]\.?[sS]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"aleyhisselam'\1", metin)
    metin = re.sub(r'\(\s*[aA][sS]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"aleyhisselam'\1", metin)
    metin = re.sub(r'\(\s*[aA]\.?[sS]\.?\s*\)', 'aleyhisselam', metin)
    metin = re.sub(r'\(\s*[aA][sS]\.?\s*\)', 'aleyhisselam', metin)
    metin = re.sub(r'\b[aA]\.[sS]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'aleyhisselam', metin)
    metin = re.sub(r'\b[aA][sS]\.(?=\s|[,\.;:!?\'’\"]|$)', 'aleyhisselam', metin)

    # 5. Ta'zim ve Hürmet Lafızları (c.c., cc, k.v., k.s., rh.a.)
    metin = re.sub(r'\(\s*[cC]\.?[cC]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"celle celaluhu'\1", metin)
    metin = re.sub(r'\(\s*[cC][cC]\.?\s*\)[\'’]([a-zçğıöşüâîû]+)', r"celle celaluhu'\1", metin)
    metin = re.sub(r'\(\s*[cC]\.?[cC]\.?\s*\)', 'celle celaluhu', metin)
    metin = re.sub(r'\(\s*[cC][cC]\.?\s*\)', 'celle celaluhu', metin)
    metin = re.sub(r'\b[cC]\.[cC]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'celle celaluhu', metin)
    metin = re.sub(r'\b[cC][cC]\.(?=\s|[,\.;:!?\'’\"]|$)', 'celle celaluhu', metin)

    metin = re.sub(r'\(\s*[kK]\.?[vV]\.?\s*\)', 'kerremallahu vecheh', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\b[kK]\.[vV]\.?(?=\s|[,\.;:!?\'’\"]|$)', 'kerremallahu vecheh', metin)
    metin = re.sub(r'\(\s*[kK]\.?[sS]\.?\s*\)', 'kaddesallahu sırrah', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\(\s*[rR]h?\.[aA]\.?\s*\)', 'rahmetullahi aleyh', metin, flags=re.IGNORECASE)

    # 6. Genel Türkçe Kısaltmalar
    metin = re.sub(r'\bvb\.(?=\s|[,\.;:!?\'’\"]|$)', 've benzeri', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bvs\.(?=\s|[,\.;:!?\'’\"]|$)', 've saire', metin, flags=re.IGNORECASE)
    metin = re.sub(r'\bbkz\.(?=\s|[,\.;:!?\'’\"]|$)', 'bakınız', metin, flags=re.IGNORECASE)

    # Fazla boşlukları toparla
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin


def turkce_fonetik_temizle(metin: str) -> str:
    """
    Hadis ve dualardaki lafızları
    yapay zekanın pürüzsüz ve doğal Türkçe telaffuz etmesi için normalleştirir.
    Kısaltmaları (Hz. -> Hazreti vb.) genişletir.
    Markdown işaretlerini ayıklar. Şapkalı harfler (â, î, û) korunur.
    """
    if not metin:
        return ""
    import re

    # Markdown temizliği (**bold**, *italic*)
    metin = re.sub(r"\*\*([^*]+)\*\*", r"\1", metin)
    metin = re.sub(r"\*([^*]+)\*", r"\1", metin)

    # Kısaltmaları genişlet (Hz., s.a.v., r.a. vb.)
    metin = turkce_kisaltmalari_genislet(metin)

    # Sıkça rastlanan fonetik pürüzleri akıcı Türkçeye eşle
    # Şapkalı harfler (â, î, û) korunur; Fish Audio S2.1 modelinin uzun ünlüleri (örn: takvâ, hidâyet, ahlâk)
    # asil ve vakur şekilde uzatarak okuması sağlanır.
    donusumler = {
        "sallallahu aleyhi ve sellem": "sallallahu aleyhi vesellem",
        "sallallâhu aleyhi ve sellem": "sallallahu aleyhi vesellem",
        "radıyallahu anhumâ": "radıyallahu anhüma",
        "radıyallahu anhümâ": "radıyallahu anhüma",
        "aleyhi's-selâm": "aleyhisselam",
        "aleyhis-selâm": "aleyhisselam",
        "aleyhisselâm": "aleyhisselam",
    }
    for eski, yeni in donusumler.items():
        metin = metin.replace(eski, yeni)

    # Fazla boşlukları toparla
    metin = re.sub(r"\s+", " ", metin).strip()
    return metin


def dua_fonetik_ve_es_hazirla(metin: str) -> str:
    """
    Dua metinlerinde seslendirmenin (Mazlum Kiper) tefekkür derinliğine uygun şekilde
    nefes almasını ("es vermesini") sağlamak için nida ve münacat öbeklerine
    doğal virgül ve durak işaretleri yerleştirir.
    """
    if not metin:
        return ""
    metin = metin.strip()

    # Yaygın nida ve münacat terkiplerinden sonra virgül ekle (eğer yoksa)
    nida_kaliplari = [
        (r'\b(Ey\s+Rabbimiz)(?![,;:!?])\b', r'\1,'),
        (r'\b(Ey\s+Rabbim)(?![,;:!?])\b', r'\1,'),
        (r'\b(Ey\s+Allah\'ım)(?![,;:!?])\b', r'\1,'),
        (r'\b(Allah\'ım)(?![,;:!?])\b', r'\1,'),
        (r'\b(Rabbimiz)(?![,;:!?])\b', r'\1,'),
        (r'\b(Rabbim)(?![,;:!?])\b', r'\1,'),
        (r'\b(Yâ\s+Rabbi|Ya\s+Rabbi)(?![,;:!?])\b', r'\1,'),
        (r'\b(Yâ\s+Rab|Ya\s+Rab)(?![,;:!?])\b', r'\1,'),
        (r'\b(Ey\s+merhametlilerin\s+en\s+merhametlisi)(?![,;:!?])\b', r'\1,'),
        (r'\b(Ey\s+kalpleri\s+çekip\s+çeviren\s+Rabbim)(?![,;:!?])\b', r'\1,'),
    ]
    for pattern, repl in nida_kaliplari:
        metin = re.sub(pattern, repl, metin, flags=re.IGNORECASE)

    # Noktalamadan önceki gereksiz boşlukları ve mükerrer virgülleri temizle
    metin = re.sub(r'\s*,\s*', ', ', metin)
    metin = re.sub(r',+', ',', metin)
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin


def turkce_tts_uret(
    metin: str,
    cikti_yolu: Optional[Path] = None,
    kategori: str = "hadis",
    icerik_id: Optional[str] = None,
    ses_id: Optional[str] = None,
    hiz: float = 0.9,
    model: str = "s2.1-pro-free",
    ton_promptu: Optional[str] = None,
    zaman_damgasi_al: bool = True,
    overwrite: bool = False
) -> Path:
    """
    Fish Audio API kullanarak Türkçe Hadis veya Dua metnini yüksek kaliteli MP3 sesine dönüştürür.
    Zaman damgası aktifken (zaman_damgasi_al=True) kelime kelime milisaniye zamanlarını
    aynı isimli .json dosyasına kaydeder (Video karaoke senkronizasyonu için).
    ton_promptu: Fish Audio S2.1 modeline duygu ve manevi atmosfer direktifi verir.
    Metin hash'ine duyarlı önbellek mekanizmasıyla mükerrer çağrıları engellerken,
    metin değiştiğinde %100 güncel ses üretimini garanti eder.
    """
    import base64
    import json
    import hashlib
    from ..ayar import get_env

    # 1. Metni fonetik ve duraklama açısından hazırla
    if kategori == "dua":
        temiz_metin = turkce_fonetik_temizle(dua_fonetik_ve_es_hazirla(metin))
    else:
        temiz_metin = turkce_fonetik_temizle(metin)

    # 2. Çıktı yolunu belirle (Temiz metin ve hız hash'i ile tam eşleşme garantisi)
    active_voice_id = ses_id or get_env("FISH_AUDIO_VOICE_ID", DEFAULT_FISH_VOICE_ID)
    metin_hash = hashlib.md5(f"{temiz_metin}_{hiz}_{active_voice_id}".encode("utf-8")).hexdigest()[:8]

    if cikti_yolu is None:
        hedef_klasor = KOK_DIZIN / "data" / "sesler" / kategori
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        if icerik_id:
            dosya_adi = f"{icerik_id}_{metin_hash}.mp3"
        else:
            dosya_adi = f"{kategori}_{metin_hash}.mp3"
        cikti_yolu = hedef_klasor / dosya_adi
    else:
        cikti_yolu = Path(cikti_yolu)
        cikti_yolu.parent.mkdir(parents=True, exist_ok=True)

    json_yolu = cikti_yolu.with_suffix(".json")

    # 3. Önbellek kontrolü
    if not overwrite and cikti_yolu.exists() and cikti_yolu.stat().st_size > 1000:
        log.info(f"Fish Audio sesi zaten mevcut (Önbellek): {cikti_yolu}")
        return cikti_yolu

    # 4. API Yapılandırması
    api_key = get_env("FISH_AUDIO_API_KEY")
    if not api_key:
        raise ValueError("FISH_AUDIO_API_KEY .env dosyasında tanımlı değil!")

    active_voice_id = ses_id or get_env("FISH_AUDIO_VOICE_ID", DEFAULT_FISH_VOICE_ID)

    # Fish Audio S2.1 Duygu / Ulvi Ton Promptlama Entegrasyonu
    if ton_promptu and ton_promptu.strip():
        tag = ton_promptu.strip()
        if not (tag.startswith("[") and tag.endswith("]")):
            tag = f"[{tag}]"
        temiz_metin = f"{tag} {temiz_metin}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model
    }

    payload = {
        "text": temiz_metin,
        "reference_id": active_voice_id,
        "format": "mp3",
        "prosody": {
            "speed": hiz
        }
    }

    # 5. Kelime Zaman Damgalı Akış (Stream with timestamp)
    if zaman_damgasi_al:
        try:
            url = "https://api.fish.audio/v1/tts/stream/with-timestamp"
            log.info(f"Fish Audio TTS (Zaman Damgalı) çağrılıyor ({kategori}): {temiz_metin[:40]}...")
            resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
            if resp.status_code == 200:
                full_audio = bytearray()
                # Fish Audio akışında her chunk_seq için güncel hizalamaları ve zaman ofsetlerini topla
                chunk_alignments: Dict[int, Tuple[float, list]] = {}

                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        try:
                            evt = json.loads(line_str[6:])
                            if "audio_base64" in evt and evt["audio_base64"]:
                                full_audio.extend(base64.b64decode(evt["audio_base64"]))
                            seq = evt.get("chunk_seq", 0)
                            offset = float(evt.get("chunk_audio_offset_sec", 0.0) or 0.0)
                            if "alignment" in evt and evt["alignment"] and "segments" in evt["alignment"]:
                                chunk_alignments[seq] = (offset, evt["alignment"]["segments"])
                        except Exception:
                            pass

                if len(full_audio) > 1000:
                    cikti_yolu.write_bytes(full_audio)
                    # Tüm chunk_seq parçalarındaki kelimeleri zaman ofsetlerini ekleyerek birleştir
                    all_segments = []
                    for seq in sorted(chunk_alignments.keys()):
                        offset, segs = chunk_alignments[seq]
                        for seg in segs:
                            all_segments.append({
                                "text": seg.get("text", ""),
                                "start": round(float(seg.get("start", 0.0)) + offset, 3),
                                "end": round(float(seg.get("end", 0.0)) + offset, 3),
                            })

                    if all_segments:
                        json_yolu.write_text(
                            json.dumps(all_segments, ensure_ascii=False, indent=2),
                            encoding="utf-8"
                        )
                        log.info(f"Kelime zaman damgaları kaydedildi ({len(all_segments)} kelime): {json_yolu}")
                    log.info(f"Fish Audio sesi başarıyla üretildi: {cikti_yolu} ({len(full_audio)} bayt)")
                    return cikti_yolu
        except Exception as e:
            log.warning(f"Fish Audio zaman damgalı akış hatası, standart API deneniyor: {e}")

    # Fallback: Standart TTS
    log.info(f"Fish Audio standart TTS çağrılıyor ({kategori}): {temiz_metin[:40]}...")
    resp = requests.post("https://api.fish.audio/v1/tts", headers=headers, json=payload, timeout=60)

    if resp.status_code == 200:
        cikti_yolu.write_bytes(resp.content)
        log.info(f"Fish Audio sesi başarıyla üretildi: {cikti_yolu} ({len(resp.content)} bayt)")
        return cikti_yolu
    else:
        hata_mesaji = f"Fish Audio API Hatası ({resp.status_code}): {resp.text}"
        log.error(hata_mesaji)
        raise RuntimeError(hata_mesaji)


def turkce_kelime_zamanlari_getir(mp3_veya_json_yolu: Path) -> list:
    """
    Daha önce üretilen Türkçe ses dosyasının kelime bazlı zaman damgalarını döner.
    Dönen liste: [{'text': 'kelime', 'start': 0.40, 'end': 1.28}, ...]
    """
    import json
    p = Path(mp3_veya_json_yolu)
    json_path = p.with_suffix(".json")
    if json_path.exists():
        try:
            return json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Kelime zaman dosyası okunamadı: {e}")
    return []

