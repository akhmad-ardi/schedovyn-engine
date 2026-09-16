# Schedovyn pilot-training solver prototype

Dokumentasi ini menjelaskan tujuan, ruang lingkup, dan pembuatan prototipe mesin penjadwalan Schedovyn, mulai dari kebutuhan operasional hingga implementasi Python dengan OR-Tools CP-SAT. Fokus utama adalah penjadwalan pelatihan dengan data sintetis.

Status proyek: **prototipe solver berbasis command line**, versi paket `0.1.0`. Kemampuan yang dijelaskan sebagai implementasi tersedia di repositori ini; bagian pengembangan lanjutan merupakan pekerjaan yang belum diselesaikan.

## 1. Latar belakang dan tujuan

Penjadwalan pelatihan harus mempertemukan pengajar, kelompok peserta, dan ruangan pada waktu yang sama. Sebuah ruangan yang kosong belum tentu memenuhi kebutuhan fasilitas atau jumlah peserta. Pengajar yang kompeten juga dapat memiliki keterbatasan waktu atau beban mengajar.

Prototipe ini dibuat untuk:

- Membuktikan bahwa kebutuhan tersebut dapat diterjemahkan menjadi aturan penjadwalan yang dapat dihitung.
- Menemukan jadwal lengkap yang memenuhi seluruh aturan wajib.
- Memilih jadwal dengan pemenuhan preferensi berbobot terbaik yang dapat ditemukan dalam batas pencarian.
- Menghasilkan keluaran terstruktur untuk diperiksa dan menjadi dasar pengembangan integrasi Schedovyn.

Kata *pilot-training* merujuk pada uji coba penjadwalan kegiatan pelatihan. Mesin bekerja berdasarkan data dan aturan yang diberikan; tidak melakukan pelatihan model machine learning.

## 2. Pengguna dan alur operasional

| Peran | Tanggung jawab dalam uji coba |
| --- | --- |
| Pengelola pelatihan | Menentukan kegiatan, kebutuhan pengajar, kelompok, ruangan, dan aturan operasional. |
| Operator penjadwalan | Menyiapkan data, mencatat pengecualian ketersediaan, menetapkan sesi terkunci, dan meninjau hasil. |
| Pengembang | Mengubah kebutuhan menjadi snapshot, menjalankan solver, serta memeriksa model dan hasilnya. |

Alur penggunaan dimulai dari pendataan sumber daya dan kegiatan, penetapan aturan wajib serta preferensi, penyusunan snapshot input, pencarian jadwal, lalu peninjauan hasil. Saat ini pengoperasian dilakukan melalui file JSON dan terminal. Antarmuka operator dan publikasi jadwal belum tersedia.

## 3. Ruang lingkup pilot pelatihan

| Aspek | Ketentuan dataset utama |
| --- | --- |
| Organisasi | Balai Pelatihan Contoh; nama dan data bersifat sintetis. |
| Periode | 21–25 September 2026, inklusif. |
| Zona waktu | Asia/Makassar, WITA atau UTC+08:00. |
| Jam operasional | Senin–Jumat, 08:00–12:00 dan 13:00–16:00. |
| Resolusi waktu | Slot 30 menit. |
| Sumber daya | 3 pengajar, 2 kelompok peserta, dan 3 ruangan. |
| Kegiatan | 8 aktivitas yang telah dijabarkan menjadi 14 sesi wajib. |
| Total durasi | 1.380 menit sesi. |
| Keputusan solver | Waktu mulai, pilihan pengajar, dan pilihan ruangan. |
| Ketetapan input | Tanggal sesi, durasi, kelompok, kebutuhan sumber daya, dan kunci penempatan. |
| Anggaran pencarian | 60 detik pada snapshot contoh. |

Setiap sesi membutuhkan satu pengajar, satu kelompok, dan satu ruangan sepanjang durasinya. Sesi berlangsung utuh pada satu tanggal dan tidak boleh melintasi istirahat. Dua kelompok diasumsikan tidak memiliki peserta yang sama.

Pilot belum mencakup jeda perpindahan, urutan wajib antarmateri, pemecahan sesi atau kelompok, pemerataan beban, dan minimisasi perubahan dari jadwal sebelumnya.

## 4. Istilah dan aturan bisnis

| Istilah | Arti dan contoh |
| --- | --- |
| Resource | Sumber daya yang digunakan bersama, seperti pengajar T1 atau laboratorium LAB. |
| Activity | Definisi kegiatan, misalnya Praktik Web A dengan durasi 120 menit. |
| Occurrence | Satu pelaksanaan kegiatan pada tanggal tertentu, misalnya O01 pada 21 September. |
| Assignment | Hasil penempatan satu occurrence: tanggal, jam, dan sumber daya terpilih. |
| Snapshot | Satu berkas input yang memuat keadaan data untuk satu proses pencarian. |
| Hard constraint | Aturan wajib; pelanggarannya membuat jadwal tidak valid. |
| Preference | Keinginan berbobot yang dioptimalkan setelah aturan wajib dipenuhi. |
| Lock | Penempatan sesi yang harus dipertahankan. |
| Published booking | Pemakaian sumber daya dari jadwal terbit yang harus diperhitungkan. |

Kapasitas kursi berbeda dari kapasitas pemakaian serentak. LAB memiliki 30 kursi, tetapi kapasitas serentaknya satu sesi. Kelompok B berisi 28 peserta sehingga tidak dapat menggunakan Kelas A yang hanya memiliki 24 kursi.

Ketersediaan khusus tanggal tertentu (*override*) menggantikan pola mingguan pada tanggal tersebut. Daftar waktu override kosong berarti tidak tersedia sepanjang hari. Override tetap tunduk pada kalender organisasi.

Interval menggunakan batas akhir eksklusif: sesi 08:00–10:00 dapat disambung sesi 10:00–12:00 tanpa dianggap bertabrakan.

## 5. Kriteria keberhasilan dan interpretasi hasil

Keberhasilan pilot dinilai dari kelengkapan sesi wajib, kepatuhan terhadap aturan, pemenuhan preferensi, dan ketepatan pelaporan status pencarian.

| Status solusi | Interpretasi |
| --- | --- |
| `Optimal` | Jadwal ditemukan dan solver membuktikan nilai objective terbaik untuk model dan snapshot tersebut. |
| `Feasible` | Jadwal ditemukan, tetapi optimalitas belum terbukti. |
| `Infeasible` | Solver membuktikan seluruh aturan dalam model tidak dapat dipenuhi bersama. |
| `Belum ditemukan` | Belum ada solusi yang dilaporkan; untuk status mentah `UNKNOWN`, belum ada bukti infeasible. |

Skor preferensi di bawah 100% tetap dapat menghasilkan jadwal valid dan optimal. Sebagian keinginan dapat saling bersaing atau dibatasi aturan wajib. Status optimal juga tidak berarti assignment harus identik dengan jadwal acuan.

Kegagalan membaca JSON, kesalahan input, dan kesalahan model perlu dibedakan dari infeasibilitas. Implementasi saat ini belum menyediakan kontrak status kegagalan dan pembatalan job yang lengkap; periksa pula `solver_status` dan pesan kesalahan proses.

## 6. Tahapan pembuatan prototipe

1. **Tetapkan masalah operasional.** Identifikasi pengguna, periode penjadwalan, keputusan yang boleh diubah, dan aturan yang harus dipertahankan.
2. **Susun dataset sintetis.** Definisikan sumber daya, kompetensi, fasilitas, kapasitas, kalender, kegiatan, dan sesi pada tanggal tertentu.
3. **Pisahkan aturan wajib dan preferensi.** Aturan wajib menentukan validitas; bobot preferensi menentukan prioritas optimasi.
4. **Bekukan kontrak input.** Simpan seluruh data satu proses dalam snapshot JSON dengan identitas dataset dan revisi input.
5. **Bangun kandidat penempatan.** Gabungkan pilihan waktu dan sumber daya yang memenuhi ketentuan setiap sesi.
6. **Bangun model CP-SAT.** Tambahkan variabel pemilihan kandidat, batas kapasitas, batas beban harian, booking, dan objective preferensi.
7. **Jalankan pencarian dan ekspor hasil.** Baca status solver, ambil assignment terpilih, lalu hitung ringkasan preferensi.
8. **Verifikasi dan evaluasi.** Periksa contoh hasil dan kasus konflik, kemudian lengkapi validator independen serta pengujian sebelum integrasi produk.

Repositori menyediakan dataset, model, CLI, dan contoh hasil untuk tahapan tersebut. Validator independen dan rangkaian pengujian otomatis belum tersedia.

## 7. Teknologi dan struktur repositori

Konfigurasi proyek pada [pyproject.toml](pyproject.toml) menetapkan Python `>=3.13`, dependensi `ortools>=9.15.6755`, serta build backend `uv_build`. File `.python-version` memilih Python 3.13 dan `uv.lock` menyimpan resolusi dependensi proyek.

```text
.
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── src/solver/
│   ├── __init__.py             # Entry point CLI: baca input dan tulis output
│   └── schedovyn_solver.py     # Kandidat, constraint, objective, dan solve
└── data/
    ├── pelatihan/              # Skenario utama pilot-training
    ├── bengkel/                # Contoh skenario tambahan
    └── layanan-pelanggan/      # Contoh skenario tambahan
```

Setiap direktori dataset berisi dokumen skenario, `Snapshot-input.json`, `Assignment-acuan.json`, dan `solver-result.json`. Assignment acuan merupakan contoh jadwal yang dapat diperiksa, sedangkan `solver-result.json` merupakan artefak hasil yang tersimpan. Solver hanya membaca snapshot input.

## 8. Arsitektur dan aliran data

```mermaid
flowchart LR
    A[Snapshot JSON] --> B[CLI solver]
    B --> C[Validasi awal]
    C --> D[Kandidat penempatan]
    D --> E[Model CP-SAT]
    E --> F[Pencarian solusi]
    F --> G[Status dan assignment]
    G --> H[Hasil JSON]
```

Entry point `solver = "solver:main"` mengarah ke [src/solver/__init__.py](src/solver/__init__.py). Fungsi `main()` membaca JSON, memanggil `PilotSolver(snapshot).solve()`, lalu menulis hasil.

Implementasi inti berada di [src/solver/schedovyn_solver.py](src/solver/schedovyn_solver.py):

| Komponen | Fungsi |
| --- | --- |
| `SnapshotError` | Menandai kesalahan input yang diperiksa secara eksplisit. |
| `PlacementOption` | Menyimpan satu kandidat lengkap: slot mulai/akhir, sumber daya per peran, dan unit penggunaan. |
| `PilotSolver.build()` | Memeriksa referensi, membuat kandidat, menambahkan aturan wajib dan preferensi. |
| `PilotSolver.solve()` | Menjalankan CP-SAT dan menyusun kontrak hasil. |
| `parse_args()` | Mendefinisikan argumen CLI `--input` dan `--output`. |

## 9. Kontrak snapshot input

Gunakan [snapshot pelatihan](data/pelatihan/Snapshot-input.json) sebagai contoh lengkap. Versi kontrak dataset utama adalah `pilot-training-1.0.0`.

| Field | Isi dan peran |
| --- | --- |
| `schema_version`, `dataset_id`, `input_revision` | Penanda format, identitas dataset, dan revisi data. |
| `workspace` | Identitas organisasi dan metadata zona waktu. |
| `period` | `start_date`, `end_date`, dan `slot_minutes`. |
| `calendar` | Hari operasional ISO, jendela buka, dan hari libur. |
| `availability_profiles` | Pola ketersediaan mingguan sumber daya. |
| `availability_overrides` | Pengganti ketersediaan untuk sumber daya pada tanggal tertentu. |
| `resources` | Jenis, status aktif, tag, kapasitas, profil ketersediaan, dan batas beban. |
| `activities` | Durasi, jendela yang diperbolehkan, dan kebutuhan sumber daya per peran. |
| `occurrences` | Daftar sesi bertanggal yang menjadi masukan langsung solver. |
| `locks` | Penempatan waktu dan sumber daya yang harus dipertahankan. |
| `published_bookings` | Pemakaian sumber daya yang sudah ditetapkan oleh jadwal terbit. |
| `replaces_schedule_version_id` | Versi jadwal yang booking-nya dikecualikan karena sedang diganti. |
| `preferences` | Preferensi aktif, sasaran aktivitas, tipe, dan bobot. |
| `solver_budget_seconds` | Batas waktu pencarian CP-SAT; default 60 detik. |
| `enabled_hard_rules` | Metadata daftar aturan pada snapshot; belum menjadi sakelar aturan di kode. |

Tanggal menggunakan `YYYY-MM-DD`, waktu menggunakan `HH:MM`, dan ISO weekday menggunakan 1 untuk Senin sampai 7 untuk Minggu. Tanggal akhir periode bersifat inklusif. Resolusi slot harus positif dan membagi 1.440 menit; durasi harus positif serta merupakan kelipatan slot.

Dalam `requirements`, `candidate_ids` adalah alternatif yang dipilih sebanyak `select_count`. `fixed_resource_id` menetapkan sumber daya tertentu. Kecocokan diperiksa melalui `type`, `required_tags`, `min_seats`, dan `min_participants`; penggunaan kapasitas ditentukan oleh `units_per_selected_resource`.

`activities.recurrence` tidak diekspansi oleh solver. Daftar `occurrences` harus sudah disiapkan sebelum pencarian, dan perubahan pola pengulangan harus disertai pembaruan daftar sesi.

## 10. Pemodelan teknis CP-SAT

### 10.1 Waktu dan kandidat penempatan

Waktu lokal diubah menjadi indeks slot sejak awal periode. Satu hari tetap direpresentasikan sebagai 24 jam agar tanggal dan pemeriksaan overlap konsisten, meskipun organisasi hanya buka pada sebagian hari.

```text
slot_absolut = selisih_hari × (1440 / slot_minutes)
               + menit_sejak_tengah_malam / slot_minutes
```

Untuk setiap occurrence, solver membentuk kombinasi sumber daya sesuai kebutuhan, menelusuri waktu mulai yang diizinkan, memeriksa ketersediaan, lalu menyaring kandidat berdasarkan lock. Satu sumber daya tidak boleh mengisi dua kebutuhan berbeda dalam kandidat yang sama.

Setiap kandidat memiliki variabel Boolean `x[o,k]`: bernilai 1 jika kandidat ke-k untuk occurrence o dipilih. Occurrence wajib memiliki tepat satu kandidat terpilih; occurrence opsional memiliki paling banyak satu. Jika occurrence wajib tidak memiliki kandidat, model dibuat infeasible.

### 10.2 Aturan wajib dan pemetaan ID

**Penomoran H01–H09 dalam kode berbeda dari dokumen skenario pelatihan.** Tabel berikut memetakan keduanya agar pembaca dapat menelusuri aturan berdasarkan maknanya.

| ID kode | ID skenario pelatihan | Aturan | Implementasi |
| --- | --- | --- | --- |
| H01 | H02 | Kapasitas serentak | `AddCumulative` membatasi jumlah unit pemakaian pada setiap resource. |
| H02 | H03 | Ketersediaan | Kandidat harus berada dalam profil atau override tanggal. |
| H03 | H04 | Kecocokan resource | Menyaring status aktif, jenis, tag, kapasitas peserta/kursi, dan kandidat. |
| H04 | H05 | Durasi dan jendela activity | Kandidat memiliki durasi tetap, sesuai slot, dan berada dalam satu jendela. |
| H05 | H06 | Kalender organisasi | Memeriksa hari buka, hari libur, dan jendela operasional. |
| H06 | H07 | Penempatan terkunci | Kandidat disaring berdasarkan waktu dan resource pada lock. |
| H07 | H08 | Beban harian | Jumlah `durasi × unit`, termasuk booking relevan, dibatasi `max_daily_minutes`. |
| H08 | H09 | Booking terbit | Menambahkan interval tetap dari workspace yang sama, kecuali versi yang diganti. |
| H09 | H01 | Kelengkapan sesi wajib | `AddExactlyOne` memilih satu penempatan lengkap untuk setiap occurrence wajib. |

Kandidat memakai optional interval yang aktif hanya saat variabel pemilihannya bernilai 1. Booking terbit memakai interval tetap dalam kumpulan kapasitas yang sama. Dengan demikian, resource berkapasitas lebih dari satu dapat dipakai bersamaan selama total unit tidak melampaui kapasitasnya.

Pemetaan tersebut menjelaskan tujuan aturan; cakupan validasi kode belum mencakup semua pemeriksaan dalam spesifikasi. Contohnya, kepemilikan workspace setiap resource belum divalidasi secara tersendiri.

### 10.3 Preferensi dan objective

Implementasi mendukung `preferred_time` dan `preferred_resource`. Preferensi waktu dapat memakai `full_interval` untuk seluruh sesi atau `start_in_window` untuk waktu mulainya. Preferensi resource terpenuhi jika setidaknya satu resource pada peran yang ditargetkan termasuk daftar pilihan.

Satu pasangan preferensi–occurrence menghasilkan nilai terpenuhi 0 atau 1. Preferensi aktif harus berbobot positif.

```text
objective = maksimum jumlah(bobot pasangan × nilai terpenuhi)
skor (%)  = bobot terpenuhi / total bobot pasangan relevan × 100
```

Jika tidak ada pasangan preferensi, skor bernilai `null`. Objective tidak mengizinkan pelanggaran aturan wajib. Solver menggunakan delapan search worker; pilihan assignment dan waktu eksekusi dapat berbeda antareksekusi.

## 11. Instalasi dan menjalankan prototipe

Jalankan perintah dari direktori utama repositori. Siapkan Python 3.13 dan `uv`, lalu sinkronkan lingkungan sesuai lockfile:

```bash
uv sync --locked
```

Jalankan dataset pelatihan dan simpan hasil baru di direktori utama:

```bash
uv run solver \
  --input data/pelatihan/Snapshot-input.json \
  --output hasil-pelatihan.json
```

Lihat bantuan CLI:

```bash
uv run solver --help
```

`--input` wajib diisi. Jika `--output` dihilangkan, hasil ditulis ke `solver-result.json` pada direktori kerja. Direktori tujuan harus sudah tersedia; file tujuan yang sudah ada akan ditimpa. Hasil utama ditulis ke file, sehingga terminal dapat tidak menampilkan keluaran saat proses berhasil.

Dataset tambahan dapat dijalankan melalui CLI yang sama:

```bash
uv run solver --input data/bengkel/Snapshot-input.json --output hasil-bengkel.json
uv run solver --input data/layanan-pelanggan/Snapshot-input.json --output hasil-layanan-pelanggan.json
```

Untuk pemakaian melalui Python setelah paket terpasang:

```python
import json
from pathlib import Path
from solver.schedovyn_solver import PilotSolver

snapshot = json.loads(
    Path("data/pelatihan/Snapshot-input.json").read_text(encoding="utf-8")
)
result = PilotSolver(snapshot).solve()
print(result["solution_status"])
```

Buat instance `PilotSolver` baru untuk setiap proses pencarian.

## 12. Membaca hasil solver

Kontrak hasil menggunakan `schema_version: pilot-training-solver-result-1.0.0`. Field utamanya adalah identitas dataset dan revisi, `solution_status`, status mentah `solver_status`, `assignments`, `unassigned_occurrences`, serta ringkasan `preference`.

Contoh satu elemen assignment:

```json
{
  "occurrence_id": "O01",
  "date": "2026-09-21",
  "start": "08:00",
  "end": "10:00",
  "resources": {
    "instructor": "T1",
    "group": "GA",
    "room": "LAB"
  }
}
```

Nilai resource per peran berupa string jika hanya satu resource terpilih, atau daftar string jika lebih dari satu. Pada solusi `Optimal` atau `Feasible`, objek `solver` memuat nilai objective, batas objective terbaik, waktu solver, jumlah konflik, dan jumlah cabang pencarian.

[Hasil pelatihan yang tersimpan](data/pelatihan/solver-result.json) mencatat 14 assignment dengan status `Optimal`, 18 dari 21 pasangan preferensi terpenuhi, dan bobot terpenuhi 46 dari 53, sehingga skornya sekitar **86,79%**. Angka ini merupakan hasil dataset contoh, bukan jaminan performa atau skor untuk dataset lain.

Waktu `wall_time_seconds` adalah metrik solver, bukan keseluruhan waktu proses dari pembacaan input sampai penulisan output. Batas `solver_budget_seconds` juga tidak mencakup seluruh waktu pembentukan kandidat dan model.

## 13. Verifikasi dan rencana pengujian

Pemeriksaan dasar hasil pelatihan mencakup 14 occurrence wajib terjadwal tepat sekali, O01 tetap terkunci pada 21 September pukul 08:00–10:00 dengan T1/GA/LAB, serta kesesuaian durasi, resource, kapasitas, dan ketersediaan. Assignment acuan digunakan untuk memahami validitas dan skor, bukan sebagai syarat kesamaan keluaran solver.

Kasus berikut perlu dimasukkan ke pengujian otomatis dan validator independen:

| Kasus | Perilaku yang perlu diverifikasi |
| --- | --- |
| Dataset dasar | Seluruh sesi wajib terjadwal dan semua aturan lulus pemeriksaan. |
| Resource tidak tersedia pada sesi terkunci | Tidak menghasilkan jadwal yang melanggar lock atau ketersediaan. |
| Kandidat ruangan tidak memenuhi kursi/tag | Kandidat ditolak; sesi wajib tanpa kandidat membuat model infeasible. |
| Dua sesi bertemu tepat pada batas akhir/awal | Tidak dianggap overlap. |
| Resource berkapasitas lebih dari satu | Overlap diizinkan sesuai total unit kapasitas. |
| Booking dari versi yang diganti | Tidak dihitung ganda; booking versi lain tetap berlaku. |
| Tidak ada preferensi | Jadwal tetap dapat dicari dengan skor `null`. |
| Batas pencarian habis | Status mengikuti hasil nyata solver; `UNKNOWN` tidak disamakan dengan `INFEASIBLE`. |

Dataset kecil dapat langsung mencapai optimalitas. Pengujian kontrak `Feasible` dan `Belum ditemukan` perlu hasil terkontrol; batas waktu sangat kecil tidak menjamin status tertentu. Daftar di atas merupakan rencana verifikasi, bukan klaim bahwa seluruh pengujian sudah tersedia atau lulus.

## 14. Keterbatasan dan pengembangan lanjutan

- **Validasi input belum lengkap.** Belum ada validasi JSON Schema menyeluruh, pemeriksaan semua ID duplikat, atau seluruh referensi dan kepemilikan workspace. Metadata `schema_version` belum divalidasi dan `enabled_hard_rules` belum mengaktifkan/menonaktifkan aturan. Field `activities.active` juga belum menjadi filter sesi.
- **Waktu masih lokal.** Metadata zona waktu belum dipakai untuk konversi datetime yang sadar zona waktu. Sesi dan booking lintas tengah malam belum didukung.
- **Ekspansi recurrence belum tersedia.** Persiapan snapshot harus membentuk occurrence terlebih dahulu.
- **Pelaporan occurrence opsional belum lengkap.** Model mendukung paling banyak satu penempatan untuk sesi opsional, tetapi hasil sukses selalu mengisi `unassigned_occurrences` dengan daftar kosong meskipun ada sesi opsional yang dilewati. Dataset utama seluruhnya wajib.
- **Diagnosis masih terbatas.** Hasil infeasible belum menjelaskan kumpulan aturan penyebab konflik. Ringkasan preferensi kosong juga dipakai pada hasil tanpa solusi, sehingga tidak boleh dianggap membuktikan input tanpa preferensi.
- **Status kegagalan perlu diperjelas.** Cabang fallback saat ini memetakan status selain `OPTIMAL`, `FEASIBLE`, dan `INFEASIBLE` menjadi `Belum ditemukan`; `MODEL_INVALID` perlu dibedakan dari `UNKNOWN` pada pengembangan berikutnya.
- **Skalabilitas belum dibuktikan.** Enumerasi kombinasi waktu dan resource dapat membesarkan model. Dataset contoh belum menjadi benchmark skala produksi.
- **Integrasi produk belum tersedia.** API, database, antrean job, pembatalan, validasi hasil independen, pemeriksaan revisi terbaru, dan publikasi atomik masih perlu dibangun.

Prioritas pengembangan adalah melengkapi validasi dan kontrak hasil, menambahkan pengujian serta validator independen, mengukur performa pada dataset lebih besar, lalu membangun integrasi dan mekanisme publikasi jadwal.

## 15. Dokumen rujukan dalam repositori

- [Skenario pilot pelatihan v1.0.0](data/pelatihan/Schedovyn-Skenario-Pilot-Pelatihan-v1.0.0.md)
- [Snapshot input pelatihan](data/pelatihan/Snapshot-input.json)
- [Assignment acuan pelatihan](data/pelatihan/Assignment-acuan.json)
- [Contoh hasil solver pelatihan](data/pelatihan/solver-result.json)
- [Skenario pilot bengkel v1.0.0](data/bengkel/Schedovyn-Skenario-Pilot-Bengkel-v1.0.0.md)
- [Skenario pilot layanan pelanggan v1.0.0](data/layanan-pelanggan/Schedovyn-Skenario-Pilot-Shift-Layanan-Pelanggan-v1.0.0.md)

Dokumen skenario memuat kebutuhan dan kriteria pembuktian pilot. README ini menghubungkannya dengan implementasi yang tersedia, termasuk perbedaan dan pekerjaan lanjutan yang masih diperlukan.
