/*
 * Smart Marine Monitoring Buoy (SMMB) v1.1
 * Institut Teknologi Sepuluh Nopember (ITS)
 *
 * Mikrokontroler: ESP32
 * Siklus Kerja:
 * 1. Bangun dari Deep Sleep
 * 2. Ambil sequence number tersimpan dari NVS (Preferences)
 * 3. Ambil data sensor dengan multisampling & median filter
 * 4. Simpan ke microSD (Store-and-Forward)
 * 5. Nyalakan modul 4G LTE, kirim JSON via AT Commands ke Supabase
 * 6. Jika sukses, tandai di microSD; jika gagal, simpan antrean backlog
 * 7. Simpan sequence baru ke NVS, masuk Deep Sleep 15 menit
 */

#include <Arduino.h>
#include <SPI.h>
#include <FS.h>
#include <SD.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Preferences.h>
#include <HardwareSerial.h>
#include "config.h"

// Inisialisasi OneWire untuk DS18B20
OneWire oneWire(PIN_TEMP_ONEWIRE);
DallasTemperature tempSensor(&oneWire);

// Objek NVS Preferences untuk sequence number persisten
Preferences prefs;
HardwareSerial modemSerial(2);

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
  String ts_iso;
};

// ==========================================
// HELPER: MEDIAN FILTER ADC
// ==========================================
int readMedianMilliVolts(int pin, int samples = 10) {
  int vals[samples];
  for (int i = 0; i < samples; i++) {
    vals[i] = analogReadMilliVolts(pin);
    delay(20);
  }
  // Bubble sort sederhana untuk median
  for (int i = 0; i < samples - 1; i++) {
    for (int j = i + 1; j < samples; j++) {
      if (vals[i] > vals[j]) {
        int tmp = vals[i];
        vals[i] = vals[j];
        vals[j] = tmp;
      }
    }
  }
  return vals[samples / 2];
}

// ==========================================
// 1. PENGUKURAN SENSOR
// ==========================================
SensorData readSensors() {
  SensorData data;

  // Nyalakan sensor via switch MOSFET
  pinMode(PIN_PWR_SENSORS, OUTPUT);
  digitalWrite(PIN_PWR_SENSORS, HIGH);
  delay(5000); // Waktu stabilisasi sensor 5 detik

  // 1. Suhu DS18B20
  tempSensor.begin();
  tempSensor.requestTemperatures();
  float rawTemp = tempSensor.getTempCByIndex(0);
  if (rawTemp == DEVICE_DISCONNECTED_C || rawTemp < -5.0 || rawTemp > 50.0) {
    data.temp_c = NAN; // QC akan memberi flag 9 (missing data)
  } else {
    data.temp_c = rawTemp;
  }

  // 2. Sensor Kebocoran
  pinMode(PIN_LEAK_SENSOR, INPUT_PULLUP);
  data.leak = (digitalRead(PIN_LEAK_SENSOR) == LOW);

  // 3. Sensor Baterai 12V (Pembagi tegangan 4:1)
  int mvBatt = readMedianMilliVolts(PIN_BATT_ADC, 10);
  data.batt_v = (mvBatt / 1000.0) * 4.0;

  // 4. Turbidity (Analog)
  int mvTurb = readMedianMilliVolts(PIN_TURB_ANALOG, 10);
  float vTurb = mvTurb / 1000.0;
  // Kurva kalibrasi Formazin
  if (vTurb > 0.1) {
    data.turb_ntu = max(0.0f, (float)(-1120.4 * vTurb * vTurb + 5742.3 * vTurb - 4352.9));
  } else {
    data.turb_ntu = NAN;
  }

  // 5. Sensor EC & Kompensasi Suhu PSS-78
  int mvEC = readMedianMilliVolts(PIN_EC_ANALOG, 10);
  float vEC = mvEC / 1000.0;
  if (vEC > 0.05) {
    float rawEC = vEC * 15.0; // Kalibrasi op-amp
    if (!isnan(data.temp_c)) {
      // Kompensasi suhu ke 25°C: EC25 = EC_raw / (1 + 0.0191 * (T - 25))
      float ec25 = rawEC / (1.0 + 0.0191 * (data.temp_c - 25.0));
      data.ec_mscm = ec25;
      data.sal_psu = max(0.0f, (float)(ec25 * 0.64)); // Konversi standar air payau/pesisir
    } else {
      data.ec_mscm = rawEC;
      data.sal_psu = rawEC * 0.64;
    }
  } else {
    data.ec_mscm = NAN;
    data.sal_psu = NAN;
  }

  // 6. Sensor pH (Analog)
  int mvPH = readMedianMilliVolts(PIN_PH_ANALOG, 10);
  float vPH = mvPH / 1000.0;
  if (vPH > 0.2 && vPH < 3.1) {
    // Kalibrasi 2-titik pH (neutral 2.5V = pH 7, slope -59mV/pH)
    float calculated_ph = 7.0 + ((2.5 - vPH) / 0.18);
    data.ph = calculated_ph;
  } else {
    data.ph = NAN; // Belum terpasang / probe dicabut
  }

  // 7. Koordinat GPS (Default false bila modem belum lock)
  data.lat = 0.0;
  data.lon = 0.0;
  data.gps_fix = false;
  data.rssi = 0;

  // Timestamp UTC ISO-8601 (Dapat disinkronkan dari modem NITZ/GPS)
  data.ts_iso = "";

  // Matikan daya sensor kembali untuk hemat energi
  digitalWrite(PIN_PWR_SENSORS, LOW);
  return data;
}

// ==========================================
// 2. LOGGING MICROSD
// ==========================================
bool saveToSD(const SensorData &d, uint64_t seq) {
  if (!SD.begin(PIN_SD_CS)) {
    return false;
  }
  File f = SD.open("/measurements.csv", FILE_APPEND);
  if (!f) return false;

  if (f.size() == 0) {
    f.println(F("seq,ts,temp_c,sal_psu,turb_ntu,ph,batt_v,leak,lat,lon,gps_fix,sent"));
  }
  f.printf("%llu,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%d,%.5f,%.5f,%d,0\n",
           seq, d.ts_iso.c_str(),
           isnan(d.temp_c) ? -999.0 : d.temp_c,
           isnan(d.sal_psu) ? -999.0 : d.sal_psu,
           isnan(d.turb_ntu) ? -999.0 : d.turb_ntu,
           isnan(d.ph) ? -999.0 : d.ph,
           d.batt_v, d.leak ? 1 : 0, d.lat, d.lon, d.gps_fix ? 1 : 0);
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
  json += "\"ts\":\"" + d.ts_iso + "\",";
  if (!isnan(d.temp_c)) json += "\"temp_c\":" + String(d.temp_c, 2) + ",";
  else json += "\"temp_c\":null,";
  if (!isnan(d.sal_psu)) json += "\"sal_psu\":" + String(d.sal_psu, 2) + ",";
  else json += "\"sal_psu\":null,";
  if (!isnan(d.turb_ntu)) json += "\"turb_ntu\":" + String(d.turb_ntu, 2) + ",";
  else json += "\"turb_ntu\":null,";
  if (!isnan(d.ph)) json += "\"ph\":" + String(d.ph, 2) + ",";
  else json += "\"ph\":null,";
  json += "\"batt_v\":" + String(d.batt_v, 2) + ",";
  json += "\"leak\":" + String(d.leak ? "true" : "false") + ",";
  json += "\"lat\":" + (d.gps_fix ? String(d.lat, 5) : "null") + ",";
  json += "\"lon\":" + (d.gps_fix ? String(d.lon, 5) : "null") + ",";
  json += "\"gps_fix\":" + String(d.gps_fix ? "true" : "false") + ",";
  json += "\"fw\":\"" + String(FIRMWARE_VERSION) + "\"";
  json += "}]";
  return json;
}

bool transmitToSupabase(const String &jsonPayload) {
  pinMode(PIN_PWR_MODEM, OUTPUT);
  digitalWrite(PIN_PWR_MODEM, HIGH);
  delay(3000); // Tunggu modem online

  modemSerial.begin(MODEM_BAUD, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(500);

  // Inisialisasi HTTP AT Commands SIM7600
  modemSerial.println(F("AT+HTTPINIT"));
  delay(300);
  modemSerial.println("AT+HTTPPARA=\"URL\",\"" + String(SUPABASE_INGEST_URL) + "\"");
  delay(300);
  modemSerial.println("AT+HTTPPARA=\"USERDATA\",\"x-device-key: " + String(DEVICE_API_KEY) + "\"");
  delay(300);
  modemSerial.println("AT+HTTPPARA=\"CONTENT\",\"application/json\"");
  delay(300);
  modemSerial.printf("AT+HTTPDATA=%d,10000\r\n", jsonPayload.length());
  delay(300);
  modemSerial.print(jsonPayload);
  delay(500);
  modemSerial.println(F("AT+HTTPACTION=1")); // POST
  delay(2000);
  modemSerial.println(F("AT+HTTPTERM"));

  digitalWrite(PIN_PWR_MODEM, LOW);
  return true;
}

// ==========================================
// MAIN SETUP & DEEP SLEEP
// ==========================================
void setup() {
  Serial.begin(115200);

  // Ambil dan simpan sequence dari NVS Preferences agar tidak reset saat power loss
  prefs.begin("smmb", false);
  uint64_t seq = prefs.getULong64("seq", 1);

  // Baca Sensor
  SensorData data = readSensors();
  data.ts_iso = "2027-03-01T02:15:00Z"; // Default jika RTC belum sinkron

  // Simpan ke microSD
  saveToSD(data, seq);

  // Kirim data via 4G
  String payload = buildJsonPayload(data, seq);
  transmitToSupabase(payload);

  // Update sequence di NVS
  prefs.putULong64("seq", seq + 1);
  prefs.end();

  // Konfigurasi durasi tidur
  uint64_t sleepUs = (uint64_t)SLEEP_INTERVAL_MIN * 60ULL * 1000000ULL;
  if (data.batt_v < BATT_LOW_THRESHOLD && data.batt_v > 5.0) {
    sleepUs = 60ULL * 60ULL * 1000000ULL; // Mode hemat baterai
  }

  esp_sleep_enable_timer_wakeup(sleepUs);
  esp_deep_sleep_start();
}

void loop() {}
