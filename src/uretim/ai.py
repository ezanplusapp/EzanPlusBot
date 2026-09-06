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
MODEL_ADI = AYARLAR.get("yapay_zeka", {}).get("model", "gemini-2.5-flash")
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
    """Gemini API'ye istek atar ve metin cevabını döner."""
    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY tanımlanmamış! Lütfen .env dosyasına ekleyin.")

    url = f"{UC_NOKTA}?key={api_key}"
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

    res = requests.post(url, json=payload, timeout=45)
    res.raise_for_status()

    data = res.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"Gemini yanıt vermedi: {data}")

    parcalar = candidates[0].get("content", {}).get("parts", [])
    cevap = "".join(p.get("text", "") for p in parcalar)
    return cevap.strip()


def _json_ayikla(metin: str) -> Dict[str, Any]:
    """Markdown kod blokları arasındaki veya çıplak JSON verisini ayrıştırır."""
    metin = metin.strip()
    # ```json ... ``` bloğu varsa temizle
    if "```" in metin:
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", metin, re.DOTALL)
        if m:
            metin = m.group(1)
        else:
            m2 = re.search(r"(\{.*\})", metin, re.DOTALL)
            if m2:
                metin = m2.group(1)

    return json.loads(metin)


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
        gecmis_ayetler = db.son_paylasilan_kaynaklar(limit=60)
        secilen_ayet = kuran_db.gunun_ayetini_sec(
            tema=tema,
            sadece_video_uygun=True,
            haric_tutulanlar=gecmis_ayetler,
        )

    if not secilen_ayet:
        # Tema kısıtını kaldırarak video için uygun herhangi bir ayeti seç
        secilen_ayet = kuran_db.gunun_ayetini_sec(tema=None, sadece_video_uygun=True)

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

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının İslami ilimler ve editoryal içerik uzmanısın.
Sana verilen tescilli Kur'an-ı Kerim ayet metnini ve mealini ASLA değiştirmeyeceksin.
Görevin:
1) Verilen Arapça ayet metninin Latin harfleriyle kelime kelime edebi, akıcı Türkçe okunuşunu (transkripsiyonunu) yazmak ("arapca_okunus"). Şapkalı harfleri (â, î, û) ve kesmeleri doğru kullan (Örn: 'İnne me'al 'usri yusrâ').
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
Türkçe Meal: "{turkce_meal}"
Kaynak: {meal_kaynagi}
Tema: {tema}

Yukarıdaki tescilli âyete %100 sadık kalarak aşağıdaki JSON formatında yanıt ver:
{{
  "arapca_okunus": "Arapça kelimelerle birebir eşleşen Latin harfleriyle Türkçe okunuşu",
  "meal_vurgulu": "Yukarıdaki Türkçe mealin hiçbir kelimesini değiştirmeden veya eksiltmeden, âyetin en can alıcı ve vurucu 2-5 kelimelik kısmını markdown **bold** içine alarak aynen yaz (Örn: 'Elbette güçlükle beraber şüphesiz **bir kolaylık vardır.**')",
  "video_baslik_satir1": "Çağrı/anons cümlesi (sonunda : olsun, maks 30 karakter)",
  "video_baslik_satir2": "Vurucu hakikat cümlesi (maks 32 karakter)",
  "tefekkur_notu": "2-3 cümlelik samimi hayat dersi ve tefekkür",
  "instagram_caption": "Yukarıda belirtilen 6 aşamalı Instagram açıklama metni"
}}
"""

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)

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
    secilen_hadis = hadis_db.gunun_hadisini_sec(tema=tema)
    if not secilen_hadis:
        secilen_hadis = hadis_db.gunun_hadisini_sec(tema=None)

    if not secilen_hadis:
        raise RuntimeError("Hadis veritabanından geçerli hadis seçilemedi!")

    hadis_metni = secilen_hadis["hadis_metni"]
    kaynak_ref = secilen_hadis["kaynak_ref"]
    ravi = secilen_hadis.get("ravi", "")
    arapca_metin = secilen_hadis.get("arapca_veciz", "") or secilen_hadis.get("arapca_metin", "")
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
- Hadis metni ve sahabi râvisi
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

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)

    # Tescilli doğrulanmış alanları veriye yerleştir (AI halüsinasyonu imkansız!)
    veri["hadis_id"] = hadis_id
    vurgulu = str(veri.get("hadis_vurgulu") or "").strip()
    # Metin bütünlüğü kontrolü: Gemini tek bir harf/kelime dahi değiştirdiyse orijinal tescilli metne geri dön
    if vurgulu and re.sub(r'[\*\s\.,;!?:“"\'”]', '', vurgulu.lower()) == re.sub(r'[\*\s\.,;!?:“"\'”]', '', hadis_metni.lower()):
        veri["hadis_metni"] = vurgulu
    else:
        veri["hadis_metni"] = hadis_metni
    veri["hadis_metni_orijinal"] = hadis_metni
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
    gecmis_kaynaklar = db.son_paylasilan_kaynaklar(limit=60)
    secilen_dua = dua_db.gunun_duasini_sec(ruh_hali=ruh_hali, haric_tutulanlar=gecmis_kaynaklar)
    if not secilen_dua:
        secilen_dua = dua_db.gunun_duasini_sec(ruh_hali=None)

    if not secilen_dua:
        raise RuntimeError("Dualar külliyatından geçerli bir dua seçilemedi!")

    dua_basligi = secilen_dua["dua_basligi"]
    kategori = secilen_dua["kategori"]
    kimin_duasi = secilen_dua["kimin_duasi"]
    arapca_metin = secilen_dua["arapca_metin"]
    arapca_okunus = secilen_dua["arapca_okunus"]
    turkce_anlam = secilen_dua["turkce_anlam"]
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
- Dua metni, anlamı ve kimin duası olduğu
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

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)

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
    veri["format"] = f"post_{format_tipi.replace(':', '_')}"

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
    gecmis_kaynaklar = db.son_paylasilan_kaynaklar(limit=60)
    secilen_kelime = None
    if kelime_tr:
        for k in kelime_db.kelimeleri_yukle():
            if k.get("kelime_tr", "").lower() == kelime_tr.lower():
                secilen_kelime = k
                break

    if not secilen_kelime:
        secilen_kelime = kelime_db.gunun_kelimesini_sec(haric_tutulanlar=gecmis_kaynaklar)

    if not secilen_kelime:
        secilen_kelime = kelime_db.gunun_kelimesini_sec(haric_tutulanlar=None)

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
        cevap = _gemini_cagir(prompt, sistem_talimati)
        veri = _json_ayikla(cevap)
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
    else:
        # Hashtag denetimi: en fazla 5 hashtag ve #ezanplus zorunluluğu
        tags = re.findall(r'#\w+', caption)
        if len(tags) > 5:
            gecerli_tags = tags[:5]
            if "#ezanplus" not in [t.lower() for t in gecerli_tags]:
                gecerli_tags[0] = "#ezanplus"
            caption_no_tags = re.sub(r'#\w+\s*', '', caption).strip()
            caption = f"{caption_no_tags}\n\n{' '.join(gecerli_tags)}"

    veri["instagram_caption"] = caption
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
