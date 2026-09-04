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

from .ayar import AYARLAR, get_env
from . import db

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


def ayet_icerigi_uret(tema: Optional[str] = None) -> Dict[str, Any]:
    """
    Günün Ayeti için Elmalılı Hamdi Yazır meali, harekeli Arapça orijinali,
    tefekkür notu ve yüksek etkileşimli Instagram açıklaması üretir.
    """
    if not tema:
        tema = random.choice(TEMALAR)

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının uzman İslami içerik yöneticisi ve sosyal medya stratejistisin.
Görevin, Kur'an-ı Kerim'den büyük İslam alimi Elmalılı Muhammed Hamdi Yazır'ın muteber, akıcı ve sadeleştirilmiş mealine harfiyen uygun,
toplumun manevi yaralarına dokunan, huzur veren ve güvenilir ayet içerikleri üretmektir.
Uydurma mealler, yanlış ayet numaraları veya güvenilmez çeviriler KESİNLİKLE yasaktır.
Meal olarak her zaman Elmalılı Muhammed Hamdi Yazır'ın sadeleştirilmiş Türkçe mealini esas alırsın.

Sosyal Medya ve Algoritma Kuralı:
Modern algoritmalarda (Instagram, TikTok, Threads) 5'ten fazla hashtag spam olarak algılanmaktadır.
Bu nedenle açıklama sonunda KESİNLİKLE ve TAM OLARAK 5 ADET en alakalı hashtag (#ezanplus dahil) yer almalıdır. Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen Tema: "{tema}"

Lütfen bu tema ile ilgili çok etkileyici, kalbe dokunan bir ayet-i kerime seç.
Aşağıdaki JSON formatında eksiksiz yanıt ver:

{{
  "sure_adi": "Sure Adı (Türkçe, örn. Ankebût)",
  "sure_no": 29,
  "ayet_no": 45,
  "cuz_no": 21,
  "sure_ayet_etiket": "Ankebût Sûresi • 45. Âyet",
  "video_baslik_satir1": "Ayetin mesajına odaklanan 3-4 kelimelik vurucu 1. satır (örn. Namaz, kötülüklerden koruyan)",
  "video_baslik_satir2": "Ayetin vurucu 2. satırı (örn. en güçlü kalkandır.)",
  "arapca_metin": "Tam harekeli orijinal Arapça ayet metni",
  "arapca_okunus": "Arapça kelimelerle birebir eşleşen Latin harfleriyle Türkçe okunuşu (Örn: Utlu mâ ûhıye ileyke minel kitâbi ve ekımis-salâte innes-salâte tenhâ ‘anil fahşâi vel-munker)",
  "turkce_meal": "Elmalılı Muhammed Hamdi Yazır sadeleştirilmiş Türkçe meali",
  "tefekkur_notu": "Bu ayetin günlük hayatımıza, iç huzurumuza ve pratik yaşamımıza bakan 2-3 cümlelik çok samimi ve bilgece dersi.",
  "hafiz_adi": "Mişari Râşid el-Afâsî",
  "instagram_caption": "Instagram/TikTok için profesyonel, yüksek etkileşimli açıklama metni. Formatı tam olarak şu yapıda olmalı:\\n\\n1) Çarpıcı, merak ve duygu uyandıran açılış cümlesi/sorusu (Hook).\\n2) Tırnak içinde ayet meali ve kaynak (Örn: '...' — Ankebût Sûresi, 45 • Elmalılı Hamdi Yazır Meali)\\n3) Hayatın telaşına ve kalbe dokunan samimi tefekkür dersi.\\n4) Etkileşim çağrısı (Kaydetme 📌, sevdikleriyle paylaşma 🕊️ ve yoruma davet 💬).\\n5) Ezan Plus yönlendirmesi: 'Daha fazlası ve namaz vakitleri için profildeki linkten Ezan Plus'ı ücretsiz indirin. 📲'\\n6) VE EN SONDA KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet ayet/konu odaklı etiket. 5'ten asla fazla olamaz!)."
}}
"""

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)
    veri["kategori"] = "ayet"
    veri["format"] = "reels_9_16"
    return veri


def hadis_icerigi_uret(tema: Optional[str] = None) -> Dict[str, Any]:
    """
    Sahih Kütüb-i Sitte hadisi, ravisi, hikmet notu ve caption üretir.
    """
    if not tema:
        tema = random.choice(TEMALAR)

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının İslami ilimler ve hadis uzmanısın.
Sadece ve sadece Kütüb-i Sitte (Buhari, Müslim, Ebu Davud, Tirmizi, Nesai, İbn Mace)
kaynaklarında geçen sahih ve muteber hadis-i şerifleri seçersin.
Zayıf, mevzu veya kaynağı belirsiz rivayetler KESİNLİKLE yasaktır.

Sosyal Medya ve Algoritma Kuralı:
Açıklama sonunda KESİNLİKLE ve TAM OLARAK 5 ADET hashtag (#ezanplus dahil) yer almalıdır. Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Seçilen Tema: "{tema}"

Bu tema ile ilgili hayatımıza rehber olacak sahih bir hadis-i şerif seç.
Aşağıdaki JSON formatında yanıt ver:

{{
  "hadis_metni": "Hadis-i şerifin akıcı ve doğru Türkçe tercümesi",
  "kaynak_ravi": "Ravi ve Kaynak (Örn: Buhârî, Îmân, 1; Müslim, Îmân, 93)",
  "tefekkur_notu": "Bu nebevi öğüdün modern hayattaki karşılığı ve bize verdiği ahlaki ders (2 cümle).",
  "instagram_caption": "Instagram için ilgi çekici, samimi ve değer katan açıklama metni. Yapısı:\\n1) Vurucu açılış cümlesi (Hook)\\n2) Hadis metni ve ravisi\\n3) Kısa hayat dersi / tefekkür\\n4) Kaydet 📌 & Paylaş 🕊️ çağrısı\\n5) Ezan Plus yönlendirmesi 📲\\n6) KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet odaklı etiket)."
}}
"""

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)
    veri["kategori"] = "hadis"
    veri["format"] = "post_4_5"
    return veri


def dua_icerigi_uret(ruh_hali: Optional[str] = None) -> Dict[str, Any]:
    """
    Hâline uygun dua içeriği üretir.
    """
    haller = [
        "İç Sıkıntısı ve Daralma Hissi",
        "Gelecek Endişesi ve Sınav/İş Kaygısı",
        "Hastalık ve Şifa Talebi",
        "Şükür ve Sevinç Anı",
        "Geçim Darlığı ve Helal Rızık Arayışı",
        "Öfke ve Kararsızlık Durumu",
    ]
    if not ruh_hali:
        ruh_hali = random.choice(haller)

    sistem_talimati = """
Sen Ezan Plus mobil uygulamasının manevi rehberlik ve dua içerik üreticisisin.
Kur'an-ı Kerim ve Peygamber Efendimiz'in (s.a.v.) sahih sünnetinde yer alan duaları,
insanların günümüzdeki duygusal ve ruhsal ihtiyaçlarına derman olacak şekilde sunarsın.

Sosyal Medya ve Algoritma Kuralı:
Açıklama sonunda KESİNLİKLE ve TAM OLARAK 5 ADET hashtag (#ezanplus dahil) yer almalıdır. Asla 5'ten fazla yazma!
Çıktıyı YALNIZCA geçerli bir JSON objesi olarak ver.
"""

    prompt = f"""
Ruh Hâli / Durum: "{ruh_hali}"

Bu ruh hâlindeki bir müminin kalbine su serpecek Kur'an'dan veya Sünnet'ten bir dua seç.
Aşağıdaki JSON formatında yanıt ver:

{{
  "dua_basligi": "Duruma uygun başlık (Örn: İç Daralması ve Ferahlık İçin Dua)",
  "arapca_metin": "Duanın harekeli Arapça metni",
  "turkce_anlam": "Duanın Türkçe samimi ve doğru anlamı",
  "okunus_veya_fazilet": "Okunuşu: ... (Kaynak/Sure-Ayet). Ne zaman okunması tavsiye edilir?",
  "instagram_caption": "Instagram için kalbe dokunan dua açıklaması. Yapısı:\\n1) İçten ve duygusal bir giriş cümlesi (Hook)\\n2) Dua metni ve anlamı\\n3) 'Yoruma bir Âmin bırakarak dualara ortak olun 🤲' ve sevdiklerine gönderme çağrısı\\n4) Ezan Plus yönlendirmesi 📲\\n5) KESİNLİKLE VE TAM 5 ADET HASHTAG (#ezanplus ve 4 adet duaya özel etiket)."
}}
"""

    cevap = _gemini_cagir(prompt, sistem_talimati)
    veri = _json_ayikla(cevap)
    veri["kategori"] = "dua"
    veri["format"] = "post_4_5"
    return veri
