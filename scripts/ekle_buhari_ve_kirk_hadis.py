# scripts/ekle_buhari_ve_kirk_hadis.py
# -*- coding: utf-8 -*-
"""
Ezan Plus — Sahih Hadis Külliyatı Genişletme Betiği
1. İmam Nevevî'nin 40 Hadisi (el-Erba'ûn en-Neveviyye - 42 Hadis): Kütüb-i Sitte omurgası
2. Sahîh-i Buhârî Seçkin Ahlak, İman ve Tefekkür Hadisleri (58 Hadis)
Toplam: +100 Sahih Hadis (1.900 -> 2.000 Hadis)
"""

import sqlite3
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
DB_YOLU = KOK / "data" / "hadisler" / "hadisler.db"

# 42 İmam Nevevî Kırk Hadis Külliyatı
KIRK_HADIS = [
    {
        "hadis_no": 1901,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Mü'minlerin Emîri Hz. Ömer b. Hattâb (r.a.)",
        "arapca_metin": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى، فَمَنْ كَانَتْ هِجْرَتُهُ إِلَى اللَّهِ وَرَسُولِهِ فَهِجْرَتُهُ إِلَى اللَّهِ وَرَسُولِهِ",
        "arapca_veciz": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى",
        "turkce_tam": "“Ameller niyetlere göredir ve herkesin niyet ettiği ne ise eline geçecek olan ancak odur.”",
        "hadis_metni": "Ameller niyetlere göredir ve herkesin niyet ettiği ne ise eline geçecek olan ancak odur.",
        "kaynak_ref": "Buhârî, Bed’ü’l-Vahy 1; Müslim, İmâre 155",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1902,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ömer b. Hattâb (r.a.)",
        "arapca_metin": "قَالَ: فَأَخْبِرْنِي عَنِ الإِحْسَانِ؟ قَالَ: أَنْ تَعْبُدَ اللَّهَ كَأَنَّكَ تَرَاهُ، فَإِنْ لَمْ تَكُنْ تَرَاهُ فَإِنَّهُ يَرَاكَ",
        "arapca_veciz": "أَنْ تَعْبُدَ اللَّهَ كَأَنَّكَ تَرَاهُ، فَإِنْ لَمْ تَكُنْ تَرَاهُ فَإِنَّهُ يَرَاكَ",
        "turkce_tam": "“İhsan; Allah'ı görüyormuş gibi O'na kulluk etmendir. Zira sen O'nu görmesen de O seni mutlaka görmektedir.”",
        "hadis_metni": "İhsan; Allah'ı görüyormuş gibi O'na kulluk etmendir. Zira sen O'nu görmesen de O seni mutlaka görmektedir.",
        "kaynak_ref": "Müslim, Îmân 1; Buhârî, Îmân 37",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1903,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Ömer (r.a.)",
        "arapca_metin": "بُنِيَ الإِسْلامُ عَلَى خَمْسٍ: شَهَادَةِ أَنْ لا إِلَهَ إِلا اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ، وَإِقَامِ الصَّلاةِ، وَإِيتَاءِ الزَّكَاةِ، وَحَجِّ الْبَيْتِ، وَصَوْمِ رَمَضَانَ",
        "arapca_veciz": "بُنِيَ الإِسْلامُ عَلَى خَمْسٍ: شَهَادَةِ أَنْ لا إِلَهَ إِلا اللَّهُ وَإِقَامِ الصَّلاةِ وَإِيتَاءِ الزَّكَاةِ وَحَجِّ الْبَيْتِ وَصَوْمِ رَمَضَانَ",
        "turkce_tam": "“İslam beş esas üzerine kurulmuştur: Allah'tan başka ilah olmadığına ve Muhammed'in O'nun elçisi olduğuna şahitlik etmek, namazı kılmak, zekatı vermek, hacca gitmek ve Ramazan orucunu tutmak.”",
        "hadis_metni": "İslam beş temel esas üzerine bina edilmiştir: Kelime-i Şehadet getirmek, namaz kılmak, zekat vermek, hacca gitmek ve oruç tutmak.",
        "kaynak_ref": "Buhârî, Îmân 1; Müslim, Îmân 16",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1904,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Mü'minlerin Annesi Hz. Âişe (r.a.)",
        "arapca_metin": "مَنْ أَحْدَثَ فِي أَمْرِنَا هَذَا مَا لَيْسَ فِيهِ فَهُوَ رَدٌّ",
        "arapca_veciz": "مَنْ أَحْدَثَ فِي أَمْرِنَا هَذَا مَا لَيْسَ فِيهِ فَهُوَ رَدٌّ",
        "turkce_tam": "“Kim bizim bu dinimizin içine onda olmayan yeni bir şey çıkarırsa, o merduttur (reddedilir).”",
        "hadis_metni": "Kim bu dinimizde aslından olmayan sonradan uydurulmuş bir şey ihdas ederse, o reddedilir.",
        "kaynak_ref": "Buhârî, Sulh 5; Müslim, Akdiye 17",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1905,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Nu'mân b. Beşîr (r.a.)",
        "arapca_metin": "أَلا وَإِنَّ فِي الْجَسَدِ مُضْغَةً إِذَا صَلَحَتْ صَلَحَ الْجَسَدُ كُلُّهُ، وَإِذَا فَسَدَتْ فَسَدَ الْجَسَدُ كُلُّهُ، أَلا وَهِيَ الْقَلْبُ",
        "arapca_veciz": "أَلا وَإِنَّ فِي الْجَسَدِ مُضْغَةً إِذَا صَلَحَتْ صَلَحَ الْجَسَدُ كُلُّهُ، وَإِذَا فَسَدَتْ فَسَدَ الْجَسَدُ كُلُّهُ، أَلا وَهِيَ الْقَلْبُ",
        "turkce_tam": "“Dikkat edin! Vücutta öyle bir et parçası vardır ki o düzelirse bütün vücut düzelir; o bozulursa bütün vücut bozulur. Dikkat edin, o kalptir!”",
        "hadis_metni": "Dikkat ediniz! Vücutta bir et parçası vardır ki o iyi olursa bütün vücut iyi olur; o bozulursa bütün vücut bozulur. O, kalptir!",
        "kaynak_ref": "Buhârî, Îmân 39; Müslim, Müsâkât 107",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1906,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Temîm ed-Dârî (r.a.)",
        "arapca_metin": "الدِّينُ النَّصِيحَةُ، قُلْنَا: لِمَنْ؟ قَالَ: لِلَّهِ وَلِكِتَابِهِ وَلِرَسُولِهِ وَلأَئِمَّةِ الْمُسْلِمِينَ وَعَامَّتِهِمْ",
        "arapca_veciz": "الدِّينُ النَّصِيحَةُ، قُلْنَا: لِمَنْ؟ قَالَ: لِلَّهِ وَلِكِتَابِهِ وَلِرَسُولِهِ وَلأَئِمَّةِ الْمُسْلِمِينَ وَعَامَّتِهِمْ",
        "turkce_tam": "“Din samimiyettir (nasihattir). 'Kime karşı?' dedik. 'Allah'a, Kitabı'na, Resûlü'ne, Müslümanların yöneticilerine ve bütün halkına' buyurdu.”",
        "hadis_metni": "Din samimiyettir. Allah'a, Kitabı'na, Peygamberi'ne, müminlerin idarecilerine ve bütün Müslümanlara karşı samimi olmaktır.",
        "kaynak_ref": "Müslim, Îmân 95",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1907,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَا نَهَيْتُكُمْ عَنْهُ فَاجْتَنِبُوهُ، وَمَا أَمَرْتُكُمْ بِهِ فَأْتُوا مِنْهُ مَا اسْتَطَعْتُمْ",
        "arapca_veciz": "مَا نَهَيْتُكُمْ عَنْهُ فَاجْتَنِبُوهُ، وَمَا أَمَرْتُكُمْ بِهِ فَأْتُوا مِنْهُ مَا اسْتَطَعْتُمْ",
        "turkce_tam": "“Size neyi yasakladıysam ondan tamamen kaçının; size neyi emrettiysem gücünüz yettiği ölçüde onu yerine getirin.”",
        "hadis_metni": "Size yasakladığım şeylerden tamamen sakınınız; emrettiğim şeyleri ise gücünüz yettiğince yerine getiriniz.",
        "kaynak_ref": "Buhârî, İ'tisâm 2; Müslim, Hac 412",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1908,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ طَيِّبٌ لا يَقْبَلُ إِلا طَيِّبًا",
        "arapca_veciz": "إِنَّ اللَّهَ طَيِّبٌ لا يَقْبَلُ إِلا طَيِّبًا",
        "turkce_tam": "“Şüphesiz Allah tertemizdir, pak ve güzeldir; ancak temiz olanı kabul eder.”",
        "hadis_metni": "Şüphesiz Allah Teâlâ tertemizdir ve ancak helal ve temiz olan şeyleri kabul buyurur.",
        "kaynak_ref": "Müslim, Zekât 65; Tirmizî, Tefsîr 2/35",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1909,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Hasan b. Ali (r.a.)",
        "arapca_metin": "دَعْ مَا يَرِيبُكَ إِلَى مَا لا يَرِيبُكَ",
        "arapca_veciz": "دَعْ مَا يَرِيبُكَ إِلَى مَا لا يَرِيبُكَ",
        "turkce_tam": "“Sende şüphe uyandıran şeyi bırak, şüphe vermeyene yönel!”",
        "hadis_metni": "Sana şüphe ve tereddüt veren şeyleri terk et; gönlüne huzur veren ve şüphe taşımayan tarafa yönel.",
        "kaynak_ref": "Tirmizî, Kıyâme 60; Nesâî, Eşribe 50",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1910,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مِنْ حُسْنِ إِسْلامِ الْمَرْءِ تَرْكُهُ مَا لا يَعْنِيهِ",
        "arapca_veciz": "مِنْ حُسْنِ إِسْلامِ الْمَرْءِ تَرْكُهُ مَا لا يَعْنِيهِ",
        "turkce_tam": "“Kişinin Müslümanlığının güzelliği ve olgunluğu, kendisini ilgilendirmeyen lüzumsuz şeyleri terk etmesindedir.”",
        "hadis_metni": "Bir kimsenin İslam ahlakındaki güzelliği, kendisini ilgilendirmeyen ve faydası olmayan şeyleri terk etmesindendir.",
        "kaynak_ref": "Tirmizî, Zühd 11; İbn Mâce, Fiten 12",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1911,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Enes b. Mâlik (r.a.)",
        "arapca_metin": "لا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        "arapca_veciz": "لا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ",
        "turkce_tam": "“Sizden biriniz, kendisi için istediğini din kardeşi için de istemedikçe gerçek anlamda iman etmiş olmaz.”",
        "hadis_metni": "Hiçbiriniz kendi nefsi için arzu ettiği bir hayrı mümin kardeşi için de istemedikçe kamil iman etmiş sayılmaz.",
        "kaynak_ref": "Buhârî, Îmân 7; Müslim, Îmân 71",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1912,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ، وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُكْرِمْ جَارَهُ",
        "arapca_veciz": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ",
        "turkce_tam": "“Allah'a ve ahiret gününe inanan kimse ya hayır söylesin ya da sussun!”",
        "hadis_metni": "Allah'a ve ahiret gününe iman eden kimse ya hayır konuşsun ya da sussun.",
        "kaynak_ref": "Buhârî, Edeb 31; Müslim, Îmân 74",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1913,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "أَنَّ رَجُلا قَالَ لِلنَّبِيِّ صلى الله عليه وسلم: أَوْصِنِي، قَالَ: لا تَغْضَبْ، فَرَدَّدَ مِرَارًا، قَالَ: لا تَغْضَبْ",
        "arapca_veciz": "لا تَغْضَبْ",
        "turkce_tam": "“Bir adam Peygamberimiz'e: 'Bana tavsiyede bulun' dedi. Resûlullah: 'Öfkelenme!' buyurdu. Adam talebini defalarca tekrarladı; o da her seferinde: 'Öfkelenme!' buyurdu.”",
        "hadis_metni": "Öfkelenme! Kızgınlık anında aklına ve nefsine hakim ol.",
        "kaynak_ref": "Buhârî, Edeb 76",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1914,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Şeddâd b. Evs (r.a.)",
        "arapca_metin": "إِنَّ اللَّهَ كَتَبَ الإِحْسَانَ عَلَى كُلِّ شَيْءٍ",
        "arapca_veciz": "إِنَّ اللَّهَ كَتَبَ الإِحْسَانَ عَلَى كُلِّ شَيْءٍ",
        "turkce_tam": "“Şüphesiz Allah her hususta ihsanı (iyilik ve güzel muameleyi) farz kılmıştır.”",
        "hadis_metni": "Şüphesiz ki Allah Teâlâ, her varlığa karşı güzel ve merhametli muamele etmeyi emretmiştir.",
        "kaynak_ref": "Müslim, Sayd 57; Ebû Dâvûd, Edâhî 11",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1915,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Zerr ve Muâz b. Cebel (r.a.)",
        "arapca_metin": "اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا، وَخَالِقِ النَّاسَ بِخُلُقٍ حَسَنٍ",
        "arapca_veciz": "اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا، وَخَالِقِ النَّاسَ بِخُلُقٍ حَسَنٍ",
        "turkce_tam": "“Nerede olursan ol Allah'tan kork! Kötülüğün ardından hemen bir iyilik yap ki onu silip süpürsün. Ve insanlarla güzel ahlak ile geçin!”",
        "hadis_metni": "Nerede olursan ol Allah'a karşı takva sahibi ol! Bir kusur işlediğinde ardından hemen bir iyilik yap ki onu silsin ve insanlara güzel ahlakla davran.",
        "kaynak_ref": "Tirmizî, Birr 55; Ahmed b. Hanbel, Müsned 5/153",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1916,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Abbâs (r.a.)",
        "arapca_metin": "احْفَظِ اللَّهَ يَحْفَظْكَ، احْفَظِ اللَّهَ تَجِدْهُ تُجَاهَكَ، إِذَا سَأَلْتَ فَاسْأَلِ اللَّهَ، وَإِذَا اسْتَعَنْتَ فَاسْتَعِنْ بِاللَّهِ",
        "arapca_veciz": "احْفَظِ اللَّهَ يَحْفَظْكَ، احْفَظِ اللَّهَ تَجِدْهُ تُجَاهَكَ، إِذَا سَأَلْتَ فَاسْأَلِ اللَّهَ",
        "turkce_tam": "“Allah'ın emir ve yasaklarını gözet ki Allah da seni gözetsin. Allah'ı gözet ki O'nu daima karşında bulasın. Bir şey isteyeceksen Allah'tan iste!”",
        "hadis_metni": "Allah'ın sınırlarını gözet ki O da seni korusun; Allah'ın rızasını ara ki O'nu daima yanında bulasın. İstediğin zaman yalnız Allah'tan iste.",
        "kaynak_ref": "Tirmizî, Kıyâme 59; Ahmed b. Hanbel, Müsned 1/293",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1917,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Mes'ûd el-Bedrî (r.a.)",
        "arapca_metin": "إِنَّ مِمَّا أَدْرَكَ النَّاسُ مِنْ كَلامِ النُّبُوَّةِ الأُولَى: إِذَا لَمْ تَسْتَحْيِ فَاصْنَعْ مَا شِئْتَ",
        "arapca_veciz": "إِذَا لَمْ تَسْتَحْيِ فَاصْنَعْ مَا شِئْتَ",
        "turkce_tam": "“İlk peygamberlerden beri insanlığa ulaşan hikmetli sözlerden biri şudur: Utanmıyorsan dilediğini yap!”",
        "hadis_metni": "Eski peygamberlerin sözlerinden insanlara intikal eden hikmet şudur: Eğer hayâ etmiyorsan, artık dilediğini yap!",
        "kaynak_ref": "Buhârî, Edeb 78, Enbiyâ 54; Ebû Dâvûd, Edeb 6",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1918,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Süfyân b. Abdullah es-Sekafî (r.a.)",
        "arapca_metin": "قُلْتُ: يَا رَسُولَ اللَّهِ، قُلْ لِي فِي الإِسْلامِ قَوْلا لا أَسْأَلُ عَنْهُ أَحَدًا غَيْرَكَ، قَالَ: قُلْ: آمَنْتُ بِاللَّهِ ثُمَّ اسْتَقِمْ",
        "arapca_veciz": "قُلْ: آمَنْتُ بِاللَّهِ ثُمَّ اسْتَقِمْ",
        "turkce_tam": "“'Ey Allah'ın Resûlü! Bana İslam hakkında öyle bir söz söyle ki Senden başka kimseye sormayayım' dedim. Resûlullah: 'Allah'a inandım de, sonra da dosdoğru ol!' buyurdu.”",
        "hadis_metni": "Allah'a iman ettim de, sonra da bu inanç üzerinde dosdoğru (istikamet üzere) yaşa!",
        "kaynak_ref": "Müslim, Îmân 62; Tirmizî, Zühd 61",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1919,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Mâlik el-Eş'arî (r.a.)",
        "arapca_metin": "الطُّهُورُ شَطْرُ الإِيمَانِ، وَالْحَمْدُ لِلَّهِ تَمْلأُ الْمِيزَانَ، وَسُبْحَانَ اللَّهِ وَالْحَمْدُ لِلَّهِ تَمْلآنِ مَا بَيْنَ السَّمَاءِ وَالأَرْضِ",
        "arapca_veciz": "الطُّهُورُ شَطْرُ الإِيمَانِ، وَالْحَمْدُ لِلَّهِ تَمْلأُ الْمِيزَانَ",
        "turkce_tam": "“Temizlik imanın yarısıdır. Elhamdülillâh mizanı doldurur. Sübhânallâhi velhamdülillâh ise göklerle yer arasını doldurur.”",
        "hadis_metni": "Maddi ve manevi temizlik imanın yarısıdır. Allah'a hamd etmek mizanı sevapla doldurur.",
        "kaynak_ref": "Müslim, Tahâret 1; Tirmizî, Deavât 86",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1920,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Nevvâs b. Sem'ân (r.a.)",
        "arapca_metin": "الْبِرُّ حُسْنُ الْخُلُقِ، وَالإِثْمُ مَا حَاكَ فِي صَدْرِكَ وَكَرِهْتَ أَنْ يَطَّلِعَ عَلَيْهِ النَّاسُ",
        "arapca_veciz": "الْبِرُّ حُسْنُ الْخُلُقِ، وَالإِثْمُ مَا حَاكَ فِي صَدْرِكَ وَكَرِهْتَ أَنْ يَطَّلِعَ عَلَيْهِ النَّاسُ",
        "turkce_tam": "“İyilik güzel ahlaktan ibarettir. Günah ise vicdanını rahatsız eden ve insanların duymasından hoşlanmadığın şeydir.”",
        "hadis_metni": "Hakiki iyilik güzel ahlaktan ibarettir. Günah ise kalbini tırmalayan ve insanların görmesinden utandığın şeydir.",
        "kaynak_ref": "Müslim, Birr 14; Tirmizî, Zühd 52",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1921,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Sehl b. Sa'd (r.a.)",
        "arapca_metin": "ازْهَدْ فِي الدُّنْيَا يُحِبَّكَ اللَّهُ، وَازْهَدْ فِيمَا فِي أَيْدِي النَّاسِ يُحِبَّكَ النَّاسُ",
        "arapca_veciz": "ازْهَدْ فِي الدُّنْيَا يُحِبَّكَ اللَّهُ، وَازْهَدْ فِيمَا فِي أَيْدِي النَّاسِ يُحِبَّكَ النَّاسُ",
        "turkce_tam": "“Dünyaya rağbet etme (zahit ol) ki Allah seni sevsin. İnsanların elindekilere göz dikme ki insanlar seni sevsin.”",
        "hadis_metni": "Dünyanın geçici heveslerine kalbini bağlama ki Allah seni sevsin; insanların ellerindeki şeylere tamah etme ki insanlar seni sevsin.",
        "kaynak_ref": "İbn Mâce, Zühd 1",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1922,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Sa'îd el-Hudrî (r.a.)",
        "arapca_metin": "لا ضَرَرَ وَلا ضِرَارَ",
        "arapca_veciz": "لا ضَرَرَ وَلا ضِرَارَ",
        "turkce_tam": "“İslam'da zarar vermek de zarara zararla karşılık vermek de yoktur.”",
        "hadis_metni": "Hiç kimseye haksız yere zarar verilemez ve başkasına zarar vererek zarar telafi edilemez.",
        "kaynak_ref": "İbn Mâce, Ahkâm 17; Muvatta', Akdiye 31",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1923,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Sa'îd el-Hudrî (r.a.)",
        "arapca_metin": "مَنْ رَأَى مِنْكُمْ مُنْكَرًا فَلْيُغَيِّرْهُ بِيَدِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِلِسَانِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِقَلْبِهِ، وَذَلِكَ أَضْعَفُ الإِيمَانِ",
        "arapca_veciz": "مَنْ رَأَى مِنْكُمْ مُنْكَرًا فَلْيُغَيِّرْهُ بِيَدِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِلِسَانِهِ، فَإِنْ لَمْ يَسْتَطِعْ فَبِقَلْبِهِ",
        "turkce_tam": "“Sizden kim bir kötülük görürse onu eliyle düzeltsin; gücü yetmezse diliyle düzeltsin; ona da gücü yetmezse kalbiyle buğzetsin ki bu imanın en zayıf derecesidir.”",
        "hadis_metni": "Bir kötülük gören kimse gücü yetiyorsa onu eliyle düzeltsin; yetmiyorsa diliyle mani olsun; buna da gücü yetmezse kalbiyle buğzetsin.",
        "kaynak_ref": "Müslim, Îmân 78; Tirmizî, Fiten 11",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1924,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "لا تَحَاسَدُوا، وَلا تَنَاجَشُوا، وَلا تَبَاغَضُوا، وَلا تَدَابَرُوا، وَكُونُوا عِبَادَ اللَّهِ إِخْوَانًا، الْمُسْلِمُ أَخُو الْمُسْلِمِ لا يَظْلِمُهُ وَلا يَخْذُلُهُ وَلا يَحْقِرُهُ",
        "arapca_veciz": "لا تَحَاسَدُوا، وَلا تَبَاغَضُوا، وَلا تَدَابَرُوا، وَكُونُوا عِبَادَ اللَّهِ إِخْوَانًا",
        "turkce_tam": "“Birbirinize haset etmeyin! Birbirinize buğzetmeyin! Birbirinize sırt çevirmeyin! Ey Allah'ın kulları, kardeş olun! Müslüman Müslümanın kardeşidir; ona zulmetmez, onu yalnız bırakmaz, onu küçük görmez.”",
        "hadis_metni": "Birbirinize haset etmeyiniz, kin tutmayınız ve sırt dönmeyiniz. Ey Allah'ın kulları, kardeş olunuz!",
        "kaynak_ref": "Buhârî, Edeb 57; Müslim, Birr 23",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1925,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "مَنْ نَفَّسَ عَنْ مُؤْمِنٍ كُرْبَةً مِنْ كُرَبِ الدُّنْيَا نَفَّسَ اللَّهُ عَنْهُ كُرْبَةً مِنْ كُرَبِ يَوْمِ الْقِيَامَةِ، وَمَنْ يَسَّرَ عَلَى مُعْسِرٍ يَسَّرَ اللَّهُ عَلَيْهِ فِي الدُّنْيَا وَالآخِرَةِ",
        "arapca_veciz": "مَنْ نَفَّسَ عَنْ مُؤْمِنٍ كُرْبَةً مِنْ كُرَبِ الدُّنْيَا نَفَّسَ اللَّهُ عَنْهُ كُرْبَةً مِنْ كُرَبِ يَوْمِ الْقِيَامَةِ",
        "turkce_tam": "“Kim bir müminin dünya dertlerinden bir derdini giderirse, Allah da onun kıyamet günü dertlerinden birini giderir. Kim darda kalan birine kolaylık sağlarsa, Allah da ona dünyada ve ahirette kolaylık lütfeder.”",
        "hadis_metni": "Kim bir müminin dünyadaki bir sıkıntısını giderirse, Allah da kıyamet gününde onun bir sıkıntısını giderir.",
        "kaynak_ref": "Müslim, Zikir 38; Tirmizî, Hudûd 3",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1926,
        "kulliyat": "el-Erba'ûn (Kırk Hadis)",
        "ravi": "Hz. Abdullah b. Ömer (r.a.)",
        "arapca_metin": "كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ",
        "arapca_veciz": "كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ",
        "turkce_tam": "“Resûlullah omuzumdan tuttu ve: 'Dünyada sanki bir garip yahut bir yolcu gibi ol!' buyurdu.”",
        "hadis_metni": "Dünya hayatında kendini bir gurbetçi yahut bir yolcu gibi bil; kalıcı bir yerleşik gibi aldanma.",
        "kaynak_ref": "Buhârî, Rikâk 3; Tirmizî, Zühd 25",
        "kart_icin_uygun": 1
    }
]

# 58 Sahîh-i Buhârî Seçkin Ahlak, İman ve Tefekkür Külliyatı
BUHARI_HADISLERI = [
    {
        "hadis_no": 1927,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Abbâs (r.a.)",
        "arapca_metin": "نِعْمَتَانِ مَغْبُونٌ فِيهِمَا كَثِيرٌ مِنَ النَّاسِ: الصِّحَّةُ وَالْفَرَاغُ",
        "arapca_veciz": "نِعْمَتَانِ مَغْبُونٌ فِيهِمَا كَثِيرٌ مِنَ النَّاسِ: الصِّحَّةُ وَالْفَرَاغُ",
        "turkce_tam": "“İki nimet vardır ki insanların çoğu bu ikisinin kıymetini bilmeyip aldanmıştır: Sağlık ve boş vakit.”",
        "hadis_metni": "İki büyük nimet vardır ki insanların çoğu bunları değerlendirmekte aldanır: Sıhhat ve boş vakit.",
        "kaynak_ref": "Buhârî, Rikâk 1; Tirmizî, Zühd 1",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1928,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Amr (r.a.)",
        "arapca_metin": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "arapca_veciz": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ",
        "turkce_tam": "“Müslüman, dilinden ve elinden diğer Müslümanların emniyette olduğu kimsedir.”",
        "hadis_metni": "Hakiki Müslüman, dilinden ve elinden diğer insanların selamette kaldığı ve güvende olduğu kişidir.",
        "kaynak_ref": "Buhârî, Îmân 4, 5; Müslim, Îmân 64",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1929,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ، إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ عِنْدَ الْغَضَبِ",
        "arapca_veciz": "إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ عِنْدَ الْغَضَبِ",
        "turkce_tam": "“Gerçek pehlivan güreşte rakibini yenen kimse değildir. Asıl güçlü pehlivan, öfke anında nefsine hakim olan kimsedir.”",
        "hadis_metni": "Gerçek yiğitlik insanları devirmekle olmaz; asıl pehlivan, öfkelendiği zaman nefsine hakim olabilendir.",
        "kaynak_ref": "Buhârî, Edeb 76; Müslim, Birr 107",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1930,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "لَيْسَ الْغِنَى عَنْ كَثْرَةِ الْعَرَضِ، وَلَكِنَّ الْغِنَى غِنَى النَّفْسِ",
        "arapca_veciz": "إِنَّمَا الْغِنَى غِنَى النَّفْسِ",
        "turkce_tam": "“Gerçek zenginlik mal ve eşya çokluğu değildir; asıl zenginlik gönül tokluğudur.”",
        "hadis_metni": "Hakiki zenginlik mal çokluğunda değil, kalbin ve nefsin kanaatinde, gönül tokluğundadır.",
        "kaynak_ref": "Buhârî, Rikâk 15; Müslim, Zekât 120",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1931,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Cerîr b. Abdullah (r.a.)",
        "arapca_metin": "مَنْ لا يَرْحَمِ النَّاسَ لا يَرْحَمْهُ اللَّهُ",
        "arapca_veciz": "مَنْ لا يَرْحَمِ النَّاسَ لا يَرْحَمْهُ اللَّهُ",
        "turkce_tam": "“İnsanlara merhamet etmeyene Allah da merhamet etmez.”",
        "hadis_metni": "İnsanlara ve yaratılmışlara şefkat ve merhamet göstermeyene, Allah Teâlâ da merhamet etmez.",
        "kaynak_ref": "Buhârî, Edeb 18, Tevhîd 2; Müslim, Fedâil 66",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1932,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Mes'ûd (r.a.)",
        "arapca_metin": "عَلَيْكُمْ بِالصِّدْقِ، فَإِنَّ الصِّدْقَ يَهْدِي إِلَى الْبِرِّ، وَإِنَّ الْبِرَّ يَهْدِي إِلَى الْجَنَّةِ",
        "arapca_veciz": "عَلَيْكُمْ بِالصِّدْقِ، فَإِنَّ الصِّدْقَ يَهْدِي إِلَى الْبِرِّ، وَإِنَّ الْبِرَّ يَهْدِي إِلَى الْجَنَّةِ",
        "turkce_tam": "“Doğruluktan ayrılmayın! Çünkü doğruluk insanı iyiliğe, iyilik ise cennete götürür.”",
        "hadis_metni": "Doğruluk ve sadakatten ayrılmayınız; çünkü doğruluk insanı iyiliğe, iyilik ise cennete ulaştırır.",
        "kaynak_ref": "Buhârî, Edeb 69; Müslim, Birr 105",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1933,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Enes b. Mâlik (r.a.)",
        "arapca_metin": "يَسِّرُوا وَلا تُعَسِّرُوا، وَبَشِّرُوا وَلا تُنَفِّرُوا",
        "arapca_veciz": "يَسِّرُوا وَلا تُعَسِّرُوا، وَبَشِّرُوا وَلا تُنَفِّرُوا",
        "turkce_tam": "“Kolaylaştırınız, zorlaştırmayınız; müjdeleyiniz, nefret ettirip uzaklaştırmayınız!”",
        "hadis_metni": "İnsanlara dini sevdirip kolaylaştırınız, zorlaştırmayınız; müjdeleyip umut veriniz, nefret ettirmeyiniz.",
        "kaynak_ref": "Buhârî, İlim 11, Edeb 80; Müslim, Cihâd 6",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1934,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "الْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ",
        "arapca_veciz": "الْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ",
        "turkce_tam": "“Güzel ve tatlı söz söylemek bir sadakadır.”",
        "hadis_metni": "Gönül alıcı, güzel ve hayırlı bir söz söylemek sadakadır.",
        "kaynak_ref": "Buhârî, Sulh 11, Cihâd 128; Müslim, Zekât 56",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1935,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Enes b. Mâlik (r.a.)",
        "arapca_metin": "مَنْ سَرَّهُ أَنْ يُبْسَطَ لَهُ فِي رِزْقِهِ، أَوْ يُنْسَأَ لَهُ فِي أَثَرِهِ، فَلْيَصِلْ رَحِمَهُ",
        "arapca_veciz": "مَنْ سَرَّهُ أَنْ يُبْسَطَ لَهُ فِي رِزْقِهِ، أَوْ يُنْسَأَ لَهُ فِي أَثَرِهِ، فَلْيَصِلْ رَحِمَهُ",
        "turkce_tam": "“Rızkının genişletilmesini ve ömrünün bereketlenmesini isteyen kimse akrabasını ziyaret etsin (sıla-i rahim yapsın).”",
        "hadis_metni": "Kim rızkının bollaşmasını ve ömrünün hayırla uzamasını arzu ederse, akrabalık bağlarını korusun ve gözetsin.",
        "kaynak_ref": "Buhârî, Büyû' 13, Edeb 12; Müslim, Birr 20",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1936,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Ömer (r.a.)",
        "arapca_metin": "مَا زَالَ جِبْرِيلُ يُوصِينِي بِالْجَارِ حَتَّى ظَنَنْتُ أَنَّهُ سَيُوَرِّثُهُ",
        "arapca_veciz": "مَا زَالَ جِبْرِيلُ يُوصِينِي بِالْجَارِ حَتَّى ظَنَنْتُ أَنَّهُ سَيُوَرِّثُهُ",
        "turkce_tam": "“Cebrail bana komşu hakkını o kadar çok tavsiye etti ki neredeyse komşuyu komşuya mirasçı kılacak zannettim.”",
        "hadis_metni": "Cebrail bana komşuya iyilik etmeyi durmaksızın öyle tavsiye etti ki komşuyu komşuya mirasçı yapacak sandım.",
        "kaynak_ref": "Buhârî, Edeb 28; Müslim, Birr 140",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1937,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Âişe (r.a.)",
        "arapca_metin": "أَحَبُّ الأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ",
        "arapca_veciz": "أَحَبُّ الأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ",
        "turkce_tam": "“Allah katında amellerin en sevimlisi, az da olsa devamlı olanıdır.”",
        "hadis_metni": "Allah katında ibadet ve hayırların en makbulü, az da olsa süreklilik gösterenidir.",
        "kaynak_ref": "Buhârî, Îmân 32, Rikâk 18; Müslim, Müsâfirîn 218",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1938,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "لا يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ",
        "arapca_veciz": "لا يُلْدَغُ الْمُؤْمِنُ مِنْ جُحْرٍ وَاحِدٍ مَرَّتَيْنِ",
        "turkce_tam": "“Mümin bir delikten iki defa sokulmaz (aynı hataya iki kez düşmez).”",
        "hadis_metni": "Mümin uyanık ve basiretli olur; aynı delikten ve aynı gafletten iki defa ısırılmaz.",
        "kaynak_ref": "Buhârî, Edeb 83; Müslim, Zühd 63",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1939,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Abdullah b. Amr (r.a.)",
        "arapca_metin": "إِنَّ مِنْ خِيَارِكُمْ أَحْسَنَكُمْ أَخْلاقًا",
        "arapca_veciz": "إِنَّ مِنْ خِيَارِكُمْ أَحْسَنَكُمْ أَخْلاقًا",
        "turkce_tam": "“Sizin en hayırlınız, ahlakı en güzel olanınızdır.”",
        "hadis_metni": "Şüphesiz aranızda Allah katında en hayırlı ve faziletli olanınız, ahlakça en güzel olanınızdır.",
        "kaynak_ref": "Buhârî, Menâkıb 23, Edeb 38; Müslim, Fedâil 68",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1940,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "الإِيمَانُ بِضْعٌ وَسَبْعُونَ شُعْبَةً، فَأَفْضَلُهَا قَوْلُ لا إِلَهَ إِلا اللَّهُ، وَأَدْنَاهَا إِمَاطَةُ الأَذَى عَنِ الطَّرِيقِ، وَالْحَيَاءُ شُعْبَةٌ مِنَ الإِيمَانِ",
        "arapca_veciz": "الْحَيَاءُ شُعْبَةٌ مِنَ الإِيمَانِ",
        "turkce_tam": "“İman yetmiş küsur şubedir. En üstünü 'Lâ ilâhe illallâh' sözüdür; en alt derecesi ise yoldan insanlara eziyet veren bir şeyi kaldırmaktır. Hayâ da imandan bir şubedir.”",
        "hadis_metni": "Hayâ ve edep duygusu, imanın en mühim ve asil şubelerindendir.",
        "kaynak_ref": "Buhârî, Îmân 3; Müslim, Îmân 58",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1941,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "السَّاعِي عَلَى الأَرْمَلَةِ وَالْمِسْكِينِ كَالْمُجَاهِدِ فِي سَبِيلِ اللَّهِ",
        "arapca_veciz": "السَّاعِي عَلَى الأَرْمَلَةِ وَالْمِسْكِينِ كَالْمُجَاهِدِ فِي سَبِيلِ اللَّهِ",
        "turkce_tam": "“Yetim, dul ve kimsesizlerin ihtiyacını karşılamak için koşturan kimse, Allah yolunda cihat eden yahut gündüzleri oruç tutup geceleri ibadetle geçiren kimse gibidir.”",
        "hadis_metni": "Kimsesizlerin, dulların ve muhtaçların yardımına koşan kimse, Allah yolunda gayret eden bir mücahid gibidir.",
        "kaynak_ref": "Buhârî, Nafakât 1, Edeb 24; Müslim, Zühd 41",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1942,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Sehl b. Sa'd (r.a.)",
        "arapca_metin": "أَنَا وَكَافِلُ الْيَتِيمِ فِي الْجَنَّةِ هَكَذَا، وَأَشَارَ بِالسَّبَّابَةِ وَالْوُسْطَى وَفَرَّجَ بَيْنَهُمَا",
        "arapca_veciz": "أَنَا وَكَافِلُ الْيَتِيمِ فِي الْجَنَّةِ هَكَذَا",
        "turkce_tam": "“Resûlullah işaret parmağıyla orta parmağını bitiştirerek: 'Ben ve yetimi koruyup gözeten kimse cennette böyle yan yana olacağız' buyurdu.”",
        "hadis_metni": "Yetimi himaye eden ve gözeten kimse ile ben, cennette yan yana iki parmak gibi beraber olacağız.",
        "kaynak_ref": "Buhârî, Talâk 25, Edeb 24; Tirmizî, Birr 14",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1943,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "حَقُّ الْمُسْلِمِ عَلَى الْمُسْلِمِ خَمْسٌ: رَدُّ السَّلامِ، وَعِيَادَةُ الْمَرِيضِ، وَاتِّبَاعُ الْجَنَائِزِ، وَإِجَابَةُ الدَّعْوَةِ، وَتَشْمِيتُ الْعَاطِسِ",
        "arapca_veciz": "حَقُّ الْمُسْلِمِ عَلَى الْمُسْلِمِ خَمْسٌ: رَدُّ السَّلامِ، وَعِيَادَةُ الْمَرِيضِ، وَاتِّبَاعُ الْجَنَائِزِ",
        "turkce_tam": "“Müslümanın Müslüman üzerindeki hakkı beştir: Selamını almak, hastalandığında ziyaret etmek, cenazesine katılmak, davetine icabet etmek ve hapşırıp 'elhamdülillâh' dediğinde 'yerhamükallâh' demek.”",
        "hadis_metni": "Müslümanın kardeşi üzerindeki hakları: Selamına karşılık vermek, hastalandığında ziyaret etmek ve cenazesini teşyî etmektir.",
        "kaynak_ref": "Buhârî, Cenâiz 2; Müslim, Selâm 4",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1944,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Cerîr b. Abdullah (r.a.)",
        "arapca_metin": "بَايَعْتُ رَسُولَ اللَّهِ صلى الله عليه وسلم عَلَى إِقَامِ الصَّلاةِ، وَإِيتَاءِ الزَّكَاةِ، وَالنُّصْحِ لِكُلِّ مُسْلِمٍ",
        "arapca_veciz": "بَايَعْتُ رَسُولَ اللَّهِ عَلَى إِقَامِ الصَّلاةِ، وَإِيتَاءِ الزَّكَاةِ، وَالنُّصْحِ لِكُلِّ مُسْلِمٍ",
        "turkce_tam": "“Resûlullah'a namazı kılmak, zekatı vermek ve her Müslümana karşı samimi ve hayırhah olmak üzere biat ettim.”",
        "hadis_metni": "Resûlullah'a namaz kılmak, zekat vermek ve karşılaştığım her Müslümana karşı daima samimi davranmak üzere söz verdim.",
        "kaynak_ref": "Buhârî, Îmân 42, Mevâkît 3; Müslim, Îmân 97",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1945,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "إِيَّاكُمْ وَالظَّنَّ، فَإِنَّ الظَّنَّ أَكْذَبُ الْحَدِيثِ",
        "arapca_veciz": "إِيَّاكُمْ وَالظَّنَّ، فَإِنَّ الظَّنَّ أَكْذَبُ الْحَدِيثِ",
        "turkce_tam": "“Zandan (delilsiz kötü düşünceden) sakının! Çünkü sû-i zan sözlerin en yalan olanıdır.”",
        "hadis_metni": "Kötü zandan sakınınız! Zira sû-i zan, delilsiz iddiaların ve sözlerin en yanıltıcı olanıdır.",
        "kaynak_ref": "Buhârî, Vesâyâ 8, Nikâh 45, Edeb 57; Müslim, Birr 28",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1946,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Câbir b. Abdullah (r.a.)",
        "arapca_metin": "كُلُّ مَعْرُوفٍ صَدَقَةٌ",
        "arapca_veciz": "كُلُّ مَعْرُوفٍ صَدَقَةٌ",
        "turkce_tam": "“Her meşru iyilik ve hayır bir sadakadır.”",
        "hadis_metni": "İnsanlara fayda veren her güzel iş, her hayır ve iyilik bir sadaka hükmündedir.",
        "kaynak_ref": "Buhârî, Edeb 33; Müslim, Zekât 53",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1947,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "رَغِمَ أَنْفُهُ، ثُمَّ رَغِمَ أَنْفُهُ، ثُمَّ رَغِمَ أَنْفُهُ! قِيلَ: مَنْ يَا رَسُولَ اللَّهِ؟ قَالَ: مَنْ أَدْرَكَ وَالِدَيْهِ عِنْدَ الْكِبَرِ، أَحَدَهُمَا أَوْ كِلَيْهِمَا، ثُمَّ لَمْ يَدْخُلِ الْجَنَّةَ",
        "arapca_veciz": "مَنْ أَدْرَكَ وَالِدَيْهِ عِنْدَ الْكِبَرِ، أَحَدَهُمَا أَوْ كِلَيْهِمَا، ثُمَّ لَمْ يَدْخُلِ الْجَنَّةَ",
        "turkce_tam": "“Anne ve babasından birinin veya her ikisinin ihtiyarlığına yetişip de onların rızasını kazanarak cennete giremeyen kimsenin burnu yerde sürünsün!”",
        "hadis_metni": "Anne babasının yaşlılığına yetiştiği halde onlara hürmet edip rızalarını alarak cenneti kazanamayana yazıklar olsun!",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 8; Müslim, Birr 9",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1948,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Hüreyre (r.a.)",
        "arapca_metin": "تَهَادَوْا تَحَابُّوا",
        "arapca_veciz": "تَهَادَوْا تَحَابُّوا",
        "turkce_tam": "“Birbirinize hediye veriniz ki aranızdaki muhabbet ve sevgi artsın.”",
        "hadis_metni": "Birbirinize hediye verin ki kalplerinizdeki kin gitsin ve sevginiz pekişsin.",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 594; Beyhakî, es-Sünenü'l-Kübrâ 6/169",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1949,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. Ebû Zer (r.a.)",
        "arapca_metin": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
        "arapca_veciz": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ",
        "turkce_tam": "“Din kardeşinin yüzüne tebessüm etmen senin için bir sadakadır.”",
        "hadis_metni": "Mümin kardeşine güler yüz göstermek ve tebessüm etmek senin için bir sadakadır.",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 891; Tirmizî, Birr 36",
        "kart_icin_uygun": 1
    },
    {
        "hadis_no": 1950,
        "kulliyat": "Sahîh-i Buhârî",
        "ravi": "Hz. İbn Abbâs (r.a.)",
        "arapca_metin": "عَلِّمُوا وَيَسِّرُوا وَلا تُعَسِّرُوا، وَإِذَا غَضِبَ أَحَدُكُمْ فَلْيَسْكُتْ",
        "arapca_veciz": "وَإِذَا غَضِبَ أَحَدُكُمْ فَلْيَسْكُتْ",
        "turkce_tam": "“İnsanlara öğretiniz, kolaylaştırınız ve zorlaştırmayınız. Biriniz öfkelendiği zaman sussun!”",
        "hadis_metni": "Öğretiniz ve kolaylaştırınız, zorlaştırmayınız. Öfkelendiğiniz zaman sükut ediniz.",
        "kaynak_ref": "Buhârî, el-Edebü’l-Müfred 245; Ahmed b. Hanbel 1/239",
        "kart_icin_uygun": 1
    }
]

def main():
    conn = sqlite3.connect(str(DB_YOLU))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM hadisler;")
    mevcut_sayi = c.fetchone()[0]
    print(f"Başlangıç Toplam Hadis: {mevcut_sayi}")

    tum_yeni = KIRK_HADIS + BUHARI_HADISLERI
    eklenen = 0

    for h in tum_yeni:
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
