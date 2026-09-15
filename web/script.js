/**
 * Ezan Plus — Dinamik Vitrin & İnteraktif Modül Motoru
 * - Canlı Namaz Vakti Geri Sayım Sayacı
 * - İnteraktif iPhone 16 Pro Mockup Deneyimi
 * - Şeyh Mişari Râşid Stüdyo Tilavet Çaları
 * - Tescilli Külliyat & Hikmet Rotatoru
 * - QR Kod Modal Yöneticisi
 */

document.addEventListener('DOMContentLoaded', () => {
    initHeaderScroll();
    initSmartDeviceDownload();
    initThreeJsBackground();
    init3dMockupTilt();
    init3dCardTilt();
    initMockupTabs();
    initGalleryCarousel();
    initFaqAccordion();
    initInteractiveDhikr();
    initLivePrayerTimes();
    initQuranShowcase();
    initWisdomRotator();
    initQrModal();
    initBetaModal();
});

/* ==========================================================================
   1. Header Scroll Efekti
   ========================================================================== */
function initHeaderScroll() {
    const header = document.querySelector('.site-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }, { passive: true });
}

/* ==========================================================================
   2. İnteraktif iPhone Mockup Sekmeleri (Gerçek Ekranlar)
   ========================================================================== */
function initMockupTabs() {
    const tabButtons = document.querySelectorAll('.mockup-tab-btn');
    const screens = document.querySelectorAll('.mockup-screen-img, .mockup-screen-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            tabButtons.forEach(b => b.classList.remove('active'));
            screens.forEach(s => s.classList.remove('active'));

            btn.classList.add('active');
            const targetScreen = document.getElementById(`screen-${targetTab}`);
            if (targetScreen) {
                targetScreen.classList.add('active');
            }
        });
    });
}

/* ==========================================================================
   3. İnteraktif Zikirmatik (Haptik / Dokunma Efekti)
   ========================================================================== */
let dhikrCount = 33;
const dhikrPhrases = [
    { ar: "سُبْحَانَ اللَّهِ", tr: "Sübhânallâh", meaning: "Allah her türlü eksiklikten münezzehtir" },
    { ar: "الْحَمْدُ لِلَّهِ", tr: "Elhamdülillâh", meaning: "Hamd ve övgü yalnız Allah'a aittir" },
    { ar: "اللَّهُ أَكْبَرُ", tr: "Allâhu Ekber", meaning: "Allah en büyüktür, yüceler yücesidir" },
    { ar: "لَا إِلٰهَ إِلَّا اللَّهُ", tr: "Lâ ilâhe illallâh", meaning: "Allah'tan başka ilah yoktur" }
];
let currentPhraseIdx = 0;

function initInteractiveDhikr() {
    const dhikrBtn = document.getElementById('dhikrInteractiveBtn');
    const dhikrCountEl = document.getElementById('dhikrCountDisplay');
    const dhikrTitleEl = document.getElementById('dhikrTitleDisplay');
    const dhikrArabicEl = document.getElementById('dhikrArabicDisplay');

    if (!dhikrBtn || !dhikrCountEl) return;

    dhikrBtn.addEventListener('click', () => {
        dhikrCount++;
        dhikrCountEl.textContent = dhikrCount;

        // Titreşim (Mobil destekleyen tarayıcılarda)
        if (navigator.vibrate) {
            navigator.vibrate(25);
        }

        // Her 33'te bir zikri değiştir
        if (dhikrCount % 33 === 0) {
            currentPhraseIdx = (currentPhraseIdx + 1) % dhikrPhrases.length;
            const p = dhikrPhrases[currentPhraseIdx];
            if (dhikrTitleEl) dhikrTitleEl.textContent = p.tr;
            if (dhikrArabicEl) dhikrArabicEl.textContent = p.ar;

            if (navigator.vibrate) {
                navigator.vibrate([40, 60, 40]);
            }
        }
    });
}

/* ==========================================================================
   4. Canlı Namaz Vakitleri & Geri Sayım Sayacı
   ========================================================================== */
const SEHIR_VAKITLERI = {
    "istanbul": { imsak: "05:18", gunes: "06:44", ogle: "13:06", ikindi: "16:38", aksam: "19:18", yatsi: "20:38" },
    "ankara":   { imsak: "05:04", gunes: "06:29", ogle: "12:51", ikindi: "16:23", aksam: "19:03", yatsi: "20:22" },
    "izmir":    { imsak: "05:27", gunes: "06:51", ogle: "13:14", ikindi: "16:47", aksam: "19:26", yatsi: "20:44" },
    "bursa":    { imsak: "05:19", gunes: "06:44", ogle: "13:06", ikindi: "16:39", aksam: "19:18", yatsi: "20:37" },
    "mekke":    { imsak: "04:52", gunes: "06:08", ogle: "12:21", ikindi: "15:44", aksam: "18:24", yatsi: "19:39" },
    "medine":   { imsak: "04:50", gunes: "06:09", ogle: "12:22", ikindi: "15:47", aksam: "18:25", yatsi: "19:42" }
};

const VAKIT_ISIMLERI = [
    { key: "imsak", tr: "İmsak" },
    { key: "gunes", tr: "Güneş" },
    { key: "ogle", tr: "Öğle" },
    { key: "ikindi", tr: "İkindi" },
    { key: "aksam", tr: "Akşam" },
    { key: "yatsi", tr: "Yatsı" }
];

let secilenSehir = "istanbul";

function initLivePrayerTimes() {
    const sehirSelect = document.getElementById('sehirSelect');
    if (sehirSelect) {
        sehirSelect.addEventListener('change', (e) => {
            secilenSehir = e.target.value;
            vakitleriGuncelle();
        });
    }

    vakitleriGuncelle();
    setInterval(vakitleriGuncelle, 1000);
}

function timeToMinutes(timeStr) {
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}

function vakitleriGuncelle() {
    const vakitler = SEHIR_VAKITLERI[secilenSehir] || SEHIR_VAKITLERI["istanbul"];
    const now = new Date();
    const curHours = now.getHours();
    const curMins = now.getMinutes();
    const curSecs = now.getSeconds();
    const nowMinutes = curHours * 60 + curMins;

    // Vakit kutularındaki saatleri yaz
    VAKIT_ISIMLERI.forEach(v => {
        const timeBox = document.getElementById(`vakitTime-${v.key}`);
        if (timeBox) {
            timeBox.textContent = vakitler[v.key];
        }
    });

    // Sıradaki vakti bul
    let siradakiVakit = null;
    let siradakiVakitDakika = 0;
    let oncekiVakit = VAKIT_ISIMLERI[VAKIT_ISIMLERI.length - 1];

    for (let i = 0; i < VAKIT_ISIMLERI.length; i++) {
        const v = VAKIT_ISIMLERI[i];
        const vDk = timeToMinutes(vakitler[v.key]);
        if (vDk > nowMinutes) {
            siradakiVakit = v;
            siradakiVakitDakika = vDk;
            oncekiVakit = i > 0 ? VAKIT_ISIMLERI[i - 1] : VAKIT_ISIMLERI[VAKIT_ISIMLERI.length - 1];
            break;
        }
    }

    // Gece yarısından sonra Yatsı geçmişse sıradaki İmsak'tır (ertesi gün)
    let kalanSaniye = 0;
    if (!siradakiVakit) {
        siradakiVakit = VAKIT_ISIMLERI[0]; // İmsak
        const ertesiImsakDakika = 24 * 60 + timeToMinutes(vakitler["imsak"]);
        kalanSaniye = (ertesiImsakDakika - nowMinutes) * 60 - curSecs;
    } else {
        kalanSaniye = (siradakiVakitDakika - nowMinutes) * 60 - curSecs;
    }

    // Vakit kutularının aktifliğini ayarla
    VAKIT_ISIMLERI.forEach(v => {
        const box = document.getElementById(`prayerBox-${v.key}`);
        if (box) {
            if (v.key === oncekiVakit.key) {
                box.classList.add('active');
                const statusEl = box.querySelector('.prayer-box-status');
                if (statusEl) statusEl.textContent = "Şu Anki Vakit";
            } else {
                box.classList.remove('active');
                const statusEl = box.querySelector('.prayer-box-status');
                if (statusEl) statusEl.textContent = (v.key === siradakiVakit.key) ? "Sıradaki Vakit" : "";
            }
        }
    });

    // Dairesel İlerleme Barı (Circular Progress) Hesapla
    const oncekiDk = timeToMinutes(vakitler[oncekiVakit.key]);
    let hedefDk = timeToMinutes(vakitler[siradakiVakit.key]);
    let simdikiDk = nowMinutes + curSecs / 60;
    
    // Gece geçişi normalizasyonu (Yatsı -> İmsak)
    if (hedefDk <= oncekiDk) {
        hedefDk += 24 * 60;
        if (simdikiDk < oncekiDk) {
            simdikiDk += 24 * 60;
        }
    }
    const toplamSure = hedefDk - oncekiDk;
    const gecenSure = simdikiDk - oncekiDk;
    const progress = Math.min(100, Math.max(0, toplamSure > 0 ? (gecenSure / toplamSure) * 100 : 0));
    
    // SVG çevresi = 2 * PI * r = 2 * 3.14159265 * 102 = 640.88
    const circumference = 640.88;
    const offset = circumference - (progress / 100) * circumference;
    const circleBar = document.getElementById('timerCircleBar');
    if (circleBar) {
        circleBar.style.strokeDashoffset = offset.toFixed(2);
    }

    // Geri sayım formatla (02:45 ve :12)
    const kSaat = Math.floor(kalanSaniye / 3600);
    const kDakika = Math.floor((kalanSaniye % 3600) / 60);
    const kSaniye = kalanSaniye % 60;
    const hmStr = `${String(kSaat).padStart(2, '0')}:${String(kDakika).padStart(2, '0')}`;
    const secStr = `:${String(kSaniye).padStart(2, '0')}`;

    const digitsHM = document.getElementById('digitsHM');
    const digitsSec = document.getElementById('digitsSec');
    if (digitsHM && digitsSec) {
        digitsHM.textContent = hmStr;
        digitsSec.textContent = secStr;
    } else {
        const countdownEl = document.getElementById('liveCountdownTimer');
        if (countdownEl) countdownEl.textContent = `${hmStr}${secStr}`;
    }

    const countdownLabelEl = document.getElementById('liveCountdownLabel');
    if (countdownLabelEl) countdownLabelEl.textContent = `${siradakiVakit.tr} Vaktine Kalan Süre`;
    const appNextVakitTag = document.getElementById('appNextVakitTag');
    if (appNextVakitTag) appNextVakitTag.textContent = siradakiVakit.tr.toUpperCase();

    // Şehir ismini kadran hapında güncelle
    const timerCityName = document.getElementById('appTimerCityName');
    const sehirSelectEl = document.getElementById('sehirSelect');
    if (timerCityName && sehirSelectEl) {
        timerCityName.textContent = sehirSelectEl.options[sehirSelectEl.selectedIndex]?.text || "İstanbul";
    }

    // Mockup içindeki küçük ekranı da güncelle
    const miniNextTime = document.getElementById('miniNextTime');
    const miniCountdown = document.getElementById('miniCountdownBadge');
    const miniNextLabel = document.getElementById('miniNextLabel');
    if (miniNextTime) miniNextTime.textContent = vakitler[siradakiVakit.key];
    if (miniCountdown) miniCountdown.textContent = `${kSaat} sa ${kDakika} dk kaldı`;
    if (miniNextLabel) miniNextLabel.textContent = `${siradakiVakit.tr} Vakti`;

    // Mockup satırlarını güncelle
    VAKIT_ISIMLERI.forEach(v => {
        const row = document.getElementById(`miniRow-${v.key}`);
        if (row) {
            if (v.key === oncekiVakit.key) {
                row.classList.add('active-prayer');
            } else {
                row.classList.remove('active-prayer');
            }
            const timeSpan = row.querySelector('.time');
            if (timeSpan) timeSpan.textContent = vakitler[v.key];
        }
    });
}

/* ==========================================================================
   5. İnteraktif Kur'an-ı Kerim, Tilavet, Hatim ve Canlı Radyo Motoru
   ========================================================================== */
const QURAN_SURAHS_DATA = {
    "ayetel-kursi": {
        id: "ayetel-kursi",
        badge: "BAKARA SÛRESİ • 255. ÂYET (ÂYETE'L-KÜRSÎ)",
        juzBadge: "3. CÜZ • MEDENÎ",
        verseKey: "2:255",
        words: [
            "اللَّهُ", "لَا", "إِلٰهَ", "إِلَّا", "هُوَ", "الْحَيُّ", "الْقَيُّومُ", "ۚ",
            "لَا", "تَأْخُذُهُ", "سِنَةٌ", "وَلَا", "نَوْمٌ", "ۚ",
            "لَهُ", "مَا", "فِي", "السَّمَاوَاتِ", "وَمَا", "فِي", "الْأَرْضِ", "ۗ",
            "مَنْ", "ذَا", "الَّذِي", "يَشْفَعُ", "عِنْدَهُ", "إِلَّا", "بِإِذْنِهِ", "ۚ",
            "يَعْلَمُ", "مَا", "بَيْنَ", "أَيْدِيهِمْ", "وَمَا", "خَلْفَهُمْ", "ۖ",
            "وَلَا", "يُحِيطُونَ", "بِشَيْءٍ", "مِنْ", "عِلْمِهِ", "إِلَّا", "بِمَا", "شَاءَ", "ۚ",
            "وَسِعَ", "كُرْسِيُّهُ", "السَّمَاوَاتِ", "وَالْأَرْضَ", "ۖ",
            "وَلَا", "يَئُودُهُ", "حِفْظُهُمَا", "ۚ",
            "وَهُوَ", "الْعَلِيُّ", "الْعَظِيمُ"
        ],
        latin: "Allâhu lâ ilâhe illâ huve'l-hayyu'l-kayyûm, lâ te'huzuhû sinetun velâ nevm, lehû mâ fî's-semâvâti vemâ fî'l-ard, men zellezî yeşfeu indehû illâ bi-iznih, ya'lemu mâ beyne eydîhim vemâ halfehum, velâ yuhîtûne bi-şey'in min ilmihî illâ bimâ şâe, vesia kursiyyuhu's-semâvâti ve'l-ard, velâ yeûduhû hifzuhumâ, ve huve'l-aliyyu'l-azîm.",
        translations: {
            diyanet: "“ Allah, O'ndan başka hiçbir ilah olmayandır; daima yaşayan (Hayy), bütün varlığın idaresini yürüten (Kayyûm) dir. O'nu ne bir uyuklama tutabilir, ne de bir uyku. Göklerde ve yerde ne varsa hepsi O'nundur... O, çok yücedir, çok büyüktür. ”",
            yazir: "“ Allah ki, O'ndan başka ilah yoktur; daima diridir, yaratıklarını koruyup yöneticidir. O'nu ne bir uyuklama tutar ne de bir uyku. Göklerde ve yerde ne varsa hepsi O'nundur... O çok yüce, çok büyüktür. ”",
            ozturk: "“ Allah, O'ndan başka ilah yoktur; diridir, her an yaratış ve idare halindedir. O'nu ne bir uyuklama tutar ne de bir uyku... O, çok yücedir, çok büyüktür. ”",
            yuksel: "“ ALLAH: O'ndan başka tanrı yoktur; Diridir, Ebedidir. O'nu ne bir uyuklama ne de bir uyku yakalayamaz... O Yücedir, Büyüktür. ”"
        },
        tefekkur: "Âyete'l-Kürsî; tevhidin, ilahi kudretin ve sarsılmaz ilmin Kur'an'daki en azametli ifadesidir.",
        localAudio: "assets/audio/002255.mp3",
        surahNum: "002",
        ayahNum: "255"
    },
    "fatiha": {
        id: "fatiha",
        badge: "FÂTİHA SÛRESİ • 1. ÂYET",
        juzBadge: "1. CÜZ • MEKKÎ",
        verseKey: "1:1",
        words: ["بِسْمِ", "اللَّهِ", "الرَّحْمَٰنِ", "الرَّحِيمِ"],
        latin: "Bismillâhirrahmânirrahîm.",
        translations: {
            diyanet: "“ Rahman ve Rahîm olan Allah'ın adıyla. ”",
            yazir: "“ Merhametli ve çok lütufkâr olan Allah'ın adıyla. ”",
            ozturk: "“ Rahman ve Rahîm Allah'ın adıyla. ”",
            yuksel: "“ Bağışlayan ve Esirgeyen ALLAH'ın adıyla. ”"
        },
        tefekkur: "Her hayırlı amelin başı, kalbi ilahi rahmet kapısına açan Nebevî anahtardır.",
        localAudio: "assets/audio/001001.mp3",
        surahNum: "001",
        ayahNum: "001"
    },
    "insirah": {
        id: "insirah",
        badge: "İNŞİRÂH SÛRESİ • 5-6. ÂYET",
        juzBadge: "30. CÜZ • MEKKÎ",
        verseKey: "94:5",
        words: ["فَإِنَّ", "مَعَ", "الْعُسْرِ", "يُسْرًا", "•", "إِنَّ", "مَعَ", "الْعُسْرِ", "يُسْرًا"],
        latin: "Fe inne meal usri yusrâ, inne meal usri yusrâ.",
        translations: {
            diyanet: "“ Şüphesiz her güçlükle beraber bir kolaylık vardır. Gerçekten güçlükle beraber bir kolaylık vardır. ”",
            yazir: "“ Demek ki zorlukla beraber bir kolaylık var. Evet, zorlukla beraber bir kolaylık var! ”",
            ozturk: "“ Demek ki, zorluğun yanında bir kolaylık mutlaka var! Evet, zorluğun yanında bir kolaylık mutlaka var! ”",
            yuksel: "“ Kuşkusuz, zorlukla beraber bir kolaylık vardır. Evet, zorlukla beraber bir kolaylık vardır. ”"
        },
        tefekkur: "Sabır ve tevekkülün sonunda kalbe inen ilahi ferahlığın ebedi müjdesidir.",
        localAudio: "assets/audio/insirah.mp3",
        surahNum: "094",
        ayahNum: "005"
    },
    "yasin": {
        id: "yasin",
        badge: "YÂSÎN SÛRESİ • 58. ÂYET",
        juzBadge: "23. CÜZ • MEKKÎ",
        verseKey: "36:58",
        words: ["سَلَامٌ", "قَوْلًا", "مِنْ", "رَبٍّ", "رَحِيمٍ"],
        latin: "Selâmun kavlen min rabbin rahîm.",
        translations: {
            diyanet: "“ Çok merhametli olan Rab'den bir söz olarak kendilerine 'Selâm' vardır. ”",
            yazir: "“ Merhametli bir Rabbin sözü olarak onlara 'Selâm' vardır. ”",
            ozturk: "“ Çok merhametli bir Rab'den bir de sözlü 'Selâm' vardır. ”",
            yuksel: "“ Çok Rahîm olan Rab'den bir söz olarak: 'Selam!' ”"
        },
        tefekkur: "Cennet ehline Yüce Mevlâ katından bizzat ikram edilecek en şerefli hitaptır.",
        localAudio: "assets/audio/036058.mp3",
        surahNum: "036",
        ayahNum: "058"
    },
    "mulk": {
        id: "mulk",
        badge: "MÜLK SÛRESİ • 1. ÂYET",
        juzBadge: "29. CÜZ • MEKKÎ",
        verseKey: "67:1",
        words: ["تَبَارَكَ", "الَّذِي", "بِيَدِهِ", "الْمُلْكُ", "وَهُوَ", "عَلَىٰ", "كُلِّ", "شَيْءٍ", "قَدِيرٌ"],
        latin: "Tebârekellezî biyedihil mulku ve huve alâ kulli şey'in kadîr.",
        translations: {
            diyanet: "“ Hükümranlık elinde olan Allah, yüceler yücesidir ve O her şeye hakkıyla güç yetirendir. ”",
            yazir: "“ Mutlak hükümranlık elinde bulunan Allah ne yücedir! O'nun her şeye gücü yeter. ”",
            ozturk: "“ Ne yücedir O ki, mülk ve saltanat O'nun elindedir. Ve O, her şeye güç yetirendir. ”",
            yuksel: "“ Egemenlik elinde bulunan çok yücedir ve O her şeye Kadirdir. ”"
        },
        tefekkur: "Kabir azabından koruyan ve geceleri tefekkürle tilavet edilmesi tavsiye edilen sûredir.",
        localAudio: "assets/audio/067001.mp3",
        surahNum: "067",
        ayahNum: "001"
    },
    "ihlas": {
        id: "ihlas",
        badge: "İHLÂS SÛRESİ • 1. ÂYET",
        juzBadge: "30. CÜZ • MEKKÎ",
        verseKey: "112:1",
        words: ["قُلْ", "هُوَ", "اللَّهُ", "أَحَدٌ"],
        latin: "Kul huvallâhu ehad.",
        translations: {
            diyanet: "“ De ki: O, Allah'tır, bir tektir. ”",
            yazir: "“ De ki: O Allah, birdir. ”",
            ozturk: "“ De ki: O, Allah'tır; Ehad'dir, tektir. ”",
            yuksel: "“ De ki: O ALLAH birdir. ”"
        },
        tefekkur: "Tevhid akidesinin özü ve Kur'an'ın üçte birine denk olan saf ihlas beyanıdır.",
        localAudio: "assets/audio/112001.mp3",
        surahNum: "112",
        ayahNum: "001"
    }
};

const QURAN_RECITERS_CONFIG = {
    alafasy: { label: "Şeyh Mişari Râşid el-Afâsî", url: "https://everyayah.com/data/Alafasy_128kbps/" },
    ghamadi: { label: "Saad el-Gâmidî", url: "https://everyayah.com/data/Ghamadi_40kbps/" },
    basit:   { label: "Abdülbâsit Abdüssamed", url: "https://everyayah.com/data/Abdul_Basit_Murattal_192kbps/" },
    husary:  { label: "Mahmud Halil el-Huserî", url: "https://everyayah.com/data/Husary_128kbps/" },
    sudais:  { label: "Abdurrahman es-Sudeys", url: "https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/" },
    shuraym: { label: "Suud eş-Şureym", url: "https://everyayah.com/data/Shuraym_128kbps/" },
    minshawi:{ label: "Muhammed Sıddık el-Minşâvî", url: "https://everyayah.com/data/Minshawy_Murattal_128kbps/" }
};

let currentSurahKey = "ayetel-kursi";
let currentReciterKey = "alafasy";
let currentMealKey = "diyanet";
let currentPlaybackSpeed = 1.0;
let isRepeatEnabled = true;

// 30 Cüz Durum Haritası (Varsayılan 18 cüz tamamlanmış = %60)
let completedJuzMap = {
    1: true, 2: true, 3: true, 4: true, 5: true, 6: true,
    7: true, 8: true, 9: true, 10: true, 11: true, 12: true,
    13: true, 14: true, 15: true, 16: true, 17: true, 18: true
};

function initQuranShowcase() {
    initQuranNavTabs();
    initQuranTilavetPlayer();
    initHatimTracker();
    initQuranRadio();
}

/* --- A. Kur'an Ana Sekmeler (Player / Hatim / Radio) --- */
function initQuranNavTabs() {
    const tabBtns = document.querySelectorAll('.quran-nav-tab');
    const panels = document.querySelectorAll('.quran-tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabKey = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPanel = document.getElementById(`quranPanel-${tabKey}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
}

/* --- B. Canlı Tilavet Çaları & Senkron Karaoke --- */
function initQuranTilavetPlayer() {
    const audioEl = document.getElementById('quranRecitationAudio');
    const playBtn = document.getElementById('mushafPlayBtn');
    const progressTrack = document.getElementById('mushafProgressTrack');
    const progressFill = document.getElementById('mushafProgressFill');
    const curTimeEl = document.getElementById('mushafCurTime');
    const durTimeEl = document.getElementById('mushafDurTime');
    const equalizer = document.getElementById('mushafEqualizer');
    const speedBtn = document.getElementById('mushafSpeedBtn');
    const repeatBtn = document.getElementById('mushafRepeatBtn');
    const surahChips = document.querySelectorAll('.surah-chip');
    const reciterSelect = document.getElementById('reciterSelect');
    const mealSelect = document.getElementById('mealSelect');

    if (!audioEl || !playBtn) return;

    function renderActiveSurah(surahKey) {
        currentSurahKey = surahKey;
        const data = QURAN_SURAHS_DATA[surahKey];
        if (!data) return;

        // Rozetler
        const badgeEl = document.getElementById('mushafAyahBadge');
        const juzBadgeEl = document.getElementById('mushafJuzBadge');
        const titleEl = document.getElementById('mushafPlayingTitle');
        if (badgeEl) badgeEl.textContent = data.badge;
        if (juzBadgeEl) juzBadgeEl.textContent = data.juzBadge;
        if (titleEl) titleEl.textContent = data.badge;

        // Arapça Hat (Kelime spans)
        const arabicEl = document.getElementById('mushafArabicText');
        if (arabicEl) {
            arabicEl.innerHTML = data.words.map((w, idx) => 
                `<span class="quran-word waiting" id="qWord-${idx}">${w}</span>`
            ).join(' ');
        }

        // Latin Okunuş
        const latinEl = document.getElementById('mushafLatinText');
        if (latinEl) latinEl.textContent = data.latin;

        // Türkçe Meal
        const transEl = document.getElementById('mushafTranslationText');
        if (transEl) transEl.textContent = data.translations[currentMealKey] || data.translations['diyanet'];

        // Tefekkür
        const tefekkurEl = document.getElementById('mushafTefekkurText');
        if (tefekkurEl) tefekkurEl.textContent = data.tefekkur;

        // Audio Source
        updateAudioSource();
    }

    function updateAudioSource() {
        const data = QURAN_SURAHS_DATA[currentSurahKey];
        if (!data) return;

        let src = data.localAudio;
        if (currentReciterKey !== 'alafasy') {
            const rConfig = QURAN_RECITERS_CONFIG[currentReciterKey];
            if (rConfig) {
                src = `${rConfig.url}${data.surahNum}${data.ayahNum}.mp3`;
            }
        }

        const wasPlaying = !audioEl.paused;
        audioEl.src = src;
        audioEl.playbackRate = currentPlaybackSpeed;
        if (wasPlaying) {
            audioEl.play().catch(e => console.log('Autoplay error:', e));
        }
    }

    function togglePlay() {
        if (audioEl.paused) {
            // Canlı radyo çalıyorsa sustur
            const radioAudio = document.getElementById('quranLiveRadioAudio');
            if (radioAudio && !radioAudio.paused) {
                radioAudio.pause();
                const rPlayBtn = document.getElementById('radioMainPlayBtn');
                const rWave = document.getElementById('radioWaveform');
                if (rPlayBtn) rPlayBtn.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"></polygon></svg>`;
                if (rWave) rWave.classList.remove('playing');
            }
            audioEl.play().catch(e => console.log('Audio blocked:', e));
        } else {
            audioEl.pause();
        }
    }

    playBtn.addEventListener('click', togglePlay);

    // Mockup mini play butonu ile senkronize
    const miniPlayBtn = document.getElementById('miniPlayBtn');
    if (miniPlayBtn) {
        miniPlayBtn.addEventListener('click', togglePlay);
    }

    audioEl.addEventListener('play', () => {
        playBtn.innerHTML = `
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="2"></rect>
                <rect x="14" y="4" width="4" height="16" rx="2"></rect>
            </svg>
        `;
        if (equalizer) equalizer.classList.add('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" rx="1"></rect>
                    <rect x="14" y="4" width="4" height="16" rx="1"></rect>
                </svg>
            `;
        }
    });

    audioEl.addEventListener('pause', () => {
        playBtn.innerHTML = `
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="6 4 20 12 6 20 6 4"></polygon>
            </svg>
        `;
        if (equalizer) equalizer.classList.remove('playing');
        if (miniPlayBtn) {
            miniPlayBtn.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 4 18 12 6 20 6 4"></polygon>
                </svg>
            `;
        }
    });

    audioEl.addEventListener('timeupdate', () => {
        if (!isNaN(audioEl.duration) && audioEl.duration > 0) {
            const progress = (audioEl.currentTime / audioEl.duration);
            if (progressFill) progressFill.style.width = `${progress * 100}%`;
            if (curTimeEl) curTimeEl.textContent = formatAudioTime(audioEl.currentTime);
            if (durTimeEl) durTimeEl.textContent = formatAudioTime(audioEl.duration);

            // Kelime Karaoke Vurgulama
            const data = QURAN_SURAHS_DATA[currentSurahKey];
            if (data && data.words) {
                const totalWords = data.words.length;
                const activeIndex = Math.min(totalWords - 1, Math.floor(progress * totalWords));

                for (let i = 0; i < totalWords; i++) {
                    const wEl = document.getElementById(`qWord-${i}`);
                    if (!wEl) continue;
                    if (i === activeIndex) {
                        wEl.className = 'quran-word active';
                    } else if (i < activeIndex) {
                        wEl.className = 'quran-word done';
                    } else {
                        wEl.className = 'quran-word waiting';
                    }
                }
            }
        }
    });

    audioEl.addEventListener('ended', () => {
        if (isRepeatEnabled) {
            audioEl.currentTime = 0;
            audioEl.play().catch(e => console.log('Repeat blocked:', e));
        } else {
            if (progressFill) progressFill.style.width = '0%';
            if (curTimeEl) curTimeEl.textContent = "0:00";
        }
    });

    if (progressTrack) {
        progressTrack.addEventListener('click', (e) => {
            const rect = progressTrack.getBoundingClientRect();
            const clickPos = (e.clientX - rect.left) / rect.width;
            if (!isNaN(audioEl.duration)) {
                audioEl.currentTime = clickPos * audioEl.duration;
            }
        });
    }

    // Sûre Değişimi
    surahChips.forEach(chip => {
        chip.addEventListener('click', () => {
            surahChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            renderActiveSurah(chip.getAttribute('data-surah'));
        });
    });

    // Hafız Değişimi
    if (reciterSelect) {
        reciterSelect.addEventListener('change', (e) => {
            currentReciterKey = e.target.value;
            updateAudioSource();
        });
    }

    // Meal Değişimi
    if (mealSelect) {
        mealSelect.addEventListener('change', (e) => {
            currentMealKey = e.target.value;
            const data = QURAN_SURAHS_DATA[currentSurahKey];
            const transEl = document.getElementById('mushafTranslationText');
            if (data && transEl) {
                transEl.textContent = data.translations[currentMealKey] || data.translations['diyanet'];
            }
        });
    }

    // Hız Butonu
    if (speedBtn) {
        speedBtn.addEventListener('click', () => {
            if (currentPlaybackSpeed === 1.0) {
                currentPlaybackSpeed = 1.25;
            } else if (currentPlaybackSpeed === 1.25) {
                currentPlaybackSpeed = 1.5;
            } else {
                currentPlaybackSpeed = 1.0;
            }
            speedBtn.textContent = `${currentPlaybackSpeed.toFixed(currentPlaybackSpeed % 1 === 0 ? 0 : 2)}x`;
            audioEl.playbackRate = currentPlaybackSpeed;
        });
    }

    // Tekrar Butonu
    if (repeatBtn) {
        repeatBtn.addEventListener('click', () => {
            isRepeatEnabled = !isRepeatEnabled;
            repeatBtn.classList.toggle('active', isRepeatEnabled);
        });
    }

    // İlk Sûreyi Render Et (Âyete'l-Kürsî)
    renderActiveSurah("ayetel-kursi");
}

/* --- C. 30 Cüz Çoklu Hatim Takibi --- */
function initHatimTracker() {
    const gridEl = document.getElementById('hatimJuzGrid');
    const percentEl = document.getElementById('hatimPercentText');
    const countEl = document.getElementById('hatimCountText');
    const barFill = document.getElementById('hatimProgressBarFill');

    if (!gridEl) return;

    function updateHatimStats() {
        const completedCount = Object.values(completedJuzMap).filter(Boolean).length;
        const percent = Math.round((completedCount / 30) * 100);

        if (percentEl) percentEl.textContent = `%${percent}`;
        if (countEl) countEl.textContent = `${completedCount} / 30 Cüz Okundu`;
        if (barFill) barFill.style.width = `${percent}%`;
    }

    gridEl.innerHTML = '';
    for (let i = 1; i <= 30; i++) {
        const isDone = !!completedJuzMap[i];
        const box = document.createElement('div');
        box.className = `juz-box ${isDone ? 'completed' : ''}`;
        box.id = `juzBox-${i}`;
        box.setAttribute('title', `${i}. Cüz (Tıkla ve durumunu değiştir)`);
        box.innerHTML = `
            <span class="juz-number">${i}</span>
            <span class="juz-status-dot"></span>
        `;

        box.addEventListener('click', () => {
            completedJuzMap[i] = !completedJuzMap[i];
            box.classList.toggle('completed', completedJuzMap[i]);
            updateHatimStats();

            if (navigator.vibrate) {
                navigator.vibrate(20);
            }
        });

        gridEl.appendChild(box);
    }

    updateHatimStats();
}

/* --- D. 7/24 Kesintisiz Kur'an Radyosu --- */
function initQuranRadio() {
    const radioAudio = document.getElementById('quranLiveRadioAudio');
    const rPlayBtn = document.getElementById('radioMainPlayBtn');
    const rWave = document.getElementById('radioWaveform');
    const statusTitle = document.getElementById('radioStatusTitle');
    const sleepBtns = document.querySelectorAll('.sleep-btn');
    let sleepTimeoutId = null;

    if (!radioAudio || !rPlayBtn) return;

    function toggleRadio() {
        if (radioAudio.paused) {
            // Tilavet çaları çalıyorsa durdur
            const qAudio = document.getElementById('quranRecitationAudio');
            if (qAudio && !qAudio.paused) {
                qAudio.pause();
            }

            if (statusTitle) statusTitle.textContent = "Bağlanıyor...";
            radioAudio.play().then(() => {
                if (statusTitle) statusTitle.textContent = "Canlı Yayın Çalıyor";
                rPlayBtn.innerHTML = `
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="4" width="4" height="16" rx="2"></rect>
                        <rect x="14" y="4" width="4" height="16" rx="2"></rect>
                    </svg>
                `;
                if (rWave) rWave.classList.add('playing');
            }).catch(e => {
                console.log('Radio error:', e);
                if (statusTitle) statusTitle.textContent = "Bağlantı Hatası";
            });
        } else {
            radioAudio.pause();
            if (statusTitle) statusTitle.textContent = "Yayın Duraklatıldı";
            rPlayBtn.innerHTML = `
                <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="6 4 20 12 6 20 6 4"></polygon>
                </svg>
            `;
            if (rWave) rWave.classList.remove('playing');
        }
    }

    rPlayBtn.addEventListener('click', toggleRadio);

    // Uyku Zamanlayıcısı
    sleepBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            sleepBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (sleepTimeoutId) clearTimeout(sleepTimeoutId);
            const mins = parseInt(btn.getAttribute('data-mins'), 10);
            if (mins > 0) {
                sleepTimeoutId = setTimeout(() => {
                    if (!radioAudio.paused) {
                        radioAudio.pause();
                        if (statusTitle) statusTitle.textContent = "Uyku Zamanlayıcı Durdurdu";
                        rPlayBtn.innerHTML = `
                            <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor">
                                <polygon points="6 4 20 12 6 20 6 4"></polygon>
                            </svg>
                        `;
                        if (rWave) rWave.classList.remove('playing');
                    }
                }, mins * 60 * 1000);
            }
        });
    });
}

function formatAudioTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
}

/* ==========================================================================
   6. Günün Hikmeti & Tescilli Külliyat Rotatoru
   ========================================================================== */
const TESCİLLİ_KÜLLİYAT = [
    {
        kategori: "hadis",
        ar: "مَنْ لَا يَرْحَمِ النَّاسَ لَا يَرْحَمْهُ اللَّهُ",
        tr: "“ İnsanlara merhamet etmeyene, Allah da merhamet etmez. ”",
        kaynak: "RİYÂZÜ'S-SÂLİHÎN • BUHÂRÎ & MÜSLİM",
        tefekkur: "İslam ahlakı; insanlara şefkatle muamele etmeyi ve merhameti hayatın merkezine koymayı öğütler."
    },
    {
        kategori: "ayet",
        ar: "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا • إِنَّ مَعَ الْعُسْرِ يُسْرًا",
        tr: "“ Elbette zorlukla beraber bir kolaylık vardır. Gerçekten zorlukla beraber bir kolaylık vardır. ”",
        kaynak: "İNŞİRÂH SÛRESİ • 5-6. ÂYET",
        tefekkur: "Hayatın en çetin imtihanlarında dahi ilahi rahmet kapıdadır; sabır, ferahlığın anahtarıdır."
    },
    {
        kategori: "dua",
        ar: "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        tr: "“ Ey Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver. Ve bizi cehennem azabından koru. ”",
        kaynak: "BAKARA SÛRESİ • 201. ÂYET",
        tefekkur: "Dünya ile ahiret dengesini mükemmel bir ahenkle birleştiren en kapsamlı nebevî münacattır."
    },
    {
        kategori: "hadis",
        ar: "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
        tr: "“ Ameller ancak niyetlere göredir. Herkes için niyet ettiği ne ise o vardır. ”",
        kaynak: "RİYÂZÜ'S-SÂLİHÎN • BUHÂRÎ, BED'Ü'L-VAHY 1",
        tefekkur: "Amellerin manevi ağırlığını ve değerini belirleyen tek ölçü; kalbin samimiyeti ve ihlasıdır."
    },
    {
        kategori: "ayet",
        ar: "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        tr: "“ Bilesiniz ki kalpler ancak Allah'ı anmakla huzur ve sükûna kavuşur. ”",
        kaynak: "RA'D SÛRESİ • 28. ÂYET",
        tefekkur: "Ruhun aradığı gerçek dinginlik ne dünyalık meşgalelerde ne de maddiyattadır; yalnız Hakk'ın zikrindendir."
    }
];

let aktifKategori = "hepsi";
let hikmetIndex = 0;

function initWisdomRotator() {
    const tabBtns = document.querySelectorAll('.wisdom-tab-btn');
    const refreshBtn = document.getElementById('btnRefreshWisdom');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aktifKategori = btn.getAttribute('data-kat');
            hikmetGoster(true);
        });
    });

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            hikmetIndex = (hikmetIndex + 1) % TESCİLLİ_KÜLLİYAT.length;
            hikmetGoster(false);
        });
    }

    hikmetGoster(false);
}

function hikmetGoster(kategoriDegisti) {
    const contentBox = document.getElementById('wisdomContentBox');
    if (!contentBox) return;

    let uygunHavuz = TESCİLLİ_KÜLLİYAT;
    if (aktifKategori !== "hepsi") {
        uygunHavuz = TESCİLLİ_KÜLLİYAT.filter(item => item.kategori === aktifKategori);
    }
    if (uygunHavuz.length === 0) uygunHavuz = TESCİLLİ_KÜLLİYAT;

    const item = uygunHavuz[hikmetIndex % uygunHavuz.length];

    // Pürüzsüz erime (Fade) animasyonu
    contentBox.style.opacity = '0';
    setTimeout(() => {
        const arEl = document.getElementById('wisdomArabic');
        const quoteEl = document.getElementById('wisdomQuote');
        const sourceEl = document.getElementById('wisdomSource');
        const tefekkurEl = document.getElementById('wisdomTefekkur');

        if (arEl) arEl.textContent = item.ar;
        if (quoteEl) quoteEl.textContent = item.tr;
        if (sourceEl) sourceEl.textContent = item.kaynak;
        if (tefekkurEl) tefekkurEl.textContent = `“ ${item.tefekkur} ”`;

        contentBox.style.opacity = '1';
    }, 250);
}

/* ==========================================================================
   7. QR Kod Modalı
   ========================================================================== */
function initQrModal() {
    const triggers = document.querySelectorAll('.qr-modal-trigger');
    const modal = document.getElementById('qrModalBackdrop');
    const closeBtn = document.getElementById('qrModalClose');

    if (!modal) return;

    triggers.forEach(trig => {
        trig.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.add('active');
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }
    });
}

/* ==========================================================================
   7.5. Google Play Kapalı Beta Modalı
   ========================================================================== */
function initBetaModal() {
    const triggers = document.querySelectorAll('.beta-modal-trigger');
    const modal = document.getElementById('betaModalBackdrop');
    const closeBtn = document.getElementById('betaModalClose');
    const dismissBtn = document.getElementById('betaModalDismissBtn');

    if (!modal) return;

    triggers.forEach(trig => {
        trig.addEventListener('click', (e) => {
            e.preventDefault();
            modal.classList.add('active');
        });
    });

    const closeModal = () => modal.classList.remove('active');

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (dismissBtn) dismissBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
}

/* ==========================================================================
   7.8. Akıllı Cihaz Tespiti & İndirme Butonu Uyarlayıcı
   ========================================================================== */
function initSmartDeviceDownload() {
    const btn = document.getElementById('headerDownloadBtn');
    const textEl = document.getElementById('headerBtnText');
    if (!btn || !textEl) return;

    const ua = (navigator.userAgent || navigator.vendor || window.opera || '').toLowerCase();
    const isIOS = /iphone|ipad|ipod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isMac = /macintosh|macintel/.test(ua) && !isIOS;
    const isAndroid = /android/.test(ua);

    const appStoreUrl = "https://apps.apple.com/us/app/ezan-plus-namaz-kuran/id6769426030";

    if (isIOS || isMac) {
        btn.classList.add('device-apple');
        textEl.textContent = "App Store'dan İndir";
        btn.href = appStoreUrl;
        btn.target = "_blank";
        btn.rel = "noopener";
    } else if (isAndroid) {
        btn.classList.add('device-android');
        textEl.textContent = "Google Play (Beta)";
        btn.href = "#";
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const betaModal = document.getElementById('betaModalBackdrop');
            if (betaModal) betaModal.classList.add('active');
        });
    } else {
        // Desktop Windows, Linux vb.
        btn.classList.add('device-desktop');
        textEl.textContent = "Uygulamayı İndir";
        btn.href = "#indir";
    }
}

/* ==========================================================================
   8. Three.js Manevi 3D Işık & Altın Parçacık Sahnesi
   ========================================================================== */
function initThreeJsBackground() {
    const canvas = document.getElementById('hero3dCanvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, heroSection.clientWidth / heroSection.clientHeight, 0.1, 1000);
    camera.position.z = 24;

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(heroSection.clientWidth, heroSection.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Altın ve Zümrüt Manevi Parçacık Sistemi
    const particleCount = 180;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const goldColor = new THREE.Color('#D97706');
    const greenColor = new THREE.Color('#1B4332');
    const redColor = new THREE.Color('#9B1B1B');

    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 45;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 25;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 30;

        const mixRatio = Math.random();
        const c = mixRatio > 0.65 ? goldColor : (mixRatio > 0.35 ? greenColor : redColor);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Yumuşak dairesel doku
    const pCanvas = document.createElement('canvas');
    pCanvas.width = 64;
    pCanvas.height = 64;
    const pCtx = pCanvas.getContext('2d');
    const gradient = pCtx.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, 'rgba(255,255,255,1)');
    gradient.addColorStop(0.3, 'rgba(255,255,255,0.7)');
    gradient.addColorStop(1, 'rgba(255,255,255,0)');
    pCtx.fillStyle = gradient;
    pCtx.fillRect(0, 0, 64, 64);

    const pTexture = new THREE.CanvasTexture(pCanvas);
    const material = new THREE.PointsMaterial({
        size: 0.9,
        vertexColors: true,
        transparent: true,
        opacity: 0.42,
        map: pTexture,
        blending: THREE.NormalBlending,
        depthWrite: false
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    window.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });

    window.addEventListener('resize', () => {
        if (!heroSection) return;
        camera.aspect = heroSection.clientWidth / heroSection.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(heroSection.clientWidth, heroSection.clientHeight);
    });

    function animate() {
        requestAnimationFrame(animate);

        targetX += (mouseX * 2.2 - targetX) * 0.03;
        targetY += (-mouseY * 1.8 - targetY) * 0.03;

        particles.rotation.y += 0.0006;
        particles.rotation.x += 0.0003;

        camera.position.x = targetX;
        camera.position.y = targetY;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }
    animate();
}

/* ==========================================================================
   9. İnteraktif iPhone 16 Pro 3D Tilt Motoru
   ========================================================================== */
function init3dMockupTilt() {
    const mockupWrap = document.getElementById('iphone3dWrapper');
    if (mockupWrap) {
        mockupWrap.style.transform = 'none';
    }
}

/* ==========================================================================
   10. Kartlarda Yumuşak 3D Açı & Işık Efekti (3D Tilt Cards)
   ========================================================================== */
function init3dCardTilt() {
    const cards = document.querySelectorAll('.feature-card, .live-prayer-card, .audio-player-card, .wisdom-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;

            const rotX = y * -8;
            const rotY = x * 8;

            card.style.transform = `perspective(800px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-4px)`;
        }, { passive: true });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0)`;
        });
    });
}

/* ==========================================================================
   11. 3D Uygulama İçi Keşif Galerisi (Coverflow Motoru)
   ========================================================================== */
function initGalleryCarousel() {
    const track = document.getElementById('galleryCardsTrack');
    const cards = document.querySelectorAll('.gallery-card');
    const prevBtn = document.getElementById('galleryPrev');
    const nextBtn = document.getElementById('galleryNext');
    const dotsContainer = document.getElementById('galleryDots');
    const scene = document.querySelector('.gallery-carousel-scene');

    if (!track || cards.length === 0) return;

    let activeIdx = 0;
    const total = cards.length;
    let autoInterval = null;

    // Sayfa Noktalarını (Dots) Oluştur
    if (dotsContainer) {
        dotsContainer.innerHTML = '';
        cards.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.className = `gallery-dot ${i === 0 ? 'active' : ''}`;
            dot.setAttribute('aria-label', `Ekran ${i + 1}`);
            dot.addEventListener('click', () => {
                activeIdx = i;
                updateCoverflow();
                resetAutoPlay();
            });
            dotsContainer.appendChild(dot);
        });
    }

    function updateCoverflow() {
        const dots = document.querySelectorAll('.gallery-dot');
        dots.forEach((d, i) => d.classList.toggle('active', i === activeIdx));

        const isMobile = window.innerWidth <= 768;
        const xOffset1 = isMobile ? 160 : 260;
        const xOffset2 = isMobile ? 260 : 440;
        const zOffset1 = isMobile ? -100 : -160;
        const zOffset2 = isMobile ? -180 : -300;

        cards.forEach((card, i) => {
            let diff = i - activeIdx;
            if (diff > total / 2) diff -= total;
            if (diff < -total / 2) diff += total;

            if (diff === 0) {
                card.style.transform = 'translateX(0) translateZ(0) rotateY(0deg) scale(1)';
                card.style.opacity = '1';
                card.style.zIndex = '15';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'none';
            } else if (diff === 1) {
                card.style.transform = `translateX(${xOffset1}px) translateZ(${zOffset1}px) rotateY(-24deg) scale(0.86)`;
                card.style.opacity = '0.85';
                card.style.zIndex = '10';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.92)';
            } else if (diff === -1) {
                card.style.transform = `translateX(-${xOffset1}px) translateZ(${zOffset1}px) rotateY(24deg) scale(0.86)`;
                card.style.opacity = '0.85';
                card.style.zIndex = '10';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.92)';
            } else if (diff === 2) {
                card.style.transform = `translateX(${xOffset2}px) translateZ(${zOffset2}px) rotateY(-36deg) scale(0.72)`;
                card.style.opacity = '0.45';
                card.style.zIndex = '6';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.8)';
            } else if (diff === -2) {
                card.style.transform = `translateX(-${xOffset2}px) translateZ(${zOffset2}px) rotateY(36deg) scale(0.72)`;
                card.style.opacity = '0.45';
                card.style.zIndex = '6';
                card.style.pointerEvents = 'auto';
                card.style.filter = 'brightness(0.8)';
            } else {
                const side = diff > 0 ? 1 : -1;
                card.style.transform = `translateX(${side * 600}px) translateZ(-500px) rotateY(${side * -45}deg) scale(0.5)`;
                card.style.opacity = '0';
                card.style.zIndex = '1';
                card.style.pointerEvents = 'none';
            }
        });
    }

    // Karta Tıklayınca Merkeze Getir
    cards.forEach((card, i) => {
        card.addEventListener('click', () => {
            if (activeIdx !== i) {
                activeIdx = i;
                updateCoverflow();
                resetAutoPlay();
            }
        });
    });

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            activeIdx = (activeIdx - 1 + total) % total;
            updateCoverflow();
            resetAutoPlay();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            activeIdx = (activeIdx + 1) % total;
            updateCoverflow();
            resetAutoPlay();
        });
    }

    // Dokunma (Touch/Swipe) Desteği
    let startX = 0;
    let endX = 0;
    if (scene) {
        scene.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
        }, { passive: true });

        scene.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            const diffX = startX - endX;
            if (Math.abs(diffX) > 40) {
                if (diffX > 0) {
                    activeIdx = (activeIdx + 1) % total;
                } else {
                    activeIdx = (activeIdx - 1 + total) % total;
                }
                updateCoverflow();
                resetAutoPlay();
            }
        }, { passive: true });
    }

    // Otomatik Döndürme
    function startAutoPlay() {
        if (autoInterval) clearInterval(autoInterval);
        autoInterval = setInterval(() => {
            activeIdx = (activeIdx + 1) % total;
            updateCoverflow();
        }, 5000);
    }

    function resetAutoPlay() {
        clearInterval(autoInterval);
        startAutoPlay();
    }

    if (scene) {
        scene.addEventListener('mouseenter', () => clearInterval(autoInterval));
        scene.addEventListener('mouseleave', () => startAutoPlay());
    }

    updateCoverflow();
    startAutoPlay();
    window.addEventListener('resize', updateCoverflow, { passive: true });
}

/* ==========================================================================
   12. SSS (Sıkça Sorulan Sorular / Accordion)
   ========================================================================== */
function initFaqAccordion() {
    const items = document.querySelectorAll('.faq-item');

    items.forEach(item => {
        const btn = item.querySelector('.faq-question-btn');
        const panel = item.querySelector('.faq-answer-panel');

        if (!btn || !panel) return;

        btn.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Diğer tüm açık panelleri kapat
            items.forEach(other => {
                if (other !== item) {
                    other.classList.remove('active');
                    const otherPanel = other.querySelector('.faq-answer-panel');
                    if (otherPanel) otherPanel.style.maxHeight = '0px';
                }
            });

            if (isActive) {
                item.classList.remove('active');
                panel.style.maxHeight = '0px';
            } else {
                item.classList.add('active');
                panel.style.maxHeight = panel.scrollHeight + 'px';
            }
        });
    });
}

