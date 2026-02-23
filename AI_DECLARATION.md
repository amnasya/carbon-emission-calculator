# Declaration of AI Tool Usage

## Carbon Emission Calculator Project

---

## A. AI Tool yang Digunakan

- **Kiro** (AI Assistant IDE)

---

## 1. Annotated Contributions (AI vs Human)

| Komponen | Human Contribution | AI Contribution |
|----------|-------------------|-----------------|
| Konsep & Ide | Menentukan topik carbon emission calculator, menentukan fitur utama (kalkulasi emisi, rute alternatif, rekomendasi) | - |
| Arsitektur Sistem | Merancang struktur Flask app, menentukan endpoint API, flow data | Memberikan saran struktur folder dan best practice |
| emission.py | Riset emission factor dari jurnal ilmiah, implementasi formula perhitungan CO2 | Membantu debugging dan refactoring kode |
| maps_api.py | Memilih OpenStreetMap sebagai provider, implementasi logic routing | Membantu error handling dan exception |
| ml_predictor.py | Pemilihan algoritma ML, training model, tuning hyperparameter | Saran optimasi dan code review |
| mlr_emission_predictor.py | Desain feature extraction, model architecture | Membantu implementasi class structure |
| Frontend (templates/) | Desain UI/UX, layout halaman, user flow | Membantu responsive CSS dan JavaScript |
| visualization.py | Konsep visualisasi chart emisi | Membantu implementasi matplotlib |
| advisor.py | Logic rekomendasi pengurangan emisi | Membantu formatting output |
| Testing (tests/) | Menulis test case, skenario testing | Membantu generate test data |
| Documentation | Konten dan struktur dokumentasi | Membantu formatting PANDUAN.md |
| Deployment & Setup | Konfigurasi environment, requirements.txt | Troubleshooting error saat running |

**Persentase Kontribusi Estimasi:**
- Human: ~70-75%
- AI: ~25-30%

---

## 2. Reflections on AI Outputs

**Kelebihan Menggunakan AI:**
- Mempercepat proses debugging dengan identifikasi error yang cepat
- Membantu menulis boilerplate code sehingga bisa fokus ke logic utama
- Memberikan alternatif solusi ketika stuck pada suatu masalah
- Membantu formatting dan dokumentasi yang konsisten

**Keterbatasan AI yang Ditemukan:**
- AI tidak memahami konteks bisnis spesifik (emission factor kendaraan Indonesia)
- Perlu validasi manual untuk memastikan akurasi perhitungan
- Kadang memberikan solusi yang terlalu generic, perlu disesuaikan
- Tidak bisa melakukan riset data terbaru (emission factor, regulasi)

**Pembelajaran:**
- AI efektif sebagai "pair programmer" bukan pengganti programmer
- Tetap perlu pemahaman fundamental untuk memvalidasi output AI
- Kritis dalam menerima saran AI, tidak semua saran cocok untuk konteks project

---

## 3. Ethical and Safety Review

**Data Privacy:**
- Aplikasi tidak menyimpan data lokasi pengguna secara permanen
- Koordinat hanya digunakan untuk kalkulasi real-time
- Tidak ada data personal yang dikumpulkan

**Accuracy & Reliability:**
- Emission factor berdasarkan standar IPCC dan penelitian ilmiah
- Hasil kalkulasi bersifat estimasi, bukan nilai absolut
- Disclaimer ditampilkan bahwa hasil adalah perkiraan

**Environmental Impact:**
- Aplikasi bertujuan positif: meningkatkan awareness emisi karbon
- Mendorong pengguna memilih rute dengan emisi lebih rendah
- Tidak ada dampak negatif terhadap lingkungan

**Bias & Fairness:**
- Model ML ditraining dengan data yang representatif
- Tidak ada diskriminasi berdasarkan jenis kendaraan tertentu
- Semua jenis kendaraan dikalkulasi dengan standar yang sama

**Responsible AI Use:**
- AI digunakan sebagai tool bantu, bukan decision maker
- Human oversight tetap ada dalam setiap tahap development
- Output AI selalu direview dan divalidasi sebelum digunakan

**Safety Considerations:**
- Aplikasi tidak memberikan instruksi mengemudi real-time
- Tidak menggantikan fungsi GPS/navigasi
- Pengguna tetap bertanggung jawab atas keputusan berkendara

---

## Pernyataan

Saya menyatakan bahwa penggunaan AI tool dalam project ini bersifat sebagai asisten untuk mempercepat proses development, bukan sebagai pengganti pemahaman konsep. Saya memahami sepenuhnya kode yang ditulis dan logika yang diimplementasikan dalam aplikasi ini.
