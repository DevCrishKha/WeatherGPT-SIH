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

load_dotenv(".env")

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
def Forecast_7Days(**arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize the arguments coming from the AI
    # ---------------------------------------------------------
    query = {}

    for key, value in arguments.items():
        if value is not None:
            query[key] = str(value).strip().lower()

    print("[FROM Tools.Forecast_7Days()] → AI query:", query)

    collection = db["7Days_Station_Forecast"]

    # ---------------------------------------------------------
    # If AI didn't provide anything, don't query the database
    # ---------------------------------------------------------
    if not query:
        return {
            "success": False,
            "error": "No search parameters provided"
        }

    # ---------------------------------------------------------
    # Build a MongoDB aggregation pipeline
    #
    # Each matching field gives the document +1 score.
    # ---------------------------------------------------------

    score_conditions = []

    for field, value in query.items():

        score_conditions.append({
            "$cond": [
                {"$eq": [
                    {"$toLower": {"$toString": f"${field}"}},
                    value
                ]},
                1,
                0
            ]
        })

    pipeline = [

        # Calculate how many requested fields match
        {
            "$addFields": {
                "_matchScore": {
                    "$add": score_conditions
                }
            }
        },

        # Highest number of matching fields first
        {
            "$sort": {
                "_matchScore": -1
            }
        },

        # We only need the best match
        {
            "$limit": 1
        }
    ]

    result = next(collection.aggregate(pipeline), None)

    # ---------------------------------------------------------
    # No document found
    # ---------------------------------------------------------

    if not result:
        print("\n[DATABASE ERROR]: No result found for the tool 7Days_Forecast")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": arguments
        }

    # Remove MongoDB internal fields
    result.pop("_id", None)
    result.pop("_matchScore", None)

    return result
#--------------------------------------------------------------------------------------------------------
#=========================================================================================================




#=========================================================================================================
#           GET CURRENT WEATHER FORECAST
#--------------------------------------------------------------------------------------------------------
#
def Current_Weather_Forecast(**arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize the arguments coming from the AI
    # ---------------------------------------------------------
    query = {}

    for key, value in arguments.items():
        if value is not None:
            query[key] = str(value).strip().lower()

    print("[FROM Tools.Current_Weather_Foreast()] → AI query:", query)

    collection = db["Current_Weather_Forecast"]

    # ---------------------------------------------------------
    # If AI didn't provide anything, don't query the database
    # ---------------------------------------------------------
    if not query:
        return {
            "success": False,
            "error": "No search parameters provided"
        }

    # ---------------------------------------------------------
    # Build a MongoDB aggregation pipeline
    #
    # Each matching field gives the document +1 score.
    # ---------------------------------------------------------

    score_conditions = []

    for field, value in query.items():

        score_conditions.append({
            "$cond": [
                {"$eq": [
                    {"$toLower": {"$toString": f"${field}"}},
                    value
                ]},
                1,
                0
            ]
        })

    pipeline = [

        # Calculate how many requested fields match
        {
            "$addFields": {
                "_matchScore": {
                    "$add": score_conditions
                }
            }
        },

        # Highest number of matching fields first
        {
            "$sort": {
                "_matchScore": -1
            }
        },

        # We only need the best match
        {
            "$limit": 1
        }
    ]

    result = next(collection.aggregate(pipeline), None)

    # ---------------------------------------------------------
    # No document found
    # ---------------------------------------------------------

    if not result:
        print("\n[DATABASE ERROR]: No result found for the tool Current_Weather_Forecast")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": arguments
        }

    # Remove MongoDB internal fields
    result.pop("_id", None)
    result.pop("_matchScore", None)

    return result
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================


#=========================================================================================================
#           DISTRICT WISE WARNING
#--------------------------------------------------------------------------------------------------------
#
def district_wise_warning(**arguments) -> dict:

    # ---------------------------------------------------------
    # Normalize the arguments coming from the AI
    # ---------------------------------------------------------
    query = {}

    for key, value in arguments.items():
        if value is not None:
            query[key] = str(value).strip().lower()

    print("[FROM district_wise_warning()] → AI query:", query)

    collection = db["District_Wise_Warning"]

    # ---------------------------------------------------------
    # If AI didn't provide anything, don't query the database
    # ---------------------------------------------------------
    if not query:
        return {
            "success": False,
            "error": "No search parameters provided"
        }

    # ---------------------------------------------------------
    # Build a MongoDB aggregation pipeline
    #
    # Each matching field gives the document +1 score.
    # ---------------------------------------------------------

    score_conditions = []

    for field, value in query.items():

        score_conditions.append({
            "$cond": [
                {"$eq": [
                    {"$toLower": {"$toString": f"${field}"}},
                    value
                ]},
                1,
                0
            ]
        })

    pipeline = [

        # Calculate how many requested fields match
        {
            "$addFields": {
                "_matchScore": {
                    "$add": score_conditions
                }
            }
        },

        # Highest number of matching fields first
        {
            "$sort": {
                "_matchScore": -1
            }
        },

        # We only need the best match
        {
            "$limit": 1
        }
    ]

    result = next(collection.aggregate(pipeline), None)

    # ---------------------------------------------------------
    # No document found
    # ---------------------------------------------------------

    if not result:
        print("\n[DATABASE ERROR]: No result found for the tool district_wise_warning")
        return {
            "success": False,
            "error": "No forecast data found",
            "query": arguments
        }

    # Remove MongoDB internal fields
    result.pop("_id", None)
    result.pop("_matchScore", None)

    return result
#--------------------------------------------------------------------------------------------------------
#===========================================================================================================