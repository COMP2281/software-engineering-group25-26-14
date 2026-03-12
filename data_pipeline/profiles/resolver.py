import logging
import requests
from typing import Optional
from data_pipeline.profiles.models import VehicleSpecs

logger = logging.getLogger(__name__)

class VehicleSpecResolver:
    """
    Resolves physical specifications of a vehicle using the Cars API by API Ninjas via RapidAPI
    or falls back to sensible defaults.
    """

    def __init__(self, api_timeout: int = 5):
        """
        Args:
            api_timeout (int): Seconds to wait for API responses.
        """
        self.api_timeout = api_timeout
        self.api_url = "https://cars-by-api-ninjas.p.rapidapi.com/v1/cars" 
        # best I could find for free but missing key specs like mechanical redline and AFR, 
        # so we have to make an educated guess based on fuel type, this affects fuel consumption estimates
        self.api_headers = {
            'x-rapidapi-key': "392dc1cfb6msh9e58f0921f76287p1881f4jsn316644a32712",
            'x-rapidapi-host': "cars-by-api-ninjas.p.rapidapi.com"
        }

    def resolve_specs(self, make: str, model: str, year: int=None, model_extension: str=None) -> VehicleSpecs:
        """
        Attempts to resolve vehicle specs by hitting the external Cars API.

        Args:
            make (str): The manufacturer name.
            model (str): The model name.
            year (int, optional): The model year.
            model_extension (str, optional): Additional model details.

        Returns:
            VehicleSpecs: Physical specifications of the vehicle.
        """
        try:
            params = {
                "make": make,
                "model": model
            }
            if year:
                params["year"] = year

            response = requests.get(
                self.api_url, 
                headers=self.api_headers, 
                params=params, 
                timeout=self.api_timeout
            )
            
            # 1. Handle Rate Limits
            if response.status_code == 429:
                logger.error("Rate limit exceeded for API Ninjas Cars API.")
                raise ValueError("API rate limit exceeded.")
                
            response.raise_for_status()
            
            data = response.json()
            if not data or len(data) == 0:
                raise ValueError(f"No match found for {make} {model} in API.")

            # 2. Extract Data (Use the first match)
            car = data[0]
            
            raw_fuel_type = str(car.get("fuel_type")).lower()
            # redline and AFR are approximated based on fuel type, as the API doesn't provide these directly
            if "diesel" in raw_fuel_type:
                fuel_type = "Diesel"
                stoich_afr = 14.5
                mechan_rpm = 4500 
            elif "electricity" in raw_fuel_type or "electric" in raw_fuel_type:
                fuel_type = "Electric"
                stoich_afr = 0.0
                mechan_rpm = 12000
            else:
                fuel_type = "Petrol"
                stoich_afr = 14.7
                mechan_rpm = 6500

            # Displacement is in Liters in this API
            displacement = float(car.get("displacement", 2.0))
            
            # API doesn't return base vehicle weights, so we still fall back
            base_weight_kg = 1400.0

            logger.info(f"Resolved specs for {make} {model} via API: {displacement}L {fuel_type}")

            return VehicleSpecs(
                fuel_type=fuel_type,
                engine_displacement_l=displacement,
                base_weight_kg=base_weight_kg,
                mechanical_max_rpm=mechan_rpm,
                stoichiometric_afr=stoich_afr
            )

        except (requests.RequestException, ValueError, Exception) as e:
            logger.warning(f"Failed to resolve full specs for {make} {model}: {e}. Using robust fallbacks.")
            return self._get_fallback_specs(make, model)

    def _get_fallback_specs(self, make: str, model: str) -> VehicleSpecs:
        """
        Sensible industry defaults for European/UK-compatible models when API specs are unavailable.
        """
        # could lead to important inaccuracies down the line.
        fuel_type = "Petrol"
        engine_displacement_l = 2.0
        mechanical_max_rpm = 6500 
        stoichiometric_afr = 14.7 
        base_weight_kg = 1400.0
        
        return VehicleSpecs(
            fuel_type=fuel_type,
            engine_displacement_l=engine_displacement_l,
            base_weight_kg=base_weight_kg,
            mechanical_max_rpm=mechanical_max_rpm,
            stoichiometric_afr=stoichiometric_afr
        )
