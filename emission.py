# Emission Calculator
# This module performs emission calculations using predefined factors

# Emission factors in grams of CO2 per kilometer
EMISSION_FACTORS = {
    "LCGC": {
        "bensin": 120,
        "solar": 140
    },
    "SUV": {
        "bensin": 180,
        "solar": 200
    },
    "EV": {
        "listrik": 40
    }
}

def get_emission_factor(car_type: str, fuel_type: str) -> float:
    """
    Get emission factor for given vehicle-fuel combination.
    
    Args:
        car_type: Vehicle type (LCGC, SUV, EV)
        fuel_type: Fuel type (bensin, solar, listrik)
        
    Returns:
        Emission factor in grams CO2 per kilometer
        
    Raises:
        KeyError: If combination not found
    """
    if car_type not in EMISSION_FACTORS:
        raise KeyError(f"Invalid vehicle type: {car_type}")
    if fuel_type not in EMISSION_FACTORS[car_type]:
        raise KeyError(f"Invalid fuel type '{fuel_type}' for vehicle type '{car_type}'")
    return EMISSION_FACTORS[car_type][fuel_type]

def calculate_emission(distance_km: float, car_type: str, fuel_type: str) -> float:
    """
    Calculate carbon emissions based on distance and vehicle characteristics.
    
    Args:
        distance_km: Distance in kilometers
        car_type: Vehicle type (LCGC, SUV, EV)
        fuel_type: Fuel type (bensin, solar, listrik)
        
    Returns:
        Emission in grams of CO2
    """
    emission_factor = get_emission_factor(car_type, fuel_type)
    return distance_km * emission_factor

def get_valid_combinations() -> list:
    """
    Get list of valid vehicle-fuel combinations for error messages.
    
    Returns:
        List of valid combinations
    """
    combinations = []
    for car_type, fuels in EMISSION_FACTORS.items():
        for fuel_type in fuels.keys():
            combinations.append(f"{car_type}-{fuel_type}")
    return combinations
