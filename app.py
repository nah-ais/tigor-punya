"""
app.py
======
Entry point Streamlit. Tugas file ini HANYA layout & orkestrasi:
1. Load data (via data_loader.load_and_prepare)
2. Render sidebar filter -> hasilkan df_filtered
3. Render KPI row
4. Render grid visualisasi (delegasi ke charts.py)

Jalankan dengan:
    streamlit run app.py
"""

import streamlit as st

from config import DEFAULT_DATA_PATH, TYPE_PELAKSANAAN_ORDER
from data_loader import load_and_prepare
import charts

# ---------------------------------------------------------------------------
# PAGE CONFIG (harus baris perintah st.* pertama)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Evaluasi Training & Learning Events",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Dashboard Evaluasi Training & Learning Events")
st.caption("Periode data: Januari – Juni 2026 · Sumber: CMS Learning Academy")


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
def get_data_source():
    """Pakai file default jika tersedia di server; jika tidak, minta upload.

    Pola ini membuat app tetap berfungsi di Streamlit Cloud/server (file
    dibundel bersama repo) MAUPUN dijalankan ad-hoc oleh user lain yang
    hanya punya file Excel-nya saja tanpa source code di sekitarnya.
    """
    if DEFAULT_DATA_PATH.exists():
        return DEFAULT_DATA_PATH
    st.sidebar.warning("File data default tidak ditemukan di server.")
    uploaded = st.sidebar.file_uploader("Upload file Excel evaluasi (.xlsx)", type=["xlsx"])
    return uploaded


data_source = get_data_source()

if data_source is None:
    st.info("⬅️ Silakan upload file Excel data evaluasi di sidebar untuk menampilkan dashboard.")
    st.stop()

try:
    df = load_and_prepare(data_source)
except Exception as e:
    st.error(f"Gagal memproses file: {e}")
    st.stop()


# ---------------------------------------------------------------------------
# 2. SIDEBAR -- GLOBAL FILTERS
# ---------------------------------------------------------------------------
st.sidebar.header("🔎 Filter Global")

# -- Filter rentang waktu (Date Range Picker) --
min_date = df["tanggal_event"].min().date()
max_date = df["tanggal_event"].max().date()

date_range = st.sidebar.date_input(
    "Rentang Tanggal Event",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
# date_input bisa mengembalikan 1 tanggal saja saat user baru klik tanggal awal
# -- guard ini mencegah error sebelum user memilih tanggal kedua.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# -- Dropdown dinamis: Learning Academy (single-select + opsi "Semua") --
academy_options = ["Semua"] + sorted(df["learning_academy"].dropna().unique().tolist())
selected_academy = st.sidebar.selectbox("Learning Academy", options=academy_options)

# -- Multiselect: Type pelaksanaan (Online/Offline/Hybrid) --
type_options = [t for t in TYPE_PELAKSANAAN_ORDER if t in df["type_pelaksanaan"].unique()]
selected_types = st.sidebar.multiselect(
    "Type Pelaksanaan",
    options=type_options,
    default=type_options,
)

st.sidebar.divider()
st.sidebar.caption(f"Total baris data mentah: {len(df):,}")


# ---------------------------------------------------------------------------
# 3. TERAPKAN FILTER
# ---------------------------------------------------------------------------
mask = (
    (df["tanggal_event"].dt.date >= start_date)
    & (df["tanggal_event"].dt.date <= end_date)
    & (df["type_pelaksanaan"].isin(selected_types))
)
if selected_academy != "Semua":
    mask &= df["learning_academy"] == selected_academy

df_filtered = df.loc[mask].copy()

if df_filtered.empty:
    st.warning("Tidak ada data yang cocok dengan kombinasi filter ini. Silakan ubah filter.")
    st.stop()


# ---------------------------------------------------------------------------
# 4. KPI METRICS -- BARIS ATAS
# ---------------------------------------------------------------------------
total_event = df_filtered["nama_kegiatan"].nunique()
total_peserta_unik = df_filtered["npp"].nunique()
avg_overall_score = df_filtered["overall_score"].mean(skipna=True)

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🗂️ Total Pelatihan/Event", f"{total_event:,}")
kpi2.metric("👥 Total Peserta Unik", f"{total_peserta_unik:,}")
kpi3.metric("⭐ Rata-rata Skor Kepuasan", f"{avg_overall_score:.2f} / 5.0")

st.divider()


# ---------------------------------------------------------------------------
# 5. VISUALISASI UTAMA
# ---------------------------------------------------------------------------
row1_col1, row1_col2 = st.columns([2, 1])
with row1_col1:
    st.plotly_chart(charts.build_participation_trend(df_filtered), use_container_width=True)
with row1_col2:
    st.plotly_chart(charts.build_type_composition_donut(df_filtered), use_container_width=True)

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.plotly_chart(charts.build_top_academy_score(df_filtered), use_container_width=True)
with row2_col2:
    st.plotly_chart(charts.build_unit_kerja_distribution(df_filtered), use_container_width=True)

st.divider()
st.subheader("🧭 Analisis Kriteria Evaluasi")
view_mode = st.radio(
    "Tampilan",
    options=["Radar (Overall)", "Heatmap (per Learning Academy)"],
    horizontal=True,
    label_visibility="collapsed",
)
if view_mode == "Radar (Overall)":
    st.plotly_chart(charts.build_evaluation_radar(df_filtered), use_container_width=True)
else:
    st.plotly_chart(charts.build_evaluation_heatmap(df_filtered), use_container_width=True)

with st.expander("📋 Lihat data hasil filter (raw)"):
    st.dataframe(df_filtered, use_container_width=True)
