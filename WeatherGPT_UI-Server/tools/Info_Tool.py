import json

TOOLS_INFO={
    "7Days_Forecast": '''
## Data Output
{
  Date: '2026-09-24',
  Station_Code: '53',
  Station_Name: 'Kanpur Airforce',
  Today_Max_temp: null,
  Today_Max_Departure_from_Normal: null,
  Previous_Day_Max_temp: '32.6',
  Previous_Day_Max_Departure_from_Normal: 'NA',
  Today_Min_temp: '25.0',
  Today_Min_Departure_from_Normal: 'NA',
  Past_24_hrs_Rainfall: '3.40',
  Relative_Humidity_at_0830: '84',
  Relative_Humidity_at_1730: null,
  Previous_Day_Relative_Humidity_at_1730: '81',
  Sunset_time: '18:04',
  Sunrise_time: '05:58',
  Moonset_time: '03:29',
  Moonrise_time: '16:39',
  Todays_Forecast_Max_Temp: '31.0',
  Todays_Forecast_Min_temp: '24.0',
  Todays_Forecast: 'Partly cloudy sky with one or two spells of rain or thundershowers',
  Day_2_Max_Temp: '29.0',
  Day_2_Min_temp: '24.0',
  Day_2_Forecast: 'Generally cloudy sky with a few spells of rain or thundershowers',
  Day_3_Max_Temp: '30.0',
  Day_3_Min_temp: '24.0',
  Day_3_Forecast: 'Generally cloudy sky with one or two spells of rain or thundershowers',
  Day_4_Max_Temp: '31.0',
  Day_4_Min_temp: '24.0',
  Day_4_Forecast: 'Partly cloudy sky',
  Day_5_Max_Temp: '32.0',
  Day_5_Min_temp: '25.0',
  Day_5_Forecast: 'Partly cloudy sky',
  Day_6_Max_Temp: '33.0',
  Day_6_Min_temp: '25.0',
  Day_6_Forecast: 'Partly cloudy sky',
  Day_7_Max_Temp: '33.0',
  Day_7_Min_temp: '25.0',
  Day_7_Forecast: 'Partly cloudy sky',
  Latitude: '26.416666666',
  Longitude: '80.383333333',
  city: 'jajmau',
  village: null,
  district: 'kanpur nagar',
  state: 'uttar pradesh'
}

    | Field | Description |
| --- | --- |
| Date | Date of Observation in YYYY-mm-dd |
| Station_Code | Station Code is unique for each station |
| Station_Name | Station name |
| Today_Max_temp | Max Temp records at 1730 Hr IST (oC) |
| Today_Max_Departure_from_Normal | Departure of today max temp from normal (oC) |
| Previous_Day_Max_temp | Max Temp of previous day records at 1730 Hr IST (oC) |
| Previous_Day_Max_Departure_from_Normal | Departure of previous day max temp from normal (oC) |
| Today_Min_temp | Min Temp records at 0530 Hr IST (oC) |
| Today_Min_Departure_from_Normal | Departure of today min temp from normal (oC) |
| Past_24_hrs_Rainfall | Recorded from 0830 hrs IST of previous day to 0830 hrs IST of today |
| Relative_Humidity_at_0830 | Relative Humidity recorded at 0830 hrs (%) |
| Relative_Humidity_at_1730 | Relative Humidity recorded at 1730 hrs (%) |
| Previous_Day_Relative_Humidity_at_1730 | Relative Humidity of previous day recorded at 1730 hrs (%) |
| Sunset_time | Sunset Time |
| Sunrise_time | Sunrise Time |
| Moonset_time | Moonset Time |
| Moonrise_time | Moonrise Time |
| Todays_Forecast_Max_Temp | Forecasted Max Temp of Day-1 (i.e. Today) (oC) |
| Todays_Forecast_Min_temp | Forecasted Min Temp of Day-1 (i.e. Today) (oC) |
| Todays_Forecast | Weather Forecast of Day-1 (i.e. Today) |
| Day_2_Max_Temp | Forecasted Max Temp of Day-2 (oC) |
| Day_2_Min_temp | Forecasted Min Temp of Day-2 (oC) |
| Day_2_Forecast | Weather Forecast of Day-2 |
| Day_3_Max_Temp | Forecasted Max Temp of Day-3 (oC) |
| Day_3_Min_temp | Forecasted Min Temp of Day-3 (oC) |
| Day_3_Forecast | Weather Forecast of Day-3 |
| Day_4_Max_Temp | Forecasted Max Temp of Day-4 (oC) |
| Day_4_Min_temp | Forecasted Min Temp of Day-4 (oC) |
| Day_4_Forecast | Weather Forecast of Day-4 |
| Day_5_Max_Temp | Forecasted Max Temp of Day-5 (oC) |
| Day_5_Min_temp | Forecasted Min Temp of Day-5 (oC) |
| Day_5_Forecast | Weather Forecast of Day-5 |
| Day_6_Max_Temp | Forecasted Max Temp of Day-6 (oC) |
| Day_6_Min_temp | Forecasted Min Temp of Day-6 (oC) |
| Day_6_Forecast | Weather Forecast of Day-6 |
| Day_7_Max_Temp | Forecasted Max Temp of Day-7 (oC) |
| Day_7_Min_temp | Forecasted Min Temp of Day-7 (oC) |
| Day_7_Forecast | Weather Forecast of Day-7 |
| Latitude | Station latitude |
| Longitude | Station longitude |
''',

"Current_Weather_Forecast":'''
## Data Format
{
  'Station Id': '42724',
  Station: 'Agartala',
  'Date of Observation': '2026-09-24',
  Time: '21',
  'Mean Sea Level Pressure': '1009',
  'Wind Direction': '50',
  'Wind Speed KMPH': '1.9',
  Temperature: '27',
  'Weather Code': '10',
  Nebulosity: '6',
  Humidity: '89',
  'Last 24 hrs Rainfall': '0',
  'Feel Like': '30.9',
  WEATHER_ICON: NumberInt('500'),
  WEATHER_MESSAGE: 'Mist',
  BACKGROUND: null,
  BACKGROUND_URL: null,
  Sunrise: '05:14',
  Sunset: '17:19',
  Moonrise: '16:25',
  Moonset: '03:42',
  city: 'agartala',
  village: null,
  district: 'west tripura',
  state: 'tripura',
  date: '2026-09-24'
}


## Weather Code Description
| Weather Code | Description |
| --- | --- |
| 01 | Clouds generally dissolving or becoming less developed |
| 02 | State of sky on the whole unchanged |
| 03 | Clouds generally forming or developing |
| 04 | Visibility reduced by smoke (e.g. veldt/forest fires, industrial smoke, volcanic ashes) |
| 05 | Haze |
| 06 | Widespread dust in suspension in the air, not raised by wind at or near the station |
| 07 | Dust or sand raised by wind at or near the station, no well-developed whirl(s), no duststorm/sandstorm seen |
| 08 | Well-developed dust/sand whirl(s) at or near station, but no duststorm/sandstorm |
| 09 | Duststorm or sandstorm within sight |
| 10 | Mist |
| 11 | Patches of shallow fog/ice fog at station (not deeper than about 2 m on land / 10 m at sea) |
| 12 | More or less continuous shallow fog/ice fog at station |
| 13 | Lightning visible, no thunder heard |
| 14 | Precipitation within sight, not reaching ground/sea surface |
| 15 | Precipitation within sight, reaching ground/sea, but distant (> 5 km) |
| 16 | Precipitation within sight, reaching ground/sea, near but not at station |
| 17 | Thunderstorm, no precipitation at observation time |
| 18 | Squalls at or within sight during preceding hour / at observation |
| 19 | Funnel cloud(s) at or within sight during preceding hour / at observation |
| 20 | Drizzle (not freezing) or snow grains not falling as showers |
| 21 | Rain (not freezing) not falling as showers |
| 22 | Snow not falling as showers |
| 23 | Rain and snow / ice pellets type (a), not falling as showers |
| 24 | Freezing drizzle / freezing rain not falling as showers |
| 25 | Showers of rain |
| 26 | Showers of snow, or rain and snow |
| 27 | Showers of hail, or rain and hail |
| 28 | Fog or ice fog |
| 29 | Thunderstorm (with or without precipitation) |
| 30 | Slight/moderate duststorm or sandstorm - decreased during preceding hour |
| 31 | Slight/moderate duststorm or sandstorm - no appreciable change |
| 32 | Slight/moderate duststorm or sandstorm - begun/increased during preceding hour |
| 33 | Severe duststorm or sandstorm - decreased during preceding hour |
| 34 | Severe duststorm or sandstorm - no appreciable change |
| 35 | Severe duststorm or sandstorm - begun/increased during preceding hour |
| 36 | Slight/moderate blowing snow generally low (below eye level) |
| 37 | Heavy drifting snow generally low (below eye level) |
| 38 | Slight/moderate blowing snow generally high (above eye level) |
| 39 | Heavy drifting snow generally high (above eye level) |
| 40 | Fog/ice fog at a distance, not at station during preceding hour |
| 41 | Fog or ice fog in patches |
| 42 | Fog/ice fog, sky visible, becoming thinner |
| 43 | Fog/ice fog, sky invisible, becoming thinner |
| 44 | Fog/ice fog, sky visible, no appreciable change |
| 45 | Fog/ice fog, sky invisible, no appreciable change |
| 46 | Fog/ice fog, sky visible, begun/become thicker |
| 47 | Fog/ice fog, sky invisible, begun/become thicker |
| 48 | Fog depositing rime, sky visible |
| 49 | Fog depositing rime, sky invisible |
| 50 | Drizzle, not freezing, intermittent slight |
| 51 | Drizzle, not freezing, continuous slight |
| 52 | Drizzle, not freezing, intermittent moderate |
| 53 | Drizzle, not freezing, continuous moderate |
| 54 | Drizzle, not freezing, intermittent heavy (dense) |
| 55 | Drizzle, not freezing, continuous heavy (dense) |
| 56 | Drizzle, freezing, slight |
| 57 | Drizzle, freezing, moderate or heavy (dense) |
| 58 | Drizzle and rain, slight |
| 59 | Drizzle and rain, moderate or heavy |
| 60 | Rain, not freezing, intermittent slight |
| 61 | Rain, not freezing, continuous slight |
| 62 | Rain, not freezing, intermittent moderate |
| 63 | Rain, not freezing, continuous moderate |
| 64 | Rain, not freezing, intermittent heavy |
| 65 | Rain, not freezing, continuous heavy |
| 66 | Rain, freezing, slight |
| 67 | Rain, freezing, moderate or heavy |
| 68 | Rain, or drizzle and snow, slight |
| 69 | Rain, or drizzle and snow, moderate or heavy |
| 70 | Intermittent fall of snowflakes, slight |
| 71 | Continuous fall of snowflakes, slight |
| 72 | Intermittent fall of snowflakes, moderate |
| 73 | Continuous fall of snowflakes, moderate |
| 74 | Intermittent fall of snowflakes, heavy |
| 75 | Continuous fall of snowflakes, heavy |
| 76 | Ice prisms (with or without fog) |
| 77 | Snow grains (with or without fog) |
| 78 | Isolated star-like snow crystals (with or without fog) |
| 79 | Ice pellets, type (a) |
| 80 | Rain shower(s), slight |
| 81 | Rain shower(s), moderate or heavy |
| 82 | Rain shower(s), violent |
| 83 | Shower(s) of rain and snow mixed, slight |
| 84 | Shower(s) of rain and snow mixed, moderate or heavy |
| 85 | Snow shower(s), slight |
| 86 | Snow shower(s), moderate or heavy |
| 87 | Shower(s) of snow pellets/ice pellets type (b), slight |
| 88 | Shower(s) of snow pellets/ice pellets type (b), moderate or heavy |
| 89 | Shower(s) of hail, with/without rain or rain and snow mixed, not associated with thunder, slight |
| 90 | Shower(s) of hail, with/without rain or rain and snow mixed, not associated with thunder, moderate or heavy |
| 91 | Slight rain at observation; thunderstorm during preceding hour but not at observation |
| 92 | Moderate/heavy rain at observation; thunderstorm during preceding hour but not at observation |
| 93 | Slight snow/rain+snow mixed/hail at observation; thunderstorm during preceding hour but not at observation |
| 94 | Moderate/heavy snow/rain+snow mixed/hail at observation; thunderstorm during preceding hour but not at observation |
| 95 | Thunderstorm, slight/moderate, without hail, with rain and/or snow at observation |
| 96 | Thunderstorm, slight/moderate, with hail at observation |
| 97 | Thunderstorm, heavy, without hail, with rain and/or snow at observation |
| 98 | Thunderstorm combined with duststorm/sandstorm at observation |
| 99 | Thunderstorm, heavy, with hail at observation |
''',

"District_Wise_Warning":'''
| Field | Description |
| --- | --- |
| Obj_id | Object ID for a district |
| Date | Date of Issue |
| UTC | Time of Issue in UTC |
| District | District Name |
| Day_1 | Warning Code for Day 1 (multiple codes can be added separated with ',') |
| Day_2 | Warning Code for Day 2 (multiple codes can be added separated with ',') |
| Day_3 | Warning Code for Day 3 (multiple codes can be added separated with ',') |
| Day_4 | Warning Code for Day 4 (multiple codes can be added separated with ',') |
| Day_5 | Warning Code for Day 5 (multiple codes can be added separated with ',') |
| Day1_Color | Color code as 1, 2, 3 or 4 |
| Day2_Color | Color code as 1, 2, 3 or 4 |
| Day3_Color | Color code as 1, 2, 3 or 4 |
| Day4_Color | Color code as 1, 2, 3 or 4 |
| Day5_Color | Color code as 1, 2, 3 or 4 |

## Warning Code
| Warning Code | Description |
| --- | --- |
| 1 | No Warning |
| 2 | Heavy Rain |
| 3 | Heavy Snow |
| 4 | Thunderstorm & Lightning, Squall etc |
| 5 | Hailstorm |
| 6 | Dust Storm |
| 7 | Dust Raising Winds |
| 8 | Strong Surface Winds |
| 9 | Heat Wave |
| 10 | Hot Day |
| 11 | Warm Night |
| 12 | Cold Wave |
| 13 | Cold Day |
| 14 | Ground Frost |
| 15 | Fog |
| 16 | Very Heavy Rain |
| 17 | Extremely Heavy Rain |

## Day Color Code Description
| Color Code | Description |
| --- | --- |
| 1 | #FF0000 (Red) |
| 2 | #ffa500 (Orange) |
| 3 | #ffff00 (Yellow) |
| 4 | #7cfc00 (Green) |

''',
"District_Wise_Nowcast":'''
| Field | Value | Description |
| --- | --- | --- |
| Station | Station name | Station name |
| Date | YYYY-mm-dd | Date of warning issued |
| Cat1 | 1 | No Weather |
| Cat2 | 2 | Light rain: < 5 mm/hr |
| Cat3 | 3 | Light snow: < 5 cm/hr |
| Cat4 | 4 | Light Thunderstorms with maximum surface wind speed less than 40 kmph (in gusts) |
| Cat5 | 5 | Slight dust storm: wind speed up to 41 kmph and visibility less than 1000 m but more than 500 m |
| Cat6 | 6 | Low cloud to ground Lightning probability (< 30%) |
| Cat7 | 7 | Moderate rain: 5-15 mm/hr |
| Cat8 | 8 | Moderate snow: 5-15 cm/hr |
| Cat9 | 9 | Moderate Thunderstorms with maximum surface wind speed between 41 - 61 kmph (in gusts) |
| Cat10 | 10 | Moderate dust storm: wind speed between 41-61 kmph and visibility between 200 and 500 m due to dust |
| Cat11 | 11 | Moderate cloud to ground Lightning probability (30 - 60%) |
| Cat12 | 12 | Heavy rain: > 15 mm/hr |
| Cat13 | 13 | Heavy snow: > 15 cm/hr |
| Cat14 | 14 | Severe Thunderstorms with maximum surface wind speed 62 - 87 kmph (in gusts) |
| Cat15 | 15 | Very Severe Thunderstorms with maximum surface wind speed > 87 kmph (in gusts) |
| Cat16 | Text | Other Warnings (text warnings can be entered) |
| Cat17 | 31 | Thunderstorms with Hail |
| Cat18 | 32 | Severe dust storm: surface wind speed (in gusts) exceeding 61 kmph and visibility less than 200 m due to dust |
| Cat19 | 33 | High cloud to ground Lightning probability (> 60%) |
| message | text | Consolidated warning message |
| toi | HHmm | Time of issue of warning |
| Vupto | HHmm | Warning valid upto |
| color | 1, 2, 3 or 4 | Color code for warning severity |

## Color Code Note
| Color Code | Usage | Color |
| --- | --- | --- |
| 1 | Cat1 | Green (#008000) |
| 2 | Cat2 to Cat6 | Yellow (#FFFF00) |
| 3 | Cat7 to Cat11 | Orange (#FFA500) |
| 4 | Cat12 to Cat19 | Red (#ff0000) |
''',

"District_wise_Rainfall" : '''

## Category used for rainfall
| Code | Description |
| --- | --- |
| LE | Large Excess (60% or more) |
| E | Excess (20% to 59%) |
| N | Normal (-19% to 19%) |
| D | Deficient (-59% to -20%) |
| LD | Large Deficient (-99% to -60%) |
| NR | No Rain (-100%) |
| ND | No Data |
'''   
}

def get_tools_information(conv_dict, **arguments) -> str:
    print(f"[FROM get_tools_information]: AI's query: {arguments}")
    # The AI will get ans for only one tool at a time
    #AI will call multiple times if it wants.
    tool_name = arguments.get("tool_name")
    if TOOLS_INFO.get(tool_name):
        return {
            # "success":True,   Tool_caller-id is already sent with the tool. AI will which tool's response that is
            tool_name: TOOLS_INFO[tool_name]
            }
    else:
        return {
        "success": False,
        "error": "No forecast data found",
        "query": arguments
    }
    