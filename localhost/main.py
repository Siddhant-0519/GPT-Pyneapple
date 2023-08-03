import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends
from read_shapefile import read_shapefile
from Pyneapple.pyneapple.weight.rook import from_dataframe as rook
from Pyneapple.pyneapple.regionalization.expressive_maxp import expressive_maxp
import uvicorn
import json
from typing import Dict, Union
import openai
from dotenv import load_dotenv
import requests
import geopandas as gpd
import jpype
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows CORS from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],
)

openai.api_key = os.getenv('OPENAI_API_KEY')
data_dir = "D:/user_pa1n/VSCode/projects/GPT-Pyneapple/testData"

function_descriptions = [
            {
                "name": "emp",
                "description": "Clustering a set of geographic areas into the maximum number of homogeneous regions that satisfies a set of user defined constraints",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "sumName": {
                            "type": "string",
                            "description": "The name of the spatial extensive attribute variable for the SUM constraint",
                            #"enum": ["pop2010", "pop_16up"]
                        },
                        "sumLow": {
                            "type": "integer",
                            "descripition": "The lowerbound for the SUM range"
                        },
                        "sumHigh": {
                            "type": "integer",
                            "descripition": "The upperbound for the SUM range"
                        },
                        "disname": {
                            "type": "string",
                            "descripition": "The dissimlarity attribute"
                        },
                    },
                    "required": ["location", "sumName", "sumLow", "sumHigh", "disname"],
                },
            }
        ]


@app.get("/gpt_end_point/process_query")
def gpt_process_query(user_query: str, file_name: str):

    print(file_name)
    df = read_shapefile(data_dir, file_name)
    df_context = str(df.columns.values)
    print(df_context)

    chat_history = []
    chat_history.append({"role": "system","content": "You are a helpful assistant"})
    chat_history.append({"role": "user","content": "Based on the name  of the columns of the  dataframe help select appropiate column as paramters for functions based on the user query"})
    chat_history.append({"role": "user", "content": "The contents of the dataframe are : " + df_context})
    print(len(chat_history))

    Initialresponse = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",

        # This is the chat message from the user
        messages=chat_history

    )

    chat_history.append(Initialresponse["choices"][0]["message"])

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",

        # This is the chat message from the user
        messages= chat_history + [{"role": "user", "content": "Given the user query : " + user_query + "respond with the function call. Make sure the arguments match exactly including the casing to a column name mentioned in the dataframe contents. Convert any integer value to a double in the arguments"}],


        functions=function_descriptions,
        function_call="auto",
    )

    ai_response_message = response["choices"][0]["message"]
    callingFunction = ai_response_message['function_call']['name']
    parameters = json.loads(ai_response_message["function_call"]["arguments"])
    print(parameters)

    if callingFunction == "emp":
        function_response = GPTempEndPoint(parameters, file_name)

    evaluate_function_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",

        # This is the chat message from the user
        messages=chat_history + [{"role": "user", "content": "The function returns : " + function_response + "if max_p shows maximum number of regions formed for the given query. Tell me the maximum number of regions that satisfy the userquery"}],

    )

    gptResult = {"gptResponse": evaluate_function_response['choices'][0]['message']['content'], "plot": function_response}
    print(gptResult)
    return gptResult


@app.get("/files/{filename}")
async def read_file_fe(filename: str):
    gdf = read_shapefile(data_dir, filename)
    gdf = gdf[['geometry']]
    gdf['id'] = range(1, len(gdf) + 1)
    # print(gdf)
    return json.loads(gdf.to_json())


@app.get("/listFiles")
async def list_files():
    files = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".shp"):
            files.append(filename)
    return files

@app.post("/api/endpoint")
def GPTempEndPoint(parameters: Dict[str, Union[float, str]], filename: str):

    # location = parameters['location']
    # if location == 'Los Angeles, CA':
    # filename = "LACity.shp"

    df = read_shapefile(data_dir, filename)
    w = rook(df)

    parameters_required = {
        "disname": "pop_16up",
        "minName": "pop_16up",
        "minLow": 0.0,
        "minHigh": 999999.0,
        "maxName": "pop_16up",
        "maxLow": 0.0,
        "maxHigh": 999999.0,
        "avgName": "pop_16up",
        "avgLow": 0.0,
        "avgHigh": 999999.0,
        "sumName": "pop_16up",
        "sumLow": 0.0,
        "sumHigh": 999999.0,
        "countLow": 0.0,
        "countHigh": 999999.0,
    }

    for param in parameters_required:
        if param in parameters:
            parameters_required[param] = parameters[param]

    # print(parameters_required)
    # print(type(df),     type(w), type(parameters_required), type(parameters_required['disname']))
    max_p, labels = expressive_maxp(df, w, parameters_required["disname"],
                                    parameters_required["minName"],
                                    parameters_required["minLow"], parameters_required["minHigh"],
                                    parameters_required["maxName"],
                                    parameters_required["maxLow"], parameters_required["maxHigh"],
                                    parameters_required["avgName"],
                                    parameters_required["avgLow"], parameters_required["avgHigh"],
                                    parameters_required["sumName"],
                                    parameters_required["sumLow"], parameters_required["sumHigh"],
                                    parameters_required["countLow"], parameters_required["countHigh"])
    labels = labels.tolist()
    empResult = {"max_p": max_p, "labels": labels}
    jsonEmpRes = json.dumps(empResult)
    return jsonEmpRes


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)