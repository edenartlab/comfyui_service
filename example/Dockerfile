FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0 

RUN pip install git+https://github.com/edenartlab/comfyui_service

# # Copy local files and code
COPY example_workflows /root/example_workflows
COPY example_endpoints /root/example_endpoints
COPY example_snapshot.json /root/example_snapshot.json
COPY downloads.json /root/downloads.json

# # Run the install script
RUN comfyui_service install \
    --workflow /root/example_workflows/txt2img.json \
    --snapshot /root/example_snapshot.json \
    --downloads /root/downloads.json \
    --comfyui-home /root/ComfyUI

# Setup server to catch any leftover dependencies/downloads
# #RUN comfyui_service run --endpoint /root/comfyui_service/example/example_endpoints/txt2img.yaml --workflow /root/comfyui_service/example/example_workflows/txt2img.json --comfyui-home /root/ComfyUI
