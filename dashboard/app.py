import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Cek pustaka pemetaan Folium
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# Cek pustaka Supabase
try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

st.set_page_config(
    page_title="SMMB — Smart Marine Monitoring Buoy ITS",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 1. KONEKSI SUPABASE DENGAN FALLBACK DEMO
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
        except Exception:
            return None
    return None

supabase_client = init_supabase()

def generate_mock_data():
    now = datetime.datetime.now(datetime.timezone.utc)
    n_points = 96 * 3  # 3 hari terakhir
    timestamps = [now - datetime.timedelta(minutes=15 * (n_points - i)) for i in range(n_points)]
    t_hours = np.array([ts.hour + ts.minute / 60 for ts in timestamps])

    temp = 29.5 + 1.8 * np.sin(2 * np.pi * (t_hours - 10) / 24) + np.random.normal(0, 0.2, n_points)
    sal = 28.0 + 3.5 * np.cos(2 * np.pi * (t_hours - 4) / 12.4) + np.random.normal(0, 0.3, n_points)
    turb = 25.0 + 10.0 * np.sin(2 * np.pi * (t_hours) / 12.4) ** 2 + np.random.exponential(3, n_points)
    ph = 7.9 + 0.3 * np.sin(2 * np.pi * (t_hours - 12) / 24) + np.random.normal(0, 0.05, n_points)
    batt = 12.8 - 0.4 * (t_hours > 18) + 0.3 * (t_hours > 6) * (t_hours < 16) + np.random.normal(0, 0.05, n_points)

    anchor_lat, anchor_lon = -7.31820, 112.82750
    drift_r = np.random.uniform(5, 25, n_points)
    drift_theta = np.random.uniform(0, 2 * np.pi, n_points)
    lat = anchor_lat + (drift_r * np.cos(drift_theta)) / 111000.0
    lon = anchor_lon + (drift_r * np.sin(drift_theta)) / (111000.0 * np.cos(np.radians(anchor_lat)))

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
        "qc_flags": qc_flags,
        "is_synthetic": True
    })
    return df

@st.cache_data(ttl=60)
def load_data():
    if supabase_client is not None:
        try:
            # Membaca data view publik
            res_pub = supabase_client.table("v_public_measurements").select("*").order("ts_utc", desc=False).limit(2000).execute()
            if res_pub.data and len(res_pub.data) > 0:
                df = pd.DataFrame(res_pub.data)
                df["ts_utc"] = pd.to_datetime(df["ts_utc"])
                df["is_synthetic"] = False
                df = df.sort_values("ts_utc")
                return df
        except Exception:
            pass
    df = generate_mock_data()
    df = df.sort_values("ts_utc")
    return df

df_raw = load_data()

# ==========================================
# 2. SIDEBAR STATUS & FILTER PERANGKAT
# ==========================================
st.sidebar.title("⚓ SMMB ITS")
st.sidebar.caption("Smart Marine Monitoring Buoy · PRD v1.1")

is_demo = df_raw["is_synthetic"].iloc[0] if "is_synthetic" in df_raw else True

if not is_demo:
    st.sidebar.success("🟢 Terhubung ke Supabase Live")
else:
    st.sidebar.warning("🟡 Mode Demo (Simulasi Data Sintetis)")

df_data = df_raw.copy()
device_list = df_raw["device_id"].unique().tolist()
selected_device = st.sidebar.selectbox("Pilih Perangkat", device_list, index=0)

# Filter dataframe berdasarkan perangkat yang dipilih
df_data = df_data[df_data["device_id"] == selected_device]
latest = df_data.iloc[-1]

st.sidebar.markdown("---")
st.sidebar.subheader("Status Terkini")
st.sidebar.metric("Tegangan Baterai", f"{latest.get('batt_v', 12.8):.2f} V")
dist_val = float(latest.get('dist_from_anchor_m', 12.0))
dist_status = "Aman (< 50m)" if dist_val <= 50.0 else "PERINGATAN HANYUT"
st.sidebar.metric("Jarak dari Anchor", f"{dist_val:.1f} m", delta=dist_status)
st.sidebar.metric("Sensor Kebocoran", "🚨 BOCOR!" if latest.get("leak", False) else "✅ Aman (Kering)")

# ==========================================
# 3. TABS DASHBOARD
# ==========================================
tab_overview, tab_trends, tab_map, tab_field, tab_export = st.tabs([
    "📊 Ringkasan Live",
    "📈 Tren Parameter QC",
    "🗺️ Peta & Geofence",
    "🔬 Kunjungan & Validasi MPV",
    "📥 Unduh Dataset",
])

# ------------------------------------------
# TAB 1: OVERVIEW
# ------------------------------------------
with tab_overview:
    st.header("🌊 Ringkasan Pemantauan Real-time")
    st.caption(f"Perangkat: {selected_device} | Pembaruan: {latest['ts_utc'].strftime('%Y-%m-%d %H:%M:%S UTC')}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Suhu Air", f"{latest['temp_c']} °C")
    col2.metric("🧂 Salinitas", f"{latest['sal_psu']} PSU")
    col3.metric("🌫️ Turbidity", f"{latest['turb_ntu']} NTU")
    ph_text = f"{latest['ph']}" if pd.notnull(latest.get('ph')) else "N/A"
    col4.metric("🧪 pH", ph_text)

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        fig_t = px.line(df_data.tail(96), x="ts_utc", y="temp_c", title="Suhu Air (24 Jam Terakhir)", color_discrete_sequence=["#0284c7"])
        fig_t.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_t, use_container_width=True)

    with col_right:
        fig_s = px.line(df_data.tail(96), x="ts_utc", y="sal_psu", title="Salinitas (24 Jam Terakhir)", color_discrete_sequence=["#0d9488"])
        fig_s.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_s, use_container_width=True)

    # Indikator dihitung secara dinamis
    st.subheader("Kesehatan Sistem & Availability")
    kpi1, kpi2, kpi3 = st.columns(3)
    rec_count = len(df_data)
    expected_est = max(1, 96 * 3)
    avail_pct = min(100.0, round((rec_count / expected_est) * 100, 1))
    kpi1.progress(int(avail_pct), text=f"Data Availability: {avail_pct}%")
    kpi2.metric("Total Siklus Diterima", rec_count)
    active_alerts = 1 if dist_val > 50 or latest.get("leak", False) else 0
    alert_status_label = "Aman" if active_alerts == 0 else "Perhatian"
    kpi3.metric("Alarm Aktif", str(active_alerts), delta=alert_status_label, delta_color="inverse")

# ------------------------------------------
# TAB 2: TRENDS DENGAN PEWARNAAN QC QARTOD
# ------------------------------------------
with tab_trends:
    st.header("📈 Analisis Parameter Kualitas Air (Standar QARTOD)")
    st.caption("Titik data diwarnai berdasarkan QC Flag: Hijau = Lolos (1), Kuning = Suspect (3), Merah = Gagal (4)")

    param_col = st.selectbox("Pilih Parameter", ["temp_c", "sal_psu", "turb_ntu", "ph"], format_func=lambda x: {
        "temp_c": "Suhu Air (°C)",
        "sal_psu": "Salinitas (PSU)",
        "turb_ntu": "Turbidity (NTU)",
        "ph": "pH"
    }[x])

    flag_colors = ["#10b981" if f.get(param_col, 1) == 1 else "#eab308" if f.get(param_col, 1) == 3 else "#ef4444" for f in df_data.get("qc_flags", [{}] * len(df_data))]

    fig_qc = go.Figure()
    fig_qc.add_trace(go.Scatter(
        x=df_data["ts_utc"],
        y=df_data[param_col],
        mode="lines+markers",
        line=dict(color="#94a3b8", width=1),
        marker=dict(size=6, color=flag_colors),
        name=param_col
    ))
    fig_qc.update_layout(title=f"Riwayat {param_col} dengan QC Flag", height=450)
    st.plotly_chart(fig_qc, use_container_width=True)

# ------------------------------------------
# TAB 3: PETA & GEOFENCE
# ------------------------------------------
with tab_map:
    st.header("🗺️ Posisi Buoy & Tracking Geofence")
    anchor_lat, anchor_lon = -7.31820, 112.82750
    curr_lat = latest.get("lat", anchor_lat)
    curr_lon = latest.get("lon", anchor_lon)

    if HAS_FOLIUM:
        m = folium.Map(location=[curr_lat, curr_lon], zoom_start=18)
        folium.Circle([anchor_lat, anchor_lon], radius=50, color="#ef4444", fill=True, fill_opacity=0.1, popup="Geofence (50m)").add_to(m)
        folium.Marker([anchor_lat, anchor_lon], popup="Anchor", icon=folium.Icon(color="black", icon="anchor", prefix="fa")).add_to(m)
        folium.Marker([curr_lat, curr_lon], popup=f"Buoy ({dist_val:.1f}m)", icon=folium.Icon(color="green" if dist_val <= 50 else "red", icon="ship", prefix="fa")).add_to(m)
        st_folium(m, width=950, height=450)

# ------------------------------------------
# TAB 4: VALIDASI MPV & KUNJUNGAN
# ------------------------------------------
with tab_field:
    st.header("🔬 Form Kunjungan & Validasi Lapangan")
    with st.form("visit_form"):
        f_date = st.date_input("Tanggal Kunjungan", datetime.date.today())
        f_tide = st.selectbox("Fase Pasang Surut", ["high", "ebb", "low", "flood", "unknown"])
        f_fouling = st.slider("Skor Biofouling (0-4)", 0, 4, 1)

        c1, c2, c3 = st.columns(3)
        v_temp = c1.number_input("Suhu Referensi (°C)", value=29.5)
        v_sal = c2.number_input("Salinitas Referensi (PSU)", value=28.0)
        v_turb = c3.number_input("Turbidity Referensi (NTU)", value=25.0)

        inst_name = st.text_input("Instrumen Referensi", "AZ Instrument 84051 / Lab ITS")
        f_notes = st.text_area("Catatan Pembersihan / Inspeksi")

        submit_btn = st.form_submit_button("Simpan Data Lapangan")
        if submit_btn:
            if supabase_client is not None:
                try:
                    res_v = supabase_client.table("field_visits").insert({
                        "device_id": selected_device,
                        "visit_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "tide_phase": f_tide,
                        "fouling_score": f_fouling,
                        "notes": f_notes
                    }).execute()
                    if res_v.data:
                        v_id = res_v.data[0]["visit_id"]
                        supabase_client.table("reference_measurements").insert([
                            {"visit_id": v_id, "measured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "parameter": "temp", "value": v_temp, "unit": "°C", "instrument": inst_name},
                            {"visit_id": v_id, "measured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "parameter": "salinity", "value": v_sal, "unit": "PSU", "instrument": inst_name},
                            {"visit_id": v_id, "measured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "parameter": "turbidity", "value": v_turb, "unit": "NTU", "instrument": inst_name},
                        ]).execute()
                        st.success("✅ Data kunjungan berhasil disimpan ke Supabase!")
                except Exception as ex:
                    st.error(f"Gagal menyimpan ke database: {ex}")
            else:
                st.info("ℹ️ Mode demo: data form tervalidasi secara lokal.")

# ------------------------------------------
# TAB 5: UNDUH DATASET
# ------------------------------------------
with tab_export:
    st.header("📥 Unduh Dataset Kualitas Air")
    c_d1, c_d2 = st.columns(2)
    start_date = c_d1.date_input("Mulai Tanggal", datetime.date.today() - datetime.timedelta(days=7))
    end_date = c_d2.date_input("Sampai Tanggal", datetime.date.today())

    # Terapkan filter rentang tanggal
    df_filtered = df_data.copy()
    if "ts_utc" in df_filtered.columns:
        df_filtered = df_filtered[
            (df_filtered["ts_utc"].dt.date >= start_date) &
            (df_filtered["ts_utc"].dt.date <= end_date)
        ]

    st.dataframe(df_filtered.tail(50), use_container_width=True)

    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    export_filename = f"SMMB_Dataset_{selected_device}_{datetime.date.today().strftime('%Y%m%d')}.csv"
    if is_demo:
        export_filename = f"SMMB_Dataset_{selected_device}_SIMULASI.csv"

    st.download_button(
        label="⬇️ Unduh CSV Terfilter",
        data=csv_data,
        file_name=export_filename,
        mime="text/csv",
    )
