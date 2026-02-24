# Carbon Emission Calculator

Aplikasi kalkulator emisi karbon untuk perjalanan kendaraan dengan dukungan Machine Learning dan visualisasi rute alternatif.

## Fitur Utama

- 🚗 Perhitungan emisi karbon untuk berbagai jenis kendaraan (LCGC, SUV, EV)
- 🗺️ Pencarian rute alternatif dengan OpenStreetMap
- 🤖 Prediksi emisi menggunakan Machine Learning
- 📊 Visualisasi grafik emisi dan perbandingan rute
- 💡 Rekomendasi pengurangan emisi
- 🌐 Interface web interaktif dengan Flask

## Instalasi

1. Clone repository:
```bash
git clone <repository-url>
cd carbon-emission-calculator
```

2. Buat virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# atau
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Setup environment variables:
```bash
cp .env.template .env
# Edit .env dan tambahkan API keys yang diperlukan
```

## Penggunaan

### CLI Mode
```bash
python main.py
```

### Web Application
```bash
python app.py
```
Buka browser di `http://localhost:5000`

## Struktur Project

```
├── app.py                       # Flask web application
├── main.py                      # CLI interface
├── requirements.txt             # Python dependencies
├── .env.template                # Environment variables template
├── src/                         # Source code
│   ├── __init__.py
│   ├── emission.py              # Emission calculation logic
│   ├── maps_api.py              # OpenStreetMap API integration
│   ├── mlr_emission_predictor.py # ML emission predictor
│   ├── ml_predictor.py          # Fuel consumption predictor
│   ├── visualization.py         # Chart generation
│   ├── advisor.py               # Emission reduction advisor
│   ├── route_comparator.py      # Route comparison logic
│   ├── emission_formatter.py    # Emission formatting utilities
│   ├── train_mlr_model.py       # ML model training script
│   ├── mlr_config.py            # ML configuration
│   ├── mlr_config.example.json  # Example ML config
│   ├── templates/               # HTML templates
│   └── static/                  # Static assets (CSS, JS)
├── models/                      # Trained ML models
│   ├── mlr_emission_model.joblib
│   ├── mlr_emission_scaler.joblib
│   ├── mlr_emission_encoder.joblib
│   ├── mlr_feature_info.joblib
│   ├── fuel_model.joblib
│   └── fuel_scaler.joblib
├── tests/                       # Unit tests
└── .github/                     # GitHub Actions workflows
    └── workflows/
        └── python-app.yml
```

## Testing

```bash
pytest tests/
```

## Model Files

Model ML yang sudah dilatih (di folder `models/`):
- `mlr_emission_model.joblib` - Model prediksi emisi
- `mlr_emission_scaler.joblib` - Scaler untuk normalisasi data
- `mlr_emission_encoder.joblib` - Encoder untuk kategori
- `mlr_feature_info.joblib` - Informasi fitur model
- `fuel_model.joblib` - Model konsumsi bahan bakar
- `fuel_scaler.joblib` - Scaler untuk fuel model

## Teknologi

- Python 3.8+
- Flask - Web framework
- scikit-learn - Machine Learning
- matplotlib - Visualisasi
- OpenStreetMap - Routing API
- pytest - Testing

## Lisensi

MIT License - lihat file [LICENSE](LICENSE) untuk detail

## Kontribusi

Kontribusi sangat diterima! Silakan buat pull request atau buka issue untuk saran dan perbaikan.
