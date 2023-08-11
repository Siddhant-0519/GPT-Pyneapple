import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends
from read_shapefile import read_shapefile
from Pyneapple.pyneapple.weight.rook import from_dataframe as rook
from Pyneapple.pyneapple.regionalization.expressive_maxp import expressive_maxp
from Pyneapple.pyneapple.regionalization.generalized_p import generalized_p
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
from typing import List
from pydantic import BaseModel

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
# print(openai.api_key)
data_dir = "D:/user_pa1n/VSCode/projects/GPT-Pyneapple/testData"


# class Label(BaseModel):
#     labels = List[int]

function_descriptions = [
            {
                "name": "emp",
                "description": "Clustering a set of geographic areas into the maximum number of homogeneous regions that satisfies a set of user defined constraints. ",
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
                        # "minName": {
                        #     "type": "string",
                        #     "descripition": " The name of the spatial extensive attribute variable for the MIN constraint"
                        # },
                        # "minLow": {
                        #     "type": "integer",
                        #     "descripition": " The lowerbound for the MIN range"
                        # },
                        # "minHigh": {
                        #     "type": "integer",
                        #     "descripition": " The upperbound for the MIN range"
                        # },
                        # "maxName": {
                        #     "type": "string",
                        #     "descripition": " The name of the spatial extensive attribute variable for the MAX constraint"
                        # },
                        # "maxLow": {
                        #     "type": "integer",
                        #     "descripition": " The lowerbound for the MAX range"
                        # },
                        # "maxHigh": {
                        #     "type": "integer",
                        #     "descripition": " The upperbound for the MAX range"
                        # },
                        # "avgName": {
                        #     "type": "string",
                        #     "descripition": "The name of the spatial extensive attribute variable for the AVG constraint"
                        # },
                        # "avgLow": {
                        #     "type": "integer",
                        #     "descripition": "The lowerbound for the AVG range."
                        # },
                        # "avgHigh": {
                        #     "type": "integer",
                        #     "descripition": "The upperbound for the AVG range."
                        # },
                        # "countLow": {
                        #     "type": "integer",
                        #     "descripition": "The lowerbound for the COUNT range."
                        # },
                        # "countHigh": {
                        #     "type": "integer",
                        #     "descripition": "The upperbound for the COUNT range."
                        # },

                    },
                    "required": ["location", "sumName", "sumLow", "sumHigh", "disname"],
                },
            },
            {
                "name": "generalized_p",
                "description": "Clustering a set of geographic areas into the fixed given number of homogeneous regions based on one constraint and one optimization parameter",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "sim_attr": {
                            "type": "string",
                            "description": "The name of the attribute to measure the heterogeneity used for optimization",
                            
                        },
                        "ext_attr": {
                            "type": "string",
                            "description": "The name of the attribute to measure the spatial extensive attribute used as a constraint",    
                        },
                        "threshold": {
                            "type": "integer",
                            "description": "The threshold value enforced on each region with regards to the extensive attribute constraint",    
                        },
                        "p": {
                            "type": "integer",
                            "description": "The pre-defined number of regions",    
                        },
                    },
                    "required": ["location", "sim_attr", "ext_attr", "threshold", "p"],
                },
            },

        ]


@app.get("/gpt_end_point/process_query")
def gpt_process_query(user_query: str, file_name: str):

    print(file_name)
    df = read_shapefile(data_dir, file_name)
    filtered_columns = [col for col in df.columns if col not in ['geometry', 'OBJECTID', 'GEOID10']]
    df_context = str(filtered_columns)
    print(df_context)

    chat_history = []
    chat_history.append({"role": "system","content": "You are a helpful assistant"})
    chat_history.append({"role": "user","content": "Based on the name  of the columns of the  dataframe help select appropiate column as paramters for functions based on the user query"})
    chat_history.append({"role": "user", "content": "The columns in the dataframe are : " + df_context})
    print(len(chat_history))

    Initialresponse = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",

        # This is the chat message from the user
        messages=chat_history

    )
    print(Initialresponse["choices"][0]["message"])
    chat_history.append(Initialresponse["choices"][0]["message"])

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",

        # This is the chat message from the user
        messages= chat_history + [{"role": "user", "content": "Given the user query : " + user_query + "respond with the function call. Make sure the arguments are exactly case matching to a string from df_context and none of them are geological coordinates based or string literals . Convert any integer value to a double in the arguments"}],


        functions=function_descriptions,
        function_call="auto",
    )

    ai_response_message = response["choices"][0]["message"]
    callingFunction = ai_response_message['function_call']['name']
    parameters = json.loads(ai_response_message["function_call"]["arguments"])
    print("Calling Function is : ", callingFunction)
    print("Parameters chosen by GPT are : ", parameters)

    if callingFunction == "emp":
        function_response = GPTempEndPoint(parameters, file_name)
        function_response_data = json.loads(function_response)
        plotLabels = function_response_data['labels']
        print(type(plotLabels))

    elif callingFunction == "generalized_p":
        function_response = gpEndPoint(parameters, file_name)
        function_response_data = json.loads(function_response)

    evaluate_function_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",

        # This is the chat message from the user
        messages=chat_history + [{"role": "user", "content": "The function returns : " + function_response + "explain the results of the user query in 2 lines which is shown by the plotted map"}],

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


@app.post("/api/endpoint/generalizedP")
def gpEndPoint(parameters: Dict[str, Union[int, float, str]], filename: str):

    df = read_shapefile(data_dir, filename)
    w = rook(df)
    parameters_required = {
        "sim_attr": "",
        "ext_attr": "",
        "threshold": 2,
        "p": 5 #confirm and change
    }

    for param in parameters_required:
        if param in parameters:
            parameters_required[param] = parameters[param]

    print(parameters_required)
    prucLabels = generalized_p(df, w, parameters_required["sim_attr"], parameters_required["ext_attr"], parameters_required["threshold"], parameters_required["p"])
    prucResult = {"heterogenity_score:": prucLabels[0], "labels": prucLabels[1]}
    jsonPrucResult = json.dumps(prucResult)

    return jsonPrucResult
#print(pruc(gdf, w, 'PCGDP1940', 'PERIMETER', 3000000, 10))


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)