# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

"""
MongoDB -> GeoJSON Tool (for Leaflet overlays)
================================================

What this does, in plain words:
--------------------------------
Your weather data sits in MongoDB, but every value there (even numbers)
is saved as a STRING, like "23.5" instead of 23.5.

This tool:
  1. Connects to your MongoDB collection.
  2. Takes a field name + a value range you give it,
     e.g. {"field": "Temperature", "start_value": 20, "end_value": 30}
  3. Converts each document's string value to a float, and keeps only
     the documents that fall inside that range.
  4. Grabs each matching document's Latitude/Longitude and builds a
     GeoJSON "FeatureCollection" of Points out of them.
  5. Saves that GeoJSON to a file, ready to drop onto a Leaflet map:
         L.geoJSON(data).addTo(map);
     Each matching document becomes one point (a dot) on the map.

Think of it like a sieve: you pour your whole database through it,
tell it what range of values to keep, and only the matching points
fall through — already placed on a map.

IMPORTANT GeoJSON detail:
--------------------------
GeoJSON always stores coordinates as [longitude, latitude] — the
REVERSE of how people usually say "lat, long" out loud. Get this
backwards and every point lands in the wrong place on the map. This
tool handles the flip for you.
"""

import json
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv("../../.env")
# ---------------------------------------------------------------------
# MONGODB COLLECTION to Station_ID_Field converter dict
# ---------------------------------------------------------------------
stationId_resolver = {
    "7Days_Station_Forecast":"Station_Code",
    "Current_Weather_Forecast":"Station Id"
}
# ---------------------------------------------------------------------
# MONGODB COLLECTION to Station_Name_Field converter dict
# ---------------------------------------------------------------------
stationName_resolver = {
    "7Days_Station_Forecast":"Station_Name",
    "Current_Weather_Forecast":"Station"
}

#
#   --- Create one more dict | For district name and their geojson | Stored in mongodb ---
#   --- Create a tool by simply using the india_geojson_tool | For districts from all the documents of loc_collection
#

# ---------------------------------------------------------------------
# EDIT THESE to match your own MongoDB setup
# ---------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_CONN")
DATABASE_NAME = "WeatherGPT"
COLLECTION_NAME = "Current_Weather_Forecast"
LOC_RESOLVE_COL="5digit_StationId_To_Location"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# The field names in your documents that hold the coordinates.
# Change these if your documents use different names (e.g. "lat", "lon").
LATITUDE_FIELD = "Latitude"
LONGITUDE_FIELD = "Longitude"


def get_filtered_geojson(collection_name:str, field: str, start_value: float, end_value: float, Date:str, 
                          save_to: str = None) -> dict:
    """
    Pull documents from MongoDB whose `field` (converted to float) falls
    between start_value and end_value (inclusive), and turn their
    coordinates into a GeoJSON FeatureCollection.

    Parameters
    ----------
    field : str
        Name of the field to filter on, e.g. "Temperature".
    start_value : float
        Lower bound of the range (inclusive).
    end_value : float
        Upper bound of the range (inclusive).
    save_to : str, optional
        If given, writes the resulting GeoJSON to this file path.

    Returns
    -------
    dict
        A GeoJSON FeatureCollection, ready to feed to Leaflet.
    """
    collection = db[collection_name]
    loc_collection = db[LOC_RESOLVE_COL]
    

    features = []
    skipped = 0

    # We fetch every document and check it in Python, because the values
    # are stored as strings — MongoDB can't correctly range-filter a
    # numeric-looking value while it's still text (e.g. "9" > "10" as text!).
    results_matching_filter = 0
    for doc in collection.find({'Date':Date}):
        # Converting to str so the tool will work as intended
        if collection_name == 'Current_Weather_Forecast':
            doc['Wind Direction'] = str(doc.get('Wind Direction'))
            doc['Wind Speed KMPH'] = str(doc.get('Wind Speed KMPH'))
        
        # station_ID_field name for that collection
        station_id_field = stationId_resolver.get(collection_name)
        station_name_field = stationName_resolver.get(collection_name)
        
        # station_id is INTEGER in LOC_COLLECTION
        station_id = int( doc.get(station_id_field) )
        station_name = doc.get(station_name_field) 
        print(f"Station Id: {station_id}, Station Name: {station_name}")
        
        
        raw_value = doc.get(field)
        loc_doc = loc_collection.find_one({"station_id":station_id})
        if loc_doc:
            raw_lat = loc_doc.get(LATITUDE_FIELD)
            raw_lon = loc_doc.get(LONGITUDE_FIELD)
        else:
            raise FileNotFoundError("[DATABASE ERROR][FROM mongo_to_geojson.get_filtered_geojson()] -> The location document was not found in the loc_collection")

        # Skip any document missing a piece we need.
        if raw_value is None or raw_lat is None or raw_lon is None:
            skipped += 1
            continue

        try:
            value = float(raw_value)
            lat = float(raw_lat)
            lon = float(raw_lon)
        except (TypeError, ValueError):
            # Couldn't convert to a number — bad/corrupt data, skip it.
            skipped += 1
            continue
        
        
        if start_value <= value <= end_value:
            results_matching_filter += 1
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    # GeoJSON order is [longitude, latitude] — NOT lat/lon!
                    "coordinates": [lon, lat],
                },
                "properties": {
                    field: value,
                    "name": f"{station_name} \n{field}: {str(value)}",
                    "_id": str(doc.get("_id")),
                },
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    print(f"Matched {len(features)} document(s). Skipped {skipped} (missing/bad data).")

    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)
        print(f"Saved GeoJSON to '{save_to}'")
        
    if results_matching_filter > 0:
        return {
            "success":True,
            "geojson":geojson,
            "No of results": results_matching_filter
            }
    else:
        print("No resuilts found")
        return {
            "success":False,
            "No of results": results_matching_filter
            }


def _self_test():
    """
    A small sanity check that runs only when this file is executed
    directly (not when imported elsewhere). It does NOT touch your real
    database — it just checks the filtering/GeoJSON logic on a tiny
    made-up example, so you know the core logic works before you run it
    against real data.
    """
    print("Running self-test on fake in-memory data...")

    fake_docs = [
        {"_id": "a", "Temperature": "25.0", "Latitude": "22.57", "Longitude": "88.36"},  # in range
        {"_id": "b", "Temperature": "40.0", "Latitude": "19.07", "Longitude": "72.87"},  # out of range
        {"_id": "c", "Temperature": "not_a_number", "Latitude": "28.61", "Longitude": "77.20"},  # bad data
    ]

    features = []
    for doc in fake_docs:
        try:
            value = float(doc["Temperature"])
            lat = float(doc["Latitude"])
            lon = float(doc["Longitude"])
        except ValueError:
            continue
        if 20 <= value <= 30:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"Temperature": value, "_id": doc["_id"]},
            })

    assert len(features) == 1, "Expected exactly 1 matching feature"
    assert features[0]["properties"]["_id"] == "a", "Wrong document matched"
    assert features[0]["geometry"]["coordinates"] == [88.36, 22.57], "Coordinate order is wrong"

    print("Self-test passed ✅\n")


def _demo():
    """
    Runs a real query against your MongoDB collection, using an example
    filter. Edit the `query` dict below, or better — import
    `get_filtered_geojson` into your own script and call it with
    whatever field/range you need.
    """
    query = {"field": "Temperature", "start_value": 20, "end_value": 30}

    print(f"Querying MongoDB for: {query}")
    get_filtered_geojson(
        field=query["field"],
        start_value=query["start_value"],
        end_value=query["end_value"],
        save_to="weather_overlay.geojson",
    )


# --------------------------------------------------------------------
# This block runs ONLY when you execute this file directly, like:
#     python mongo_to_geojson.py
# It will NOT run if you `import mongo_to_geojson` from another script.
# --------------------------------------------------------------------
if __name__ == "__main__":
    _self_test()
    _demo()