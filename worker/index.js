/**
 * ezan-plus-tetikleyici — Cloudflare Worker Zamanlayıcı
 * Günde 6 kez (11:30, 13:45, 16:30, 18:45, 20:30, 22:00 TSİ) GitHub Actions'ı sıfır gecikmeyle tetikler.
 */

export default {
  async scheduled(event, env, ctx) {
    if (!env.GITHUB_PAT || !env.GITHUB_REPO) {
      console.error("GITHUB_PAT veya GITHUB_REPO eksik!");
      return;
    }

    const now = new Date();
    const utcHours = now.getUTCHours();
    const utcMinutes = now.getUTCMinutes();
    const tsiHours = (utcHours + 3) % 24;
    const saatEtiket = `${String(tsiHours).padStart(2, '0')}:${String(utcMinutes).padStart(2, '0')} TSİ`;

    // 6 Dağıtım Slotu Eşlemesi (Exact Cron & Saat Yedekli)
    let tur = null;
    let slotAdi = null;
    const cron = event.cron;

    if (cron === "30 8 * * *" || (utcHours === 8 && utcMinutes >= 25 && utcMinutes <= 35)) {
      tur = "reels";
      slotAdi = "1. Slot: Kur'an Tilaveti Reels 1 (11:30 TSİ)";
    } else if (cron === "45 10 * * *" || (utcHours === 10 && utcMinutes >= 40 && utcMinutes <= 50)) {
      tur = "hadis";
      slotAdi = "2. Slot: Sahih Hadis-i Şerif Kartı (13:45 TSİ)";
    } else if (cron === "30 13 * * *" || (utcHours === 13 && utcMinutes >= 25 && utcMinutes <= 35)) {
      tur = "reels";
      slotAdi = "3. Slot: Kur'an Tilaveti Reels 2 (16:30 TSİ)";
    } else if (cron === "45 15 * * *" || (utcHours === 15 && utcMinutes >= 40 && utcMinutes <= 50)) {
      tur = "dua";
      slotAdi = "4. Slot: Günün Duası Kartı (18:45 TSİ)";
    } else if (cron === "30 17 * * *" || (utcHours === 17 && utcMinutes >= 25 && utcMinutes <= 35)) {
      tur = "reels";
      slotAdi = "5. Slot: Kur'an Tilaveti Reels 3 (20:30 TSİ)";
    } else if (cron === "0 19 * * *" || (utcHours === 19 && utcMinutes >= 0 && utcMinutes <= 10)) {
      tur = "kelime";
      slotAdi = "6. Slot: Kur'an Sözlüğü Kartı (22:00 TSİ)";
    } else {
      console.log(`[Zamanlayıcı] ${saatEtiket} (cron: ${cron}) - Aktif bir yayın slotu yok, atlanıyor.`);
      return;
    }

    const url = `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`;
    console.log(`[Zamanlayıcı] GitHub Actions tetikleniyor: ${env.GITHUB_REPO} (${saatEtiket} - ${tur.toUpperCase()} - ${slotAdi})`);

    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${env.GITHUB_PAT}`,
        "User-Agent": "EzanPlus-CloudflareWorker",
      },
      body: JSON.stringify({
        event_type: "gunluk_yayin",
        client_payload: {
          tetikleyen: "cloudflare_cron",
          tur: tur,
          slot: slotAdi,
          saat: saatEtiket,
          cron: event.cron,
        },
      }),
    });

    console.log(`[Zamanlayıcı] Yanıt: ${res.status}`);
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Manuel test veya acil durum tetiklemesi: /tetikle?tur=reels|hadis|dua|kelime
    if (url.pathname === "/tetikle") {
      if (!env.GITHUB_PAT || !env.GITHUB_REPO) {
        return new Response("Hata: GITHUB_PAT veya GITHUB_REPO ayarlanmamış.", { status: 500 });
      }

      const tur = url.searchParams.get("tur") || "reels";
      const tema = url.searchParams.get("tema") || "";
      const auto = url.searchParams.get("auto") === "true";

      const ghUrl = `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`;
      const res = await fetch(ghUrl, {
        method: "POST",
        headers: {
          Accept: "application/vnd.github+json",
          Authorization: `Bearer ${env.GITHUB_PAT}`,
          "User-Agent": "EzanPlus-CloudflareWorker",
        },
        body: JSON.stringify({
          event_type: "gunluk_yayin",
          client_payload: {
            tetikleyen: "manuel_web",
            tur: tur,
            tema: tema,
            auto_publish: auto,
          },
        }),
      });

      return new Response(
        `✅ Ezan Plus ${tur.toUpperCase()} üretimi tetiklendi!\n` +
        `GitHub API Yanıt Kodu: ${res.status}\n` +
        `Parametreler: tur=${tur}, tema=${tema || 'otomatik'}, auto=${auto}`
      );
    }

    return new Response(
      "🕌 Ezan Plus 6 Dağıtım Slotu Zamanlayıcı Servisi Aktif.\n\n" +
      "📅 Günlük Çizelge:\n" +
      "1. 11:30 TSİ — Kur'an Tilaveti Reels 1\n" +
      "2. 13:45 TSİ — Sahih Hadis Kartı (4:5 + 9:16)\n" +
      "3. 16:30 TSİ — Kur'an Tilaveti Reels 2\n" +
      "4. 18:45 TSİ — Günün Duası Kartı (4:5 + 9:16)\n" +
      "5. 20:30 TSİ — Kur'an Tilaveti Reels 3\n" +
      "6. 22:00 TSİ — Kur'an Sözlüğü Kartı (4:5 + 9:16)\n\n" +
      "Manuel tetiklemek için: /tetikle?tur=reels (veya hadis, dua, kelime)"
    );
  },
};
