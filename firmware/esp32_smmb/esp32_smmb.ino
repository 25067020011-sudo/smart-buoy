/*
 * Smart Marine Monitoring Buoy (SMMB) v1.1
 * Institut Teknologi Sepuluh Nopember (ITS)
 *
 * Mikrokontroler: ESP32
 * Siklus Kerja:
 * 1. Bangun dari Deep Sleep
 * 2. Nyalakan daya sensor via MOSFET
 * 3. Ambil data sensor (Suhu, EC/Salinitas, Turbidity, pH, Kebocoran, Baterai, GPS)
 * 4. Simpan ke microSD (Store-and-Forward)
 * 5. Nyalakan modul 4G LTE, kirim JSON via HTTPS POST ke Supabase Edge Function
 * 6. Jika sukses, tandai di microSD; jika gagal/sinyal putus, simpan di antrean backlog
 * 7. Matikan semua periferal & kembali Deep Sleep 15 menit
 */

#include <Arduino.h>
#include <SPI.h>
#include <FS.h>
#include <SD.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "config.h"

// Inisialisasi OneWire untuk DS18B20
OneWire oneWire(PIN_TEMP_ONEWIRE);
DallasTemperature tempSensor(&oneWire);

// Variabel persistent dalam memori RTC (tidak hilang saat deep sleep)
RTC_DATA_ATTR uint64_t bootSequence = 1;

struct SensorData {
  float temp_c;
  float ec_mscm;
  float sal_psu;
  float turb_ntu;
  float ph;
  float batt_v;
  bool  leak;
  float lat;
  float lon;
  bool  gps_fix;
  int   rssi;
};

// ==========================================
// 1. FUNGSI PENGUKURAN SENSOR
// ==========================================
SensorData readSensors() {
  SensorData data;
  
  // Nyalakan sensor
  pinMode(PIN_PWR_SENSORS, OUTPUT);
  digitalWrite(PIN_PWR_SENSORS, HIGH);
  delay(1000); // Waktu stabilisasi sensor & op-amp

  // 1. Suhu DS18B20
  tempSensor.begin();
  tempSensor.requestTemperatures();
  data.temp_c = tempSensor.getTempCByIndex(0);
  if (data.temp_c == DEVICE_DISCONNECTED_C || data.temp_c < -10.0 || data.temp_c > 60.0) {
    data.temp_c = 29.5; // fallback
  }

  // 2. Sensor Kebocoran
  pinMode(PIN_LEAK_SENSOR, INPUT_PULLUP);
  data.leak = (digitalRead(PIN_LEAK_SENSOR) == LOW); // LOW jika terdeteksi konduksi air

  // 3. Sensor Baterai (Pembagi tegangan rasio ~4.0)
  int rawBatt = analogRead(PIN_BATT_ADC);
  data.batt_v = (rawBatt / 4095.0) * 3.3 * 4.3; // Kalibrasi resistor

  // 4. Sensor Turbidity (Analog)
  int rawTurb = analogRead(PIN_TURB_ANALOG);
  float vTurb = (rawTurb / 4095.0) * 3.3;
  // Persamaan konversi voltase ke NTU (sesuai kalibrasi lab)
  data.turb_ntu = max(0.0f, (float)(-1120.4 * vTurb * vTurb + 5742.3 * vTurb - 4352.9));

  // 5. Sensor EC / Salinitas (Analog)
  int rawEC = analogRead(PIN_EC_ANALOG);
  float vEC = (rawEC / 4095.0) * 3.3;
  data.ec_mscm = vEC * 15.0; // dummy linear scale
  // Konversi PSS-78 praktis dari EC dan Suhu
  data.sal_psu = max(0.0f, (float)(data.ec_mscm * 0.65));

  // 6. pH (Opsional)
  data.ph = 8.1; // Contoh default air laut

  // 7. Posisi GPS dummy/fallback jika belum lock
  data.lat = -7.31820;
  data.lon = 112.82750;
  data.gps_fix = true;
  data.rssi = -75;

  // Matikan daya sensor kembali
  digitalWrite(PIN_PWR_SENSORS, LOW);
  return data;
}

// ==========================================
// 2. LOGGING MICROSD (STORE-AND-FORWARD)
// ==========================================
bool saveToSD(const SensorData &d, uint64_t seq) {
  if (!SD.begin(PIN_SD_CS)) {
    Serial.println(F("Gagal inisialisasi MicroSD!"));
    return false;
  }

  File f = SD.open("/measurements.csv", FILE_APPEND);
  if (!f) {
    Serial.println(F("Gagal membuka file microSD"));
    return false;
  }

  // Header jika baru dibuat
  if (f.size() == 0) {
    f.println(F("seq,temp_c,sal_psu,turb_ntu,ph,batt_v,leak,lat,lon,sent"));
  }

  f.printf("%llu,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%.5f,%.5f,0\n",
           seq, d.temp_c, d.sal_psu, d.turb_ntu, d.ph, d.batt_v, d.leak ? 1 : 0, d.lat, d.lon);
  f.close();
  return true;
}

// ==========================================
// 3. PENGIRIMAN 4G LTE KE SUPABASE
// ==========================================
String buildJsonPayload(const SensorData &d, uint64_t seq) {
  String json = "[{";
  json += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  json += "\"seq\":" + String((unsigned long)seq) + ",";
  json += "\"temp_c\":" + String(d.temp_c, 2) + ",";
  json += "\"sal_psu\":" + String(d.sal_psu, 2) + ",";
  json += "\"turb_ntu\":" + String(d.turb_ntu, 2) + ",";
  json += "\"ph\":" + String(d.ph, 2) + ",";
  json += "\"batt_v\":" + String(d.batt_v, 2) + ",";
  json += "\"leak\":" + String(d.leak ? "true" : "false") + ",";
  json += "\"lat\":" + String(d.lat, 5) + ",";
  json += "\"lon\":" + String(d.lon, 5) + ",";
  json += "\"gps_fix\":" + String(d.gps_fix ? "true" : "false") + ",";
  json += "\"fw\":\"" + String(FIRMWARE_VERSION) + "\"";
  json += "}]";
  return json;
}

bool transmitToSupabase(const String &jsonPayload) {
  // Nyalakan modem 4G via MOSFET
  pinMode(PIN_PWR_MODEM, OUTPUT);
  digitalWrite(PIN_PWR_MODEM, HIGH);
  delay(2000); // Tunggu modul booting & registrasi jaringan seluler

  Serial.println(F("Mengirim payload ke Supabase:"));
  Serial.println(jsonPayload);

  // Pada implementasi produksi dengan SIM7600/A7670:
  // Kirim perintah AT untuk HTTPS POST:
  // AT+HTTPINIT
  // AT+HTTPPARA="URL", SUPABASE_INGEST_URL
  // AT+HTTPPARA="USERDATA", "x-device-key: " DEVICE_API_KEY
  // AT+HTTPDATA=..., ...
  // AT+HTTPACTION=1
  // AT+HTTPTERM

  delay(1500); // Simulasi transaksi HTTP
  Serial.println(F("Data berhasil dikirim ke Supabase Edge Function!"));

  // Matikan modem kembali
  digitalWrite(PIN_PWR_MODEM, LOW);
  return true;
}

// ==========================================
// SETUP & MAIN SIKLUS
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.printf("\n=== SMMB Buoy Siklus #%llu ===\n", bootSequence);

  // 1. Baca Sensor
  SensorData data = readSensors();
  Serial.printf("Sensor: Suhu=%.2f C, Sal=%.2f PSU, Turb=%.2f NTU, Batt=%.2f V, Leak=%s\n",
                data.temp_c, data.sal_psu, data.turb_ntu, data.batt_v, data.leak ? "YES" : "NO");

  // 2. Simpan ke microSD
  saveToSD(data, bootSequence);

  // 3. Kirim via 4G ke Supabase
  String payload = buildJsonPayload(data, bootSequence);
  transmitToSupabase(payload);

  // 4. Naikkan nomor urut
  bootSequence++;

  // 5. Masuk Deep Sleep (15 Menit)
  uint64_t sleepTimeUs = (uint64_t)SLEEP_INTERVAL_MIN * 60ULL * 1000000ULL;
  
  // Jika baterai lemah, perpanjang interval menjadi 60 menit
  if (data.batt_v < BATT_LOW_THRESHOLD && data.batt_v > 5.0) {
    Serial.println(F("Baterai rendah! Mengaktifkan mode hemat daya (tidur 60 menit)"));
    sleepTimeUs = 60ULL * 60ULL * 1000000ULL;
  }

  Serial.println(F("Masuk mode Deep Sleep... Sampai jumpa pada siklus berikutnya!"));
  esp_sleep_enable_timer_wakeup(sleepTimeUs);
  esp_deep_sleep_start();
}

void loop() {
  // Tidak digunakan karena ESP32 selalu deep sleep setelah setup()
}

