# Schedovyn — Skenario Pilot Shift Layanan Pelanggan

Versi: 1.0.0 • Tahap: 1 — data dan aturan • Tanggal: 16 September 2026

Acuan: Schedovyn-PRD-v1.0.0.md; struktur mengikuti dokumen skenario pilot pelatihan dan bengkel.

Dokumen ini menetapkan contoh penjadwalan tim layanan pelanggan dengan beberapa petugas dalam satu shift. Dataset, nama, durasi, dan kebijakan operasional bersifat sintetis. Dokumen berisi aturan, jadwal acuan, kasus uji, snapshot JSON, dan assignment JSON; tidak memuat implementasi atau hasil eksekusi solver.

## 1. Tujuan dan batas pilot

Koordinator harus mengisi tiga blok layanan harian dan satu blok callback. Shift domestik membutuhkan satu ketua dan dua agen; shift berbahasa Inggris membutuhkan satu ketua dan satu agen. Semua petugas harus berbeda dalam satu occurrence dan tersedia sepanjang shift. Masing-masing petugas memakai satu workstation.

Callback merupakan blok kerja untuk menindaklanjuti pelanggan, dengan waktu mulai fleksibel. Panggilan individual tidak dimodelkan sebagai activity. Jumlah petugas adalah kebutuhan operasional yang sudah ditetapkan, bukan hasil prediksi volume panggilan.

| Parameter | Keputusan pilot |
| --- | --- |
| Organisasi | Pusat Layanan Contoh; workspace WS-SUPPORT |
| Horizon | Senin, 21 September–Rabu, 23 September 2026, inklusif |
| Zona waktu | Asia/Makassar; semua jam WITA (UTC+08:00) |
| Jam operasional | Senin–Jumat 08:00–12:00 dan 13:00–16:00 |
| Istirahat | 12:00–13:00; tidak ada activity yang melintasinya |
| Resolusi waktu | 30 menit |
| Skala | 7 resource, 4 activity, 12 occurrence wajib |
| Total durasi occurrence | 1.980 menit; berbeda dari total menit kerja seluruh petugas |
| Keputusan engine | Pemilihan petugas pada setiap role; waktu mulai callback |
| Input tetap | Tanggal occurrence, durasi, jendela layanan, jumlah petugas, unit workstation, dan kunci |
| Batas pencarian tahap berikutnya | 60 detik waktu solver, sesuai default PRD |

Jendela A01–A03 sama panjang dengan durasinya sehingga waktu shift sudah ditentukan oleh input. Ini bukan tiga kunci tambahan: operator tetap dapat mengubah definisi jendela pada revisi input. A04 memiliki jendela lebih lebar sehingga waktu callback dapat dipilih engine.

Pilot memodelkan shift sederhana pada satu hari. Tidak ada shift lintas tengah malam, pergantian petugas di tengah shift, jeda istirahat bergilir di dalam shift, aturan jarak antarsift, batas mingguan, atau pemerataan beban. Aturan lanjutan tersebut memerlukan cakupan tersendiri sesuai PRD. Batas 420 menit adalah parameter contoh, bukan klaim kepatuhan ketenagakerjaan.

Tanggal occurrence tetap mengikuti recurrence. Shift Rabu tidak boleh dipindahkan ke Selasa untuk memperbaiki skor atau menghindari ketidaktersediaan.

### 1.1 Hal yang dibuktikan oleh skenario

| Kebutuhan | Representasi |
| --- | --- |
| Dua agen untuk satu shift | Satu requirement agents dengan select_count = 2 |
| Ketua dan agen harus orang berbeda | Larangan memakai resource yang sama pada role lead dan agents |
| Kemampuan bahasa | Tag id dan en pada employee |
| Senior dapat menjadi ketua atau agen | S1/S2 berada pada beberapa daftar kandidat, tetapi tidak boleh mengisi dua role sekaligus |
| Lima tempat kerja yang identik | Pool DESK berkapasitas serentak 5 |
| Tiga petugas menggunakan tiga workstation | Satu resource pool dipilih, dengan units_per_selected_resource = 3 |
| Layanan tetap dan callback fleksibel | Durasi serta allowed_windows berbeda menurut activity |

Jumlah orang dan jumlah unit tidak boleh disamakan: dua agen berarti memilih dua employee berbeda masing-masing satu unit; tiga workstation berarti memilih satu pool dan memakai tiga unit kapasitasnya.

## 2. Data resource

| ID | Nama / jenis | Tag kemampuan | Kapasitas serentak | Batas beban harian |
| --- | --- | --- | --- | --- |
| S1 | Alya / employee | id, en, senior | 1 | 420 menit |
| S2 | Bagas / employee | id, en, senior | 1 | 420 menit |
| S3 | Citra / employee | id, en | 1 | 420 menit |
| S4 | Damar / employee | id | 1 | 420 menit |
| S5 | Eka / employee | id | 1 | 420 menit |
| S6 | Farah / employee | id, en | 1 | 420 menit |
| DESK | Pool Workstation / workstation_pool | support_terminal | 5 | Tidak dikonfigurasi |

Semua resource aktif dan berada dalam WS-SUPPORT. DESK merepresentasikan lima paket identik, masing-masing terdiri dari meja, komputer, headset, dan akses aplikasi. Semua paket mendukung layanan domestik, bahasa Inggris, dan callback. Nomor meja tidak ditentukan oleh engine.

Ketua juga memakai satu workstation selama seluruh shift. Pool tidak menyatakan bahwa satu petugas dapat melayani beberapa activity bersamaan; kapasitas setiap employee tetap satu.

### 2.1 Ketersediaan dan override

Seluruh resource mengikuti jam operasional, kecuali:

| Resource | Tanggal | Seluruh jendela tersedia pengganti | Alasan |
| --- | --- | --- | --- |
| S1 | 2026-09-22 | 08:00–12:00 | Tidak tersedia sore |
| S6 | 2026-09-23 | 13:00–16:00 | Tidak tersedia pagi |

Override menggantikan seluruh pola ketersediaan tanggal tersebut. Daftar kosong berarti tidak tersedia seharian. Kalender organisasi tetap membatasi override; override tidak membuka jam tutup atau hari libur.

### 2.2 Booking dari jadwal terbit lain

| ID | Versi terbit | Resource | Unit | Tanggal | Waktu | Keterangan |
| --- | --- | --- | --- | --- | --- | --- |
| B01 | EXT-DESK-V1 | DESK | 2 | 2026-09-22 | 13:00–15:00 | Dua workstation digunakan tim lain |

Booking hanya memakai dua unit DESK, tanpa memakai S1–S6. Booking tetap tidak dapat digeser dan tidak termasuk 12 occurrence wajib. Pada Selasa 13:00–15:00 hanya tiga unit tersisa untuk pilot.

Saat revisi, versi yang secara eksplisit digantikan tidak dihitung lagi sebagai booking tambahan. Booking dari versi lain tetap diperhitungkan.

## 3. Activity dan pembentukan occurrence

Keempat activity berulang setiap Senin, Selasa, dan Rabu selama 21–23 September, tanpa excluded_dates. Setiap activity menghasilkan tiga occurrence.

| ID | Activity | Durasi | Jendela diizinkan | Ketua | Agen | Workstation |
| --- | --- | --- | --- | --- | --- | --- |
| A01 | Layanan Domestik Pagi | 240 menit | 08:00–12:00 | 1 dari S1/S2 | 2 dari S1–S6 | 3 unit DESK |
| A02 | Layanan Bahasa Inggris | 180 menit | 09:00–12:00 | 1 dari S1/S2 | 1 dari S1/S2/S3/S6 | 2 unit DESK |
| A03 | Layanan Domestik Sore | 180 menit | 13:00–16:00 | 1 dari S1/S2 | 2 dari S1–S6 | 3 unit DESK |
| A04 | Callback Pelanggan | 60 menit | 08:00–12:00 atau 13:00–16:00 | Tidak diminta | 1 dari S1–S6 | 1 unit DESK |

Pada A01/A03, lead membutuhkan tag senior dan id; agents membutuhkan id. Pada A02, lead membutuhkan senior dan en; agents membutuhkan en. A04 meminta agen bertag id. Setiap petugas memakai satu unit employee sepanjang durasi.

Daftar kandidat adalah pilihan alternatif yang sudah memenuhi jenis/tag. Ketersediaan, kapasitas, dan perbedaan orang tetap harus diperiksa setelah pemilihan. Kandidat yang tercantum tidak otomatis boleh dipakai pada semua jam.

| Tanggal | A01 | A02 | A03 | A04 |
| --- | --- | --- | --- | --- |
| 2026-09-21 | O01 | O02 | O03 | O04 |
| 2026-09-22 | O05 | O06 | O07 | O08 |
| 2026-09-23 | O09 | O10 | O11 | O12 |

Occurrence dibentuk sebelum solver berjalan. Mengubah recurrence atau pengecualian tanggal harus memperbarui occurrence dan input_revision. Sistem tidak boleh menghapus occurrence wajib karena kekurangan petugas.

## 4. Constraint wajib

ID aturan berikut berlaku lokal pada schema pilot layanan pelanggan ini.

| ID | Aturan dan pemeriksaan | Acuan PRD |
| --- | --- | --- |
| H01 | Setiap occurrence wajib mendapat tepat satu assignment lengkap, tanpa duplikat atau occurrence asing. | §4.2, FR-11, FR-16 |
| H02 | Total unit serentak setiap resource tidak melebihi kapasitas, termasuk booking terbit lain. | §4.2, §4.4 |
| H03 | Seluruh interval berada dalam ketersediaan setiap resource setelah override. | FR-05, §4.4 |
| H04 | Resource aktif, milik workspace yang sama, sesuai jenis/tag/kandidat; setiap role memilih tepat select_count resource berbeda dengan unit yang ditentukan. | FR-02, FR-06, §4.2 |
| H05 | Durasi utuh, kontinu pada tanggal occurrence, dalam satu allowed_window, dan seluruh batas selaras slot. | §4.2, §6.1 |
| H06 | Interval berada dalam jam operasional, di luar hari libur, dan tidak melintasi istirahat. | §4.4 |
| H07 | O01 tetap 21 September 08:00–12:00 dengan lead S1, agents S4/S5, dan 3 unit DESK. | FR-15 |
| H08 | Total beban harian setiap employee maksimal 420 menit, termasuk booking terbit lain yang memakai employee tersebut. | §4.4 |
| H09 | Booking eksternal tetap berlaku; versi yang digantikan tidak dihitung ganda. | §4.2, FR-16 |
| H10 | Pada A01/A02/A03, pilihan lead dan agents harus saling terpisah. Satu employee tidak boleh dihitung sebagai ketua sekaligus agen pada occurrence yang sama. | §4.2 |

Interval menggunakan [start, end): callback 08:00–09:00 tidak bertabrakan dengan shift yang dimulai 09:00. Istirahat 12:00–13:00 memisahkan shift pagi dan sore. Setiap orang dalam satu shift hadir selama seluruh interval; mengganti orang di tengah shift tidak dianggap assignment lengkap.

H04 juga melarang daftar agents berisi S4 dua kali untuk memenuhi select_count = 2. H10 memeriksa perbedaan lintas role, walaupun S1/S2 memang tercantum sebagai kandidat pada kedua role.

Beban employee adalah jumlah durasi × unit pada tanggal lokal. Pada pilot setiap employee selalu menggunakan satu unit. Pemakaian DESK mengikuti tiga, dua, atau satu unit sesuai activity, bukan selalu satu unit per occurrence. Tidak ada batas menit harian DESK selain kalender dan kapasitas serentak.

### 4.1 Validasi awal dan diagnosis

Sebelum generate, periksa referensi, identitas workspace, status aktif, field wajib, durasi/unit positif, kandidat unik, jumlah pilihan, tag, recurrence/occurrence, keselarasan slot, dan konflik langsung pada kunci. Jumlah unit DESK pada input harus sama dengan jumlah petugas yang diminta activity dalam kontrak pilot ini; assignment tidak boleh mengurangi unit untuk menghindari konflik.

Kesalahan input ditolak sebagai kesalahan validasi. Ketidakmungkinan gabungan aturan yang dibuktikan pencarian dilaporkan Infeasible. Diagnosis yang belum terbukti harus disebut indikasi.

Contoh pesan: “O08 pada 22 September 14:00–15:00 membutuhkan 1 workstation, sementara O07 memakai 3 dan B01 memakai 2. Total 6 melebihi kapasitas DESK 5 (H02/H09).”

## 5. Preference dan objective

Setiap pasangan preference–occurrence bernilai 1 jika terpenuhi, selain itu 0. Preference pada role dengan beberapa orang dinilai sekali per occurrence, bukan sekali per orang.

| ID | Preference | Target activity | Bobot | Pasangan relevan | Bobot total |
| --- | --- | --- | --- | --- | --- |
| P01 | Callback seluruhnya di pagi hari 08:00–12:00 | A04 | Tinggi = 5 | 3 | 15 |
| P02 | Ketua shift domestik adalah S1 | A01, A03 | Sedang = 3 | 6 | 18 |
| P03 | Agen layanan bahasa Inggris adalah S3 | A02 | Sedang = 3 | 3 | 9 |
| P04 | S6 termasuk salah satu agen shift domestik sore | A03 | Rendah = 1 | 3 | 3 |
| **Total** | | | | **15** | **45** |

Objective: maksimalkan jumlah bobot terpenuhi setelah semua occurrence lengkap dan seluruh constraint dipenuhi. Skor = bobot terpenuhi / bobot relevan × 100.

P04 terpenuhi jika daftar agents mengandung S6. Menambahkan petugas melebihi jumlah yang diminta bukan cara menaikkan skor: hal itu melanggar H04. Urutan daftar agen tidak memengaruhi skor. Resource preference hanya memeriksa role target; S1 yang menjadi agen tidak memenuhi P02 yang menargetkan lead.

Bobot tinggi bukan prioritas mutlak atas gabungan bobot lain. Preference yang relevan tetapi mustahil dipenuhi tetap masuk penyebut, termasuk P02 pada O07 ketika S1 tidak tersedia sore. Preference nonaktif atau tanpa occurrence target tidak masuk penyebut. Jika penyebut nol, skor null dan tampilkan “Tidak ada preference”.

Bandingkan skor hanya pada snapshot, aturan, dan bobot yang sama. Pemerataan beban bukan objective pilot.

## 6. Contoh jadwal lengkap yang valid

Jadwal berikut disusun sebagai acuan data, bukan hasil solver atau klaim Optimal. Semua pilihan orang dalam satu baris berlaku sepanjang intervalnya.

| Occurrence | Tanggal | Waktu WITA | Activity | Ketua | Agen | Unit DESK |
| --- | --- | --- | --- | --- | --- | --- |
| O01 | 2026-09-21 | 08:00–12:00 | A01 | S1 | S4, S5 | 3 |
| O02 | 2026-09-21 | 09:00–12:00 | A02 | S2 | S3 | 2 |
| O03 | 2026-09-21 | 13:00–16:00 | A03 | S2 | S4, S6 | 3 |
| O04 | 2026-09-21 | 08:00–09:00 | A04 | — | S6 | 1 |
| O05 | 2026-09-22 | 08:00–12:00 | A01 | S1 | S4, S5 | 3 |
| O06 | 2026-09-22 | 09:00–12:00 | A02 | S2 | S6 | 2 |
| O07 | 2026-09-22 | 13:00–16:00 | A03 | S2 | S3, S5 | 3 |
| O08 | 2026-09-22 | 15:00–16:00 | A04 | — | S4 | 1 |
| O09 | 2026-09-23 | 08:00–12:00 | A01 | S1 | S4, S5 | 3 |
| O10 | 2026-09-23 | 09:00–12:00 | A02 | S2 | S3 | 2 |
| O11 | 2026-09-23 | 13:00–16:00 | A03 | S1 | S4, S6 | 3 |
| O12 | 2026-09-23 | 13:00–14:00 | A04 | — | S5 | 1 |

Pada 09:00–12:00 setiap hari, dua shift memakai lima orang berbeda dan seluruh lima workstation. Callback pagi pada acuan selesai sebelum layanan bahasa Inggris dimulai. Selasa sore, O08 menunggu B01 selesai pukul 15:00. S1 tidak ditugaskan Selasa sore dan S6 tidak ditugaskan Rabu pagi.

### 6.1 Beban harian petugas

| Resource | Senin | Selasa | Rabu | Batas per hari |
| --- | --- | --- | --- | --- |
| S1 | 240 | 240 | 420 | 420 |
| S2 | 360 | 360 | 180 | 420 |
| S3 | 180 | 180 | 180 | 420 |
| S4 | 420 | 300 | 420 | 420 |
| S5 | 240 | 420 | 300 | 420 |
| S6 | 240 | 180 | 180 | 420 |
| **Total menit kerja** | **1.680** | **1.680** | **1.680** | — |

Durasi occurrence per hari = 240 + 180 + 180 + 60 = 660 menit, sehingga total tiga hari 1.980 menit. Total menit kerja petugas per hari = (240 × 3) + (180 × 2) + (180 × 3) + (60 × 1) = 1.680 menit, atau 5.040 menit selama horizon. Perbedaan ini penting agar laporan tidak menyamakan durasi shift dengan beban seluruh tim.

### 6.2 Skor jadwal acuan

| Preference | Terpenuhi | Tidak terpenuhi | Bobot diperoleh / relevan |
| --- | --- | --- | --- |
| P01 | O04 | O08, O12 | 5 / 15 |
| P02 | O01, O05, O09, O11 | O03, O07 | 12 / 18 |
| P03 | O02, O10 | O06 | 6 / 9 |
| P04 | O03, O11 | O07 | 2 / 3 |
| **Total** | | | **25 / 45 = 55,56%** |

Pembanding valid: ubah hanya O08 menjadi 22 September 08:00–09:00 dengan agen S3. S3 belum bertugas pagi itu dan total bebannya menjadi 240 menit. Pemakaian DESK pada 08:00–09:00 adalah 3 + 1 = 4. P01 bertambah 5, sehingga bobot menjadi **30/45 = 66,67%**; beban S4 Selasa turun menjadi 240 menit. Ini acuan evaluator, bukan target optimum.

## 7. Varian kasus uji untuk tahap berikutnya

Setiap kasus dimulai dari dataset utama dan menerapkan hanya perubahan yang dinyatakan. Edit assignment menguji validator; perubahan input menguji validasi awal/pencarian. Ekspektasi berikut belum merupakan hasil eksekusi solver.

| ID | Perubahan / tindakan | Ekspektasi |
| --- | --- | --- |
| C01 | Generate dataset utama. | Hasil lengkap 12 occurrence dan valid; status Optimal/Feasible mengikuti bukti runtime. |
| C02 | Hapus S6 dari agents O03. | Tolak: hanya satu agen, padahal dibutuhkan dua (H04). |
| C03 | Tetapkan agents O03 menjadi S4, S4. | Tolak: resource duplikat tidak memenuhi dua orang berbeda (H04). |
| C04 | Tetapkan agents O03 menjadi S2, S6, lead tetap S2. | Tolak: S2 mengisi lead sekaligus agents (H10). |
| C05 | Tambahkan S5 sebagai agen ketiga O03. | Tolak: select_count harus tepat dua, bukan minimal dua (H04). |
| C06 | Tetapkan agen O02 menjadi S4. | Tolak: tidak mempunyai tag en/bukan kandidat (H04); juga bentrok O01 (H02). |
| C07 | Tetapkan lead O02 menjadi S1. | Tolak: S1 sedang menjadi lead O01 (H02). |
| C08 | Tetapkan lead O07 menjadi S1. | Tolak: override Selasa melarang S1 sore (H03). |
| C09 | Tetapkan agen O10 menjadi S6. | Tolak: S6 tidak tersedia Rabu pagi (H03), walaupun memiliki tag en. |
| C10 | Edit O08 menjadi 14:00–15:00 dengan S4 tetap. | Tolak: 3 unit O07 + 1 unit O08 + 2 unit B01 = 6 > 5 (H02/H09). S4 sendiri tidak bentrok. |
| C11 | Edit O04 menjadi 09:00–10:00 dengan S6 tetap. | Tolak: O01/O02 memakai 5 workstation; O04 menaikkan total ke 6 (H02), walaupun S6 tersedia. |
| C12 | Edit units DESK O03 dari 3 menjadi 1. | Tolak: assignment tidak memenuhi kebutuhan unit yang dibekukan input (H04). |
| C13 | Edit O04 menjadi 11:30–12:30. | Tolak: melintasi istirahat/jendela activity (H05/H06); validator boleh melaporkan pelanggaran lain yang juga terjadi. |
| C14 | Edit O08 menjadi 15:00–15:30; terpisah, coba 14:45–15:45. | Tolak karena durasi salah atau batas tidak selaras slot (H05); varian kedua juga melewati booking DESK. |
| C15 | Edit lead O03 dari S2 ke S1 tanpa mengubah lainnya. | Valid; beban S1 Senin menjadi 420, P02 bertambah 3, skor 28/45. |
| C16 | Edit agen O04 dari S6 ke S4, waktu tetap. | Tolak: S4 bentrok O01 (H02) dan total beban hariannya menjadi 480 > 420 (H08). |
| C17 | Evaluasi acuan lalu ubah hanya O08 menjadi 08:00–09:00 dengan S3. | Dua jadwal valid; bobot 25 → 30, penyebut tetap 45. |
| C18 | Hapus assignment O12. | Kelengkapan 11/12; tolak publikasi; hasil parsial tidak diberi status Feasible/Optimal. |
| C19 | Hapus semua preference. | Tetap wajib menghasilkan jadwal lengkap; skor null, “Tidak ada preference”. |
| C20 | Ubah input: DESK.concurrent_capacity menjadi 4. | Mustahil: A01/A02 harus overlap 09:00–12:00 dengan kebutuhan 3 + 2 unit. Perlu bukti awal atau Infeasible, bukan timeout. |
| C21 | Ubah input: kunci O02 memakai S1 sebagai lead, 09:00–12:00, agen S3 dan DESK 2. | Validasi awal menolak konflik dengan kunci O01; tidak menyamarkan masalah sebagai status pencarian. |
| C22 | Tambahkan 23 September ke excluded_dates A04 lalu bentuk ulang occurrence. | O12 dihapus; 11 occurrence dan bobot relevan 40. |
| C23 | Tetapkan 23 September hari libur, seluruh occurrence Rabu tetap wajib. | Tidak ada penempatan valid hari itu; hari libur tidak menghapus kewajiban secara diam-diam. |
| C24 | Simulasikan versi SUPPORT-V1 berisi acuan; draft menyatakan menggantikannya. | Assignment SUPPORT-V1 tidak dihitung ganda; B01 tetap berlaku. |
| C25 | Setelah job dibuat, ubah sumber menjadi S1 tidak tersedia Senin. | Snapshot lama tidak berubah; tolak publikasi hasil kedaluwarsa dan deteksi konflik kunci O01 pada validasi terbaru. |
| C26 | Tukar urutan agents O01 dari S4/S5 menjadi S5/S4. | Assignment dan kunci tetap setara; pilihan adalah himpunan, bukan posisi berurutan. Skor tetap 25/45. |

### 7.1 Fixture kekurangan ketua pada dua shift bersamaan

Isolasi A01/A02 dan O01/O02 pada 21 September. Hapus kunci, booking, dan preference; ubah recurrence menjadi hanya Senin dalam horizon satu hari. Batasi kandidat lead kedua activity menjadi hanya S1. Pertahankan jendela, durasi, kandidat agents, dan DESK kapasitas 5.

Masing-masing shift dapat dijadwalkan sendiri, tetapi keduanya membutuhkan S1 pada 09:00–12:00. Tidak ada jadwal lengkap. Mesin harus membuktikan ketidakmungkinan atau pemeriksa awal menolaknya dengan bukti konflik kebutuhan. Menambahkan kandidat agen tidak menyelesaikan kekurangan ketua.

### 7.2 Fixture batas beban tanpa benturan waktu

Isolasi A01/A03 dan occurrence O09/O11 pada 23 September. Hapus kunci, booking, dan preference, recurrence hanya Rabu. Batasi lead kedua activity ke S1 dan max_daily_minutes S1 menjadi 360.

Kedua shift tidak overlap, tetapi memerlukan 240 + 180 = 420 menit S1. Masing-masing dapat dipenuhi sendiri; gabungannya mustahil karena H08. Pada varian pembanding dengan batas 420, kedua shift dapat berjalan dengan agen S4/S5 pagi dan S4/S6 sore.

### 7.3 Fixture preference gagal tetapi jadwal valid

Isolasi A03/O07 pada 22 September; tanpa kunci atau booking, recurrence hanya Selasa. Pertahankan override S1 hanya pagi dan preference P02 dengan target hanya A03.

S2 dapat menjadi lead dengan agen S3/S5. P02 mustahil terpenuhi, tetapi seluruh constraint terpenuhi. Skor 0/3 = 0%. Engine dapat menyatakan Optimal jika telah membuktikan optimum, meskipun skor bukan 100%.

Setiap fixture memakai dataset_id berbeda dan revisi input baru. Daftar recurrence, occurrence, kunci, dan target preference harus konsisten. Varian tidak boleh membawa kewajiban dari tanggal yang telah dikeluarkan.

## 8. Kontrak hasil dan kriteria penerimaan

| Status PRD | Bukti yang diperlukan |
| --- | --- |
| Optimal | Jadwal lengkap valid; engine membuktikan optimum objective pada snapshot tersebut. |
| Feasible | Jadwal lengkap valid ditemukan; optimum belum terbukti. |
| Infeasible | Engine membuktikan tidak ada jadwal lengkap yang memenuhi seluruh constraint. |
| Belum ditemukan | Batas waktu tercapai tanpa solusi lengkap dan tanpa bukti infeasible. |
| Gagal / dibatalkan | Gangguan teknis atau pembatalan; bukan bukti infeasible. |

Status job, status solusi, dan status versi terpisah. Versi mengikuti Draft → Published → Archived. Input/model yang salah dilaporkan sebagai kesalahan, bukan bukti bahwa kebutuhan bisnis mustahil.

Dataset kecil tidak menjamin munculnya status Feasible atau Belum ditemukan. Uji kontrak status menggunakan hasil terkontrol; pada uji integrasi catat hasil runtime sebenarnya. Jangan menganggap timeout sangat kecil pasti menghasilkan status tertentu. Pembatalan dan kegagalan worker memerlukan pengujian kontrol proses.

Kriteria penerimaan tahap solver:

1. Seluruh 12 occurrence wajib mendapat assignment lengkap dan nol pelanggaran validator terpisah.
2. select_count memilih jumlah employee berbeda yang tepat; lead tidak dihitung ulang sebagai agents.
3. Unit DESK dijumlahkan sesuai kebutuhan tiap activity dan booking eksternal.
4. Kunci O01, override, kemampuan bahasa, batas harian, dan seluruh jendela dipenuhi.
5. Evaluator menghasilkan 25/45 pada acuan serta 30/45 pada pembanding O08.
6. Kelengkapan, kesalahan assignment, kesalahan input, ketidakmungkinan, dan timeout dibedakan sesuai bukti.
7. Urutan resource dalam role tidak mengubah arti assignment, skor, atau kunci.

Catatan hasil minimum: schema/dataset/input revision, identitas job, status job/solusi, assignment lengkap dengan unit, jumlah wajib/terjadwal, occurrence belum terjadwal, pelanggaran validator, rincian preference, bobot terpenuhi/relevan, skor atau null, waktu antre/solver terpisah, alasan berhenti, diagnosis dan tingkat kepastian, serta versi runtime dan konfigurasi komputasi.

Publikasi hanya boleh dilakukan setelah semua occurrence lengkap, constraint lulus validator terpisah, input mutakhir, serta tidak bentrok dengan jadwal terbit terbaru. Validasi dan penggantian versi harus atomik pada implementasi produk. Dokumen ini menetapkan acuan, bukan menguji transaksi publikasi.

## Lampiran A — Snapshot input contoh

Kontrak contoh `pilot-support-shifts-1.0.0`, bukan schema API/database final. Semua entitas mewarisi WS-SUPPORT dari snapshot; booking juga menyimpan workspace_id. ID aturan merujuk definisi dokumen ini.

Tanggal ISO dan jam HH:MM adalah waktu lokal Asia/Makassar. ISO weekday 1=Senin hingga 7=Minggu. Batas akhir periode/recurrence inklusif; batas akhir interval eksklusif. Override menggantikan pola mingguan pada tanggal terkait. max_daily_minutes yang tidak ada berarti tidak ada batas harian tambahan.

Setiap requirement memilih tepat select_count ID berbeda dari candidate_ids atau fixed_resource_id. Setiap pilihan memakai units_per_selected_resource. distinct_resource_roles menyatakan bahwa pilihan pada role yang tercantum tidak boleh saling beririsan; ini representasi eksplisit aturan perbedaan resource pada PRD §4.2.

Assignment dan kunci memakai peta role ke daftar objek {resource_id, units}, termasuk role yang hanya memilih satu resource. Bentuk ini mendukung banyak petugas dan jumlah unit secara eksplisit. Urutan elemen daftar tidak bermakna; daftar harus bebas duplikat. Schema ini berbeda dari contoh pelatihan/bengkel yang memetakan role langsung ke satu ID; parser/validator harus mengenali schema_version sebelum membaca data, bukan mengasumsikan kompatibilitas langsung.

Preference resource memakai match = any_selected: pasangan terpenuhi bila sedikitnya satu resource yang diutamakan ada pada role target. Nilainya tetap satu kali per pasangan preference–occurrence. Snapshot utama hanya memakai satu preferred resource per preference.

```json
{
  "schema_version": "pilot-support-shifts-1.0.0",
  "dataset_id": "SUPPORT-BASE-01",
  "input_revision": 1,
  "workspace": {"id": "WS-SUPPORT","name": "Pusat Layanan Contoh","timezone": "Asia/Makassar"},
  "period": {"start_date": "2026-09-21","end_date": "2026-09-23","slot_minutes": 30},
  "calendar": {"iso_weekdays": [1,2,3,4,5],"open_windows": [["08:00","12:00"],["13:00","16:00"]],"holidays": []},
  "availability_profiles": [
    {"id": "WORKDAYS","iso_weekdays": [1,2,3,4,5],"windows": [["08:00","12:00"],["13:00","16:00"]]}
  ],
  "resources": [
    {"id": "S1","name": "Alya","type": "employee","tags": ["id","en","senior"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "S2","name": "Bagas","type": "employee","tags": ["id","en","senior"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "S3","name": "Citra","type": "employee","tags": ["id","en"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "S4","name": "Damar","type": "employee","tags": ["id"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "S5","name": "Eka","type": "employee","tags": ["id"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "S6","name": "Farah","type": "employee","tags": ["id","en"],"concurrent_capacity": 1,"max_daily_minutes": 420,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "DESK","name": "Pool Workstation","type": "workstation_pool","tags": ["support_terminal"],"concurrent_capacity": 5,"active": true,"availability_profile_id": "WORKDAYS"}
  ],
  "availability_overrides": [
    {"resource_id": "S1","date": "2026-09-22","available_windows": [["08:00","12:00"]],"reason": "Tidak tersedia sore"},
    {"resource_id": "S6","date": "2026-09-23","available_windows": [["13:00","16:00"]],"reason": "Tidak tersedia pagi"}
  ],
  "activities": [
    {"id": "A01","name": "Layanan Domestik Pagi","active": true,"duration_minutes": 240,"allowed_windows": [["08:00","12:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,2,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "lead","type": "employee","required_tags": ["senior","id"],"candidate_ids": ["S1","S2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "agents","type": "employee","required_tags": ["id"],"candidate_ids": ["S1","S2","S3","S4","S5","S6"],"select_count": 2,"units_per_selected_resource": 1},{"role": "workstations","type": "workstation_pool","required_tags": ["support_terminal"],"fixed_resource_id": "DESK","select_count": 1,"units_per_selected_resource": 3}],"distinct_resource_roles": [["lead","agents"]]},
    {"id": "A02","name": "Layanan Bahasa Inggris","active": true,"duration_minutes": 180,"allowed_windows": [["09:00","12:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,2,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "lead","type": "employee","required_tags": ["senior","en"],"candidate_ids": ["S1","S2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "agents","type": "employee","required_tags": ["en"],"candidate_ids": ["S1","S2","S3","S6"],"select_count": 1,"units_per_selected_resource": 1},{"role": "workstations","type": "workstation_pool","required_tags": ["support_terminal"],"fixed_resource_id": "DESK","select_count": 1,"units_per_selected_resource": 2}],"distinct_resource_roles": [["lead","agents"]]},
    {"id": "A03","name": "Layanan Domestik Sore","active": true,"duration_minutes": 180,"allowed_windows": [["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,2,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "lead","type": "employee","required_tags": ["senior","id"],"candidate_ids": ["S1","S2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "agents","type": "employee","required_tags": ["id"],"candidate_ids": ["S1","S2","S3","S4","S5","S6"],"select_count": 2,"units_per_selected_resource": 1},{"role": "workstations","type": "workstation_pool","required_tags": ["support_terminal"],"fixed_resource_id": "DESK","select_count": 1,"units_per_selected_resource": 3}],"distinct_resource_roles": [["lead","agents"]]},
    {"id": "A04","name": "Callback Pelanggan","active": true,"duration_minutes": 60,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,2,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "agents","type": "employee","required_tags": ["id"],"candidate_ids": ["S1","S2","S3","S4","S5","S6"],"select_count": 1,"units_per_selected_resource": 1},{"role": "workstations","type": "workstation_pool","required_tags": ["support_terminal"],"fixed_resource_id": "DESK","select_count": 1,"units_per_selected_resource": 1}],"distinct_resource_roles": []}
  ],
  "occurrences": [
    {"id": "O01","activity_id": "A01","date": "2026-09-21","required": true},
    {"id": "O02","activity_id": "A02","date": "2026-09-21","required": true},
    {"id": "O03","activity_id": "A03","date": "2026-09-21","required": true},
    {"id": "O04","activity_id": "A04","date": "2026-09-21","required": true},
    {"id": "O05","activity_id": "A01","date": "2026-09-22","required": true},
    {"id": "O06","activity_id": "A02","date": "2026-09-22","required": true},
    {"id": "O07","activity_id": "A03","date": "2026-09-22","required": true},
    {"id": "O08","activity_id": "A04","date": "2026-09-22","required": true},
    {"id": "O09","activity_id": "A01","date": "2026-09-23","required": true},
    {"id": "O10","activity_id": "A02","date": "2026-09-23","required": true},
    {"id": "O11","activity_id": "A03","date": "2026-09-23","required": true},
    {"id": "O12","activity_id": "A04","date": "2026-09-23","required": true}
  ],
  "enabled_hard_rules": ["H01","H02","H03","H04","H05","H06","H07","H08","H09","H10"],
  "locks": [
    {"occurrence_id": "O01","date": "2026-09-21","start": "08:00","end": "12:00","resources": {"lead": [{"resource_id": "S1","units": 1}],"agents": [{"resource_id": "S4","units": 1},{"resource_id": "S5","units": 1}],"workstations": [{"resource_id": "DESK","units": 3}]}}
  ],
  "published_bookings": [
    {"id": "B01","workspace_id": "WS-SUPPORT","schedule_version_id": "EXT-DESK-V1","date": "2026-09-22","start": "13:00","end": "15:00","resource_units": {"DESK": 2},"label": "Workstation digunakan tim lain"}
  ],
  "replaces_schedule_version_id": null,
  "preferences": [
    {"id": "P01","type": "preferred_time","activity_ids": ["A04"],"weight": 5,"window": ["08:00","12:00"],"match": "full_interval","active": true},
    {"id": "P02","type": "preferred_resource","activity_ids": ["A01","A03"],"weight": 3,"role": "lead","resource_ids": ["S1"],"match": "any_selected","active": true},
    {"id": "P03","type": "preferred_resource","activity_ids": ["A02"],"weight": 3,"role": "agents","resource_ids": ["S3"],"match": "any_selected","active": true},
    {"id": "P04","type": "preferred_resource","activity_ids": ["A03"],"weight": 1,"role": "agents","resource_ids": ["S6"],"match": "any_selected","active": true}
  ],
  "solver_budget_seconds": 60
}
```

## Lampiran B — Assignment acuan

Setiap role berisi daftar pilihan resource dengan unit eksplisit. Role lead tidak muncul pada callback karena tidak diminta activity. Semua assignment berikut disusun sebagai acuan valid; tidak menyimpan status hasil solver.

```json
[
  {
    "occurrence_id": "O01",
    "date": "2026-09-21",
    "start": "08:00",
    "end": "12:00",
    "resources": {
      "lead": "S1",
      "agents": [
        "S4",
        "S5"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O02",
    "date": "2026-09-21",
    "start": "09:00",
    "end": "12:00",
    "resources": {
      "lead": "S2",
      "agents": "S3",
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O03",
    "date": "2026-09-21",
    "start": "13:00",
    "end": "16:00",
    "resources": {
      "lead": "S2",
      "agents": [
        "S4",
        "S6"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O04",
    "date": "2026-09-21",
    "start": "08:00",
    "end": "09:00",
    "resources": {
      "agents": "S6",
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O05",
    "date": "2026-09-22",
    "start": "08:00",
    "end": "12:00",
    "resources": {
      "lead": "S1",
      "agents": [
        "S4",
        "S5"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O06",
    "date": "2026-09-22",
    "start": "09:00",
    "end": "12:00",
    "resources": {
      "lead": "S2",
      "agents": "S6",
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O07",
    "date": "2026-09-22",
    "start": "13:00",
    "end": "16:00",
    "resources": {
      "lead": "S2",
      "agents": [
        "S3",
        "S5"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O08",
    "date": "2026-09-22",
    "start": "15:00",
    "end": "16:00",
    "resources": {
      "agents": "S4",
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O09",
    "date": "2026-09-23",
    "start": "08:00",
    "end": "12:00",
    "resources": {
      "lead": "S1",
      "agents": [
        "S4",
        "S5"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O10",
    "date": "2026-09-23",
    "start": "09:00",
    "end": "12:00",
    "resources": {
      "lead": "S2",
      "agents": "S3",
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O11",
    "date": "2026-09-23",
    "start": "13:00",
    "end": "16:00",
    "resources": {
      "lead": "S1",
      "agents": [
        "S4",
        "S6"
      ],
      "workstations": "DESK"
    }
  },
  {
    "occurrence_id": "O12",
    "date": "2026-09-23",
    "start": "13:00",
    "end": "14:00",
    "resources": {
      "agents": "S5",
      "workstations": "DESK"
    }
  }
]
```
