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
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ZIP = "zip"
    BOOL_ARRAY = "bool[]"
    INT_ARRAY = "int[]"
    FLOAT_ARRAY = "float[]"
    STRING_ARRAY = "string[]"
    IMAGE_ARRAY = "image[]"
    VIDEO_ARRAY = "video[]"
    AUDIO_ARRAY = "audio[]"
    ZIP_ARRAY = "zip[]"


FILE_TYPES = [ParameterType.IMAGE, ParameterType.VIDEO, ParameterType.AUDIO, ParameterType.ZIP]
FILE_ARRAY_TYPES = [ParameterType.IMAGE_ARRAY, ParameterType.VIDEO_ARRAY, ParameterType.AUDIO_ARRAY, ParameterType.ZIP_ARRAY]


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
    minimum: Optional[float] = Field(None)
    maximum: Optional[float] = Field(None)
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
        ParameterType.IMAGE: lambda v: isinstance(v, str),
        ParameterType.VIDEO: lambda v: isinstance(v, str),
        ParameterType.AUDIO: lambda v: isinstance(v, str),
        ParameterType.ZIP: lambda v: isinstance(v, str),
        ParameterType.BOOL_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, bool) for i in v),
        ParameterType.INT_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, int) for i in v),
        ParameterType.FLOAT_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, float) for i in v),
        ParameterType.STRING_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
        ParameterType.IMAGE_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
        ParameterType.VIDEO_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
        ParameterType.AUDIO_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
        ParameterType.ZIP_ARRAY: lambda v: isinstance(v, list) and all(isinstance(i, str) for i in v),
    }
    if not type_validators[type](value):
        raise ValueError(f"Argument '{key}' must be a {type}")


def prepare_args(endpoint_file, config, save_files=False):
    if not os.path.exists(endpoint_file):
        raise ValueError(f"Endpoint file not found: {endpoint_file}")
    with open(endpoint_file, 'r') as file:
        data = yaml.safe_load(file)
        endpoint = Endpoint(**data)

    args = {}
    for param in endpoint.parameters:
        key = param.name
        value = None
        if param.default is not None:
            value = param.default
        if config.get(key) is not None:
            value = config[key]

        if value == "random":
            value = random.randint(param.minimum, param.maximum)

        if param.required and value is None:
            raise ValueError(f"Required argument '{key}' is missing")

        validate_type(key, value, param.type)
            
        # save files if required
        if param.type in FILE_TYPES and save_files:
            value = save_file(value)
        elif param.type in FILE_ARRAY_TYPES and save_files:
            value = [save_file(v) for v in value]

        # set args value
        args[key] = value
        
    return args
