def get_top_hotels(hotels: list, min_rating: float = 4.0):
    return sorted(
        [h for h in hotels if h["rating"] >= min_rating],
        key=lambda x: x["rating"],
        reverse=True
    )