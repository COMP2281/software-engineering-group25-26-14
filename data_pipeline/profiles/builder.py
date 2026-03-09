from typing import Any
import pandas as pd
import logging
from dataclasses import dataclass

from data_pipeline.profiles.models import VehicleProfile
from data_pipeline.profiles.resolver import VehicleSpecResolver
from data_pipeline.profiles.exceptions import CalibrationDataError

logger = logging.getLogger(__name__)

class VehicleProfileBuilder:
    """
    Builds a `VehicleProfile` (a digital twin of the vehicle) from a processed dataset.
    This calibrates the vehicle's engine base characteristics by integrating external 
    APIs for mechanical maximums and telematics datasets for behavioural characteristics.
    """

    def __init__(self, api_timeout: int = 5):
        """
        Initializes the VehicleProfileBuilder.
        """
        self.resolver = VehicleSpecResolver(api_timeout=api_timeout)

    def build_from_dataset(
        self, processed_dataset: Any, passenger_count: int = 1, cargo_weight_kg: float = 0.0
    ) -> VehicleProfile:
        """
        Builds a full digital twin from a dataset processed by PreprocessingPipeline.

        Args:
            processed_dataset: ProcessedDataset object containing `vehicle` and `trips`.
            passenger_count (int): Dynamic passenger count (assumed 75kg each).
            cargo_weight_kg (float): Independent dynamic load cargo weight in kg.

        Returns:
            VehicleProfile: Built and calibrated digital twin data.

        Raises:
            CalibrationDataError: If the dataset has no valid trips or missing metrics.
        """
        if not processed_dataset.trips:
            raise CalibrationDataError("ProcessedDataset has no trips. Cannot calibrate vehicle profile.")

        make = processed_dataset.vehicle.make or "Unknown"
        model = processed_dataset.vehicle.model or "Unknown"
        vehicle_id = processed_dataset.vehicle.vehicle_id

        # External API resolution
        specs = self.resolver.resolve_specs(make, model)

        # Dynamic Payload
        passenger_weight = passenger_count * 75.0
        dynamic_payload_kg = passenger_weight + cargo_weight_kg

        # Telematics Calibration (Behavior/Idle Extraction)
        # Concatenate all trip dataframes sequentially to map standard operating behavior
        all_trips_df = pd.concat([trip.dataframe for trip in processed_dataset.trips], ignore_index=True)

        if all_trips_df.empty:
            raise CalibrationDataError("ProcessedDataset trips contain no valid rows.")
            
        required_columns = {"RPM", "Speed"}
        if not required_columns.issubset(all_trips_df.columns):
            raise CalibrationDataError(f"Missing required columns in dataset. Found: {list(all_trips_df.columns)}")

        # Driver behaviour: typical max RPM (99th percentile across all trips regardless of speed)
        # Avoids noise/spike data at the absolute highest end.
        typical_max_rpm = all_trips_df["RPM"].quantile(0.99)
        
        if pd.isna(typical_max_rpm):
            raise CalibrationDataError("RPM column contains invalid/NaN values preventing typical max RPM calculation.")

        # Idle RPM: Average RPM when Speed == 0
        idle_mask = all_trips_df["Speed"] == 0
        idle_rpm_series = all_trips_df.loc[idle_mask, "RPM"]
        
        if idle_rpm_series.empty or idle_rpm_series.isna().all():
            logger.warning(f"No idle data found for vehicle {vehicle_id} (Speed=0 not met). Using default 800 RPM.")
            idle_rpm_baseline = 800.0
        else:
            idle_rpm_baseline = idle_rpm_series.mean()

        # Build Profile Object
        profile = VehicleProfile(
            vehicle_id=vehicle_id,
            make=make,
            model=model,
            
            fuel_type=specs.fuel_type,
            stoichiometric_afr=specs.stoichiometric_afr,
            engine_displacement_l=specs.engine_displacement_l,
            
            base_weight_kg=specs.base_weight_kg,
            dynamic_payload_kg=dynamic_payload_kg,
            
            idle_rpm_baseline=float(idle_rpm_baseline),
            typical_max_rpm=float(typical_max_rpm),
            mechanical_max_rpm=specs.mechanical_max_rpm
        )

        logger.info(f"Built Digital Twin Profile for {vehicle_id}: "
                    f"Idle {profile.idle_rpm_baseline:.0f} RPM, "
                    f"Max operating {profile.typical_max_rpm:.0f} RPM.")
                    
        return profile


if __name__ == "__main__":
    # Mocking PreprocessingPipeline output to demonstrate the module
    from dataclasses import dataclass
    
    @dataclass
    class MockVehicleInfo:
        make: str
        model: str
        vehicle_id: str
        source_filename: str

    @dataclass
    class MockProcessedTrip:
        dataframe: pd.DataFrame
        
    @dataclass
    class MockProcessedDataset:
        vehicle: MockVehicleInfo
        trips: list

    vehicle_info = MockVehicleInfo("Seat", "Leon", "seat_01", "2017-07-05_Seat_Leon_RT_S_Stau.csv")
    
    # Mock some basic telematics trip DataFrame
    trip_data = pd.DataFrame({
        "RPM": [800, 1500, 3000, 3500, 3200, 800, 4000],
        "Speed": [0, 20, 50, 70, 60, 0, 80],
        "MAF": [2.5, 5.0, 12.0, 15.0, 13.0, 2.5, 20.0],
        "Throttle": [5, 20, 40, 50, 45, 5, 80]
    })
    
    dataset = MockProcessedDataset(
        vehicle=vehicle_info, 
        trips=[MockProcessedTrip(dataframe=trip_data)]
    )

    builder = VehicleProfileBuilder(api_timeout=2)
    profile = builder.build_from_dataset(dataset, passenger_count=2, cargo_weight_kg=50.0)

    print("Vehicle Profile Digital Twin:")
    print("-" * 30)
    print(f"Vehicle: {profile.make} {profile.model} (ID: {profile.vehicle_id})")
    print(f"Fuel: {profile.fuel_type} (AFR: {profile.stoichiometric_afr})")
    print(f"Engine: {profile.engine_displacement_l}L")
    print(f"Base Weight: {profile.base_weight_kg}kg, Total Operating Weight: {profile.total_weight_kg}kg")
    print(f"Idle RPM: {profile.idle_rpm_baseline:.0f}")
    print(f"Typical Max RPM (Driver Behaviour): {profile.typical_max_rpm:.0f}")
    print(f"Mechanical Max RPM (API Specs): {profile.mechanical_max_rpm}")
