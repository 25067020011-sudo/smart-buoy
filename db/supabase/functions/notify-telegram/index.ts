// Supabase Edge Function: notify-telegram
// Dipanggil oleh Database Webhook saat ada baris baru di tabel `alerts`

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

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
    const record = payload.record;

    if (!record) {
      return new Response("No alert record in payload", { status: 400 });
    }

    const icon =
      record.type === "leak"
        ? "🚨 <b>AIR LAUT BOCOR!</b>"
        : record.type === "geofence"
        ? "⚓ <b>BUOY HANYUT / KELUAR GEOFENCE!</b>"
        : record.type === "battery_low"
        ? "🪫 <b>BATERAI LEMAH!</b>"
        : record.type === "no_data"
        ? "⚠️ <b>DATA TERHENTI &gt; 60 MENIT</b>"
        : "⚠️ <b>ALARM PERINGATAN</b>";

    const text = `
${icon}
━━━━━━━━━━━━━━━━━━━━
📍 <b>Perangkat:</b> <code>${escapeHtml(record.device_id)}</code>
🚨 <b>Jenis Alarm:</b> <b>${escapeHtml(record.type)}</b>
📝 <b>Pesan:</b> ${escapeHtml(record.message)}
⏱ <b>Waktu (UTC):</b> ${escapeHtml(record.triggered_at)}
${record.trigger_value ? `📊 <b>Nilai Pemicu:</b> ${escapeHtml(String(record.trigger_value))}` : ""}
━━━━━━━━━━━━━━━━━━━━
<i>Harap segera cek dashboard monitoring atau lakukan inspeksi lapangan!</i>
    `.trim();

    const telegramUrl = `https://api.telegram.org/bot${telegramToken}/sendMessage`;
    const res = await fetch(telegramUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: defaultChatId,
        text: text,
        parse_mode: "HTML",
      }),
    });

    const resJson = await res.json();
    if (!res.ok) {
      return new Response(JSON.stringify(resJson), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }

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
