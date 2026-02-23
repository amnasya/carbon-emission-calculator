#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Demo: Perbandingan Static Calculation vs MLR Prediction
Menunjukkan perbedaan antara perhitungan statis dan ML prediction
"""

from mlr_emission_predictor import MLREmissionPredictor, FeatureExtractor
from emission import get_emission_factor

def print_separator():
    print("=" * 80)

def print_subseparator():
    print("-" * 80)

def demo_comparison():
    """
    Demo perbandingan Static vs MLR dengan input seperti di sistem
    """
    print_separator()
    print("DEMO: Perbandingan Static Calculation vs MLR Prediction")
    print_separator()
    
    # Initialize MLR predictor
    try:
        mlr_predictor = MLREmissionPredictor()
        feature_extractor = FeatureExtractor()
        print("\n✅ MLR Model berhasil dimuat")
    except Exception as e:
        print(f"\n❌ Error loading MLR model: {e}")
        print("Pastikan model sudah di-train dengan menjalankan: python train_mlr_model.py")
        return
    
    # Test cases berdasarkan screenshot
    test_cases = [
        {
            "name": "Test 1: Perjalanan Pendek (SUV Bensin)",
            "distance_km": 19.32,
            "duration_min": 19.3,
            "vehicle_type": "SUV",
            "fuel_type": "Bensin"
        },
        {
            "name": "Test 2: Perjalanan Sedang (LCGC Bensin)",
            "distance_km": 33.25,
            "duration_min": 32.0,
            "vehicle_type": "LCGC",
            "fuel_type": "Bensin"
        },
        {
            "name": "Test 3: Perjalanan Jauh - Tol (SUV Bensin)",
            "distance_km": 170.0,
            "duration_min": 120.0,  # Lancar di tol
            "vehicle_type": "SUV",
            "fuel_type": "Bensin"
        },
        {
            "name": "Test 4: Perjalanan Jauh - Macet (SUV Bensin)",
            "distance_km": 170.0,
            "duration_min": 240.0,  # Macet parah
            "vehicle_type": "SUV",
            "fuel_type": "Bensin"
        },
        {
            "name": "Test 5: EV Listrik",
            "distance_km": 50.0,
            "duration_min": 45.0,
            "vehicle_type": "EV",
            "fuel_type": "Listrik"
        }
    ]
    
    for test in test_cases:
        print("\n")
        print_separator()
        print(f"📍 {test['name']}")
        print_separator()
        
        # Input data
        distance_km = test['distance_km']
        duration_min = test['duration_min']
        vehicle_type = test['vehicle_type']
        fuel_type = test['fuel_type']
        
        # Calculate average speed
        avg_speed_kmh = (distance_km / duration_min) * 60.0
        
        # Get fuel consumption
        fuel_consumption_kml = feature_extractor.get_fuel_consumption(vehicle_type, fuel_type)
        
        print(f"\n📊 INPUT DATA:")
        print(f"   Jarak           : {distance_km:.2f} km")
        print(f"   Waktu Tempuh    : {duration_min:.1f} menit")
        print(f"   Kecepatan Rata² : {avg_speed_kmh:.1f} km/h")
        print(f"   Jenis Kendaraan : {vehicle_type}")
        print(f"   Jenis Bahan Bakar: {fuel_type}")
        print(f"   Konsumsi BB     : {fuel_consumption_kml:.1f} km/L")
        
        # STATIC CALCULATION
        print(f"\n🔢 STATIC CALCULATION:")
        print_subseparator()
        
        try:
            # Map fuel type for static calculation
            fuel_type_static = fuel_type.lower()
            if fuel_type_static == 'diesel':
                fuel_type_static = 'solar'
            elif fuel_type_static == 'listrik':
                fuel_type_static = 'listrik'
            
            # Map vehicle type for static calculation
            vehicle_type_static = vehicle_type
            
            emission_factor = get_emission_factor(vehicle_type_static, fuel_type_static)
            static_emission_g = distance_km * emission_factor
            static_emission_kg = static_emission_g / 1000.0
            
            print(f"   Formula: Emisi = Jarak × Faktor Emisi")
            print(f"   Faktor Emisi: {emission_factor} g/km")
            print(f"   Perhitungan: {distance_km:.2f} km × {emission_factor} g/km")
            print(f"   Hasil: {static_emission_g:,.0f} g = {static_emission_kg:.2f} kg CO₂")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            static_emission_g = None
            static_emission_kg = None
        
        # MLR PREDICTION
        print(f"\n🤖 MLR PREDICTION:")
        print_subseparator()
        
        try:
            mlr_emission_g = mlr_predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=avg_speed_kmh
            )
            mlr_emission_kg = mlr_emission_g / 1000.0
            
            print(f"   Formula: Emisi = β₀ + β₁(Jarak) + β₂(Fuel) + β₃(Vehicle)")
            print(f"                    + β₄(Konsumsi) + β₅(Kecepatan)")
            print(f"   Fitur yang digunakan:")
            print(f"     - Jarak: {distance_km:.2f} km")
            print(f"     - Fuel Type: {fuel_type}")
            print(f"     - Vehicle Type: {vehicle_type}")
            print(f"     - Konsumsi BB: {fuel_consumption_kml:.1f} km/L")
            print(f"     - Kecepatan: {avg_speed_kmh:.1f} km/h")
            print(f"   Hasil: {mlr_emission_g:,.0f} g = {mlr_emission_kg:.2f} kg CO₂")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            mlr_emission_g = None
            mlr_emission_kg = None
        
        # COMPARISON
        if static_emission_g is not None and mlr_emission_g is not None:
            print(f"\n📊 PERBANDINGAN:")
            print_subseparator()
            
            difference_g = mlr_emission_g - static_emission_g
            difference_pct = (difference_g / static_emission_g) * 100
            
            print(f"   Static : {static_emission_kg:.2f} kg CO₂")
            print(f"   MLR    : {mlr_emission_kg:.2f} kg CO₂")
            print(f"   Selisih: {difference_g:+,.0f} g ({difference_pct:+.1f}%)")
            
            if abs(difference_pct) < 5:
                print(f"   Status : ✅ Hasil hampir sama (perbedaan < 5%)")
            elif difference_g < 0:
                print(f"   Status : 📉 MLR lebih rendah (kondisi optimal)")
            else:
                print(f"   Status : 📈 MLR lebih tinggi (kondisi tidak optimal)")
            
            # Explanation
            print(f"\n💡 PENJELASAN:")
            if avg_speed_kmh < 40:
                print(f"   - Kecepatan rendah ({avg_speed_kmh:.1f} km/h) → kemungkinan macet")
                print(f"   - MLR memprediksi emisi lebih tinggi karena stop-and-go")
            elif avg_speed_kmh > 90:
                print(f"   - Kecepatan tinggi ({avg_speed_kmh:.1f} km/h) → hambatan udara tinggi")
                print(f"   - MLR memprediksi emisi lebih tinggi karena resistensi udara")
            else:
                print(f"   - Kecepatan optimal ({avg_speed_kmh:.1f} km/h) → efisiensi baik")
                print(f"   - MLR memprediksi emisi mendekati perhitungan statis")

def demo_speed_impact():
    """
    Demo khusus: Dampak kecepatan terhadap emisi
    """
    print("\n\n")
    print_separator()
    print("DEMO KHUSUS: Dampak Kecepatan terhadap Emisi")
    print("Jarak yang sama (50 km) dengan kecepatan berbeda")
    print_separator()
    
    try:
        mlr_predictor = MLREmissionPredictor()
        feature_extractor = FeatureExtractor()
    except Exception as e:
        print(f"\n❌ Error loading MLR model: {e}")
        return
    
    distance_km = 50.0
    vehicle_type = "SUV"
    fuel_type = "Bensin"
    fuel_consumption_kml = feature_extractor.get_fuel_consumption(vehicle_type, fuel_type)
    
    # Static calculation
    emission_factor = get_emission_factor(vehicle_type, fuel_type.lower())
    static_emission = distance_km * emission_factor
    
    print(f"\n📊 Perhitungan Static (baseline):")
    print(f"   {distance_km} km × {emission_factor} g/km = {static_emission:,.0f} g CO₂")
    
    print(f"\n🚗 Skenario dengan kecepatan berbeda:")
    print_subseparator()
    
    speeds = [
        (20, "Macet parah (dalam kota)"),
        (40, "Macet ringan"),
        (60, "Lancar (optimal)"),
        (80, "Jalan tol (optimal)"),
        (100, "Jalan tol cepat"),
        (120, "Sangat cepat (boros)")
    ]
    
    for speed, description in speeds:
        try:
            mlr_emission = mlr_predictor.predict_emission(
                distance_km=distance_km,
                fuel_type=fuel_type,
                vehicle_type=vehicle_type,
                fuel_consumption_kml=fuel_consumption_kml,
                avg_speed_kmh=speed
            )
            
            difference = mlr_emission - static_emission
            difference_pct = (difference / static_emission) * 100
            
            print(f"\n   Kecepatan: {speed} km/h - {description}")
            print(f"   MLR Prediction: {mlr_emission:,.0f} g CO₂")
            print(f"   vs Static: {difference:+,.0f} g ({difference_pct:+.1f}%)")
            
        except Exception as e:
            print(f"\n   Kecepatan: {speed} km/h - Error: {e}")

if __name__ == "__main__":
    # Run main comparison demo
    demo_comparison()
    
    # Run speed impact demo
    demo_speed_impact()
    
    print("\n\n")
    print_separator()
    print("✅ Demo selesai!")
    print_separator()
    print("\nKESIMPULAN:")
    print("- Static calculation: Sederhana, cepat, reliable")
    print("- MLR prediction: Lebih detail, mempertimbangkan kecepatan & konsumsi")
    print("- MLR berguna untuk: analisis mendalam, optimasi rute, rekomendasi")
    print_separator()
