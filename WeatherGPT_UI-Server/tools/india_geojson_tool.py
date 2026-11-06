"""
India GeoJSON Tool
===================

What this does (in plain words):
---------------------------------
You give it a name — a city, a district, or a state in India — and it
gives you back the "shape" of that place as GeoJSON data.

GeoJSON is just a standard file format for describing shapes on a map
(points, lines, areas) using plain JSON text. Think of it like a blueprint
file, but for geography instead of a circuit.

How it works under the hood:
-----------------------------
We call a free public service called "Nominatim" (part of OpenStreetMap).
It's like asking a librarian: "give me the outline of Kolkata" — and it
mails back the boundary as GeoJSON.

How to use it:
--------------
From the command line:
    python india_geojson_tool.py "Kolkata"
    python india_geojson_tool.py "West Bengal"

From your own code:
    from india_geojson_tool import get_geojson
    data = get_geojson("Kolkata")
"""

import sys
import json
import requests


# The web address of the Nominatim search service.
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim's rules say every request must identify itself.
# This is like putting your name/roll-number on an answer sheet —
# just good etiquette when using someone else's free service.
HEADERS = {
    "User-Agent": "india-geojson-tool/1.0 (student project)"
}


def get_geojson(place_name: str, save_to: str = None) -> dict:
    """
    Fetch the GeoJSON boundary for a place inside India.

    Parameters
    ----------
    place_name : str
        Name of the city / district / state. Example: "Kolkata".
    save_to : str, optional
        If given, also saves the GeoJSON to this file path.

    Returns
    -------
    dict or None
        The GeoJSON data as a Python dictionary, or None if nothing
        was found for that name.
    """
    # Note: Nominatim does NOT allow mixing the free-text "q" search with
    # a separate "country" field — doing so causes a 400 Bad Request.
    # So instead, we just add "India" straight into the search text.
    params = {
        "q": f"{place_name}, India",
        "format": "geojson",
        "polygon_geojson": 1,   # 1 = "please also send me the boundary shape"
        "limit": 1,             # just the single best match
    }

    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()  # stop loudly if the request itself failed

    data = response.json()

    # An empty "features" list means Nominatim found nothing for this name.
    if not data.get("features"):
        print(f"No results found for '{place_name}'. Try a more specific name.")
        return None

    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved GeoJSON to '{save_to}'")

    return data


def _self_test():
    """
    A tiny sanity check: make sure a well-known place actually returns
    a valid GeoJSON shape. This is the "test case" that only runs when
    you execute this file directly (see the bottom of the file).
    """
    print("Running self-test on a known place ('Kolkata')...")
    result = get_geojson("Kolkata")

    assert result is not None, "Expected a result, got None"
    assert "features" in result, "Result should contain a 'features' key"
    assert len(result["features"]) > 0, "Expected at least one feature"
    assert "geometry" in result["features"][0], "Feature should have a 'geometry'"

    print("Self-test passed ✅\n")


def _demo():
    """
    Runs the tool on whatever place name you typed on the command line
    (or a default one), and prints a short preview of the result.
    """
    place = sys.argv[1] if len(sys.argv) > 1 else "Kolkata"
    filename = f"{place.replace(' ', '_')}.geojson"

    print(f"Fetching GeoJSON for: {place}")
    result = get_geojson(place, save_to=filename)

    if result:
        feature = result["features"][0]
        print("\n--- Quick preview ---")
        print("Matched place   :", feature["properties"].get("display_name"))
        print("Geometry type   :", feature["geometry"]["type"])
        print("Total features  :", len(result["features"]))


# --------------------------------------------------------------------
# This block runs ONLY when you execute this file directly, like:
#     python india_geojson_tool.py
#
# It will NOT run if someone just imports this file, like:
#     import india_geojson_tool
#
# This is the standard Python way to separate "reusable code" from
# "code that runs as a script" — similar to how a header file (.h) in
# C just declares things, but only main.c actually runs on boot.
# --------------------------------------------------------------------
if __name__ == "__main__":
    _self_test()
    _demo()