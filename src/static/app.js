// Carbon Emission Calculator - Frontend JavaScript

let map;
let originMarker = null;
let destMarker = null;
let originCoords = null;
let destCoords = null;
let emissionChart = null;
let comparisonChart = null;
let routeLines = [];  // Store route polylines

// Vehicle fuel mapping
const vehicleFuels = {
    'LCGC': ['bensin', 'solar'],
    'SUV': ['bensin', 'solar'],
    'EV': ['listrik']
};

// Initialize map
function initMap() {
    // Center on Indonesia
    map = L.map('map').setView([-6.2088, 106.8456], 10);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Add click event
    map.on('click', onMapClick);
}

// Handle map click
function onMapClick(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    if (!originCoords) {
        // Set origin
        originCoords = { lat, lng };
        
        // Add green marker
        originMarker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            })
        }).addTo(map);
        
        originMarker.bindPopup('📍 Lokasi Awal').openPopup();
        
        // Update display
        document.getElementById('originText').textContent = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
        document.getElementById('originDisplay').classList.add('selected');
        
    } else if (!destCoords) {
        // Set destination
        destCoords = { lat, lng };
        
        // Add red marker
        destMarker = L.marker([lat, lng], {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            })
        }).addTo(map);
        
        destMarker.bindPopup('🎯 Lokasi Tujuan').openPopup();
        
        // Update display
        document.getElementById('destText').textContent = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
        document.getElementById('destDisplay').classList.add('selected');
        
        // Enable calculate button if vehicle selected
        checkCalculateButton();
    }
}

// Reset locations
function resetLocations() {
    // Remove markers
    if (originMarker) {
        map.removeLayer(originMarker);
        originMarker = null;
    }
    if (destMarker) {
        map.removeLayer(destMarker);
        destMarker = null;
    }
    
    // Remove route lines
    routeLines.forEach(line => map.removeLayer(line));
    routeLines = [];
    
    // Hide legend
    document.getElementById('mapLegend').style.display = 'none';
    
    // Reset coordinates
    originCoords = null;
    destCoords = null;
    
    // Reset displays
    document.getElementById('originText').textContent = 'Klik pada peta untuk memilih lokasi awal';
    document.getElementById('destText').textContent = 'Klik pada peta untuk memilih lokasi tujuan';
    document.getElementById('originDisplay').classList.remove('selected');
    document.getElementById('destDisplay').classList.remove('selected');
    
    // Hide results
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('chartsSection').style.display = 'none';
    document.getElementById('advisorSection').style.display = 'none';
    
    // Disable calculate button
    document.getElementById('calculateBtn').disabled = true;
}

// Update fuel options based on vehicle type
function updateFuelOptions() {
    const carType = document.getElementById('carType').value;
    const fuelSelect = document.getElementById('fuelType');
    
    // Clear options
    fuelSelect.innerHTML = '<option value="">-- Pilih Bahan Bakar --</option>';
    
    if (carType && vehicleFuels[carType]) {
        vehicleFuels[carType].forEach(fuel => {
            const option = document.createElement('option');
            option.value = fuel;
            option.textContent = fuel.charAt(0).toUpperCase() + fuel.slice(1);
            fuelSelect.appendChild(option);
        });
    }
    
    checkCalculateButton();
}

// Check if calculate button should be enabled
function checkCalculateButton() {
    const carType = document.getElementById('carType').value;
    const fuelType = document.getElementById('fuelType').value;
    const btn = document.getElementById('calculateBtn');
    
    btn.disabled = !(originCoords && destCoords && carType && fuelType);
}

// Calculate emissions
async function calculateEmissions() {
    const carType = document.getElementById('carType').value;
    const fuelType = document.getElementById('fuelType').value;
    
    if (!originCoords || !destCoords || !carType || !fuelType) {
        alert('Mohon lengkapi semua data!');
        return;
    }
    
    // Show loading
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    resultsSection.innerHTML = '<div class="loading">⏳ Menghitung rute dan emisi...</div>';
    
    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origin_lat: originCoords.lat,
                origin_lng: originCoords.lng,
                dest_lat: destCoords.lat,
                dest_lng: destCoords.lng,
                car_type: carType,
                fuel_type: fuelType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            displayRoutesOnMap(data);
            displayAdvisor(data);
            createCharts(data);
            
            // Smooth scroll to results
            setTimeout(() => {
                document.getElementById('resultsSection').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }, 300);
        } else {
            resultsSection.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
        }
    } catch (error) {
        resultsSection.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
    }
}

// Display routes on map
function displayRoutesOnMap(data) {
    // Remove existing route lines
    routeLines.forEach(line => map.removeLayer(line));
    routeLines = [];
    
    // Add route lines to map
    data.routes.forEach((route, index) => {
        if (route.geometry && route.geometry.length > 0) {
            // Convert coordinates from [lng, lat] to [lat, lng] for Leaflet
            const latlngs = route.geometry.map(coord => [coord[1], coord[0]]);
            
            // Determine color and style
            const isBest = index === 0;
            const color = isBest ? '#4CAF50' : (index === 1 ? '#2196F3' : '#FF9800');
            const weight = isBest ? 5 : 4;
            const opacity = isBest ? 0.8 : 0.6;
            
            // Create polyline
            const polyline = L.polyline(latlngs, {
                color: color,
                weight: weight,
                opacity: opacity,
                smoothFactor: 1
            }).addTo(map);
            
            // Add popup
            polyline.bindPopup(`
                <strong>Rute ${route.route_number}${isBest ? ' (REKOMENDASI)' : ''}</strong><br>
                Jarak: ${route.distance_km.toFixed(2)} km<br>
                Waktu: ${route.duration_min.toFixed(1)} menit<br>
                Emisi: ${route.emission_kg.toFixed(2)} kg CO2
            `);
            
            routeLines.push(polyline);
        }
    });
    
    // Fit map to show all routes
    if (routeLines.length > 0) {
        const group = L.featureGroup(routeLines);
        map.fitBounds(group.getBounds().pad(0.1));
        
        // Show legend
        document.getElementById('mapLegend').style.display = 'block';
    }
}

// Display results
function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    let html = '';
    
    data.routes.forEach((route, index) => {
        const isBest = index === 0;
        const cardClass = isBest ? 'best' : (index === 1 ? 'alt1' : 'alt2');
        const routeLabel = isBest ? '(REKOMENDASI - Emisi Terendah)' : (index === 1 ? '(Alternatif 1)' : '(Alternatif 2)');
        
        html += `
            <div class="route-card ${cardClass}">
                <div class="route-header">
                    <div class="route-title">
                        ${isBest ? '⭐ ' : ''}Rute ${route.route_number} ${routeLabel}
                    </div>
                    ${isBest ? '<span class="badge badge-success">Emisi Terendah</span>' : ''}
                </div>
                
                <div class="route-stats">
                    <div class="stat-box">
                        <div class="stat-label">Jarak</div>
                        <div class="stat-value">${route.distance_km.toFixed(2)} km</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Waktu Tempuh</div>
                        <div class="stat-value">${route.duration_min.toFixed(1)} menit</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Emisi Karbon</div>
                        <div class="stat-value">${route.emission_kg.toFixed(2)} kg CO2</div>
                    </div>
                </div>
                
                ${route.savings_g ? `
                    <div class="savings-box">
                        <h4>💰 Penghematan Emisi</h4>
                        <p>Menghemat ${route.savings_g.toFixed(0)} g CO2 (${route.savings_pct.toFixed(1)}% lebih rendah dari rute terburuk)</p>
                    </div>
                ` : ''}
                
                <div class="directions">
                    <h4>🗺️ Petunjuk Arah (${route.steps.length} langkah)</h4>
                    ${route.steps.slice(0, 10).map((step, i) => `
                        <div class="direction-step">
                            ${i + 1}. ${step.instruction} di <strong>${step.road}</strong> (${step.distance_km.toFixed(2)} km)
                        </div>
                    `).join('')}
                    ${route.steps.length > 10 ? `<p style="text-align: center; color: #666; margin-top: 10px;">... dan ${route.steps.length - 10} langkah lainnya</p>` : ''}
                </div>
            </div>
        `;
    });
    
    // Add navigation buttons
    html += `
        <div style="text-align: center; margin-top: 30px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
            <button onclick="document.getElementById('advisorSection').scrollIntoView({behavior: 'smooth'})" 
                    class="nav-btn nav-btn-advisor"
                    onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.3)'"
                    style="padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
                💡 Lihat Rekomendasi
            </button>
            <button onclick="document.getElementById('chartsSection').scrollIntoView({behavior: 'smooth'})" 
                    class="nav-btn nav-btn-charts"
                    onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(76, 175, 80, 0.4)'"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(76, 175, 80, 0.3)'"
                    style="padding: 12px 24px; background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%); color: white; border: none; border-radius: 8px; font-size: 1em; font-weight: 600; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);">
                📊 Lihat Grafik
            </button>
        </div>
    `;
    
    resultsSection.innerHTML = html;
}

// Display advisor recommendations
function displayAdvisor(data) {
    if (!data.advice) return;
    
    const advisorSection = document.getElementById('advisorSection');
    const advisorContent = document.getElementById('advisorContent');
    
    // Parse the advice text into structured sections
    const lines = data.advice.split('\n');
    let html = '';
    let inRecommendation = false;
    let recommendationContent = '';
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Skip separator lines
        if (line.match(/^={3,}$/)) {
            continue;
        }
        
        // Main section headers
        if (line.includes('RINGKASAN PERJALANAN')) {
            html += '<div class="advisor-summary"><h3>📊 RINGKASAN PERJALANAN</h3>';
        } else if (line.includes('REKOMENDASI PENGURANGAN EMISI')) {
            html += '</div><div class="advisor-recommendations"><h3>💡 REKOMENDASI PENGURANGAN EMISI</h3>';
        }
        // Recommendation items
        else if (line.match(/^Rekomendasi \d+:/)) {
            if (inRecommendation && recommendationContent) {
                html += `<div class="recommendation-item">${recommendationContent}</div>`;
                recommendationContent = '';
            }
            inRecommendation = true;
            const recNum = line.match(/\d+/)[0];
            recommendationContent = `<h4>🎯 Rekomendasi ${recNum}</h4>`;
        }
        // Savings line
        else if (line.includes('Penghematan:')) {
            const savingsMatch = line.match(/Penghematan:\s*(.+)/);
            if (savingsMatch) {
                const savings = savingsMatch[1]
                    .replace(/(\d+,?\d*)\s*g\s*CO2/g, '<span class="emission-value">$1 g CO2</span>')
                    .replace(/(\d+\.\d+)\s*kg/g, '<span class="emission-value">$1 kg</span>')
                    .replace(/(\d+\.\d+)%/g, '<span class="percentage">$1%</span>');
                recommendationContent += `<div class="savings-info">💰 <strong>Penghematan:</strong> ${savings}</div>`;
            }
        }
        // Total potential savings
        else if (line.includes('Total Potensi')) {
            if (inRecommendation && recommendationContent) {
                html += `<div class="recommendation-item">${recommendationContent}</div>`;
                recommendationContent = '';
                inRecommendation = false;
            }
            const totalMatch = line.match(/Total Potensi[^:]*:\s*(.+)/);
            if (totalMatch) {
                const total = totalMatch[1]
                    .replace(/(\d+,?\d*)\s*g\s*CO2/g, '<span class="emission-value">$1 g CO2</span>')
                    .replace(/(\d+\.\d+)\s*kg/g, '<span class="emission-value">$1 kg</span>');
                html += `<div class="total-savings">⭐ <strong>${line.split(':')[0]}:</strong> ${total}</div>`;
            }
        }
        // Summary info lines
        else if (line.includes('Jarak Tempuh') || line.includes('Jenis Kendaraan') || line.includes('Total Emisi')) {
            const parts = line.split(':');
            if (parts.length === 2) {
                const label = parts[0].trim();
                let value = parts[1].trim()
                    .replace(/(\d+\.\d+)\s*km/g, '<span class="value-highlight">$1 km</span>')
                    .replace(/(\d+,?\d*)\s*g\s*CO2/g, '<span class="emission-value">$1 g CO2</span>')
                    .replace(/(\d+\.\d+)\s*kg\s*CO2/g, '<span class="emission-value">$1 kg CO2</span>');
                html += `<div class="summary-item"><span class="label">${label}:</span> ${value}</div>`;
            }
        }
        // Regular content lines
        else if (line && !line.match(/^={3,}$/)) {
            if (inRecommendation) {
                const formatted = line
                    .replace(/(\d+,?\d*)\s*g\s*CO2/g, '<span class="emission-value">$1 g CO2</span>')
                    .replace(/(\d+\.\d+)\s*kg/g, '<span class="emission-value">$1 kg</span>')
                    .replace(/(\d+\.\d+)%/g, '<span class="percentage">$1%</span>');
                recommendationContent += `<p>${formatted}</p>`;
            }
        }
    }
    
    // Close any open recommendation
    if (inRecommendation && recommendationContent) {
        html += `<div class="recommendation-item">${recommendationContent}</div>`;
    }
    
    html += '</div>';
    
    advisorContent.innerHTML = html;
    advisorSection.style.display = 'block';
}

// Create charts
function createCharts(data) {
    document.getElementById('chartsSection').style.display = 'block';
    
    // Destroy existing charts
    if (emissionChart) emissionChart.destroy();
    if (comparisonChart) comparisonChart.destroy();
    
    // Emission chart (per 25km)
    const emissionCtx = document.getElementById('emissionChart').getContext('2d');
    const routeColors = ['#4CAF50', '#2196F3', '#FF9800'];  // Green, Blue, Orange
    const datasets = data.routes.map((route, index) => ({
        label: `Rute ${route.route_number} (${route.distance_km.toFixed(1)} km)`,
        data: route.emission_points,
        borderColor: routeColors[index] || '#999',
        backgroundColor: routeColors[index] ? routeColors[index] + '20' : 'rgba(153, 153, 153, 0.1)',
        borderWidth: 3,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 7
    }));
    
    emissionChart = new Chart(emissionCtx, {
        type: 'line',
        data: {
            labels: data.routes[0].distance_points.map(d => d.toFixed(0)),
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `Emisi Karbon Kumulatif - ${data.car_type} ${data.fuel_type} (${data.emission_factor} g CO2/km)`,
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Jarak (km)',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Emisi Karbon Kumulatif (kg CO2)',
                        font: { size: 14, weight: 'bold' }
                    },
                    beginAtZero: true
                }
            }
        }
    });
    
    // Comparison chart
    const comparisonCtx = document.getElementById('comparisonChart').getContext('2d');
    const labels = data.routes.map(r => `Rute ${r.route_number}`);
    const distances = data.routes.map(r => r.distance_km);
    const emissions = data.routes.map(r => r.emission_kg);
    const colors = data.routes.map((r, i) => {
        if (i === 0) return '#4CAF50';  // Green for best route
        if (i === 1) return '#2196F3';  // Blue for alternative 1
        return '#FF9800';  // Orange for alternative 2
    });
    
    comparisonChart = new Chart(comparisonCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Jarak (km)',
                    data: distances,
                    backgroundColor: colors.map(c => c + '80'),
                    borderColor: colors,
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Emisi (kg CO2)',
                    data: emissions,
                    backgroundColor: colors.map(c => c + '40'),
                    borderColor: colors,
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Perbandingan Jarak dan Emisi',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Jarak (km)',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Emisi (kg CO2)',
                        font: { size: 14, weight: 'bold' }
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    
    document.getElementById('carType').addEventListener('change', updateFuelOptions);
    document.getElementById('fuelType').addEventListener('change', checkCalculateButton);
    document.getElementById('calculateBtn').addEventListener('click', calculateEmissions);
    document.getElementById('resetBtn').addEventListener('click', resetLocations);
});
