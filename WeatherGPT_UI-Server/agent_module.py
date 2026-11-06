# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

import json
import datetime
from typing import Any, Callable, Dict
from tools.Tool_Context import get_tool_context
from tools.Tools import Forecast_7Days, Current_Weather_Forecast, district_wise_warning, plot_on_map, show_filtered_results, get_datetime
from tools.Info_Tool import get_tools_information
from tools.HTML_Render import Forecast_7Days_HTML
from dotenv import load_dotenv
import os
import logging
import traceback
from rich.console import Console
from rich.markdown import Markdown
import requests
import random

from openai import OpenAI



#=============================================================
#               <{<<  CONFIGURATION  >>}>
#-------------------------------------------------------------

# --- TOOLS CONTEXT ---
TOOLS = get_tool_context()
MAXIMUM_ROUNDS=10

#  --- CONFIGURE ---
load_dotenv('.env')
API_KEY = os.getenv("GEMINI_API_KEY")
NVIDIA_API = os.getenv("NVIDIA_API_KEY")
GROQ_API = os.getenv("GROQ_API_KEY")


# client = OpenAI(
#     api_key=API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

# client = OpenAI(
#   base_url = "https://integrate.api.nvidia.com/v1",
#   api_key = NVIDIA_API
# )

client = OpenAI(
  base_url = "https://api.groq.com/openai/v1",
  api_key = GROQ_API 
)

MODEL="openai/gpt-oss-120b" 
# MODEL="z-ai/glm-5.3-flash",
# MODEL="gemini-3.8-flash",

print("Prepared the client...")
#---------------------------------------------------------------
#              </{<<  CONFIGURATION  >>}>
#=============================================================



# ============================================================
# SYSTEM PROMPT
# ============================================================
'''  10. Always give a proof of your answer by using the show_table_to_user tool to send the API weather data to the user as a table.  '''
SYSTEM_PROMPT = f"""
You are WeatherGPT.

**NO API CONTAINS DATA AHEAD OF CURRENT DATE, CURRENT DATE IS THE MAXIMUM DATE YOU CAN USE IN YOUR SEARCH. ELSE YOU A PAST DATE SMARTLY.**
**ALWAYS CALCULATE IF THE DATE AND DAY-OF-WEEK ENTERED BY USER IS VALID OR THERE IS A MISTAKE AND IF THE DAY-OF-THE-WEEK DOES NOT MATCH WITH THAT DATE.**

You have access to tools that retrieve weather data.

Rules:

1. Use tools whenever the user's request requires data.

2. Do not invent weather data.

3. You may call multiple tools if necessary.

4. You may use the result of one tool to decide what tool to call next.

5. There are different API tools for different information, ask the user for the specific information you need to retrieve weather data from a tool. You can call the forecast tool using city, district or state.

6. Do not expose internal tool-calling details to the user.

7. Once you have enough information, provide a clear conversational answer.

8. If you can't get data from one API call another API which can contain the same data, example: Current_Weather_Data & 7Days_Forecast contains the same data for different number of days.

9. If you can't find the data in the API response say it clearly to the user. **Do not try to call the API multiple times**. The database pipeline is implemented such that you get the output in a single search.

10. **Do not run a tool 2nd time with the same parameter. If the tool gives an error, explain the problem to the user kindly.**
    **The database is implemented to first match the date and then match all the location information, and if it fails it tries to match the maximum number of location information like city, district, state, etc.** **Do never call a tool twice**
    **After getting data from the database check the Date & location information first and compaire to what the user asked for. If there is any difference, explain to the user exactly that data is not present in the database.**
    **IF a tool returns 'success':False then do not try again.**

11. Call multiple tools at once when possible. Do not wait for one tool's output to call the next tool if the they are not dependent.

12. Never resolve a query without any text response, even if you are only rendering forecast data.
"""

# --- MAKING MESSAGES A GLOBAL VARIABLE ---
messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f""
        }
    ]

#==========================================================================================================================
# TOOL REGISTRY
#-------------------------------------------------------------------------------------------------------------------------
#
# This maps the name the AI sees to the actual python function name.
#
TOOL_REGISTRY: dict[str, Callable] = {
    "Forecast_7Days": Forecast_7Days,
    "Current_Weather_Forecast": Current_Weather_Forecast,
    "Get_Tools_Info": get_tools_information,
    "District_Wise_Warning":district_wise_warning,
    "Render_7Days_Forecas_Data": Forecast_7Days_HTML,
    "Point_on_Map":plot_on_map,
    "filter_API_Response_and_Plot_on_Map":show_filtered_results,
    "Get_Date-Time_Location":get_datetime
}

TOOL_CALL_STATUS_MESSAGE:dict [str, Callable] = {
    "Forecast_7Days": "Calling API for 7days weather forecast..",
    "Current_Weather_Forecast": "IMD Current Weather Forecast API  ...",
    "Get_Tools_Info": "Reading IMD documentation...",
    "District_Wise_Warning": "Checking district wise warning...",
    "Render_7Days_Forecas_Data": "Rendering API content 7Days → HTML",
    "Point_on_Map":"Pointing on the Map, open to see.",
    "filter_API_Response_and_Plot_on_Map":"Applying the Filter..."
}

def update_tool_status(tool_name, conv_dict):    
    URL = "http://localhost:5000/get_tool_status"
    # 1. Prepare your custom internal authorization token header
    headers = {
        "Authorization": "Bearer YOUR_INTERNAL_TOKEN_HERE"  # Update this to match your _internal_token_ok() logic
    }
    # 2. The backend receives the json data and takes user_id, conversation_id, html from there
    if not TOOL_CALL_STATUS_MESSAGE.get(tool_name):
        status_msg = "Thinking.."
    else:
        status_msg = TOOL_CALL_STATUS_MESSAGE.get(tool_name)
    payload_data = {
        "user_id": conv_dict['user_id'],
        "message":status_msg
    }
    response = requests.post(URL, headers=headers, json=payload_data)
    
    # 5. Handle the server response
    if response.status_code == 200:
        pass
    else:
        print(f"--------------------------------------------------------------\n[TOOL STATUS ERROR] Failed to send status to frontend {response.status_code}: {response.text}\n--------------------------------------------")
#------------------------------------------------------------------------------------------------------------------------
#==========================================================================================================================


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(tool_name: str, arguments: dict, conv_dict: dict):

    # --------------------------------------------------------
    # Check whether the requested tool exists
    # --------------------------------------------------------

    function = TOOL_REGISTRY.get(tool_name)

    if function is None:

        return {
            "success": False,
            "error": (
                f"Unknown tool requested: {tool_name}"
            )
        }
        
    # --------------------------------------------------------
    # Execute the tool
    # --------------------------------------------------------

    try:
        # if tool_name == "7Days_Forecast":
        #     result = function(**arguments)
        #     return result
        # else:
        #     result = function(**arguments)
        #     return result
        
        result = function(conv_dict, **arguments)
        
        return result

    except Exception as e:

        # Log the real exception on the server
        print(
            f"\n[TOOL ERROR] {tool_name}:"
        )

        traceback.print_exc()

        # Do NOT crash the whole AI loop.
        #
        # Instead, return an error to the model so that
        # it can potentially recover or use another tool.

        return {
            "success": False,
            "error": (
                f"Tool '{tool_name}' failed."
            )
        }

#================================================================================================================
#                      <{<<  AI HARNESS  >>}>
#----------------------------------------------------------------------------------------------------------------

# ============================================================
# ONE USER REQUEST
# ============================================================

def process_one_prompt(history: list, conv_dict: dict):
    # --------------------------------------------------------
    # Conversation for this request
    # --------------------------------------------------------

    messages.extend(history)


    # ========================================================
    #            TOOL-CALLING LOOP
    #
    # The AI can do maximum 3 rounds of reasoning before giving the ans
    # In the for loop round_number=1, 2, 3
    # --------------------------------------------------------

    for round_number in range(1, 10+1):

        print(  f"\n========== TOOL ROUND  {round_number}/{MAXIMUM_ROUNDS} =========="  )


        # ----------------------------------------------------
        # Ask Gemini
        # ----------------------------------------------------

        try:

            response = client.chat.completions.create(

                MODEL="openai/gpt-oss-120b",

                messages=messages,

                tools=TOOLS,

                tool_choice="auto",

                parallel_tool_calls=True
            )

        except Exception as e:

            print("\n[MODEL ERROR]")
            traceback.print_exc()

            return (
                "I encountered a problem while "
                "processing your request."
            )

        message = response.choices[0].message
        messages.append(message)
        
        # --- CHECK FOR FINAL ANSWER ---
        
        if not message.tool_calls:
            print( "\n[MODEL] Final answer generated."  )
            return message.content or ""
            
        # --- TOOL CALL ---
        
        print( f"[MODEL] Requested {len(message.tool_calls)} tool(s)" )

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name
            raw_arguments = ( tool_call.function.arguments )    # Converting into json → dict


            print( f"\n[MODEL CALLED → TOOL]: {tool_name}" )

            print( "[AI's TOOL ARGUMENTS]", raw_arguments )

            update_tool_status(tool_name, conv_dict)


            # ------------------------------------------------
            # Parse JSON raw arguments → dict
            # ------------------------------------------------

            try:
                arguments = json.loads( raw_arguments )

            except json.JSONDecodeError:
                print(
                    "[ERROR] Model produced invalid "
                    f"Invalid JSON arguments cannot be loaded to a dict.. Tool → '{tool_name}()'"
                )

                tool_result = {
                    "success": False,
                    "error": (
                        "Invalid JSON arguments "
                        "generated for the tool."
                    )
                }

            else:

                # --------------------------------------------
                # Execute tool
                tool_result = execute_tool( tool_name, arguments, conv_dict )
                # --------------------------------------------




            # ----------------------------------------------------------------------
            # Make sure result is JSON serializable Do not dump dict → json directly
            try:
                serialized_result = json.dumps( tool_result, default=str )

            except Exception:
                serialized_result = json.dumps({
                    "success": False,
                    "error":
                        "Tool returned "
                        "non-serializable data."
                })
            # ----------------------------------------------------------------------



            # ------------------------------------------------
            # Send tool result back to Gemini
            #
            messages.append({ 
                "role": "tool", 
                "tool_call_id": tool_call.id,
                "content":  serialized_result
            })
            # ------------------------------------------------
            
            
            with open("chat-history-Agent.json", "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=4, ensure_ascii=False, default=str)

            
    # ========================================================
    #           MAXIMUM TOOL ROUNDS REACHED
    
    # We have deliberately stopped the autonomous loop.
    # Do NOT silently continue forever.
    #
    print( "\n[MAX TOOL ROUNDS REACHED]" )  
        
    
    return (
        "I couldn't complete the request within the "
        "maximum number of data-retrieval steps."
    )
    # --------------------------------------------------------
    # ========================================================
    
#================================================================================================================
#                      </{<<  AI HARNESS  >>}>
#----------------------------------------------------------------------------------------------------------------


# ============================================================
#       INITIALIZATION POINT    
# ============================================================

def main(user_input, history, conv_dict):

    # ========================================================
    #       --- OUTER INFINITE LOOP ---
    # For a single user msg
    # This will also receive the conv_dict so that tools can 
    #   send content to the flask reatAPIs with info of the user's 
    #   socket room and conv_id for the specific chat history
    
    output = process_one_prompt(history, conv_dict)

    messages.clear()
    print("\n \nONE USER PROMPT EXECUTED")
    
    # Give a simple markdown output which will be appended to the chat-history
    return output

    # ========================================================
    
if __name__ == "__main__":
    
    print("=" * 60)
    print("WeatherGPT")
    print("Gemini + OpenAI SDK Tool Calling")
    print("=" * 60)
    print( "\nType 'exit' or 'quit' to stop.\n" )
    
    # We take the input from the user in the main function inside the infinite loop
    
    prompt=input("\nYou: ").strip()
    assert prompt, ("You did not enter anything")
    main(prompt)