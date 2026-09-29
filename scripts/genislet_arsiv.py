# scripts/genislet_arsiv.py
# -*- coding: utf-8 -*-
"""
Ezan Plus — Dua ve Kur'an Kavramları Külliyatını Genişletme Betiği
Dualar: 100 -> 150 (50 Yeni Sahih Hadis ve Kur'an Niyazı)
Kavramlar: 200 -> 250 (50 Yeni Râgıb el-İsfahânî Kök Anlamı ve Medine Mushaf Âyeti)
"""

import json
from pathlib import Path
from src.kuran_db import ayet_getir

KOK = Path(__file__).resolve().parent.parent
DUALAR_PATH = KOK / "data" / "dualar" / "dualar.json"
KELIMELER_PATH = KOK / "data" / "kelimeler" / "kelimeler.json"

YENI_DUALAR = [
    {
        "id": 101,
        "dua_basligi": "Secdede İki Secde Arasında Okunan Mağfiret Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Namaz Huşûsu ve İstiğfar Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "رَبِّ اغْفِرْ لِي، رَبِّ اغْفِرْ لِي، وَارْحَمْنِي، وَاهْدِنِي، وَارْزُقْنِي، وَعَافِنِي",
        "arapca_okunus": "Rabbiğfir lî, rabbiğfir lî, verhamnî, vehdinî, verzuknî, ve 'âfinî",
        "turkce_anlam": "Rabbim beni bağışla! Rabbim beni bağışla! **Bana merhamet et, beni doğru yola ilet,** bana rızık ver ve bana afiyet lütfet.",
        "kaynak_ref": "Ebû Dâvûd, Salât, 145; İbn Mâce, İkâme, 23",
        "fazilet_notu": "Resûlullah'ın iki secde arasındaki oturuşta sıkça tekrar ettiği kapsamlı bir af ve afiyet niyazıdır."
    },
    {
        "id": 102,
        "dua_basligi": "Evden Çıkarken Okunan Emniyet ve Tevekkül Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Güne Başlarken ve Yola Çıkarken",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "بِسْمِ اللَّهِ تَوَكَّلْتُ عَلَى اللَّهِ، وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
        "arapca_okunus": "Bismillâhi tevekkeltü 'alallâh, ve lâ havle ve lâ kuvvete illâ billâh",
        "turkce_anlam": "Allah'ın adıyla. **Yalnızca Allah'a tevekkül ettim.** Güç ve kuvvet ancak yüce Allah'ın yardımıyladır.",
        "kaynak_ref": "Ebû Dâvûd, Edeb, 103; Tirmizî, Deavât, 34",
        "fazilet_notu": "Evden çıkarken bu duayı okuyan kimseye 'Hidayete erdirildin, ihtiyaçların karşılandı ve korundun' denilir."
    },
    {
        "id": 103,
        "dua_basligi": "Eve Girerken Bereket ve Selam Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Huzurlu Yuva ve Aile Bereketi",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ الْمَوْلَجِ وَخَيْرَ الْمَخْرَجِ، بِسْمِ اللَّهِ وَلَجْنَا وَبِسْمِ اللَّهِ خَرَجْنَا، وَعَلَى اللَّهِ رَبِّنَا تَوَكَّلْنَا",
        "arapca_okunus": "Allâhümme innî es'elüke hayral mevleci ve hayral mahrec, bismillâhi velecnâ ve bismillâhi haracnâ, ve 'alallâhi rabbinâ tevekkelnâ",
        "turkce_anlam": "Allah'ım! Senden girişin ve çıkışın en hayırlısını dilerim. **Allah'ın adıyla girdik, Allah'ın adıyla çıktık** ve Rabbimiz Allah'a tevekkül ettik.",
        "kaynak_ref": "Ebû Dâvûd, Edeb, 103",
        "fazilet_notu": "Eve girildiğinde bu dua okunup aile fertlerine selam verildiğinde şeytan o eve giremez, bereket iner."
    },
    {
        "id": 104,
        "dua_basligi": "Helal Rızık ve Borçtan Kurtuluş Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Maddi Darlık ve Helal Kazanç Arayışı",
        "kimin_duasi": "Hz. Ali (r.a.) / Hz. Peygamber (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ اكْفِنِي بِحَلَالِكَ عَنْ حَرَامِكَ، وَأَغْنِنِي بِفَضْلِكَ عَمَّنْ سِوَاكَ",
        "arapca_okunus": "Allâhümmekfinî bi-halâlike 'an harâmik, ve ağninî bi-fadlike 'ammen sivâk",
        "turkce_anlam": "Allah'ım! **Bana helalinden nasip ederek haramlardan koru;** lütfunla beni Senden başkasına muhtaç eyleme.",
        "kaynak_ref": "Tirmizî, Deavât, 111",
        "fazilet_notu": "Hz. Ali, dağlar kadar borcu olan bir kimsenin bu duaya devam etmesi halinde borcunu ödemeye muvaffak kılınacağını müjdelemiştir."
    },
    {
        "id": 105,
        "dua_basligi": "Gam, Keder ve Borç Yükünden Sığınma Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Ağır Üzüntü ve Borç Baskısı Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ، وَأَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ، وَأَعُوذُ بِكَ مِنَ الْجُبْنِ وَالْبُخْلِ، وَأَعُوذُ بِكَ مِنْ غَلَبَةِ الدَّيْنِ وَقَهْرِ الرِّجَالِ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike minel hemmi vel hazen, ve e'ûzü bike minel 'aczi vel kesel, ve e'ûzü bike minel cübni vel buhl, ve e'ûzü bike min ğalebetid-deyni ve kahrir-ricâl",
        "turkce_anlam": "Allah'ım! **Kederden ve tasadan Sana sığınırım.** Acizlikten ve tembellikten, korkaklıktan ve cimrilikten, borç altında ezilmekten ve insanların baskısından Sana sığınırım.",
        "kaynak_ref": "Buhârî, Deavât, 35; Ebû Dâvûd, Salât, 367",
        "fazilet_notu": "Resûl-i Ekrem'in kederli ve borçlu sahâbî Ebû Ümâme'ye sabah akşam okumasını tavsiye ettiği meşhur nebevî zikirdir."
    },
    {
        "id": 106,
        "dua_basligi": "Öfke ve Hiddet Anında Teskin Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Öfke, Sabırsızlık ve Hiddet Anı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ، اللَّهُمَّ اغْفِرْ لِي ذَنْبِي وَأَذْهِبْ غَيْظَ قَلْبِي",
        "arapca_okunus": "E'ûzü billâhi mineş-şeytânir-racîm, Allâhümmağfir lî zenbî ve ezhib ğayza kalbî",
        "turkce_anlam": "Kovulmuş şeytandan Allah'a sığınırım. **Allah'ım! Günahımı bağışla ve kalbimin öfkesini teskin eyle.**",
        "kaynak_ref": "Buhârî, Bed'ü'l-Halk, 11; Müslim, Birr, 109",
        "fazilet_notu": "Peygamberimiz hiddetlenen birine 'Ben öyle bir kelime biliyorum ki onu söylerse öfkesi diner' buyurarak bu ilticayı tavsiye etmiştir."
    },
    {
        "id": 107,
        "dua_basligi": "Gece Uykusuzluk ve Korku Halinde Okunan Dua",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Korku, Endişe ve Gece Huzursuzluğu",
        "kimin_duasi": "Hz. Hâlid b. Velîd (r.a.) / Hz. Peygamber (s.a.v.)",
        "arapca_metin": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ غَضَبِهِ وَعِقَابِهِ وَشَرِّ عِبَادِهِ، وَمِنْ هَمَزَاتِ الشَّيَاطِينِ وَأَنْ يَحْضُرُونِ",
        "arapca_okunus": "E'ûzü bi-kelimâtillâhit-tâmmâti min ğazabihî ve 'ıkâbihî ve şerri 'ıbâdih, ve min hemezâtiş-şeyâtîni ve en yahdurûn",
        "turkce_anlam": "Allah'ın gazabından, azabından, kullarının şerrinden, **şeytanların kışkırtmalarından ve yanımda bulunmalarından** Allah'ın tastamam kelimelerine sığınırım.",
        "kaynak_ref": "Ebû Dâvûd, Tıbb, 19; Tirmizî, Deavât, 94",
        "fazilet_notu": "Gece uykusunda korkup uyanan veya dehşete kapılan kimseye kalbi emniyet ve sükunet bağışlayan şifalı bir niyazdır."
    },
    {
        "id": 108,
        "dua_basligi": "Kalp Katılığı ve Nimetin Zevalinden Sığınma",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Nimetin Şükrü ve İman Muhafazası",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنْ زَوَالِ نِعْمَتِكَ، وَتَحَوُّلِ عَافِيَتِكَ، وَفُجَاءَةِ نِقْمَتِكَ، وَجَمِيعِ سَخَطِكَ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike min zevâli ni'metik, ve tehavvüli 'âfiyetik, ve fücâ'eti nıkmetik, ve cemî'ı sahatık",
        "turkce_anlam": "Allah'ım! **Nimetinin yok olmasından, verdiğin afiyetin değişmesinden,** ansızın gelecek azabından ve Senin her türlü gazabından Sana sığınırım.",
        "kaynak_ref": "Müslim, Zikir, 96; Ebû Dâvûd, Vitir, 32",
        "fazilet_notu": "Manevi ve maddi huzuru, sıhhati ve ilahi rızayı her daim muhafaza etmek için okunacak en kapsamlı sığınma dualarındandır."
    },
    {
        "id": 109,
        "dua_basligi": "Tembellik ve Yaşlılığın Zaafından Sığınma",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Hayırlı Ömür ve Dinçlik Niyazı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْكَسَلِ وَالْهَرَمِ، وَالْمَأْثَمِ وَالْمَغْرَمِ، وَمِنْ فِتْنَةِ الْقَبْرِ وَعَذَابِ الْقَبْرِ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike minel keseli vel heram, vel me'semi vel mağram, ve min fitnetil kabri ve 'azâbil kabr",
        "turkce_anlam": "Allah'ım! **Tembellikten, elden ayaktan düşüren yaşlılıktan,** günahtan, borçtan, kabir imtihanından ve kabir azabından Sana sığınırım.",
        "kaynak_ref": "Buhârî, Deavât, 39; Müslim, Zikir, 49",
        "fazilet_notu": "İnsanın ömrünü hayırlı ve verimli kılmasını, nefsani uyuşukluktan arınarak hayra koşmasını sağlayan nebevi bir yakarıştır."
    },
    {
        "id": 110,
        "dua_basligi": "Kabir Azabı ve Fitnelerden Sığınma Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Ahiret Bilinci ve Son Nefes Emniyeti",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنْ عَذَابِ جَهَنَّمَ، وَمِنْ عَذَابِ الْقَبْرِ، وَمِنْ فِتْنَةِ الْمَحْيَا وَالْمَمَاتِ، وَمِنْ شَرِّ فِتْنَةِ الْمَسِيحِ الدَّجَّالِ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike min 'azâbi cehennem, ve min 'azâbil kabr, ve min fitnetil mahyâ vel memât, ve min şerri fitnetil mesîhid-deccâl",
        "turkce_anlam": "Allah'ım! Cehennem azabından, **kabir azabından, hayatın ve ölümün fitnesinden** ve Mesîh Deccâl'in şerrinden Sana sığınırım.",
        "kaynak_ref": "Buhârî, Ezân, 149; Müslim, Mesâcid, 128",
        "fazilet_notu": "Resûlullah her namazın son oturuşunda tahiyyat ve salavattan sonra bu dört sığınmayı okumayı ümmetine emretmiştir."
    },
    {
        "id": 111,
        "dua_basligi": "Muhtaçlık ve Zilletten Korunma Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "İffet, Onur ve Gönül Zenginliği Talebi",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْفَقْرِ، وَالْقِلَّةِ، وَالذِّلَّةِ، وَأَعُوذُ بِكَ مِنْ أَنْ أَظْلِمَ أَوْ أُظْلَمَ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike minel fakri, vel kılleti, vez-zilleti, ve e'ûzü bike min en azlime ev uzlem",
        "turkce_anlam": "Allah'ım! **Fakirlikten, yokluktan ve zilletten Sana sığınırım.** Başkasına zulmetmekten veya zulme uğramaktan da Sana sığınırım.",
        "kaynak_ref": "Ebû Dâvûd, Vitir, 32; Nesâî, İstiâze, 14",
        "fazilet_notu": "Müminin izzetini koruyan, hem başkalarına haksızlık yapmaktan hem de haksızlığa boyun eğmekten muhafaza eden nebevi kalkandır."
    },
    {
        "id": 112,
        "dua_basligi": "Musibet ve Keder Anında İnnâ Lillâh Zikri",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Kayıp, Hüzün ve Büyük İmtihan Hali",
        "kimin_duasi": "Sabreden Salih Müminler",
        "arapca_metin": "إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ، اللَّهُمَّ أْجُرْنِي فِي مُصِيبَتِي وَأَخْلِفْ لِي خَيْرًا مِنْهَا",
        "arapca_okunus": "İnnâ lillâhi ve innâ ileyhi râci'ûn, Allâhümme'curnî fî musîbetî ve ahlif lî hayran minhâ",
        "turkce_anlam": "Biz şüphesiz Allah'a aidiz ve sonunda yine O'na döneceğiz. **Allah'ım! Başıma gelen musibette bana ecir ver** ve ardından bana daha hayırlısını lütfet.",
        "kaynak_ref": "Bakara Sûresi, 156. Âyet; Müslim, Cenâiz, 3",
        "fazilet_notu": "Ümmü Seleme bu duayı okuduğunda kendisine vefat eden eşinden daha hayırlı olarak bizzat Resûlullah'ın nasip olduğunu rivayet etmiştir."
    },
    {
        "id": 113,
        "dua_basligi": "Korku ve Tehdit Karşısında Hasbünallâh Sığınması",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Yalnızlık, Korku ve Düşman Baskısı",
        "kimin_duasi": "Hz. İbrâhîm (a.s.) ve Sahâbe-i Kirâm",
        "arapca_metin": "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ، نِعْمَ الْمَوْلَى وَنِعْمَ النَّصِيرُ",
        "arapca_okunus": "Hasbünallâhu ve ni'mel vekîl, ni'mel mevlâ ve ni'men-nasîr",
        "turkce_anlam": "**Allah bize yeter; O ne güzel bir vekildir!** O ne güzel dost ve ne mükemmel bir yardımcıdır.",
        "kaynak_ref": "Âl-i İmrân Sûresi, 173. Âyet; Buhârî, Tefsîr, 3/13",
        "fazilet_notu": "Hz. İbrâhîm ateşe atılırken ve Hz. Muhammed hendek muhasarasında bu zikre sarılmış; ateş gülistana dönmüştür."
    },
    {
        "id": 114,
        "dua_basligi": "Zikir, Şükür ve İbadette Sebat Talebi (Muâz Niyazı)",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Şükür ve Kullukta Samimiyet Arayışı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ، وَشُكْرِكَ، وَحُسْنِ عِبَادَتِكَ",
        "arapca_okunus": "Allâhümme e'ınnî 'alâ zikrike, ve şükrike, ve hüsni 'ıbâdetik",
        "turkce_anlam": "Allah'ım! **Seni anmak, Sana şükretmek ve Sana en güzel şekilde kulluk etmek için** bana yardım eyle.",
        "kaynak_ref": "Ebû Dâvûd, Salât, 361; Tirmizî, Deavât, 102",
        "fazilet_notu": "Peygamber Efendimiz, çok sevdiği Muâz b. Cebel'in elini tutarak her namazın ardından bu duayı asla terk etmemesini vasiyet etmiştir."
    },
    {
        "id": 115,
        "dua_basligi": "Hidayet, Takva, İffet ve Gönül Zenginliği Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Ruhsal Olgunluk ve İffet Arayışı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى، وَالتُّقَى، وَالْعَفَافَ، وَالْغِنَى",
        "arapca_okunus": "Allâhümme innî es'elükel hüdâ, vet-tukâ, vel 'afâfe, vel ğınâ",
        "turkce_anlam": "Allah'ım! Senden **hidayet, takva, iffet ve gönül zenginliği** dilerim.",
        "kaynak_ref": "Müslim, Zikir, 72; Tirmizî, Deavât, 72",
        "fazilet_notu": "Dünya ve ahiret mutluluğunun dört ana sütununu (doğruluk, sakınma, iffet ve tokgözlülük) toplayan en özlü nebevi niyazdır."
    },
    {
        "id": 116,
        "dua_basligi": "Güzel Ahlak ve Karakter Talebi Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Ahlaki Arınma ve Nefis Tezkiyesi",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ اهْدِنِي لِأَحْسَنِ الْأَخْلَاقِ لَا يَهْدِي لِأَحْسَنِهَا إِلَّا أَنْتَ، وَاصْرِفْ عَنِّي سَيِّئَهَا لَا يَصْرِفُ عَنِّي سَيِّئَهَا إِلَّا أَنْتَ",
        "arapca_okunus": "Allâhümmehdinî li-ahsenil ahlâkı lâ yehdî li-ahsenihâ illâ ente, vasrif 'annî seyyiehâ lâ yasrifü 'annî seyyiehâ illâ ente",
        "turkce_anlam": "Allah'ım! Beni ahlakın en güzeline ilet; **ona ancak Sen iletirsin.** Kötü ahlaktan da beni uzak tut; ondan ancak Sen uzak tutarsın.",
        "kaynak_ref": "Müslim, Müsâfirîn, 201; Ebû Dâvûd, Salât, 118",
        "fazilet_notu": "İnsanın iç dünyasını kibir, riya ve hasetten arındırıp Nebevî zarafetle donatan ihlaslı bir ahlak duasıdır."
    },
    {
        "id": 117,
        "dua_basligi": "Zulmetmekten ve Zulme Uğramaktan Sığınma",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Adalet İsteği ve Masumiyeti Koruma",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ أَنْ أَضِلَّ أَوْ أُضَلَّ، أَوْ أَزِلَّ أَوْ أُزَلَّ، أَوْ أَظْلِمَ أَوْ أُظْلَمَ، أَوْ أَجْهَلَ أَوْ يُجْهَلَ عَلَيَّ",
        "arapca_okunus": "Allâhümme innî e'ûzü bike en edılle ev udal, ev ezille ev üzel, ev azlime ev uzlem, ev echele ev yüchele 'aleyy",
        "turkce_anlam": "Allah'ım! **Sapmaktan veya saptırılmaktan, ayağımın kaymasından veya kaydırılmasından,** haksızlık etmekten veya haksızlığa uğramaktan, cahillik yapmaktan veya cahillikle karşılaşmaktan Sana sığınırım.",
        "kaynak_ref": "Ebû Dâvûd, Edeb, 103; Tirmizî, Deavât, 34",
        "fazilet_notu": "Peygamber Efendimiz evinden her çıktığında göğe bakarak bu duayı okur, adalet ve vakarla gününe başlardı."
    },
    {
        "id": 118,
        "dua_basligi": "Gece Teheccüd Vaktinde Nur Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Teheccüd, Gece İbadeti ve Aydınlanma",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ اجْعَلْ فِي قَلْبِي نُورًا، وَفِي بَصَرِي نُورًا، وَفِي سَمْعِي نُورًا، وَعَنْ يَمِينِي نُورًا، وَعَنْ شِمَالِي نُورًا، وَمِنْ فَوْقِي نُورًا، وَمِنْ تَحْتِي نُورًا، وَأَعْظِمْ لِي نُورًا",
        "arapca_okunus": "Allâhümmec'al fî kalbî nûrâ, ve fî basarî nûrâ, ve fî sem'î nûrâ, ve 'an yemînî nûrâ, ve 'an şimâlî nûrâ, ve min fevkî nûrâ, ve min tahtî nûrâ, ve a'zım lî nûrâ",
        "turkce_anlam": "Allah'ım! Kalbime bir nur, gözüme bir nur, kulağıma bir nur koy. **Sağıma nur, soluma nur, üstüme nur, altıma nur eyle** ve nurumu artır.",
        "kaynak_ref": "Buhârî, Deavât, 9; Müslim, Müsâfirîn, 181",
        "fazilet_notu": "Gece karanlığında kalkıp teheccüde duran kalplere ilahi basiret, idrak ve içsel aydınlık bağışlayan kutlu münacattır."
    },
    {
        "id": 119,
        "dua_basligi": "Hacet ve Darlık Halinde Rabbe İltica",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Çaresizlik, Hacet ve Çözümsüzlük Anı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "لَا إِلَهَ إِلَّا اللَّهُ الْحَلِيمُ الْكَرِيمُ، سُبْحَانَ اللَّهِ رَبِّ الْعَرْشِ الْعَظِيمِ، الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ، أَسْأَلُكَ مُوجِبَاتِ رَحْمَتِكَ وَعَزَائِمَ مَغْفِرَتِكَ",
        "arapca_okunus": "Lâ ilâhe illallâhul halîmül kerîm, sübhânallâhi rabbil 'arşil 'azîm, elhamdü lillâhi rabbil 'âlemîn, es'elüke mûcibâti rahmetike ve 'azâime mağfiratik",
        "turkce_anlam": "Halîm ve Kerîm olan Allah'tan başka ilah yoktur. Yüce arşın Rabbi olan Allah noksanlıklardan uzaktır. **Rahmetini celbeden amelleri ve mağfiretini dilerim.**",
        "kaynak_ref": "Tirmizî, Vitir, 17; İbn Mâce, İkâme, 189",
        "fazilet_notu": "Gönlünde çözülmesi gereken bir hacet veya zorluk bulunan kimsenin abdest alıp iki rekat namaz sonrası okuyacağı hacet niyazıdır."
    },
    {
        "id": 120,
        "dua_basligi": "Şükür Secdesi ve Nimet İtirafı (Hz. Süleyman)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Büyük İhsan, Zenginlik ve Şükür Coşkusu",
        "kimin_duasi": "Hz. Süleyman (a.s.)",
        "arapca_metin": "رَبِّ أَوْزِعْنِي أَنْ أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَى وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ وَأَدْخِلْنِي بِرَحْمَتِكَ فِي عِبَادِكَ الصَّالِحِينَ",
        "arapca_okunus": "Rabbi evzı'nî en eşküra ni'metekelletî en'amte 'aleyye ve 'alâ vâlideyye ve en a'mele sâlihan terdâhü ve edhılnî bi-rahmetike fî 'ıbâdikes-sâlihîn",
        "turkce_anlam": "Rabbim! Bana ve ana babama lütfettiğin nimete şükretmemi ve **razı olacağın salih amel işlememi bana ilham eyle.** Rahmetinle beni salih kullarının arasına kat.",
        "kaynak_ref": "Neml Sûresi, 19. Âyet",
        "fazilet_notu": "Kişiye verilen ilahi nimeti şımarmadan, nankörlük etmeden bilakis daha derin bir tevazu ve ihlasla karşılamayı öğreten kur'ani adap."
    },
    {
        "id": 121,
        "dua_basligi": "Hata ve Kusur Sonrası Af Talebi (Hz. Âdem ve Havva)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Pişmanlık, Hüzün ve Mahcubiyet Hali",
        "kimin_duasi": "Hz. Âdem (a.s.) ve Hz. Havva",
        "arapca_metin": "رَبَّنَا ظَلَمْنَا أَنْفُسَنَا وَإِنْ لَمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ",
        "arapca_okunus": "Rabbenâ zalemnâ enfüsenâ ve in lem tağfir lenâ ve terhamnâ le-nekûnenne minel hâsirîn",
        "turkce_anlam": "Rabbimiz! **Biz kendimize zulmettik.** Eğer bizi bağışlamaz ve bize merhamet etmezsen elbette hüsrana uğrayanlardan oluruz.",
        "kaynak_ref": "A'râf Sûresi, 23. Âyet",
        "fazilet_notu": "İnsanlığın atası Hz. Âdem'in affına vesile olan, şeytanın kibrine inat insanın aczini ve tevbesini sembolleştiren ebedi niyazdır."
    },
    {
        "id": 122,
        "dua_basligi": "Hayırlı ve Bereketli Bir Menzil Talebi (Hz. Nûh)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Yeni Başlangıçlar ve Emniyet Arayışı",
        "kimin_duasi": "Hz. Nûh (a.s.)",
        "arapca_metin": "رَبِّ أَنْزِلْنِي مُنْزَلًا مُبَارَكًا وَأَنْتَ خَيْرُ الْمُنْزِلِينَ",
        "arapca_okunus": "Rabbi enzilnî münzelen mübâraken ve ente hayrul münzilîn",
        "turkce_anlam": "Rabbim! **Beni bereketli bir yere indir;** çünkü Sen ikram edenlerin ve barındıranların en hayırlısısın.",
        "kaynak_ref": "Mü'minûn Sûresi, 29. Âyet",
        "fazilet_notu": "Yeni bir eve taşınırken, bir şehre varıldığında veya yeni bir işe adım atıldığında bereket ve selamet getirmesi için okunur."
    },
    {
        "id": 123,
        "dua_basligi": "Bozgunculara Karşı Yardım ve Zafer Niyazı (Hz. Lût)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Toplumsal Bozulma ve Fitne Baskısı",
        "kimin_duasi": "Hz. Lût (a.s.)",
        "arapca_metin": "رَبِّ انْصُرْنِي عَلَى الْقَوْمِ الْمُفْسِدِينَ",
        "arapca_okunus": "Rabbin-surnî 'alel kavmil müfsidîn",
        "turkce_anlam": "Rabbim! **Bozguncu ve ifsat edici topluluğa karşı bana yardım eyle.**",
        "kaynak_ref": "Ankebût Sûresi, 30. Âyet",
        "fazilet_notu": "Kötülüğün, yozlaşmanın ve ahlaksızlığın yaygınlaştığı cemiyetlerde müminin istikametini koruyabilmesi için yaptığı güçlü iltica."
    },
    {
        "id": 124,
        "dua_basligi": "Hak İle Hüküm ve Adalet Talebi (Hz. Şuayb)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Haksızlık, İftira ve Anlaşmazlık Hali",
        "kimin_duasi": "Hz. Şuayb (a.s.)",
        "arapca_metin": "رَبَّنَا افْتَحْ بَيْنَنَا وَبَيْنَ قَوْمِنَا بِالْحَقِّ وَأَنْتَ خَيْرُ الْفَاتِحِينَ",
        "arapca_okunus": "Rabbenafteh beynenâ ve beyne kavminâ bil hakkı ve ente hayrul fâtihîn",
        "turkce_anlam": "Rabbimiz! Bizimle kavmimiz arasında **hak ile hükmet ve gerçeği ortaya çıkar;** çünkü Sen hüküm verenlerin en hayırlısısın.",
        "kaynak_ref": "A'râf Sûresi, 89. Âyet",
        "fazilet_notu": "İki taraf arasında anlaşmazlık çıktığında veya haksız ithamlara maruz kalındığında hakkın tecelli etmesi için okunur."
    },
    {
        "id": 125,
        "dua_basligi": "İhtiyarlık ve Zayıflık Anında Rahmet Niyazı (Hz. Zekeriyyâ)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Güçsüzlük, Yalnızlık ve Ümit Kapısı",
        "kimin_duasi": "Hz. Zekeriyyâ (a.s.)",
        "arapca_metin": "رَبِّ إِنِّي وَهَنَ الْعَظْمُ مِنِّي وَاشْتَعَلَ الرَّأْسُ شَيْبًا وَلَمْ أَكُنْ بِدُعَائِكَ رَبِّ شَقِيًّا",
        "arapca_okunus": "Rabbi innî vehenel 'azmü minnî veşte'aler-ra'sü şeyben ve lem ekün bi-du'âike rabbi şekıyyâ",
        "turkce_anlam": "Rabbim! Doğrusu kemiklerim zayıfladı, saçım ağardı. **Rabbim, Sana ettiğim hiçbir duada mahrum ve ümitsiz kalmadım.**",
        "kaynak_ref": "Meryem Sûresi, 4. Âyet",
        "fazilet_notu": "Tıbben veya maddeten imkansız gibi görünen durumlarda dahi Allah'ın sonsuz kudret ve merhametine duyulan sarsılmaz hüsn-i zan."
    },
    {
        "id": 126,
        "dua_basligi": "Ashâb-ı Kehf’in Mağaradaki Rüşd ve Rahmet Duası",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Baskı, Çıkmaz ve Sığınacak Yer Arayışı",
        "kimin_duasi": "Ashâb-ı Kehf (Mağara Gençleri)",
        "arapca_metin": "رَبَّنَا آتِنَا مِنْ لَدُنْكَ رَحْمَةً وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا",
        "arapca_okunus": "Rabbenâ âtinâ min ledünke rahmeten ve heyyi' lenâ min emrinâ raşedâ",
        "turkce_anlam": "Rabbimiz! Bize katından bir rahmet ver ve **işimizde bizim için doğru ve hayırlı bir çıkış yolu hazırla.**",
        "kaynak_ref": "Kehf Sûresi, 10. Âyet",
        "fazilet_notu": "Büyük kriz, imtihan ve belirsizlik anlarında feraset ve ilahi yardım bulmak için okunacak en tesirli ayetlerdendir."
    },
    {
        "id": 127,
        "dua_basligi": "Sabır, Sebat ve Zafer Niyazı (Tâlût ve Ordusu)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Zorlu Mücadele ve Güçlü Düşman Karşısı",
        "kimin_duasi": "Tâlût'un Mümin Askerleri",
        "arapca_metin": "رَبَّنَا أَفْرِغْ عَلَيْنَا صَبْرًا وَثَبِّتْ أَقْدَامَنَا وَانْصُرْنَا عَلَى الْقَوْمِ الْكَافِرِينَ",
        "arapca_okunus": "Rabbenâ efriğ 'aleynâ sabran ve sebbit ekdâmenâ vansurnâ 'alel kavmil kâfirîn",
        "turkce_anlam": "Rabbimiz! **Üzerimize sabır yağdır, ayaklarımızı sabit kıl** ve inkarcı topluluğa karşı bize yardım eyle.",
        "kaynak_ref": "Bakara Sûresi, 250. Âyet",
        "fazilet_notu": "Câlût gibi azametli zorluklarla karşılaşan azınlıktaki samimi müminlerin sarsılmaz bir sabır kuşanarak zafere erdiği mübarek dua."
    },
    {
        "id": 128,
        "dua_basligi": "İman Üzere Vefat ve Sabır Niyazı (Firavun’un Sihirbazları)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Büyük İmtihan ve Son Nefeste İman Endişesi",
        "kimin_duasi": "İman Eden Sihirbazlar",
        "arapca_metin": "رَبَّنَا أَفْرِغْ عَلَيْنَا صَبْرًا وَتَوَفَّنَا مُسْلِمِينَ",
        "arapca_okunus": "Rabbenâ efriğ 'aleynâ sabran ve teveffenâ müslimîn",
        "turkce_anlam": "Rabbimiz! **Üzerimize sabır yağdır ve canımızı Müslümanlar olarak al.**",
        "kaynak_ref": "A'râf Sûresi, 126. Âyet",
        "fazilet_notu": "Hakikati gördükten sonra hiçbir tehdide boyun eğmeyenlerin son nefeslerini tevhid üzere tamamlama yakarışıdır."
    },
    {
        "id": 129,
        "dua_basligi": "Şahitlerle Beraber Yazılma Duası (Havârîler)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "İman Coşkusu ve Hakka Bağlılık",
        "kimin_duasi": "Hz. Îsâ'nın Havârîleri",
        "arapca_metin": "رَبَّنَا آمَنَّا بِمَا أَنْزَلْتَ وَاتَّبَعْنَا الرَّسُولَ فَاكْتُبْنَا مَعَ الشَّاهِدِينَ",
        "arapca_okunus": "Rabbenâ âmennâ bi-mâ enzelte vetteba'ner-rasûle fektübnâ ma'aş-şâhidîn",
        "turkce_anlam": "Rabbimiz! İndirdiğine inandık ve Peygamber'e uyduk; **artık bizi hakka şahitlik edenlerle beraber yaz.**",
        "kaynak_ref": "Âl-i İmrân Sûresi, 53. Âyet",
        "fazilet_notu": "Vahye ve Peygamber'in sünnetine sadakatle bağlananların kıyamet günü sıddîklerle haşrolunma niyazıdır."
    },
    {
        "id": 130,
        "dua_basligi": "Gafletten Uyanış ve Mağfiret Niyazı",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Hata ve Kusurları İtiraf Hali",
        "kimin_duasi": "Müminler",
        "arapca_metin": "رَبَّنَا آمَنَّا فَاغْفِرْ لَنَا وَارْحَمْنَا وَأَنْتَ خَيْرُ الرَّاحِمِينَ",
        "arapca_okunus": "Rabbenâ âmennâ fağfir lenâ verhamnâ ve ente hayrur-râhimîn",
        "turkce_anlam": "Rabbimiz! **Biz iman ettik; öyleyse bizi bağışla ve bize merhamet eyle;** zira Sen merhamet edenlerin en hayırlısısın.",
        "kaynak_ref": "Mü'minûn Sûresi, 109. Âyet",
        "fazilet_notu": "İlahi rahmete sığınarak günahların affını ve kalbin arınmasını talep eden samimi bir mümin yakarışıdır."
    },
    {
        "id": 131,
        "dua_basligi": "Cehennem Azabından Korunma Talebi (İbâdü’r-Rahmân)",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Ahiret Korkusu ve Ebedi Kurtuluş",
        "kimin_duasi": "Rahmân'ın Has Kullarından",
        "arapca_metin": "رَبَّنَا اصْرِفْ عَنَّا عَذَابَ جَهَنَّمَ إِنَّ عَذَابَهَا كَانَ غَرَامًا",
        "arapca_okunus": "Rabbenasrif 'annâ 'azâbe cehenneme inne 'azâbehâ kâne ğarâmâ",
        "turkce_anlam": "Rabbimiz! **Cehennem azabını bizden uzaklaştır;** çünkü onun azabı gerçekten helak edicidir.",
        "kaynak_ref": "Furkân Sûresi, 65. Âyet",
        "fazilet_notu": "Rahmân'ın övgüsüne mazhar olan gerçek müminlerin geceleri secdeye kapanıp ahiret için ettikleri titrek yakarış."
    },
    {
        "id": 132,
        "dua_basligi": "Mümin Kardeşlerine Karşı Kalpte Kin Kalmama Niyazı",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Gönül Saflığı ve Kardeşlik Sevgisi",
        "kimin_duasi": "Muhacir ve Ensar'a Tabi Olan Müminler",
        "arapca_metin": "رَبَّنَا اغْفِرْ لَنَا وَلِإِخْوَانِنَا الَّذِينَ سَبَقُونَا بِالْإِيمَانِ وَلَا تَجْعَلْ فِي قُلُوبِنَا غِلًّا لِلَّذِينَ آمَنُوا رَبَّنَا إِنَّكَ رَءُوفٌ رَحِيمٌ",
        "arapca_okunus": "Rabbenâğfir lenâ ve li-ihvâninellezîne sebekûnâ bil îmâni ve lâ tec'al fî kulûbinâ ğıllen lillezîne âmenû rabbenâ inneke ra'ûfün rahîm",
        "turkce_anlam": "Rabbimiz! Bizi ve bizden önce iman etmiş kardeşlerimizi bağışla. **İman edenlere karşı kalplerimizde hiçbir kin bırakma.** Rabbimiz! Şüphesiz Sen çok şefkatli ve çok merhametlisin.",
        "kaynak_ref": "Haşr Sûresi, 10. Âyet",
        "fazilet_notu": "Müslümanın kalbini kardeşine karşı haset, kin ve düşmanlıktan arındıran eşsiz bir uhuvvet duasıdır."
    },
    {
        "id": 133,
        "dua_basligi": "Nurun Tamamlanması ve Kusurların Örtülmesi Duası",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Mahşer Günü Işığı ve Mağfiret",
        "kimin_duasi": "Salih Müminler",
        "arapca_metin": "رَبَّنَا أَتْمِمْ لَنَا نُورَنَا وَاغْفِرْ لَنَا إِنَّكَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ",
        "arapca_okunus": "Rabbenâ etmim lenâ nûranâ vağfir lenâ inneke 'alâ külli şey'in kadîr",
        "turkce_anlam": "Rabbimiz! **Nurumuzu tamamla ve bizi bağışla;** şüphesiz Sen her şeye hakkıyla kadirsin.",
        "kaynak_ref": "Tahrîm Sûresi, 8. Âyet",
        "fazilet_notu": "Sırat köprüsünde münafıkların ışığı sönerken, müminlerin nurunun önlerini ve sağlarını aydınlatması için yaptıkları niyaz."
    },
    {
        "id": 134,
        "dua_basligi": "Ezan Sonrası Vesile ve Şefaat Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Namaza Hazırlık ve Nebevi Muhabbet",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ الْقَائِمَةِ، آتِ مُحَمَّدًا الْوَسِيلَةَ وَالْفَضِيلَةَ، وَابْعَثْهُ مَقَامًا مَحْمُودًا الَّذِي وَعَدْتَهُ",
        "arapca_okunus": "Allâhümme rabbe hâzihid-da'vetit-tâmmeh, ves-salâtil kâimeh, âti muhammedenil vesîlete vel fadîleh, veb'ashü makâmen mahmûdenillezî va'adteh",
        "turkce_anlam": "Ey bu eksiksiz davetin ve kılınacak namazın Rabbi olan Allah'ım! **Muhammed'e vesileyi ve fazileti lütfet.** Onu vadettiğin Makâm-ı Mahmûd'a ulaştır.",
        "kaynak_ref": "Buhârî, Ezân, 8; Ebû Dâvûd, Salât, 38",
        "fazilet_notu": "Ezanı dinleyip bu duayı okuyan kimseye kıyamet gününde Resûlullah'ın şefaatinin vacip olacağı müjdelenmiştir."
    },
    {
        "id": 135,
        "dua_basligi": "Abdest Sonrası Manevi Arınma ve Tevbe Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Maddi ve Manevi Temizlik Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُولُهُ، اللَّهُمَّ اجْعَلْنِي مِنَ التَّوَّابِينَ، وَاجْعَلْنِي مِنَ الْمُتَطَهِّرِينَ",
        "arapca_okunus": "Eşhedü el lâ ilâhe illallâhü vahdehû lâ şerîke leh, ve eşhedü enne muhammeden 'abdühû ve rasûlüh, Allâhümmec'alnî minet-tevvâbîn, vec'alnî minel mütetahhirîn",
        "turkce_anlam": "Şehadet ederim ki Allah'tan başka ilah yoktur; O tektir, ortağı yoktur. Muhammed O'nun kulu ve elçisidir. **Allah'ım! Beni çokça tevbe edenlerden ve tertemiz olanlardan eyle.**",
        "kaynak_ref": "Müslim, Tahâret, 17; Tirmizî, Tahâret, 41",
        "fazilet_notu": "Abdesti güzelce alıp bu zikri okuyana cennetin sekiz kapısının açılacağı ve dilediğinden girebileceği bildirilmiştir."
    },
    {
        "id": 136,
        "dua_basligi": "Mescide Girerken Rahmet Kapılarının Açılması Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Mescide Adım Atarken Huşû Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "بِسْمِ اللَّهِ، وَالصَّلَاةُ وَالسَّلَامُ عَلَى رَسُولِ اللَّهِ، اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ",
        "arapca_okunus": "Bismillâhi, ves-salâtü ves-selâmü 'alâ rasûlillâh, Allâhümmafteh lî ebvâbe rahmetik",
        "turkce_anlam": "Allah'ın adıyla. Salât ve selam Allah'ın Resûlü'nün üzerine olsun. **Allah'ım! Bana rahmetinin kapılarını aç.**",
        "kaynak_ref": "Müslim, Müsâfirîn, 68; Ebû Dâvûd, Salât, 18",
        "fazilet_notu": "Allah'ın evi olan mescide girerken sağ ayakla girilip okunması müstehap olan kutlu nebevi edep zikridir."
    },
    {
        "id": 137,
        "dua_basligi": "Mescitten Çıkarken Lütuf ve İhsan Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Namaz Sonrası Hayata Dönüş",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "بِسْمِ اللَّهِ، وَالصَّلَاةُ وَالسَّلَامُ عَلَى رَسُولِ اللَّهِ، اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ",
        "arapca_okunus": "Bismillâhi, ves-salâtü ves-selâmü 'alâ rasûlillâh, Allâhümme innî es'elüke min fadlik",
        "turkce_anlam": "Allah'ın adıyla. Salât ve selam Allah'ın Resûlü'nün üzerine olsun. **Allah'ım! Şüphesiz ben Senin sonsuz lütfundan dilerim.**",
        "kaynak_ref": "Müslim, Müsâfirîn, 68; Ebû Dâvûd, Salât, 18",
        "fazilet_notu": "İbadet sonrası dünya meşgalesine ve rızık aramaya dönerken sol ayakla çıkıp Allah'ın fazlına iltica etmektir."
    },
    {
        "id": 138,
        "dua_basligi": "Yemek Sonrası Nimet ve İhsan Şükrü",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Sofra Bereketi ve Doyma Hissiyatı",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مُسْلِمِينَ",
        "arapca_okunus": "Elhamdü lillâhillezî et'amenâ ve sekânâ ve ce'alenâ müslimîn",
        "turkce_anlam": "**Bizi doyuran, bizi sulayan** ve bizi Müslümanlardan kılan Allah'a hamdolsun.",
        "kaynak_ref": "Ebû Dâvûd, Et'ime, 52; Tirmizî, Deavât, 55",
        "fazilet_notu": "Sofranın rızkını veren Rezzâk olan Rabbimize şükretmeyi ve nimetin kıymetini idrak etmeyi sağlayan sünnettir."
    },
    {
        "id": 139,
        "dua_basligi": "Yeni Bir Elbise Giyerken Bereket Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Yeni Nimet Sevinci ve Şükür",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "الْحَمْدُ لِلَّهِ الَّذِي كَسَانِي هَذَا الثَّوْبَ وَرَزَقَنِيهِ مِنْ غَيْرِ حَوْلٍ مِنِّي وَلَا قُوَّةٍ",
        "arapca_okunus": "Elhamdü lillâhillezî kesânî hâzes-sevbe ve rezakanîhi min ğayri havlin minnî ve lâ kuvveh",
        "turkce_anlam": "Benim bir gücüm ve kuvvetim olmaksızın **bu elbiseyi bana giydiren ve beni rızıklandıran Allah'a hamdolsun.**",
        "kaynak_ref": "Ebû Dâvûd, Libâs, 1; Tirmizî, Deavât, 107",
        "fazilet_notu": "Yeni elbise giyerken bu duayı okuyan kimsenin geçmiş günahlarının bağışlanacağı müjdelenmiştir."
    },
    {
        "id": 140,
        "dua_basligi": "Vasıtaya ve Bineğe Binerken Yol Emniyeti Duası",
        "kategori": "Kur'an-ı Kerim",
        "ruh_hali": "Seyahat, Yolculuk ve Hareket Hali",
        "kimin_duasi": "Salih Yolcular",
        "arapca_metin": "سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ، وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ",
        "arapca_okunus": "Sübhânellezî sahhara lenâ hâzâ ve mâ künnâ lehû mukrinîn, ve innâ ilâ rabbinâ le-münkalibûn",
        "turkce_anlam": "**Bunu bizim hizmetimize boyun eğdiren Allah noksanlıklardan uzaktır;** yoksa bizim buna gücümüz yetmezdi. Şüphesiz biz Rabbimize döneceğiz.",
        "kaynak_ref": "Zuhruf Sûresi, 13-14. Âyetler; Müslim, Hac, 425",
        "fazilet_notu": "Her türlü taşıta binerken yolculuğun emniyetle geçmesi ve insanın fani bir yolcu olduğunu unutmaması için okunur."
    },
    {
        "id": 141,
        "dua_basligi": "Yolculuktan Dönerken Tevbe ve Hamd Zikri",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Sılaya Kavuşma ve Selamet Sevinci",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "آيِبُونَ تَائِبُونَ عَابِدُونَ لِرَبِّنَا حَامِدُونَ",
        "arapca_okunus": "Âyibûne tâibûne 'âbidûne li-rabbinâ hâmidûn",
        "turkce_anlam": "**Dönenler, tevbe edenler, kullukta bulunanlar** ve yalnız Rabbimize hamd edenleriz.",
        "kaynak_ref": "Buhârî, Cihâd, 197; Müslim, Hac, 428",
        "fazilet_notu": "Peygamberimiz seferden memleketine yaklaştığında tepe veya düzlüğe her çıkışında bu zikri üç kez tekrar ederdi."
    },
    {
        "id": 142,
        "dua_basligi": "Yağmur Yağarken Bereket ve Menfaat Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Rahmet İnişi ve Tabiat Tefekkürü",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ صَيِّبًا نَافِعًا، مُطِرْنَا بِفَضْلِ اللَّهِ وَرَحْمَتِهِ",
        "arapca_okunus": "Allâhümme sayyiben nâfi'â, mutırnâ bi-fadlillâhi ve rahmetih",
        "turkce_anlam": "Allah'ım! **Bunu yararlı ve bereketli bir yağmur eyle.** Allah'ın lütfu ve rahmetiyle yağmura kavuştuk.",
        "kaynak_ref": "Buhârî, İstiskâ, 14, 24",
        "fazilet_notu": "Yağmurun afet değil hayır getirmesi ve yağmur anında duaların icabet bulması inancıyla okunan kutlu sünnettir."
    },
    {
        "id": 143,
        "dua_basligi": "Fırtına ve Şiddetli Rüzgarda Hayır Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Doğal Afet Korkusu ve Emniyet",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَهَا، وَخَيْرَ مَا فِيهَا، وَخَيْرَ مَا أُرْسِلَتْ بِهِ، وَأَعُوذُ بِكَ مِنْ شَرِّهَا، وَشَرِّ مَا فِيهَا، وَشَرِّ مَا أُرْسِلَتْ بِهِ",
        "arapca_okunus": "Allâhümme innî es'elüke hayrahâ, ve hayra mâ fîhâ, ve hayra mâ ürsilet bih, ve e'ûzü bike min şerrihâ, ve şerri mâ fîhâ, ve şerri mâ ürsilet bih",
        "turkce_anlam": "Allah'ım! Bu rüzgarın hayrını, **içindekilerin hayrını ve gönderiliş gayesinin hayrını dilerim.** Şerrinden de Sana sığınırım.",
        "kaynak_ref": "Müslim, İstiskâ, 15; Ebû Dâvûd, Edeb, 104",
        "fazilet_notu": "Şiddetli rüzgar veya fırtına koptuğunda tabiatın sahibi olan Allah'a yönelip felaketlerden himaye istemektir."
    },
    {
        "id": 144,
        "dua_basligi": "Hilali Görünce Emniyet ve Selamet Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Yeni Ay Girişi ve Zaman Şuuru",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "اللَّهُمَّ أَهِلَّهُ عَلَيْنَا بِالْأَمْنِ وَالْإِيمَانِ، وَالسَّلَامَةِ وَالْإِسْلَامِ، رَبِّي وَرَبُّكَ اللَّهُ، هِلَالُ رُشْدٍ وَخَيْرٍ",
        "arapca_okunus": "Allâhümme ehillehû 'aleynâ bil emni vel îmân, ves-selâmeti vel islâm, rabbî ve rabbükallâh, hilâlü rüşdin ve hayr",
        "turkce_anlam": "Allah'ım! **Bu hilali bize emniyet, iman, selamet ve İslam ile doğdur.** Ey hilal! Benim Rabbim de senin Rabbin de Allah'tır. Hayır ve hidayet hilali olsun.",
        "kaynak_ref": "Tirmizî, Deavât, 51; Dârimî, Savm, 3",
        "fazilet_notu": "Yeni bir kameri aya girerken bereket, huzur ve hayırlı başlangıçlar temenni etmek için okunur."
    },
    {
        "id": 145,
        "dua_basligi": "İftar Vaktinde Susuzluğun Gitmesi ve Ecir Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Oruç Açma Sevinci ve Şükür Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "ذَهَبَ الظَّمَأُ، وَابْتَلَّتِ الْعُرُوقُ، وَثَبَتَ الْأَجْرُ إِنْ شَاءَ اللَّهُ",
        "arapca_okunus": "Zehebez-zame'u, vebtelletil 'urûk, ve seb兴tel ecru in şâallâh",
        "turkce_anlam": "**Susuzluk gitti, damarlar ıslandı** ve inşallah mükafat sabit oldu.",
        "kaynak_ref": "Ebû Dâvûd, Savm, 22",
        "fazilet_notu": "İftar sofrasında ilk lokma veya su yudumlandıktan sonra bizzat Resûl-i Ekrem'in dilinden dökülen şükran sözleridir."
    },
    {
        "id": 146,
        "dua_basligi": "Hasta Ziyaretinde Şifa ve Afiyet Niyazı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Hastalık, Şefkat ve Şifa Dileği",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "أَسْأَلُ اللَّهَ الْعَظِيمَ رَبَّ الْعَرْشِ الْعَظِيمِ أَنْ يَشْفِيَكَ",
        "arapca_okunus": "Es'elüllâhel 'azîme rabbal 'arşil 'azîmi en yeşfiyek",
        "turkce_anlam": "**Yüce arşın Rabbi olan ulu Allah'tan** sana şifa vermesini dilerim.",
        "kaynak_ref": "Ebû Dâvûd, Cenâiz, 8; Tirmizî, Tıbb, 32",
        "fazilet_notu": "Eceli gelmemiş bir hastanın yanında yedi defa bu dua okunduğunda Allah'ın o hastaya şifa bahşedeceği bildirilmiştir."
    },
    {
        "id": 147,
        "dua_basligi": "Kabir Ziyaretinde Ahiret Selamı ve Rahmet Talebi",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Kabir Ziyareti, Ölüm Tefekkürü ve Dua",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "السَّلَامُ عَلَيْكُمْ أَهْلَ الدِّيَارِ مِنَ الْمُؤْمِنِينَ وَالْمُسْلِمِينَ، وَإِنَّا إِنْ شَاءَ اللَّهُ بِكُمْ لَاحِقُونَ، نَسْأَلُ اللَّهَ لَنَا وَلَكُمُ الْعَافِيَةَ",
        "arapca_okunus": "Es-selâmü 'aleyküm ehled-diyâri minel mü'minîne vel müslimîn, ve innâ in şâallâhü biküm lâhikûn, nes'elüllâhe lenâ ve lekümül 'âfiyeh",
        "turkce_anlam": "Selam size ey bu diyarın mümin ve müslüman ahalisi! **İnşallah biz de sizlere katılacağız.** Allah'tan bize ve size afiyet dileriz.",
        "kaynak_ref": "Müslim, Cenâiz, 102; İbn Mâce, Cenâiz, 36",
        "fazilet_notu": "Kabristana girildiğinde geçmişlerin ruhuna selam gönderip ölüm hakikatini kalbe nakşeden sünnettir."
    },
    {
        "id": 148,
        "dua_basligi": "Meclisten Kalkarken Hatalara Keffâret Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Sohbet Sonu ve Kusurlardan Arınma",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ، أَشْهَدُ أَنْ لَا إِلَهَ إِلَّا أَنْتَ، أَسْتَغْفِرُكَ وَأَتُوبُ إِلَيْكَ",
        "arapca_okunus": "Sübhânekallâhümme ve bi-hamdike, eşhedü el lâ ilâhe illâ ente, estağfiruke ve etûbü ileyk",
        "turkce_anlam": "Allah'ım! Seni hamdinle tesbih ederim. **Senden başka ilah olmadığına şehadet ederim.** Senden bağışlanma diler ve Sana tevbe ederim.",
        "kaynak_ref": "Tirmizî, Deavât, 39; Ebû Dâvûd, Edeb, 27",
        "fazilet_notu": "Bir meclis veya toplantıdan kalkarken bu duayı okuyan kimsenin o meclisteki sehven işlenen kusurlarının bağışlanacağı müjdelenmiştir."
    },
    {
        "id": 149,
        "dua_basligi": "Korkulu Rüya Gören Kimsenin Okuyacağı Sığınma Duası",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Kötü Rüya, Ürkme ve Uyanış Hali",
        "kimin_duasi": "Hz. Muhammed (s.a.v.)",
        "arapca_metin": "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّةِ مِنْ كُلِّ شَيْطَانٍ وَهَامَّةٍ وَمِنْ كُلِّ عَيْنٍ لَامَّةٍ",
        "arapca_okunus": "E'ûzü bi-kelimâtillâhit-tâmmeti min külli şeytânin ve hâmmeh, ve min külli 'aynin lâmmeh",
        "turkce_anlam": "**Her türlü şeytandan, zehirli zararlı hayvandan** ve kem gözlerden Allah'ın eksiksiz kelimelerine sığınırım.",
        "kaynak_ref": "Buhârî, Ehâdîsü'l-Enbiyâ, 10; Tirmizî, Tıbb, 14",
        "fazilet_notu": "Hz. İbrâhîm'in oğulları İsmâîl ve İshâk için yaptığı, Resûlullah'ın da torunları Hasan ve Hüseyin'i korumak için okuduğu ilahi kalkandır."
    },
    {
        "id": 150,
        "dua_basligi": "Hayy ve Kayyûm Olan Allah’a İltica ve Halin Islahı",
        "kategori": "Hadis-i Şerif",
        "ruh_hali": "Göz Açıp Kapayıncaya Kadar Bile Yalnız Kalmama",
        "kimin_duasi": "Hz. Fâtıma (r.a.) / Hz. Peygamber (s.a.v.)",
        "arapca_metin": "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ، أَصْلِحْ لِي شَأْنِي كُلَّهُ، وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
        "arapca_okunus": "Yâ hayyu yâ kayyûmü bi-rahmetike esteğîs, aslih lî şe'nî külleh, ve lâ tekilnî ilâ nefsî tarfete 'ayn",
        "turkce_anlam": "Ey daima diri olan Hayy ve her şeyi ayakta tutan Kayyûm! Rahmetinle yardımını dilerim. **Bütün işlerimi düzelt ve beni göz açıp kapayıncaya kadar bile nefsime bırakma.**",
        "kaynak_ref": "Hâkim, el-Müstedrek, 1/545; Nesâî, es-Sünenü'l-Kübrâ, 10330",
        "fazilet_notu": "Peygamber Efendimiz'in kızı Hz. Fâtıma'ya sabah ve akşam vakitlerinde hiç bırakmadan okumasını tavsiye ettiği en derin teslimiyet duasıdır."
    }
]

# 50 Yeni Kur'an Kavramı (201 - 250)
YENI_KAVRAMLAR_TUPLES = [
    # (id, tr, ar, okunus, kok, lugat, kuran_boyut, hayat_dersi, sure_no, ayet_no)
    (
        201, "Üsve-i Hasene", "الأُسْوَةُ الحَسَنَةُ", "el-Üsvetü'l-Hasene", "E-S-V (Örnek Almak)",
        "Her çağ ve şartta izinden gidilecek **en güzel, en kamil ve kusursuz ahlak örneği**.",
        "“Andolsun ki Resûlullah sizin için, Allah'a ve ahiret gününe kavuşmayı umanlar için en güzel örnektir.” (Ahzâb, 21)",
        "İyilik ve erdem arayışında yönünü kaybetmemek için pusulayı Resûlullah'ın şefkat, adalet ve vakarına çevir.",
        33, 21
    ),
    (
        202, "Safh-ı Cemîl", "الصَّفْحُ الجَمِيلُ", "es-Safhu'l-Cemîl", "S-F-H (Yüz Çevirmek, Affetmek)",
        "İçinde sitem, başa kakma ve kin barındırmayan **asil, tertemiz ve gönülden bağışlama**.",
        "“Artık sen onlara karşı yumuşak davran ve asil bir bağışlama ile muamele et.” (Hicr, 85)",
        "Affettiğin kişiye karşı içindeki intikam ateşini tamamen söndür; bağışlamanın şerefi, hatayı unutabilmektir.",
        15, 85
    ),
    (
        203, "Hecr-i Cemîl", "الهَجْرُ الجَمِيلُ", "el-Hecru'l-Cemîl", "H-C-R (Terk Etmek, Mesafe Koymak)",
        "Kırmadan, incitmeden ve münakaşaya girmeden **zarafetle mesafe koyup uzaklaşma**.",
        "“Onların söylediklerine sabret ve onlardan güzel bir ayrılışla (hecr-i cemîl) uzaklaş.” (Müzzemmil, 10)",
        "Her kabalığa karşılık vermek zorunda değilsin; bazen en asil duruş, haksız münakaşadan sükunetle uzaklaşmaktır.",
        73, 10
    ),
    (
        204, "Faslü’l-Hitâb", "فَصْلُ الخِطَابِ", "Faslü'l-Hitâb", "F-S-L (Ayırmak, Hükme Bağlamak)",
        "Hakkı batıldan ayıran, şüpheleri gideren **kesin, tesirli ve hikmetli söz söyleme yetisi**.",
        "“Biz onun mülkünü güçlendirdik; ona hikmet ve hakkı batıldan ayıran kesin hitap yeteneği verdik.” (Sâd, 20)",
        "Sözü uzatıp gereksiz yere karmaşıklaştırma; hakkı açıkça ve gönülleri ikna edecek bir zarafetle ortaya koy.",
        38, 20
    ),
    (
        205, "Sirâc-ı Münîr", "السِّرَاجُ المُنِيرُ", "es-Sirâcü'l-Münîr", "S-R-C (Işık Saçmak)",
        "Cehalet ve inkâr karanlıklarını aydınlatan **ilahi bir nur kaynağı ve hidayet kandili**.",
        "“Ve Seni Allah'ın izniyle bir davetçi ve etrafını aydınlatan bir kandil (sirâc-ı münîr) kıldık.” (Ahzâb, 46)",
        "Hayatında nur saçmak istiyorsan, karanlığa küfretmek yerine Peygamber ahlakından bir meşale tutuştur.",
        33, 46
    ),
    (
        206, "Habbetü Hardal", "حَبَّةُ خَرْدَلٍ", "Habbetü Hardal", "H-B-B / H-R-D-L (Zerre ve Tohum)",
        "Gözle zor seçilen **en küçük bir hardal tanesi kadar dahi olsa hiçbir amelin kaybolmayacağı şuuru**.",
        "“Yapılan iş bir hardal tanesi ağırlığında olsa bile onu getiririz. Hesap görücü olarak Biz yeteriz.” (Enbiyâ, 47)",
        "Küçük gördüğün hiçbir iyiliği hafife alma; bir tebessüm veya bir damla gözyaşı ebedi kurtuluşun olabilir.",
        21, 47
    ),
    (
        207, "Zıll-i Memdûd", "الظِّلُّ المَمْدُودُ", "ez-Zıllü'l-Memdûd", "Z-L-L / M-D-D (Gölge ve Uzamak)",
        "Güneşin kavurucu sıcağından uzak, **uzayıp giden serin, kesintisiz ve ebedi cennet gölgesi**.",
        "“Ve uzamış gölgeler altındadırlar.” (Vâkı'a, 30)",
        "Dünyanın geçici ve yakıcı dertlerine sabredenler, ahirette Rabbin ebedi rahmet ve sükûnet gölgesine sığınacaktır.",
        56, 30
    ),
    (
        208, "Mâ’-i Meskûb", "المَاءُ المَسْكُوبُ", "el-Mâü'l-Meskûb", "S-K-B (Çağlamak, Akmak)",
        "Hiç kesilmeksizin çağıldayan, **berrak, saf ve susuzluğu ebediyen dindiren cennet suyu**.",
        "“Ve dökülen (çağlayan) duru sular içindedirler.” (Vâkı'a, 31)",
        "Ruhunun manevi susuzluğunu dünyanın bulanık pınarlarında değil, Kur'an'ın berrak hakikat membaında gider.",
        56, 31
    ),
    (
        209, "Cennetü Me’vâ", "جَنَّةُ المَأْوَى", "Cennetü'l-Me'vâ", "E-V-Y (Sığınmak, Barınmak)",
        "Müminlerin ve şehitlerin ebedi emniyetle konaklayacağı **en huzurlu ilahi sığınak**.",
        "“Ki onun yanında sığınılacak cennet (Cennetü'l-Me'vâ) vardır.” (Necm, 15)",
        "Dünyada kalbini günahlardan koruyarak Allah'a sığınan, ahirette hiçbir korkunun olmadığı ebedi yuvaya kavuşur.",
        53, 15
    ),
    (
        210, "Sidretü’l-Müntehâ", "سِدْرَةُ المُنْتَهَى", "Sidretü'l-Müntehâ", "S-D-R / N-H-Y (Son Hudut)",
        "Yaratılmışların ilim ve idrakinin bittiği, **ilahi sırların başladığı en yüce makam**.",
        "“Sidretü'l-Müntehâ'nın yanında.” (Necm, 14)",
        "Aklın bir sınırı vardır ama imanın ve teslimiyetin ufku sonsuzdur; idrak edemediğin ilahi hikmetlere boyun eğ.",
        53, 14
    ),
    (
        211, "Burhân", "البُرْهَانُ", "el-Burhân", "B-R-H (Açık ve Kesin Olmak)",
        "Şüpheye ve tereddüde yer bırakmayan **en kuvvetli ve apaçık ilahi delil**.",
        "“Ey insanlar! Rabbinizden size kesin bir delil (burhân) geldi ve size aydınlatıcı bir nur indirdik.” (Nisâ, 174)",
        "Vesvese ve şüphe kasırgaları karşısında kalbini Kur'an'ın sarsılmaz burhanları ile tahkim et.",
        4, 174
    ),
    (
        212, "Sultân-ı Nasîr", "السُّلْطَانُ النَّصِيرُ", "es-Sultânü'n-Nasîr", "S-L-T / N-S-R (Güç ve Zafer)",
        "Zulme karşı hakkı üstün kılan **ilahi destek, galip getiren kesin güç ve nusret**.",
        "“De ki: Rabbim! Bana katından yardımcı bir güç (sultân-ı nasîr) ihsan eyle.” (İsrâ, 80)",
        "Zorluklara karşı yalnız kendi zekana veya gücüne güvenme; daima Allah'ın yardım ve kuvvetine dayan.",
        17, 80
    ),
    (
        213, "Zikr-i Hakîm", "الذِّكْرُ الحَكِيمُ", "ez-Zikrü'l-Hakîm", "Z-K-R / H-K-M (Hatırlatıcı Hikmet)",
        "Her hükmü yerli yerinde olan, **insana varoluş gayesini öğreten hikmetli Kur'an**.",
        "“İşte bu sana okuduğumuz âyetler ve hikmet dolu Zikir'dir (ez-Zikrü'l-Hakîm).” (Âl-i İmrân, 58)",
        "Gönlünü gaflet bastığında Kur'an'ın hikmetli ikazlarına kulak ver; o seni hakiki varlığına uyandırır.",
        3, 58
    ),
    (
        214, "Şefaat", "الشَّفَاعَةُ", "eş-Şefâ'a", "Ş-F-' (Eş Yapmak, Destek Olmak)",
        "Allah'ın izniyle, sevdiklerinin bağışlanması veya derecelerinin yükseltilmesi için **vesile olma**.",
        "“O gün, Rahmân'ın izin verdiği ve sözünden hoşnut olduğu kimseden başkasının şefaati fayda vermez.” (Tâhâ, 109)",
        "Şefaate layık olmak istiyorsan, dünyada şefaat sahibinin sevgisini ve sünnetini hayatında yaşat.",
        20, 109
    ),
    (
        215, "Nüzül", "النُّزُلُ", "en-Nüzül", "N-Z-L (İnmek, Misafir Etmek)",
        "Kıymetli bir misafire ikram edilen **şerefli ziyafet ve cömert ilahi ağırlama**.",
        "“İman edip salih ameller işleyenlere gelince; onlar için konak olarak Firdevs cennetleri vardır.” (Kehf, 107)",
        "Dünyada Allah'ın rızasına misafir olanın ahiretteki ev sahibi bizatihi Kerîm olan Allah'tır.",
        18, 107
    ),
    (
        216, "İhsâ", "الإِحْصَاءُ", "el-İhsâ", "H-S-Y (Saymak, Kaydetmek)",
        "İnsan unutup gitse bile **yapılan her hayrın ve şerrin zerre atlanmadan ilahi ilimle kaydedilmesi**.",
        "“Allah onların hepsini tek tek saymış (ihsâ etmiş), onlarsa bunu unutmuşlardır.” (Mücâdele, 6)",
        "İyiliklerini unutup kibirlenme, günahlarını ise hafif görüp geçme; Allah katında hiçbir an zayi olmaz.",
        58, 6
    ),
    (
        217, "Kıst", "القِسْطُ", "el-Kıst", "Q-S-T (Adil Paylaşım)",
        "Hakkı sahibine eksiksizce teslim eden **hassas, şaşmaz ve dengeli ilahi adalet**.",
        "“Eğer hüküm verirsen aralarında adaletle (kıst ile) hükmet; çünkü Allah adil olanları sever.” (Mâide, 42)",
        "En zor anlarda, hatta kendi aleyhine dahi olsa teraziyi doğrudan yana tut; hakkaniyet müminin şiarıdır.",
        5, 42
    ),
    (
        218, "İrşâd", "الإِرْشَادُ", "el-İrşâd", "R-Ş-D (Doğruyu Bulmak)",
        "Hakkı arayan bir gönle **doğru yolu göstermek, hakikate kılavuzluk etmek**.",
        "“Allah kimi saptırırsa, artık onun için doğru yolu gösterecek bir dost (veli-yi mürşid) bulamazsın.” (Kehf, 17)",
        "Bir insanın hidayetine vesile olmak, üzerine güneşin doğup battığı her şeyden daha hayırlıdır.",
        18, 17
    ),
    (
        219, "Teveccüh", "التَّوَجُّهُ", "et-Teveccüh", "V-C-H (Yönelmek)",
        "Bütün sahte ilahlardan ve fani kaygılardan arınarak **yüzünü ve kalbini yalnız Allah'a çevirme**.",
        "“Ben yüzümü tamamen gökleri ve yeri yoktan var edene çevirdim ve ben ortak koşanlardan değilim.” (En'âm, 79)",
        "Kalbinin kıblesi tek olsun; teveccühünü Allah'a kilitleyen, mahlukatın takdir ve yergisinden azat olur.",
        6, 79
    ),
    (
        220, "Tevkîr", "التَّوْقِيرُ", "et-Tevkîr", "V-Q-R (Hürmet Göstermek, Vakar)",
        "Peygamber Efendimiz'e ve ilahi mukaddesata **derin bir saygı, tazim ve hürmetle bağlanma**.",
        "“Tâ ki Allah'a ve Resûlüne iman edesiniz, O'na yardım edesiniz ve O'na hürmet gösteresiniz.” (Fetih, 9)",
        "Mukaddes değerlere hürmet kalbin takvasındandır; hürmeti olanın bereketi ve edebi tükenmez.",
        48, 9
    ),
    (
        221, "Ta’zîr", "التَّعْزِيرُ", "et-Ta'zîr", "'-Z-R (Desteklemek, Yardım Etmek)",
        "Hakkı ve hakikati ayakta tutmak için **birlik olup destek vermek, güç katmak**.",
        "“O'nu destekleyesiniz, O'na hürmet edesiniz ve sabah akşam O'nu tesbih edesiniz diye.” (Fetih, 9)",
        "İyilik tek başına kalmamalı; hayırlı işlerin ve mümin kardeşlerinin yanında daima bir destekçi ol.",
        48, 9
    ),
    (
        222, "Sebât", "الثَّبَاتُ", "es-Sebât", "S-B-T (Sarsılmamak, Kararlı Olmak)",
        "Zorluklar, fitneler ve fırtınalar karşısında **imanda ve davada sarsılmaz bir kararlılık gösterme**.",
        "“Ey iman edenler! Bir toplulukla karşılaştığınızda sebat edin ve Allah'ı çokça anın.” (Enfâl, 45)",
        "Başarı rüzgarın esişinde değil, fırtınada köklerini toprağa sımsıkı salan sebatkar duruşta saklıdır.",
        8, 45
    ),
    (
        223, "Ganiyy-i Kerîm", "الغَنِيُّ الكَرِيمُ", "el-Ganiyyü'l-Kerîm", "Ğ-N-Y / K-R-M (Zenginlik ve Kerem)",
        "Hiçbir şeye muhtaç olmayan ama **kullarına sınırsızca ihsan eden yüce zenginlik**.",
        "“Kim nankörlük ederse bilsin ki Rabbim hiçbir şeye muhtaç değildir (Ganiyy'dir), sonsuz kerem sahibidir.” (Neml, 40)",
        "Verdikleriyle gururlanma, elinden çıkanlara da dövünme; gerçek zengin olan da kerem sahibi olan da yalnız O'dur.",
        27, 40
    ),
    (
        224, "Kavl-i Adl", "القَوْلُ العَدْلُ", "el-Kavlü'l-'Adl", "Q-V-L / '-D-L (Adaletli Söz)",
        "Akraban dahi olsa, hakkı ve doğruyu söylemekten geri durmayan **tarafsız ve adil konuşma**.",
        "“Konuştuğunuz zaman, yakınınız dahi olsa adaletle konuşun ve Allah'a verdiğiniz sözü tutun.” (En'âm, 152)",
        "Sevgilinin hatırı hakkın önüne geçemez; adaletle konuş ki sözün hem dünyada hem mahşerde ağırlık kazansın.",
        6, 152
    ),
    (
        225, "Huşû-ı Kalb", "خُشُوعُ القَلْبِ", "Huşû'u'l-Kalb", "H-Ş-' (Eğilmek, Titremek)",
        "Allah'ın büyüklüğü karşısında **kalbin ürpertiyle sükûnete bürünmesi ve boyun eğmesi**.",
        "“İman edenlerin kalplerinin Allah'ın zikri ve inen hak ile ürperip yumuşama zamanı gelmedi mi?” (Hadîd, 16)",
        "Katılaşmış kalpler gaflet üretir; gönlünü Kur'an'ın zikriyle yumuşat ki oraya rahmet tohumları ekilsin.",
        57, 16
    ),
    (
        226, "Şükr-i Cezîl", "الشُّكْرُ الجَزِيلُ", "eş-Şükrü'l-Cezîl", "Ş-K-R / C-Z-L (Bol ve Gür Şükür)",
        "Nimetlerin hakiki sahibine karşı **kesintisiz, içten ve bolca sunulan minnettarlık**.",
        "“Şüphesiz Biz ona yolu gösterdik; ister şükredici olsun, isterse nankör.” (İnsân, 3)",
        "Hayat bir seçimdir; nankörlüğün darlığını değil, şükrün bereketli ve huzurlu genişliğini seç.",
        76, 3
    ),
    (
        227, "Zikr-i Kesîr", "الذِّكْرُ الكَثِيرُ", "ez-Zikrü'l-Kesîr", "Z-K-R / K-S-R (Çokça Anmak)",
        "Dili ve kalbi bir an bile boş bırakmaksızın **Allah'ı her hal ve mekanda sürekli hatırlama**.",
        "“Ey iman edenler! Allah'ı çokça anın (zikr-i kesîr ile yad edin).” (Ahzâb, 41)",
        "Günde kaç defa nefes alıyorsan o kadar hatırla; çünkü zikir, kalbin oksijeni ve ruhun hayatıdır.",
        33, 41
    ),
    (
        228, "Fakr-ı İlel-Hakk", "الفَقْرُ إِلَى اللَّهِ", "el-Fakru ilallâh", "F-Q-R (Muhtaç Olmak)",
        "Bütün mahlukatın var olmak ve yaşamak için **her an Allah'a mutlak surette muhtaç olduğu bilinci**.",
        "“Ey insanlar! Siz Allah'a muhtaçsınız; Allah ise hiçbir şeye muhtaç olmayan, her türlü övgüye layık olandır.” (Fâtır, 15)",
        "Benliğin ve gururun boş bir seraptır; aczini ve muhtaçlığını itiraf ettiğin an gerçek manevi kuvvete erersin.",
        35, 15
    ),
    (
        229, "Rıfk", "الرِّفْقُ", "er-Rıfk", "R-F-Q (Yumuşak Huyluluk)",
        "İnsan ilişkilerinde kabalıktan, sertlikten ve öfkeden uzak **şefkatli ve nezaketli muamele**.",
        "“Allah'ın rahmeti sayesindedir ki sen onlara yumuşak davrandın. Kaba ve katı yürekli olsaydın dağılıp giderlerdi.” (Âl-i İmrân, 159)",
        "Zarafet ve yumuşaklık nereye girerse orayı güzelleştirir; sertlik ise girdiği her kalbi kırar.",
        3, 159
    ),
    (
        230, "Kemâl-i Îmân", "كَمَالُ الإِيمَانِ", "Kemâlü'l-Îmân", "K-M-L (Tamamlanmak, Olgunlaşmak)",
        "Şüpheye düşmeksizin **canıyla ve malıyla Allah yolunda gayret edenlerin ulaştığı olgun iman mertebesi**.",
        "“Müminler ancak o kimselerdir ki Allah'a ve Resûlüne iman etmişler, sonra asla şüpheye düşmemişlerdir.” (Hucurât, 15)",
        "İman sadece bir söz değil, fırtınalarda sınanmış ve asla sarsılmamış bir gönül kalitesidir.",
        49, 15
    ),
    (
        231, "İ’tisâm bi-Hablillâh", "الاِعْتِصَامُ بِحَبْلِ اللَّهِ", "el-İ'tisâmu bi-Hablillâh", "'-S-M (Sarılmak, Korunmak)",
        "Ayrılığa ve tefrikaya düşmeksizin **Allah'ın ipine (Kur'an'a ve İslam'a) sımsıkı kenetlenme**.",
        "“Hep birlikte Allah'ın ipine sımsıkı sarılın ve parçalanıp bölünmeyin.” (Âl-i İmrân, 103)",
        "Tek başına kalan dal kırılır; ümmetin vahdetine sarıl ki şeytan seni yalnızlıkta avlayamasın.",
        3, 103
    ),
    (
        232, "Kitâb-ı Mübîn", "الكِتَابُ المُبِينُ", "el-Kitâbü'l-Mübîn", "K-T-B / B-Y-N (Açıklayan Kitap)",
        "Evrendeki her zerreye dair hakikatleri bildiren, **hakkı apaçık ortaya koyan ilahi ferman**.",
        "“Yerde ve gökte zerre ağırlığınca hiçbir şey Rabbinden gizli kalmaz... hepsi apaçık bir kitaptadır.” (Yûnus, 61)",
        "Kaderin sırlarını sorgulamak yerine, hayatını o kitabın nurlu ilkeleri doğrultusunda inşa etmeye bak.",
        10, 61
    ),
    (
        233, "İstiâne", "الاِسْتِعَانَةُ", "el-İsti'âne", "'-V-N (Yardım İstemek)",
        "İnsanın aczini bilip **bütün sıkıntı ve ihtiyaçlarında yalnızca Allah'tan yardım dilemesi**.",
        "“Yalnız Sana ibadet eder ve yalnız Senden yardım dileriz.” (Fâtiha, 5)",
        "Kula minnet eyleme; rızkın da devanın da sahibi yalnız O'dur. Dilenen el ancak Rabbe açılmalıdır.",
        1, 5
    ),
    (
        234, "Hamd-i Bâlig", "الحَمْدُ البَالِغُ", "el-Hamdü'l-Bâliğ", "H-M-D (Kusursuz Övgü)",
        "Varlık âlemindeki bütün kemâl ve güzelliklerin sahibi olan **âlemlerin Rabbine sunulan kamil şükür**.",
        "“Hamd, âlemlerin Rabbi olan Allah'a mahsustur.” (Fâtiha, 2)",
        "Gördüğün her güzellikte Sanatkârı hatırla; hamd, şükrün kalbi ve varoluşun en yüksek idrakidir.",
        1, 2
    ),
    (
        235, "Nefs-i Mülheme", "النَّفْسُ المُلْهَمَةُ", "en-Nefsü'l-Mülheme", "L-H-M (İlham Almak)",
        "Kötülüklerden sakınma ve **iyilikleri kavrama kabiliyeti fıtratına ilham edilmiş olan uyanık nefis**.",
        "“Nefse ve onu şekillendirip ona kötülüğünü ve sakınmasını ilham edene andolsun.” (Şems, 8)",
        "Vicdanının sesini dünyanın gürültüsüyle boğma; kalbine gelen doğru ilhamlar seni hakka çağırır.",
        91, 8
    ),
    (
        236, "Kavl-i Hak", "القَوْلُ الحَقُّ", "el-Kavlü'l-Hakk", "Q-V-L / H-Q-Q (Değişmez Gerçek)",
        "İçinde zerre şüphe veya yalan bulunmayan, **zaman ve mekandan münezzeh ilahi gerçek söz**.",
        "“Sûra üflendiği gün O'nun sözü haktır ve mülk yalnızca O'nundur.” (En'âm, 73)",
        "Yalanların ve algıların egemen olduğu dünyada, doğruluğu ilahi vahiy olan Kavl-i Hak'tan şaşma.",
        6, 73
    ),
    (
        237, "Sem’-i Hakîkî", "السَّمْعُ الحَقِيقِيُّ", "es-Sem'u'l-Hakîkî", "S-M-' (İşitmek ve İtaat)",
        "Sadece sesleri duymakla yetinmeyip **hakikati idrak ederek teslimiyetle itaat etme hali**.",
        "“Eğer biz dinlemiş veya akletmiş olsaydık, şu alevli cehennemin ehli arasında olmazdık.” (Mülk, 10)",
        "Hakkı sadece kulağınla dinleme, kalbinle de duy; hakiki işitmek, duyduğun doğrunun gereğini yapmaktır.",
        67, 10
    ),
    (
        238, "Basar-ı Nâfiz", "البَصَرُ النَّافِذُ", "el-Basaru'n-Nâfiz", "B-S-R / N-F-Z (Keskin Bakış)",
        "Dünyanın perdeleri kalktığında ahiret hakikatlerini **bütün çıplaklığıyla gören keskin görüş**.",
        "“Artık senden perdeni kaldırdık; bugün artık gözün pek keskindir.” (Kâf, 22)",
        "Gözünü sadece fani olana dikme; basiretini keskinleştir ki eşyanın arkasındaki ilahi kudreti görebilesin.",
        50, 22
    ),
    (
        239, "Cennet-i Adn", "جَنَّاتُ عَدْنٍ", "Cennâtü 'Adn", "'-D-N (Yerleşmek, İkamet Etmek)",
        "Müminlerin ebediyen kalacakları, **asla zevali ve bitişi olmayan ikamet cennetleri**.",
        "“Allah mümin erkeklere ve kadınlara altından ırmaklar akan ebedi cennetler ve Adn cennetlerinde güzel meskenler vadetti.” (Tevbe, 72)",
        "Dünya bir gurbet evidir, ahiret ise vatan; gerçek yuvan için amel işle ki Adn bahçelerine varabilesin.",
        9, 72
    ),
    (
        240, "Makâm-ı Emîn", "المَقَامُ الأَمِينُ", "el-Makâmü'l-Emîn", "E-M-N (Güvende Olmak)",
        "Her türlü korku, hüzün, hastalık ve ayrılıktan uzak **mutlak güvenlik ve esenlik makamı**.",
        "“Şüphesiz takva sahipleri güvenli bir makamdadırlar (Makâm-ı Emîn).” (Duhân, 51)",
        "Dünyadaki hiçbir sığınak kalıcı güvenlik vermez; gerçek emniyet yalnız Allah'a teslim olan kalptedir.",
        44, 51
    ),
    (
        241, "Aynü’l-Yakîn", "عَيْنُ اليَقِينِ", "Aynü'l-Yakîn", "'-Y-N / Y-Q-N (Gözle Görerek Bilmek)",
        "Şüpheleri kökünden silen, **bizzat gözle görerek ve müşahede ederek elde edilen kesin bilgi**.",
        "“Sonra onu elbette kesin bir gözle (aynü'l-yakîn olarak) göreceksiniz.” (Tekâsür, 7)",
        "Gözlerinle gördüğün dünya fanidir; imanın gözüyle ahiret hakikatlerini müşahede etmeyi öğren.",
        102, 7
    ),
    (
        242, "Hakkü’l-Yakîn", "حَقُّ اليَقِينِ", "Hakkü'l-Yakîn", "H-Q-Q / Y-Q-N (Bizzat Yaşayarak Bilmek)",
        "Bilginin en üst derecesi; hakikatin içinde eriyerek **bizzat tecrübe ile ulaşılan kesin idrak**.",
        "“Şüphesiz bu, mutlak ve kesin bir hakikattir (Hakkü'l-Yakîn).” (Vâkı'a, 95)",
        "Dini sadece kulaktan dolma yaşama; onu kalbinde ve amellerinde tat ki yakînin şüpheden arınsın.",
        56, 95
    ),
    (
        243, "İlmü’l-Yakîn", "عِلْمُ اليَقِينِ", "İlmü'l-Yakîn", "'-L-M / Y-Q-N (Delille Kesin Bilmek)",
        "Akıl, vahiy ve sağlam deliller ışığında **şüpheden tamamen arınmış kesin ilim mertebesi**.",
        "“Hayır! Keşke kesin bir bilgiyle (ilmü'l-yakîn olarak) bilseydiniz!” (Tekâsür, 5)",
        "İlim amel edilmek için öğrenilir; delile dayanan iman seni gaflet uykusundan sarsarak uyandırır.",
        102, 5
    ),
    (
        244, "Hüsn-i Hâtime", "حُسْنُ الخَاتِمَةِ", "Hüsnü'l-Hâtime", "H-S-N / H-T-M (Güzel Son)",
        "Ömrü iman, salih amel ve tevhid üzere tamamlayarak **huzur ve afiyetle son nefesi verme arzusu**.",
        "“Rabbimiz! Günahlarımızı bağışla, kötülüklerimizi ört ve canımızı iyilerle (ebrâr ile) beraber al.” (Âl-i İmrân, 193)",
        "Nasıl yaşarsan öyle ölürsün; son nefesinin güzel olmasını istiyorsan her gününü bir veda namazı huşûsuyla yaşa.",
        3, 193
    ),
    (
        245, "Şükr-i Nimet", "شُكْرُ النِّعْمَةِ", "Şükrü'n-Ni'meh", "Ş-K-R / N-'-M (Nimete Şükretmek)",
        "Lütfedilen her ihsanın Allah'tan olduğunu bilip **nimetin cinsinden infak ve itaat ile karşılık verme**.",
        "“Andolsun ki eğer şükrederseniz elbette size olan nimetimi artırırım.” (İbrâhîm, 7)",
        "Nimet şükürle korunur ve çoğalır; nankörlük ise ilahi bereketi kurutan en büyük afettir.",
        14, 7
    ),
    (
        246, "Dâr-ı Âhiret", "الدَّارُ الآخِرَةُ", "ed-Dârü'l-Âhireh", "D-V-R / E-H-R (Ahiret Yurdu)",
        "Geçici dünyanın sona ermesiyle başlayan, **ölümün olmadığı hakiki ve ebedi hayat yurdu**.",
        "“Bu dünya hayatı bir eğlence ve oyundan başka bir şey değildir. Asıl hayat ahiret yurdudur; keşke bilselerdi!” (Ankebût, 64)",
        "Otele yerleşir gibi dünyada kalıcı sanma kendini; asıl memleketine azık hazırla.",
        29, 64
    ),
    (
        247, "Hayât-ı Tayyibe", "الحَيَاةُ الطَّيِّبَةُ", "el-Hayâtü't-Tayyibe", "H-Y-Y / T-Y-B (Huzurlu ve Arı Yaşam)",
        "İman ve salih amel zemininde yeşeren **huzurlu, onurlu, bereketli ve arı-duru bir dünya hayatı**.",
        "“Erkek veya kadın, her kim mümin olarak salih amel işlerse, elbette onu tertemiz bir hayatla (hayât-ı tayyibe) yaşatırız.” (Nahl, 97)",
        "Mutluluk dünyalıkların çokluğunda değil, Allah rızasıyla yoğrulmuş temiz ve sade bir ömürdedir.",
        16, 97
    ),
    (
        248, "Rûh-ı Emîn", "الرُّوحُ الأَمِينُ", "er-Rûhu'l-Emîn", "R-V-H / E-M-N (Güvenilir Ruh)",
        "İlahi vahyi peygamberlerin kalbine eksiksizce ulaştıran **en güvenilir melek (Cebrail a.s.)**.",
        "“Onu Rûhu'l-Emîn (Cebrail) indirdi; uyarıcılardan olasın diye senin kalbine.” (Şuarâ, 193-194)",
        "Emanete sadakat meleklerin sıfatıdır; sen de kalbine gelen hakikati hayatında emanet bilip koru.",
        26, 193
    ),
    (
        249, "Kavl-i Sakîl", "القَوْلُ الثَّقِيلُ", "el-Kavlü's-Sakîl", "Q-V-L / S-Q-L (Ağır ve Sorumlu Söz)",
        "Manevi ağırlığı, sorumluluğu ve hükümleri cihanı titreten **yüce Kur'an vahyi**.",
        "“Doğrusu Biz senin üzerine taşınması ağır bir söz (kavl-i sakîl) bırakacağız.” (Müzzemmil, 5)",
        "Vahyin sorumluluğu büyüktür; onu sadece dille okumak yetmez, omuzlarında bir dava olarak taşımalısın.",
        73, 5
    ),
    (
        250, "Hakk-ı Tilâvet", "حَقُّ التِّلَاوَةِ", "Hakku't-Tilâveh", "H-Q-Q / T-L-V (Layıkıyla Okumak)",
        "Kur'an'ı sadece harfleriyle değil; **anlayarak, hissederek ve hayatına tatbik ederek hakkıyla okuma**.",
        "“Kendilerine verdiğimiz Kitab'ı hakkıyla okuyanlar (hakk-ı tilâvetle okuyanlar) var ya, işte onlar ona gerçekten iman edenlerdir.” (Bakara, 121)",
        "Kur'an'ın hakkını vermek, onun her ayetini kalbine şifa ve adımlarına rehber kılmaktan geçer.",
        2, 121
    )
]

def main():
    # 1. Dualar Güncellemesi
    with open(DUALAR_PATH, "r", encoding="utf-8") as f:
        dualar = json.load(f)

    print(f"Mevcut Dua Sayısı: {len(dualar)}")
    mevcut_d_idler = {d["id"] for d in dualar}

    eklenen_dua = 0
    for d in YENI_DUALAR:
        if d["id"] not in mevcut_d_idler:
            dualar.append(d)
            eklenen_dua += 1

    with open(DUALAR_PATH, "w", encoding="utf-8") as f:
        json.dump(dualar, f, ensure_ascii=False, indent=2)

    print(f"Eklenen Dua: {eklenen_dua}, Toplam Dua: {len(dualar)}")

    # 2. Kelimeler Güncellemesi
    with open(KELIMELER_PATH, "r", encoding="utf-8") as f:
        kelimeler = json.load(f)

    print(f"Mevcut Kelime Sayısı: {len(kelimeler)}")
    mevcut_k_idler = {k["id"] for k in kelimeler}

    eklenen_kelime = 0
    for k_id, tr, ar, okunus, kok, lugat, kuran_b, ders, s_no, a_no in YENI_KAVRAMLAR_TUPLES:
        if k_id in mevcut_k_idler:
            continue
        ay = ayet_getir(s_no, a_no)
        if not ay:
            print(f"HATA: {tr} için {s_no}:{a_no} âyeti bulunamadı!")
            continue

        sure_adi = ay.get("sure_adi_tr", "")
        ayet_ref = f"{sure_adi} Sûresi, {a_no}. Âyet"
        ayet_ar = ay.get("arapca_metin", "")

        kelime_obj = {
            "id": k_id,
            "kelime_tr": tr,
            "kelime_ar": ar,
            "okunus": okunus,
            "kok": kok,
            "lugat_anlami": lugat,
            "kuran_boyutu": kuran_b,
            "hayat_dersi": ders,
            "ayet_ref": ayet_ref,
            "paylasildi_mi": False,
            "ayet_arapca": ayet_ar,
            "paylasim_sayisi": 0,
            "son_paylasim": None
        }
        kelimeler.append(kelime_obj)
        eklenen_kelime += 1

    with open(KELIMELER_PATH, "w", encoding="utf-8") as f:
        json.dump(kelimeler, f, ensure_ascii=False, indent=2)

    print(f"Eklenen Kelime: {eklenen_kelime}, Toplam Kelime: {len(kelimeler)}")

if __name__ == "__main__":
    main()
