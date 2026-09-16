# Schedovyn — Skenario Pilot Penjadwalan Servis Kendaraan

Versi: 1.0.0 • Tahap: 1 — data dan aturan • Tanggal dokumen: 16 September 2026

Acuan: Schedovyn-PRD-v1.0.0.md dan struktur Schedovyn-Skenario-Pilot-Pelatihan-v1.0.0.md.

Dokumen ini menetapkan satu skenario alternatif untuk menguji model penjadwalan lintas industri: bengkel servis armada kendaraan. Isinya meliputi dataset sintetis, constraint, preference, jadwal acuan, varian pengujian, serta snapshot dan assignment dalam JSON. Seluruh nama, durasi, dan aturan operasional merupakan asumsi contoh. Dokumen ini tidak memuat implementasi atau hasil eksekusi solver.

## 1. Tujuan dan batas pilot

Koordinator bengkel harus menjadwalkan pekerjaan servis yang berbagi teknisi, bay servis, dan alat diagnostik. Kendaraan juga menjadi resource agar dua pekerjaan pada kendaraan yang sama tidak dijadwalkan bersamaan.

Setiap pekerjaan membutuhkan satu teknisi, satu kendaraan, dan satu bay selama seluruh durasi. Pekerjaan diagnostik membutuhkan tambahan satu unit alat scanner. Engine memilih jam mulai serta teknisi dan bay dari kandidat yang sesuai.

| Parameter | Keputusan pilot |
| --- | --- |
| Organisasi | Bengkel Armada Contoh; workspace WS-WORKSHOP |
| Horizon | Senin, 21 September–Rabu, 23 September 2026, inklusif |
| Zona waktu | Asia/Makassar; semua jam WITA (UTC+08:00) |
| Jam operasional | Senin–Jumat 08:00–12:00 dan 13:00–16:00 |
| Istirahat | 12:00–13:00; pekerjaan tidak boleh melintasinya |
| Resolusi | 30 menit |
| Skala | 12 resource, 8 activity, 10 occurrence wajib; 960 menit pekerjaan |
| Keputusan engine | Jam mulai, teknisi, dan bay dari kandidat |
| Input tetap | Tanggal occurrence, kendaraan, durasi, kebutuhan unit, dan kunci |
| Batas pencarian tahap berikutnya | 60 detik waktu solver, sesuai default PRD |

Armada sudah berada di lokasi sebelum pekerjaan dimulai. Perpindahan kendaraan, pembersihan bay, dan persiapan alat diasumsikan tidak membutuhkan jeda tambahan pada pilot. Setiap teknisi dan setiap bay dipakai penuh sepanjang interval pekerjaan. Suku cadang diasumsikan tersedia dan tidak dimodelkan sebagai persediaan.

Semua pekerjaan berdiri sendiri. Diagnostik bukan prasyarat wajib penggantian oli atau pemeriksaan rem. Diagnostik V1/V2 pada Senin dan Rabu merupakan dua pemeriksaan rutin independen. Pilot tidak mencakup urutan pekerjaan, pekerjaan terpecah, pengambilan kendaraan, waktu perjalanan, pemakaian alat hanya pada sebagian durasi, atau proses servis bertahap. Aturan urutan dan jeda memerlukan cakupan lanjutan sesuai PRD.

Tanggal tidak menjadi variabel optimasi. Pengulangan mingguan membentuk occurrence pada tanggal yang ditetapkan; engine hanya memilih waktu pada tanggal tersebut. A01 pada Rabu tidak boleh dipindahkan ke Selasa untuk memperbaiki skor.

### 1.1 Pemetaan konsep umum

| Konsep Schedovyn | Contoh pada bengkel |
| --- | --- |
| Resource manusia | Teknisi dengan tag kemampuan |
| Resource objek pekerjaan | Kendaraan yang sedang ditangani |
| Resource fasilitas | Bay servis umum atau bay dengan lift |
| Resource dengan kapasitas >1 | Pool dua scanner yang identik |
| Activity | Diagnostik, penggantian oli, pemeriksaan rem |
| Constraint | Teknisi sesuai kemampuan; bay tidak bentrok; scanner cukup |
| Preference | Diagnostik di pagi hari; teknisi tertentu diutamakan |

Model ini menguji kebutuhan resource yang bervariasi: tiga role untuk servis biasa dan empat role untuk diagnostik. Engine tidak boleh mengasumsikan semua industri selalu mempunyai role pengajar, kelompok, dan ruangan.

## 2. Data resource

| ID | Nama / jenis | Tag | Kapasitas serentak | Batas beban harian |
| --- | --- | --- | --- | --- |
| T1 | Teknisi Adi / technician | diagnostic | 1 | 240 menit |
| T2 | Teknisi Bima / technician | diagnostic, oil | 1 | 240 menit |
| T3 | Teknisi Candra / technician | oil, brake | 1 | 240 menit |
| BA | Bay Umum / service_bay | general | 1 | Tidak dikonfigurasi |
| BB | Bay Lift / service_bay | general, lift | 1 | Tidak dikonfigurasi |
| SCAN | Pool Scanner / equipment_pool | obd | 2 | Tidak dikonfigurasi |
| V1 | Mobil Armada 01 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |
| V2 | Mobil Armada 02 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |
| V3 | Mobil Armada 03 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |
| V4 | Mobil Armada 04 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |
| V5 | Mobil Armada 05 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |
| V6 | Mobil Armada 06 / vehicle | passenger_car | 1 | Tidak dikonfigurasi |

Semua resource aktif dan berada dalam WS-WORKSHOP. BA dan BB masing-masing menampung satu mobil. Seluruh kendaraan contoh kompatibel dengan kedua bay; atribut ukuran atau berat tidak digunakan pada pilot.

SCAN merepresentasikan dua alat identik yang dapat dipertukarkan. Setiap pekerjaan diagnostik memakai satu unit selama seluruh durasinya. Dua pekerjaan boleh memakai SCAN bersama; tiga pekerjaan bersamaan tidak boleh. Identitas nomor seri scanner tidak dilacak. Bila kelak alat memiliki kemampuan atau kalender berbeda, modelkan sebagai resource terpisah atau ubah representasi kapasitas secara eksplisit.

### 2.1 Ketersediaan dan override

Semua resource mengikuti jam operasional, kecuali:

| Resource | Tanggal | Seluruh jendela tersedia pengganti | Alasan |
| --- | --- | --- | --- |
| T1 | 2026-09-22 | 08:00–12:00 | Tidak tersedia sore |
| BB | 2026-09-22 | 10:00–12:00 dan 13:00–16:00 | Pemeliharaan lift pagi |

Override menggantikan seluruh pola ketersediaan pada tanggal tersebut. Daftar kosong berarti tidak tersedia seharian. Kalender organisasi tetap membatasi override; override tidak membuka jam tutup atau hari libur.

### 2.2 Booking dari jadwal terbit lain

| ID | Versi terbit | Resource dan unit | Tanggal | Waktu | Keterangan |
| --- | --- | --- | --- | --- | --- |
| B01 | EXT-BAY-V1 | BA: 1 | 2026-09-22 | 13:00–14:30 | Penggunaan bay oleh kegiatan lain |
| B02 | EXT-SCAN-V1 | SCAN: 1 | 2026-09-23 | 08:00–10:00 | Peminjaman satu scanner |

Booking hanya memakai resource yang tercantum, tidak otomatis memakai teknisi atau kendaraan pilot. B02 menyisakan satu unit SCAN untuk pekerjaan pilot selama intervalnya. Booking tetap tidak dapat digeser dan tidak termasuk 10 occurrence wajib.

Saat revisi, hanya booking dari versi yang secara eksplisit digantikan yang dikeluarkan dari perhitungan. Booking versi terbit lain tetap berlaku.

## 3. Activity dan pembentukan occurrence

Seluruh activity aktif, dengan jendela yang diizinkan 08:00–12:00 atau 13:00–16:00. Pengulangan mingguan berlaku 21–23 September 2026 tanpa tanggal pengecualian.

| ID | Activity | Durasi | Hari | Kendaraan tetap | Kandidat teknisi | Kandidat bay | Alat tambahan | Occurrence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | Diagnostik Armada 01 | 90 menit | Senin, Rabu | V1 | T1, T2 | BA, BB | SCAN: 1 | O01, O09 |
| A02 | Diagnostik Armada 02 | 90 menit | Senin, Rabu | V2 | T1, T2 | BA, BB | SCAN: 1 | O02, O10 |
| A03 | Ganti Oli Armada 03 | 120 menit | Senin | V3 | T2, T3 | BB | — | O03 |
| A04 | Periksa Rem Armada 04 | 90 menit | Senin | V4 | T3 | BB | — | O04 |
| A05 | Ganti Oli Armada 05 | 120 menit | Selasa | V5 | T2, T3 | BB | — | O05 |
| A06 | Periksa Rem Armada 06 | 90 menit | Selasa | V6 | T3 | BB | — | O06 |
| A07 | Diagnostik Armada 03 | 90 menit | Selasa | V3 | T1, T2 | BA, BB | SCAN: 1 | O07 |
| A08 | Diagnostik Armada 04 | 90 menit | Selasa | V4 | T1, T2 | BA, BB | SCAN: 1 | O08 |

Setiap role memilih tepat satu resource dan memakai satu unit. Oli/rem tidak membutuhkan SCAN. Bay diagnostik memerlukan tag general; oli/rem memerlukan general dan lift. Teknisi harus memiliki tag diagnostic, oil, atau brake sesuai activity.

Daftar kandidat dibekukan dalam snapshot berdasarkan jenis dan tag. Validator tetap memeriksa atribut kandidat. Memasukkan BA ke daftar kandidat penggantian oli tidak menghilangkan kewajiban tag lift.

Occurrence dibentuk sebelum pencarian. Lampiran A memuat daftar hasil ekspansi. Perubahan recurrence atau excluded_dates harus memperbarui occurrence dan input_revision; solver tidak boleh menghapus kewajiban secara diam-diam.

## 4. Constraint wajib

ID H01–H09 berlaku lokal pada schema pilot bengkel ini.

| ID | Aturan dan pemeriksaan | Acuan PRD |
| --- | --- | --- |
| H01 | Setiap occurrence wajib memiliki tepat satu assignment lengkap. Tidak ada occurrence asing, duplikat, atau role wajib yang hilang. | §4.2, FR-11, FR-16 |
| H02 | Total unit pemakaian serentak setiap resource tidak melebihi kapasitas, termasuk booking terbit lain. | §4.2, §4.4 |
| H03 | Seluruh interval berada dalam ketersediaan setiap resource setelah override tanggal. | FR-05, §4.4 |
| H04 | Resource aktif, milik workspace yang sama, sesuai jenis, tag, kandidat atau resource tetap, jumlah pilihan, dan unit kebutuhan. | FR-02, FR-06, §4.4 |
| H05 | Durasi persis sesuai activity, kontinu pada tanggal occurrence, berada dalam satu jendela yang diizinkan, dan selaras slot. | §4.2, §6.1 |
| H06 | Seluruh interval berada dalam jam operasional, di luar hari libur, dan tidak melintasi istirahat. | §4.4 |
| H07 | O01 tetap pada 21 September 08:00–09:30 dengan T1 + V1 + BA + 1 unit SCAN. | FR-15 |
| H08 | Beban harian T1/T2/T3 maksimal 240 menit, termasuk booking terbit lain yang memakai teknisi tersebut. | §4.4 |
| H09 | Booking eksternal tetap berlaku; versi yang digantikan saat revisi tidak dihitung sebagai booking tambahan. | §4.2, FR-16 |

Interval menggunakan [start, end). Pekerjaan yang selesai 09:30 dapat langsung diikuti pekerjaan lain mulai 09:30. Pekerjaan 11:00–13:00 melanggar istirahat. Durasi 120 menit tidak boleh dipecah menjadi 11:00–12:00 dan 13:00–14:00.

Beban harian adalah jumlah durasi × unit pada tanggal lokal untuk resource yang mempunyai batas harian. Pada dataset utama, semua kebutuhan memakai satu unit. Kapasitas serentak dihitung pada setiap interval waktu, bukan sebagai batas jumlah pekerjaan per hari.

### 4.1 Validasi awal dan diagnosis

Sebelum generate, periksa referensi, workspace, status aktif, field wajib, durasi/unit positif, keselarasan slot, kandidat, kecocokan tag, tanggal occurrence, konsistensi recurrence, dan konflik langsung pada kunci.

Kesalahan input ditolak sebagai kesalahan validasi, bukan hasil pencarian Infeasible. Jika ketidakmungkinan baru terbukti melalui pencarian, laporkan sesuai bukti engine. Diagnosis yang belum terbukti harus disebut indikasi.

Contoh: “O05 membutuhkan BB pada 22 September 08:00–10:00, tetapi BB baru tersedia mulai 10:00 karena pemeliharaan. Pelanggaran H03.” Pesan harus menyertakan occurrence, resource, waktu, dan aturan terkait.

## 5. Preference dan objective

Satu pasangan preference–occurrence bernilai 1 jika terpenuhi dan 0 jika tidak. Pagi berarti seluruh interval berada di 08:00–12:00. Target mencakup occurrence terkunci.

| ID | Preference | Target activity | Bobot | Pasangan relevan | Bobot total |
| --- | --- | --- | --- | --- | --- |
| P01 | Diagnostik di pagi hari | A01, A02, A07, A08 | Tinggi = 5 | 6 | 30 |
| P02 | Diagnostik menggunakan T1 | A01, A02, A07, A08 | Sedang = 3 | 6 | 18 |
| P03 | Penggantian oli menggunakan T2 | A03, A05 | Rendah = 1 | 2 | 2 |
| P04 | Pemeriksaan rem di pagi hari | A04, A06 | Rendah = 1 | 2 | 2 |
| **Total** | | | | **16** | **52** |

Objective: maksimalkan jumlah bobot terpenuhi setelah seluruh occurrence terjadwal dan semua constraint terpenuhi.

Skor tampilan = bobot terpenuhi / bobot relevan × 100. Bobot tinggi tidak memberi prioritas mutlak terhadap gabungan preference lain. Preference tidak dapat mengabaikan ketersediaan atau kapasitas.

Pasangan relevan yang mustahil terpenuhi tetap masuk penyebut. Preference nonaktif atau tanpa occurrence target dalam periode tidak masuk penyebut. Jika penyebut nol, skor null dan tampilkan “Tidak ada preference”. Bandingkan skor hanya pada snapshot, aturan, dan bobot yang sama.

Pemerataan beban teknisi, pengurangan waktu kosong, dan minimisasi perubahan tidak menjadi objective pilot karena termasuk cakupan P2.

## 6. Contoh jadwal lengkap yang valid

Jadwal disusun sebagai acuan data, bukan hasil solver atau klaim Optimal. Solver boleh memilih penempatan lain selama semua aturan dan kunci dipenuhi.

| Occurrence | Tanggal | Waktu WITA | Activity | Teknisi | Kendaraan | Bay | SCAN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| O01 | 2026-09-21 | 08:00–09:30 | A01 | T1 | V1 | BA | 1 unit |
| O02 | 2026-09-21 | 08:00–09:30 | A02 | T2 | V2 | BB | 1 unit |
| O03 | 2026-09-21 | 10:00–12:00 | A03 | T2 | V3 | BB | — |
| O04 | 2026-09-21 | 13:00–14:30 | A04 | T3 | V4 | BB | — |
| O05 | 2026-09-22 | 10:00–12:00 | A05 | T2 | V5 | BB | — |
| O06 | 2026-09-22 | 13:00–14:30 | A06 | T3 | V6 | BB | — |
| O07 | 2026-09-22 | 08:00–09:30 | A07 | T1 | V3 | BA | 1 unit |
| O08 | 2026-09-22 | 14:30–16:00 | A08 | T2 | V4 | BA | 1 unit |
| O09 | 2026-09-23 | 08:00–09:30 | A01 | T1 | V1 | BA | 1 unit |
| O10 | 2026-09-23 | 10:00–11:30 | A02 | T2 | V2 | BB | 1 unit |

O01 dan O02 berjalan bersama dengan total dua unit SCAN; teknisi, kendaraan, dan bay berbeda. O05 dimulai setelah pemeliharaan BB. O08 dimulai tepat ketika booking BA selesai dan memakai T2 karena T1 tidak tersedia sore. Pada Rabu pagi, O09 bersama B02 menggunakan dua unit SCAN. O10 dimulai ketika peminjaman scanner sudah selesai.

### 6.1 Beban harian teknisi

| Resource | Senin | Selasa | Rabu | Batas per hari |
| --- | --- | --- | --- | --- |
| T1 | 90 | 90 | 90 | 240 |
| T2 | 210 | 210 | 90 | 240 |
| T3 | 90 | 90 | 0 | 240 |

Semua angka dalam menit. Total pekerjaan: 6 × 90 menit diagnostik + 2 × 120 menit penggantian oli + 2 × 90 menit pemeriksaan rem = **960 menit**. Beban bay, kendaraan, dan scanner tidak ditambahkan lagi sebagai durasi pekerjaan.

### 6.2 Skor jadwal acuan

| Preference | Terpenuhi | Tidak terpenuhi | Bobot diperoleh / relevan |
| --- | --- | --- | --- |
| P01 | O01, O02, O07, O09, O10 | O08 | 25 / 30 |
| P02 | O01, O07, O09 | O02, O08, O10 | 9 / 18 |
| P03 | O03, O05 | — | 2 / 2 |
| P04 | — | O04, O06 | 0 / 2 |
| **Total** | | | **36 / 52 = 69,23%** |

Perbaikan pembanding: ganti teknisi O10 dari T2 menjadi T1, tanpa mengubah waktu. T1 memakai 180 menit pada Rabu, tanpa benturan dengan O09. Jadwal tetap valid dan bobot menjadi **39/52 = 75,00%**. Ini acuan evaluator preference, bukan target optimum.

## 7. Varian kasus uji untuk tahap berikutnya

Setiap kasus dimulai dari dataset utama, lalu hanya menerapkan perubahan yang dinyatakan. Edit assignment menguji validator; ubah input menguji validasi awal dan pencarian. Semua ekspektasi berikut merupakan spesifikasi, bukan laporan eksekusi solver.

| ID | Perubahan / tindakan | Ekspektasi |
| --- | --- | --- |
| C01 | Generate dataset utama. | Ditemukan 10 assignment lengkap dan valid; Optimal atau Feasible mengikuti bukti runtime. |
| C02 | Evaluasi O01/O02 pada jadwal acuan. | Valid: dua unit SCAN dipakai bersama. Implementasi yang melarang seluruh overlap SCAN salah. |
| C03 | Edit bay O02 menjadi BA. | Tolak: BA bentrok O01 (H02). |
| C04 | Edit teknisi O02 menjadi T1. | Tolak: T1 bentrok O01 (H02), meskipun tag sesuai. |
| C05 | Edit bay O03 menjadi BA. | Tolak: BA tidak memiliki lift dan bukan kandidat (H04). |
| C06 | Edit teknisi O04 menjadi T1. | Tolak: tidak memiliki tag brake dan bukan kandidat (H04), walaupun kosong sore itu. |
| C07 | Edit O05 menjadi 08:00–10:00, resource tetap. | Tolak: BB dalam pemeliharaan (H03). |
| C08 | Edit teknisi O08 menjadi T1. | Tolak: override T1 melarang sore (H03). |
| C09 | Edit O05 menjadi 11:00–13:00. | Tolak: melintasi istirahat (H05/H06). |
| C10 | Edit O07 menjadi 08:00–09:00; pada percobaan terpisah, 08:15–09:45. | Tolak masing-masing karena durasi salah atau tidak selaras slot (H05). |
| C11 | Edit O08 menjadi 13:00–14:30, resource tetap. | Tolak: BA dipakai B01 (H02/H09). |
| C12 | Edit O10 menjadi 08:00–09:30, resource tetap. | Tolak: O09 + O10 + B02 memakai 3 unit SCAN, melebihi 2; teknisi, bay, dan kendaraan O09/O10 tetap berbeda (H02). |
| C13 | Ubah input: kunci juga O02 pada 08:00–09:30 dengan T2 + V2 + BA + SCAN. | Validasi awal menolak konflik dua kunci di BA; bukan status pencarian Infeasible. |
| C14 | Evaluasi acuan, lalu ubah teknisi O10 menjadi T1. | Dua jadwal valid; bobot 36 → 39, penyebut tetap 52. |
| C15 | Hapus assignment O10. | Kelengkapan 9/10; O10 belum terjadwal; tolak publikasi dan jangan beri status Feasible/Optimal pada hasil parsial. |
| C16 | Hapus seluruh preference. | Jadwal lengkap tetap diperlukan; skor null, “Tidak ada preference”. |
| C17 | Ubah input: T3.max_daily_minutes menjadi 60. | O04/O06 masing-masing memerlukan 90 menit dan hanya T3 yang kompeten. Pemeriksa awal boleh menolak dengan bukti; jika masuk pencarian, diperlukan bukti Infeasible. |
| C18 | Ubah input: tambah 23 September ke excluded_dates A01 lalu bentuk ulang occurrence. | O09 hilang; 9 occurrence; bobot relevan 44. Kunci O01 tetap berlaku. |
| C19 | Ubah input: tetapkan 23 September sebagai hari libur, O09/O10 tetap wajib. | Tidak ada penempatan pada tanggal tersebut. Hari libur tidak otomatis menghapus occurrence. |
| C20 | Simulasikan versi terbit WORKSHOP-V1 berisi acuan; draft menyatakan menggantikannya. Pertahankan B01/B02. | WORKSHOP-V1 tidak dihitung ganda; booking dua versi eksternal tetap berlaku. |
| C21 | Setelah job dibuat, ubah sumber menjadi T1 tidak tersedia seharian Senin. | Hasil lama tetap terikat snapshot lama; tolak publikasi sebagai kedaluwarsa. Validasi terbaru mendeteksi konflik kunci O01 tanpa menggesernya. |
| C22 | Hapus role equipment_pool dari assignment O07. | Tolak: kebutuhan SCAN belum dipenuhi (H01/H04). Tidak dianggap sekadar preference yang gagal. |

### 7.1 Fixture kapasitas 2 versus kapasitas 1

Isolasi A01/A02 dan O01/O02 pada 21 September, tanpa kunci, booking, atau preference. Ubah recurrence keduanya menjadi hanya Senin pada horizon satu hari. Batasi allowed_windows keduanya ke 08:00–09:30, pertahankan durasi 90 menit dan seluruh kandidat.

- Dengan SCAN berkapasitas 2, keduanya dapat dijadwalkan bersamaan menggunakan T1/BA dan T2/BB.
- Ubah hanya kapasitas SCAN menjadi 1: kedua occurrence tidak mungkin dijadwalkan bersama. Masing-masing feasible sendiri, tetapi total permintaan dua unit melebihi satu pada satu-satunya interval.

Ketidakmungkinan perlu dibuktikan pemeriksa awal atau pencarian, bukan disimpulkan dari timeout. Fixture ini juga menguji bahwa kapasitas 2 berlaku pada waktu yang sama, bukan batas dua pekerjaan per hari.

### 7.2 Fixture benturan kendaraan

Isolasi O01/A01 dan O02/A02 pada 21 September, tanpa kunci, booking, atau preference. Tetapkan kendaraan A02 menjadi V1, lalu gunakan dua assignment 08:00–09:30: T1 + V1 + BA + SCAN dan T2 + V1 + BB + SCAN.

Validator harus menolak karena V1 dipakai dua pekerjaan bersamaan (H02), meskipun teknisi dan bay berbeda serta SCAN cukup. Jika jendela input tetap 08:00–12:00 dan 13:00–16:00, engine dapat menjadwalkan keduanya berurutan; benturan pada assignment contoh tidak berarti seluruh input Infeasible.

### 7.3 Fixture preference yang tidak mungkin terpenuhi

Isolasi O08/A08 pada 22 September. Hilangkan booking dan kunci; batasi jendela activity ke 13:00–16:00, dengan recurrence hanya Selasa. Pertahankan override T1 hanya tersedia pagi. Gunakan P01/P02 dengan target hanya A08.

Occurrence tetap dapat ditempatkan memakai T2 dan BA atau BB. P01 dan P02 sama-sama gagal; skor maksimum 0/8 = 0%. Ini tetap jadwal valid dan, jika dibuktikan engine, dapat berstatus Optimal walaupun skornya bukan 100%.

Setiap fixture mempunyai dataset_id berbeda dan revisi input baru. Recurrence, occurrence, target preference, kunci, serta resource harus konsisten dengan cakupan fixture.

## 8. Kontrak hasil dan kriteria penerimaan

| Status hasil PRD | Bukti yang dibutuhkan |
| --- | --- |
| Optimal | Jadwal lengkap valid dan engine membuktikan optimum objective pada snapshot tersebut. |
| Feasible | Jadwal lengkap valid ditemukan; optimalitas belum terbukti. |
| Infeasible | Engine membuktikan tidak ada jadwal lengkap yang memenuhi seluruh constraint. |
| Belum ditemukan | Batas waktu tercapai tanpa solusi lengkap dan tanpa bukti infeasible. |
| Gagal / dibatalkan | Kesalahan teknis atau pembatalan; bukan bukti infeasible. |

Status job, status solusi, dan status versi jadwal terpisah. Job selesai dapat menghasilkan Infeasible atau Belum ditemukan. Versi mengikuti Draft → Published → Archived. Kesalahan input atau model harus dilaporkan sebagai kesalahan, bukan ketidakmungkinan bisnis.

Dataset kecil tidak menjamin munculnya status Feasible atau Belum ditemukan. Uji kontrak status dengan hasil terkontrol dan uji integrasi dengan mencatat status yang benar-benar dikembalikan. Timeout sangat kecil tidak menjamin status tertentu. Kegagalan worker dan pembatalan memerlukan kontrol proses pada tahap implementasi.

Kriteria penerimaan tahap solver:

1. Dataset utama menghasilkan 10 occurrence terjadwal tepat sekali, seluruh kebutuhan lengkap, dan nol pelanggaran validator terpisah.
2. Kunci O01 dipertahankan, override dipatuhi, serta B01/B02 diperhitungkan.
3. Kapasitas pool SCAN mendukung dua unit bersamaan dan menolak kelebihan unit termasuk booking eksternal.
4. Evaluator menghasilkan 36/52 untuk acuan dan 39/52 untuk pembanding.
5. Varian valid, pelanggaran assignment, kesalahan input, dan kasus mustahil dibedakan sesuai bukti.
6. Tidak ada asumsi bahwa seluruh activity memiliki jumlah atau nama role yang sama.
7. Hasil parsial dan kedaluwarsa tidak dapat dipublikasikan.

Catatan hasil minimum: schema/dataset/input revision, identitas job, status job dan solusi, assignment, jumlah wajib/terjadwal, occurrence yang belum terjadwal, pelanggaran validator, rincian preference, bobot terpenuhi/relevan, skor atau null, waktu antre dan solver terpisah, alasan berhenti, diagnosis dan tingkat kepastiannya, serta versi runtime dan konfigurasi komputasi.

Gate publikasi: lengkap, semua constraint lulus validator terpisah, input mutakhir, dan tidak bertabrakan dengan jadwal terbit terbaru. Validasi serta penggantian versi harus atomik pada implementasi produk; dokumen tahap 1 ini hanya menetapkan acuannya.

## Lampiran A — Snapshot input contoh

Kontrak contoh `pilot-workshop-1.0.0`, bukan schema API/database final. Seluruh entitas dalam snapshot milik WS-WORKSHOP melalui konteks snapshot; booking juga menyimpan workspace_id secara eksplisit. ID aturan ditafsirkan menggunakan dokumen bengkel ini.

Tanggal ISO dan jam HH:MM bersifat lokal pada Asia/Makassar. ISO weekday 1=Senin hingga 7=Minggu. Batas akhir periode/recurrence inklusif; batas akhir interval eksklusif. availability_profile_id mereferensikan pola mingguan; override menggantikan pola pada tanggal itu. max_daily_minutes yang tidak ada berarti tidak ada batas harian tambahan.

candidate_ids berisi alternatif, bukan semua resource yang harus dipakai. Setiap requirement memilih select_count resource, masing-masing memakai units_per_selected_resource. Dalam fixture ini select_count selalu 1. Assignment memetakan role ke satu ID; jumlah unit diambil dari requirement, sehingga `equipment_pool: "SCAN"` berarti satu unit, bukan seluruh pool.

Kunci membekukan waktu dan semua resource; kebutuhan unit tetap mengikuti snapshot. units tidak boleh diubah melalui edit assignment. Snapshot pelatihan yang lama tetap terpisah dan tidak ditimpa.

```json
{
  "schema_version": "pilot-workshop-1.0.0",
  "dataset_id": "WORKSHOP-BASE-01",
  "input_revision": 1,
  "workspace": {"id": "WS-WORKSHOP","name": "Bengkel Armada Contoh","timezone": "Asia/Makassar"},
  "period": {"start_date": "2026-09-21","end_date": "2026-09-23","slot_minutes": 30},
  "calendar": {"iso_weekdays": [1,2,3,4,5],"open_windows": [["08:00","12:00"],["13:00","16:00"]],"holidays": []},
  "availability_profiles": [
    {"id": "WORKDAYS","iso_weekdays": [1,2,3,4,5],"windows": [["08:00","12:00"],["13:00","16:00"]]}
  ],
  "resources": [
    {"id": "T1","name": "Teknisi Adi","type": "technician","tags": ["diagnostic"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS","max_daily_minutes": 240},
    {"id": "T2","name": "Teknisi Bima","type": "technician","tags": ["diagnostic","oil"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS","max_daily_minutes": 240},
    {"id": "T3","name": "Teknisi Candra","type": "technician","tags": ["oil","brake"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS","max_daily_minutes": 240},
    {"id": "BA","name": "Bay Umum","type": "service_bay","tags": ["general"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "BB","name": "Bay Lift","type": "service_bay","tags": ["general","lift"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "SCAN","name": "Pool Scanner","type": "equipment_pool","tags": ["obd"],"concurrent_capacity": 2,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V1","name": "Mobil Armada 01","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V2","name": "Mobil Armada 02","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V3","name": "Mobil Armada 03","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V4","name": "Mobil Armada 04","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V5","name": "Mobil Armada 05","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},
    {"id": "V6","name": "Mobil Armada 06","type": "vehicle","tags": ["passenger_car"],"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"}
  ],
  "availability_overrides": [
    {"resource_id": "T1","date": "2026-09-22","available_windows": [["08:00","12:00"]],"reason": "Tidak tersedia sore"},
    {"resource_id": "BB","date": "2026-09-22","available_windows": [["10:00","12:00"],["13:00","16:00"]],"reason": "Pemeliharaan lift 08:00–10:00"}
  ],
  "activities": [
    {"id": "A01","name": "Diagnostik Armada 01","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["diagnostic"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V1","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general"],"candidate_ids": ["BA","BB"],"select_count": 1,"units_per_selected_resource": 1},{"role": "equipment_pool","type": "equipment_pool","required_tags": ["obd"],"candidate_ids": ["SCAN"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A02","name": "Diagnostik Armada 02","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["diagnostic"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V2","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general"],"candidate_ids": ["BA","BB"],"select_count": 1,"units_per_selected_resource": 1},{"role": "equipment_pool","type": "equipment_pool","required_tags": ["obd"],"candidate_ids": ["SCAN"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A03","name": "Ganti Oli Armada 03","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["oil"],"candidate_ids": ["T2","T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V3","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general","lift"],"candidate_ids": ["BB"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A04","name": "Periksa Rem Armada 04","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["brake"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V4","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general","lift"],"candidate_ids": ["BB"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A05","name": "Ganti Oli Armada 05","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["oil"],"candidate_ids": ["T2","T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V5","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general","lift"],"candidate_ids": ["BB"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A06","name": "Periksa Rem Armada 06","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["brake"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V6","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general","lift"],"candidate_ids": ["BB"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A07","name": "Diagnostik Armada 03","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["diagnostic"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V3","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general"],"candidate_ids": ["BA","BB"],"select_count": 1,"units_per_selected_resource": 1},{"role": "equipment_pool","type": "equipment_pool","required_tags": ["obd"],"candidate_ids": ["SCAN"],"select_count": 1,"units_per_selected_resource": 1}]},
    {"id": "A08","name": "Diagnostik Armada 04","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2],"start_date": "2026-09-21","until_date": "2026-09-23","excluded_dates": []},"requirements": [{"role": "technician","type": "technician","required_tags": ["diagnostic"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "vehicle","type": "vehicle","fixed_resource_id": "V4","select_count": 1,"units_per_selected_resource": 1},{"role": "service_bay","type": "service_bay","required_tags": ["general"],"candidate_ids": ["BA","BB"],"select_count": 1,"units_per_selected_resource": 1},{"role": "equipment_pool","type": "equipment_pool","required_tags": ["obd"],"candidate_ids": ["SCAN"],"select_count": 1,"units_per_selected_resource": 1}]}
  ],
  "occurrences": [
    {"id": "O01","activity_id": "A01","date": "2026-09-21","required": true},
    {"id": "O02","activity_id": "A02","date": "2026-09-21","required": true},
    {"id": "O03","activity_id": "A03","date": "2026-09-21","required": true},
    {"id": "O04","activity_id": "A04","date": "2026-09-21","required": true},
    {"id": "O05","activity_id": "A05","date": "2026-09-22","required": true},
    {"id": "O06","activity_id": "A06","date": "2026-09-22","required": true},
    {"id": "O07","activity_id": "A07","date": "2026-09-22","required": true},
    {"id": "O08","activity_id": "A08","date": "2026-09-22","required": true},
    {"id": "O09","activity_id": "A01","date": "2026-09-23","required": true},
    {"id": "O10","activity_id": "A02","date": "2026-09-23","required": true}
  ],
  "enabled_hard_rules": ["H01","H02","H03","H04","H05","H06","H07","H08","H09"],
  "locks": [
    {"occurrence_id": "O01","date": "2026-09-21","start": "08:00","end": "09:30","resources": {"technician": "T1","vehicle": "V1","service_bay": "BA","equipment_pool": "SCAN"}}
  ],
  "published_bookings": [
    {"id": "B01","workspace_id": "WS-WORKSHOP","schedule_version_id": "EXT-BAY-V1","date": "2026-09-22","start": "13:00","end": "14:30","resource_units": {"BA": 1},"label": "Penggunaan bay oleh kegiatan lain"},
    {"id": "B02","workspace_id": "WS-WORKSHOP","schedule_version_id": "EXT-SCAN-V1","date": "2026-09-23","start": "08:00","end": "10:00","resource_units": {"SCAN": 1},"label": "Peminjaman satu scanner"}
  ],
  "replaces_schedule_version_id": null,
  "preferences": [
    {"id": "P01","type": "preferred_time","activity_ids": ["A01","A02","A07","A08"],"weight": 5,"window": ["08:00","12:00"],"match": "full_interval","active": true},
    {"id": "P02","type": "preferred_resource","activity_ids": ["A01","A02","A07","A08"],"weight": 3,"role": "technician","resource_ids": ["T1"],"active": true},
    {"id": "P03","type": "preferred_resource","activity_ids": ["A03","A05"],"weight": 1,"role": "technician","resource_ids": ["T2"],"active": true},
    {"id": "P04","type": "preferred_time","activity_ids": ["A04","A06"],"weight": 1,"window": ["08:00","12:00"],"match": "full_interval","active": true}
  ],
  "solver_budget_seconds": 60
}
```

## Lampiran B — Assignment acuan

Setiap role memakai satu unit sesuai requirement Lampiran A. Role equipment_pool hanya ada pada pekerjaan diagnostik. Assignment ini disusun sebagai contoh valid dan tidak menyimpan status hasil solver.

```json
[
  {"occurrence_id": "O01","date": "2026-09-21","start": "08:00","end": "09:30","resources": {"technician": "T1","vehicle": "V1","service_bay": "BA","equipment_pool": "SCAN"}},
  {"occurrence_id": "O02","date": "2026-09-21","start": "08:00","end": "09:30","resources": {"technician": "T2","vehicle": "V2","service_bay": "BB","equipment_pool": "SCAN"}},
  {"occurrence_id": "O03","date": "2026-09-21","start": "10:00","end": "12:00","resources": {"technician": "T2","vehicle": "V3","service_bay": "BB"}},
  {"occurrence_id": "O04","date": "2026-09-21","start": "13:00","end": "14:30","resources": {"technician": "T3","vehicle": "V4","service_bay": "BB"}},
  {"occurrence_id": "O05","date": "2026-09-22","start": "10:00","end": "12:00","resources": {"technician": "T2","vehicle": "V5","service_bay": "BB"}},
  {"occurrence_id": "O06","date": "2026-09-22","start": "13:00","end": "14:30","resources": {"technician": "T3","vehicle": "V6","service_bay": "BB"}},
  {"occurrence_id": "O07","date": "2026-09-22","start": "08:00","end": "09:30","resources": {"technician": "T1","vehicle": "V3","service_bay": "BA","equipment_pool": "SCAN"}},
  {"occurrence_id": "O08","date": "2026-09-22","start": "14:30","end": "16:00","resources": {"technician": "T2","vehicle": "V4","service_bay": "BA","equipment_pool": "SCAN"}},
  {"occurrence_id": "O09","date": "2026-09-23","start": "08:00","end": "09:30","resources": {"technician": "T1","vehicle": "V1","service_bay": "BA","equipment_pool": "SCAN"}},
  {"occurrence_id": "O10","date": "2026-09-23","start": "10:00","end": "11:30","resources": {"technician": "T2","vehicle": "V2","service_bay": "BB","equipment_pool": "SCAN"}}
]
```
