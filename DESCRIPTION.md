# Carbon Emission Calculator - Deskripsi Aplikasi

## 🌍 Tentang Aplikasi

Carbon Emission Calculator adalah aplikasi berbasis web dan CLI yang dirancang untuk menghitung emisi karbon dioksida (CO₂) dari perjalanan kendaraan bermotor. Aplikasi ini membantu pengguna memahami dampak lingkungan dari pilihan transportasi mereka dan memberikan rekomendasi untuk mengurangi jejak karbon.

## 🎯 Tujuan

Aplikasi ini dikembangkan dengan tujuan:
- **Meningkatkan Kesadaran Lingkungan**: Membantu masyarakat memahami kontribusi emisi karbon dari aktivitas perjalanan sehari-hari
- **Mendukung Keputusan Berkelanjutan**: Memberikan informasi untuk memilih rute dan kendaraan yang lebih ramah lingkungan
- **Edukasi**: Menyediakan visualisasi dan rekomendasi praktis untuk mengurangi emisi karbon

## ✨ Fitur Utama

### 1. Perhitungan Emisi Multi-Kendaraan
- Mendukung berbagai jenis kendaraan: LCGC, SUV, dan Electric Vehicle (EV)
- Perhitungan untuk berbagai jenis bahan bakar: Bensin, Solar, dan Listrik
- Akurasi tinggi dengan emission factors yang terstandarisasi

### 2. Pencarian Rute Alternatif
- Integrasi dengan OpenStreetMap untuk mendapatkan rute real-time
- Menampilkan hingga 3 rute alternatif dengan detail jarak dan waktu tempuh
- Turn-by-turn directions untuk setiap rute

### 3. Prediksi Berbasis Machine Learning
- **Multiple Linear Regression (MLR)**: Memprediksi emisi berdasarkan jarak, jenis kendaraan, konsumsi bahan bakar, dan kecepatan rata-rata
- **Random Forest Regressor**: Memprediksi konsumsi bahan bakar dengan mempertimbangkan berbagai faktor
- Model dilatih dengan data real-world untuk akurasi optimal

### 4. Perbandingan Rute Cerdas
- Membandingkan emisi dari berbagai rute alternatif
- Menampilkan rute dengan emisi terendah sebagai rekomendasi
- Menghitung penghematan emisi dalam gram dan persentase

### 5. Visualisasi Data
- **Grafik Progres Emisi**: Menampilkan akumulasi emisi per 25 km
- **Grafik Perbandingan**: Bar chart untuk membandingkan emisi antar rute
- Export grafik dalam format PNG

### 6. Rekomendasi Pengurangan Emisi
- Saran praktis untuk mengurangi emisi karbon
- Rekomendasi berdasarkan jenis kendaraan dan pola perjalanan
- Tips alternatif transportasi yang lebih ramah lingkungan

### 7. Dual Interface
- **Web Application**: Interface modern dan user-friendly dengan peta interaktif
- **CLI Application**: Command-line interface untuk pengguna advanced dan automation

## 🔬 Teknologi & Metodologi

### Machine Learning
- **Algoritma**: Multiple Linear Regression (MLR) dan Random Forest
- **Features**: Distance, fuel type, vehicle type, fuel consumption, average speed
- **Training Data**: Dataset komprehensif dengan berbagai kondisi perjalanan
- **Validation**: Cross-validation dan testing untuk memastikan akurasi

### Emission Factors
Aplikasi menggunakan emission factors yang terstandarisasi:
- **LCGC Bensin**: 120 g CO₂/km
- **LCGC Solar**: 95 g CO₂/km
- **SUV Bensin**: 250 g CO₂/km
- **SUV Solar**: 200 g CO₂/km
- **EV Listrik**: 0 g CO₂/km (zero emission)

### Routing Engine
- Menggunakan OpenStreetMap Routing API (OSRM)
- Real-time route calculation
- Mendukung multiple route alternatives

## 💡 Use Cases

### 1. Perencanaan Perjalanan Harian
Pengguna dapat merencanakan rute perjalanan sehari-hari (rumah-kantor, rumah-sekolah) dengan memilih rute yang paling efisien dari segi emisi.

### 2. Perbandingan Kendaraan
Sebelum membeli kendaraan baru, pengguna dapat membandingkan emisi dari berbagai jenis kendaraan untuk perjalanan rutin mereka.

### 3. Edukasi Lingkungan
Institusi pendidikan dapat menggunakan aplikasi ini sebagai alat pembelajaran tentang dampak transportasi terhadap lingkungan.

### 4. Corporate Sustainability
Perusahaan dapat menggunakan aplikasi untuk menghitung dan melacak carbon footprint dari armada kendaraan mereka.

### 5. Penelitian & Analisis
Peneliti dapat menggunakan CLI interface untuk batch processing dan analisis data emisi dalam skala besar.

## 📊 Output & Hasil

Aplikasi memberikan output komprehensif:
- **Emisi Total**: Dalam gram dan kilogram CO₂
- **Jarak Tempuh**: Dalam kilometer
- **Waktu Perjalanan**: Estimasi durasi dalam menit
- **Kecepatan Rata-rata**: Untuk prediksi ML
- **Penghematan Potensial**: Jika memilih rute alternatif
- **Visualisasi Grafis**: Chart untuk analisis visual
- **Rekomendasi Aksi**: Langkah konkret untuk mengurangi emisi

## 🌟 Keunggulan

1. **Akurat**: Menggunakan ML dan emission factors terstandarisasi
2. **Real-time**: Data rute dari OpenStreetMap yang selalu update
3. **User-friendly**: Interface intuitif dan mudah digunakan
4. **Gratis & Open Source**: Dapat digunakan dan dikembangkan oleh siapa saja
5. **Edukatif**: Memberikan insight dan rekomendasi yang actionable
6. **Fleksibel**: Tersedia dalam web dan CLI interface
7. **Extensible**: Mudah dikembangkan dengan fitur tambahan

## 🎓 Target Pengguna

- **Masyarakat Umum**: Yang peduli dengan lingkungan dan ingin mengurangi jejak karbon
- **Pelajar & Mahasiswa**: Untuk pembelajaran tentang sustainability
- **Peneliti**: Untuk analisis data emisi transportasi
- **Perusahaan**: Untuk sustainability reporting dan fleet management
- **Pemerintah**: Untuk policy making terkait transportasi berkelanjutan
- **Developer**: Yang ingin berkontribusi pada open source environmental tools

## 🚀 Pengembangan Masa Depan

Potensi pengembangan aplikasi:
- Integrasi dengan real-time traffic data
- Support untuk lebih banyak jenis kendaraan (motor, bus, truk)
- Gamification untuk mendorong penggunaan transportasi ramah lingkungan
- Mobile app (iOS & Android)
- API untuk integrasi dengan aplikasi lain
- Carbon offset calculator dan marketplace
- Social features untuk berbagi achievement
- Multi-language support

## 📈 Impact

Dengan menggunakan aplikasi ini, pengguna dapat:
- **Mengurangi emisi karbon** hingga 20-30% dengan memilih rute optimal
- **Menghemat bahan bakar** dengan rute yang lebih efisien
- **Meningkatkan awareness** tentang dampak transportasi terhadap lingkungan
- **Berkontribusi** pada upaya global mengurangi pemanasan global

## 🤝 Kontribusi pada SDGs

Aplikasi ini mendukung Sustainable Development Goals (SDGs):
- **SDG 11**: Sustainable Cities and Communities
- **SDG 13**: Climate Action
- **SDG 7**: Affordable and Clean Energy
- **SDG 9**: Industry, Innovation, and Infrastructure

## 📝 Lisensi

Aplikasi ini menggunakan MIT License, yang berarti:
- Gratis untuk digunakan
- Dapat dimodifikasi sesuai kebutuhan
- Dapat didistribusikan ulang
- Open source dan transparan

---

**Carbon Emission Calculator** - *Driving Towards a Greener Future* 🌱🚗
