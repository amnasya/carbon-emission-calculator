"""
Demo runner untuk Carbon Emission Calculator
Menjalankan aplikasi dengan input yang sudah ditentukan
"""

import subprocess
import sys

def run_with_input(inputs):
    """Jalankan main.py dengan input yang sudah ditentukan"""
    input_str = '\n'.join(inputs) + '\n'
    
    try:
        result = subprocess.run(
            [sys.executable, 'main.py'],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("Error: Program timeout")
    except Exception as e:
        print(f"Error: {e}")

print("="*70)
print("DEMO 1: Jakarta ke Bandung dengan SUV bensin")
print("="*70)
run_with_input([
    "Jakarta, Indonesia",
    "Bandung, Indonesia",
    "SUV",
    "bensin"
])

print("\n" + "="*70)
print("DEMO 2: Surabaya ke Malang dengan LCGC bensin")
print("="*70)
run_with_input([
    "Surabaya, Indonesia",
    "Malang, Indonesia",
    "LCGC",
    "bensin"
])

print("\n" + "="*70)
print("DEMO 3: Yogyakarta ke Solo dengan EV listrik")
print("="*70)
run_with_input([
    "Yogyakarta, Indonesia",
    "Solo, Indonesia",
    "EV",
    "listrik"
])
