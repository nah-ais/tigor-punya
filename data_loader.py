"""
data_loader.py
===============
Layer data engineering: load -> clean -> transform.
Dipisah dari app.py agar bisa di-unit-test atau dipakai ulang (misal untuk
batch report) tanpa harus menjalankan Streamlit.

Alur (dipanggil berurutan oleh `load_and_prepare`):
    1. load_raw_data()            -> baca sheet mentah dari Excel
    2. _clean_column_names()      -> strip() & rename ke snake_case
    3. _map_likert_to_numeric()   -> ubah 7 kolom teks evaluasi -> angka 1-5
    4. _compute_session_duration()-> hitung durasi sesi (jam) dari Jam Mulai/Selesai
    5. _compute_overall_score()   -> rata-rata baris dari 7 skor (overall satisfaction)
    6. _add_time_dimensions()     -> kolom bulan/tahun untuk agregasi tren
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import streamlit as st

from config import (
    COLUMN_RENAME_MAP,
    EVAL_COLUMNS,
    EVAL_COLUMNS_MAP,
    LIKERT_MAP,
    RAW_SHEET_NAME,
)


# ---------------------------------------------------------------------------
# 1. LOADING
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Memuat data mentah dari Excel...")
def load_raw_data(file: Union[str, Path, "st.runtime.uploaded_file_manager.UploadedFile"]) -> pd.DataFrame:
    """Baca sheet data mentah ('Data tarikan CMS') dari file Excel.

    `file` bisa berupa path (str/Path) ATAU objek hasil st.file_uploader,
    keduanya didukung langsung oleh pandas.read_excel.
    """
    df = pd.read_excel(file, sheet_name=RAW_SHEET_NAME)
    return df


# ---------------------------------------------------------------------------
# 2. CLEANING NAMA KOLOM
# ---------------------------------------------------------------------------
def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace di nama kolom, lalu rename ke snake_case yang konsisten.

    Catatan: sumber data punya kolom seperti 'Learning Academy ' (trailing
    space) -- tanpa strip() ini, rename via COLUMN_RENAME_MAP akan gagal diam-diam.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Rename kolom non-evaluasi
    df = df.rename(columns=COLUMN_RENAME_MAP)

    # Rename 7 kolom pertanyaan evaluasi (teks panjang -> alias singkat)
    eval_rename = {raw.strip(): alias for raw, alias in EVAL_COLUMNS_MAP.items()}
    df = df.rename(columns=eval_rename)

    return df


# ---------------------------------------------------------------------------
# 3. MAPPING TEKS EVALUASI -> ANGKA (1-5)
# ---------------------------------------------------------------------------
def _map_likert_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Konversi 7 kolom evaluasi dari teks ('Sangat Setuju', dst) ke numerik.

    Nilai yang tidak dikenali (termasuk NaN asli) akan menjadi NaN -- BUKAN 0 --
    supaya tidak menurunkan rata-rata skor secara artifisial. Baris yang
    NaN akan otomatis dikeluarkan saat .mean() dihitung (skipna=True default).
    """
    df = df.copy()
    for col in EVAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().map(LIKERT_MAP)
            # .map() pada string "nan" (hasil astype(str) dari NaN asli) akan
            # otomatis jadi NaN karena "nan" tidak ada di LIKERT_MAP -- sudah aman.
    return df


# ---------------------------------------------------------------------------
# 4. HITUNG DURASI SESI (JAM)
# ---------------------------------------------------------------------------
def _time_to_timedelta(t) -> pd.Timedelta:
    """Helper: konversi datetime.time -> pd.Timedelta sejak tengah malam."""
    if pd.isna(t):
        return pd.NaT
    if isinstance(t, dt.time):
        return pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    # Fallback jika kolom terbaca sebagai string "HH:MM:SS"
    return pd.to_timedelta(str(t))


def _compute_session_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Hitung 'durasi_sesi_jam' = Jam Selesai - Jam Mulai (dalam jam, desimal).

    PENTING: ini BERBEDA dari kolom 'total_hari_program' (atribut level
    program, misal "22" = total minggu program berjalan). 'durasi_sesi_jam'
    adalah durasi SATU sesi/pertemuan yang dihitung dari jam_mulai & jam_selesai.

    Menangani kasus sesi yang melewati tengah malam (jam_selesai < jam_mulai)
    dengan menambahkan 24 jam -- meski di dataset Jan-Jun 2026 belum ada kasus
    ini, kode dibuat defensif untuk periode mendatang.
    """
    df = df.copy()
    mulai = df["jam_mulai"].apply(_time_to_timedelta)
    selesai = df["jam_selesai"].apply(_time_to_timedelta)

    durasi = (selesai - mulai).dt.total_seconds() / 3600.0
    # Sesi yang melewati tengah malam -> durasi negatif -> tambah 24 jam
    durasi = np.where(durasi < 0, durasi + 24, durasi)

    df["durasi_sesi_jam"] = durasi
    return df


# ---------------------------------------------------------------------------
# 5. SKOR KEPUASAN KESELURUHAN PER BARIS
# ---------------------------------------------------------------------------
def _compute_overall_score(df: pd.DataFrame) -> pd.DataFrame:
    """Tambah kolom 'overall_score' = rata-rata 7 skor evaluasi per baris.

    skipna=True (default) -> jika peserta hanya menjawab sebagian pertanyaan,
    rata-rata dihitung dari yang terjawab saja, bukan dianggap 0.
    """
    df = df.copy()
    available_cols = [c for c in EVAL_COLUMNS if c in df.columns]
    df["overall_score"] = df[available_cols].mean(axis=1, skipna=True)
    return df


# ---------------------------------------------------------------------------
# 6. DIMENSI WAKTU UNTUK AGREGASI TREN
# ---------------------------------------------------------------------------
def _add_time_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tanggal_event"] = pd.to_datetime(df["tanggal_event"])
    df["bulan_periode"] = df["tanggal_event"].dt.to_period("M").dt.to_timestamp()
    df["bulan_label"] = df["tanggal_event"].dt.strftime("%b %Y")
    return df


# ---------------------------------------------------------------------------
# ENTRY POINT: PIPELINE LENGKAP
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Memproses & membersihkan data...")
def load_and_prepare(file: Union[str, Path, "st.runtime.uploaded_file_manager.UploadedFile"]) -> pd.DataFrame:
    """Pipeline preprocessing lengkap: raw Excel -> DataFrame siap pakai dashboard."""
    df_raw = pd.read_excel(file, sheet_name=RAW_SHEET_NAME)  # tidak panggil load_raw_data agar cache key tunggal
    df = _clean_column_names(df_raw)
    df = _map_likert_to_numeric(df)
    df = _compute_session_duration(df)
    df = _compute_overall_score(df)
    df = _add_time_dimensions(df)
    return df
