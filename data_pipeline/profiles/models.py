from dataclasses import dataclass

@dataclass
class VehicleSpecs:
    """
    Represents physical specifications of a vehicle, typically fetched from an API.
    """
    fuel_type: str
    engine_displacement_l: float
    base_weight_kg: float
    mechanical_max_rpm: int
    stoichiometric_afr: float


@dataclass
class VehicleProfile:
    """
    Digital Twin representation of the vehicle containing base specifications
    and operational calibration data derived from telematics.
    """
    vehicle_id: str
    make: str
    model: str
    
    fuel_type: str
    stoichiometric_afr: float
    engine_displacement_l: float
    
    base_weight_kg: float
    dynamic_payload_kg: float
    
    idle_rpm_baseline: float
    typical_max_rpm: float
    mechanical_max_rpm: int

    @property
    def total_weight_kg(self) -> float:
        """
        Calculates the total operating weight of the vehicle combining 
        the base structural weight and the dynamic payload (passengers + cargo).
        """
        return self.base_weight_kg + self.dynamic_payload_kg
