import pandas as pd
import numpy as np
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Constants for Fuel Density (grams per Liter)
FUEL_DENSITY_G_PER_L = {
    "Petrol": 745.0,
    "Diesel": 832.0,
    "Electric": 0.0, # Cannot compute L/100km for electric without kWh mapping
}
DEFAULT_DENSITY = 745.0 # Fallback to petrol density if unknown

class FuelEstimator:
    """
    Estimates highly accurate fuel consumption in L/100km from telematics data 
    and a calibrated VehicleProfile Digital Twin.
    """
    
    @staticmethod
    def calculate_trip_fuel_consumption(profile: Any, trip: Any) -> float:
        """
        Calculates the fuel consumption (L/100km) for a single ProcessedTrip.
        
        Args:
            profile (VehicleProfile): The digital twin profile containing AFR and fuel type.
            trip (ProcessedTrip): The trip object containing the pandas dataframe.
            
        Returns:
            float: The estimated fuel efficiency in L/100km. Returns NaN if missing critical data 
                   or if total distance is 0.
        """
        df = trip.dataframe
        
        # Require minimum columns
        required_cols = {"MAF", "Speed", "Timestamp"}
        if not required_cols.issubset(df.columns):
            logger.error(f"Missing required columns for fuel estimation. Need {required_cols}. Found: {list(df.columns)}")
            return np.nan
        
        # Ensure Timestamp is a datetime type for accurate delta calculation
        if not pd.api.types.is_datetime64_any_dtype(df['Timestamp']):
            df = df.copy()
            try:
                # Handle potential timestamp formats
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="mixed")
            except Exception as e:
                logger.error(f"Timestamp conversion failed: {e}")
                return np.nan

        # Calculate time delta in seconds between sequential rows
        time_delta_s = df['Timestamp'].diff().dt.total_seconds().fillna(0)
        
        # Clean up anomalous time jumps (e.g. >10 min gaps within a single segments, clip to 1s as naive fallback)
        time_delta_s = np.where((time_delta_s < 0) | (time_delta_s > 600), 1.0, time_delta_s)

        # 1. Total Distance (km)
        # Speed is in km/h -> km/s conversion
        distance_inter_km = (df['Speed'] / 3600.0) * time_delta_s
        total_distance_km = distance_inter_km.sum()
        
        if total_distance_km <= 0:
            logger.warning("Trip has 0 total distance. Cannot calculate L/100km efficiency.")
            return np.nan

        # 2. Fuel Mass (grams) = [MAF (g/s) / stoichiometric_afr] * time_delta (s)
        afr = getattr(profile, 'stoichiometric_afr', 14.7)
        if not afr or pd.isna(afr) or afr <= 0:
            afr = 14.7  # Safe fallback if AFR is broken in profile

        fuel_mass_grams = (df['MAF'] / afr) * time_delta_s
        total_fuel_mass_g = fuel_mass_grams.sum()

        # 3. Fuel Volume (Liters)
        fuel_type = getattr(profile, 'fuel_type', 'Petrol')
        density_g_l = FUEL_DENSITY_G_PER_L.get(fuel_type, DEFAULT_DENSITY)
        
        if density_g_l <= 0:
            logger.error(f"Unsupported or zero-density fuel type for L/100km estimation: {fuel_type}")
            return np.nan

        total_fuel_liters = total_fuel_mass_g / density_g_l

        # 4. Fuel Efficiency (L/100km)
        efficiency_l_100km = (total_fuel_liters / total_distance_km) * 100.0
        
        return float(efficiency_l_100km)

if __name__ == "__main__":
    # Internal Debugging and Testing Block
    from dataclasses import dataclass
    from datetime import datetime, timedelta

    @dataclass
    class MockProfile:
        fuel_type: str = "Diesel"
        stoichiometric_afr: float = 14.5

    @dataclass
    class MockTrip:
        dataframe: pd.DataFrame

    print("--- Running FuelEstimator Test ---")
    
    # Mock Data (1 second intervals simulating a short burst of speed)
    start_time = datetime.now()
    times = [start_time + timedelta(seconds=i) for i in range(10)]
    speeds = [0, 10, 30, 50, 50, 50, 50, 30, 10, 0] # km/h
    mafs = [2.5, 8.0, 15.0, 30.0, 25.0, 25.0, 25.0, 15.0, 8.0, 2.5] # grams/second
    
    mock_df = pd.DataFrame({
        "Timestamp": times,
        "Speed": speeds,
        "MAF": mafs
    })
    
    trip = MockTrip(dataframe=mock_df)
    profile = MockProfile()
    
    estimator = FuelEstimator()
    liters_per_100km = estimator.calculate_trip_fuel_consumption(profile, trip)
    
    print(f"Vehicle Setup | Fuel: {profile.fuel_type}, AFR: {profile.stoichiometric_afr}")
    print(f"Trip Snapshot | Start: {times[0].time()}, Duration: {len(times)} records")
    print(f"Result        | Estimated Fuel Consumption: {liters_per_100km:.2f} L/100km")
