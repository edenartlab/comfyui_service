import time
import signal
import os
import uuid
import json
import yaml
import shutil
import subprocess
import threading
import tempfile
import urllib.request
import websocket
from timeit import default_timer as timer
from urllib.error import URLError

from .configs import prepare_args, Endpoint


class ComfyUI:

    def __init__(
        self, 
        comfyui_root="./ComfyUI", 
        server_address="127.0.0.1",
        server_port="8188"
    ):
        self.comfyui_root = comfyui_root
        self.server_address = f"{server_address}:{server_port}"
        self.server_port = server_port
        self.id = uuid.uuid4()
        self.t0 = timer()

    def run_workflow(self, workflow_file, endpoint_file, config, client_id=None):
        if client_id is None:
            client_id = str(uuid.uuid4())

        self.temp_files_dir = tempfile.mkdtemp()

        with open(workflow_file, 'r') as file:
            workflow = json.load(file)
        
        with open(endpoint_file, 'r') as file:
            endpoint = yaml.safe_load(file)
            output_node_id = str(endpoint["comfyui_output_node_id"])

        args = prepare_args(endpoint_file, config, save_files=True)
        print("COMFYUI ARGS")
        print(args)
        workflow = self.inject_args_into_workflow(endpoint_file, workflow_file, args)
        print("WORKFLOW")
        print(workflow)
        outputs = self.get_outputs(workflow, client_id)

        if output_node_id not in outputs: 
            print("No output found for node id", output_node_id)

        outputs = outputs[output_node_id]

        # clean up
        shutil.rmtree(self.temp_files_dir)

        return outputs
    
        
    def inject_args_into_workflow(self, endpoint_file, workflow_file, args):
        #endpoint_file = f"./endpoints/{endpoint_name}.yaml"
        #workflow_file = f"./workflows/{endpoint_name}.json"

        with open(endpoint_file, 'r') as file:
            endpoint = Endpoint(**yaml.safe_load(file))

        with open(workflow_file, 'r') as file:
            workflow = json.load(file)

        comfyui_map = {
            param.name: param.comfyui 
            for param in endpoint.parameters if param.comfyui
        }
        
        for key, comfyui in comfyui_map.items():
            value = args.get(key)
            if value is None:
                continue

            print("THE VALUE IS 1111")
            print(value)

            if comfyui.preprocessing is not None:
                print("PREPROCESSING", comfyui.preprocessing)
                if comfyui.preprocessing == "csv":
                    value = ",".join(value)

                elif comfyui.preprocessing == "folder":
                    temp_subfolder = tempfile.mkdtemp(dir=self.temp_files_dir)
                    if isinstance(value, list):
                        for i, file in enumerate(value):
                            filename = f"{i:06d}_{os.path.basename(file)}"
                            new_path = os.path.join(temp_subfolder, filename)
                            shutil.move(file, new_path)
                    else:
                        shutil.move(value, temp_subfolder)
                    value = temp_subfolder
                    print("THE VALUE IS 3333")
                    print(value)

            print("THE VALUE IS 2222"    )
            print(value)


            node_id, field, subfield = str(comfyui.node_id), comfyui.field, comfyui.subfield
            workflow[node_id][field][subfield] = value

        return workflow


    def setup(self):
        self.t1 = timer()
        self.server_process = None
        self.start_server()
        self.t2 = timer()
        print(f"Boot ComfyUI {self.id} time:", self.t1 - self.t0, self.t2 - self.t1)

    def start_server(self):
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()
        while not self.is_server_running():
            time.sleep(1) 
        print("ComfyUI Server running!")

    def run_server(self):
        command = f"python {self.comfyui_root}/main.py --listen --port {self.server_port}"
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

    def get_outputs(self, prompt, client_id):
        ws = websocket.WebSocket()                
        ws.connect("ws://{}/ws?clientId={}".format(self.server_address, client_id))
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
    print("Final prompt string:", formatted_prompt)

    return prompt_list, formatted_prompt

