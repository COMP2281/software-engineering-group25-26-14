import os
import json
import logging
from typing import List, Dict, Any
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GraniteCoachingService:
    """
    A service class to interact with IBM Granite locally via Ollama.
    This generates driver coaching messages and fuel strategy advice without needing an API key
    or an internet connection.
    """
    def __init__(self, model_id: str = "granite3.1-dense:8b"):
        """
        Initialize the IBM Granite coaching service using local Ollama.
        
        WHAT YOU NEED TO DO:
        Make sure you have Ollama installed and have pulled the model by running:
        `ollama run granite3.1-dense:8b` in your terminal.
        
        :param model_id: The local Ollama model to use.
        """
        self.model_id = model_id
        
        # Verify Ollama is running and the model is available
        self._verify_connection()

    def _verify_connection(self):
        """Checks if Ollama is running and the model is pulled locally."""
        try:
            # We list local models to ensure it's installed
            models = ollama.list()
            # The 'models' object is a list of model objects, each with a 'model' attribute
            model_names = [m.model for m in models.models]
            
            if not any(self.model_id in name for name in model_names):
                logging.warning(f"Model '{self.model_id}' not found locally. Please run: 'ollama pull {self.model_id}'")
            else:
                logging.info(f"Successfully connected to local Ollama running: {self.model_id}")
        except Exception as e:
            logging.error(f"Failed to connect to Ollama. Make sure the Ollama app is running! Error: {e}")

    def _generate_text(self, prompt: str, max_tokens: int = 150) -> str:
        """Helper to call the local Ollama Granite model API."""
        try:
            # We use the generate endpoint (rather than chat) since we are passing a pre-formatted system prompt
            response = ollama.generate(
                model=self.model_id,
                prompt=prompt,
                options={
                    "temperature": 0.1, # Greedy decoding (less creative, factual)
                    "num_predict": max_tokens, # Equivalent to max_new_tokens
                    "repeat_penalty": 1.05
                }
            )
            
            if 'response' in response:
                return response['response'].strip()
                
            return "Error: Could not extract AI advice from local Granite response."
            
        except Exception as e:
            logging.error(f"Error querying local Ollama model: {e}")
            return f"Error: Failed to generate response from {self.model_id}."

    # =========================================================================
    # Feature 7 – Personalised Coaching with IBM Granite
    # =========================================================================

    def generate_coaching_message(self, trip_summary: Dict[str, Any], inefficiencies: List[Dict[str, Any]]) -> str:
        """
        BR7.1: Generate coaching messages when inefficiencies exist.
        Links specific behaviour to fuel impact and provides a recommended improvement.
        """
        prompt = f"""<|system|>
You are a highly analytical and supportive AI driving coach.
The user has just completed a trip with the following summary:
- Duration: {trip_summary.get('duration_mins', 'Unknown')} minutes
- Distance: {trip_summary.get('distance_km', 'Unknown')} km
- Fuel Consumed: {trip_summary.get('fuel_consumed_liters', 'Unknown')} Liters

The following inefficiency events were logged during the trip:
{json.dumps(inefficiencies, indent=2)}

Task: Provide a natural-language coaching message for the driver.
Rules:
1. MUST START your response with the exact word "Negative:" followed by a space.
2. Link the specific inefficient behaviours directly to their negative impact on fuel consumption.
3. Provide a clear, actionable recommended improvement for their next trip.
4. Keep the tone encouraging but informative. Do not use hardcoded templates; natural language only.
<|user|>
Generate the coaching message.
<|assistant|>"""

        return self._generate_text(prompt, max_tokens=250)

    def generate_positive_reinforcement(self, trip_summary: Dict[str, Any]) -> str:
        """
        BR7.2: Generate positive reinforcement when no inefficiencies exist.
        Includes a proactive suggestion to maintain efficient driving.
        """
        prompt = f"""<|system|>
You are a highly encouraging AI driving coach.
The user has just completed an excellent trip with ZERO major inefficiency events.

Trip Summary:
- Duration: {trip_summary.get('duration_mins', 'Unknown')} minutes
- Distance: {trip_summary.get('distance_km', 'Unknown')} km
- Fuel Consumed: {trip_summary.get('fuel_consumed_liters', 'Unknown')} Liters

Task: Provide a positive reinforcement message for the driver.
Rules:
1. MUST START your response with the exact word "Positive:" followed by a space.
2. Congratulate them on their highly efficient driving with no major inefficiencies.
3. Include at least one proactive, generalized suggestion or tip to help them maintain this fuel-efficient driving style in the future.
4. Keep the tone very positive and motivating.
<|user|>
Generate the positive reinforcement message.
<|assistant|>"""

        return self._generate_text(prompt, max_tokens=200)

    # =========================================================================
    # Feature 10 – Fuel Strategy Advice and High-Level Guidance
    # =========================================================================

    def summarize_inefficiency_patterns(self, historical_trips: List[Dict[str, Any]]) -> str:
        """
        BR10.1: Summarise common inefficiency patterns across multiple trips.
        Identifies frequent inefficiency event types and generates a short natural-language summary.
        """
        event_frequencies = {}
        for trip in historical_trips:
            for event in trip.get("inefficiencies", []):
                e_type = event.get("type", "Unknown")
                event_frequencies[e_type] = event_frequencies.get(e_type, 0) + 1
                
        prompt = f"""<|system|>
You are a seasoned Fleet Analyst AI.
Over a recent period, a driver completed several trips.
Here is the frequency of inefficiency events detected across all these trips:
{json.dumps(event_frequencies, indent=2)}

Task: Identify the most frequent inefficiency event types from the data above.
Rules:
1. Generate a short natural-language summary identifying these patterns.
2. Explain what these repeated behaviors mean generally across multiple trips.
<|user|>
Generate the summary of patterns.
<|assistant|>"""

        return self._generate_text(prompt, max_tokens=200)

    def provide_high_level_recommendations(self, strategy_summary_text: str) -> str:
        """
        BR10.2: Provide high-level recommendations to reduce fuel usage based on the summary.
        Produces advice clearly distinct from trip-specific coaching messages.
        """
        prompt = f"""<|system|>
You are an expert Fleet Strategy AI.
The following is a summary of a driver's common inefficiency patterns across multiple trips:
"{strategy_summary_text}"

Task: Produce at least one high-level strategy recommendation to reduce fuel overall.
Rules:
1. These recommendations should be broader than per-trip feedback (e.g., long-term decisions regarding route selection, maintaining coasting distances, vehicle maintenance, or scheduling).
2. The advice must be clearly distinct from trip-specific, real-time coaching messages. Focus on the big picture.
<|user|>
Generate the high-level strategic recommendation.
<|assistant|>"""

        return self._generate_text(prompt, max_tokens=250)


# =========================================================================
# Testing Block (Demonstration)
# =========================================================================
if __name__ == "__main__":
    print("Initializing Offline Granite Coaching Module...")
    
    # We no longer need to pass API keys, we just initialize it to hit localhost!
    service = GraniteCoachingService()
    
    import sys
    from pathlib import Path
    import pandas as pd
    
    # Add project root and Model Development to path
    base_dir = Path(__file__).resolve().parent
    project_root = base_dir.parent
    sys.path.append(str(project_root))
    sys.path.append(str(project_root / "Model Development"))
    
    from data_pipeline.ingestion.preprocessing import PreprocessingPipeline
    from model_engine import analyse_trip
    
    data_dir = project_root / "data"
    pipeline = PreprocessingPipeline()
    result = pipeline.ingest_path(data_dir)
    
    all_trips_events = []
    
    print(f"Files processed for real data: {len(result.processed_datasets)}\n")
    
    for dataset in result.processed_datasets:
        if dataset.validation.status != "accepted":
            continue
            
        for trip in dataset.trips:
            try:
                df = trip.dataframe
                if "Timestamp" in df.columns:
                    df["Timestamp"] = pd.to_datetime(
                        df["Timestamp"], format="%H:%M:%S.%f", errors="coerce"
                    ).astype("datetime64[ns]")
                
                analysis = analyse_trip(df)
                
                # compute trip summary
                duration_mins = 0
                if not df.empty and "Timestamp" in df.columns:
                    duration_s = (df["Timestamp"].max() - df["Timestamp"].min()).total_seconds()
                    duration_mins = duration_s / 60
                
                avg_speed = analysis["trip_metrics"].get("average_speed", 0)
                distance_km = avg_speed * (duration_mins / 60)
                avg_fuel = analysis["trip_metrics"].get("average_fuel_efficiency", 8.5)
                fuel_consumed = (distance_km / 100) * avg_fuel
                
                trip_summary = {
                    "duration_mins": round(duration_mins, 2),
                    "distance_km": round(distance_km, 2),
                    "fuel_consumed_liters": round(fuel_consumed, 2)
                }
                
                # Format inefficiencies
                events = analysis.get("events", [])
                
                event_counts = {}
                for e in events:
                    e_type = e["type"]
                    duration = e.get("duration", 0)
                    if e_type not in event_counts:
                        event_counts[e_type] = {"count": 0, "total_duration": 0}
                    event_counts[e_type]["count"] += 1
                    event_counts[e_type]["total_duration"] += duration
                
                inefficiencies = [
                    {"type": k, "count": v["count"], "total_duration_secs": round(v["total_duration"], 2)}
                    for k, v in event_counts.items()
                ]
                
                all_trips_events.append({"trip_id": trip.metadata.trip_id, "inefficiencies": inefficiencies})
                
                print(f"--- Trip {trip.metadata.trip_id} Analysis ---")
                if len(inefficiencies) > 0:
                    print("Testing BR7.1: Coaching with Inefficiencies")
                    print(service.generate_coaching_message(trip_summary, inefficiencies))
                else:
                    print("Testing BR7.2: Positive Reinforcement")
                    print(service.generate_positive_reinforcement(trip_summary))
                print("-" * 40)
                    
            except Exception as e:
                print(f"Error analyzing trip {trip.metadata.trip_id}: {e}")

    if all_trips_events:
        print("\n--- Testing BR10.1: Summarise Inefficiency Patterns (Real Data) ---")
        summary = service.summarize_inefficiency_patterns(all_trips_events)
        print(summary)
        
        print("\n--- Testing BR10.2: High-Level Recommendations (Real Data) ---")
        print(service.provide_high_level_recommendations(summary))
