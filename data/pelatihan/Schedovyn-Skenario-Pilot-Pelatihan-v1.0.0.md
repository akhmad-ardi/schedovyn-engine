# Schedovyn — Skenario Pilot Scheduling Engine

Versi: 1.0.0 • Tahap: 1 — data dan aturan • Acuan: Schedovyn-PRD-v1.0.0.md

Dokumen pendamping PRD untuk menyiapkan prototipe Python + OR-Tools CP-SAT. Isinya menetapkan satu skenario pelatihan, dataset sintetis, aturan yang dapat diuji, jadwal acuan, dan kriteria pembuktian untuk tahap 2. Tidak ada implementasi atau hasil eksekusi solver dalam dokumen ini. PRD sumber tetap menjadi acuan kebutuhan produk.

## 1. Tujuan dan batas pilot

Operator harus menjadwalkan dua kelompok pelatihan yang berbagi pengajar dan ruangan. Setiap sesi membutuhkan tepat satu pengajar yang kompeten, satu kelompok peserta, serta satu ruangan yang sesuai dan cukup besar, secara bersamaan sepanjang sesi.

| Parameter | Keputusan pilot |
| --- | --- |
| Organisasi | Balai Pelatihan Contoh; semua nama dan data bersifat sintetis |
| Horizon | Senin, 21 September–Jumat, 25 September 2026, inklusif |
| Zona waktu | Asia/Makassar; semua jam dalam WITA (UTC+08:00) |
| Jam operasional | Senin–Jumat 08:00–12:00 dan 13:00–16:00 |
| Istirahat | 12:00–13:00; sesi tidak boleh melintasi istirahat |
| Resolusi | 30 menit; durasi, awal, akhir, dan semua batas jendela selaras slot |
| Skala | 8 resource, 8 activity, 14 occurrence wajib; total 1.380 menit sesi |
| Keputusan engine | Jam mulai, pengajar dari kandidat, dan ruangan dari kandidat |
| Sudah ditetapkan input | Tanggal occurrence, durasi, kelompok, kebutuhan resource, dan semua kunci |
| Batas pencarian tahap 2 | 60 detik waktu solver, sesuai default PRD; bukan jaminan waktu selesai |

Satu kelompok merupakan satu resource dengan kapasitas serentak 1, meskipun beranggotakan banyak peserta. Kedua kelompok diasumsikan tidak memiliki peserta yang sama. Tidak ada jeda perpindahan, urutan wajib antarmateri, pembagian sesi, pemisahan kelompok, atau kewajiban memakai pengajar yang sama pada semua pertemuan. Pemerataan beban, minimisasi jeda kosong, dan minimisasi perubahan otomatis mengikuti P2, sehingga tidak dimasukkan sebagai objective pilot.

Tanggal tidak menjadi variabel optimasi: pola mingguan membentuk occurrence pada hari yang dipilih. Contohnya, A01 membentuk O01 pada Senin dan O07 pada Rabu; O07 tidak boleh dipindahkan ke Kamis untuk memperbaiki skor. Ini mengikuti PRD §4.2. Preference hari tidak memberi kebebasan mengganti tanggal tersebut.

Keputusan kalender, kapasitas, durasi, dan batas beban dalam dokumen ini adalah asumsi contoh, bukan kebijakan resmi BPVP Bantaeng atau ketentuan kurikulum.

## 2. Data resource

| ID | Nama / jenis | Kompetensi atau fasilitas | Peserta / kursi | Kapasitas serentak | Batas beban harian |
| --- | --- | --- | --- | --- | --- |
| T1 | Pengajar Arman | web | — | 1 | 240 menit |
| T2 | Pengajar Bella | web, network | — | 1 | 240 menit |
| T3 | Pengajar Citra | network, career | — | 1 | 240 menit |
| GA | Kelompok A | participant_group | 20 peserta | 1 | 240 menit |
| GB | Kelompok B | participant_group | 28 peserta | 1 | 240 menit |
| RA | Kelas A | classroom, projector | 24 kursi | 1 | Tidak dikonfigurasi |
| RB | Kelas B | classroom, projector | 32 kursi | 1 | Tidak dikonfigurasi |
| LAB | Laboratorium Komputer | computer, projector | 30 kursi | 1 | Tidak dikonfigurasi |

Kursi dan kapasitas serentak adalah atribut berbeda. LAB berkapasitas 30 kursi tetap hanya boleh dipakai satu sesi pada satu waktu. RA tidak boleh dipakai GB karena 24 < 28, walaupun ruangannya sedang kosong. LAB tidak memiliki tag `classroom`, sehingga tidak menjadi kandidat sesi career dalam contoh ini.

### 2.1 Ketersediaan dan pengecualian

Semua resource mengikuti jam operasional, kecuali dua override berikut. Daftar waktu override **menggantikan seluruh pola ketersediaan pada tanggal tersebut**, bukan ditambahkan ke pola mingguan.

| Resource | Tanggal | Seluruh jendela tersedia pengganti | Alasan |
| --- | --- | --- | --- |
| T1 | 23 September | 13:00–16:00 | Berhalangan pada pagi hari |
| LAB | 22 September | 10:00–12:00 dan 13:00–16:00 | Pemeliharaan 08:00–10:00 |

Daftar override kosong berarti resource tidak tersedia seharian. Kalender organisasi tetap membatasi override: override tidak dapat membuka hari libur atau jam tutup organisasi.

### 2.2 Pemakaian dari jadwal terbit lain

| Booking | Versi jadwal | Resource | Tanggal | Waktu | Unit |
| --- | --- | --- | --- | --- | --- |
| B01 — Rapat internal | EXT-ROOM-V1 | RB | 21 September | 08:00–10:00 | 1 |
| B02 — Uji kompetensi eksternal | EXT-LAB-V1 | LAB | 24 September | 13:00–15:00 | 1 |

Keduanya berada dalam workspace yang sama dan tidak dapat digeser engine. Booking hanya memakai resource yang tercantum; tidak otomatis memakai pengajar atau kelompok pilot. Keduanya bukan bagian dari 14 occurrence yang harus dijadwalkan. Saat revisi, hanya booking dari versi yang secara eksplisit digantikan yang dikeluarkan dari perhitungan; booking versi lain tetap berlaku.

## 3. Activity dan pembentukan occurrence

Semua activity aktif, berlangsung kontinu pada satu tanggal, dan mempunyai jendela yang diizinkan 08:00–12:00 atau 13:00–16:00. Setiap kebutuhan menggunakan 1 unit dari tepat 1 resource. Pengulangan mingguan berlaku mulai 21 sampai 25 September, tanpa tanggal pengecualian pada dataset utama.

| ID | Activity | Durasi | Hari | Kelompok | Kandidat pengajar | Kandidat ruangan | Occurrence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A01 | Praktik Web A | 120 menit | Senin, Rabu | GA | T1, T2 | LAB | O01, O07 |
| A02 | Praktik Web B | 120 menit | Senin, Rabu | GB | T1, T2 | LAB | O02, O08 |
| A03 | Komunikasi Kerja A | 60 menit | Senin, Rabu | GA | T3 | RA, RB | O03, O09 |
| A04 | Komunikasi Kerja B | 60 menit | Senin, Rabu | GB | T3 | RB | O04, O10 |
| A05 | Praktik Jaringan A | 120 menit | Selasa, Kamis | GA | T2, T3 | LAB | O05, O11 |
| A06 | Praktik Jaringan B | 120 menit | Selasa, Kamis | GB | T2, T3 | LAB | O06, O12 |
| A07 | Persiapan Karier A | 90 menit | Jumat | GA | T3 | RA, RB | O13 |
| A08 | Persiapan Karier B | 90 menit | Jumat | GB | T3 | RB | O14 |

Daftar kandidat merupakan hasil kecocokan jenis, seluruh tag kebutuhan, dan kursi minimum. Snapshot membekukan daftar tersebut, tetapi validator tetap memeriksa atribut agar kandidat yang salah tidak diam-diam diterima. Guru harus memiliki tag `web`, `network`, atau `career` sesuai materi. Ruangan praktik memerlukan `computer` dan `projector`; ruangan career memerlukan `classroom` dan `projector`.

Occurrence tidak dibentuk ulang oleh solver. Lampiran menyediakan daftar hasil ekspansi yang diharapkan untuk dibandingkan dengan pembentuk occurrence kelak. Mengubah recurrence atau menghapus tanggal melalui pengecualian harus memperbarui daftar occurrence dan revisi input sebelum generate.

## 4. Constraint wajib

Semua aturan berikut aktif. Kegagalan memenuhi satu aturan membuat assignment atau jadwal tidak valid; bobot preference tidak dapat membenarkannya.

| ID | Aturan dan pemeriksaan | Acuan PRD |
| --- | --- | --- |
| H01 | Setiap occurrence wajib mempunyai tepat satu assignment lengkap: waktu, pengajar, kelompok, ruangan. Tidak ada occurrence asing atau duplikat. | §4.2, FR-11, FR-16 |
| H02 | Total unit pemakaian serentak setiap resource tidak melebihi kapasitas, termasuk booking terbit lain. Pengajar, kelompok, dan ruangan diperiksa terpisah. | §4.2, §4.4 |
| H03 | Seluruh interval berada dalam ketersediaan setiap resource setelah override tanggal. | FR-05, §4.4 |
| H04 | Resource aktif dan berasal dari workspace yang sama; tepat jenis, semua tag, kursi minimum, kandidat, dan unit kebutuhannya. | FR-02, FR-06, §4.4 |
| H05 | Durasi persis sesuai activity, kontinu, berada pada tanggal occurrence dan dalam satu jendela yang diizinkan; batas selaras slot. | §4.2, §4.4, §6.1 |
| H06 | Seluruh interval berada dalam jam operasional, di luar hari libur, dan tidak melintasi istirahat. | §4.4 |
| H07 | O01 harus tetap 21 September, 08:00–10:00, T1 + GA + LAB. Kunci mencakup waktu dan seluruh resource. | FR-15 |
| H08 | Total menit pemakaian per hari untuk T1/T2/T3/GA/GB maksimal 240, termasuk pemakaian dari jadwal terbit lain yang diperhitungkan. | §4.4 |
| H09 | Booking eksternal tetap berlaku; ketika revisi, versi yang digantikan tidak dihitung ganda. | §4.2, FR-16 |

Interval adalah `[start, end)`: 08:00–10:00 dan 10:00–12:00 tidak bentrok. Sesi 11:00–13:00 melanggar jam istirahat meskipun awal/akhir berada pada jam kalender hari itu. Sesi 120 menit tidak boleh dipecah menjadi 11:00–12:00 dan 13:00–14:00.

Beban harian dihitung sebagai jumlah `durasi × unit` pada tanggal lokal untuk semua assignment yang memakai resource itu. Pada pilot setiap unit bernilai 1. Tidak ada batas beban ruangan selain ketersediaan dan kapasitas serentaknya.

### 4.1 Validasi awal dan diagnosis

Sebelum generate, periksa identitas/referensi, field wajib, durasi/unit positif, kelipatan slot, jendela, daftar kandidat, kecocokan atribut, tanggal occurrence, serta konflik langsung pada kunci. Input yang salah ditolak sebagai kesalahan validasi, bukan otomatis diberi hasil pencarian Infeasible. Konflik yang baru terbukti melalui pencarian dilaporkan sesuai bukti engine.

Contoh pesan: “O01 terkunci pada 21 September 08:00–10:00 menggunakan LAB, tetapi LAB tidak tersedia pada interval tersebut. Perbaiki ketersediaan atau buka kunci O01.” Sertakan ID occurrence, resource, waktu, dan ID aturan agar operator dapat menemukan data sumber. Diagnosis yang belum terbukti harus ditandai sebagai indikasi.

## 5. Preference dan objective

Satu pasangan preference–occurrence hanya bernilai 1 (terpenuhi) atau 0 (tidak). Preferensi pagi berarti **seluruh interval** berada di 08:00–12:00. Target diterapkan pada semua occurrence wajib dari activity yang disebutkan, termasuk occurrence terkunci.

| ID | Preference | Target activity | Bobot | Pasangan relevan | Bobot total |
| --- | --- | --- | --- | --- | --- |
| P01 | Praktik web di pagi hari | A01, A02 | Tinggi = 5 | 4 | 20 |
| P02 | Praktik web menggunakan T1 | A01, A02 | Sedang = 3 | 4 | 12 |
| P03 | Praktik jaringan menggunakan T2 | A05, A06 | Sedang = 3 | 4 | 12 |
| P04 | Career kelompok A menggunakan RA | A03, A07 | Rendah = 1 | 3 | 3 |
| P05 | Sesi career di pagi hari | A03, A04, A07, A08 | Rendah = 1 | 6 | 6 |
| **Total** | | | | **21** | **53** |

Objective: maksimalkan jumlah bobot pasangan yang terpenuhi, setelah jadwal lengkap dan semua constraint terpenuhi. Skor tampilan = bobot terpenuhi / bobot relevan × 100. Bobot 5 bukan prioritas mutlak terhadap semua preference berbobot 3: kontribusi dijumlahkan sesuai PRD §4.4.

Pasangan yang relevan tetapi mustahil terpenuhi tetap masuk penyebut; jangan menyembunyikan preferensi yang gagal. Preferensi tidak aktif atau target di luar occurrence aktif periode ini tidak masuk penyebut. Jika penyebut nol, tampilkan “Tidak ada preference” dengan skor null. Dua hasil hanya dibandingkan skornya pada snapshot, aturan, dan bobot yang sama.

## 6. Contoh jadwal lengkap yang valid

Jadwal berikut disusun sebagai acuan pemeriksaan data. Jadwal ini menunjukkan bahwa dataset utama mempunyai setidaknya satu penempatan lengkap yang memenuhi aturan. Ini bukan hasil solver dan tidak menyatakan status Optimal. Solver boleh menghasilkan jam atau resource berbeda selama valid dan mempertahankan O01.

| Occurrence | Tanggal | Waktu WITA | Activity | Pengajar | Kelompok | Ruangan |
| --- | --- | --- | --- | --- | --- | --- |
| O01 | 2026-09-21 | 08:00–10:00 | A01 | T1 | GA | LAB |
| O02 | 2026-09-21 | 10:00–12:00 | A02 | T2 | GB | LAB |
| O03 | 2026-09-21 | 10:00–11:00 | A03 | T3 | GA | RA |
| O04 | 2026-09-21 | 13:00–14:00 | A04 | T3 | GB | RB |
| O05 | 2026-09-22 | 10:00–12:00 | A05 | T2 | GA | LAB |
| O06 | 2026-09-22 | 13:00–15:00 | A06 | T3 | GB | LAB |
| O07 | 2026-09-23 | 13:00–15:00 | A01 | T1 | GA | LAB |
| O08 | 2026-09-23 | 08:00–10:00 | A02 | T2 | GB | LAB |
| O09 | 2026-09-23 | 08:00–09:00 | A03 | T3 | GA | RA |
| O10 | 2026-09-23 | 10:00–11:00 | A04 | T3 | GB | RB |
| O11 | 2026-09-24 | 08:00–10:00 | A05 | T2 | GA | LAB |
| O12 | 2026-09-24 | 10:00–12:00 | A06 | T3 | GB | LAB |
| O13 | 2026-09-25 | 08:00–09:30 | A07 | T3 | GA | RA |
| O14 | 2026-09-25 | 09:30–11:00 | A08 | T3 | GB | RB |

Contoh pemeriksaan penting: O03 boleh dimulai saat O01 selesai karena interval tidak berbenturan; O05 menunggu pemeliharaan lab selesai; O07 memakai T1 hanya setelah 13:00; O04 menghindari booking RB dan benturan kelompok; O11/O12 selesai sebelum booking LAB Kamis sore.

### 6.1 Beban harian jadwal acuan

| Resource | Senin | Selasa | Rabu | Kamis | Jumat | Batas per hari |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 120 | 0 | 120 | 0 | 0 | 240 |
| T2 | 120 | 120 | 120 | 120 | 0 | 240 |
| T3 | 120 | 120 | 120 | 120 | 180 | 240 |
| GA | 180 | 120 | 180 | 120 | 90 | 240 |
| GB | 180 | 120 | 180 | 120 | 90 | 240 |

Semua angka dalam menit. Total sesi terjadwal 1.380 menit; total beban tidak dijumlahkan lintas semua resource sebagai durasi sesi karena satu sesi memakai tiga resource sekaligus.

### 6.2 Skor jadwal acuan

| Preference | Terpenuhi | Tidak terpenuhi | Bobot diperoleh / relevan |
| --- | --- | --- | --- |
| P01 | O01, O02, O08 | O07 | 15 / 20 |
| P02 | O01, O07 | O02, O08 | 6 / 12 |
| P03 | O05, O11 | O06, O12 | 6 / 12 |
| P04 | O03, O09, O13 | — | 3 / 3 |
| P05 | O03, O09, O10, O13, O14 | O04 | 5 / 6 |
| **Total** | | | **35 / 53 = 66,04%** |

Skor ini sengaja tidak dijadikan target optimum. Contoh perbaikan yang valid: ganti pengajar O02 dari T2 ke T1 tanpa mengubah waktunya. T1 kini mengajar 08:00–12:00, total 240 menit pada Senin; P02 bertambah 3 sehingga skor menjadi 38/53 = 71,70%. Ini menjadi pasangan pembanding sederhana untuk evaluator preference tahap 2. Jangan menuntut hasil solver persis sama dengan jadwal acuan.

## 7. Varian kasus uji untuk tahap 2

Setiap kasus dimulai dari dataset utama yang utuh, lalu hanya menerapkan perubahan pada barisnya. “Edit assignment” menguji validator; “ubah input” menguji validasi awal/pencarian. Seluruh kasus di bawah merupakan spesifikasi ekspektasi, belum laporan pengujian solver.

| ID | Perubahan / tindakan | Ekspektasi yang harus dibuktikan |
| --- | --- | --- |
| C01 | Jalankan dataset utama. | Temukan 14 assignment lengkap dan valid. Hasil Optimal atau Feasible sesuai bukti runtime; tidak perlu identik dengan acuan. |
| C02 | Edit O03 menjadi 09:00–10:00, resource tetap. | Tolak: GA bentrok O01 meskipun pengajar dan ruangan berbeda (H02). |
| C03 | Edit O04 menjadi 10:00–11:00, resource tetap. | Tolak: T3 bentrok O03 dan GB bentrok O02 (H02). |
| C04 | Edit O02 menjadi 09:00–11:00. | Tolak: LAB bentrok O01 (H02). |
| C05 | Edit ruangan O04 menjadi RA. | Tolak: kursi kurang dan bukan kandidat (H04). |
| C06 | Edit pengajar O03 menjadi T1. | Tolak: tidak memiliki kompetensi career/bukan kandidat (H04), walaupun T1 kosong pada jam itu. |
| C07 | Edit O07 menjadi 10:00–12:00 dengan T1. | Tolak: override T1 Rabu (H03). |
| C08 | Edit O05 menjadi 08:00–10:00. | Tolak: LAB dalam pemeliharaan (H03). |
| C09 | Edit O05 menjadi 11:00–13:00. | Tolak: melintasi istirahat (H05/H06). |
| C10 | Edit O13 menjadi 08:00–09:00; terpisah, coba mulai 08:15–09:45. | Tolak masing-masing karena durasi salah dan batas tidak selaras slot (H05). |
| C11 | Ubah input: kunci juga O02 pada 08:00–10:00, T2 + GB + LAB. | Validasi awal menolak konflik dua kunci di LAB; tidak menyamarkannya sebagai hasil solver. |
| C12 | Ubah input: batas beban T3 Jumat menjadi 150 menit, dengan batas 240 pada hari lain. Tidak ada pengajar career alternatif. | Kasus mustahil: O13 + O14 memerlukan 180 menit T3 pada Jumat. Pemeriksa awal yang mampu membuktikan boleh menolak dengan alasan ini; jika masuk pencarian, engine harus membuktikan Infeasible. |
| C13 | Dataset terisolasi: hanya O05/O06 dan activity A05/A06, horizon 22 September, tanpa kunci, booking, preference, atau pengulangan Kamis. Tetapkan LAB tersedia hanya 10:00–12:00. | Masing-masing sesi bisa ditempatkan sendiri, keduanya memerlukan total 240 menit pada LAB kapasitas 1 yang hanya tersedia 120 menit. Mustahil bersama. Bukti agregat atau hasil Infeasible diperlukan; bukan timeout yang dianggap bukti. |
| C14 | Dataset terisolasi: hanya O07/A01 pada 23 September, tanpa kunci/booking, batasi jendela activity ke 08:00–12:00, pertahankan kandidat T1/T2 serta P01 dan P02 saja. | Tetap dapat dijadwalkan pagi; P02 gagal karena T1 tidak tersedia pagi itu, tetapi tetap berbobot relevan. Skor maksimum 5/8 = 62,50%, bukan Infeasible atau 100%. Preferensi T1 tidak boleh mengabaikan override ketersediaannya. |
| C15 | Hapus semua preference. | Jadwal lengkap tetap diperlukan; tampilkan “Tidak ada preference”, skor null. Status optimalitas mengikuti bukti engine. |
| C16 | Evaluasi jadwal acuan, lalu ganti T2 menjadi T1 hanya di O02. | Keduanya valid; jumlah bobot berubah 35 → 38, penyebut tetap 53. |
| C17 | Hapus assignment O14 dari jadwal acuan. | Kelengkapan 13/14, O14 tercantum belum terjadwal; tolak publikasi. Jangan laporkan hasil Feasible/Optimal untuk jadwal parsial. |
| C18 | Edit O12 menjadi 13:00–15:00. | Tolak: bentrok dengan booking B02 di LAB (H02/H09). |
| C19 | Simulasikan versi terbit PILOT-V1 berisi jadwal acuan; draft revisi menyatakan menggantikan PILOT-V1. Pertahankan B01/B02. | Assignment PILOT-V1 tidak dihitung sebagai booking tambahan; B01/B02 tetap diperhitungkan. Tanpa identitas versi pengganti, versi terbit tidak boleh dikeluarkan diam-diam. |
| C20 | Ubah snapshot sumber setelah job dibuat: T1 menjadi tidak tersedia seharian Senin. | Hasil lama tetap terikat revisi lama; publikasi ditolak sebagai kedaluwarsa, dan O01 terdeteksi bermasalah saat validasi terbaru. Engine tidak menggeser kunci otomatis. |
| C21 | Ubah input: tambah 23 September ke excluded_dates A01 dan bangun ulang occurrence. | O07 tidak terbentuk; total 13 occurrence, penyebut preference menjadi 45. Jangan membawa O07 sebagai kewajiban atau tetap memakai penyebut 53. |
| C22 | Ubah input: hari libur organisasi 25 September; biarkan O13/O14 wajib. | Tidak ada penempatan valid pada Jumat. Hari libur tidak menghapus occurrence secara diam-diam; operator harus mengubah recurrence/aturan secara eksplisit. |

Untuk C12, representasikan perubahan sebagai aturan beban khusus tanggal; field dasar `max_daily_minutes` pada dataset utama berlaku semua hari. Setiap varian wajib memperbarui input_revision dan memiliki ID dataset berbeda. Pada varian terisolasi, daftar occurrence, recurrence, preference target, serta kunci harus konsisten dengan cakupannya.

### 7.1 Kasus tambahan kapasitas di atas satu

PRD §7.3 juga mensyaratkan pengujian kapasitas >1. Gunakan fixture kecil terpisah agar arti ruang kelas utama tetap jelas: LAB-SHARED adalah laboratorium 60 kursi yang dibagi menjadi dua area tetap masing-masing 30 kursi. Resource ini mempunyai `concurrent_capacity = 2`, atribut `seats_per_unit = 30`, tag computer/projector, tersedia 08:00–10:00. Ini konvensi fixture; kebutuhan kecocokan memakai seats_per_unit untuk satu area.

Jadwalkan dua sesi praktik web berdurasi 120 menit dengan jendela tunggal 08:00–10:00: sesi pertama memakai T1 + GA + 1 unit LAB-SHARED, kedua memakai T2 + GB + 1 unit LAB-SHARED. Pengajar dan kelompok tersedia, masing-masing berkapasitas 1 dan batas harian 240 menit. Tanpa booking, kunci, atau preference. Kedua sesi harus dapat berjalan bersama karena total pemakaian lab = 2. Ketika kapasitas LAB-SHARED diubah menjadi 1, keduanya mustahil ditempatkan bersama. Ketika GB diubah menjadi 31 peserta, kebutuhan satu area harus ditolak karena melebihi 30 kursi per unit, meskipun kapasitas serentak lab 2.

Fixture ini membuktikan batas serentak tidak boleh dikodekan selalu sebagai “tidak overlap”. Ini bukan dukungan otomatis untuk memecah kelompok atau menghitung dua area sebagai satu kebutuhan; aktivitas di fixture selalu memakai tepat satu area.

## 8. Kontrak hasil yang harus diuji kelak

| Status hasil PRD | Bukti yang dibutuhkan | Implikasi |
| --- | --- | --- |
| Optimal | Jadwal lengkap valid dan optimalitas objective untuk snapshot tersebut telah dibuktikan engine. | Dapat ditinjau untuk publikasi; tetap melewati semua gate. |
| Feasible | Jadwal lengkap valid ditemukan; optimalitas belum terbukti. | Dapat ditinjau untuk publikasi; skor kurang dari 100% tetap boleh. |
| Infeasible | Ada bukti tidak ada jadwal lengkap yang memenuhi semua constraint. | Perbaiki input/aturan; tidak boleh menerbitkan hasil. |
| Belum ditemukan | Batas waktu tercapai tanpa solusi lengkap dan tanpa bukti infeasible. | Boleh mencoba ulang; jangan menyatakan jadwal mustahil. |
| Gagal / dibatalkan | Kesalahan teknis atau pembatalan job. | Bukan bukti infeasible; tidak menjadikan hasil parsial layak publikasi. |

Status job dan status solusi terpisah. Job yang selesai normal dapat menghasilkan Infeasible atau Belum ditemukan. Versi jadwal juga terpisah: Draft → Published → Archived. Kesalahan input/model bukan bukti ketidakmungkinan jadwal yang valid secara bisnis.

Dataset kecil tidak dapat memaksa status Feasible atau Belum ditemukan hanya dengan menentukan data. Solver bisa langsung membuktikan Optimal. Pada tahap 2, uji kontrak status memakai hasil terkontrol dan uji integrasi memakai batas pencarian yang dicatat. Jangan mengasumsikan timeout sangat kecil selalu menghasilkan status tertentu; catat status yang benar-benar dikembalikan. Kasus pembatalan dan kegagalan worker juga memerlukan kontrol proses pada tahap 2, bukan sekadar perubahan dataset.

Catatan hasil minimum untuk tahap 2: dataset/schema/input revision, identitas job, status job, status solusi, assignment, jumlah wajib/terjadwal, occurrence belum terjadwal, pelanggaran constraint hasil validator, rincian tiap pasangan preference, bobot terpenuhi/relevan, skor atau null, waktu antre terpisah dari waktu solver, alasan berhenti, diagnosis beserta tingkat kepastiannya. Versi runtime/solver dan pengaturan komputasi dicatat agar hasil dapat diulang.

Gate publikasi: seluruh occurrence wajib terjadwal tepat sekali, semua constraint lulus validator terpisah, input masih mutakhir, dan tidak bertabrakan dengan jadwal terbit terbaru. Pemeriksaan serta penggantian versi dilakukan atomik pada implementasi produk. Pilot tahap 1 menetapkan acuannya; tidak menguji transaksi database atau implementasi publikasi.

## 9. Kriteria penutupan tahap 1 dan serah-terima

Tahap 1 menyediakan: ruang lingkup dan asumsi, resource/ketersediaan, activity/occurrence, constraint teridentifikasi, preference berbobot, snapshot contoh, jadwal acuan lengkap, perhitungan skor, serta varian negatif dan kontrak hasil. Konsistensi dataset dan jadwal acuan diperiksa secara deterministik tanpa menjalankan solver.

Yang baru dibuktikan pada tahap 2: ketepatan model CP-SAT, kemampuan pencarian/optimasi, status runtime, batas waktu, serta kesesuaian dengan validator terpisah. Dataset ini belum merupakan benchmark skala 100 resource/500 occurrence dan belum memvalidasi kebijakan nyata lembaga pelatihan.

## Lampiran A — Snapshot input contoh

JSON berikut dapat disalin menjadi fixture tahap 2. Ini kontrak contoh versi `pilot-training-1.0.0`, bukan schema API/database final. Semua ID entitas di dalam snapshot milik WS-PILOT kecuali dinyatakan lain. `candidate_ids` merupakan pilihan alternatif; engine memilih `select_count`, bukan menggunakan semua kandidat.

Aturan interpretasi: tanggal ISO lokal, jam HH:MM lokal, ISO weekday 1=Senin sampai 7=Minggu; batas akhir periode dan recurrence inklusif; batas akhir interval eksklusif. `availability_profile_id` mereferensikan pola mingguan, override tanggal mengganti pola hari tersebut. Field `max_daily_minutes` yang tidak ada berarti tidak ada batas beban harian tambahan. `enabled_hard_rules` mengacu definisi H01–H09 dalam dokumen ini. Snapshot ini hanya berisi input, sedangkan assignment acuan ada di Lampiran B.

```json
{
  "schema_version": "pilot-training-1.0.0",
  "dataset_id": "TRAINING-BASE-01",
  "input_revision": 1,
  "workspace": {"id": "WS-PILOT","name": "Balai Pelatihan Contoh","timezone": "Asia/Makassar"},
  "period": {"start_date": "2026-09-21","end_date": "2026-09-25","slot_minutes": 30},
  "calendar": {"iso_weekdays": [1,2,3,4,5],"open_windows": [["08:00","12:00"],["13:00","16:00"]],"holidays": []},
  "availability_profiles": [{"id": "WORKDAYS","iso_weekdays": [1,2,3,4,5],"windows": [["08:00","12:00"],["13:00","16:00"]]}],
  "resources": [{"id": "T1","name": "Pengajar Arman","type": "instructor","tags": ["web"],"concurrent_capacity": 1,"max_daily_minutes": 240,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "T2","name": "Pengajar Bella","type": "instructor","tags": ["web","network"],"concurrent_capacity": 1,"max_daily_minutes": 240,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "T3","name": "Pengajar Citra","type": "instructor","tags": ["network","career"],"concurrent_capacity": 1,"max_daily_minutes": 240,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "GA","name": "Kelompok A","type": "participant_group","tags": [],"participant_count": 20,"concurrent_capacity": 1,"max_daily_minutes": 240,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "GB","name": "Kelompok B","type": "participant_group","tags": [],"participant_count": 28,"concurrent_capacity": 1,"max_daily_minutes": 240,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "RA","name": "Kelas A","type": "room","tags": ["classroom","projector"],"seats": 24,"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "RB","name": "Kelas B","type": "room","tags": ["classroom","projector"],"seats": 32,"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"},{"id": "LAB","name": "Laboratorium Komputer","type": "room","tags": ["computer","projector"],"seats": 30,"concurrent_capacity": 1,"active": true,"availability_profile_id": "WORKDAYS"}],
  "availability_overrides": [{"resource_id": "T1","date": "2026-09-23","available_windows": [["13:00","16:00"]],"reason": "Tidak tersedia pagi"},{"resource_id": "LAB","date": "2026-09-22","available_windows": [["10:00","12:00"],["13:00","16:00"]],"reason": "Pemeliharaan 08:00–10:00"}],
  "activities": [{"id": "A01","name": "Praktik Web A","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["web"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GA","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","computer"],"min_seats": 20,"candidate_ids": ["LAB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A02","name": "Praktik Web B","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["web"],"candidate_ids": ["T1","T2"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GB","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","computer"],"min_seats": 28,"candidate_ids": ["LAB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A03","name": "Komunikasi Kerja A","active": true,"duration_minutes": 60,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["career"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GA","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","classroom"],"min_seats": 20,"candidate_ids": ["RA","RB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A04","name": "Komunikasi Kerja B","active": true,"duration_minutes": 60,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [1,3],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["career"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GB","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","classroom"],"min_seats": 28,"candidate_ids": ["RB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A05","name": "Praktik Jaringan A","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2,4],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["network"],"candidate_ids": ["T2","T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GA","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","computer"],"min_seats": 20,"candidate_ids": ["LAB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A06","name": "Praktik Jaringan B","active": true,"duration_minutes": 120,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [2,4],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["network"],"candidate_ids": ["T2","T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GB","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","computer"],"min_seats": 28,"candidate_ids": ["LAB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A07","name": "Persiapan Karier A","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [5],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["career"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GA","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","classroom"],"min_seats": 20,"candidate_ids": ["RA","RB"],"select_count": 1,"units_per_selected_resource": 1}]},{"id": "A08","name": "Persiapan Karier B","active": true,"duration_minutes": 90,"allowed_windows": [["08:00","12:00"],["13:00","16:00"]],"recurrence": {"frequency": "weekly","iso_weekdays": [5],"start_date": "2026-09-21","until_date": "2026-09-25","excluded_dates": []},"requirements": [{"role": "instructor","type": "instructor","required_tags": ["career"],"candidate_ids": ["T3"],"select_count": 1,"units_per_selected_resource": 1},{"role": "group","type": "participant_group","fixed_resource_id": "GB","select_count": 1,"units_per_selected_resource": 1},{"role": "room","type": "room","required_tags": ["projector","classroom"],"min_seats": 28,"candidate_ids": ["RB"],"select_count": 1,"units_per_selected_resource": 1}]}],
  "occurrences": [{"id": "O01","activity_id": "A01","date": "2026-09-21","required": true},{"id": "O02","activity_id": "A02","date": "2026-09-21","required": true},{"id": "O03","activity_id": "A03","date": "2026-09-21","required": true},{"id": "O04","activity_id": "A04","date": "2026-09-21","required": true},{"id": "O05","activity_id": "A05","date": "2026-09-22","required": true},{"id": "O06","activity_id": "A06","date": "2026-09-22","required": true},{"id": "O07","activity_id": "A01","date": "2026-09-23","required": true},{"id": "O08","activity_id": "A02","date": "2026-09-23","required": true},{"id": "O09","activity_id": "A03","date": "2026-09-23","required": true},{"id": "O10","activity_id": "A04","date": "2026-09-23","required": true},{"id": "O11","activity_id": "A05","date": "2026-09-24","required": true},{"id": "O12","activity_id": "A06","date": "2026-09-24","required": true},{"id": "O13","activity_id": "A07","date": "2026-09-25","required": true},{"id": "O14","activity_id": "A08","date": "2026-09-25","required": true}],
  "enabled_hard_rules": ["H01","H02","H03","H04","H05","H06","H07","H08","H09"],
  "locks": [{"occurrence_id": "O01","date": "2026-09-21","start": "08:00","end": "10:00","resources": {"instructor": "T1","group": "GA","room": "LAB"}}],
  "published_bookings": [{"id": "B01","workspace_id": "WS-PILOT","schedule_version_id": "EXT-ROOM-V1","date": "2026-09-21","start": "08:00","end": "10:00","resource_units": {"RB": 1},"label": "Rapat internal"},{"id": "B02","workspace_id": "WS-PILOT","schedule_version_id": "EXT-LAB-V1","date": "2026-09-24","start": "13:00","end": "15:00","resource_units": {"LAB": 1},"label": "Uji kompetensi eksternal"}],
  "replaces_schedule_version_id": null,
  "preferences": [{"id": "P01","type": "preferred_time","activity_ids": ["A01","A02"],"weight": 5,"window": ["08:00","12:00"],"match": "full_interval","active": true},{"id": "P02","type": "preferred_resource","activity_ids": ["A01","A02"],"weight": 3,"role": "instructor","resource_ids": ["T1"],"active": true},{"id": "P03","type": "preferred_resource","activity_ids": ["A05","A06"],"weight": 3,"role": "instructor","resource_ids": ["T2"],"active": true},{"id": "P04","type": "preferred_resource","activity_ids": ["A03","A07"],"weight": 1,"role": "room","resource_ids": ["RA"],"active": true},{"id": "P05","type": "preferred_time","activity_ids": ["A03","A04","A07","A08"],"weight": 1,"window": ["08:00","12:00"],"match": "full_interval","active": true}],
  "solver_budget_seconds": 60
}
```

## Lampiran B — Assignment acuan

```json
[
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
  },
  {
    "occurrence_id": "O02",
    "date": "2026-09-21",
    "start": "10:00",
    "end": "12:00",
    "resources": {
      "instructor": "T2",
      "group": "GB",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O03",
    "date": "2026-09-21",
    "start": "10:00",
    "end": "11:00",
    "resources": {
      "instructor": "T3",
      "group": "GA",
      "room": "RA"
    }
  },
  {
    "occurrence_id": "O04",
    "date": "2026-09-21",
    "start": "13:00",
    "end": "14:00",
    "resources": {
      "instructor": "T3",
      "group": "GB",
      "room": "RB"
    }
  },
  {
    "occurrence_id": "O05",
    "date": "2026-09-22",
    "start": "10:00",
    "end": "12:00",
    "resources": {
      "instructor": "T2",
      "group": "GA",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O06",
    "date": "2026-09-22",
    "start": "13:00",
    "end": "15:00",
    "resources": {
      "instructor": "T3",
      "group": "GB",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O07",
    "date": "2026-09-23",
    "start": "13:00",
    "end": "15:00",
    "resources": {
      "instructor": "T1",
      "group": "GA",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O08",
    "date": "2026-09-23",
    "start": "08:00",
    "end": "10:00",
    "resources": {
      "instructor": "T2",
      "group": "GB",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O09",
    "date": "2026-09-23",
    "start": "08:00",
    "end": "09:00",
    "resources": {
      "instructor": "T3",
      "group": "GA",
      "room": "RA"
    }
  },
  {
    "occurrence_id": "O10",
    "date": "2026-09-23",
    "start": "10:00",
    "end": "11:00",
    "resources": {
      "instructor": "T3",
      "group": "GB",
      "room": "RB"
    }
  },
  {
    "occurrence_id": "O11",
    "date": "2026-09-24",
    "start": "08:00",
    "end": "10:00",
    "resources": {
      "instructor": "T2",
      "group": "GA",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O12",
    "date": "2026-09-24",
    "start": "10:00",
    "end": "12:00",
    "resources": {
      "instructor": "T3",
      "group": "GB",
      "room": "LAB"
    }
  },
  {
    "occurrence_id": "O13",
    "date": "2026-09-25",
    "start": "08:00",
    "end": "09:30",
    "resources": {
      "instructor": "T3",
      "group": "GA",
      "room": "RA"
    }
  },
  {
    "occurrence_id": "O14",
    "date": "2026-09-25",
    "start": "09:30",
    "end": "11:00",
    "resources": {
      "instructor": "T3",
      "group": "GB",
      "room": "RB"
    }
  }
]
```
