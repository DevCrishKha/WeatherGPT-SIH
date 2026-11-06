# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.


import json
from datetime import datetime, date
from typing import Any, Callable, Dict
from tools.weather import get_current_weather, get_weather_alerts
from tools.Tool_Context import get_tool_context
from tools.Tools import Forecast_7Days, Current_Weather_Forecast, district_wise_warning
from tools.Tools2 import get_tools_information
from dotenv import load_dotenv
import os
import logging
import traceback
from rich.console import Console
from rich.markdown import Markdown

from openai import OpenAI

# --- TOOLS CONTEXT ---
TOOLS = get_tool_context()
MAXIMUM_ROUNDS=4

# ============================================================
#                   CONFIGURATION
#-------------------------------------------------------------
#
# --- CONFIGURE ---
load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set."
    )

# client = OpenAI(
#     api_key=API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)
#---------------------------------------------------------------
print("Prepared the client...")
# ============================================================


# ============================================================
# SYSTEM PROMPT
# ============================================================
'''  10. Always give a proof of your answer by using the show_table_to_user tool to send the API weather data to the user as a table.  '''
SYSTEM_PROMPT = """
You are WeatherGPT.

You have access to tools that retrieve weather data.

Rules:

1. Use tools whenever the user's request requires data.

2. Do not invent weather data.

3. You may call multiple tools if necessary.

4. You may use the result of one tool to decide what tool to call next.

5. There are different API tools for different information, ask the user for the specific information you need to retrieve weather data from a tool.

6. Do not expose internal tool-calling details to the user.

7. Once you have enough information, provide a clear conversational answer.

8. If you can't get data from one API call another API which can contain the same data, example: Current_Weather_Data & 7Days_Forecast contains the same data for different number of days.

9. If the available tools cannot provide the requested information, clearly explain to the user without trying multiple times calling the same tool.

10. Call multiple tools at once when possible. Do not wait for one tool's output to call the next tool if the they are not dependent.
"""

# --- MAKING MESSAGES A GLOBAL VARIABLE ---
messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]


# ==========================================================================================================================
# TOOL REGISTRY
# -------------------------------------------------------------------------------------------------------------------------
#
# This maps the name the AI sees to the actual python function name.
#
TOOL_REGISTRY: dict[str, Callable] = {
    "7Days_Forecast": Forecast_7Days,
    "Current_Weather_Forecast": Current_Weather_Forecast,
    "Get_Tools_Info": get_tools_information,
    "District_Wise_Warning":district_wise_warning
}
#------------------------------------------------------------------------------------------------------------------------
# ==========================================================================================================================


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(tool_name: str, arguments: dict):

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
        
        result = function(**arguments)
        
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



# ============================================================
# ONE USER REQUEST
# ============================================================

def process_one_prompt(user_input: str):
    # --------------------------------------------------------
    # Conversation for this request
    # --------------------------------------------------------

    messages.append(

        {
            "role": "user",
            "content": user_input
        }
    )


    # ========================================================
    #            TOOL-CALLING LOOP
    #
    # The AI can do maximum 3 rounds of reasoning before giving the ans
    # In the for loop round_number=1, 2, 3
    # --------------------------------------------------------

    for round_number in range(1, MAXIMUM_ROUNDS+1):

        print(  f"\n========== TOOL ROUND  {round_number}/{MAXIMUM_ROUNDS} ==========" )


        # ----------------------------------------------------
        # Ask Gemini
        # ----------------------------------------------------

        try:

            response = client.chat.completions.create(

                model="z-ai/glm-5.3-flash",

                messages=messages,

                tools=TOOLS,

                tool_choice="auto",

                # Prevent an accidental explosion of
                # parallel calls.
                #
                # Set True if your tools are designed to
                # safely execute in parallel.
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
                tool_result = execute_tool( tool_name, arguments )
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
    
# ============================================================
#       INITIALIZATION POINT    
# ============================================================

def main(prompt):

    # ========================================================
    #       --- OUTER INFINITE LOOP ---
    # For user conversation
    # Inside this the process_single_prompt's tool-calling 
    # loop will run
    #
    # user_input = input("\n You: ")
    datetime_format = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_input = f"Current Date: {datetime_format}  \n\n{prompt}"
    print(f"Prompt: {user_input}")
    
    while True:
        
        # ----------------------------------------------------
        # Exit
        if user_input.lower() in { "exit", "quit" }:
            print( "\n User entered to stop... \nGoodbye!" )
            break
        # ----------------------------------------------------



        # ----------------------------------------------------
        # Process request
        try: 
            answer = process_one_prompt( user_input )
            
            # 1. Initialize the Rich Console
            console = Console()
            md = Markdown(answer)
            console.print(md)
            break

        except Exception: 
            print( "\nAn unexpected error occurred." ) 
            traceback.print_exc()
            break
        # ----------------------------------------------------
        
        
        
    #---------------------------------------------------------
    print("\n \nONE USER PROMPT EXECUTED")
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