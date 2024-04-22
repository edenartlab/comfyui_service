import time
import signal
import os
import uuid
import json
import yaml
import random
import subprocess
import threading
import urllib.request
import websocket
from typing import Iterator, Optional, List
from urllib.error import URLError
from PIL import Image



class ComfyUI:

    def __init__(
        self, 
        comfyui_root="./ComfyUI", 
        server_address="127.0.0.1:8188"
    ):
        self.comfyui_root = comfyui_root
        self.server_address = server_address

    def run_workflow(self, workflow_name, args, client_id=None):
        if client_id is None:
            client_id = str(uuid.uuid4())

        workflow_file = f"./workflows/{workflow_name}.json"
        with open(workflow_file, 'r') as file:
            workflow = json.load(file)
            print(workflow)

        config_file = f"./endpoints/{workflow_name}.yaml"
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

            parameters = config["parameters"]
            output_node_id = config["comfyui_output_node_id"]

        workflow_args = prepare_workflow_args(parameters, args)
        workflow = inject_into_workflow(workflow, workflow_args)
        
        #     verbose = True
        #     if verbose:
        #         # pretty print final config:
        #         print("------------------------------------------")
        #         print(json.dumps(workflow, indent=4, sort_keys=True))
        #         print("------------------------------------------")

        ws = websocket.WebSocket()                
        ws.connect("ws://{}/ws?clientId={}".format(self.server_address, client_id))

        outputs = self.get_outputs(ws, workflow, client_id)

        if str(output_node_id) not in outputs: 
            print("No output found for node id", output_node_id)

        outputs = outputs[str(output_node_id)]

        return outputs

    def setup(self):
        self.server_process = None
        self.start_server()

    def start_server(self):
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()
        while not self.is_server_running():
            time.sleep(1) 
        print("ComfyUI Server running!")

    def run_server(self):
        command = f"python {self.comfyui_root}/main.py --dont-print-server --multi-user --listen --port 8188"
        self.server_process = subprocess.Popen(command, shell=True, start_new_session=True)
        self.server_process.wait()
    
    def stop_server(self):
        if self.server_process is not None:
            print("Stopping ComfyUI server...")
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            print("ComfyUI server stopped!")
        else:
            print("Server process not found.")

    def is_server_running(self):
        try:
            url = "http://{}/history/123".format(self.server_address)
            with urllib.request.urlopen(url) as response:
                return response.status == 200
        except URLError:
            return False

    def queue_prompt(self, prompt, client_id):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(self.server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_history(self, prompt_id):
        with urllib.request.urlopen("http://{}/history/{}".format(self.server_address, prompt_id)) as response:
            return json.loads(response.read())

    def get_outputs(self, ws, prompt, client_id):
        prompt_id = self.queue_prompt(prompt, client_id)['prompt_id']
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break #Execution is done
            else:
                continue #previews are binary data
        outputs = {}
        history = self.get_history(prompt_id)[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    outputs[node_id] = [
                        os.path.join(self.comfyui_root, "output", image['subfolder'], image['filename'])
                        for image in node_output['images']
                    ]                
                elif 'gifs' in node_output:
                    outputs[node_id] = [
                        os.path.join(self.comfyui_root, "output", video['subfolder'], video['filename'])
                        for video in node_output['gifs']
                    ]
        return outputs


def format_prompt(prompt, n_frames):
    prompt_list = prompt.split('|')
    n_frames_per_prompt = n_frames // len(prompt_list)

    formatted_prompt = ""
    for i, p in enumerate(prompt_list):
        frame = str(i * n_frames_per_prompt)
        formatted_prompt += f"\"{frame}\" : \"{p}\",\n"

    # Removing the last comma and newline
    formatted_prompt = formatted_prompt.rstrip(',\n')
    print("Final prompt string:")
    print(formatted_prompt)

    return prompt_list, formatted_prompt


def inject_into_workflow(workflow, config):
    for (node_id, field, subfield), value in config.items():
        if str(node_id) in workflow:
            if field in workflow[str(node_id)]:
                workflow[str(node_id)][field][subfield] = value
            else:
                workflow[str(node_id)][field] = {subfield: value}
        else:
            workflow[str(node_id)] = {field: {subfield: value}}
    return workflow


def prepare_workflow_args(parameters, args):
    workflow_args = {}
    for param in parameters:
        node_id = param['comfyui']['node_id']
        field = param['comfyui']['field']
        subfield = param['comfyui']['subfield']
        key = param['name']
        
        if key in args:
            value = args[key]
        else:
            value = param.get('default')

        if key == "seed" and value is None:
            value = random.randint(0, int(1e16))
        
        if value is None:
            continue
        
        if 'required' in param and param['required'] and key not in args:
            raise ValueError(f"Required argument '{key}' is missing")
        
        if 'allowed_values' in param:
            if value not in param['allowed_values']:
                raise ValueError(f"Argument '{key}' with value {value} is not allowed. Allowed values are {param['allowed_values']}")

        if 'minimum' in param and 'maximum' in param:
            minimum = float(param['minimum'])
            maximum = float(param['maximum'])
            if not isinstance(value, (int, float)):
                raise ValueError(f"Argument '{key}' with value {value} must be a number")                
            if not (minimum <= value <= maximum):
                raise ValueError(f"Argument '{key}' with value {value} must be between {minimum} and {maximum}")
            
        workflow_args[(node_id, field, subfield)] = value

    for arg in workflow_args:
        if arg not in [param['name'] for param in parameters]:
            print(f"Warning: Provided argument '{arg}' is not recognized and will be ignored.")

    return workflow_args


