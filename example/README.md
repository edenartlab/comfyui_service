### Example of comfyui_service

Build the image:

    docker build -t comfyui .

Run a shell inside a container with GPU support:

    docker run --gpus all -it comfyui bash

From the shell, run a job:

    comfyui_service run --endpoint /root/example_endpoints/txt2img.yaml --workflow /root/example_workflows/txt2img.json --comfyui-home /root/ComfyUI

Or launch a python shell

```
from comfyui_service import ComfyUI

comfyui = ComfyUI()
comfyui.setup()

config = {
    "prompt": "A cat and a dog eating a pizza"
}

result = comfyui.run_workflow(
    "/root/example_workflows/txt2img.json", 
    "/root/example_endpoints/txt2img.yaml", 
    config
) 

comfyui.stop_server()
```