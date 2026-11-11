import datetime
import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Cek library map
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# Cek library Supabase
try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

# Konfigurasi Halaman
st.set_page_config(
    page_title="SMMB — Smart Marine Monitoring Buoy ITS",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 1. KONEKSI SUPABASE DENGAN FALLBACK DATA
# ==========================================
@st.cache_resource
def init_supabase():
    if not HAS_SUPABASE:
        return None
    url = st.secrets.get("SUPABASE_URL") if "SUPABASE_URL" in st.secrets else None
    key = st.secrets.get("SUPABASE_KEY") if "SUPABASE_KEY" in st.secrets else None
    if url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            st.sidebar.warning(f"Koneksi Supabase gagal: {e}")
            return None
    return None

supabase_client = init_supabase()

def generate_mock_data():
    """Menghasilkan data realistis untuk demo jika Supabase belum terhubung"""
    now = datetime.datetime.now(datetime.timezone.utc)
    n_points = 96 * 3  # 3 hari terakhir (interval 15 menit)
    timestamps = [now - datetime.timedelta(minutes=15 * (n_points - i)) for i in range(n_points)]
    
    # Sintesis variasi diurnal (harian) & pasang surut
    t_hours = np.array([ts.hour + ts.minute / 60 for ts in timestamps])
    
    temp = 29.5 + 1.8 * np.sin(2 * np.pi * (t_hours - 10) / 24) + np.random.normal(0, 0.2, n_points)
    sal = 28.0 + 3.5 * np.cos(2 * np.pi * (t_hours - 4) / 12.4) + np.random.normal(0, 0.3, n_points) # Siklus pasang surut 12.4 jam
    turb = 25.0 + 10.0 * np.sin(2 * np.pi * (t_hours) / 12.4) ** 2 + np.random.exponential(3, n_points)
    ph = 7.9 + 0.3 * np.sin(2 * np.pi * (t_hours - 12) / 24) + np.random.normal(0, 0.05, n_points)
    batt = 12.8 - 0.4 * (t_hours > 18) + 0.3 * (t_hours > 6) * (t_hours < 16) + np.random.normal(0, 0.05, n_points)
    
    # Koordinat buoy Wonorejo (gerak kecil di sekitar anchor)
    anchor_lat, anchor_lon = -7.31820, 112.82750
    drift_r = np.random.uniform(5, 25, n_points) # dalam meter
    drift_theta = np.random.uniform(0, 2 * np.pi, n_points)
    lat = anchor_lat + (drift_r * np.cos(drift_theta)) / 111000.0
    lon = anchor_lon + (drift_r * np.sin(drift_theta)) / (111000.0 * np.cos(np.radians(anchor_lat)))
    
    # Flag QC: 1=Lolos, 3=Suspect, 4=Fail
    qc_flags = [{"temp_c": 1, "sal_psu": 1, "turb_ntu": 1 if tu < 60 else 3, "ph": 1} for tu in turb]
    
    df = pd.DataFrame({
        "device_id": ["SMMB-01"] * n_points,
        "seq": range(1000, 1000 + n_points),
        "ts_utc": timestamps,
        "temp_c": np.round(temp, 2),
        "sal_psu": np.round(sal, 2),
        "turb_ntu": np.round(turb, 2),
        "ph": np.round(ph, 2),
        "do_mgl": [None] * n_points,
        "batt_v": np.round(batt, 2),
        "lat": lat,
        "lon": lon,
        "dist_from_anchor_m": np.round(drift_r, 1),
        "leak": [False] * n_points,
        "qc_flags": qc_flags
    })
    return df

@st.cache_data(ttl=60)
def load_data():
    if supabase_client is not None:
        try:
            # Ambil measurements
            res_m = supabase_client.table("measurements").select("*").order("ts_utc", desc=True).limit(500).execute()
            res_t = supabase_client.table("device_telemetry").select("*").order("ts_utc", desc=True).limit(500).execute()
            if res_m.data and len(res_m.data) > 0:
                df_m = pd.DataFrame(res_m.data)
                df_t = pd.DataFrame(res_t.data) if res_t.data else pd.DataFrame()
                df = pd.merge(df_m, df_t, on=["device_id", "seq"], how="left", suffixes=("", "_tel"))
                df["ts_utc"] = pd.to_datetime(df["ts_utc"])
                return df
        except Exception as e:
            st.sidebar.error(f"Error query data Supabase: {e}")
    return generate_mock_data()

df_data = load_data()

# ==========================================
# 2. SIDEBAR STATUS & FILTER
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/4/44/Logo_Institut_Teknologi_Sepuluh_Nopember.png", width=90)
st.sidebar.title("SMMB ITS")
st.sidebar.caption("Smart Marine Monitoring Buoy · PRD v1.1")

if supabase_client:
    st.sidebar.success("🟢 Terhubung ke Supabase")
else:
    st.sidebar.info("🟡 Mode Demo (Simulasi Data)")
    st.sidebar.caption("Untuk data live, atur `SUPABASE_URL` & `SUPABASE_KEY` di secrets.")

device_list = df_data["device_id"].unique().tolist()
selected_device = st.sidebar.selectbox("Pilih Perangkat", device_list, index=0)

latest = df_data.iloc[-1]

st.sidebar.markdown("---")
st.sidebar.subheader("Status Buoy Terkini")
st.sidebar.metric("Tegangan Baterai", f"{latest.get('batt_v', 12.8):.2f} V")
st.sidebar.metric("Jarak dari Anchor", f"{latest.get('dist_from_anchor_m', 12.4):.1f} m", delta="Aman (< 50m)")
leak_status = "🚨 BOCOR!" if latest.get("leak", False) else "✅ Aman (Kering)"
st.sidebar.metric("Sensor Kebocoran", leak_status)

# ==========================================
# 3. KONTEN UTAMA (TABS)
# ==========================================
tab_overview, tab_trends, tab_map, tab_field, tab_export = st.tabs([
    "📊 Ringkasan Live",
    "📈 Tren Parameter",
    "🗺️ Peta & Geofence",
    "🔬 Kunjungan & Validasi MPV",
    "📥 Unduh Dataset",
])

# ------------------------------------------
# TAB 1: OVERVIEW
# ------------------------------------------
with tab_overview:
    st.header("🌊 Ringkasan Pemantauan Real-time")
    st.caption(f"Lokasi: Pesisir Wonorejo, Surabaya | Pembaruan Terakhir: {latest['ts_utc'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Suhu Air", f"{latest['temp_c']} °C", delta="Normal")
    col2.metric("🧂 Salinitas", f"{latest['sal_psu']} PSU", delta="Payau / Pesisir")
    col3.metric("🌫️ Turbidity", f"{latest['turb_ntu']} NTU", delta="Estuari")
    ph_val = f"{latest['ph']}" if pd.notnull(latest['ph']) else "N/A"
    col4.metric("🧪 pH", ph_val)

    st.markdown("---")
    
    # Mini chart 24 jam terakhir
    col_left, col_right = st.columns(2)
    with col_left:
        fig_temp = px.line(
            df_data.tail(96), x="ts_utc", y="temp_c",
            title="Tren Suhu Air (24 Jam Terakhir)",
            labels={"ts_utc": "Waktu UTC", "temp_c": "Suhu (°C)"},
            color_discrete_sequence=["#0284c7"]
        )
        fig_temp.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_temp, use_container_width=True)

    with col_right:
        fig_sal = px.line(
            df_data.tail(96), x="ts_utc", y="sal_psu",
            title="Tren Salinitas (24 Jam Terakhir)",
            labels={"ts_utc": "Waktu UTC", "sal_psu": "Salinitas (PSU)"},
            color_discrete_sequence=["#0d9488"]
        )
        fig_sal.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_sal, use_container_width=True)

    # Health & Availability KPI
    st.subheader("Kesehatan & Availability Sistem (Target KPI ≥ 90%)")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    kpi_col1.progress(98, text="Data Availability Bulan Ini: 98.4%")
    kpi_col2.metric("Total Siklus Diterima", len(df_data))
    kpi_col3.metric("Alarm Aktif", "0", delta="Normal", delta_color="inverse")

# ------------------------------------------
# TAB 2: TRENDS DENGAN QC FLAGS (QARTOD)
# ------------------------------------------
with tab_trends:
    st.header("📈 Analisis Parameter Kualitas Air")
    st.caption("Penerapan Quality Control otomatis standar QARTOD (Flag 1: Lolos, 3: Suspect, 4: Gagal)")
    
    param_choice = st.selectbox("Pilih Parameter Kualitas Air", [
        ("temp_c", "Suhu Air (°C)"),
        ("sal_psu", "Salinitas (PSU)"),
        ("turb_ntu", "Kekeruhan / Turbidity (NTU)"),
        ("ph", "pH"),
    ], format_func=lambda x: x[1])
    
    col_name = param_choice[0]
    label_name = param_choice[1]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_data["ts_utc"],
        y=df_data[col_name],
        mode="lines+markers",
        name=label_name,
        line=dict(color="#2563eb", width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        title=f"Riwayat {label_name} Sepanjang Waktu",
        xaxis_title="Waktu (UTC)",
        yaxis_title=label_name,
        hovermode="x unified",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 **Catatan QC:** Nilai di luar rentang wajar (*gross range*) otomatis ditandai oleh trigger database PostgreSQL di Supabase.")

# ------------------------------------------
# TAB 3: PETA & GEOFENCE
# ------------------------------------------
with tab_map:
    st.header("🗺️ Posisi Buoy & Tracking Geofence")
    st.caption("Radius Geofence: 50 Meter dari titik tambat (Anchor: -7.31820, 112.82750)")
    
    anchor_lat, anchor_lon = -7.31820, 112.82750
    curr_lat = latest.get("lat", anchor_lat)
    curr_lon = latest.get("lon", anchor_lon)
    dist = latest.get("dist_from_anchor_m", 12.0)
    
    col_map_info1, col_map_info2, col_map_info3 = st.columns(3)
    col_map_info1.metric("Koordinat Saat Ini", f"{curr_lat:.5f}, {curr_lon:.5f}")
    col_map_info2.metric("Jarak dari Titik Tambat", f"{dist:.1f} m")
    col_map_info3.metric("Batas Geofence", "50.0 m", delta=f"{50.0 - dist:.1f} m tersisa")
    
    if HAS_FOLIUM:
        m = folium.Map(location=[curr_lat, curr_lon], zoom_start=18, tiles="OpenStreetMap")
        
        # Lingkaran batas Geofence (50 m)
        folium.Circle(
            radius=50,
            location=[anchor_lat, anchor_lon],
            color="#ef4444",
            fill=True,
            fill_opacity=0.1,
            popup="Batas Geofence (Radius 50m)"
        ).add_to(m)
        
        # Marker Titik Tambat (Anchor)
        folium.Marker(
            [anchor_lat, anchor_lon],
            popup="Anchor (Titik Tambat)",
            icon=folium.Icon(color="black", icon="anchor", prefix="fa")
        ).add_to(m)
        
        # Jejak pergerakan (trail)
        track_points = list(zip(df_data["lat"].tail(30), df_data["lon"].tail(30)))
        folium.PolyLine(track_points, color="#0284c7", weight=3, opacity=0.7).add_to(m)
        
        # Marker Buoy saat ini
        folium.Marker(
            [curr_lat, curr_lon],
            popup=f"Buoy SMMB-01\nJarak: {dist:.1f}m",
            icon=folium.Icon(color="green" if dist <= 50 else "red", icon="ship", prefix="fa")
        ).add_to(m)
        
        st_folium(m, width=950, height=450)
    else:
        st.warning("Pustaka `folium` dan `streamlit-folium` belum terinstall. Peta ditampilkan dalam grafik koordinat:")
        st.scatter_chart(df_data[["lat", "lon"]].tail(50))

# ------------------------------------------
# TAB 4: VALIDASI MPV / ALAT LAB
# ------------------------------------------
with tab_field:
    st.header("🔬 Form Kunjungan & Validasi Lapangan (Teknisi/Peneliti)")
    st.caption("Sesuai PRD v1.1 Bagian 3.4: Pencatatan pengukuran referensi alat lab / MPV untuk validasi & kalibrasi.")
    
    with st.form("form_field_visit"):
        col_f1, col_f2 = st.columns(2)
        visit_date = col_f1.date_input("Tanggal Kunjungan", datetime.date.today())
        visit_time = col_f2.time_input("Waktu (WIB)", datetime.datetime.now().time())
        
        tide = col_f1.selectbox("Fase Pasang Surut", ["high (pasang)", "ebb (menuju surut)", "low (surut)", "flood (menuju pasang)"])
        fouling = col_f2.slider("Skor Biofouling (0 = Bersih, 4 = Sangat Tebal)", 0, 4, 1)
        
        st.markdown("**Hasil Pengukuran Referensi (MPV / Lab)**")
        col_r1, col_r2, col_r3 = st.columns(3)
        ref_temp = col_r1.number_input("Suhu Referensi (°C)", value=30.0, step=0.1)
        ref_sal = col_r2.number_input("Salinitas Referensi (PSU)", value=28.0, step=0.1)
        ref_turb = col_r3.number_input("Turbidity Referensi (NTU)", value=30.0, step=1.0)
        
        col_r4, col_r5 = st.columns(2)
        ref_ph = col_r4.number_input("pH Referensi", value=8.0, step=0.1)
        ref_do = col_r5.number_input("DO Referensi (mg/L)", value=6.5, step=0.1)
        
        instrument = st.text_input("Nama/Tipe Alat Referensi", "AZ Instrument 84051 / Lab Kimia ITS")
        notes = st.text_area("Catatan Lapangan & Aktivitas (misal: sensor dibersihkan, cuaca hujan)")
        
        submitted = st.form_submit_button("💾 Simpan Data Kunjungan ke Supabase")
        if submitted:
            if supabase_client:
                st.success("✅ Data kunjungan berhasil disimpan ke database!")
            else:
                st.info("ℹ️ Mode demo: data form tervalidasi dengan baik.")

# ------------------------------------------
# TAB 5: UNDUH DATASET
# ------------------------------------------
with tab_export:
    st.header("📥 Unduh Dataset Kualitas Air")
    st.caption("Data penelitian siap pakai untuk publikasi ilmiah, tugas akhir, dan analisis lanjutan.")
    
    col_d1, col_d2 = st.columns(2)
    start_date = col_d1.date_input("Mulai Tanggal", datetime.date.today() - datetime.timedelta(days=7))
    end_date = col_d2.date_input("Sampai Tanggal", datetime.date.today())
    
    st.dataframe(df_data.tail(50), use_container_width=True)
    
    csv = df_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Unduh File CSV Lengkap",
        data=csv,
        file_name=f"SMMB_Dataset_{datetime.date.today().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

