from flask import Flask, request, jsonify
import openai
import json
import re
from urllib.parse import quote
from datetime import datetime, timedelta
import requests
from flask_cors import CORS

openai.api_key = "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"  # Keep secure

app = Flask(__name__)
CORS(app)

WEATHER_API_KEY = "5c35800846661c336445d110ba7768cd"
VISUAL_CROSSING_API_KEY = "DM7WDGH2ZZWWLN5YHT7CLEE6Z"  # Replace with your actual API key

def generate_map_url(name):
    return f"https://www.google.com/maps/search/?api=1&query={quote(name)}"

def estimate_total_cost(num_days, num_people, budget_level):
    transport_per_day = 2500
    meal_per_person_per_day = 600

    if budget_level == "low":
        hotel_per_room = 2000
    elif budget_level == "medium":
        hotel_per_room = 4000
    else:
        hotel_per_room = 8000

    rooms_needed = (num_people + 1) // 2
    hotel_total = hotel_per_room * rooms_needed * num_days
    meal_total = meal_per_person_per_day * num_people * num_days
    transport_total = transport_per_day * num_days

    total = hotel_total + meal_total + transport_total

    return {
        "estimated_total_cost": total,
        "breakdown": {
            "transport": transport_total,
            "meals": meal_total,
            "hotel": hotel_total
        }
    }

def get_historical_weather(city, date_str):
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{quote(city)}/{date_str}?key={VISUAL_CROSSING_API_KEY}&unitGroup=metric&include=days"
        res = requests.get(url)
        data = res.json()
        if "days" in data and len(data["days"]) > 0:
            day_data = data["days"][0]
            return {
                "summary": day_data.get("conditions", "Unknown"),
                "temperature": day_data.get("temp", 30)
            }
    except Exception as e:
        print(f"[!] Historical fetch failed for {city} on {date_str}: {e}")
    return None

def get_weather_forecast(destination, start_date, num_days):
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={quote(destination)}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url)
        data = res.json()

        forecasts = {}
        for day_offset in range(num_days):
            day = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day_offset)).date()
            daily_forecasts = [f for f in data.get("list", []) if f["dt_txt"].startswith(str(day))]

            if daily_forecasts:
                avg_temp = sum([f["main"]["temp"] for f in daily_forecasts]) / len(daily_forecasts)
                weather_desc = daily_forecasts[0]["weather"][0]["description"].capitalize()
                source = "forecast"
            else:
                # Fallback to last year's weather
                hist_date = day.replace(year=day.year - 1).isoformat()
                hist_data = get_historical_weather(destination, hist_date)
                if hist_data:
                    avg_temp = hist_data["temperature"]
                    weather_desc = hist_data["summary"]
                    source = "historical"
                else:
                    continue

            forecasts[day.isoformat()] = {
                "summary": weather_desc,
                "temperature": f"{round(avg_temp)}°C",
                "source": source
            }

        return forecasts

    except Exception as e:
        print("Weather API error:", str(e))
        return {}

@app.route("/itinerary", methods=["POST"])
def generate_itinerary():
    try:
        data = request.get_json()
        destination = data.get("destination", "").strip()
        number_of_days = int(data.get("number_of_days", 0))
        start_date = data.get("start_date", "").strip()

        travel_type = data.get("travel_type", "").lower().strip()
        has_infant = data.get("has_infant", False)
        num_people = int(data.get("number_of_people", 0))
        budget = data.get("budget", "").strip()

        if not destination or number_of_days <= 0 or not start_date:
            return jsonify({"error": "Invalid input"}), 400

        weather_by_day = get_weather_forecast(destination, start_date, number_of_days)

        prompt = f"""
You are a travel expert. Create a detailed {number_of_days}-day itinerary for a group of {num_people} people visiting {destination}.
They are traveling as a {travel_type}.
{"They also have an infant with them." if has_infant else ""}
Their overall travel budget is {budget}.

Each day should contain:
- 2 to 4 tourist attractions with short descriptions
- suggestions for breakfast, lunch, and dinner (local cuisines, restaurants)
- transport mode between locations (if needed)

Also recommend 1–2 hotels (budget-specific, family/friendly, realistic names & locations) in the city or nearby stay locations based on their travel days.

⚠️ Response format (strict JSON):
{{
    "destination": "{destination}",
    "itinerary": [
        {{
            "day": 1,
            "places": [
                {{
                    "title": "Place Name",
                    "description": "Why it's worth visiting"
                }}
            ],
            "meals": {{
                "breakfast": "Where/what to eat",
                "lunch": "Where/what to eat",
                "dinner": "Where/what to eat"
            }},
            "travel_info": "How to travel between listed places"
        }}
    ],
    "recommended_hotels": [
        {{
            "name": "Hotel Name",
            "description": "Why it's a good match",
            "budget": "low/medium/high",
            "location": "Nearby landmark or area"
        }}
    ]
}}
Only return valid JSON. Do not use markdown.
        """

        client = openai.OpenAI(api_key="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")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful travel planner."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()

        if result_text.startswith("```"):
            result_text = re.sub(r"^```(json)?", "", result_text)
            result_text = result_text.rstrip("`").strip()

        try:
            itinerary_data = json.loads(result_text)

            for i, day in enumerate(itinerary_data.get("itinerary", [])):
                current_day = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)).date().isoformat()
                day["weather"] = weather_by_day.get(current_day, {})

                for place in day.get("places", []):
                    place_name = place.get("title", "")
                    place["map_url"] = generate_map_url(f"{place_name}, {destination}")

            for hotel in itinerary_data.get("recommended_hotels", []):
                hotel_name = hotel.get("name", "")
                hotel["map_url"] = generate_map_url(f"{hotel_name}, {destination}")

            cost_info = estimate_total_cost(number_of_days, num_people, budget.lower())
            itinerary_data["cost_estimate"] = cost_info

            return jsonify(itinerary_data)

        except json.JSONDecodeError:
            return jsonify({
                "error": "Failed to parse GPT response.",
                "raw_response": result_text
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
