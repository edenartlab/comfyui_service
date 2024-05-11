import os
import yaml
import random
import requests
import tempfile
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class ParameterType(str, Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    FILE = "file"
    BOOL_ARRAY = "bool[]"
    INT_ARRAY = "int[]"
    FLOAT_ARRAY = "float[]"
    STRING_ARRAY = "string[]"
    FILE_ARRAY = "file[]"

class ComfyUIInfo(BaseModel):
    node_id: int
    field: str
    subfield: str
    preprocessing: Optional[str] = None

class EndpointParameter(BaseModel):
    name: str
    label: str
    description: str
    required: Optional[bool] = Field(False)
    type: ParameterType
    media_upload: Optional[str] = Field(None)
    default: Optional[Any] = Field(None)
    minimum: Optional[int] = Field(None)
    maximum: Optional[int] = Field(None)
    min_length: Optional[int] = Field(None)
    max_length: Optional[int] = Field(None)
    options: Optional[List[Any]] = Field(None)
    comfyui: Optional[ComfyUIInfo] = Field(None)

class Endpoint(BaseModel):
    name: str
    description: str
    comfyui_output_node_id: Optional[int] = Field(None)
    parameters: List[EndpointParameter]


def save_file(value):
    if value.startswith("http"):
        file_path = download_file(value)
        return file_path
    elif os.path.isfile(value):
        return value
    else:
        raise ValueError(f"Invalid file path: {value}")


def download_file(url):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)
        temp_file.close()
        return temp_file.name
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")
        return None


def validate_type(key, value, type):
    type_validators = {
        ParameterType.BOOL: lambda v: isinstance(v, bool),
        ParameterType.INT: lambda v: isinstance(v, int),
        ParameterType.FLOAT: lambda v: isinstance(v, float),
        ParameterType.STRING: lambda v: isinstance(v, str),
        ParameterType.FILE: lambda v: isinstance(v, str),
        ParameterType.BOOL_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, bool) for i in v),
        ParameterType.INT_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, int) for i in v),
        ParameterType.FLOAT_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, float) for i in v),
        ParameterType.STRING_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
        ParameterType.FILE_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
    }
    if not type_validators[type](value):
        print("THE TYPE DID NO T VALIDATE   "  , type, value)
        raise ValueError(f"Argument '{key}' must be a {type}")


def prepare_args(endpoint_name, config, save_files=False):
    endpoint_file = f"./endpoints/{endpoint_name}.yaml"
    print("OPENING FILE", endpoint_file)
    # check if its there
    if not os.path.exists(endpoint_file):
        print("ERR!!!OR: Endpoint file not found", endpoint_file)
    with open(endpoint_file, 'r') as file:
        print(" ==> OPEN FILE", endpoint_file)
        zz = yaml.safe_load(file)
        print(zz)
        print("ok,...")

        endpoint = Endpoint(**zz)
        print("END OOHITS IS OPEN")
        print(endpoint)

    args = {}
    for param in endpoint.parameters:
        print("$$$$ the param is", param)
        key = param.name
        print("!!!! the key is", key)
        # set default value, then overwrite
        value = None
        if param.default is not None:
            value = param.default
        if config.get(key) is not None:
            value = config[key]

        print("ABCD!EEEFF", value)
        if value == "random":
            print("GET RANDOM")
            value = random.randint(param.minimum, param.maximum)

        if param.required and value is None:
            raise ValueError(f"Required argument '{key}' is missing")

        print("the value is", value)
        # validate the type
        validate_type(key, value, param.type)
            
        # save files if required
        if param.type == ParameterType.FILE_ARRAY and save_files:
            value = [save_file(v) for v in value]
        elif param.type == ParameterType.FILE and save_files:
            value = save_file(value)

        print("the valu eis now", value)

        # set args value
        args[key] = value
        
    return args

