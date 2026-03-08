import os
import json
from typing import List, Dict, Any
from genai import Client, Credentials
from genai.schema import TextGenerationParameters

class GraniteCoachingService:
    """
    A service class to interact with IBM Granite directly via the IBM Generative AI SDK.
    This generates driver coaching messages and fuel strategy advice.
    """
    def __init__(self, api_key: str = None, endpoint: str = "https://bam-api.res.ibm.com"):
        """
        Initialize the IBM Granite coaching service.
        
        WHAT YOU NEED TO DO:
        The easiest way to make this work locally without hardcoding your passwords 
        is to open your terminal (Mac/Linux) and run these two commands before running the python script:
        
        export GRANITE_API_KEY="your-actual-api-key-here"
        export GRANITE_API_ENDPOINT="https://us-south.ml.cloud.ibm.com"  <-- (Use this if using Watsonx instead of BAM)
        
        :param api_key: IBM Granite API Key (e.g., BAM API key or IBM Cloud API Key)
        :param endpoint: IBM Granite API endpoint (BAM or Watsonx URL)
        """
        # We try to grab the key from the environment variables you exported.
        self.api_key = api_key or os.environ.get("GRANITE_API_KEY")
        self.endpoint = endpoint or os.environ.get("GRANITE_API_ENDPOINT", "https://bam-api.res.ibm.com")
        self.client = None
        
        # This is the standard open-source Granite model used for conversational chat
        self.model_id = "ibm/granite-13b-chat-v2" 
        
        # If an API key was found, we attempt to authenticate immediately
        if self.api_key:
            self._authenticate()

    def _authenticate(self):
        """Initializes the Granite Client using the provided API key."""
        try:
            # We bundle your API key and endpoint URL into a Credentials object
            credentials = Credentials(api_key=self.api_key, api_endpoint=self.endpoint)
            # We then create the main Client which will be used to send all prompts to IBM
            self.client = Client(credentials=credentials)
        except Exception as e:
            print(f"Warning: Failed to initialize Granite Client: {e}")

    def _generate_text(self, prompt: str, max_new_tokens: int = 150) -> str:
        """Helper to call IBM Granite text generation API."""
        
        # If the client wasn't set up (because you didn't export the API key), we return a fake message
        if not self.client:
            return "[Mock Granite Response]: Configure GRANITE_API_KEY to generate real AI advice."
            
        # These parameters control how the AI thinks:
        # - greedy: Picks the most likely next word (less creative, more factual)
        # - max_new_tokens: How long the AI's response is allowed to be
        # - repetition_penalty: Stops the AI from repeating the same sentence over and over
        parameters = TextGenerationParameters(
            decoding_method="greedy",
            max_new_tokens=max_new_tokens,
            repetition_penalty=1.05
        )
        
        try:
            # We send the prompt to IBM Granite and ask for a generation back
            responses = list(self.client.text.generation.create(
                model_id=self.model_id,
                inputs=[prompt],
                parameters=parameters
            ))
            
            # If the response was successful, we extract just the raw text
            if responses and responses[0].results:
                return responses[0].results[0].generated_text.strip()
            
            return "Error: Could not extract AI advice from Granite response."
        except Exception as e:
            print(f"Error connecting to IBM Granite: {e}")
            return "Error: Connection failed."

    # =========================================================================
    # Feature 7 – Personalised Coaching with IBM Granite
    # =========================================================================

    def generate_coaching_message(self, trip_summary: Dict[str, Any], inefficiencies: List[Dict[str, Any]]) -> str:
        """
        BR7.1: Generate coaching messages when inefficiencies exist.
        Links specific behaviour to fuel impact and provides a recommended improvement.
        """
        # The prompt is split into [System], [User], and [Assistant]. 
        # This is the required format to make Granite "roleplay" properly.
        prompt = f"""[System]
You are a highly analytical and supportive AI driving coach.
The user has just completed a trip with the following summary:
- Duration: {trip_summary.get('duration_mins', 'Unknown')} minutes
- Distance: {trip_summary.get('distance_km', 'Unknown')} km
- Fuel Consumed: {trip_summary.get('fuel_consumed_liters', 'Unknown')} Liters

The following inefficiency events were logged during the trip:
{json.dumps(inefficiencies, indent=2)}

Task: Provide a natural-language coaching message for the driver.
Rules:
1. Link the specific inefficient behaviours directly to their negative impact on fuel consumption.
2. Provide a clear, actionable recommended improvement for their next trip.
3. Keep the tone encouraging but informative. Do not use hardcoded templates; natural language only.
[User]
Generate the coaching message.
[Assistant]"""

        return self._generate_text(prompt, max_new_tokens=250)

    def generate_positive_reinforcement(self, trip_summary: Dict[str, Any]) -> str:
        """
        BR7.2: Generate positive reinforcement when no inefficiencies exist.
        Includes a proactive suggestion to maintain efficient driving.
        """
        prompt = f"""[System]
You are a highly encouraging AI driving coach.
The user has just completed an excellent trip with ZERO major inefficiency events.

Trip Summary:
- Duration: {trip_summary.get('duration_mins', 'Unknown')} minutes
- Distance: {trip_summary.get('distance_km', 'Unknown')} km
- Fuel Consumed: {trip_summary.get('fuel_consumed_liters', 'Unknown')} Liters

Task: Provide a positive reinforcement message for the driver.
Rules:
1. Congratulate them on their highly efficient driving with no major inefficiencies.
2. Include at least one proactive, generalized suggestion or tip to help them maintain this fuel-efficient driving style in the future.
3. Keep the tone very positive and motivating.
[User]
Generate the positive reinforcement message.
[Assistant]"""

        return self._generate_text(prompt, max_new_tokens=200)

    # =========================================================================
    # Feature 10 – Fuel Strategy Advice and High-Level Guidance
    # =========================================================================

    def summarize_inefficiency_patterns(self, historical_trips: List[Dict[str, Any]]) -> str:
        """
        BR10.1: Summarise common inefficiency patterns across multiple trips.
        Identifies frequent inefficiency event types and generates a short natural-language summary.
        """
        # Before asking the AI, we loop through all the trips in Python to count how 
        # often each bad behavior (like 'Idling') happens. It's better to do the math in Python 
        # than to force the AI to count things!
        event_frequencies = {}
        for trip in historical_trips:
            for event in trip.get("inefficiencies", []):
                e_type = event.get("type", "Unknown")
                event_frequencies[e_type] = event_frequencies.get(e_type, 0) + 1
                
        prompt = f"""[System]
You are a seasoned Fleet Analyst AI.
Over a recent period, a driver completed several trips.
Here is the frequency of inefficiency events detected across all these trips:
{json.dumps(event_frequencies, indent=2)}

Task: Identify the most frequent inefficiency event types from the data above.
Rules:
1. Generate a short natural-language summary identifying these patterns.
2. Explain what these repeated behaviors mean generally across multiple trips.
[User]
Generate the summary of patterns.
[Assistant]"""

        return self._generate_text(prompt, max_new_tokens=200)

    def provide_high_level_recommendations(self, strategy_summary_text: str) -> str:
        """
        BR10.2: Provide high-level recommendations to reduce fuel usage based on the summary.
        Produces advice clearly distinct from trip-specific coaching messages.
        """
        prompt = f"""[System]
You are an expert Fleet Strategy AI.
The following is a summary of a driver's common inefficiency patterns across multiple trips:
"{strategy_summary_text}"

Task: Produce at least one high-level strategy recommendation to reduce fuel overall.
Rules:
1. These recommendations should be broader than per-trip feedback (e.g., long-term decisions regarding route selection, maintaining coasting distances, vehicle maintenance, or scheduling).
2. The advice must be clearly distinct from trip-specific, real-time coaching messages. Focus on the big picture.
[User]
Generate the high-level strategic recommendation.
[Assistant]"""

        return self._generate_text(prompt, max_new_tokens=250)


# =========================================================================
# Testing Block (Demonstration)
# =========================================================================
if __name__ == "__main__":
    print("Initializing Granite Coaching Module...")
    
    # ----------------------------------------------------
    # WHAT YOU NEED TO DO:
    # ----------------------------------------------------
    # When you want this to use the REAL AI, you must export these two variables 
    # in your terminal before running this script:
    # 
    #   export GRANITE_API_KEY="your-actual-api-key"
    #   export GRANITE_API_ENDPOINT="https://bam-api.res.ibm.com"  
    # 
    # If the variables aren't found, the code prints [Mock Granite Response] below.
    service = GraniteCoachingService()
    
    # ---------------------------------------------------------
    # Test BR7.1: Coaching Message (with inefficiencies)
    # ---------------------------------------------------------
    trip_summary_bad = {"duration_mins": 45, "distance_km": 30, "fuel_consumed_liters": 4.5}
    inefficiencies = [
        {"type": "Harsh Braking", "count": 4, "severity": "High", "fuel_wasted_est": 0.3},
        {"type": "Over-revving", "count": 2, "severity": "Medium", "fuel_wasted_est": 0.1}
    ]
    print("\n--- Testing BR7.1: Coaching with Inefficiencies ---")
    print(service.generate_coaching_message(trip_summary_bad, inefficiencies))
    
    # ---------------------------------------------------------
    # Test BR7.2: Positive Reinforcement (no inefficiencies)
    # ---------------------------------------------------------
    trip_summary_good = {"duration_mins": 35, "distance_km": 30, "fuel_consumed_liters": 2.8}
    print("\n--- Testing BR7.2: Positive Reinforcement ---")
    print(service.generate_positive_reinforcement(trip_summary_good))
    
    # ---------------------------------------------------------
    # Test BR10.1: Summarise Patterns
    # ---------------------------------------------------------
    historical_trips = [
        {"trip_id": 1, "inefficiencies": [{"type": "Idling"}, {"type": "Harsh Acceleration"}]},
        {"trip_id": 2, "inefficiencies": [{"type": "Idling"}]},
        {"trip_id": 3, "inefficiencies": [{"type": "Idling"}, {"type": "Harsh Braking"}]}
    ]
    print("\n--- Testing BR10.1: Summarise Inefficiency Patterns ---")
    summary = service.summarize_inefficiency_patterns(historical_trips)
    print(summary)
    
    # ---------------------------------------------------------
    # Test BR10.2: High-Level Recommendations
    # ---------------------------------------------------------
    print("\n--- Testing BR10.2: High-Level Recommendations ---")
    print(service.provide_high_level_recommendations(summary))
