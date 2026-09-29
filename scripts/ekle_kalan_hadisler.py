# scripts/ekle_kalan_hadisler.py
# -*- coding: utf-8 -*-
"""
Ezan Plus — Kalan 50 Hadisi Ekleyerek Külliyatı 2.000 Hadise Tamamlama Betiği
1951 - 2000 arası:
- 16 Hadis: İmam Nevevî'nin Kırk Hadisi (el-Erba'ûn) tamamlayıcısı
- 34 Hadis: Sahîh-i Buhârî seçkin hikmet ve fazilet hadisleri
"""

import sqlite3
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
DB_YOLU = KOK / "data" / "hadisler" / "hadisler.db"

KALAN_HADISLER = [
    # --- el-Erba'ûn Kırk Hadis Tamamlayıcıları (1951 - 1966) ---
    {
        "hadis_no": 1951,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Vâbisa b. Ma'bed (r.a.)",
        "arapca_metin": "اسْتَفْتِ قَلْبَكَ، الْبِرُّ مَا اطْمَأَنَّتْ إِلَيْهِ النَّفْسُ وَاطْمَأَنَّ إِلَيْهِ الْقَلْبُ، وَالإِثْمُ مَا حَاكَ فِي النَّفْسِ وَتَرَدَّدَ فِي الصَّدْرِ، وَإِنْ أَفْتَاكَ النَّاسُ وَأَفْتَوْكَ",
        "arapca_veciz": "اسْتَفْتِ قَلْبَكَ، الْبِرُّ مَا اطْمَأَنَّتْ إِلَيْهِ النَّفْسُ وَاطْمَأَنَّ إِلَيْهِ الْقَلْبُ",
        "turkce_tam": "“Kalbime ve vicdanına danış! İyilik, nefsin ve kalbin kendisiyle huzur bulduğu şeydir. Kötülük ise insanlar sana fetva verseler bile içini kemiren ve göğsünde tereddüt uyandıran şeydir.”",
        "hadis_metni": "Vicdanına danış! İyilik, kalbin huzur bulduğu şeydir; günah ise insanlar fetva verse bile içini tırmalayan şeydir.",
        "kaynak_ref": "Ahmed b. Hanbel, Müsned 4/227; Dârimî, Büyû' 2",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1952,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. İrbâd b. Sâriye (r.a.)",
        "arapca_metin": "عَلَيْكُمْ بِسُنَّتِي وَسُنَّةِ الْخُلَفَاءِ الرَّاشِدِينَ الْمَهْدِيِّينَ، عَضُّوا عَلَيْهَا بِالنَّوَاجِذِ، وَإِيَّاكُمْ وَمُحْدَثَاتِ الأُمُورِ",
        "arapca_veciz": "عَلَيْكُمْ بِسُنَّتِي وَسُنَّةِ الْخُلَفَاءِ الرَّاشِدِينَ الْمَهْدِيِّينَ، عَضُّوا عَلَيْهَا بِالنَّوَاجِذِ",
        "turkce_tam": "“Size sünnetime ve doğru yolda olan hulefâ-i râşidînin yoluna sarılmanızı tavsiye ederim; onlara azı dişlerinizle sımsıkı yapışın!”",
        "hadis_metni": "Benim sünnetime ve hidayet üzere olan râşid halifelerimin yoluna sımsıkı sarılınız.",
        "kaynak_ref": "Ebû Dâvûd, Sünnet 5; Tirmizî, İlim 16",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1953,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Muâz b. Cebel (r.a.)",
        "arapca_metin": "أَلا أُخْبِرُكَ بِمَلاكِ ذَلِكَ كُلِّهِ؟ قُلْتُ: بَلَى يَا نَبِيَّ اللَّهِ، فَأَخَذَ بِلِسَانِهِ قَالَ: كُفَّ عَلَيْكَ هَذَا",
        "arapca_veciz": "كُفَّ عَلَيْكَ هَذَا، قُلْتُ: وَإِنَّا لَمُؤَاخَذُونَ بِمَا نَتَكَلَّمُ بِهِ؟ قَالَ: وَهَلْ يَكُبُّ النَّاسَ فِي النَّارِ إِلا حَصَائِدُ أَلْسِنَتِهِمْ",
        "turkce_tam": "“Resûlullah dilini tuttu ve: 'Bunu koru!' buyurdu. 'Biz konuştuklarımızdan da hesaba mı çekileceğiz?' dedim. 'İnsanları yüzüstü cehenneme sürükleyen dillerinin kazandığından başkası mıdır?' buyurdu.”",
        "hadis_metni": "Dilini koru! İnsanları yüzüstü ateşe sürükleyen şey, dillerinin kazandığı günahlardan başkası mıdır?",
        "kaynak_ref": "Tirmizî, Îmân 8; İbn Mâce, Fiten 12",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1954,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Sa'lebe el-Huşenî (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ تَعَالَى فَرَضَ فَرَائِضَ فَلا تُضَيِّعُوهَا، وَحَدَّ حُدُودًا فَلا تَعْتَدُوهَا، وَسَكَتَ عَنْ أَشْيَاءَ رَحْمَةً لَكُمْ غَيْرَ نِسْيَانٍ فَلا تَبْحَثُوا عَنْهَا",
        "arapca_veciz": "إِنَّ اللَّهَ فَرَضَ فَرَائِضَ فَلا تُضَيِّعُوهَا، وَحَدَّ حُدُودًا فَلا تَعْتَدُوهَا",
        "turkce_tam": "“Allah Teâlâ bazı farzlar koydu, onları zayi etmeyin. Sınırlar çizdi, onları aşmayın. Unutmaksızın size merhametinden ötürü bazı şeylerden sustu; onları da deşelemeyin!”",
        "hadis_metni": "Allah bazı farzlar koydu, onları terk etmeyiniz; sınırlar çizdi, onları aşmayınız.",
        "kaynak_ref": "Dârekutnî, es-Sünen 4/184; Nevevî, el-Erba'ûn 30",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1955,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Abbâs (r.a.)",
        "arapca_metin": "لَوْ يُعْطَى النَّاسُ بِدَعْوَاهُمْ، لادَّعَى رِجَالٌ أَمْوَالَ قَوْمٍ وَدِمَاءَهُمْ، لَكِنِ الْبَيِّنَةُ عَلَى الْمُدَّعِي، وَالْيَمِينُ عَلَى مَنْ أَنْكَرَ",
        "arapca_veciz": "الْبَيِّنَةُ عَلَى الْمُدَّعِي، وَالْيَمِينُ عَلَى مَنْ أَنْكَرَ",
        "turkce_tam": "“Eğer insanlara her iddialarına göre hak verilseydi, bazıları diğerlerinin mallarını ve canlarını iddia ederdi. Fakat delil getirmek iddia edene, yemin etmek ise inkar edene düşer.”",
        "hadis_metni": "Hukukta delil getirmek iddia sahibine, yemin etmek ise inkar edene aittir.",
        "kaynak_ref": "Buhârî, Rehn 6; Beyhakî, es-Sünenü'l-Kübrâ 10/252",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1956,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Abbâs (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ كَتَبَ الْحَسَنَاتِ وَالسَّيِّئَاتِ ثُمَّ بَيَّنَ ذَلِكَ، فَمَنْ هَمَّ بِحَسَنَةٍ فَلَمْ يَعْمَلْهَا كَتَبَهَا اللَّهُ لَهُ عِنْدَهُ حَسَنَةً كَامِلَةً",
        "arapca_veciz": "فَمَنْ هَمَّ بِحَسَنَةٍ فَلَمْ يَعْمَلْهَا كَتَبَهَا اللَّهُ لَهُ عِنْدَهُ حَسَنَةً كَامِلَةً",
        "turkce_tam": "“Allah iyilikleri ve kötülükleri takdir etti. Kim bir iyilik yapmaya niyet eder de yapamazsa, Allah katında ona tam bir iyilik sevabı yazılır.”",
        "hadis_metni": "Kim bir hayra niyet eder de yapamazsa, Allah ona tam bir iyilik yapmış gibi sevap yazar.",
        "kaynak_ref": "Buhârî, Rikâk 31; Müslim, Îmân 207",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1957,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ تَعَالَى قَالَ: مَنْ عَادَى لِي وَلِيًّا فَقَدْ آذَنْتُهُ بِالْحَرْبِ، وَمَا تَقَرَّبَ إِلَيَّ عَبْدِي بِشَيْءٍ أَحَبَّ إِلَيَّ مِمَّا افْتَرَضْتُ عَلَيْهِ",
        "arapca_veciz": "مَنْ عَادَى لِي وَلِيًّا فَقَدْ آذَنْتُهُ بِالْحَرْبِ، وَمَا تَقَرَّبَ إِلَيَّ عَبْدِي بِشَيْءٍ أَحَبَّ إِلَيَّ مِمَّا افْتَرَضْتُ عَلَيْهِ",
        "turkce_tam": "“Allah Teâlâ şöyle buyurdu: Kim benim bir veli kuluma düşmanlık ederse, Ben ona savaş ilan ederim. Kulum Bana, üzerine farz kıldığım şeylerden daha sevimli bir şeyle yaklaşamaz.”",
        "hadis_metni": "Allah buyurur: Kulum Bana, kendisine farz kıldığım şeylerden daha sevimli bir amelle yaklaşamaz.",
        "kaynak_ref": "Buhârî, Rikâk 38",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1958,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Abbâs (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ تَجَاوَزَ لِي عَنْ أُمَّتِي الْخَطَأَ وَالنِّسْيَانَ وَمَا اسْتُكْرِهُوا عَلَيْهِ",
        "arapca_veciz": "إِنَّ اللَّهَ تَجَاوَزَ لِي عَنْ أُمَّتِي الْخَطَأَ وَالنِّسْيَانَ وَمَا اسْتُكْرِهُوا عَلَيْهِ",
        "turkce_tam": "“Şüphesiz Allah, ümmetimden hata ile, unutarak ve zorlama altında işledikleri günahların sorumluluğunu kaldırmıştır.”",
        "hadis_metni": "Allah Teâlâ ümmetimin hataen, unutarak ve zorlanarak işlediği şeyleri bağışlamıştır.",
        "kaynak_ref": "İbn Mâce, Talâk 16; Beyhakî 7/356",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1959,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Enes b. Mâlik (r.a.)",
        "arapca_metin": "قَالَ اللَّهُ تَعَالَى: يَا ابْنَ آدَمَ، إِنَّكَ مَا دَعَوْتَنِي وَرَجَوْتَنِي غَفَرْتُ لَكَ عَلَى مَا كَانَ فِيكَ وَلا أُبَالِي",
        "arapca_veciz": "يَا ابْنَ آدَمَ، إِنَّكَ مَا دَعَوْتَنِي وَرَجَوْتَنِي غَفَرْتُ لَكَ عَلَى مَا كَانَ فِيكَ وَلا أُبَالِي",
        "turkce_tam": "“Allah Teâlâ buyurur: Ey Âdemoğlu! Sen Bana dua ettiğin ve Benden umduğun sürece, ne kadar günahın olursa olsun seni bağışlarım ve buna aldırmam!”",
        "hadis_metni": "Ey insanoğlu! Sen Bana dua edip rahmetimi umdukça, sendeki kusurlara bakmadan seni bağışlarım.",
        "kaynak_ref": "Tirmizî, Deavât 98; Ahmed b. Hanbel 5/172",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1960,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "قَالَ اللَّهُ عَزَّ وَجَلَّ: أَنَا عِنْدَ ظَنِّ عَبْدِي بِي، وَأَنَا مَعَهُ حَيْثُ يَذْكُرُنِي",
        "arapca_veciz": "أَنَا عِنْدَ ظَنِّ عَبْدِي بِي، وَأَنَا مَعَهُ حَيْثُ يَذْكُرُنِي",
        "turkce_tam": "“Allah Teâlâ buyurur: Ben kulumun Benim hakkımdaki zannı üzereyim. Beni andığı zaman Ben onunla beraberim.”",
        "hadis_metni": "Yüce Allah buyurur: Ben kulumun hakkımdaki zannı yanındayım; Beni andığı yerde onunlayım.",
        "kaynak_ref": "Buhârî, Tevhîd 15; Müslim, Zikir 2",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1961,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Câbir b. Abdullah (r.a.)",
        "arapca_metin": "أَفْضَلُ الذِّكْرِ لا إِلَهَ إِلا اللَّهُ، وَأَفْضَلُ الدُّعَاءِ الْحَمْدُ لِلَّهِ",
        "arapca_veciz": "أَفْضَلُ الذِّكْرِ لا إِلَهَ إِلا اللَّهُ، وَأَفْضَلُ الدُّعَاءِ الْحَمْدُ لِلَّهِ",
        "turkce_tam": "“Zikrin en faziletlisi 'Lâ ilâhe illallâh', duanın en faziletlisi ise 'Elhamdülillâh'tır.”",
        "hadis_metni": "Zikirlerin en faziletlisi 'Lâ ilâhe illallâh' tevhididir; duaların en güzeli ise Allah'a hamd etmektir.",
        "kaynak_ref": "Tirmizî, Deavât 9; İbn Mâce, Edeb 55",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1962,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Zerr el-Gıfârî (r.a.)",
        "arapca_metin": "لا تَحْقِرَنَّ مِنَ الْمَعْرُوفِ شَيْئًا، وَلَوْ أَنْ تَلْقَى أَخَاكَ بِوَجْهٍ طَلْقٍ",
        "arapca_veciz": "لا تَحْقِرَنَّ مِنَ الْمَعْرُوفِ شَيْئًا، وَلَوْ أَنْ تَلْقَى أَخَاكَ بِوَجْهٍ طَلْقٍ",
        "turkce_tam": "“Din kardeşini güler yüzle karşılamak dahi olsa, hiçbir iyiliği küçük görüp hafife alma!”",
        "hadis_metni": "Kardeşini güler yüzle karşılamak bile olsa, hiçbir iyiliği ve hayrı sakın küçük görme.",
        "kaynak_ref": "Müslim, Birr 144; Tirmizî, Et'ime 30",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1963,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِذَا مَاتَ الإِنْسَانُ انْقَطَعَ عَنْهُ عَمَلُهُ إِلا مِنْ ثَلاثَةٍ: إِلا مِنْ صَدَقَةٍ جَارِيَةٍ، أَوْ عِلْمٍ يُنْتَفَعُ بِهِ، أَوْ وَلَدٍ صَالِحٍ يَدْعُو لَهُ",
        "arapca_veciz": "إِذَا مَاتَ الإِنْسَانُ انْقَطَعَ عَمَلُهُ إِلا مِنْ ثَلاثٍ: صَدَقَةٍ جَارِيَةٍ، أَوْ عِلْمٍ يُنْتَفَعُ بِهِ، أَوْ وَلَدٍ صَالِحٍ يَدْعُو لَهُ",
        "turkce_tam": "“İnsan ölünce amel defteri kapanır; ancak şu üç şey hariç: Sadaka-i câriye, faydalanılan ilim ve kendisine dua eden salih bir evlat.”",
        "hadis_metni": "Kişi öldüğünde ameli kesilir; ancak sadaka-i cariye, faydalı bir ilim ve ardında dua eden salih evlat bırakan müstesnadır.",
        "kaynak_ref": "Müslim, Vasiyyet 14; Tirmizî, Ahkâm 36",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1964,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Amr (r.a.)",
        "arapca_metin": "رِضَا الرَّبِّ فِي رِضَا الْوَالِدِ، وَسَخَطُ الرَّبِّ فِي سَخَطِ الْوَالِدِ",
        "arapca_veciz": "رِضَا الرَّبِّ فِي رِضَا الْوَالِدِ، وَسَخَطُ الرَّبِّ فِي سَخَطِ الْوَالِدِ",
        "turkce_tam": "“Rabbin rızası anne babanın rızasındadır; Rabbin gazabı da anne babanın öfkesindedir.”",
        "hadis_metni": "Allah'ın hoşnutluğu anne ve babanın rızasındadır; Allah'ın gazabı da onların öfkesindedir.",
        "kaynak_ref": "Tirmizî, Birr 3; İbn Hibbân 429",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1965,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Osman b. Affân (r.a.)",
        "arapca_metin": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        "arapca_veciz": "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ",
        "turkce_tam": "“Sizin en hayırlınız, Kur'an'ı öğrenen ve başkalarına öğreteninizdir.”",
        "hadis_metni": "İçinizde en hayırlı ve faziletli kimse, Kur'an-ı Kerim'i bizzat öğrenen ve onu insanlara öğretendir.",
        "kaynak_ref": "Buhârî, Fedâilü'l-Kur'ân 21; Tirmizî, Fedâil 15",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1966,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "كَلِمَتَانِ خَفِيفَتَانِ عَلَى اللِّسَانِ، ثَقِيلَتَانِ فِي الْمِيزَانِ، حَبِيبَتَانِ إِلَى الرَّحْمَنِ: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
        "arapca_veciz": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
        "turkce_tam": "“Dile hafif, mizanda ağır, Rahmân'a çok sevimli iki kelime vardır: Sübhânallâhi ve bi-hamdihî, Sübhânallâhi'l-Azîm.”",
        "hadis_metni": "Dile hafif gelen, mizanda çok ağır basan ve Rahmân'a çok sevimli olan zikir: Sübhânallâhi ve bi-hamdihî, Sübhânallâhi'l-Azîm'dir.",
        "kaynak_ref": "Buhârî, Deavât 65, Tevhîd 58; Müslim, Zikir 31",
        "kart_icin_uygun": 1
    },

    # --- Sahîh-i Buhârî Seçkin Külliyatı (1967 - 2000) ---
    {
        "hadis_no": 1967,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Muâviye (r.a.)",
        "arapca_metin": "مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ",
        "arapca_veciz": "مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ",
        "turkce_tam": "“Allah kimin hakkında hayır dilerse, onu dinde derin anlayış ve kavrayış sahibi kılar.”",
        "hadis_metni": "Allah kime hayır murat ederse, ona dinde derin bir basiret ve kavrayış ihsan eder.",
        "kaynak_ref": "Buhârî, İlim 10; Müslim, İmâre 175",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1968,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِنَّ الدِّينَ يُسْرٌ، وَلَنْ يُشَادَّ الدِّينَ أَحَدٌ إِلا غَلَبَهُ",
        "arapca_veciz": "إِنَّ الدِّينَ يُسْرٌ، وَلَنْ يُشَادَّ الدِّينَ أَحَدٌ إِلا غَلَبَهُ",
        "turkce_tam": "“Şüphesiz din kolaylıktır. Kim dini aşırı zorlaştırırsa din ona mutlaka galip gelir.”",
        "hadis_metni": "Şüphesiz bu din kolaylıktır; kim onu kaldıramayacağı şekilde zorlaştırırsa mağlup düşer.",
        "kaynak_ref": "Buhârî, Îmân 29; Nesâî, Îmân 28",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1969,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Enes b. Mâlik (r.a.)",
        "arapca_metin": "ثَلاثٌ مَنْ كُنَّ فِيهِ وَجَدَ حَلاوَةَ الإِيمَانِ: أَنْ يَكُونَ اللَّهُ وَرَسُولُهُ أَحَبَّ إِلَيْهِ مِمَّا سِوَاهُمَا",
        "arapca_veciz": "أَنْ يَكُونَ اللَّهُ وَرَسُولُهُ أَحَبَّ إِلَيْهِ مِمَّا سِوَاهُمَا",
        "turkce_tam": "“Üç haslet vardır ki bunlar kimde bulunursa imanın tadını alır: Allah ve Resûlü'nü her şeyden çok sevmek...”",
        "hadis_metni": "Allah ve Resûlü'nü her şeyden daha çok seven kimse, kalbinde imanın hakiki tatlılığını bulur.",
        "kaynak_ref": "Buhârî, Îmân 9, 14; Müslim, Îmân 67",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1970,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ صَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ",
        "arapca_veciz": "مَنْ صَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ",
        "turkce_tam": "“Kim inanarak ve sevabını yalnızca Allah'tan umarak Ramazan orucunu tutarsa, geçmiş günahları bağışlanır.”",
        "hadis_metni": "Kim inanarak ve mükafatını sadece Allah'tan bekleyerek Ramazan orucunu tutarsa geçmiş günahları affolunur.",
        "kaynak_ref": "Buhârî, Îmân 28, Savm 6; Müslim, Müsâfirîn 175",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1971,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ قَامَ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ",
        "arapca_veciz": "مَنْ قَامَ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ",
        "turkce_tam": "“Kim Kadir gecesini inanarak ve ecrini Allah'tan umarak ihya ederse, geçmiş günahları bağışlanır.”",
        "hadis_metni": "Kadir gecesini samimi bir iman ve ihlasla ibadetle geçirenin geçmiş günahları mağfiret olunur.",
        "kaynak_ref": "Buhârî, Îmân 25, Fadlu Leyleti'l-Kadr 1; Müslim, Müsâfirîn 175",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1972,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "الصَّلَوَاتُ الْخَمْسُ وَالْجُمُعَةُ إِلَى الْجُمُعَةِ كَفَّارَاتٌ لِمَا بَيْنَهُنَّ مَا لَمْ تُغْشَ الْكَبَائِرُ",
        "arapca_veciz": "الصَّلَوَاتُ الْخَمْسُ كَفَّارَاتٌ لِمَا بَيْنَهُنَّ مَا لَمْ تُغْشَ الْكَبَائِرُ",
        "turkce_tam": "“Büyük günahlardan kaçınıldığı sürece, beş vakit namaz ve cuma namazı diğer cumaya kadar aradaki günahlara kefarettir.”",
        "hadis_metni": "Büyük günahlardan sakınıldığı müddetçe kılınan beş vakit namaz, aradaki küçük günahlara kefarettir.",
        "kaynak_ref": "Buhârî, Mevâkît 4; Müslim, Tahâret 14",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1973,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Mes'ûd (r.a.)",
        "arapca_metin": "سَأَلْتُ النَّبِيَّ صلى الله عليه وسلم: أَيُّ الْعَمَلِ أَحَبُّ إِلَى اللَّهِ؟ قَالَ: الصَّلاةُ عَلَى وَقْتِهَا، قُلْتُ: ثُمَّ أَيٌّ؟ قَالَ: ثُمَّ بِرُّ الْوَالِدَيْنِ",
        "arapca_veciz": "أَحَبُّ الْعَمَلِ إِلَى اللَّهِ: الصَّلاةُ عَلَى وَقْتِهَا، ثُمَّ بِرُّ الْوَالِدَيْنِ",
        "turkce_tam": "“Allah'a en sevimli amel hangisidir?' dedim. 'Vaktinde kılınan namazdır' buyurdu. 'Sonra hangisi?' dedim. 'Anne ve babaya iyilik etmektir' buyurdu.”",
        "hadis_metni": "Allah katında amellerin en sevimlisi, vaktinde eda edilen namaz ve ardından ana babaya yapılan iyiliktir.",
        "kaynak_ref": "Buhârî, Mevâkît 5, Cihâd 1; Müslim, Îmân 137",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1974,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Mûsâ el-Eş'arî (r.a.)",
        "arapca_metin": "مَثَلُ الَّذِي يَذْكُرُ رَبَّهُ وَالَّذِي لا يَذْكُرُ رَبَّهُ مَثَلُ الْحَيِّ وَالْمَيِّتِ",
        "arapca_veciz": "مَثَلُ الَّذِي يَذْكُرُ رَبَّهُ وَالَّذِي لا يَذْكُرُ رَبَّهُ مَثَلُ الْحَيِّ وَالْمَيِّتِ",
        "turkce_tam": "“Rabbini zikreden ile zikretmeyenin misali, diri ile ölünün misali gibidir.”",
        "hadis_metni": "Rabbini zikreden kimse diri, zikretmeyen gafil kimse ise adeta bir ölü gibidir.",
        "kaynak_ref": "Buhârî, Deavât 66; Müslim, Müsâfirîn 211",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1975,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "سَبْعَةٌ يُظِلُّهُمُ اللَّهُ فِي ظِلِّهِ يَوْمَ لا ظِلَّ إِلا ظِلُّهُ: إِمَامٌ عَادِلٌ، وَشَابٌّ نَشَأَ فِي عِبَادَةِ اللَّهِ",
        "arapca_veciz": "سَبْعَةٌ يُظِلُّهُمُ اللَّهُ فِي ظِلِّهِ يَوْمَ لا ظِلَّ إِلا ظِلُّهُ: إِمَامٌ عَادِلٌ، وَشَابٌّ نَشَأَ فِي عِبَادَةِ اللَّهِ",
        "turkce_tam": "“Başka hiçbir gölgenin olmadığı mahşer gününde Allah yedi sınıf insanı arşının gölgesinde gölgelendirir: Adil yönetici, Rabbine ibadetle yetişen genç...”",
        "hadis_metni": "Hiçbir himayenin olmadığı kıyamet gününde adil idareci ve ibadetle büyüyen genç, ilahi rahmet gölgesindedir.",
        "kaynak_ref": "Buhârî, Ezân 36, Hudûd 19; Müslim, Zekât 91",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1976,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Câbir b. Abdullah (r.a.)",
        "arapca_metin": "اتَّقُوا الظُّلْمَ، فَإِنَّ الظُّلْمَ ظُلُمَاتٌ يَوْمَ الْقِيَامَةِ",
        "arapca_veciz": "اتَّقُوا الظُّلْمَ، فَإِنَّ الظُّلْمَ ظُلُمَاتٌ يَوْمَ الْقِيَامَةِ",
        "turkce_tam": "“Zulümden sakının! Çünkü zulüm, kıyamet gününde zifiri karanlıklardır.”",
        "hadis_metni": "Haksızlıktan ve zulmetmekten sakınınız; zira zulüm kıyamet gününde koyu bir karanlıktır.",
        "kaynak_ref": "Buhârî, Mezâlim 8; Müslim, Birr 56",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1977,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Ömer (r.a.)",
        "arapca_metin": "الْمُسْلِمُ أَخُو الْمُسْلِمِ لا يَظْلِمُهُ وَلا يُسْلِمُهُ، وَمَنْ كَانَ فِي حَاجَةِ أَخِيهِ كَانَ اللَّهُ فِي حَاجَتِهِ",
        "arapca_veciz": "الْمُسْلِمُ أَخُو الْمُسْلِمِ لا يَظْلِمُهُ وَلا يُسْلِمُهُ، وَمَنْ كَانَ فِي حَاجَةِ أَخِيهِ كَانَ اللَّهُ فِي حَاجَتِهِ",
        "turkce_tam": "“Müslüman Müslümanın kardeşidir; ona zulmetmez ve onu zalime teslim etmez. Kim kardeşinin bir ihtiyacını karşılarsa, Allah da onun ihtiyacını karşılar.”",
        "hadis_metni": "Müslüman kardeşine zulmetmez; kim din kardeşinin yardımında bulunursa Allah da ona yardım eder.",
        "kaynak_ref": "Buhârî, Mezâlim 3, İkrâh 7; Müslim, Birr 58",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1978,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. İbn Abbâs (r.a.)",
        "arapca_metin": "وَاتَّقِ دَعْوَةَ الْمَظْلُومِ، فَإِنَّهُ لَيْسَ بَيْنَهَا وَبَيْنَ اللَّهِ حِجَابٌ",
        "arapca_veciz": "وَاتَّقِ دَعْوَةَ الْمَظْلُومِ، فَإِنَّهُ لَيْسَ بَيْنَهَا وَبَيْنَ اللَّهِ حِجَابٌ",
        "turkce_tam": "“Mazlumun bedduasından sakın! Çünkü onunla Allah arasında hiçbir perde yoktur.”",
        "hadis_metni": "Haksızlığa uğrayan mazlumun ahından sakınınız; zira onun yakarışı ile Allah arasında hiçbir engel yoktur.",
        "kaynak_ref": "Buhârî, Zekât 41, Mezâlim 9; Müslim, Îmân 29",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1979,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِنَّ رَحْمَتِي غَلَبَتْ غَضَبِي",
        "arapca_veciz": "إِنَّ رَحْمَتِي غَلَبَتْ غَضَبِي",
        "turkce_tam": "“Allah mahlukatı yarattığı zaman Arş'ın üzerindeki Kitabı'na şunu yazdı: 'Şüphesiz rahmetim gazabıma üstün gelmiştir.'”",
        "hadis_metni": "Yüce Allah kendi katında şöyle hükmetti: Benim rahmetim gazabıma galip gelmiştir.",
        "kaynak_ref": "Buhârî, Bed'ü'l-Halk 1, Tevhîd 15; Müslim, Tevbe 14",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1980,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "قَالَ اللَّهُ: كَذَّبَنِي ابْنُ آدَمَ وَلَمْ يَكُنْ لَهُ ذَلِكَ، وَشَتَمَنِي وَلَمْ يَكُنْ لَهُ ذَلِكَ",
        "arapca_veciz": "قَالَ رَسُولُ اللَّهِ: إِذَا سَمِعْتُمْ صِيَاحَ الدِّيَكَةِ فَاسْأَلُوا اللَّهَ مِنْ فَضْلِهِ",
        "turkce_tam": "“Horozun ötüşünü duyduğunuz zaman Allah'ın lütfundan isteyiniz; çünkü o bir melek görmüştür.”",
        "hadis_metni": "Geceleri horozun ötüşünü işittiğinizde Allah'tan hayır ve lütuf dileyiniz.",
        "kaynak_ref": "Buhârî, Bed'ü'l-Halk 15; Müslim, Zikir 82",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1981,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Âişe (r.a.)",
        "arapca_metin": "مَنْ أَحَبَّ لِقَاءَ اللَّهِ أَحَبَّ اللَّهُ لِقَاءَهُ، وَمَنْ كَرِهَ لِقَاءَ اللَّهِ كَرِهَ اللَّهُ لِقَاءَهُ",
        "arapca_veciz": "مَنْ أَحَبَّ لِقَاءَ اللَّهِ أَحَبَّ اللَّهُ لِقَاءَهُ",
        "turkce_tam": "“Kim Allah'a kavuşmayı arzu ederse, Allah da ona kavuşmayı arzu eder.”",
        "hadis_metni": "Kim Allah Teâlâ'ya vuslatı muhabbetle arzu ederse, Allah da ona kavuşmayı sever.",
        "kaynak_ref": "Buhârî, Rikâk 41; Müslim, Zikir 14",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1982,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "حُفَّتِ الْجَنَّةُ بِالْمَكَارِهِ، وَحُفَّتِ النَّارُ بِالشَّهَوَاتِ",
        "arapca_veciz": "حُفَّتِ الْجَنَّةُ بِالْمَكَارِهِ، وَحُفَّتِ النَّارُ بِالشَّهَوَاتِ",
        "turkce_tam": "“Cennet nefsin hoşlanmadığı zahmetli şeylerle perdelenmiştir; cehennem ise nefsin arzuladığı şehvetlerle çevrilmiştir.”",
        "hadis_metni": "Cennet fedakarlık ve sabırla çevrilidir; cehennem ise nefsin heva ve şehvetleriyle kuşatılmıştır.",
        "kaynak_ref": "Buhârî, Rikâk 28; Müslim, Cennet 1",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1983,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "لَوْ تَعْلَمُونَ مَا أَعْلَمُ لَضَحِكْتُمْ قَلِيلا وَلَبَكَيْتُمْ كَثِيرًا",
        "arapca_veciz": "لَوْ تَعْلَمُونَ مَا أَعْلَمُ لَضَحِكْتُمْ قَلِيلا وَلَبَكَيْتُمْ كَثِيرًا",
        "turkce_tam": "“Eğer benim bildiğim hakikatleri sizler bilseydiniz, az güler çok ağlardınız!”",
        "hadis_metni": "Eğer ahiret ve hesap hakkında benim bildiklerimi bilseydiniz, dünyaya az güler, çok ağlardınız.",
        "kaynak_ref": "Buhârî, Küsûf 2, Rikâk 27; Müslim, Salât 112",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1984,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "تَعِسَ عَبْدُ الدِّينَارِ، وَعَبْدُ الدِّرْهَمِ، وَعَبْدُ الْخَمِيصَةِ، إِنْ أُعْطِيَ رَضِيَ، وَإِنْ لَمْ يُعْطَ سَخِطَ",
        "arapca_veciz": "تَعِسَ عَبْدُ الدِّينَارِ، وَعَبْدُ الدِّرْهَمِ",
        "turkce_tam": "“Altının kulu, gümüşün kulu ve lüks elbisenin kulu olan kimse helak olsun! Kendisine verilirse memnun olur, verilmezse öfkelenir.”",
        "hadis_metni": "Paranın, mevkinin ve lüksün esiri olan helak olmuştur; kalbini fanilere bağlayan hüsrandadır.",
        "kaynak_ref": "Buhârî, Cihâd 70, Rikâk 10",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1985,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "قَالَ اللَّهُ: أَعْدَدْتُ لِعِبَادِي الصَّالِحِينَ مَا لا عَيْنٌ رَأَتْ، وَلا أُذُنٌ سَمِعَتْ، وَلا خَطَرَ عَلَى قَلْبِ بَشَرٍ",
        "arapca_veciz": "أَعْدَدْتُ لِعِبَادِي الصَّالِحِينَ مَا لا عَيْنٌ رَأَتْ، وَلا أُذُنٌ سَمِعَتْ، وَلا خَطَرَ عَلَى قَلْبِ بَشَرٍ",
        "turkce_tam": "“Allah Teâlâ buyurur: Salih kullarım için cennette hiçbir gözün görmediği, hiçbir kulağın işitmediği ve hiçbir insan kalbinin hayal edemediği nimetler hazırladım.”",
        "hadis_metni": "Salih müminler için cennette gözlerin görmediği, kulakların duymadığı ve insan aklına gelmeyen nimetler hazırlanmıştır.",
        "kaynak_ref": "Buhârî, Bed'ü'l-Halk 8, Tefsîr 32; Müslim, Cennet 2",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1986,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Cerîr b. Abdullah (r.a.)",
        "arapca_metin": "إِنَّكُمْ سَتَرَوْنَ رَبَّكُمْ كَمَا تَرَوْنَ هَذَا الْقَمَرَ لا تُضَامُونَ فِي رُؤْيَتِهِ",
        "arapca_veciz": "إِنَّكُمْ سَتَرَوْنَ رَبَّكُمْ كَمَا تَرَوْنَ هَذَا الْقَمَرَ لا تُضَامُونَ فِي رُؤْيَتِهِ",
        "turkce_tam": "“Dolunay gecesinde aya baktık. Resûlullah: 'Şu ayı zahmetsizce gördüğünüz gibi, Rabbinizi de kıyamet günü apaçık göreceksiniz' buyurdu.”",
        "hadis_metni": "Cennette müminler dolunayı seyreder gibi Rablerinin cemâlini zahmetsizce ve apaçık müşahede edeceklerdir.",
        "kaynak_ref": "Buhârî, Mevâkît 16, Tevhîd 24; Müslim, Mesâcid 211",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1987,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Sa'îd el-Hudrî (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ يَقُولُ لأَهْلِ الْجَنَّةِ: يَا أَهْلَ الْجَنَّةِ، فَيَقُولُونَ: لَبَّيْكَ رَبَّنَا وَسَعْدَيْكَ، فَيَقُولُ: هَلْ رَضِيتُمْ؟ فَيَقُولُونَ: وَمَا لَنَا لا نَرْضَى؟",
        "arapca_veciz": "أُحِلُّ عَلَيْكُمْ رِضْوَانِي فَلا أَسْخَطُ عَلَيْكُمْ بَعْدَهُ أَبَدًا",
        "turkce_tam": "“Allah cennet ehline: 'Size rızamı ebediyen helal kıldım; bundan sonra size asla gazap etmeyeceğim' buyurur.”",
        "hadis_metni": "Cennet nimetlerinin en büyüğü, Yüce Allah'ın ebedi rızasını ve hoşnutluğunu kazanmaktır.",
        "kaynak_ref": "Buhârî, Rikâk 51, Tevhîd 38; Müslim, Cennet 9",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1988,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "قَالَ رَسُولُ اللَّهِ: رَأَى رَجُلٌ كَلْبًا يَأْكُلُ الثَّرَى مِنَ الْعَطَشِ، فَأَخَذَ سَرَاوِيلَهُ فَسَقَاهُ، فَشَكَرَ اللَّهُ لَهُ فَأَدْخَلَهُ الْجَنَّةَ",
        "arapca_veciz": "فِي كُلِّ كَبِدٍ رَطْبَةٍ أَجْرٌ",
        "turkce_tam": "“Susuzluktan toprağı yalayan bir köpeğe ayakkabısıyla kuyuya inip su veren adamı Allah bağışladı ve cennetine koydu. 'Her canlıya yapılan iyilikte bir ecir vardır' buyurdu.”",
        "hadis_metni": "Her canlı varlığa merhametle yapılan iyilikte ve ikramda Allah katında büyük bir mükafat vardır.",
        "kaynak_ref": "Buhârî, Vudû' 33, Mezâlim 23; Müslim, Selâm 153",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1989,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "عُذِّبَتِ امْرَأَةٌ فِي هِرَّةٍ حَبَسَتْهَا حَتَّى مَاتَتْ جُوعًا، فَدَخَلَتْ فِيهَا النَّارَ",
        "arapca_veciz": "عُذِّبَتِ امْرَأَةٌ فِي هِرَّةٍ حَبَسَتْهَا حَتَّى مَاتَتْ جُوعًا",
        "turkce_tam": "“Bir kadın, bağlayıp aç bıraktığı ve ölümüne sebep olduğu bir kedi yüzünden cehenneme girdi.”",
        "hadis_metni": "Bir kediye dahi merhametsizlik edip aç bırakan kimse ilahi azaba uğramıştır; merhametsizlik helak sebebidir.",
        "kaynak_ref": "Buhârî, Müsâkât 9, Bed'ü'l-Halk 16; Müslim, Selâm 151",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1990,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. İbn Ömer (r.a.)",
        "arapca_metin": "كُلُّكُمْ رَاعٍ وَكُلُّكُمْ مَسْئُولٌ عَنْ رَعِيَّتِهِ",
        "arapca_veciz": "كُلُّكُمْ رَاعٍ وَكُلُّكُمْ مَسْئُولٌ عَنْ رَعِيَّتِهِ",
        "turkce_tam": "“Hepiniz birer çobansınız ve hepiniz elinizin altındakilerden, sorumluluğunuzdakilerden mesulsünüz.”",
        "hadis_metni": "Her biriniz birer gözetleyicisiniz ve her biriniz sorumluluğunuz altında olan kimselerden hesaba çekileceksiniz.",
        "kaynak_ref": "Buhârî, Cum'a 11, Nikâh 90; Müslim, İmâre 20",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1991,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ كَانَتْ لَهُ مَظْلَمَةٌ لأَخِيهِ مِنْ عِرْضِهِ أَوْ شَيْءٍ فَلْيَتَحَلَّلْهُ مِنْهُ الْيَوْمَ قَبْلَ أَنْ لا يَكُونَ دِينَارٌ وَلا دِرْهَمٌ",
        "arapca_veciz": "فَلْيَتَحَلَّلْهُ مِنْهُ الْيَوْمَ قَبْلَ أَنْ لا يَكُونَ دِينَارٌ وَلا دِرْهَمٌ",
        "turkce_tam": "“Kimin üzerinde kardeşinin ırzına veya malına dair bir haksızlık varsa, paranın pulun geçmeyeceği mahşer günü gelmeden önce bugün ondan helallik alsın!”",
        "hadis_metni": "Kardeşine haksızlık eden kimse, altının ve paranın geçmeyeceği hesap günü gelmeden önce bugün helalleşsin.",
        "kaynak_ref": "Buhârî, Mezâlim 10, Rikâk 48",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1992,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ، وَمَا زَادَ اللَّهُ عَبْدًا بِعَفْوٍ إِلا عِزًّا، وَمَا تَوَاضَعَ أَحَدٌ لِلَّهِ إِلا رَفَعَهُ اللَّهُ",
        "arapca_veciz": "مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ، وَمَا تَوَاضَعَ أَحَدٌ لِلَّهِ إِلا رَفَعَهُ اللَّهُ",
        "turkce_tam": "“Sadaka vermekle mal eksilmez. Allah affeden kulunun ancak izzet ve şerefini artırır. Allah rızası için tevazu göstereni ise Allah mutlaka yüceltir.”",
        "hadis_metni": "Sadaka malı eksiltmez; affetmek insanı yüceltir ve Allah için alçakgönüllü olanı Allah katında yükseltir.",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 402; Müslim, Birr 69",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1993,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Sa'îd el-Hudrî (r.a.)",
        "arapca_metin": "مَنْ يَتَصَبَّرْ يُصَبِّرْهُ اللَّهُ، وَمَا أُعْطِيَ أَحَدٌ عَطَاءً خَيْرًا وَأَوْسَعَ مِنَ الصَّبْرِ",
        "arapca_veciz": "وَمَا أُعْطِيَ أَحَدٌ عَطَاءً خَيْرًا وَأَوْسَعَ مِنَ الصَّبْرِ",
        "turkce_tam": "“Kim sabretmeye gayret ederse Allah ona sabır verir. Hiç kimseye sabırdan daha hayırlı ve daha geniş bir nimet verilmemiştir.”",
        "hadis_metni": "Hiçbir kula, her türlü imtihanı göğüslemesini sağlayan sabırdan daha hayırlı bir ikram verilmemiştir.",
        "kaynak_ref": "Buhârî, Zekât 50, Rikâk 20; Müslim, Zekât 124",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1994,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَا يُصِيبُ الْمُسْلِمَ مِنْ نَصَبٍ وَلا وَصَبٍ وَلا هَمٍّ وَلا حَزَنٍ وَلا أَذًى وَلا غَمٍّ، حَتَّى الشَّوْكَةِ يُشَاكُهَا، إِلا كَفَّرَ اللَّهُ بِهَا مِنْ خَطَايَاهُ",
        "arapca_veciz": "مَا يُصِيبُ الْمُسْلِمَ مِنْ نَصَبٍ وَلا وَصَبٍ إِلا كَفَّرَ اللَّهُ بِهَا مِنْ خَطَايَاهُ",
        "turkce_tam": "“Müslümanın başına gelen hiçbir yorgunluk, hastalık, tasa, keder, eziyet ve hüzün yoktur ki —ayağına batan bir diken dahi olsa— Allah onunla günahlarını bağışlamasın.”",
        "hadis_metni": "Müminin ayağına batan bir diken dahi olsa, karşılaştığı her keder ve hastalık onun günahlarına kefaret olur.",
        "kaynak_ref": "Buhârî, Merdâ 1; Müslim, Birr 52",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1995,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُصِبْ مِنْهُ",
        "arapca_veciz": "مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُصِبْ مِنْهُ",
        "turkce_tam": "“Allah kimin hakkında hayır dilerse, onu arındırmak için birtakım sıkıntı ve musibetlerle imtihan eder.”",
        "hadis_metni": "Allah bir kulu hakkında hayır dilerse, manevi derecesini yükseltmek için onu imtihana tabi tutar.",
        "kaynak_ref": "Buhârî, Merdâ 1; Muvatta', Cenâiz 40",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1996,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Âişe (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ رَفِيقٌ يُحِبُّ الرِّفْقَ فِي الأَمْرِ كُلِّهِ",
        "arapca_veciz": "إِنَّ اللَّهَ رَفِيقٌ يُحِبُّ الرِّفْقَ فِي الأَمْرِ كُلِّهِ",
        "turkce_tam": "“Şüphesiz Allah Rıfk (şefkat ve nezaket) sahibidir; her işte yumuşaklığı ve zarafeti sever.”",
        "hadis_metni": "Şüphesiz ki Allah lütufkârdır; her işte nezaket, zarafet ve yumuşak huyluluğu sever.",
        "kaynak_ref": "Buhârî, İstitâbe 4, Edeb 35; Müslim, Selâm 10",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1997,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Muâz b. Cebel (r.a.)",
        "arapca_metin": "مَنْ كَانَ آخِرُ كَلامِهِ لا إِلَهَ إِلا اللَّهُ دَخَلَ الْجَنَّةَ",
        "arapca_veciz": "مَنْ كَانَ آخِرُ كَلامِهِ لا إِلَهَ إِلا اللَّهُ دَخَلَ الْجَنَّةَ",
        "turkce_tam": "“Kimin son sözü 'Lâ ilâhe illallâh' olursa cennete girer.”",
        "hadis_metni": "Son nefesinde dili ve kalbiyle 'Lâ ilâhe illallâh' tevhidini tasdik eden cennete dahil olur.",
        "kaynak_ref": "Buhârî, Cenâiz 1; Ebû Dâvûd, Cenâiz 16",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1998,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "أَقْرَبُ مَا يَكُونُ الْعَبْدُ مِنْ رَبِّهِ وَهُوَ سَاجِدٌ، فَأَكْثِرُوا الدُّعَاءَ",
        "arapca_veciz": "أَقْرَبُ مَا يَكُونُ الْعَبْدُ مِنْ رَبِّهِ وَهُوَ سَاجِدٌ",
        "turkce_tam": "“Kulun Rabbine en yakın olduğu an secde anıdır; öyleyse secdede duayı çokça yapınız!”",
        "hadis_metni": "Kulun Rabbine manen en yakın olduğu an secde halidir; o anda samimiyetle dua ediniz.",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 1133; Müslim, Salât 215",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1999,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Ömer (r.a.)",
        "arapca_metin": "إِذَا أَمْسَيْتَ فَلا تَنْتَظِرِ الصَّبَاحَ، وَإِذَا أَصْبَحْتَ فَلا تَنْتَظِرِ الْمَسَاءَ، وَخُذْ مِنْ صِحَّتِكَ لِمَرَضِكَ، وَمِنْ حَيَاتِكَ لِمَوْتِكَ",
        "arapca_veciz": "خُذْ مِنْ صِحَّتِكَ لِمَرَضِكَ، وَمِنْ حَيَاتِكَ لِمَوْتِكَ",
        "turkce_tam": "“Akşama çıktığında sabahı bekleme; sabaha erdiğinde akşamı bekleme. Sağlığından hastalığın için, hayatından da ölümün için azık hazırla!”",
        "hadis_metni": "Hayattayken ölümün için, sağlıklıyken hastalık günlerin için salih amellerle azık hazırla.",
        "kaynak_ref": "Buhârî, Rikâk 3; Tirmizî, Zühd 25",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 2000,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "تَرَكْتُ فِيكُمْ أَمْرَيْنِ لَنْ تَضِلُّوا مَا تَمَسَّكْتُمْ بِهِمَا: كِتَابَ اللَّهِ وَسُنَّةَ نَبِيِّهِ",
        "arapca_veciz": "تَرَكْتُ فِيكُمْ أَمْرَيْنِ لَنْ تَضِلُّوا مَا تَمَسَّكْتُمْ بِهِمَا: كِتَابَ اللَّهِ وَسُنَّةَ نَبِيِّهِ",
        "turkce_tam": "“Size iki emanet bırakıyorum; onlara sımsıkı sarıldığınız müddetçe asla yolunuzu şaşırmazsınız: Allah'ın Kitabı ve Resûlü'nün Sünneti.”",
        "hadis_metni": "Size iki emanet bırakıyorum ki onlara sarıldıkça asla sapmazsınız: Allah'ın Kitabı Kur'an ve Peygamberi'nin Sünneti.",
        "kaynak_ref": "Buhârî, el-İ'tisâm 2; Muvatta', Kader 3; Hâkim 1/93",
        "kart_icin_uygun": 1
    }
]

def main():
    conn = sqlite3.connect(str(DB_YOLU))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM hadisler;")
    mevcut_sayi = c.fetchone()[0]
    print(f"Mevcut Hadis Sayısı: {mevcut_sayi}")

    eklenen = 0
    for h in KALAN_HADISLER:
        c.execute("SELECT id FROM hadisler WHERE hadis_no = ? OR hadis_metni = ?", (h["hadis_no"], h["hadis_metni"]))
        var_mi = c.fetchone()
        if var_mi:
            continue

        c.execute("""
            INSERT INTO hadisler (
                hadis_no, kulliyat, ravi, arapca_metin, arapca_veciz,
                turkce_tam, hadis_metni, kaynak_ref, kelime_sayisi,
                kart_icin_uygun, paylasim_sayisi, son_paylasim
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
        """, (
            h["hadis_no"],
            h["kulliyat"],
            h["ravi"],
            h["arapca_metin"],
            h["arapca_veciz"],
            h["turkce_tam"],
            h["hadis_metni"],
            h["kaynak_ref"],
            len(h["hadis_metni"].split()),
            h["kart_icin_uygun"]
        ))
        eklenen += 1

    conn.commit()

    c.execute("SELECT COUNT(*) FROM hadisler;")
    yeni_toplam = c.fetchone()[0]
    print(f"Eklenen Hadis Sayısı: {eklenen}")
    print(f"Yeni Toplam Hadis: {yeni_toplam}")

    c.execute("SELECT kulliyat, COUNT(*) FROM hadisler GROUP BY kulliyat;")
    print("Güncel Külliyat Dağılımı:", c.fetchall())

    conn.close()

if __name__ == "__main__":
    main()
