import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Local Imports
from data_pipeline.profiles.models import VehicleProfile, VehicleSpecs
from data_pipeline.profiles.builder import VehicleProfileBuilder
from data_pipeline.ingestion.preprocessing import ProcessedDataset, ProcessedTrip, VehicleInfo, ValidationReport
from analytics_engine.fuel_estimation.estimator import FuelEstimator

class TestFuelEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = FuelEstimator()
        self.profile = VehicleProfile(
            vehicle_id="ABC1", make="Seat", model="Leon", fuel_type="Diesel",
            stoichiometric_afr=14.5, engine_displacement_l=1.6, base_weight_kg=1300.0,
            dynamic_payload_kg=150.0, idle_rpm_baseline=800.0, typical_max_rpm=6200.0,
            mechanical_max_rpm=7000
        )
        
        times = [datetime.now() + timedelta(seconds=i) for i in range(5)]
        self.valid_df = pd.DataFrame({
            'RPM': [800, 1500, 2000, 2500, 2000],
            'MAF': [5.0, 15.0, 25.0, 35.0, 20.0],
            'Speed': [0, 30, 60, 90, 60],
            'Timestamp': times
        })
        self.valid_trip = ProcessedTrip(metadata=MagicMock(), dataframe=self.valid_df)

    def test_fuel_consumption_valid(self):
        """Maps to unit_test-04: Application calculates exact fuel estimates from valid interval telemetry"""
        result = self.estimator.calculate_trip_fuel_consumption(self.profile, self.valid_trip)
        self.assertFalse(pd.isna(result))
        self.assertGreater(result, 0)
        
    def test_fuel_consumption_zero_distance(self):
        """Maps to unit_test-05: Application gracefully handles trip segments exhibiting zero total distance"""
        zero_df = self.valid_df.copy()
        zero_df['Speed'] = 0 
        zero_trip = ProcessedTrip(metadata=MagicMock(), dataframe=zero_df)
        result = self.estimator.calculate_trip_fuel_consumption(self.profile, zero_trip)
        self.assertTrue(pd.isna(result))

    def test_fuel_consumption_missing_columns(self):
        """Maps to unit_test-06: System rejects calculations if core physics metrics are missing"""
        invalid_df = self.valid_df.drop(columns=['MAF'])
        invalid_trip = ProcessedTrip(metadata=MagicMock(), dataframe=invalid_df)
        result = self.estimator.calculate_trip_fuel_consumption(self.profile, invalid_trip)
        self.assertTrue(pd.isna(result))

class TestVehicleProfileBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = VehicleProfileBuilder(api_timeout=1)
        self.mock_specs = VehicleSpecs(
            fuel_type="Petrol", engine_displacement_l=2.0, base_weight_kg=1400.0,
            mechanical_max_rpm=7000, stoichiometric_afr=14.7
        )
        
        self.vehicle_info = VehicleInfo(make="Seat", model="Leon", vehicle_id="ABC1", source_filename="test.csv")
        self.valid_df = pd.DataFrame({'RPM': [800, 1500, 2000], 'Speed': [0, 30, 60]})
        self.valid_trip = ProcessedTrip(metadata=MagicMock(), dataframe=self.valid_df)
        
        # Proper setup of ValidationReport avoiding TypeError
        val_report = ValidationReport(
            filename="test.csv",
            source_path=None,
            status="valid",
            processed_at="2026-03-12T00:00:00",
            row_count=3,
            checksum="fake_checksum",
        )
        self.dataset = ProcessedDataset(validation=val_report, vehicle=self.vehicle_info, trips=[self.valid_trip])

    @patch('data_pipeline.profiles.resolver.VehicleSpecResolver.resolve_specs')
    def test_build_from_dataset_valid(self, mock_resolve):
        """Maps to unit_test-01: Application successfully builds a calibrated VehicleProfile from valid data"""
        mock_resolve.return_value = self.mock_specs
        profile = self.builder.build_from_dataset(self.dataset, passenger_count=2, cargo_weight_kg=50.0)
        self.assertEqual(profile.dynamic_payload_kg, 200.0) # 2 * 75kg + 50kg
        self.assertEqual(profile.total_weight_kg, 1600.0) # 1400kg base + 200kg dynamic
        
    def test_build_empty_dataset(self):
        """Maps to unit_test-02: Application accurately rejects an empty dataset during calibration"""
        val_report = ValidationReport(
            filename="test.csv", source_path=None, status="valid", 
            processed_at="2026-03-12", row_count=0, checksum="abc"
        )
        empty_dataset = ProcessedDataset(validation=val_report, vehicle=self.vehicle_info, trips=[])
        with self.assertRaises(ValueError):
            self.builder.build_from_dataset(empty_dataset)
            
    def test_build_missing_columns(self):
        """Maps to unit_test-03: Application intercepts telemetry dataframes missing critical analytical variables"""
        invalid_df = self.valid_df.drop(columns=['RPM'])
        invalid_trip = ProcessedTrip(metadata=MagicMock(), dataframe=invalid_df)
        val_report = ValidationReport(
            filename="test.csv", source_path=None, status="valid", 
            processed_at="2026-03-12", row_count=3, checksum="abc"
        )
        invalid_dataset = ProcessedDataset(validation=val_report, vehicle=self.vehicle_info, trips=[invalid_trip])
        with self.assertRaises(ValueError):
            self.builder.build_from_dataset(invalid_dataset)

if __name__ == '__main__':
    unittest.main()
