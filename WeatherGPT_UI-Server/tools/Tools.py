# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.


from pymongo import MongoClient
import os
from dotenv import load_dotenv
from . import india_geojson_tool
from .import mongo_to_geojson
import requests
import random
import datetime

load_dotenv("../.env")

MONGO_CURR = os.getenv("MONGO_CONN")
MAIN_DB = os.getenv("MAIN_DB")

assert MAIN_DB, ("No MAIN_DB found")

client = MongoClient(MONGO_CURR)
db = client[MAIN_DB]


#=======================================================================================================
#           GET 7DAYS FORECAST DATA
#-------------------------------------------------------------------------------------------------------
#
def Forecast_7Days_obsolete(**arguments) -> dict:
    # kwargs acts as a dictionary inside the function
    my_dict = {}
    for key, value in arguments.items():
        my_dict[key] = value.strip().lower()
        
    print(my_dict)
    
    collection = db['7Days_Station_Forecast']
    
    document = collection.find_one(my_dict)
    if document: 
        document.pop('_id', None)
        return document
    else:
        return {
            "success": False,
            "error": "No forecast data found",
            "query": arguments
        }
#--------------------------------------------------------------------------------------------------------
#=========================================================================================================


#=======================================================================================================
#           GET 7DAYS FORECAST DATA
#-------------------------------------------------------------------------------------------------------
#
def Forecast_7Days(conv_dict, **arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize AI arguments
    # ---------------------------------------------------------

    query = {}

    for key, value in arguments.items():

        if value is not None:
            query[key] = str(value).strip().lower()

    collection = db["7Days_Station_Forecast"]

    # ---------------------------------------------------------
    # DATE IS MANDATORY
    # ---------------------------------------------------------

    if "Date" not in query:
        return {
            "success": False,
            "error": "Date is required"
        }

    date_value = query["Date"]

    # ---------------------------------------------------------
    # LOCATION PRIORITY
    #
    # City → District → State
    # ---------------------------------------------------------

    location_field = None
    location_value = None

    if query.get("city"):
        location_field = "city"
        location_value = query["city"]

    elif query.get("district"):
        location_field = "district"
        location_value = query["district"]

    elif query.get("state"):
        location_field = "state"
        location_value = query["state"]

    # ---------------------------------------------------------
    # Build MongoDB query
    # ---------------------------------------------------------

    mongo_query = {
        "Date": date_value
    }

    # Add the highest-priority location available
    if location_field:
        mongo_query[location_field] = location_value

    # ---------------------------------------------------------
    # Find document
    # ---------------------------------------------------------

    result = collection.find_one(
        mongo_query,
        {
            "_id": 0
        }
    )

    # ---------------------------------------------------------
    # No result
    # ---------------------------------------------------------

    if not result:
        print("[FROM Tools.Forecast_7Days()] ERROR → No forecast data on database")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": mongo_query
        }
    print(
            "[FROM Tools.Forecast_7Days()] success → MongoDB query:",
            mongo_query
        )
    return result
#--------------------------------------------------------------------------------------------------------
#=========================================================================================================




#=========================================================================================================
#           GET CURRENT WEATHER FORECAST
#--------------------------------------------------------------------------------------------------------
#
def Current_Weather_Forecast(conv_dict, **arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize AI arguments
    # ---------------------------------------------------------

    query = {}

    for key, value in arguments.items():

        if value is not None:
            query[key] = str(value).strip().lower()

    collection = db["Current_Weather_Forecast"]

    # ---------------------------------------------------------
    # DATE IS MANDATORY
    # ---------------------------------------------------------

    if "Date" not in query:
        return {
            "success": False,
            "error": "date is required"
        }

    date_value = query["Date"]

    # ---------------------------------------------------------
    # LOCATION PRIORITY
    #
    # City → District → State
    # ---------------------------------------------------------

    location_field = None
    location_value = None

    if query.get("city"):
        location_field = "city"
        location_value = query["city"]

    elif query.get("district"):
        location_field = "district"
        location_value = query["district"]

    elif query.get("state"):
        location_field = "state"
        location_value = query["state"]

    # ---------------------------------------------------------
    # Build MongoDB query
    # ---------------------------------------------------------

    mongo_query = {
        "Date": date_value
    }

    # Add the highest-priority location available
    if location_field:
        mongo_query[location_field] = location_value

    # ---------------------------------------------------------
    # Find document
    # ---------------------------------------------------------

    result = collection.find_one(
        mongo_query,
        {
            "_id": 0
        }
    )

    # ---------------------------------------------------------
    # No result
    # ---------------------------------------------------------

    if not result:
        print("[FROM Tools.Current_Weather_Forecast()] ERROR → No forecast data on database")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": mongo_query
        }
    print(
            "[FROM Tools.Current_Weather_Forecast()] success → MongoDB query:",
            mongo_query
        )
    return result
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================


#=========================================================================================================
#           DISTRICT WISE WARNING
#--------------------------------------------------------------------------------------------------------
#
def district_wise_warning(conv_dict, **arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize AI arguments
    # ---------------------------------------------------------

    query = {}

    for key, value in arguments.items():

        if value is not None:
            query[key] = str(value).strip().lower()

    collection = db["District_Wise_Warning"]

    # ---------------------------------------------------------
    # DATE IS MANDATORY
    # ---------------------------------------------------------

    if "Date" not in query:
        return {
            "success": False,
            "error": "Date is required"
        }

    date_value = query["Date"]

    # ---------------------------------------------------------
    # LOCATION PRIORITY
    #
    # City → District → State
    # ---------------------------------------------------------

    location_field = None
    location_value = None

    if query.get("district"):
        location_field = "district"
        location_value = query["district"]
        pointer_helper(conv_dict, location_value)

    elif query.get("state"):
        location_field = "state"
        location_value = query["state"]
        pointer_helper(conv_dict, location_value)

    # ---------------------------------------------------------
    # Build MongoDB query
    # ---------------------------------------------------------

    mongo_query = {
        "Date": date_value
    }

    # Add the highest-priority location available
    if location_field:
        mongo_query[location_field] = location_value

    # ---------------------------------------------------------
    # Find document
    # ---------------------------------------------------------

    result = collection.find_one(
        mongo_query,
        {
            "_id": 0
        }
    )

    # ---------------------------------------------------------
    # No result
    # ---------------------------------------------------------

    if not result:
        print("[FROM Tools.DistrictWise_Warning()] ERROR → No forecast data on database")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": mongo_query
        }
    print(
            "[FROM Tools.DistrictWise_Warning()] success → MongoDB query:",
            mongo_query
        )
    return result
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================


#=========================================================================================================
#           PLOT ON MAP
#--------------------------------------------------------------------------------------------------------
#
def plot_on_map(conv_dict, **arguments) -> dict:
    for key, value in arguments.items():
        if key != 'color':
            location = value
            data = india_geojson_tool.get_geojson(value, None)
        else:
            overlay_color=arguments.get(key) or 'Blue'
        
    if not data:
        print("[FROM plot_on_map()] ERROR → Geojson not found ")
        return {
            "success":False,
            "error":f"geojson not found for '{location}' in database."
        }
        
    url = "http://localhost:5000/get_tool_geojson"
    payload={
        "user_id":conv_dict['user_id'],
        "geojson": data,
        "color":overlay_color
    }
    response = requests.post(url, json=payload)
    print("[FROM plot_on_map()] success → Geojson Found ")
    return {
        "success":True,
        "error":f"Successfully sen't geolocation for '{location}' to frontend."
            }
    
def pointer_helper(conv_dict, location) -> dict:
    data = india_geojson_tool.get_geojson(location, None)
        
    if not data:
        print("[FROM plot_on_map()] ERROR → Geojson not found ")
        return {
            "success":False,
            "error":f"geojson not found for '{location}' in database."
        }
        
    url = "http://localhost:5000/get_tool_geojson"
    payload={
        "user_id":conv_dict['user_id'],
        "geojson": data
    }
    response = requests.post(url, json=payload)
    print("[FROM plot_on_map()] success → Geojson Found ")
    return {
        "success":True,
        "error":f"Successfully sen't geolocation for '{location}' to frontend."
            }
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================


#=========================================================================================================
#           Filter and show results on map
#--------------------------------------------------------------------------------------------------------
#
# A dictionary mapping numbers 0-6 to light, pastel overlay colors
color_map = {
    0: "#F5627D",  # Light Pastel Red / Coral
    1: "#F0A12B",  # Light Pastel Orange
    2: "#FCF3CF",  # Light Pastel Yellow
    3: "#7AE8A6",  # Light Pastel Green
    4: "#EFA792",  # Light Pastel Blue
    5: "#B63FF1",  # Light Pastel Purple
    6: "#4F9AE4"   # Light Pastel Gray / Silver
}
def show_filtered_results(conv_dict, **arguments):
    collection_name = arguments.get('collection_name')
    field = arguments.get('fields')
    st_value = arguments.get('start_value')
    end_value = arguments.get('end_value')
    Date = arguments.get('Date')
    
    random_num = random.randint(0, 6)
    overlay_color = arguments.get('color') or color_map[random_num]
    
    result = mongo_to_geojson.get_filtered_geojson(collection_name, field, st_value, end_value, Date, None)
    
    if not result['success']:
        print("[FROM show_filtered_results()] ERROR → Filter not applied ")
        return {
            "success":False,
            "error":f"Filter couldn't be applied. No data sent to user. Nothing plotted on the map."
        }
    
    geoJSON_data = result['geojson']  
    url = "http://localhost:5000/get_tool_geojson"
    payload={
        "user_id":conv_dict['user_id'],
        "geojson": geoJSON_data,
        "color":overlay_color
    }
    response = requests.post(url, json=payload)
    print("[FROM show_filtered_results()] success → Filter Applied ")
    return {
        "success":True,
        "error":f"Succesfully applied the filter on the collection and plotted the results on the map.",
        "No of results matching the filter":result['No of results']
            }
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================

def get_datetime(conv_dict, **arguments):
    data = requests.get("https://ipinfo.io/json").json()
    day_of_the_week = datetime.date.today().strftime("%A")
    
    return f"Current Date & Time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {day_of_the_week} \n\nLocation: {data["loc"]} "