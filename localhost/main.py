import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Depends
from read_shapefile import read_shapefile
from Pyneapple.pyneapple.weight.rook import from_dataframe as rook
from Pyneapple.pyneapple.regionalization.expressive_maxp import expressive_maxp
from Pyneapple.pyneapple.regionalization.MaxP import maxp
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
import math
import numpy as np

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
                "name": "maxp",
                "description": "Clustering a set of geographic areas into the maximum number of homogeneous regions that satisfies a set of user defined constraints. The number of regions to partition is determined by the parameters and conditions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        
                        "sumName": {
                            "type": "string",
                            "description": "The name of the spatial extensive attribute variable for the SUM constraint, usually the central component parameter to fetermine the regionalization.",
                            #"enum": ["pop2010", "pop_16up"]
                        },
                        "sumLow": {
                            "type": "integer",
                            "descripition": "The lowerbound for the SUM range."
                            
                        },
                        "sumHigh": {
                            "type": "integer",
                            "descripition": "The upperbound for the SUM range."
                        },
                        "disname": {
                            "type": "string",
                            "descripition": "The dissimlarity attribute"
                        },
                        "minName": {
                            "type": "string",
                            "descripition": " The name of the spatial extensive attribute variable for the MIN constraint"
                        },
                        "minLow": {
                            "type": "integer",
                            "descripition": " The lowerbound for the MIN range"
                        },
                        "minHigh": {
                            "type": "integer",
                            "descripition": " The upperbound for the MIN range"
                        },
                        "maxName": {
                            "type": "string",
                            "descripition": " The name of the spatial extensive attribute variable for the MAX constraint"
                        },
                        "maxLow": {
                            "type": "integer",
                            "descripition": " The lowerbound for the MAX range"
                        },
                        "maxHigh": {
                            "type": "integer",
                            "descripition": " The upperbound for the MAX range"
                        },
                        "avgName": {
                            "type": "string",
                            "descripition": "The name of the spatial extensive attribute variable for the AVG constraint"
                        },
                        "avgLow": {
                            "type": "integer",
                            "descripition": "The lowerbound for the AVG range."
                        },
                        "avgHigh": {
                            "type": "integer",
                            "descripition": "The upperbound for the AVG range."
                        },
                        "countLow": {
                            "type": "integer",
                            "descripition": "The lowerbound for the COUNT range."
                        },
                        "countHigh": {
                            "type": "integer",
                            "descripition": "The upperbound for the COUNT range."
                        },

                    },
                    "required": ["disname", "sumName", "sumLow", "sumHigh"],
                },
            },
            {
                "name": "generalized_p",
                "description": "Clustering a set of geographic areas into the fixed given number of homogeneous regions based on one constraint and one optimization parameter. Only used when the number of regions to partition the given dataset is mentioned in the user query. ",
                "parameters": {
                    "type": "object",
                    "properties": {
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
                    "required": ["sim_attr", "ext_attr", "threshold", "p"],
                },
            },

        ]

DESCRIPTIONS_JSON = '../testdata/descriptions.json'

def generate_column_descriptions(df_context: str) -> dict:
    # Here, you call GPT-3 API to generate a detailed description for columns
    chat_history = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Describe each of the following dataframe columns in detail: " + df_context}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=chat_history
    )

    detailed_description = response["choices"][0]["message"]["content"]
    return detailed_description


@app.get("/gpt_end_point/generate_description/{file_name}")
def generate_description(file_name: str) -> dict:
    # If the descriptions file exists, load it
    if os.path.exists(DESCRIPTIONS_JSON):
        with open(DESCRIPTIONS_JSON, 'r') as f:
            descriptions = json.load(f)
    else:
        descriptions = {}

    # If the description already exists, return it
    if file_name in descriptions:
        return {"status": "exists", "description": descriptions[file_name]}

    df = read_shapefile(data_dir, file_name)
    filtered_columns = [col for col in df.columns if col not in ['geometry', 'OBJECTID', 'GEOID10']]
    df_context = str(filtered_columns)

    # Generate detailed descriptions for the columnsb 
    column_descriptions = generate_column_descriptions(df_context)

    descriptions[file_name] = column_descriptions

    # Save the updated descriptions
    with open(DESCRIPTIONS_JSON, 'w') as f:
        json.dump(descriptions, f)

    return {"status": "created", "description": column_descriptions}



def get_description(file_name: str) -> str:
    with open(DESCRIPTIONS_JSON, 'r') as f:
        descriptions = json.load(f)
        
    return descriptions.get(file_name, "")


@app.get("/gpt_end_point/process_query")
def gpt_process_query(user_query: str, file_name: str):

    # print(file_name)
    # df = read_shapefile(data_dir, file_name)
    # filtered_columns = [col for col in df.columns if col not in ['geometry', 'OBJECTID', 'GEOID10']]
    # df_cols = str(filtered_columns)
    # print(df_context)

    df_context = get_description(file_name)
    
    # If no description exists, it means it hasn't been generated before. 
    if not df_context:
        return {"error": "Description not found for the given file_name"}
    print("File description: ", df_context)

    chat_history = []
    chat_history.append({"role": "system","content": "Only choose from the functions provided to you. Default values for lower bound parameters is negative infinty and upper bound is infintiy. Only use ',' as a delimeter for larger integers"})
    chat_history.append({"role": "system", "content": "Function generalized_p is chosen if the number of regions to partition the dataset is mentioned by the user. If the nu,ber of regions/partitions are not mentioned you should choose the function maxp"})
    chat_history.append({"role": "system", "content": "Make sure to choose the required string parameters for each function."})
    # chat_history.append({"role": "user","content": "Based on the name of the columns of the  dataframe help select appropiate column as arguments for functions based on the user query. Give a detailed analysis of inference of each column name"})
    # chat_history.append({"role": "user", "content": "The columns in the dataframe are : " + df_context})
    # chat_history.append({"role": "system", "content": "The function is case sensitive so for arguments return exact names of the columns as parameters."})
    # print(len(chat_history))

    # Initialresponse = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo-16k-0613",

    #     # This is the chat message from the user
    #     messages=chat_history

    # )
    # print(Initialresponse["choices"][0]["message"])
    # chat_history.append(Initialresponse["choices"][0]["message"])
    # chat_history.append({"role": "system", "content": "Default values for lower bound parameters is negative infinty and upper bound is infintiy. Only use ',' as a delimeter for larger integers"})
    

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",

        # This is the chat message from the user
        messages = chat_history + [{"role": "user", "content": "Respond with an appropiate function call where arguments match a certain column name for the given the user query : " + user_query + "given the column description: " + df_context}],

        functions=function_descriptions,
        function_call="auto",
    )

    ai_response_message = response["choices"][0]["message"]
    print("Initial response Message: ", ai_response_message)
    # print("Debug: ", ai_response_message.keys())
    # if "function_call" not in ai_response_message:
    #     print("Debug: ")
    #     #print(ai_response_message.keys())

    if "function_call" in ai_response_message:
        callingFunction = ai_response_message['function_call']['name']
        print("Calling Function is : ", callingFunction)
        parameters = json.loads(ai_response_message["function_call"]["arguments"])
        print("Parameters chosen by GPT are : ", parameters)
    else:
        print("In the validation function")
        validate_function_call = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",

        # This is the chat message from the user
        messages=[{"role": "user", "content": "Respond only with the filled dictionary {'calling_function': , 'arguments': {} } based on the response " + ai_response_message["content"] + "available function names are either maxp or generalized_p"}],
        # functions=function_descriptions,
        # function_call="none",
        )

        validate_function_response = validate_function_call["choices"][0]["message"]
        print("Validation Response: ", validate_function_response)

        # Convert the 'content' string to a dictionary
        fixed_json_str = validate_function_response["content"].replace("'", "\"")
        content_dict = json.loads(fixed_json_str)
        print("Content dictionary: ", content_dict)

        # Extract the values from the dictionary
        callingFunction = content_dict["calling_function"]
        print("Validated function call: ", callingFunction)

        # Assuming you want to replace underscores from keys in the 'arguments' dictionary
        parameters = content_dict["arguments"]
        print("Parameters chosen by function validator: ", parameters)
        # print(str(parameters))

    # refined_response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo-16k-0613",

    #     # This is the chat message from the user
    #     messages=[{"role": "user", "content": "Based on the conditions, Validate and only return the dictonary: " + str(parameters) + "Conditions: Integer values should only be seperated by ',' as a delimeter. String values must exactly match a certain column from given column names: " + df_cols}],
    # )
    # print("Refined Response: ",refined_response["choices"][0]["message"])
    # parameters = json.loads(refined_response["choices"][0]["message"]["content"])
    # print("refined parameters: ", parameters)

## Validate Parameterrs generated
    # validate_parameters = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo-16k-0613",

    #     # This is the chat message from the user
    #     messages=[{"role": "user", "content": "Only return the validated dictionary where if the value is a string should match a column from " + df_cols+ "and if an integer should be seperated using a ','. Dictionary to validate is: " + str(parameters)}],
    # )

    # validate_parameters_response = validate_parameters["choices"][0]["message"]
    # print("Validated parameters: ", validate_parameters_response)

    if callingFunction == "maxp":
        function_response = GPTmaxPEndPoint(parameters, file_name)
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
def GPTmaxPEndPoint(parameters: Dict[str, Union[float, str]], filename: str):

    # location = parameters['location']
    # if location == 'Los Angeles, CA':
    # filename = "LACity.shp"

    df = read_shapefile(data_dir, filename)
    w = rook(df)

    parameters_required = {
        "disname": None,
        "minName": None,
        "minLow": -math.inf,
        "minHigh": math.inf,
        "maxName": None,
        "maxLow": -math.inf,
        "maxHigh": math.inf,
        "avgName": None,
        "avgLow": -math.inf,
        "avgHigh": math.inf,
        "sumName": None,
        "sumLow": -math.inf,
        "sumHigh": math.inf,
        "countLow": -math.inf,
        "countHigh": math.inf,
    }

    for param in parameters_required:
        if param in parameters:
            parameters_required[param] = parameters[param]

    for key, value in parameters_required.items():
        if isinstance(value, (int, float)):
            parameters_required[key] = jpype.JDouble(value)
    print(parameters_required)
    # print(type(df),     type(w), type(parameters_required), type(parameters_required['disname']))
    max_p, labels = maxp(df, w, parameters_required["disname"], 
                         parameters_required["sumName"],
                         parameters_required["sumLow"], parameters_required["sumHigh"],
                         parameters_required["minName"],
                         parameters_required["minLow"], parameters_required["minHigh"],
                         parameters_required["maxName"],
                         parameters_required["maxLow"], parameters_required["maxHigh"],
                         parameters_required["avgName"],
                         parameters_required["avgLow"], parameters_required["avgHigh"],
                         parameters_required["countLow"], parameters_required["countHigh"])
    # print("Maxp:", max_p, "labels", labels)
    # labels = labels.tolist()
    empResult = {"max_p": max_p, "labels": labels}
    if isinstance(empResult, np.ndarray):
        empResult = empResult.tolist()

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
    print("generalized_p result: ", prucLabels)
    prucResult = {"heterogenity_score:": prucLabels[0], "labels": prucLabels[1]}
    jsonPrucResult = json.dumps(prucResult)

    return jsonPrucResult
#print(pruc(gdf, w, 'PCGDP1940', 'PERIMETER', 3000000, 10))


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)