TOOLS = [
    {
                        "type": "function",
                        "function": {
                            "name": "Get_Date-Time_Location",
                            "description": (
                                "Use this tool to get the current Date, current Time and location of the user."
                                "**EVERYTIME A USER ENTERS A DATE AND A DAY OF THE WEEK, CORRECT THE USER BY TELLING THEM THE CURRENT DATE & DAY OF THE WEEK AND WHICH DAY OF THE WEEK THAT STATED DATE WILL BE**"
                                ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                            },
                            "additionalProperties": False,
                        },
                    }
                },
    {
            "type": "function",
            "function": {
                "name": "Forecast_7Days",
                "description": (
                    "Gives 7days weather foresact data from the IMD API including the date provided and the Next 6 days."
                    "**NO API CONTAINS DATA AHEAD OF CURRENT DATE, CURRENT DATE IS THE MAXIMUM DATE YOU CAN USE IN YOUR SEARCH. ELSE YOU A PAST DATE SMARTLY.**"
                    "You have to provide the Date which is the mandatory field and then you can give any location info like city, village, district, state, Station_Code to get the 7Days forecast data."
                    "You only get result of one station from this tool, if you need multiple stations data you need to call the tool multiple times."
                    "**Use this when user asks for a forecast ahead of date. SEARCH THE DATA BASE USING CURRENT DATE AND YOU WILL GET FORECAST OF TODAY + NEXT 6 DAYS**"
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
                        
                          "Station_Code": {
                            "type": "string",
                          },
                          "Station_Name": {
                            "type": "string",
                          },
                          "Today_Max_temp": {
                            "type": "string",
                            "description": "Maximum temperature recorded today"
                          },
                          "Today_Max_Departure_from_Normal": {
                            "type": "string",
                            "description": "Departure of today's maximum temperature from the normal value"
                          },
                          "Today_Min_temp": {
                            "type": "string",
                            "description": "Minimum temperature recorded today"
                          },
                          "Today_Min_Departure_from_Normal": {
                            "type": "string",
                            "description": "Departure of today's minimum temperature from the normal value"
                          },
                          "Past_24_hrs_Rainfall": {
                            "type": "string",
                            "description": "Rainfall recorded during the past 24 hours"
                          },
                          "Relative_Humidity_at_0830": {
                            "type": "string",
                            "description": "Relative humidity measured at 08:30"
                          },
                          "Relative_Humidity_at_1730": {
                            "type": "string",
                            "description": "Relative humidity measured at 17:30"
                          },
                          "Sunset_time": {
                            "type": "string",
                            "description": "Local sunset time"
                          },
                          "Sunrise_time": {
                            "type": "string",
                            "description": "Local sunrise time"
                          },
                          "Moonset_time": {
                            "type": "string",
                            "description": "Local moonset time"
                          },
                          "Moonrise_time": {
                            "type": "string",
                            "description": "Local moonrise time"
                          },
                          "Todays_Forecast_Max_Temp": {
                            "type": "string",
                            "description": "Forecast maximum temperature for today"
                          },
                          "Todays_Forecast_Min_temp": {
                            "type": "string",
                            "description": "Forecast minimum temperature for today"
                          },
                          "Todays_Forecast": {
                            "type": "string",
                            "description": "Weather forecast for today"
                          },
                          "city": {
                            "type": "string"
                          },
                          "village": {
                            "type": "string"
                          },
                          "subdistrict": {
                            "type": "string",
                            "description": "Subdistrict is also known as tehsil or taluka in India"
                          },
                          "district": {
                            "type": "string"
                          },
                          "state": {
                            "type": "string"
                          }
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
                            "Date": {
                                "type": "string",
                                "description": (
                                    "The Date field is mandatory for searching, Date should be in this format 2026-09-24."
                                    "And use the parameter 'date' and not 'Date' "
                                ),
                            },
                            
                            "Station Id": {
                                "type": "string",
                                "description": "Unique identifier of the weather station"
                            },
                            "Station": {
                                "type": "string",
                                "description": "Name of the weather station"
                            },
                            "Date of Observation": {
                                "type": "string",
                                "description": "Date on which the weather observation was recorded in YYYY-MM-DD format"
                            },
                            "Time": {
                                "type": "string",
                                "description": "Observation time in hours"
                            },
                            "Mean Sea Level Pressure": {
                                "type": "string",
                                "description": "Mean sea level atmospheric pressure"
                            },
                            "Wind Direction": {
                                "type": "number",
                                "description": "Wind direction"
                            },
                            "Wind Speed KMPH": {
                                "type": "number",
                                "description": "Wind speed in kilometers per hour"
                            },
                            "Temperature": {
                                "type": "string",
                                "description": "Observed temperature"
                            },
                            "Weather Code": {
                                "type": "string",
                                "description": "Weather condition code"
                            },
                            "Nebulosity": {
                                "type": "string",
                                "description": "Amount of cloudiness or nebulosity"
                            },
                            "Humidity": {
                                "type": "string",
                                "description": "Relative humidity"
                            },
                            "Last 24 hrs Rainfall": {
                                "type": "string",
                                "description": "Rainfall recorded during the last 24 hours"
                            },
                            "Feel Like": {
                                "type": "string",
                                "description": "Feels-like or apparent temperature"
                            },
                            "Sunrise": {
                                "type": "string",
                                "description": "Local sunrise time"
                            },
                            "Sunset": {
                                "type": "string",
                                "description": "Local sunset time"
                            },
                            "Moonrise": {
                                "type": "string",
                                "description": "Local moonrise time"
                            },
                            "Moonset": {
                                "type": "string",
                                "description": "Local moonset time"
                            },
                            "city": {
                                "type": "string"
                            },
                            "village": {
                                "type": "string"
                            },
                            "district": {
                                "type": "string"
                            },
                            "subdistrict": {
                                "type": "string",
                                "description": "Subdistrict is also known as tehsil or taluka in India"
                            },
                            "state": {
                                "type": "string"
                            },

                        },
                        "required": [ "Date", ],
                        "additionalProperties": False,
                    },
                }
            },
    {
                    "type": "function",
                    "function": {
                        "name": "Get_Tools_Info",
                        "description": (
                            "A tool might output certain information which is hard to interpret. Pass the name of the tool whose information you need."
                            "Whenever you feel like an API gives a  response which you don't understand use this tool."
                            "This tool contains information from the API's documentation."
                            "You can even call this tool to see how 'Forecast_7Days' & 'Current_Weather_Forecast' or other tool's output looks."
                            "Call this tool specially before calling the 'filter_API_Response_by' tool to see the output of a forecast tool first."
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
                            }
                        },
                            "required": [ "tool_name", ],
                            "additionalProperties": False,
                    }
                }
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
                    },
                        "required": [ "Date", ],
                        "additionalProperties": False,
                },
            }
        },
    {
            "type": "function",
            "function": {
                "name": "Render_7Days_Forecas_Data",
                "description": (
                    "Use this to render the 7Days forecast data to show the user visualy."
                    "When user tells you to render the weather forecast data visually, use this tool."
                    "You don't need to call another tool to get the forecast data and then render, you can pass the Date, state, district, etc here directly."
                    "You just have to pass the Date, state, district, etc. This tool will fetch the forecast information and render it to HTML and show to the user."
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
        }
    },
    {
                "type": "function",
                "function": {
                    "name": "Point_on_Map",
                    "description": (
                        "Users have a map in front of them. Use this tool to point to a city, district or state on that map."
                        ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": (
                                "Takes any location information, any Indian city, district or state."
                                "Only point to a city, district or state because the tool is only capable of that."
                                "If a user forces too much then try to plot a place which is unique like a monument, etc else the tool will get confuse and point to something completely wrong."
                            ),
                        },
                        "color":{
                            "type": "string",
                            "description": (
                                "using this color the overlay will be added on the map in the user's UI"
                            ),
                        },
                    },
                    "required": [ "location", "color" ],
                    "additionalProperties": False,
                },
            }
        },
    {
                    "type": "function",
                    "function": {
                        "name": "filter_API_Response_and_Plot_on_Map",
                        "description": (
                            "Use this tool to filter a specific field from the API response. For example: Temperature 0*C-34*C. An API response contains weather info of multiple stations. Use this to filter out the responses."
                            "As an API contains 1000s of fields the data is not given to you to save the context window instead the data is sent directly to the user's UI after filtering and creating visual components like graphs & charts."
                            "The user is also able to see the location of the 1000s of IMD stations on the map."
                            "You will need to provide the collection_name, field ('Today_Max_temp', etc), start_value & end_value for this tool."
                            "The API gives the values inside fields in string format, this tool converts them to integer values before applying the filter."
                            "The user doesn't know the fields in the 7Days API response. First get a clear understanding on what are the different fields inside the API response using 'Get_Tools_Info' Then use a key that is present in the actual json as field for this tool. "
                            "**THIS TOOLS ALSO RETURNS YOU THE NUMBER OF RESULTS MATCHING THE FILTER BUT IT DOES NOT GIVE YOU THE RESULTS, USE THIS TOOL FOR THE USER BUT IF THE USER INSISTS 2ND TIME TELL THE USER THAT YOU CANNOT ANALYZE THE RESULT OF THIS FILTER. BUT THE DATA IS 100% REAL IMD DATA. **"
                            ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "collection_name": {
                                "type": "string",
                                "description": (
                                    "For collection_name the two possible values are '7Days_Station_Forecast' & 'Current_Weather_Forecast' "
                                    "To know the value of possible fields call the 'Get_Tools_Info' tool."
                                    ),
                            },
                            "fields":{ "type":"string","description":("The user doesn't know the fields in the 7Days API response. First get a clear understanding on what are the different fields inside the API response using 'Get_Tools_Info' Then use a key that is present in the actual json as field for this tool. ") },
                            "start_value":{ "type":"number" },
                            "end_value":{ "type":"number" },
                            "Date":{ "type":"string" },
                            "color":{ "type":"string","description":("This will be the color using which the tool will point the places on the map.")  },
                        },
                        "required": [ "collection_name", "Date", "fields", "start_value", "end_value", "color"],
                        "additionalProperties": False,
                    },
                }
            }
   
]

def get_tool_context() -> dict:
    return TOOLS