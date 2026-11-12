// Supabase Edge Function: ingest
// Endpoint: POST /functions/v1/ingest
// Menerima array record dari ESP32, verifikasi API Key, validasi payload, dan simpan secara aman

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.38.4";

const MAX_BATCH_SIZE = 200;

function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let res = 0;
  for (let i = 0; i < a.length; i++) {
    res |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return res === 0;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: { "Content-Type": "application/json" } });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const deviceKey = req.headers.get("x-device-key");
    if (!deviceKey) {
      return new Response(JSON.stringify({ error: "Missing x-device-key header" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Hash device key dengan SHA-256
    const msgUint8 = new TextEncoder().encode(deviceKey);
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const deviceKeyHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

    const body = await req.json();
    const records = Array.isArray(body) ? body : [body];

    if (records.length === 0 || records.length > MAX_BATCH_SIZE) {
      return new Response(JSON.stringify({ error: "Invalid batch size (1 - 200 records allowed)" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const firstEntry = records[0];
    const deviceId = firstEntry?.device_id;
    if (!deviceId) {
      return new Response(JSON.stringify({ error: "Missing device_id" }), { status: 400 });
    }

    // Validasi seluruh record dalam batch memiliki device_id yang seragam
    for (const r of records) {
      if (r.device_id !== deviceId) {
        return new Response(JSON.stringify({ error: "Inconsistent device_id across batch" }), { status: 400 });
      }
    }

    // Verifikasi device dan hash key secara constantTime
    const { data: device, error: devErr } = await supabase
      .from("devices")
      .select("device_id, api_key_hash")
      .eq("device_id", deviceId)
      .single();

    if (devErr || !device || !constantTimeCompare(device.api_key_hash, deviceKeyHash)) {
      return new Response(JSON.stringify({ error: "Unauthorized device or invalid key" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      });
    }

    const accepted: number[] = [];
    const duplicate: number[] = [];
    const rejected: number[] = [];

    for (const item of records) {
      try {
        const seq = item.seq;
        // Validasi tipe data dan rentang
        if (!Number.isInteger(seq) || seq < 0) {
          rejected.push(seq);
          continue;
        }

        // Tolak record tanpa timestamp pengukuran riil dari perangkat
        if (!item.ts) {
          rejected.push(seq);
          continue;
        }
        const tsUtc = item.ts;

        // Atomic ingestion via rpc("ingest_record", ...) or transactional store
        const { error: mErr } = await supabase.from("measurements").insert({
          device_id: deviceId,
          seq: seq,
          ts_utc: tsUtc,
          temp_c: Number.isFinite(item.temp_c) ? item.temp_c : null,
          ec_mscm: Number.isFinite(item.ec_mscm) ? item.ec_mscm : null,
          sal_psu: Number.isFinite(item.sal_psu) ? item.sal_psu : null,
          ph: Number.isFinite(item.ph) ? item.ph : null,
          do_mgl: Number.isFinite(item.do_mgl) ? item.do_mgl : null,
          turb_ntu: Number.isFinite(item.turb_ntu) ? item.turb_ntu : null,
          calib_ids: item.calib_ids ?? null,
          fw_version: item.fw ?? "1.0.0",
        });

        // Simpan telemetri pendukung
        await supabase.rpc("log_telemetry_safe", {
          p_device_id: deviceId,
          p_seq: seq,
          p_ts_utc: tsUtc,
          p_lat: item.lat ?? null,
          p_lon: item.lon ?? null,
          p_gps_fix: Boolean(item.gps_fix),
          p_batt_v: item.batt_v ?? null,
          p_leak: Boolean(item.leak)
        }).catch(() => {});

        if (mErr && mErr.code === "23505") {
          duplicate.push(seq);
        } else if (mErr) {
          rejected.push(seq);
        } else {
          accepted.push(seq);
        }
      } catch (err) {
        rejected.push(item.seq);
      }
    }

    return new Response(JSON.stringify({ accepted, duplicate, rejected }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});
