"""
tests/test_yeni_icerik_turleri.py
Hadis-i Şerif ve Günün Duası görsel kart motorunun ve veritabanı kaydının testleri.
"""

from pathlib import Path
from PIL import Image
from src.uretim.kart import hadis_karti_ciz, dua_karti_ciz, ayet_karti_ciz
from src import db


def test_hadis_kartlari():
    # 4:5 Testi
    p_45 = hadis_karti_ciz(
        hadis_metni="İki nimet vardır ki insanların çoğu bunlar hususunda aldanmıştır: Sağlık ve boş vakit.",
        kaynak_ravi="Buhârî, Rikâk, 1",
        tefekkur_notu="Zaman ve sıhhat telafisi olmayan nebevi emanetlerdir. Kaybetmeden önce kadrini bilmek gerekir.",
        cikti_dosya_adi="test_unit_hadis_45.png",
        format_tipi="4:5",
    )
    assert p_45.exists()
    with Image.open(p_45) as im:
        assert im.size == (1080, 1350)

    # 9:16 Testi
    p_916 = hadis_karti_ciz(
        hadis_metni="İki nimet vardır ki insanların çoğu bunlar hususunda aldanmıştır: Sağlık ve boş vakit.",
        kaynak_ravi="Buhârî, Rikâk, 1",
        tefekkur_notu="Zaman ve sıhhat telafisi olmayan nebevi emanetlerdir. Kaybetmeden önce kadrini bilmek gerekir.",
        cikti_dosya_adi="test_unit_hadis_916.png",
        format_tipi="9:16",
    )
    assert p_916.exists()
    with Image.open(p_916) as im:
        assert im.size == (1080, 1920)


def test_dua_kartlari():
    # 4:5 Testi
    p_45 = dua_karti_ciz(
        dua_basligi="Rabbena Duası • Dünya ve Ahiret Hayrı",
        turkce_anlam="Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.",
        arapca_metin="رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        arapca_okunus="Rabbenâ âtinâ fi'd-dünyâ haseneten ve fi'l-âhirati haseneten ve kınâ azâbe'n-nâr.",
        okunus_veya_fazilet="Bakara Sûresi, 201. Âyet. Efendimiz'in (s.a.v.) en çok okuduğu dualardandır.",
        cikti_dosya_adi="test_unit_dua_45.png",
        format_tipi="4:5",
    )
    assert p_45.exists()
    with Image.open(p_45) as im:
        assert im.size == (1080, 1350)

    # 9:16 Testi
    p_916 = dua_karti_ciz(
        dua_basligi="Rabbena Duası • Dünya ve Ahiret Hayrı",
        turkce_anlam="Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.",
        arapca_metin="رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        arapca_okunus="Rabbenâ âtinâ fi'd-dünyâ haseneten ve fi'l-âhirati haseneten ve kınâ azâbe'n-nâr.",
        okunus_veya_fazilet="Bakara Sûresi, 201. Âyet. Efendimiz'in (s.a.v.) en çok okuduğu dualardandır.",
        cikti_dosya_adi="test_unit_dua_916.png",
        format_tipi="9:16",
    )
    assert p_916.exists()
    with Image.open(p_916) as im:
        assert im.size == (1080, 1920)


def test_veritabani_kaydi():
    pid = db.paylasim_ekle(
        kategori="hadis",
        format_tipi="post_4_5",
        turkce_metin="Test hadis metni",
        baslik="Buhârî, Rikâk, 1",
        kaynak="Buhârî, Rikâk, 1",
        tefekkur="Test tefekkür",
        caption="Test caption #ezanplus",
        gorsel_yollari=["data/cikti/test_unit_hadis_45.png"],
        durum="taslak",
    )
    assert pid > 0
    kayit = db.paylasim_getir(pid)
    assert kayit is not None
    assert kayit["kategori"] == "hadis"
    assert kayit["format"] == "post_4_5"


if __name__ == "__main__":
    test_hadis_kartlari()
    print("✓ test_hadis_kartlari başarılı!")
    test_dua_kartlari()
    print("✓ test_dua_kartlari başarılı!")
    test_veritabani_kaydi()
    print("✓ test_veritabani_kaydi başarılı!")
    print("Tüm testler eksiksiz geçti!")
