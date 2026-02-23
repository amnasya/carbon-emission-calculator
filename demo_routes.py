"""
Demo untuk fitur perbandingan rute alternatif
"""

import subprocess
import sys

def run_with_input(inputs, title):
    """Jalankan main.py dengan input yang sudah ditentukan"""
    input_str = '\n'.join(inputs) + '\n'
    
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)
    
    try:
        result = subprocess.run(
            [sys.executable, 'main.py'],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=45
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("Error: Program timeout")
    except Exception as e:
        print(f"Error: {e}")

print("="*80)
print("DEMO: PERBANDINGAN RUTE ALTERNATIF - CARBON EMISSION CALCULATOR")
print("="*80)
print("\nDemo ini akan menunjukkan:")
print("- Beberapa rute alternatif dari origin ke destination")
print("- Perhitungan emisi untuk setiap rute")
print("- Rekomendasi rute dengan emisi terendah")
print("- Petunjuk arah turn-by-turn untuk setiap rute")

# Demo 1: Jakarta to Bandung
run_with_input(
    [
        "Jakarta, Indonesia",
        "Bandung, Indonesia",
        "SUV",
        "bensin"
    ],
    "DEMO 1: Jakarta → Bandung (SUV bensin)"
)

# Demo 2: Surabaya to Malang
run_with_input(
    [
        "Surabaya, Indonesia",
        "Malang, Indonesia",
        "LCGC",
        "bensin"
    ],
    "DEMO 2: Surabaya → Malang (LCGC bensin)"
)

# Demo 3: Short trip with EV
run_with_input(
    [
        "Yogyakarta, Indonesia",
        "Solo, Indonesia",
        "EV",
        "listrik"
    ],
    "DEMO 3: Yogyakarta → Solo (EV listrik)"
)

print("\n" + "="*80)
print("DEMO SELESAI!")
print("="*80)
print("\n>> Tips:")
print("   - Rute dengan jarak lebih pendek = emisi lebih rendah")
print("   - Pilih kendaraan EV untuk emisi paling rendah")
print("   - Gunakan LCGC untuk efisiensi yang baik dengan bensin")
print("="*80)
