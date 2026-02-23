# Visualization Module
# This module creates charts to visualize emission comparisons

import matplotlib.pyplot as plt
import matplotlib
import os

# Set backend untuk Windows
matplotlib.use('Agg')  # Non-interactive backend

def create_emission_chart(routes, car_type, fuel_type, emission_factor, output_file='emission_chart.png'):
    """
    Create a line chart showing cumulative emissions per 25km for each route.
    
    Args:
        routes: List of route dictionaries with distance_km
        car_type: Vehicle type
        fuel_type: Fuel type
        emission_factor: Emission factor in g CO2/km
        output_file: Output filename for the chart
    """
    plt.figure(figsize=(12, 7))
    
    # Prepare data for each route
    for idx, route in enumerate(routes):
        distance_km = route['distance_km']
        route_num = route['route_number']
        
        # Create distance points every 25 km
        distance_points = []
        emission_points = []
        
        current_distance = 0
        interval = 25  # km
        
        while current_distance <= distance_km:
            distance_points.append(current_distance)
            emission_points.append(current_distance * emission_factor / 1000.0)  # Convert to kg
            current_distance += interval
        
        # Add final point if not already there
        if distance_points[-1] < distance_km:
            distance_points.append(distance_km)
            emission_points.append(distance_km * emission_factor / 1000.0)
        
        # Plot line for this route
        label = f'Rute {route_num} ({distance_km:.1f} km)'
        plt.plot(distance_points, emission_points, marker='o', linewidth=2, label=label, markersize=6)
    
    # Customize chart
    plt.xlabel('Jarak (km)', fontsize=12, fontweight='bold')
    plt.ylabel('Emisi Karbon Kumulatif (kg CO2)', fontsize=12, fontweight='bold')
    plt.title(f'Perbandingan Emisi Karbon per 25 km\n{car_type} - {fuel_type} ({emission_factor} g CO2/km)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Add interval markers on x-axis
    max_distance = max(route['distance_km'] for route in routes)
    x_ticks = list(range(0, int(max_distance) + 26, 25))
    plt.xticks(x_ticks)
    
    # Tight layout
    plt.tight_layout()
    
    # Save chart
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file


def create_comparison_bar_chart(routes, emission_factor, output_file='comparison_chart.png'):
    """
    Create a bar chart comparing total emissions and distances for each route.
    
    Args:
        routes: List of route dictionaries
        emission_factor: Emission factor in g CO2/km
        output_file: Output filename for the chart
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Prepare data
    route_numbers = [f"Rute {r['route_number']}" for r in routes]
    distances = [r['distance_km'] for r in routes]
    emissions = [r['distance_km'] * emission_factor / 1000.0 for r in routes]  # kg CO2
    
    # Find best route (lowest emission)
    best_idx = emissions.index(min(emissions))
    colors = ['#2ecc71' if i == best_idx else '#3498db' for i in range(len(routes))]
    
    # Chart 1: Distance comparison
    bars1 = ax1.bar(route_numbers, distances, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Jarak (km)', fontsize=11, fontweight='bold')
    ax1.set_title('Perbandingan Jarak', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f} km',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Chart 2: Emission comparison
    bars2 = ax2.bar(route_numbers, emissions, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Emisi Karbon (kg CO2)', fontsize=11, fontweight='bold')
    ax2.set_title('Perbandingan Emisi Karbon', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f} kg',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', edgecolor='black', label='Rekomendasi (Terendah)'),
        Patch(facecolor='#3498db', edgecolor='black', label='Rute Alternatif')
    ]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.98), 
               ncol=2, fontsize=10, frameon=True)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save chart
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file


def display_chart_info(chart_files):
    """
    Display information about generated charts.
    
    Args:
        chart_files: List of chart filenames
    """
    print("\n" + "="*70)
    print("GRAFIK VISUALISASI")
    print("="*70)
    print("\nGrafik telah dibuat dan disimpan:")
    
    for chart_file in chart_files:
        if os.path.exists(chart_file):
            file_size = os.path.getsize(chart_file) / 1024  # KB
            print(f"  - {chart_file} ({file_size:.1f} KB)")
    
    print("\nAnda dapat membuka file grafik untuk melihat visualisasi perbandingan.")
    print("="*70)
