"""
config.py
=========
Konfigurasi terpusat untuk Dashboard Evaluasi Training & Learning Events.
Semua "magic string" (nama kolom, mapping skor, label) didefinisikan di sini
agar mudah dirawat ketika struktur sumber data berubah di periode mendatang.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 1. LOKASI DATA
# ---------------------------------------------------------------------------
# Nama file default yang dicari otomatis di folder yang sama dengan app.py.
# Jika tidak ditemukan, dashboard akan menampilkan file_uploader sebagai fallback.
DEFAULT_DATA_FILENAME = "Data_Set_Evaluasi_Training___Learning_Events_Jan_26-20_Jun_2026.xlsx"
DEFAULT_DATA_PATH = Path(__file__).parent / DEFAULT_DATA_FILENAME
RAW_SHEET_NAME = "Data tarikan CMS"

# ---------------------------------------------------------------------------
# 2. STANDARDISASI NAMA KOLOM
# ---------------------------------------------------------------------------
# Sumber data punya beberapa nama kolom yang panjang/ada trailing space
# (contoh: "Learning Academy " dengan spasi di akhir). Kita mapping ke nama
# pendek yang konsisten (snake_case) supaya kode downstream lebih bersih.
# Catatan: proses cleaning akan men-strip() semua nama kolom dulu sebelum
# rename ini dijalankan, jadi key di bawah tidak perlu spasi ekstra.
COLUMN_RENAME_MAP = {
    "Nama Kegiatan": "nama_kegiatan",
    "Jenis Pembelajaran (Training / Learning Events)": "jenis_pembelajaran",
    "Category (Inhouse/Public)": "category",
    "Type (Online/Offline/Hybrid)": "type_pelaksanaan",
    "Type Event": "type_event",
    "Learning Academy": "learning_academy",
    "Sub Learning Academy": "sub_learning_academy",
    "Narasumber": "narasumber",
    "NPP": "npp",
    "Nama": "nama_peserta",
    "Level": "level",
    "Jabatan": "jabatan",
    "Unit Kerja": "unit_kerja",
    "Gender": "gender",
    "Tanggal Event": "tanggal_event",
    "Jam Mulai": "jam_mulai",
    "Jam Selesai": "jam_selesai",
    "Total Hari": "total_hari_program",  # atribut level-program, BUKAN durasi sesi
}

# 7 kolom pertanyaan evaluasi (teks) -> alias singkat untuk dipakai di chart.
# Urutan dict ini menentukan urutan tampil di radar chart / heatmap.
EVAL_COLUMNS_MAP = {
    "Apakah Materi Learning/Event ini bermanfaat?": "kemanfaatan_materi",
    "Apakah Materi Learning/Event ini mudah dipahami?": "kemudahan_dipahami",
    "Apakah Materi Learning/Event ini sesuai dengan kebutuhan terkait tugas dan tanggung jawab pekerjaan?": "relevansi_tugas",
    "Apakah Materi Learning/Event ini perlu ada tahapan selanjutnya?": "perlu_tindak_lanjut",
    "Apakah narasumber menyampaikan materi dengan jelas, runut dan mudah dipahami?": "kejelasan_narasumber",
    "Apakah metode pengajaran sesuai dengan tujuan pelatihan yang ingin dicapai?": "kesesuaian_metode",
    "Apakah narasumber mampu menjawab pertanyaan audience dengan baik?": "kemampuan_menjawab_pertanyaan",
}

# Label pendek (untuk axis radar/heatmap) -- urutan harus sama dengan EVAL_COLUMNS_MAP
EVAL_SHORT_LABELS = {
    "kemanfaatan_materi": "Kemanfaatan Materi",
    "kemudahan_dipahami": "Kemudahan Dipahami",
    "relevansi_tugas": "Relevansi dgn Tugas",
    "perlu_tindak_lanjut": "Perlu Tindak Lanjut",
    "kejelasan_narasumber": "Kejelasan Narasumber",
    "kesesuaian_metode": "Kesesuaian Metode",
    "kemampuan_menjawab_pertanyaan": "Kemampuan Menjawab Tanya",
}

EVAL_COLUMNS = list(EVAL_COLUMNS_MAP.values())

# ---------------------------------------------------------------------------
# 3. MAPPING SKALA LIKERT (TEKS -> ANGKA 1-5)
# ---------------------------------------------------------------------------
# Berdasarkan legenda di "Sheet1" pada file sumber, DITAMBAH label "Cukup Setuju"
# yang ditemukan di kolom evaluasi aktual tapi tidak terdaftar di legenda asli.
# NaN/kosong sengaja TIDAK dipetakan ke 0 -- dianggap "tidak menjawab" agar
# tidak mendistorsi rata-rata skor kepuasan ke bawah.
LIKERT_MAP = {
    "Sangat Setuju": 5,
    "Setuju": 4,
    "Cukup Setuju": 3,   # ditemukan di data aktual, tidak ada di legenda Sheet1
    "Netral": 3,         # label di legenda Sheet1, dijaga untuk kompatibilitas periode lain
    "Tidak Setuju": 2,
    "Sangat Tidak Setuju": 1,
}

LIKERT_SCALE_MAX = 5.0

# ---------------------------------------------------------------------------
# 4. LAIN-LAIN
# ---------------------------------------------------------------------------
TYPE_PELAKSANAAN_ORDER = ["online", "offline", "hybrid"]
TOP_N_LEARNING_ACADEMY = 5
TOP_N_UNIT_KERJA = 10
