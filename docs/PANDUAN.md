# Panduan Penggunaan Carbon Emission Calculator

## Deskripsi
Aplikasi web untuk menghitung emisi karbon dari perjalanan kendaraan berdasarkan rute, jenis kendaraan, dan bahan bakar.

## Persyaratan Sistem
- Python 3.8 atau lebih baru
- Koneksi internet (untuk mengambil data rute)

## Instalasi

### 1. Extract file backup
Extract `carbon-emission-backup.zip` ke folder yang diinginkan.

### 2. Buat Virtual Environment (Opsional tapi Disarankan)
```bash
python -m venv .venv
```

Aktifkan virtual environment:
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

### Web Application (Sederhana)
```bash
python run_web.py
```
Buka browser dan akses: http://localhost:5000

### Web Application (Dengan ML)
```bash
python app.py
```
Buka browser dan akses: http://localhost:5000

## Cara Menggunakan

1. Buka aplikasi di browser (http://localhost:5000)
2. Masukkan koordinat titik asal (latitude, longitude)
3. Masukkan koordinat titik tujuan (latitude, longitude)
4. Pilih jenis kendaraan (LCGC, SUV, Sedan, EV)
5. Pilih jenis bahan bakar (bensin, solar, listrik)
6. Klik tombol "Hitung" untuk melihat hasil

## Fitur Utama

- **Perhitungan Emisi**: Menghitung emisi CO2 berdasarkan jarak dan jenis kendaraan
- **Rute Alternatif**: Menampilkan beberapa rute dengan perbandingan emisi
- **Rekomendasi**: Memberikan saran rute dengan emisi terendah
- **Visualisasi**: Grafik perbandingan emisi antar rute
- **ML Prediction**: Prediksi emisi menggunakan machine learning (opsional)

## Jenis Kendaraan yang Didukung

| Kendaraan | Bahan Bakar |
|-----------|-------------|
| LCGC | Bensin |
| SUV | Bensin, Solar |
| Sedan | Bensin |
| EV | Listrik |

## Struktur File Penting

- `run_web.py` - Web app sederhana (tanpa ML)
- `app.py` - Web app lengkap dengan ML
- `emission.py` - Logika perhitungan emisi
- `maps_api.py` - Integrasi dengan OpenStreetMap
- `ml_predictor.py` - Prediksi menggunakan ML
- `templates/` - File HTML
- `static/` - File CSS dan JavaScript

## Troubleshooting

### Port 5000 sudah digunakan
Ubah port di file `run_web.py` atau `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Module not found
Pastikan sudah install semua dependencies:
```bash
pip install -r requirements.txt
```

### Tidak bisa akses rute
Pastikan koneksi internet aktif karena aplikasi menggunakan OpenStreetMap API.

## Menghentikan Aplikasi
Tekan `Ctrl+C` di terminal untuk menghentikan server.
