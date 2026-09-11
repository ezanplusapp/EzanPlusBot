"""
denetleyici.py — Ezan Plus Yayın Öncesi Kalite, Boyut ve Taşma Denetim Motoru

Paylaşım öncesinde tüm video, kart görseli, tescilli metin ve mizanpaj verilerini
sıkı bir kalite kontrol filtresinden geçirir:
1. Eksik Metin & Bütünlük Denetimi (Arapça, Meal, Tefekkür, Başlıklar, Caption, Hashtag'ler)
2. Boyut & Çözünürlük Denetimi (1080x1920 Reels/Story, 1080x1350 Feed, dosya boyut limitleri)
3. Mizanpaj & Taşma Denetimi (Piksel bazlı mizanpaj çakışma ve emniyet aralığı testi)
4. Sıfır Halüsinasyon & Tescilli Külliyat Bütünlüğü Denetimi
5. Marka Dili & Sıfır Bot İbaresi Denetimi
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from . import db
from .uretim.kart import parse_markdown_bold, wrap_mixed_tokens

log = logging.getLogger(__name__)

# Yasaklı Yapay / Bot İfadeleri (GEMINI.md Anayasa Kuralı)
YASAKLI_IFADELER = [
    "bot",
    "otomasyon",
    "yapay zeka",
    "yapay zekâ",
    "gemini",
    "chatgpt",
    "openai",
    "ai üretimi",
    "otomatik üretilmiştir",
    "otomatik paylaşımdır",
]


@dataclass
class DenetimSonucu:
    """Yayın öncesi kalite kontrolünün ayrıntılı sonuç raporu."""
    gecerli: bool
    kategori: str
    hatalar: List[str] = field(default_factory=list)
    uyarilar: List[str] = field(default_factory=list)
    metrikler: Dict[str, Any] = field(default_factory=dict)

    def formatli_rapor(self, kisa: bool = False) -> str:
        """Telegram veya loglar için insan tarafından okunabilir durum raporu üretir."""
        if self.gecerli:
            durum_ikon = "✅"
            baslik = "<b>YAYIN ÖNCESİ KALİTE KONTROLÜ BAŞARILI</b>"
        else:
            durum_ikon = "🚨"
            baslik = "<b>YAYIN ÖNCESİ KALİTE KONTROL HATASI</b>"

        satirlar = [f"{durum_ikon} {baslik}", f"📁 <i>Kategori:</i> {self.kategori.upper()}"]

        if self.metrikler:
            m = self.metrikler
            detaylar = []
            if "cozunurluk" in m:
                detaylar.append(f"📐 {m['cozunurluk']}")
            if "dosya_boyutu_kb" in m:
                detaylar.append(f"💾 {m['dosya_boyutu_kb']} KB")
            if "sure_sn" in m:
                detaylar.append(f"⏱️ {m['sure_sn']:.1f} sn")
            if "serbest_alan_px" in m:
                detaylar.append(f"📏 Emniyet: {m['serbest_alan_px']}px")
            if detaylar:
                satirlar.append("📊 <i>Metrikler:</i> " + " • ".join(detaylar))

        if self.hatalar:
            satirlar.append("\n❌ <b>Kritik Hatalar (Yayın Durduruldu):</b>")
            for h in self.hatalar:
                satirlar.append(f"  • {h}")

        if self.uyarilar:
            satirlar.append("\n⚠️ <b>Uyarılar:</b>")
            for u in self.uyarilar:
                satirlar.append(f"  • {u}")

        return "\n".join(satirlar)


def _metin_temizle(metin: str) -> str:
    """Noktalama, tırnak, markdown ve boşlukları atarak çıplak harfleri bırakır."""
    if not metin:
        return ""
    return re.sub(r'[\*\s\.,;!?:“"\'”\(\)\[\]\-_—/]', '', metin.lower())


def denetle_metin(veri: Dict[str, Any], kategori: str = "ayet") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Eksik metin, yasaklı kelimeler ve hashtag kurallarını denetler."""
    hatalar: List[str] = []
    uyarilar: List[str] = []
    metrikler: Dict[str, Any] = {}

    turkce = str(veri.get("turkce_metin") or veri.get("turkce_meal") or veri.get("hadis_metni") or "").strip()
    arapca = str(veri.get("arapca_metin") or "").strip()
    kaynak = str(veri.get("kaynak") or veri.get("baslik") or "").strip()
    tefekkur = str(veri.get("tefekkur") or veri.get("tefekkur_notu") or "").strip()
    caption = str(veri.get("caption") or "").strip()

    # 1. Türkçe Metin Denetimi
    if not turkce or len(turkce) < 5:
        hatalar.append("Türkçe meal/metin eksik veya çok kısa (<5 karakter).")
    metrikler["turkce_uzunluk"] = len(turkce)

    # 2. Arapça Metin Denetimi
    if not arapca or len(arapca) < 3:
        hatalar.append("Arapça orijinal metin eksik veya boş.")
    else:
        # Arapça Unicode karakter kontrolü (\u0600 - \u06FF)
        has_arabic = any(0x0600 <= ord(c) <= 0x06FF for c in arapca)
        if not has_arabic:
            hatalar.append("Arapça metin alanında geçerli Arapça harf tespit edilemedi.")
    metrikler["arapca_uzunluk"] = len(arapca)

    # 3. Kaynak ve Tefekkür Denetimi
    if not kaynak or len(kaynak) < 3:
        hatalar.append("Kaynak / Künye referansı eksik.")
    if not tefekkur or len(tefekkur) < 15:
        hatalar.append("Günün Hikmeti / Tefekkür notu eksik veya yetersiz (<15 karakter).")

    # 4. Reels Video Başlıkları Denetimi
    if kategori in ("ayet", "reels"):
        s1 = str(veri.get("video_baslik_satir1") or "").strip()
        s2 = str(veri.get("video_baslik_satir2") or "").strip()
        if s1 and len(s1) > 50:
            uyarilar.append(f"Video başlık 1. satırı uzun ({len(s1)} karakter, önerilen: <35).")
        if s2 and len(s2) > 50:
            uyarilar.append(f"Video başlık 2. satırı uzun ({len(s2)} karakter, önerilen: <35).")

    # 5. Caption ve Hashtag Denetimi
    if not caption or len(caption) < 20:
        hatalar.append("Sosyal medya açıklama metni (caption) eksik veya çok kısa (<20 karakter).")
    if not caption or "#ezanplus" not in caption.lower():
        hatalar.append("Açıklama metninde zorunlu '#ezanplus' etiketi bulunamadı.")
    if caption:
        hashtags = re.findall(r'#\w+', caption)
        metrikler["hashtag_sayisi"] = len(hashtags)
        if len(hashtags) < 3:
            uyarilar.append(f"Hashtag sayısı az ({len(hashtags)} adet, asgari 5 önerilir).")
        elif len(hashtags) > 10:
            uyarilar.append(f"Hashtag sayısı fazla ({len(hashtags)} adet, azami 5 önerilir).")

    # 6. Yasaklı Bot / AI İfadeleri Kontrolü (Marka Standartı)
    butun_metinler = f"{turkce} {caption} {tefekkur} {kaynak}".lower()
    for yasakli in YASAKLI_IFADELER:
        if re.search(rf"\b{re.escape(yasakli)}\b", butun_metinler):
            hatalar.append(f"Yasaklı bot/yapay zeka ifadesi tespit edildi: '{yasakli}' (GEMINI.md anayasası ihlali).")

    return hatalar, uyarilar, metrikler


def denetle_gorsel_dosyalari(gorsel_yollari: List[str], beklenen_oranlar: Optional[List[str]] = None) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Oluşturulan kart görsellerinin dosya varlığını, boyutunu ve piksel ölçülerini denetler."""
    hatalar: List[str] = []
    uyarilar: List[str] = []
    metrikler: Dict[str, Any] = {}

    if not gorsel_yollari:
        hatalar.append("Paylaşılacak hiçbir görsel dosyası bulunamadı (gorsel_yollari boş).")
        return hatalar, uyarilar, metrikler

    oranlar = beklenen_oranlar or (["4:5", "9:16"] if len(gorsel_yollari) >= 2 else ["4:5"])
    cozunurlukler = []

    for idx, yol_str in enumerate(gorsel_yollari):
        p = Path(yol_str)
        if not p.exists() or not p.is_file():
            hatalar.append(f"Görsel dosyası diskte bulunamadı: {p.name}")
            continue

        boyut_kb = p.stat().st_size // 1024
        if boyut_kb < 30:
            hatalar.append(f"Görsel dosya boyutu şüpheli derecede küçük: {p.name} ({boyut_kb} KB, asgari 30 KB).")

        try:
            with Image.open(p) as im:
                w, h = im.size
                cozunurlukler.append(f"{w}x{h}")
                hedef_oran = oranlar[idx] if idx < len(oranlar) else "serbest"

                if hedef_oran == "4:5":
                    if (w, h) != (1080, 1350):
                        hatalar.append(f"Görsel feed ölçüsü hatalı: {p.name} -> {w}x{h} px (Beklenen: 1080x1350).")
                elif hedef_oran == "9:16":
                    if (w, h) != (1080, 1920):
                        hatalar.append(f"Görsel story ölçüsü hatalı: {p.name} -> {w}x{h} px (Beklenen: 1080x1920).")

        except Exception as e:
            hatalar.append(f"Görsel dosyası açılamadı veya bozuk: {p.name} ({e})")

    if cozunurlukler:
        metrikler["cozunurluk"] = " / ".join(cozunurlukler)
    metrikler["gorsel_sayisi"] = len(gorsel_yollari)

    return hatalar, uyarilar, metrikler


def denetle_video_dosyasi(video_yolu: str, min_sure: float = 3.0) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Oluşturulan MP4 video dosyasının varlığını, boyutunu, süresini ve çözünürlüğünü denetler."""
    hatalar: List[str] = []
    uyarilar: List[str] = []
    metrikler: Dict[str, Any] = {}

    if not video_yolu:
        hatalar.append("Video dosya yolu belirtilmemiş (boş).")
        return hatalar, uyarilar, metrikler

    p = Path(video_yolu)
    if not p.exists() or not p.is_file():
        hatalar.append(f"Video dosyası diskte bulunamadı: {p.name}")
        return hatalar, uyarilar, metrikler

    boyut_kb = p.stat().st_size // 1024
    metrikler["dosya_boyutu_kb"] = boyut_kb
    if boyut_kb < 300:
        hatalar.append(f"Video dosya boyutu çok küçük ({boyut_kb} KB, asgari 300 KB).")

    try:
        import imageio
        reader = imageio.get_reader(str(p))
        meta = reader.get_meta_data()
        size = meta.get("size")
        fps = meta.get("fps", 0)
        duration = meta.get("duration", 0)
        reader.close()

        if size:
            w, h = size
            metrikler["cozunurluk"] = f"{w}x{h}"
            if (w, h) != (1080, 1920):
                hatalar.append(f"Video çözünürlüğü 9:16 standartına uymuyor: {w}x{h} px (Beklenen: 1080x1920).")

        if duration:
            metrikler["sure_sn"] = duration
            if duration < min_sure:
                hatalar.append(f"Video süresi çok kısa: {duration:.1f} sn (Asgari: {min_sure} sn).")
            elif duration > 90.0:
                uyarilar.append(f"Video süresi Reels/Shorts sınırı için uzun: {duration:.1f} sn.")

        if fps and not (24 <= fps <= 60):
            uyarilar.append(f"Alışılmadık kare hızı (FPS): {fps}")

    except Exception as e:
        hatalar.append(f"Video dosyası okunamadı veya akış bozuk: {p.name} ({e})")

    return hatalar, uyarilar, metrikler


def denetle_reels_mizanpaj(
    sure_ayet: str,
    turkce_meal: str,
    arapca_metin: str,
    arapca_okunus: Optional[str] = None,
    tefekkur_notu: str = "",
    s1: str = "",
    s2: str = "",
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """
    Reels video motorunun (_SayfaVerisi) tüm sayfalarındaki mizanpajı simüle ederek
    Arapça, Latin okunuş, Türkçe meal ve Tefekkür kutusu arasındaki dikey boşlukları,
    çakışmaları ve taşmaları piksel piksel test eder.
    """
    hatalar: List[str] = []
    uyarilar: List[str] = []
    metrikler: Dict[str, Any] = {}

    try:
        from .uretim.video import _SayfaVerisi, _meal_parcala, akilli_sayfa_araliklari, arapca_kelimeleri_ayristir

        ar_kelimeler = arapca_kelimeleri_ayristir(arapca_metin)
        tr_kelimeler = (arapca_okunus or "").split()
        toplam_kelime = len(ar_kelimeler)

        # Sayfa bölme algoritması (14 kelimeye kadar tek sayfa, 15+ kelimede çoklu sayfa)
        if toplam_kelime <= 14:
            sayfa_sayisi = 1
        elif toplam_kelime <= 28:
            sayfa_sayisi = 2
        else:
            sayfa_sayisi = math.ceil(toplam_kelime / 14)

        sayfa_araliklari = akilli_sayfa_araliklari(ar_kelimeler, arapca_metin, None, sayfa_sayisi)
        split_ratios = [w_e / max(1, toplam_kelime) for _, w_e in sayfa_araliklari[:-1]]
        meal_parcalari = _meal_parcala(turkce_meal, sayfa_sayisi, split_ratios=split_ratios)

        en_dar_serbest_alan = 9999

        for p_idx, (s_w, e_w) in enumerate(sayfa_araliklari):
            page_ar = ar_kelimeler[s_w:e_w]
            page_tr = tr_kelimeler[s_w:e_w] if tr_kelimeler else []
            page_meal = meal_parcalari[p_idx] if p_idx < len(meal_parcalari) else turkce_meal

            sv = _SayfaVerisi(
                p_idx=p_idx,
                sayfa_sayisi=sayfa_sayisi,
                start_w=s_w,
                end_w=e_w,
                page_ar=page_ar,
                page_tr=page_tr,
                page_meal=page_meal,
                sure_ayet=sure_ayet,
                s1=s1 or "Günün Ayeti:",
                s2=s2 or "Tefekkür ve İbadet",
                tef=tefekkur_notu or "Kalpleri mutmain kılan yegane hakikat Allah'ı anmaktır.",
                hafiz_adi="Mişari Râşid el-Afâsî",
            )

            # Net serbest meal boşluğu (Meal ile Tefekkür arasındaki emniyet tamponu)
            net_serbest = getattr(sv, "net_serbest_meal", 50)
            if net_serbest < en_dar_serbest_alan:
                en_dar_serbest_alan = net_serbest

            # Çakışma kontrolü
            if net_serbest < 0:
                hatalar.append(
                    f"Sayfa {p_idx + 1}/{sayfa_sayisi}: Meal ile Tefekkür kutusu arasında dikey ÇAKIŞMA tespit edildi! "
                    f"Taşma miktarı: {abs(net_serbest)}px."
                )
            elif net_serbest < 12:
                uyarilar.append(
                    f"Sayfa {p_idx + 1}/{sayfa_sayisi}: Serbest dikey boşluk çok dar ({net_serbest}px, asgari 15px önerilir)."
                )

            # Arapça punto emniyet kontrolü
            if sv.pt_ar < 46:
                uyarilar.append(f"Sayfa {p_idx + 1}: Arapça punto çok küçük ({sv.pt_ar}pt).")

            # Türkçe meal punto emniyet kontrolü
            if sv.pt_meal < 36:
                uyarilar.append(f"Sayfa {p_idx + 1}: Türkçe meal puntosu çok küçük ({sv.pt_meal}pt).")

        metrikler["serbest_alan_px"] = en_dar_serbest_alan
        metrikler["sayfa_sayisi"] = sayfa_sayisi

    except Exception as e:
        hatalar.append(f"Reels mizanpaj simülasyonu çalıştırılamadı: {e}")

    return hatalar, uyarilar, metrikler


def denetle_tescilli_kaynak(kategori: str, veri: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Tescilli yerel veritabanı (Kur'an, Hadis, Dua, Kelime) ile metin bütünlüğünü doğrular."""
    hatalar: List[str] = []
    uyarilar: List[str] = []

    try:
        if kategori in ("ayet", "reels"):
            from . import kuran_db
            sure_no = veri.get("sure_no")
            ayet_no = veri.get("ayet_no")
            if sure_no and ayet_no:
                db_ayet = kuran_db.ayet_getir(int(sure_no), int(ayet_no))
                if not db_ayet:
                    hatalar.append(f"Kur'an veritabanında {sure_no}:{ayet_no} âyeti bulunamadı!")
                else:
                    turkce = str(veri.get("turkce_meal") or veri.get("turkce_metin") or "")
                    c_turkce = _metin_temizle(turkce)
                    c_elmalili = _metin_temizle(db_ayet.get("meal_elmalili", ""))
                    c_diyanet = _metin_temizle(db_ayet.get("meal_diyanet", ""))

                    if c_turkce != c_elmalili and c_turkce != c_diyanet:
                        if c_turkce in c_elmalili or c_turkce in c_diyanet:
                            pass
                        else:
                            uyarilar.append("Türkçe meal tescilli veritabanındaki Elmalılı veya Diyanet metninden farklılık gösteriyor.")

        elif kategori == "hadis":
            from . import hadis_db
            hadis_id = veri.get("hadis_id")
            if hadis_id:
                db_hadis = hadis_db.hadis_getir(int(hadis_id))
                if not db_hadis:
                    hatalar.append(f"Hadis veritabanında #{hadis_id} nolu sahih hadis bulunamadı!")

    except Exception as e:
        log.warning(f"Tescilli kaynak kontrolü sırasında hata oluştu: {e}")

    return hatalar, uyarilar


def denetle_paylasim(paylasim_id: int) -> DenetimSonucu:
    """
    Belirtilen paylaşım ID'sine ait tüm verileri, medya dosyalarını ve mizanpajı
    kapsamlı bir kalite kontrolünden geçirir.
    """
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        return DenetimSonucu(
            gecerli=False,
            kategori="bilinmiyor",
            hatalar=[f"Paylaşım ID #{paylasim_id} veritabanında bulunamadı!"],
        )

    kategori = kayit.get("kategori", "ayet")
    format_tipi = kayit.get("format", "")

    tum_hatalar: List[str] = []
    tum_uyarilar: List[str] = []
    birlesik_metrikler: Dict[str, Any] = {}

    # 1. Metin ve İçerik Bütünlüğü Denetimi
    m_hatalar, m_uyarilar, m_metrikler = denetle_metin(kayit, kategori=kategori)
    tum_hatalar.extend(m_hatalar)
    tum_uyarilar.extend(m_uyarilar)
    birlesik_metrikler.update(m_metrikler)

    # 2. Tescilli Külliyat Doğrulaması
    k_hatalar, k_uyarilar = denetle_tescilli_kaynak(kategori, kayit)
    tum_hatalar.extend(k_hatalar)
    tum_uyarilar.extend(k_uyarilar)

    # 3. Medya ve Dosya Boyutu Denetimi
    if format_tipi == "reels_9_16" or kayit.get("video_yolu"):
        v_yolu = kayit.get("video_yolu")
        v_hatalar, v_uyarilar, v_metrikler = denetle_video_dosyasi(v_yolu)
        tum_hatalar.extend(v_hatalar)
        tum_uyarilar.extend(v_uyarilar)
        birlesik_metrikler.update(v_metrikler)

        # Reels Mizanpaj Çakışma Denetimi (Yalnızca Âyet tilavet şablonu için)
        if kategori in ("ayet", "reels"):
            r_hatalar, r_uyarilar, r_metrikler = denetle_reels_mizanpaj(
                sure_ayet=kayit.get("baslik", "Günün Ayeti"),
                turkce_meal=kayit.get("turkce_metin", ""),
                arapca_metin=kayit.get("arapca_metin", ""),
                arapca_okunus=kayit.get("arapca_okunus"),
                tefekkur_notu=kayit.get("tefekkur", ""),
                s1=kayit.get("video_baslik_satir1", ""),
                s2=kayit.get("video_baslik_satir2", ""),
            )
            tum_hatalar.extend(r_hatalar)
            tum_uyarilar.extend(r_uyarilar)
            birlesik_metrikler.update(r_metrikler)

    else:
        # Görsel Kartlar (4:5 ve 9:16)
        g_yollari = kayit.get("gorsel_yollari") or []
        g_hatalar, g_uyarilar, g_metrikler = denetle_gorsel_dosyalari(g_yollari)
        tum_hatalar.extend(g_hatalar)
        tum_uyarilar.extend(g_uyarilar)
        birlesik_metrikler.update(g_metrikler)

    gecerli = len(tum_hatalar) == 0

    sonuc = DenetimSonucu(
        gecerli=gecerli,
        kategori=kategori,
        hatalar=tum_hatalar,
        uyarilar=tum_uyarilar,
        metrikler=birlesik_metrikler,
    )

    if gecerli:
        log.info(f"Paylaşım #{paylasim_id} ({kategori.upper()}) kalite kontrolünden başarıyla GEÇTİ.")
    else:
        log.error(f"Paylaşım #{paylasim_id} ({kategori.upper()}) kalite kontrolünden GEÇEMEDİ! Hatalar: {tum_hatalar}")

    return sonuc


def otomatik_onar(paylasim_id: int) -> Tuple[bool, List[str]]:
    """
    Tespit edilen kalite, boyut veya mizanpaj hatalarını akıllı telafi algoritmalarıyla otomatik olarak onarır.
    Düzeltilen alanları veritabanına kaydeder, gerekiyorsa medyayı optimize ederek yeniden üretir
    ve ikinci bir doğrulama süzgecinden geçirir.

    Döner: (onarıldı_mı: bool, yapılan_düzeltmeler: List[str])
    """
    import time
    kayit = db.paylasim_getir(paylasim_id)
    if not kayit:
        return False, ["Paylaşım kaydı bulunamadı."]

    ilk_denetim = denetle_paylasim(paylasim_id)
    if ilk_denetim.gecerli:
        return True, ["İçerik zaten geçerli, onarıma ihtiyaç duyulmadı."]

    duzeltmeler: List[str] = []
    guncellemeler: Dict[str, Any] = {}
    kategori = kayit.get("kategori", "ayet")
    format_tipi = kayit.get("format", "")

    # 1. Caption & Hashtag Telafisi
    caption = str(kayit.get("caption") or "").strip()
    caption_degisti = False

    # Yasaklı ifadeleri temizle
    for yasakli in YASAKLI_IFADELER:
        if re.search(rf"\b{re.escape(yasakli)}\b", caption, flags=re.IGNORECASE):
            caption = re.sub(rf"\b{re.escape(yasakli)}\b", "", caption, flags=re.IGNORECASE).strip()
            caption_degisti = True
            duzeltmeler.append(f"Açıklama metninden yasaklı '{yasakli}' ibaresi temizlendi.")

    if not caption or len(caption) < 20:
        baslik = kayit.get("baslik", "Ezan Plus")
        metin = kayit.get("turkce_metin", "")
        caption = f"“{metin}”\n\n{baslik}"
        caption_degisti = True
        duzeltmeler.append("Eksik açıklama metni tescilli külliyat içeriğinden otomatik oluşturuldu.")

    from .uretim.ai import caption_hashtaglari_guncelle
    kategori_varsayilan = {
        "ayet": ["ezanplus", "kuran", "ayet", "tilavet", "tefekkur"],
        "hadis": ["ezanplus", "hadis", "sunnet", "tefekkur", "dua"],
        "dua": ["ezanplus", "dua", "niyaz", "huzur", "tefekkur"],
        "kelime": ["ezanplus", "kuran", "kavram", "kelime", "tefekkur"],
    }
    varsayilan_tags = kategori_varsayilan.get(kategori, ["ezanplus", "ayet", "kuran", "dua", "huzur"])
    yeni_caption = caption_hashtaglari_guncelle(caption, varsayilan_etiketler=varsayilan_tags)
    if yeni_caption != caption:
        caption = yeni_caption
        caption_degisti = True
        duzeltmeler.append("Açıklama metni etiketleri normalize edildi (tekilleştirildi, #ezanplus garantilendi).")

    if caption_degisti:
        guncellemeler["caption"] = caption

    # 2. Tescilli Külliyat ile Metin Eşitleme (Halüsinasyon Telafisi)
    turkce_metin = kayit.get("turkce_metin", "")
    if kategori in ("ayet", "reels"):
        from . import kuran_db
        sure_no = kayit.get("sure_no")
        ayet_no = kayit.get("ayet_no")
        if not (sure_no and ayet_no):
            m_s = re.search(r'(\d+)\.\s*(?:Sure|Sûre)', kayit.get("baslik", ""))
            m_a = re.search(r'(\d+)\.\s*(?:Ayet|Âyet)', kayit.get("baslik", ""))
            if m_s and m_a:
                sure_no, ayet_no = int(m_s.group(1)), int(m_a.group(1))

        if sure_no and ayet_no:
            db_ayet = kuran_db.ayet_getir(int(sure_no), int(ayet_no))
            if db_ayet:
                c_turkce = _metin_temizle(turkce_metin)
                c_elmalili = _metin_temizle(db_ayet.get("meal_elmalili", ""))
                c_diyanet = _metin_temizle(db_ayet.get("meal_diyanet", ""))
                if c_turkce != c_elmalili and c_turkce != c_diyanet:
                    guncellemeler["turkce_metin"] = db_ayet["meal_elmalili"]
                    guncellemeler["arapca_metin"] = db_ayet["arapca_metin"]
                    turkce_metin = db_ayet["meal_elmalili"]
                    duzeltmeler.append("Türkçe meal tescilli Kur'an veritabanı (Elmalılı) ile %100 eşitlendi.")

    elif kategori == "hadis":
        from . import hadis_db
        hadis_id = kayit.get("hadis_id")
        if hadis_id:
            db_hadis = hadis_db.hadis_getir(int(hadis_id))
            if db_hadis:
                c_turkce = _metin_temizle(turkce_metin)
                c_hadis = _metin_temizle(db_hadis.get("hadis_metni", ""))
                if c_turkce != c_hadis:
                    guncellemeler["turkce_metin"] = db_hadis["hadis_metni"]
                    turkce_metin = db_hadis["hadis_metni"]
                    duzeltmeler.append("Hadis metni tescilli Riyâzü's-Sâlihîn külliyatı ile eşitlendi.")

    # 3. Reels Dikey Mizanpaj Çakışması Telafisi
    if format_tipi == "reels_9_16" and kategori in ("ayet", "reels"):
        r_hatalar, _, r_metrikler = denetle_reels_mizanpaj(
            sure_ayet=kayit.get("baslik", "Günün Ayeti"),
            turkce_meal=turkce_metin,
            arapca_metin=kayit.get("arapca_metin", ""),
            arapca_okunus=kayit.get("arapca_okunus"),
            tefekkur_notu=kayit.get("tefekkur", ""),
            s1=kayit.get("video_baslik_satir1", ""),
            s2=kayit.get("video_baslik_satir2", ""),
        )
        if r_hatalar or (r_metrikler.get("serbest_alan_px", 999) < 10) or ("turkce_metin" in guncellemeler) or ("arapca_metin" in guncellemeler):
            log.warning("Mizanpaj taşması veya güncellenen tescilli metin tespit edildi, güvenli punto override ile video yeniden üretiliyor...")
            try:
                from .uretim.video import reels_videosu_uret
                from .uretim.ses import ayet_kelime_zamanlari_getir
                sure_no = kayit.get("sure_no", 94)
                ayet_no = kayit.get("ayet_no", 5)
                kelime_zamanlari = ayet_kelime_zamanlari_getir(int(sure_no), int(ayet_no)) if sure_no and ayet_no else None
                yeni_video = reels_videosu_uret(
                    sure_ayet=kayit.get("baslik", "Günün Ayeti"),
                    turkce_meal=turkce_metin,
                    ses_yolu=kayit.get("ses_yolu"),
                    arapca_metin=kayit.get("arapca_metin"),
                    arapca_okunus=kayit.get("arapca_okunus"),
                    video_baslik_satir1=kayit.get("video_baslik_satir1"),
                    video_baslik_satir2=kayit.get("video_baslik_satir2"),
                    tefekkur_notu=kayit.get("tefekkur"),
                    hafiz_adi=kayit.get("hafiz_adi", "Mişari Râşid el-Afâsî"),
                    pt_ar_override=76,
                    kelime_zamanlari=kelime_zamanlari,
                )
                guncellemeler["video_yolu"] = str(yeni_video)
                duzeltmeler.append("Video, güncellenen tescilli metin ve 76pt güvenlik tavanı ile yeniden render edildi.")
            except Exception as e:
                log.error(f"Otomatik Reels yeniden render hatası: {e}")

    # 4. Görsel Kart Boyut / Format Eksikliği Telafisi
    else:
        g_yollari = kayit.get("gorsel_yollari") or []
        g_hatalar, _, _ = denetle_gorsel_dosyalari(g_yollari)
        if g_hatalar or len(g_yollari) < 2 or ("turkce_metin" in guncellemeler) or ("arapca_metin" in guncellemeler):
            log.warning("Görsel boyut, eksik dosya veya güncellenen metin tespit edildi, şablonlar yeniden çiziliyor...")
            try:
                from .uretim import kart as sablon_ciz
                kategori = kayit.get("kategori", "hadis")
                dosya_eki = int(time.time())

                if kategori == "hadis":
                    p_4_5 = sablon_ciz.hadis_karti_ciz(
                        hadis_metni=turkce_metin,
                        kaynak_ravi=kayit.get("kaynak"),
                        tefekkur_notu=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"hadis_4_5_fix_{dosya_eki}.png",
                        format_tipi="4:5",
                        arapca_metin=kayit.get("arapca_metin"),
                    )
                    p_9_16 = sablon_ciz.hadis_karti_ciz(
                        hadis_metni=turkce_metin,
                        kaynak_ravi=kayit.get("kaynak"),
                        tefekkur_notu=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"hadis_9_16_fix_{dosya_eki}.png",
                        format_tipi="9:16",
                        arapca_metin=kayit.get("arapca_metin"),
                    )
                    guncellemeler["gorsel_yollari"] = [str(p_4_5), str(p_9_16)]
                    duzeltmeler.append("Hadis kartları standart 4:5 Feed ve 9:16 Story formatlarında yeniden render edildi.")

                elif kategori == "ayet":
                    p_4_5 = sablon_ciz.ayet_karti_ciz(
                        sure_ayet=kayit.get("baslik", "Günün Ayeti"),
                        turkce_meal=turkce_metin,
                        arapca_metin=kayit.get("arapca_metin"),
                        tefekkur_notu=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"ayet_4_5_fix_{dosya_eki}.png",
                        format_tipi="4:5",
                    )
                    p_9_16 = sablon_ciz.ayet_karti_ciz(
                        sure_ayet=kayit.get("baslik", "Günün Ayeti"),
                        turkce_meal=turkce_metin,
                        arapca_metin=kayit.get("arapca_metin"),
                        tefekkur_notu=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"ayet_9_16_fix_{dosya_eki}.png",
                        format_tipi="9:16",
                    )
                    guncellemeler["gorsel_yollari"] = [str(p_4_5), str(p_9_16)]
                    duzeltmeler.append("Ayet kartları standart 4:5 Feed ve 9:16 Story formatlarında yeniden render edildi.")

                elif kategori == "dua":
                    p_4_5 = sablon_ciz.dua_karti_ciz(
                        dua_basligi=kayit.get("baslik", "Günün Duası"),
                        turkce_anlam=turkce_metin,
                        arapca_metin=kayit.get("arapca_metin"),
                        okunus_veya_fazilet=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"dua_4_5_fix_{dosya_eki}.png",
                        format_tipi="4:5",
                    )
                    p_9_16 = sablon_ciz.dua_karti_ciz(
                        dua_basligi=kayit.get("baslik", "Günün Duası"),
                        turkce_anlam=turkce_metin,
                        arapca_metin=kayit.get("arapca_metin"),
                        okunus_veya_fazilet=kayit.get("tefekkur"),
                        cikti_dosya_adi=f"dua_9_16_fix_{dosya_eki}.png",
                        format_tipi="9:16",
                    )
                    guncellemeler["gorsel_yollari"] = [str(p_4_5), str(p_9_16)]
                    duzeltmeler.append("Dua kartları standart 4:5 Feed ve 9:16 Story formatlarında yeniden render edildi.")

                elif kategori == "kelime":
                    p_4_5 = sablon_ciz.kelime_karti_ciz(
                        kelime_tr=kayit.get("baslik", "Kur'an Sözlüğü"),
                        kelime_ar=kayit.get("arapca_metin", ""),
                        lugat_anlami=turkce_metin,
                        hayat_dersi=kayit.get("tefekkur", ""),
                        cikti_dosya_adi=f"kelime_4_5_fix_{dosya_eki}.png",
                        format_tipi="4:5",
                    )
                    p_9_16 = sablon_ciz.kelime_karti_ciz(
                        kelime_tr=kayit.get("baslik", "Kur'an Sözlüğü"),
                        kelime_ar=kayit.get("arapca_metin", ""),
                        lugat_anlami=turkce_metin,
                        hayat_dersi=kayit.get("tefekkur", ""),
                        cikti_dosya_adi=f"kelime_9_16_fix_{dosya_eki}.png",
                        format_tipi="9:16",
                    )
                    guncellemeler["gorsel_yollari"] = [str(p_4_5), str(p_9_16)]
                    duzeltmeler.append("Kur'an Sözlüğü kartları 4:5 Feed ve 9:16 Story formatlarında yeniden render edildi.")

            except Exception as e:
                log.error(f"Otomatik kart yeniden render hatası: {e}")

    # Yapılan değişiklikleri veritabanına işle
    if guncellemeler:
        db.paylasim_guncelle(paylasim_id, **guncellemeler)

    # İkinci Doğrulama Geçişi (Onarım Gerçekleşti mi?)
    ikinci_denetim = denetle_paylasim(paylasim_id)
    if ikinci_denetim.gecerli:
        log.info(f"Paylaşım #{paylasim_id} başarıyla otomatik onarıldı! Düzeltmeler: {duzeltmeler}")
        return True, duzeltmeler
    else:
        log.error(f"Paylaşım #{paylasim_id} otomatik onarılamadı! Kalan hatalar: {ikinci_denetim.hatalar}")
        return False, ikinci_denetim.hatalar
