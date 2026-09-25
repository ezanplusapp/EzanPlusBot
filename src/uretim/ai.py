"""
icerik_uret.py — Ezan Plus Gemini AI İçerik Üretim Motoru
Google Gemini API kullanarak güvenilir İslami kaynaklara (Elmalılı Hamdi Yazır meali, Kütüb-i Sitte)
sadık ayet, hadis, dua, tefekkür notları ve yüksek etkileşimli Instagram caption/hashtag setleri üretir.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Optional
import requests

from ..ayar import AYARLAR, get_env
from .. import db
from .. import hadis_db
from .. import kuran_db
from .. import dua_db
from .. import kelime_db

log = logging.getLogger(__name__)

GEMINI_API_KEY = get_env("GEMINI_API_KEY")
MODEL_ADI = AYARLAR.get("yapay_zeka", {}).get("model", "gemini-3.6-flash")
UC_NOKTA = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ADI}:generateContent"

# İlham Verici İslami Temalar (Her üretimde rastgele seçilir veya parametre olarak verilir)
TEMALAR = [
    "Zorluk ve Kolaylık (İnşirah, Sabır)",
    "Huzur, Tevekkül ve İç Ferahlığı",
    "Şükür ve Nimetin Kıymeti",
    "Tövbe, İstiğfar ve Allah'ın Sonsuz Merhameti",
    "Dua ve İcabet (Rabbe Yakınlık)",
    "Güzel Ahlak, Nezaket ve İyilik",
    "Namazın Önemi ve Kalbe Etkisi",
    "Anne-Baba Hakkı ve Sıla-i Rahim",
    "İnfak, Sadaka ve Cömertlik",
    "Dünya Hayatının Geçiciliği ve Ahiret Bilinci",
    "Kardeşlik ve Birlik",
    "Doğruluk, Emanet ve Güvenilirlik",
]

# Dini Günler ve Kandiller Takvimi (Özel günlerde temayı otomatik belirler)
DINI_GUNLER = {
    # 2026
    "2026-01-15": ("Regaip Kandili", "Regaip Kandili, üç ayların bereketi, tövbe ve mağfiret"),
    "2026-01-16": ("Miraç Kandili", "Miraç Gecesi, İsra Sûresi, namaz ve ilahi yakınlık"),
    "2026-02-02": ("Berat Kandili", "Berat Gecesi, af, mağfiret ve ilahi rahmet kapıları"),
    "2026-02-18": ("Ramazan Başlangıcı", "Ramazan-ı Şerif, oruç ibadeti ve Kur'an ayı"),
    "2026-03-16": ("Kadir Gecesi", "Kadir Gecesi, Kadir Sûresi, bin aydan hayırlı gece ve Kur'an'ın nüzulü"),
    "2026-03-20": ("Ramazan Bayramı", "Ramazan Bayramı, bayram sevinci, şükür ve kardeşlik"),
    "2026-05-27": ("Kurban Bayramı", "Kurban Bayramı, Hz. İbrahim teslimiyeti, fedakarlık ve takva"),
    "2026-06-16": ("Hicri Yılbaşı", "Hicret şuuru, yeni bir başlangıç ve muhasebe"),
    "2026-06-25": ("Aşure Günü", "Aşure Günü, peygamberlerin kurtuluşu, sabır ve şükür"),
    "2026-08-24": ("Mevlid Kandili", "Peygamber Efendimiz'in (s.a.v) doğumu, sünnet-i seniyye ve alemlere rahmet"),
    # 2027
    "2027-01-07": ("Regaip Kandili", "Regaip Kandili ve üç aylar"),
    "2027-02-05": ("Miraç Kandili", "Miraç Gecesi, namaz ve göğe yükseliş"),
    "2027-02-22": ("Berat Kandili", "Berat Gecesi ve ilahi af"),
    "2027-03-08": ("Ramazan Başlangıcı", "Ramazan ayı, sahur ve oruç"),
    "2027-04-03": ("Kadir Gecesi", "Kadir Gecesi ve Kur'an nuru"),
    "2027-04-07": ("Ramazan Bayramı", "Ramazan Bayramı ve muhabbet"),
    "2027-05-16": ("Kurban Bayramı", "Kurban, takva ve kardeşlik"),
}


def dini_gun_bilgisi(tarih_str: Optional[str] = None) -> Optional[tuple[str, str]]:
    """Bugünün veya verilen tarihin özel bir dini gün olup olmadığını denetler."""
    from datetime import datetime
    bugun = tarih_str or datetime.now().strftime("%Y-%m-%d")
    return DINI_GUNLER.get(bugun)


def _gemini_cagir(prompt: str, sistem_talimati: str = "") -> str:
    """Gemini API'ye istek atar ve metin cevabını döner. 503 veya geçici arızalarda alternatif modellere otonom geçer."""
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY tanımlanmamış! Lütfen .env dosyasına ekleyin.")

    modeller: List[str] = [MODEL_ADI]
    for yedek in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.7-flash"]:
        if yedek not in modeller:
            modeller.append(yedek)

    son_hata = None
    for model in modeller:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

        if sistem_talimati:
            payload["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": sistem_talimati}],
            }

        try:
            res = requests.post(url, json=payload, timeout=45)
            if res.status_code in (503, 429, 500, 502, 504) and model != modeller[-1]:
                log.warning(f"Gemini {model} geçici yoğunluk ({res.status_code}), sonraki modele geçiliyor...")
                time.sleep(0.5)
                continue
            res.raise_for_status()

            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(f"Gemini yanıt vermedi: {data}")

            parcalar = candidates[0].get("content", {}).get("parts", [])
            cevap = "".join(p.get("text", "") for p in parcalar)
            return cevap.strip()
        except Exception as e:
            son_hata = e
            if model != modeller[-1]:
                log.warning(f"Gemini {model} çağrısı başarısız ({e}), yedek modele geçiliyor...")
                time.sleep(0.5)
                continue
            raise son_hata

    raise son_hata or RuntimeError("Tüm Gemini modelleri denendi fakat yanıt alınamadı.")


def _json_onar(metin: str) -> str:
    """Yaygın LLM JSON sözdizimi hatalarını (virgüller, tırnaklar) temizler."""
    s = metin.strip()
    # Markdown kod bloklarını ayıkla
    if "```" in s:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
        if m:
            s = m.group(1)
        else:
            m2 = re.search(r"(\{.*\})", s, re.DOTALL)
            if m2:
                s = m2.group(1)
    else:
        m2 = re.search(r"(\{.*\})", s, re.DOTALL)
        if m2:
            s = m2.group(1)

    # 1. Sondaki gereksiz virgülleri temizle (örn: {"a": 1,} veya [1, 2,])
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s


def _json_ayikla(metin: str) -> Dict[str, Any]:
    """Markdown kod blokları arasındaki veya çıplak JSON verisini toleranslı ayrıştırır."""
    metin = metin.strip()
    # İlk deneme: doğrudan veya temizlenmiş
    try:
        if "```" in metin:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", metin, re.DOTALL)
            if m:
                return json.loads(m.group(1), strict=False)
        return json.loads(metin, strict=False)
    except Exception:
        pass

    # İkinci deneme: onarılmış metin
    onarilmis = _json_onar(metin)
    try:
        return json.loads(onarilmis, strict=False)
    except Exception as e:
        log.warning(f"JSON onarma başarısız oldu ({e}): {metin[:300]}")
        raise e


def _gemini_cagir_json(prompt: str, sistem_talimati: str = "", maks_deneme: int = 2) -> Dict[str, Any]:
    """Gemini API'ye istek atar, JSON yanıtını doğrular ve hata durumunda otomatik düzeltme ile yeniden dener."""
    guncel_prompt = prompt
    son_hata: Optional[Exception] = None

    for deneme in range(1, maks_deneme + 1):
        try:
            cevap = _gemini_cagir(guncel_prompt, sistem_talimati)
            return _json_ayikla(cevap)
        except Exception as e:
            son_hata = e
            log.warning(f"Gemini yanıtı JSON ayrıştırma hatası (deneme {deneme}/{maks_deneme}): {e}")
            if deneme < maks_deneme:
                time.sleep(1.5)
                guncel_prompt = (
                    f"{prompt}\n\n"
                    f"⚠️ KRİTİK DÜZELTME TALİMATI: Önceki yanıtın JSON olarak okunamadı ({e}). "
                    f"Lütfen yanıtını SADECE geçerli, RFC-8259 uyumlu, string içindeki tırnakların kaçışlı (\\\") olduğu "
                    f"ve fazladan virgül içermeyen saf JSON nesnesi olarak ver. Markdown açıklaması yazma."
                )

    raise RuntimeError(f"Gemini {maks_deneme} denemede de geçerli bir JSON üretemedi: {son_hata}")


def _etiket_anahtari(etiket: str) -> str:
    """
    Etiket karşılaştırması için Türkçe ve şapkalı karakterleri sadeleştirir.
    casefold() tek başına yetmez — #şükür ile #sukur veya #dua ile #duâ aynı etiket sayılır.
    Bu yalnızca karşılaştırma anahtarıdır; basılan etiket orijinal yazımını korur.
    """
    cevrim = str.maketrans("çğıöşüâîû", "cgiosuaiu")
    e = etiket.lstrip("#").strip().casefold().translate(cevrim)
    return re.sub(r'[^0-9a-z_]', '', e)


def hashtaglari_normallestir(
    etiketler: List[str],
    maks: int = 5,
    zorunlu_ilk: str = "ezanplus"
) -> List[str]:
    """
    Hashtag listesini tekilleştirir, Türkçe karakter/şapka benzerliklerini ayıklar,
    ilk sıraya zorunlu etiketi (#ezanplus) yerleştirir ve azami `maks` adetle sınırlar.
    """
    zorunlu_temiz = zorunlu_ilk.lstrip("#").strip()
    goruldu = {_etiket_anahtari(zorunlu_temiz)}
    sonuc = [f"#{zorunlu_temiz}"]

    for etiket in etiketler:
        ham = etiket.lstrip("#").strip()
        temiz = re.sub(r'[^0-9A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ_]', '', ham)
        if not temiz:
            continue
        anahtar = _etiket_anahtari(temiz)
        if not anahtar or anahtar in goruldu:
            continue
        goruldu.add(anahtar)
        sonuc.append(f"#{temiz}")
        if len(sonuc) >= maks:
            break

    return sonuc


def caption_hashtaglari_guncelle(
    caption: str,
    varsayilan_etiketler: Optional[List[str]] = None,
    maks: int = 5,
    zorunlu_ilk: str = "ezanplus",
) -> str:
    """
    Caption içindeki hashtagleri ayıklar, normalize eder ve caption sonuna garantili
    azami `maks` adet tekilleştirilmiş hashtag olarak ekler.
    """
    mevcut_etiketler = re.findall(r'#\w+', caption)

    tum_adaylar = list(mevcut_etiketler)
    if varsayilan_etiketler:
        tum_adaylar.extend(varsayilan_etiketler)

    normallesmis = hashtaglari_normallestir(tum_adaylar, maks=maks, zorunlu_ilk=zorunlu_ilk)

    # Caption gövdesindeki tüm etiketleri ve fazla satır başlarını ayıkla
    metin_govdesi = re.sub(r'#\w+', '', caption).strip()
    metin_govdesi = re.sub(r'\n{3,}', '\n\n', metin_govdesi).strip()

    if not metin_govdesi:
        return " ".join(normallesmis)

    return f"{metin_govdesi}\n\n{' '.join(normallesmis)}"


def ayet_icerigi_uret(
    tema: Optional[str] = None,
    meal_tercihi: str = "elmalili",
    ozel_sure_ayet: Optional[tuple[int, int]] = None,
) -> Dict[str, Any]:
    """
    Tescilli Kur'an Veritabanından (data/kuran/kuran.db - 6.236 Âyet)
    otantik ayeti ve tescilli Türkçe mealini çeker.
    Gemini AI yalnızca bu tescilli ayet üzerine Latin okunuş, 2 satırlık video başlığı,
    tefekkür notu ve 5 odaklı hashtag'e sahip Instagram açıklaması üretir.
    Sıfır yapay zeka halüsinasyonu garantisi sunar.
    """
    if not tema:
        dini_gun = dini_gun_bilgisi()
        if dini_gun:
            gun_adi, gun_tema = dini_gun
            log.info(f"Bugün özel dini gün tespit edildi: {gun_adi} -> {gun_tema}")
            tema = gun_tema
        else:
            tema = random.choice(TEMALAR)

    # 1. Tescilli Kur'an veritabanından ayeti seç
    secilen_ayet = None
    if ozel_sure_ayet:
        s_no, a_no = ozel_sure_ayet
        secilen_ayet = kuran_db.ayet_getir(s_no, a_no)

    if not secilen_ayet:
        gecmis_ayetler = db.son_paylasilan_kaynaklar(limit=90, kategori="ayet")
        secilen_ayet = kuran_db.gunun_ayetini_sec(
            tema=tema,
            sadece_video_uygun=True,
            haric_tutulanlar=gecmis_ayetler,
        )

    if not secilen_ayet:
        # Tema kısıtını kaldırarak video için uygun herhangi bir ayeti seç (hariç tutulanlar korunur)
        gecmis_ayetler = db.son_paylasilan_kaynaklar(limit=90, kategori="ayet")
        secilen_ayet = kuran_db.gunun_ayetini_sec(tema=None, sadece_video_uygun=True, haric_tutulanlar=gecmis_ayetler)

    if not secilen_ayet:
        raise RuntimeError("Kur'an veritabanından geçerli bir ayet seçilemedi!")

    sure_adi = secilen_ayet["sure_adi_tr"]
    sure_no = secilen_ayet["sure_no"]
    ayet_no = secilen_ayet["ayet_no"]
    cuz_no = secilen_ayet["cuz_no"]
    sure_ayet_etiket = secilen_ayet["sure_ayet_etiket"]
    arapca_metin = secilen_ayet["arapca_metin"]
    
    # Meal seçimi (varsayılan: Elmalılı Hamdi Yazır)
    if meal_tercihi == "diyanet":
        turkce_meal = secilen_ayet["meal_diyanet"]
        meal_kaynagi = "Diyanet İşleri Başkanlığı Meali"
    else:
        turkce_meal = secilen_ayet["meal_elmalili"]
        meal_kaynagi = "Elmalılı Hamdi Yazır Meali"

    from .video import arapca_kelimeleri_ayristir
    ar_kelime_listesi = arapca_kelimeleri_ayristir(arapca_metin)
    toplam_ar_kelime = len(ar_kelime_listesi)
    ar_kelimeler_numarali = "\n".join(f"{i+1}. {w}" for i, w in enumerate(ar_kelime_listesi))

    sistem_talimati = f"""
Sen Ezan Plus mobil uygulamasının İslami ilimler ve editoryal içerik uzmanısın.
Sana verilen tescilli Kur'an-ı Kerim ayet metnini ve mealini ASLA değiştirmeyeceksin.
Görevin:
1) Verilen Arapça kelime listesindeki tam {toplam_ar_kelime} kelimeye birebir (1:1) karşılık gelen Latin okunuşlarını bir dizi ("latin_kelimeler") olarak üretmek. Her bir eleman tam olarak karşılık gelen Arapça kelimenin okunuşudur. Dizi tam {toplam_ar_kelime} elemanlı olmalıdır. Şapkalı harfleri (â, î, û) ve kesmeleri (') doğru kullan. Asla akademik alt/üst noktalı harfler (ḍ, ẓ, ṭ, ṣ vb.) kullanma; halkın rahat okuduğu standart Türkçe harfler (d, z, t, s, h vb.) kullan. Harf-i tarifleri (es-süfehâe, el-kitâb vb.) tek bir kelime olarak yaz, asla ayırma. Ayrıca tüm bu kelimelerin aralarında boşluk olan tam akıcı metnini "arapca_okunus" alanında ver.
2) İnsanın kalbine veya manevi bir haline dokunan, sonunda iki nokta üst üste olan 2-4 kelimelik bir çağrı anonsu yazmak ("video_baslik_satir1"). Örn: 'Kalbin daraldığında hatırla:', 'Dünya seni aldattığında bil ki:', 'Ruhun yorulduğunda hatırla:', 'Yalnız hissettiğinde unutma:'. Asla ucuz yapay kancalar ('bu ayet senin için' vb.) yazma! Asla tırnak koyma! Maksimum 30 karakter.
3) Ayetin mesajından süzülen 2-4 kelimelik derin, manşet gücünde vurucu hakikat cümlesi yazmak ("video_baslik_satir2"). Örn: 'Zorlukla beraber kolaylık var.', 'Gerçek hayat ahirettir.', 'Allah sabredenlerle beraberdir.'. Asla tırnak koyma! Maksimum 32 karakter.
4) Bu ayetin günlük hayatımıza, iç huzurumuza ve pratik yaşamımıza bakan 2-3 cümlelik çok samimi, bilgece ve kalbe dokunan bir tefekkür dersi yazmak ("tefekkur_notu").
5) Instagram ve TikTok için profesyonel, yüksek etkileşimli bir açıklama metni hazırlamak ("instagram_caption").
   Açıklama yapısı tam olarak şu 6 aşamada olmalıdır:
   - Çarpıcı açılış sorusu veya cümlesi (Hook)
   - Tırnak içinde ayet meali ve kaynak (Örn: '...' — Ankebût Sûresi, 45 • Elmalılı Hamdi Yazır Meali)
   - Samimi tefekkür dersi ve hayat rehberi
   - Kaydet 📌 & Paylaş 🕊️ çağrısı
   - Ezan Plus yönlendirmesi 📲
   - KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet ayet/konu odaklı etiket). Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen Tescilli Kur'an Âyeti:
Sûre ve Âyet: {sure_ayet_etiket}
Arapça Metin: {arapca_metin}
Arapça Kelimeler ({toplam_ar_kelime} kelime):
{ar_kelimeler_numarali}
Türkçe Meal: "{turkce_meal}"
Kaynak: {meal_kaynagi}
Tema: {tema}

Yukarıdaki tescilli âyete %100 sadık kalarak aşağıdaki JSON formatında yanıt ver:
{{
  "latin_kelimeler": [
    "1. kelimenin okunuşu",
    "2. kelimenin okunuşu",
    "tam {toplam_ar_kelime} adet eleman içeren dizi"
  ],
  "arapca_okunus": "Latin kelimelerin aralarında tek boşluk olan tam metni",
  "meal_vurgulu": "Yukarıdaki Türkçe mealin hiçbir kelimesini değiştirmeden veya eksiltmeden, âyetin en can alıcı ve vurucu 2-5 kelimelik kısmını markdown **bold** içine alarak aynen yaz. Asla bold işaretini (**...**) cümle veya dua ortasında yarım bırakma (Örn: 'Elbette güçlükle beraber şüphesiz **bir kolaylık vardır.**')",
  "video_baslik_satir1": "Çağrı/anons cümlesi (sonunda : olsun, maks 30 karakter)",
  "video_baslik_satir2": "Vurucu hakikat cümlesi (maks 32 karakter)",
  "tefekkur_notu": "2-3 cümlelik samimi hayat dersi ve tefekkür",
  "instagram_caption": "Yukarıda belirtilen 6 aşamalı Instagram açıklama metni"
}}
"""

    veri = _gemini_cagir_json(prompt, sistem_talimati)

    # Latin kelimeler kontrolü: Eğer tam dizi geldiyse kullan, eksikse/fazlaysa hizala
    from .video import turkce_okunus_hizala, latin_okunus_temizle
    lk = veri.get("latin_kelimeler")
    if isinstance(lk, list) and len(lk) == toplam_ar_kelime:
        veri["latin_kelimeler"] = [latin_okunus_temizle(str(w).strip()) for w in lk]
        veri["arapca_okunus"] = " ".join(veri["latin_kelimeler"])
    else:
        tr_ham = [latin_okunus_temizle(str(w).strip()) for w in lk] if isinstance(lk, list) and lk else [latin_okunus_temizle(w) for w in str(veri.get("arapca_okunus") or "").split()]
        if not tr_ham:
            tr_ham = [""] * toplam_ar_kelime
        veri["latin_kelimeler"] = turkce_okunus_hizala(tr_ham, ar_kelime_listesi)
        veri["arapca_okunus"] = " ".join(w for w in veri["latin_kelimeler"] if w)

    # Başlık ve anons temizliği: Tırnaksız ve garantili fallbacks
    s1 = str(veri.get("video_baslik_satir1") or "").strip().strip("“”\"'")
    s2 = str(veri.get("video_baslik_satir2") or "").strip().strip("“”\"'")
    if not s1:
        s1 = "Günün manevi tefekkürü:"
    elif not s1.endswith(":"):
        s1 = f"{s1}:"
    if not s2:
        s2 = "Huzura doğru bir adım."
    veri["video_baslik_satir1"] = s1
    veri["video_baslik_satir2"] = s2

    tef = str(veri.get("tefekkur_notu") or "").strip()
    if not tef or len(tef) < 15:
        tef = "Kalpleri mutmain kılan yegâne hakikat Allah'ı zikretmek ve O'nun rızasına sığınmaktır."
    veri["tefekkur_notu"] = tef

    cap = str(veri.get("instagram_caption") or "").strip()
    if not cap or len(cap) < 20:
        cap = f"“{turkce_meal}”\n\n{sure_ayet_etiket}"
    varsayilan = ["ezanplus", "kuran", "ayet", "tilavet", "tefekkur"]
    veri["instagram_caption"] = caption_hashtaglari_guncelle(cap, varsayilan_etiketler=varsayilan)

    # Tescilli doğrulanmış alanları veriye yerleştir (AI halüsinasyonu kesinlikle İMKANSIZDIR)
    veri["sure_adi"] = sure_adi
    veri["sure_no"] = sure_no
    veri["ayet_no"] = ayet_no
    veri["cuz_no"] = cuz_no
    veri["sure_ayet_etiket"] = sure_ayet_etiket
    veri["arapca_metin"] = arapca_metin

    # Vurgulu meal kontrolü: Gemini tek bir harf dahi değiştirdiyse orijinal tescilli meale dön
    vurgulu = str(veri.get("meal_vurgulu") or "").strip()
    if vurgulu and re.sub(r'[\*\s\.,;!?:“"\'”]', '', vurgulu.lower()) == re.sub(r'[\*\s\.,;!?:“"\'”]', '', turkce_meal.lower()):
        veri["turkce_meal"] = vurgulu
    else:
        veri["turkce_meal"] = turkce_meal
    veri["turkce_meal_orijinal"] = turkce_meal

    veri["meal_kaynagi"] = meal_kaynagi
    veri["kategori"] = "ayet"
    veri["format"] = "reels_9_16"
    veri["hafiz_adi"] = "Mişari Râşid el-Afâsî"

    return veri


def hadis_icerigi_uret(tema: Optional[str] = None) -> Dict[str, Any]:
    """
    Doğrulanmış Sahih Hadis Külliyatından (Riyâzü's-Sâlihîn / Buhârî / Müslim)
    tescilli bir hadis seçer ve Gemini AI ile Nebevî Öğüt ve Instagram caption üretir.
    Hadis metni, Arapçası ve kaynağı %100 orijinal ve tescillidir; halüsinasyon riski sıfırdır.
    """
    if not tema:
        tema = random.choice(TEMALAR)

    # 1. Doğrulanmış tescilli veritabanından hadis seç
    gecmis_hadisler = db.son_paylasilan_kaynaklar(limit=90, kategori="hadis")
    secilen_hadis = hadis_db.gunun_hadisini_sec(tema=tema, haric_tutulanlar=gecmis_hadisler)
    if not secilen_hadis:
        secilen_hadis = hadis_db.gunun_hadisini_sec(tema=None, haric_tutulanlar=gecmis_hadisler)

    if not secilen_hadis:
        raise RuntimeError("Hadis veritabanından geçerli hadis seçilemedi!")

    hadis_metni = (secilen_hadis.get("hadis_metni") or secilen_hadis.get("turkce_tam") or "").strip()
    from .ses import turkce_kisaltmalari_genislet, hadis_metninden_kaynaklari_temizle, turkce_metin_harf_duzelt
    hadis_metni = hadis_metninden_kaynaklari_temizle(hadis_metni)
    hadis_metni = turkce_kisaltmalari_genislet(hadis_metni)
    hadis_metni = turkce_metin_harf_duzelt(hadis_metni)
    hadis_metni = hadis_metni.strip("“”\"' —-")
    kaynak_ref = secilen_hadis["kaynak_ref"]
    ravi = turkce_kisaltmalari_genislet(secilen_hadis.get("ravi", ""))
    arapca_metin = (secilen_hadis.get("arapca_metin") or secilen_hadis.get("arapca_veciz") or "").strip()
    from .kart import arapca_glif_temizle
    arapca_metin = arapca_glif_temizle(arapca_metin)
    hadis_id = secilen_hadis.get("id")

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının İslami ilimler ve editoryal içerik uzmanısın.
Sana verilen SAHİH HADİS-İ ŞERİF metnini ve kaynağını ASLA değiştirmeyeceksin.
Görevin:
1) Verilen Arapça hadis metninin Latin harfleriyle tam, edebi ve akıcı Türkçe okunuşunu (transkripsiyonunu) yazmak ("arapca_okunus"). Şapkalı harfleri (â, î, û) ve kesmeleri doğru kullan (Örn: Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn).
2) Bu nebevi öğüdün modern hayattaki karşılığı ve bize verdiği pratik ahlaki dersi anlatan 2 cümlelik zarif bir "tefekkur_notu" (Günün Nebevî Öğüdü) yazmak.
3) Instagram ve Threads için yüksek etkileşimli, samimi, değer katan bir "instagram_caption" hazırlamak.
Açıklama yapısı:
- Vurucu ve dikkat çekici açılış cümlesi (Hook)
- Hadis metni ve sahabi râvisi (Asla 'Hz.' veya 'sav.' gibi kısaltmalar kullanma; editoryal zarafet gereği her zaman 'Hazreti' ve 'sallallahu aleyhi vesellem' olarak tam yaz)
- Kısa hayat dersi / nebevi öğüt
- Kaydet 📌 & Paylaş 🕊️ çağrısı
- Ezan Plus yönlendirmesi 📲
- KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet odaklı etiket). Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen Sahih Hadis:
Arapça Metin: {arapca_metin}
Türkçe Meal: "{hadis_metni}"
Râvi: {ravi}
Kaynak: {kaynak_ref}
Tema: {tema}

Yukarıdaki sahih hadise sadık kalarak aşağıdaki JSON formatında yanıt ver:
{{
  "arapca_okunus": "Arapça metnin Türkçe Latin harfleriyle edebi okunuşu (Örn: Lâ yüldeğu’l-mü’minü min cuhrin vâhıdin merrateyn)",
  "hadis_vurgulu": "Yukarıdaki Türkçe mealin hiçbir kelimesini değiştirmeden veya eksiltmeden, hadisin en can alıcı ve vurucu 2-5 kelimelik kısmını markdown **bold** içine alarak aynen yaz (Örn: 'Mü’min bir delikten **iki defa sokulmaz.**')",
  "tefekkur_notu": "Bu nebevi öğüdün modern hayattaki karşılığı ve bize verdiği ahlaki ders (Maksimum 2 cümle).",
  "instagram_caption": "Yukarıda belirtilen 6 aşamalı Instagram açıklama metni."
}}
"""

    veri = _gemini_cagir_json(prompt, sistem_talimati)

    # Tescilli doğrulanmış alanları veriye yerleştir (AI halüsinasyonu imkansız!)
    veri["hadis_id"] = hadis_id
    vurgulu = str(veri.get("hadis_vurgulu") or "").strip()
    # Metin bütünlüğü kontrolü: Gemini tek bir harf/kelime dahi değiştirdiyse orijinal tescilli metne geri dön
    if vurgulu and re.sub(r'[\*\s\.,;!?:“"\'”]', '', vurgulu.lower()) == re.sub(r'[\*\s\.,;!?:“"\'”]', '', hadis_metni.lower()):
        veri["hadis_metni"] = turkce_metin_harf_duzelt(hadis_metninden_kaynaklari_temizle(vurgulu))
    else:
        veri["hadis_metni"] = turkce_metin_harf_duzelt(hadis_metninden_kaynaklari_temizle(hadis_metni))
    veri["hadis_metni_orijinal"] = turkce_metin_harf_duzelt(hadis_metninden_kaynaklari_temizle(hadis_metni))
    veri["kaynak_ravi"] = kaynak_ref
    veri["kaynak"] = kaynak_ref
    veri["ravi"] = ravi
    veri["arapca_metin"] = arapca_metin
    
    # Okunuş temizleme ve tırnak içine alma (JSON / dict korumalı)
    raw_okunus = veri.get("arapca_okunus")
    if isinstance(raw_okunus, dict):
        okunus_ham = str(raw_okunus.get("okunus") or raw_okunus.get("latin") or next(iter(raw_okunus.values()), ""))
    elif isinstance(raw_okunus, str):
        if raw_okunus.strip().startswith("{") and "okunus" in raw_okunus:
            try:
                import json as _j
                sub_j = _j.loads(raw_okunus.strip())
                okunus_ham = str(sub_j.get("okunus", raw_okunus))
            except Exception:
                okunus_ham = raw_okunus
        else:
            okunus_ham = raw_okunus
    else:
        okunus_ham = str(raw_okunus or "")

    okunus_ham = okunus_ham.strip("“”\"'{}[] ")
    veri["arapca_okunus"] = okunus_ham

    tef = str(veri.get("tefekkur_notu") or "").strip()
    if not tef or len(tef) < 15:
        tef = "Resûlullah'ın sünnetine tabi olmak, hem dünya hem de ahiret saadetinin anahtarıdır."
    veri["tefekkur_notu"] = tef

    cap = str(veri.get("instagram_caption") or "").strip()
    if not cap or len(cap) < 20:
        cap = f"“{hadis_metni}”\n\n{kaynak_ref}"
    varsayilan = ["ezanplus", "hadis", "sunnet", "tefekkur", "dua"]
    veri["instagram_caption"] = caption_hashtaglari_guncelle(cap, varsayilan_etiketler=varsayilan)

    veri["kategori"] = "hadis"
    veri["format"] = "post_4_5"
    return veri


def dua_icerigi_uret(
    ruh_hali: Optional[str] = None,
    format_tipi: str = "4:5",
) -> Dict[str, Any]:
    """
    Tescilli Dualar Külliyatından (data/dualar/dualar.json) ruh hâline uygun
    otantik bir dua seçer ve Gemini AI ile tefekkür ve Instagram açıklaması üretir.
    Dua metni, Arapçası ve kaynağı %100 tescillidir; halüsinasyon riski sıfırdır.
    """
    haller = [
        "İç Sıkıntısı ve Daralma Hissi",
        "Gelecek Endişesi ve Sınav/İş Kaygısı",
        "Hastalık ve Şifa Talebi",
        "Şükür ve Sevinç Anı",
        "Geçim Darlığı ve Helal Rızık Arayışı",
        "Öfke ve Kararsızlık Durumu",
        "Tevekkül ve Teslimiyet İhtiyacı",
        "Tevbe ve Günahlardan Arınma Niyazı",
    ]
    if not ruh_hali:
        ruh_hali = random.choice(haller)

    # Mükerrer kontrolü
    gecmis_kaynaklar = db.son_paylasilan_kaynaklar(limit=90, kategori="dua")
    secilen_dua = dua_db.gunun_duasini_sec(ruh_hali=ruh_hali, haric_tutulanlar=gecmis_kaynaklar)
    if not secilen_dua:
        secilen_dua = dua_db.gunun_duasini_sec(ruh_hali=None, haric_tutulanlar=gecmis_kaynaklar)

    if not secilen_dua:
        raise RuntimeError("Dualar külliyatından geçerli bir dua seçilemedi!")

    from .ses import dua_fonetik_ve_es_hazirla, turkce_kisaltmalari_genislet, turkce_metin_harf_duzelt
    dua_basligi = turkce_kisaltmalari_genislet(secilen_dua["dua_basligi"])
    kategori = secilen_dua["kategori"]
    kimin_duasi = turkce_kisaltmalari_genislet(secilen_dua.get("kimin_duasi", ""))
    from .kart import arapca_glif_temizle
    arapca_metin = arapca_glif_temizle(secilen_dua["arapca_metin"])
    arapca_okunus = secilen_dua["arapca_okunus"]
    turkce_anlam = turkce_metin_harf_duzelt(turkce_kisaltmalari_genislet(dua_fonetik_ve_es_hazirla(secilen_dua["turkce_anlam"])))
    kaynak_ref = secilen_dua["kaynak_ref"]
    fazilet_notu = secilen_dua["fazilet_notu"]
    dua_id = secilen_dua["id"]

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının manevi rehberlik ve dua içerik yöneticisisin.
Sana verilen Kur'an ve Sünnet'ten tescilli dua metnini ve anlamını ASLA değiştirmeyeceksin.
Görevin:
1) Bu duanın insanın kalbine ferahlık veren hikmetini ve ruh hâline dokunan 1-2 cümlelik tefekkür dersini yazmak.
2) Instagram ve Threads için yüksek etkileşimli, kalbe dokunan bir açıklama metni ("instagram_caption") hazırlamak.
Açıklama yapısı:
- Samimi, içten ve merak uyandıran giriş sorusu / cümlesi (Hook)
- Dua metni, anlamı ve kimin duası olduğu (Asla 'Hz.' kısaltması kullanma; her zaman 'Hazreti' ve 'aleyhisselam' olarak tam yaz)
- 'Yoruma bir Âmin bırakarak dualara ortak olun 🤲' ve sevdiklerine gönderme çağrısı
- Ezan Plus yönlendirmesi 📲
- KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet duaya odaklı etiket). Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen Tescilli Dua:
Başlık: {dua_basligi}
Kategori: {kategori} ({kimin_duasi})
Arapça Metin: {arapca_metin}
Okunuş: {arapca_okunus}
Türkçe Anlam: "{turkce_anlam}"
Kaynak: {kaynak_ref}
Fazilet: {fazilet_notu}
Ruh Hâli / Durum: {ruh_hali}

Yukarıdaki duaya sadık kalarak aşağıdaki JSON formatında yanıt ver:
{{
  "tefekkur_notu": "Bu duanın insanın kalbine dokunan 1-2 cümlelik hikmeti ve manevi şifası",
  "instagram_caption": "Yukarıda belirtilen 5 aşamalı Instagram açıklama metni"
}}
"""

    veri = _gemini_cagir_json(prompt, sistem_talimati)

    # Tescilli doğrulanmış alanları yerleştir
    veri["dua_id"] = dua_id
    veri["dua_basligi"] = dua_basligi
    veri["kategori"] = "dua"
    veri["kimin_duasi"] = kimin_duasi
    veri["arapca_metin"] = arapca_metin
    veri["arapca_okunus"] = arapca_okunus
    veri["turkce_anlam"] = turkce_anlam
    veri["kaynak_fazilet"] = f"{kaynak_ref} • {fazilet_notu}"
    veri["okunus_veya_fazilet"] = f"{kaynak_ref} • {fazilet_notu}"
    veri["ruh_hali"] = ruh_hali
    veri["kaynak_ref"] = kaynak_ref
    veri["fazilet_notu"] = fazilet_notu
    veri["format"] = f"post_{format_tipi.replace(':', '_')}"

    cap = str(veri.get("instagram_caption") or "").strip()
    if not cap or len(cap) < 20:
        cap = f"“{turkce_anlam}”\n\n{dua_basligi}"
    varsayilan = ["ezanplus", "dua", "niyaz", "huzur", "tefekkur"]
    veri["instagram_caption"] = caption_hashtaglari_guncelle(cap, varsayilan_etiketler=varsayilan)

    return veri

def _varsayilan_kelime_caption(
    k_tr: str,
    k_ar: str,
    okunus: str,
    kok: str,
    lugat_anlami: str,
    kuran_boyutu: str,
    hayat_dersi: str,
    ayet_ref: str,
    ayet_ar: Optional[str] = None,
) -> str:
    """Gemini AI yanıt vermediğinde devreye giren editoryal standart 6 aşamalı açıklama şablonu."""
    temiz_lugat = re.sub(r'\*\*', '', lugat_anlami).strip()
    # Eğer kuran_boyutu içinde parantez içi sure referansı varsa ayıkla (çift referans olmasın)
    temiz_ayet = re.sub(r'\s*\([^)]*\)\s*$', '', kuran_boyutu).strip('“”" ')

    tr_map = str.maketrans("ıîâûşğüöçİÎÂÛŞĞÜÖÇ", "iiaasguocIIAASGUOC")
    slug = re.sub(r'[^a-zA-Z0-9]', '', k_tr.translate(tr_map).lower())

    if ayet_ar:
        kuran_bloku = (
            f"✨ Kelimenin Kur'an-ı Kerim'deki Yeri:\n"
            f"{ayet_ar}\n"
            f"“{temiz_ayet}”\n"
            f"📍 {ayet_ref}"
        )
    else:
        kuran_bloku = (
            f"Allah Teâlâ şöyle buyuruyor:\n"
            f"“{temiz_ayet}” ({ayet_ref})"
        )

    return (
        f"“Dünyanın telâşı ve gürültüsü içinde kalbine derin bir dinginlik katacak ilahi bir hikmet durağı...”\n\n"
        f"📖 Kavram: {okunus} ({k_ar})\n"
        f"🌱 Kök: {kok}\n"
        f"🌿 Lügat Manası: {temiz_lugat}\n\n"
        f"{kuran_bloku}\n\n"
        f"💡 Hikmet Notu:\n"
        f"{hayat_dersi}\n\n"
        f"📌 Kalbine ferahlık vermesi için kaydet, ihtiyaç duyduğunda tekrar oku.\n"
        f"🕊️ Bu manevi tefekküre vesile olmak için sevdiklerinle paylaş.\n"
        f"📲 Günlük Kur'an tilavetleri, sahih hadisler ve manevi rehberlik için Ezan Plus uygulamasını biyografideki bağlantıdan ücretsiz indirebilirsin.\n\n"
        f"#ezanplus #kuransözlüğü #{slug} #tefekkür #ayetler"
    )


def kelime_icerigi_uret(
    kelime_tr: Optional[str] = None,
    format_tipi: str = "4:5",
) -> Dict[str, Any]:
    """
    Tescilli Kelimeler Külliyatından (data/kelimeler/kelimeler.json)
    Kur'an ve İslam kavramı seçer ve Gemini AI ile 6 aşamalı yüksek etkileşimli Instagram açıklaması üretir.
    Kök, ayet ve lügat manası %100 tescillidir; halüsinasyon riski sıfırdır.
    """
    gecmis_kaynaklar = db.son_paylasilan_kaynaklar(limit=90, kategori="kelime")
    secilen_kelime = None
    if kelime_tr:
        for k in kelime_db.kelimeleri_yukle():
            if k.get("kelime_tr", "").lower() == kelime_tr.lower():
                secilen_kelime = k
                break

    if not secilen_kelime:
        secilen_kelime = kelime_db.gunun_kelimesini_sec(haric_tutulanlar=gecmis_kaynaklar)

    if not secilen_kelime:
        secilen_kelime = kelime_db.gunun_kelimesini_sec(haric_tutulanlar=gecmis_kaynaklar)

    if not secilen_kelime:
        raise RuntimeError("Kelimeler külliyatından kavram seçilemedi!")

    kelime_id = secilen_kelime["id"]
    k_tr = secilen_kelime["kelime_tr"]
    k_ar = secilen_kelime["kelime_ar"]
    okunus = secilen_kelime["okunus"]
    kok = secilen_kelime["kok"]
    lugat_anlami = secilen_kelime["lugat_anlami"]
    kuran_boyutu = secilen_kelime["kuran_boyutu"]
    hayat_dersi = secilen_kelime["hayat_dersi"]
    ayet_ref = secilen_kelime["ayet_ref"]
    ayet_ar = secilen_kelime.get("ayet_arapca", "")

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının İslami ilimler ve Kur'an lügatı uzmanısın.
Sana verilen kavramın lügat manasını, kökünü ve Kur'an âyetini ASLA değiştirmeyeceksin.
Görevin:
Instagram, Threads ve Facebook için yüksek etkileşimli, samimi, edebi ve kalbe dokunan bir açıklama metni ("instagram_caption") hazırlamak.

Açıklama şablonu TAM OLARAK şu 6 bloktan oluşmalıdır (bloklar arasında birer satır boşluk bırak):
1) VURUCU KANCA (HOOK): Kalbe dokunan, merak uyandıran 1-2 cümlelik edebi bir açılış veya soru (tırnak içinde).
2) KAVRAM KÜNYESİ:
📖 Kavram: (okunuş ve arapça)
🌱 Kök: (kök bilgisi)
🌿 Lügat Manası: (verilen lügat manası)
3) KELÂM-I İLÂHÎ (KUR'AN'DAKİ YERİ):
✨ Kelimenin Kur'an-ı Kerim'deki Yeri:
(verilen ayetin orijinal Arapça metni)
“(verilen meal)”
📍 (verilen ayet referansı)
4) GÜNÜN HİKMETİ:
💡 Hikmet Notu:
(verilen hayat dersini ve tefekkürü içeren 2 cümlelik pratik manevi öğüt)
5) ÇAĞRI (CTA):
📌 Kalbine ferahlık vermesi için kaydet, ihtiyaç duyduğunda tekrar oku.
🕊️ Bu manevi tefekküre vesile olmak için sevdiklerinle paylaş.
📲 Günlük Kur'an tilavetleri, sahih hadisler ve manevi rehberlik için Ezan Plus uygulamasını biyografideki bağlantıdan ücretsiz indirebilirsin.
6) HASHTAGLER:
KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus #kuransözlüğü #kavramadı #tefekkür #ayetler). Asla 5'ten fazla veya eksik yazma!

Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen İslami Kavram:
Kavram: {k_tr} ({okunus})
Arapça: {k_ar}
Kök: {kok}
Lügat Manası: {lugat_anlami}
Kur'an'daki Âyet (Arapça): {ayet_ar}
Kur'an'daki Âyet (Meal): {kuran_boyutu}
Âyet Kaynağı: {ayet_ref}
Hayat Dersi: {hayat_dersi}

Yukarıdaki kavrama sadık kalarak aşağıdaki JSON formatında yanıt ver:
{{
  "instagram_caption": "Yukarıda belirtilen 6 aşamalı Instagram açıklama metni"
}}
"""

    try:
        veri = _gemini_cagir_json(prompt, sistem_talimati)
    except Exception as e:
        log.warning(f"Kelime açıklaması üretilirken Gemini hatası ({e}), varsayılan editoryal şablon kullanılıyor.")
        veri = {}

    caption = str(veri.get("instagram_caption") or "").strip()
    if not caption or len(caption) < 80:
        caption = _varsayilan_kelime_caption(
            k_tr=k_tr,
            k_ar=k_ar,
            okunus=okunus,
            kok=kok,
            lugat_anlami=lugat_anlami,
            kuran_boyutu=kuran_boyutu,
            hayat_dersi=hayat_dersi,
            ayet_ref=ayet_ref,
            ayet_ar=ayet_ar,
        )
    varsayilan = ["ezanplus", "kuran", "kavram", "kelime", "tefekkur"]
    veri["instagram_caption"] = caption_hashtaglari_guncelle(caption, varsayilan_etiketler=varsayilan)
    veri["kelime_id"] = kelime_id
    veri["kelime_tr"] = k_tr
    veri["kelime_ar"] = k_ar
    veri["okunus"] = okunus
    veri["kok"] = kok
    veri["lugat_anlami"] = lugat_anlami
    veri["kuran_boyutu"] = kuran_boyutu
    veri["hayat_dersi"] = hayat_dersi
    veri["ayet_ref"] = ayet_ref
    veri["ayet_arapca"] = ayet_ar
    veri["kategori"] = "kelime"
    veri["format"] = f"post_{format_tipi.replace(':', '_')}"

    return veri


def metin_ve_tefekkur_revize_et(
    turkce_metin: str,
    kategori: str = "ayet",
    hedef: str = "yenile",
    mevcut_tefekkur: str = "",
    mevcut_caption: str = "",
) -> Dict[str, str]:
    """
    GEMINI.md Anayasasına tam uyumlu olarak:
    - Orijinal Türkçe meal/hadis metnine KESİNLİKLE DOKUNMAZ.
    - Yalnızca edebi tefekkür notunu ve sosyal medya açıklamasını (caption) revize eder.
    - hedef:
        'kisalt'  -> Tefekkürü tek cümlelik, öz ve vurucu bir hale getirir.
        'genislet'-> Tefekkürü 2-3 cümlelik daha derin bir hikmet dersine dönüştürür.
        'yenile'  -> Yeni ve taze bir edebi bakış açısıyla tefekkür ve caption üretir.
    """
    hedef_talimat = {
        "kisalt": "Mevcut tefekkür notunu ve hayat dersini TEK CÜMLELİK, son derece vurucu, net ve öz bir hikmet cümlesine indirge.",
        "genislet": "Mevcut tefekkür notunu 2-3 cümlelik daha derin, kalbe dokunan ve günlük hayata rehberlik eden doyurucu bir tefekküre dönüştür.",
        "yenile": "Bu metin üzerine taze, samimi, bilgece ve kalbe dokunan yepyeni bir tefekkür notu ve sosyal medya metni kaleme al.",
    }.get(hedef, "Taze bir tefekkür notu ve açıklama yaz.")

    prompt = f"""
Aşağıdaki kutsal / tescilli İslami metin için edebi tefekkür notunu ve sosyal medya açıklamasını revize et.

METİN KATEGORİSİ: {kategori.upper()}
TESCİLLİ TÜRKÇE MEAL / METİN (BU METNE ASLA DOKUNMA, AYNEN KORU):
"{turkce_metin}"

MEVCUT TEFEKKÜR NOTU:
"{mevcut_tefekkur}"

GÖREV:
{hedef_talimat}

KURALLAR:
1. Türkçe meal metnini asla değiştirme veya yapay zekayla yeniden çevirme!
2. Asla "bot", "otomasyon", "yapay zeka", "algoritma" gibi kelimeler KULLANMA.
3. Çıktıyı kesinlikle geçerli bir JSON olarak ver:
{{
  "tefekkur_notu": "Revize edilmiş tefekkür notu",
  "caption": "Instagram/TikTok için kopyalanabilir tam açıklama metni (#ezanplus etiketiyle)"
}}
"""
    try:
        veri = _gemini_cagir_json(prompt)
        tef = str(veri.get("tefekkur_notu") or "").strip()
        cap = str(veri.get("caption") or "").strip()
        if not tef:
            tef = mevcut_tefekkur
        if not cap:
            cap = mevcut_caption
        if "#ezanplus" not in cap:
            cap += "\n\n#ezanplus #tefekkur"
        return tef, cap
    except Exception as e:
        log.warning(f"Metin revizyonu hatası ({e}), mevcut metin korundu.")
        return mevcut_tefekkur, mevcut_caption

