// Supabase Edge Function: notify-telegram
// Dipanggil oleh Database Webhook saat ada baris baru di tabel `alerts`

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

serve(async (req) => {
  try {
    const telegramToken = Deno.env.get("TELEGRAM_BOT_TOKEN");
    const defaultChatId = Deno.env.get("TELEGRAM_CHAT_ID");

    if (!telegramToken || !defaultChatId) {
      return new Response(JSON.stringify({ error: "Missing Telegram credentials in env" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }

    const payload = await req.json();
    const record = payload.record; // Row from alerts table

    if (!record) {
      return new Response("No alert record in payload", { status: 400 });
    }

    const icon =
      record.type === "leak"
        ? "🚨 AIR LAUT BOCOR!"
        : record.type === "geofence"
        ? "⚓ BUOY HANYUT / KELUAR GEOFENCE!"
        : record.type === "battery_low"
        ? "🪫 BATERAI LEMAH!"
        : record.type === "no_data"
        ? "⚠️ DATA TERHENTI > 60 MENIT"
        : "⚠️ ALARM PERINGATAN";

    const text = `
${icon}
━━━━━━━━━━━━━━━━━━━━
📍 *Perangkat:* \`${record.device_id}\`
🚨 *Jenis Alarm:* *${record.type}*
📝 *Pesan:* ${record.message}
⏱ *Waktu (UTC):* ${record.triggered_at}
${record.trigger_value ? `📊 *Nilai Pemicu:* ${record.trigger_value}` : ""}
━━━━━━━━━━━━━━━━━━━━
_Harap segera cek dashboard monitoring atau lakukan inspeksi lapangan!_
    `.trim();

    const telegramUrl = `https://api.telegram.org/bot${telegramToken}/sendMessage`;
    const res = await fetch(telegramUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: defaultChatId,
        text: text,
        parse_mode: "Markdown",
      }),
    });

    const resJson = await res.json();
    return new Response(JSON.stringify(resJson), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});

