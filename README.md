# `GPT-Pyneapple`

**GPT-Pyneapple** is a custom UI which aims to integrate the chat GPT's LLM with Pyneapple which is an open-source Python library for scalable and enriched spatial data analysis. GPT-Pyneapple uses chat GPT's superior language processing capabilities to process natural language audio and textual user queries into interpretable function calls for the Pyneapple library. This novel approach shows promising results and will keep improving with the underlying model.

## Requirements

### Python
- [`JPype`](https://jpype.readthedocs.io/en/latest/)
- [`numpy`](https://numpy.org/devdocs/)
- [`geopandas`](https://geopandas.org/en/stable/)
- [`pandas`](https://pandas.pydata.org/)
- [`libpysal`](https://github.com/pysal/libpysal)
- [`matplotlib`](https://matplotlib.org/)
- [`spopt`](https://pysal.org/spopt/)
- [`poetry`](https://pypi.org/project/poetry/)

### Backend
- [`openai`](https://pypi.org/project/openai/)
- [`fastapi`](https://pypi.org/project/fastapi/)
- [`uvicorn`](https://pypi.org/project/uvicorn/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

### Frontend
- [`react`](https://www.npmjs.com/package/react)
- [`react-leaflet`](https://www.npmjs.com/package/react-leaflet)
- [`shapefile`](https://www.npmjs.com/package/react-leaflet-shapefile)
- [`react-speech-recognition`](https://www.npmjs.com/package/react-speech-recognition)

## Installation

### Dependency Management
We are utilizing the power of poetry, a dependency management toolkit for python. It is a powerful toolkit which eliminates dependency management and versioning errors for python projects. Inorder to avoid installing each dependency one at a time, poetry allows user to install all the required python dependencies with version control. To get started use the following commands:

```
$ pip install poetry
```
Once poetry is installed, navigate to the root directory of this project. Note that the project file already consist of the pyproject.toml file which indicates all the required dependencies and their version constraints. Next,

```
$ poetry install
```
Initially the above command will create a virtual environment and install all the mentioned python and backend dependencies within the virtual environment. Once installed, to load into the virtual environment use command

```
$ poetry shell
```

### Hosting the backend server

Once all the required python and backend dependencies exist, we can navigate to the folder localhost within the project, and use the following command to host our backend server

```
$ uvicorn main:app --reload
```

To verify that the backend server is up and running with necessary endpoints, uding any browser load https://localhost:8000/docs which should be a swagger page and documentation about the expected input and outputs for each backend end point

### Starting the frontend

Install the required frontend dependencies by first navigating to the frontend folder, and installing the required frontend dependencies using

```
$ npm install
```

Next inorder to start the frontend web application, use the command

```
$ npm start
```

This should load up a web application at https://localhost:3000.

The frontend should have the necessary elements to select and load a map for a selected file as well as querying elements which allow both text as well as audio querying. Note that currently, the react speech recognition library only fully supports chrome browsers, therefore it is recommended to make full use of the application, use chrome/ chromium based browsers. 