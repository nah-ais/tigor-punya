"""
charts.py
=========
Kumpulan fungsi pure-function untuk membangun setiap visualisasi.
Setiap fungsi menerima DataFrame yang SUDAH terfilter dan mengembalikan
objek Plotly Figure -- tidak ada pemanggilan st.* di sini, supaya logic
visualisasi bisa dites/dipakai ulang terpisah dari layout Streamlit.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import EVAL_COLUMNS, EVAL_SHORT_LABELS, LIKERT_SCALE_MAX, TOP_N_LEARNING_ACADEMY, TOP_N_UNIT_KERJA

# Palet warna konsisten dipakai di semua chart
COLOR_PRIMARY = "#1f4e8c"
COLOR_SEQUENCE = px.colors.sequential.Blues_r
TYPE_COLOR_MAP = {"online": "#2563eb", "offline": "#f59e0b", "hybrid": "#10b981"}


def build_participation_trend(df: pd.DataFrame) -> go.Figure:
    """Line chart: jumlah peserta UNIK per bulan (tren partisipasi)."""
    trend = (
        df.groupby("bulan_periode")["npp"]
        .nunique()
        .reset_index(name="jumlah_peserta_unik")
        .sort_values("bulan_periode")
    )
    trend["bulan_label"] = trend["bulan_periode"].dt.strftime("%b %Y")

    fig = px.line(
        trend,
        x="bulan_label",
        y="jumlah_peserta_unik",
        markers=True,
        text="jumlah_peserta_unik",
        title="Tren Partisipasi Peserta per Bulan",
    )
    fig.update_traces(line_color=COLOR_PRIMARY, textposition="top center")
    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Jumlah Peserta Unik",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def build_top_academy_score(df: pd.DataFrame, top_n: int = TOP_N_LEARNING_ACADEMY) -> go.Figure:
    """Horizontal bar chart: Top-N Learning Academy berdasarkan rata-rata overall_score."""
    agg = (
        df.dropna(subset=["overall_score"])
        .groupby("learning_academy")["overall_score"]
        .mean()
        .reset_index()
        .sort_values("overall_score", ascending=False)
        .head(top_n)
    )
    # Urutkan ascending untuk tampilan bar horizontal (terbesar di atas)
    agg = agg.sort_values("overall_score", ascending=True)

    fig = px.bar(
        agg,
        x="overall_score",
        y="learning_academy",
        orientation="h",
        text=agg["overall_score"].round(2),
        title=f"Top {top_n} Learning Academy (Rata-rata Skor Evaluasi)",
        color="overall_score",
        color_continuous_scale="Blues",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title=f"Rata-rata Skor (skala {LIKERT_SCALE_MAX:.0f})",
        yaxis_title="",
        xaxis_range=[0, LIKERT_SCALE_MAX + 0.5],
        coloraxis_showscale=False,
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def build_type_composition_donut(df: pd.DataFrame) -> go.Figure:
    """Donut chart: proporsi event berdasarkan Type Pelaksanaan (online/offline/hybrid)."""
    # Dihitung berbasis event unik (Nama Kegiatan), bukan baris peserta,
    # supaya proporsi merefleksikan jumlah PROGRAM, bukan jumlah kehadiran.
    comp = (
        df.drop_duplicates(subset=["nama_kegiatan", "tanggal_event", "type_pelaksanaan"])
        ["type_pelaksanaan"]
        .value_counts()
        .reset_index()
    )
    comp.columns = ["type_pelaksanaan", "jumlah"]

    fig = px.pie(
        comp,
        names="type_pelaksanaan",
        values="jumlah",
        hole=0.55,
        title="Komposisi Pelaksanaan Event",
        color="type_pelaksanaan",
        color_discrete_map=TYPE_COLOR_MAP,
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(margin=dict(t=50, l=10, r=10, b=10), showlegend=True)
    return fig


def build_unit_kerja_distribution(df: pd.DataFrame, top_n: int = TOP_N_UNIT_KERJA) -> go.Figure:
    """Bar chart: Unit Kerja dengan jumlah peserta UNIK terbanyak."""
    agg = (
        df.groupby("unit_kerja")["npp"]
        .nunique()
        .reset_index(name="jumlah_peserta_unik")
        .sort_values("jumlah_peserta_unik", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        agg,
        x="unit_kerja",
        y="jumlah_peserta_unik",
        text="jumlah_peserta_unik",
        title=f"Top {top_n} Unit Kerja Penyumbang Peserta",
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Jumlah Peserta Unik",
        xaxis_tickangle=-35,
        margin=dict(t=50, l=10, r=10, b=10),
    )
    return fig


def build_evaluation_radar(df: pd.DataFrame) -> go.Figure:
    """Radar chart: rata-rata skor untuk masing-masing 7 kriteria evaluasi."""
    means = df[EVAL_COLUMNS].mean(skipna=True)
    labels = [EVAL_SHORT_LABELS[c] for c in EVAL_COLUMNS]
    values = means.values.tolist()
    # Tutup loop radar (titik pertama diulang di akhir)
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            name="Rata-rata Skor",
            line_color=COLOR_PRIMARY,
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, LIKERT_SCALE_MAX])),
        title="Analisis Kriteria Evaluasi (Radar)",
        margin=dict(t=50, l=30, r=30, b=10),
        showlegend=False,
    )
    return fig


def build_evaluation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap alternatif: rata-rata skor 7 kriteria evaluasi per Learning Academy.

    Memberi insight tambahan dibanding radar (yang overall saja): kriteria
    mana yang lemah di Learning Academy MANA -- berguna untuk root-cause area
    perbaikan per akademi.
    """
    pivot = (
        df.groupby("learning_academy")[EVAL_COLUMNS]
        .mean()
        .rename(columns=EVAL_SHORT_LABELS)
    )

    fig = px.imshow(
        pivot,
        text_auto=".2f",
        color_continuous_scale="Blues",
        zmin=1,
        zmax=LIKERT_SCALE_MAX,
        aspect="auto",
        title="Analisis Kriteria Evaluasi per Learning Academy (Heatmap)",
    )
    fig.update_layout(
        xaxis_title="Kriteria Evaluasi",
        yaxis_title="Learning Academy",
        margin=dict(t=50, l=10, r=10, b=10),
    )
    fig.update_xaxes(tickangle=-25)
    return fig
