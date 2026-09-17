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


def test_v18_hibrit_kartlar():
    # V18 Hadis (Arapça + Parşömen Taç)
    p_hadis = hadis_karti_ciz(
        hadis_metni="Müslüman, elinden ve dilinden diğer Müslümanların **emin olduğu** kimsedir.",
        kaynak_ravi="Buhârî, Îmân 4; Müslim, Îmân 64",
        tefekkur_notu="Mümin, çevresine emniyet ve huzur aşılayan güven timsalidir.",
        cikti_dosya_adi="test_v18_hadis.png",
        format_tipi="4:5",
        arapca_metin="الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        arapca_okunus="El-müslimü men selime'l-müslimûne min lisânihî ve yedih.",
        ravi="Abdullah b. Amr (r.a.)",
    )
    assert p_hadis.exists()

    # V18 Dua (Ruh Hali + Dinamik Palet + Kimin Duası)
    p_dua = dua_karti_ciz(
        dua_basligi="Hz. Mûsâ'nın Gönül Genişliği Niyazı",
        turkce_anlam="Rabbim! **Gönlüme ferahlık ver**, işimi bana kolaylaştır.",
        arapca_metin="رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي",
        arapca_okunus="Rabbi'şrah lî sadrî ve yessir lî emrî.",
        cikti_dosya_adi="test_v18_dua.png",
        format_tipi="9:16",
        ruh_hali="İç Sıkıntısı ve Daralma Hissi",
        kimin_duasi="Hz. Mûsâ (a.s.)'ın Niyazı",
        kaynak_ref="Tâhâ Sûresi, 25-26",
        fazilet_notu="Zor işlerin kolaylaşması için tavsiye edilir.",
    )
    assert p_dua.exists()


def test_veritabani_kaydi():
    pid = db.paylasim_ekle(
        kategori="kelime",
        format_tipi="gorsel_4_5",
        turkce_metin="Test kelime metni",
        baslik="Test Başlık",
        kaynak="Kur'an Sözlüğü",
        tefekkur="Test tefekkür",
        caption="Test caption #ezanplus",
        gorsel_yollari=["data/cikti/test_unit_kelime_45.png"],
        durum="taslak",
    )
    try:
        assert pid > 0
        kayit = db.paylasim_getir(pid)
        assert kayit is not None
        assert kayit["kategori"] == "kelime"
        assert kayit["format"] == "gorsel_4_5"
    finally:
        with db.baglanti_al() as con:
            con.execute("DELETE FROM paylasimlar WHERE id = ?", (pid,))


if __name__ == "__main__":
    test_hadis_kartlari()
    print("✓ test_hadis_kartlari başarılı!")
    test_dua_kartlari()
    print("✓ test_dua_kartlari başarılı!")
    test_v18_hibrit_kartlar()
    print("✓ test_v18_hibrit_kartlar başarılı!")
    test_veritabani_kaydi()
    print("✓ test_veritabani_kaydi başarılı!")
    print("Tüm testler eksiksiz geçti!")
