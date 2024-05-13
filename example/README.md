    docker build -t comfyui .

    docker run --gpus all -it comfyui bash

    comfyui_service run --endpoint /root/comfyui_service/example/example_endpoints/txt2img.yaml --workflow /root/comfyui_service/example/example_workflows/txt2img.json --comfyui-home /root/ComfyUI