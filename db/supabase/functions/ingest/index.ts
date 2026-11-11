// Supabase Edge Function: ingest
// Endpoint: POST /functions/v1/ingest
// Menerima array record dari ESP32, verifikasi API Key, dan simpan ke Supabase

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.4";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-device-key",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const deviceKey = req.headers.get("x-device-key");
    if (!deviceKey) {
      return new Response(JSON.stringify({ error: "Missing x-device-key header" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Hash device key dengan SHA-256
    const msgUint8 = new TextEncoder().encode(deviceKey);
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const deviceKeyHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

    const body = await req.json();
    const records = Array.isArray(body) ? body : [body];

    if (records.length === 0) {
      return new Response(JSON.stringify({ error: "No records received" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const deviceId = records[0].device_id;

    // Verifikasi device dan hash key
    const { data: device, error: devErr } = await supabase
      .from("devices")
      .select("device_id, api_key_hash")
      .eq("device_id", deviceId)
      .single();

    if (devErr || !device || device.api_key_hash !== deviceKeyHash) {
      return new Response(JSON.stringify({ error: "Unauthorized device or invalid key" }), {
        status: 403,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const accepted: number[] = [];
    const duplicate: number[] = [];
    const rejected: number[] = [];

    for (const item of records) {
      try {
        const seq = item.seq;
        const tsUtc = item.ts || new Date().toISOString();

        // 1. Insert Measurement
        const { error: mErr } = await supabase.from("measurements").insert({
          device_id: deviceId,
          seq: seq,
          ts_utc: tsUtc,
          temp_c: item.temp_c ?? null,
          ec_mscm: item.ec_mscm ?? null,
          sal_psu: item.sal_psu ?? null,
          ph: item.ph ?? null,
          do_mgl: item.do_mgl ?? null,
          turb_ntu: item.turb_ntu ?? null,
          fw_version: item.fw ?? "1.0.0",
        });

        // 2. Insert Telemetry
        const { error: tErr } = await supabase.from("device_telemetry").insert({
          device_id: deviceId,
          seq: seq,
          ts_utc: tsUtc,
          lat: item.lat ?? null,
          lon: item.lon ?? null,
          gps_fix: Boolean(item.gps_fix),
          batt_v: item.batt_v ?? null,
          solar_v: item.solar_v ?? null,
          encl_temp_c: item.encl_temp_c ?? null,
          encl_rh: item.encl_rh ?? null,
          leak: Boolean(item.leak),
          rssi: item.rssi ?? null,
        });

        if (mErr && mErr.code === "23505") { // unique constraint violation (duplicate seq)
          duplicate.push(seq);
        } else if (mErr || tErr) {
          console.error("Insert error:", mErr || tErr);
          rejected.push(seq);
        } else {
          accepted.push(seq);
        }
      } catch (err) {
        console.error("Record processing error:", err);
        rejected.push(item.seq);
      }
    }

    return new Response(
      JSON.stringify({ accepted, duplicate, rejected }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

