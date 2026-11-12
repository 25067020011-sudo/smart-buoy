-- ==============================================================================
-- SMMB (Smart Marine Monitoring Buoy) — Database Schema & Triggers
-- Platform: Supabase (PostgreSQL 15+)
-- ==============================================================================

-- 1. ENUM TYPES
create type user_role     as enum ('admin', 'researcher', 'supervisor', 'technician');
create type device_status as enum ('planned', 'testing', 'deployed', 'maintenance', 'retired', 'lost');
create type wq_parameter  as enum ('temp', 'ec', 'salinity', 'turbidity', 'ph', 'do');
create type qc_test       as enum ('gross_range', 'spike', 'flat_line', 'rate_of_change');
create type tide_phase    as enum ('high', 'ebb', 'low', 'flood', 'unknown');
create type alert_type    as enum ('geofence', 'battery_low', 'no_data', 'out_of_range', 'leak');
create type alert_status  as enum ('open', 'acknowledged', 'resolved');

-- 2. TABLES

-- 2.1 Profiles (Pengguna)
create table if not exists profiles (
  id               uuid primary key references auth.users(id) on delete cascade,
  full_name        text not null,
  role             user_role not null default 'researcher',
  telegram_chat_id text,
  created_at       timestamptz not null default now()
);

-- 2.2 Devices (Buoy)
create table if not exists devices (
  device_id     text primary key,                      -- contoh: 'SMMB-01'
  name          text not null,
  status        device_status not null default 'planned',
  anchor_lat    double precision,                      -- Titik tambat
  anchor_lon    double precision,
  geofence_m    integer not null default 50 check (geofence_m > 0),
  interval_min  integer not null default 15 check (interval_min between 1 and 240),
  batt_low_v    numeric(4,2) not null default 11.80,
  api_key_hash  text not null,                         -- SHA-256 hash API key perangkat
  installed_at  timestamptz,
  created_at    timestamptz not null default now()
);

-- 2.3 Sensors (Sensor fisik terpasang)
create table if not exists sensors (
  sensor_id    uuid primary key default gen_random_uuid(),
  device_id    text not null references devices(device_id) on delete cascade,
  parameter    wq_parameter not null,
  model        text not null,
  serial_no    text,
  unit         text not null,
  range_min    numeric,
  range_max    numeric,
  installed_at timestamptz not null default now(),
  removed_at   timestamptz,
  check (removed_at is null or removed_at > installed_at)
);
create unique index if not exists sensors_one_active
  on sensors (device_id, parameter) where removed_at is null;

-- 2.4 Calibrations
create table if not exists calibrations (
  calib_id      uuid primary key default gen_random_uuid(),
  sensor_id     uuid not null references sensors(sensor_id) on delete cascade,
  calibrated_at timestamptz not null,
  method        text not null,
  standards     jsonb not null,
  coefficients  jsonb not null,
  performed_by  uuid references profiles(id),
  valid_from    timestamptz not null,
  valid_to      timestamptz,
  notes         text
);
create index if not exists idx_calibrations_sensor on calibrations (sensor_id, valid_from desc);

-- 2.5 Measurements (Data kualitas air per siklus)
create table if not exists measurements (
  id          bigint generated always as identity primary key,
  device_id   text not null references devices(device_id),
  seq         bigint not null,
  ts_utc      timestamptz not null,
  received_at timestamptz not null default now(),
  temp_c      numeric(5,2),
  ec_mscm     numeric(6,2),
  sal_psu     numeric(5,2),
  ph          numeric(4,2),
  do_mgl      numeric(5,2),
  turb_ntu    numeric(7,2),
  fw_version  text,
  calib_ids   jsonb,
  qc_flags    jsonb not null default '{}'::jsonb,
  unique (device_id, seq)
);
create index if not exists idx_measurements_ts on measurements (device_id, ts_utc desc);

-- 2.6 Device Telemetry (Kesehatan perangkat)
create table if not exists device_telemetry (
  id                 bigint generated always as identity primary key,
  device_id          text not null references devices(device_id),
  seq                bigint not null,
  ts_utc             timestamptz not null,
  lat                double precision,
  lon                double precision,
  gps_fix            boolean not null default false,
  dist_from_anchor_m numeric(8,1),
  batt_v             numeric(4,2),
  solar_v            numeric(4,2),
  encl_temp_c        numeric(4,1),
  encl_rh            numeric(4,1),
  leak               boolean not null default false,
  rssi               integer,
  unique (device_id, seq)
);
create index if not exists idx_telemetry_ts on device_telemetry (device_id, ts_utc desc);

-- 2.7 Field Visits (Kunjungan lapangan & pembersihan)
create table if not exists field_visits (
  visit_id      uuid primary key default gen_random_uuid(),
  device_id     text not null references devices(device_id),
  visit_at      timestamptz not null,
  tide_phase    tide_phase not null default 'unknown',
  weather       text,
  activities    text[] not null default '{}',
  fouling_score smallint check (fouling_score between 0 and 4),
  photo_paths   text[] not null default '{}',
  notes         text,
  created_by    uuid references profiles(id),
  created_at    timestamptz not null default now()
);

-- 2.8 Reference Measurements (Hasil MPV / Alat Lab)
create table if not exists reference_measurements (
  id                     uuid primary key default gen_random_uuid(),
  visit_id               uuid not null references field_visits(visit_id) on delete cascade,
  matched_measurement_id bigint references measurements(id),
  measured_at            timestamptz not null,
  parameter              wq_parameter not null,
  value                  numeric not null,
  unit                   text not null,
  instrument             text not null,
  depth_m                numeric(4,2)
);
create index if not exists idx_ref_param_measured on reference_measurements (parameter, measured_at);

-- 2.9 QC Thresholds
create table if not exists qc_thresholds (
  id        integer generated always as identity primary key,
  device_id text not null references devices(device_id) on delete cascade,
  parameter wq_parameter not null,
  test      qc_test not null,
  params    jsonb not null,
  active    boolean not null default true,
  unique (device_id, parameter, test)
);

-- 2.10 Alerts
create table if not exists alerts (
  id            bigint generated always as identity primary key,
  device_id     text not null references devices(device_id),
  type          alert_type not null,
  triggered_at  timestamptz not null default now(),
  trigger_value numeric,
  message       text not null,
  status        alert_status not null default 'open',
  handled_by    uuid references profiles(id),
  resolved_at   timestamptz
);
create unique index if not exists alerts_one_open
  on alerts (device_id, type) where status <> 'resolved';

-- 3. FUNCTIONS & TRIGGERS

-- 3.1 Haversine Distance (meter)
create or replace function haversine_m(lat1 float8, lon1 float8, lat2 float8, lon2 float8)
returns float8 language sql immutable as $$
  select 2 * 6371000 * asin(sqrt(
    power(sin(radians(lat2 - lat1) / 2), 2) +
    cos(radians(lat1)) * cos(radians(lat2)) * power(sin(radians(lon2 - lon1) / 2), 2)
  ));
$$;

-- 3.2 Telemetry Trigger (Geofence, Baterai, Kebocoran)
create or replace function telemetry_before_insert()
returns trigger language plpgsql security definer as $$
declare d devices;
begin
  select * into d from devices where device_id = new.device_id;

  if new.gps_fix and d.anchor_lat is not null then
    new.dist_from_anchor_m := haversine_m(d.anchor_lat, d.anchor_lon, new.lat, new.lon);
    if new.dist_from_anchor_m > d.geofence_m then
      insert into alerts (device_id, type, trigger_value, message)
      values (new.device_id, 'geofence', new.dist_from_anchor_m,
              format('Buoy %s berada %s m dari titik tambat', new.device_id, round(new.dist_from_anchor_m)))
      on conflict do nothing;
    end if;
  end if;

  if new.batt_v is not null and new.batt_v < d.batt_low_v then
    insert into alerts (device_id, type, trigger_value, message)
    values (new.device_id, 'battery_low', new.batt_v,
            format('Baterai %s V di bawah ambang %s V', new.batt_v, d.batt_low_v))
    on conflict do nothing;
  end if;

  if new.leak then
    insert into alerts (device_id, type, message)
    values (new.device_id, 'leak', 'Sensor kebocoran enclosure terpicu')
    on conflict do nothing;
  end if;

  return new;
end $$;

drop trigger if exists trg_telemetry on device_telemetry;
create trigger trg_telemetry before insert on device_telemetry
for each row execute function telemetry_before_insert();

-- 3.3 Measurements QC Gross Range Trigger
create or replace function measurements_qc_gross_range()
returns trigger language plpgsql as $$
declare
  t record;
  v numeric;
  col text;
  flags jsonb := '{}'::jsonb;
begin
  for t in
    select parameter, params from qc_thresholds
    where device_id = new.device_id and test = 'gross_range' and active
  loop
    col := case t.parameter
             when 'temp' then 'temp_c'       when 'ec' then 'ec_mscm'
             when 'salinity' then 'sal_psu'  when 'turbidity' then 'turb_ntu'
             when 'ph' then 'ph'             when 'do' then 'do_mgl' end;
    v := (to_jsonb(new) ->> col)::numeric;
    flags := flags || jsonb_build_object(col,
      case when v is null then 9
           when v < (t.params->>'min')::numeric or v > (t.params->>'max')::numeric then 4
           else 1 end);
  end loop;
  new.qc_flags := new.qc_flags || flags;
  return new;
end $$;

drop trigger if exists trg_measurements_qc on measurements;
create trigger trg_measurements_qc before insert on measurements
for each row execute function measurements_qc_gross_range();

-- QARTOD tests evaluation logic: 'spike', 'rate_of_change', 'flat_line'
-- Job pg_cron untuk mendeteksi alarm 'no_data' jika buoy terhenti > 60 menit
-- select cron.schedule('check-no-data', '*/15 * * * *', $$
--   insert into alerts (device_id, type, message)
--   select d.device_id, 'no_data', 'Data terhenti > 60 menit' from devices d
--   where d.status = 'deployed' and not exists (
--     select 1 from measurements m where m.device_id = d.device_id and m.received_at > now() - interval '60 minutes'
--   ) on conflict do nothing;
-- $$);

-- 4. VIEWS
alter table profiles enable row level security;
alter table devices enable row level security;
alter table sensors enable row level security;
alter table calibrations enable row level security;
alter table measurements enable row level security;
alter table device_telemetry enable row level security;
alter table field_visits enable row level security;
alter table reference_measurements enable row level security;
alter table qc_thresholds enable row level security;
alter table alerts enable row level security;

-- Policies
create policy "Allow read measurements" on measurements for select using (true);
create policy "Allow read telemetry" on device_telemetry for select using (true);
create policy "Allow read devices" on devices for select using (true);
create policy "Allow read alerts" on alerts for select using (true);
create policy "Allow read field visits" on field_visits for select using (true);
create policy "Allow read reference measurements" on reference_measurements for select using (true);
create policy "Allow read calibrations" on calibrations for select using (true);
create policy "Allow read sensors" on sensors for select using (true);
create policy "Allow read qc thresholds" on qc_thresholds for select using (true);

-- 5. VIEWS

create or replace view v_public_measurements as
select m.device_id, m.ts_utc, m.temp_c, m.sal_psu, m.ph, m.do_mgl, m.turb_ntu,
       round(t.lat::numeric, 2) as lat_approx,
       round(t.lon::numeric, 2) as lon_approx
from measurements m
left join device_telemetry t using (device_id, seq)
where not exists (
  select 1 from jsonb_each_text(m.qc_flags) f where f.value::int in (3, 4)
);

create or replace view v_daily_availability as
select m.device_id,
       date_trunc('day', m.ts_utc) as day,
       count(*) as received,
       (1440 / d.interval_min) as expected,
       round(100.0 * count(*) / (1440 / d.interval_min), 1) as availability_pct
from measurements m
join devices d using (device_id)
group by m.device_id, date_trunc('day', m.ts_utc), d.interval_min;

create or replace view v_validation_pairs as
select r.parameter, r.measured_at, r.value as ref_value, r.instrument,
       case r.parameter
         when 'temp' then m.temp_c      when 'ec' then m.ec_mscm
         when 'salinity' then m.sal_psu when 'turbidity' then m.turb_ntu
         when 'ph' then m.ph            when 'do' then m.do_mgl end as sensor_value,
       m.ts_utc as sensor_ts, v.fouling_score
from reference_measurements r
join field_visits v using (visit_id)
join measurements m on m.id = r.matched_measurement_id;

-- 6. MATCHING FUNCTION (Referensi vs Sensor)
create or replace function match_reference_measurements()
returns trigger language plpgsql as $$
declare
  target_id bigint;
begin
  select id into target_id
  from measurements
  where device_id = (select device_id from field_visits where visit_id = new.visit_id)
    and abs(extract(epoch from (ts_utc - new.measured_at))) <= 450 -- dalam toleransi +- 7.5 menit
  order by abs(extract(epoch from (ts_utc - new.measured_at))) asc
  limit 1;

  new.matched_measurement_id := target_id;
  return new;
end $$;

drop trigger if exists trg_match_reference on reference_measurements;
create trigger trg_match_reference
before insert on reference_measurements
for each row execute function match_reference_measurements();

-- 7. INITIAL QC THRESHOLDS CONFIGURATION
-- Catatan: Perangkat dan kunci API didaftarkan via antarmuka admin / script provisi (tools/provision_device.py)
insert into qc_thresholds (device_id, parameter, test, params) values
  ('SMMB-01', 'temp',      'gross_range', '{"min":20,"max":40}'),
  ('SMMB-01', 'ec',        'gross_range', '{"min":0,"max":70}'),
  ('SMMB-01', 'salinity',  'gross_range', '{"min":0,"max":40}'),
  ('SMMB-01', 'turbidity', 'gross_range', '{"min":0,"max":1000}'),
  ('SMMB-01', 'ph',        'gross_range', '{"min":6.0,"max":9.5}'),
  ('SMMB-01', 'do',        'gross_range', '{"min":0,"max":15}')
on conflict (device_id, parameter, test) do nothing;

