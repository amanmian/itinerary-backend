def generate_itinerary(destination, days, interests):
    itinerary = {}
    sample_places = {
        "nature": ["Botanical Garden", "Lake View", "Nature Walk"],
        "history": ["Old Fort", "Museum", "Heritage Site"],
        "food": ["Local Market", "Street Food Tour", "Famous Cafe"],
        "adventure": ["Paragliding", "Trekking", "Zipline"]
    }

    for day in range(1, days + 1):
        day_plan = []
        for interest in interests:
            places = sample_places.get(interest, [])
            if places:
                day_plan.append(places[day % len(places)])
        itinerary[f"Day {day}"] = day_plan or ["Explore city on your own"]
    return itinerary
