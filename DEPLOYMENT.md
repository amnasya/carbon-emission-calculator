# Panduan Deployment

## Deployment ke Production

### Persiapan

1. Pastikan semua dependencies terinstall:
```bash
pip install -r requirements.txt
```

2. Set environment variables yang diperlukan di `.env`

3. Test aplikasi secara lokal:
```bash
python app.py
```

### Deployment dengan Gunicorn (Linux/Mac)

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Jalankan aplikasi:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Deployment dengan Docker

1. Buat Dockerfile:
```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

2. Build dan run:
```bash
docker build -t carbon-emission-calculator .
docker run -p 5000:5000 carbon-emission-calculator
```

### Deployment ke Cloud

#### Heroku

1. Buat `Procfile`:
```
web: gunicorn app:app
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

#### Railway/Render

Upload repository dan set build command:
```bash
pip install -r requirements.txt
```

Start command:
```bash
gunicorn app:app
```

## Environment Variables

Pastikan set environment variables berikut di production:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`

## Monitoring

Gunakan logging untuk monitoring:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Backup Model Files

Pastikan file model ML (.joblib) ter-backup:
- mlr_emission_model.joblib
- mlr_emission_scaler.joblib
- mlr_emission_encoder.joblib
- fuel_model.joblib
- fuel_scaler.joblib
