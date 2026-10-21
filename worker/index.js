/**
 * ezan-plus-tetikleyici — Cloudflare Worker Zamanlayıcı
 * Günde 4 Altın Slot (08:30, 13:00, 17:00, 19:30 TSİ) GitHub Actions'ı sıfır gecikmeyle tetikler.
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

    // 4 Dağıtım Slotu Eşlemesi (Exact Cron & Saat Yedekli)
    let tur = null;
    let slotAdi = null;
    const cron = event.cron;

    if (cron === "30 5 * * *" || (utcHours === 5 && utcMinutes >= 25 && utcMinutes <= 35)) {
      tur = "kelime";
      slotAdi = "1. Slot: Kur'an Sözlüğü Kartı (08:30 TSİ)";
    } else if (cron === "0 10 * * *" || (utcHours === 10 && utcMinutes >= 0 && utcMinutes <= 10)) {
      tur = "reels";
      slotAdi = "2. Slot: Kur'an Tilaveti Reels (13:00 TSİ)";
    } else if (cron === "0 14 * * *" || (utcHours === 14 && utcMinutes >= 0 && utcMinutes <= 10)) {
      tur = "hadis";
      slotAdi = "3. Slot: Sahih Hadis-i Şerif (17:00 TSİ)";
    } else if (cron === "30 16 * * *" || (utcHours === 16 && utcMinutes >= 25 && utcMinutes <= 35)) {
      tur = "dua";
      slotAdi = "4. Slot: Günün Duası (19:30 TSİ)";
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
          auto_publish: true,
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
      const auto = url.searchParams.get("auto") !== "false";

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
      "🕌 Ezan Plus 4 Dağıtım Slotu Zamanlayıcı Servisi Aktif.\n\n" +
      "📅 Günlük Çizelge (TSİ):\n" +
      "1. 08:30 TSİ — 📚 Kur'an Sözlüğü Kartı (4:5 + 9:16)\n" +
      "2. 13:00 TSİ — 📖 Kur'an Tilaveti Reels (9:16)\n" +
      "3. 17:00 TSİ — 📜 Sahih Hadis-i Şerif (V20 Video)\n" +
      "4. 19:30 TSİ — 🤲 Günün Duası (V20 Video)\n\n" +
      "Manuel tetiklemek için: /tetikle?tur=reels (veya hadis, dua, kelime)"
    );
  },
};
