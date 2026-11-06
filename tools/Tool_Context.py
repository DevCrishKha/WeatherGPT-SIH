# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

TOOLS = [
    {
            "type": "function",
            "function": {
                "name": "7Days_Forecast",
                "description": (
                    "Gives 7days weather foresact data from the IMD API including the date provided and the Next 6 days."
                    "You have to provide the Date which is the mandatory field and then you can give any location info like city, village, district, state, Station_Code to get the 7Days forecast data."
                    "You only get result of one station from this tool, if you need multiple stations data you need to call the tool multiple times."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Date": {
                            "type": "string",
                            "description": (
                                "The Date field is mandatory for searching, Date should be in this format 2026-09-24"
                            ),
                        },
                        "Station_Code": { "type": "string", },
                        "city": { "type": "string", },
                        "village": { "type": "string", },
                        "subdistrict": { "type": "string", "description":"subdistrict is also known as tehsil or taluka in India" },
                        "district": { "type": "string", },
                        "state": { "type": "string" },
                    },
                    "required": [ "Date", ],
                    "additionalProperties": False,
                },
            },
        },
    {
                "type": "function",
                "function": {
                    "name": "Current_Weather_Forecast",
                    "description": (
                        "This tool gives current forecast data of a place you want from the IMD API."
                        "You can also use this to get weather for past dates."
                        ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": (
                                    "The Date field is mandatory for searching, Date should be in this format 2026-09-24."
                                    "And use the parameter 'date' and not 'Date' "
                                ),
                            },
                            "Station Id": { "type": "string", },
                            "city": { "type": "string", },
                            "village": { "type": "string", },
                            "subdistrict": { "type": "string", "description":"subdistrict is also known as tehsil or taluka in India" },
                            "district": { "type": "string", },
                            "state": { "type": "string" },
                        },
                        "required": [ "Date", ],
                        "additionalProperties": False,
                    },
                },
            },
    {
                    "type": "function",
                    "function": {
                        "name": "Get_Tools_Info",
                        "description": (
                            "A tool might output certain information which is hard to interpret. Pass the name of the tool whose information you need."
                            "Whenever you feel like an API gives a  response which you don't understand use this tool."
                            "This tool contains information from the API's documentation."
                            ),
                        "parameters": {
                            "type": "object",
                            
                            "properties": {
                                "tool_name": {
                                    "type": "string",
                                    "description": (
                                        "If you do not understand the data output from a tool,"
                                        "Pass the tool name here as it is."
                                    ),
                            },
                            "required": [ "tool_name", ],
                            "additionalProperties": False,
                            
                        },
                    },
                },
    },
    {
                "type": "function",
                "function": {
                    "name": "District_Wise_Warning",
                    "description": (
                        "Whenever user asks for weather warnings, use this tool to find the weather warning regarding to a district."
                        ),
                    "parameters": {
                        "type": "object",
                        
                        "properties": {
                            "Date": {
                                "type": "string",
                                "description": (
                                    "The Date field is mandatory for searching, Date should be in this format 2026-09-24."
                                ),
                        },
                            "District":{ 
                                "type":"string", 
                                "description":(
                                "Search with the keyword 'District' and not 'district' "
                                ) 
                                        },
                        "required": [ "Date", ],
                        "additionalProperties": False,
                        
                    },
                },
            },
        }
   
]

def get_tool_context() -> dict:
    return TOOLS