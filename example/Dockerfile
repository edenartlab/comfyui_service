FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0 

RUN pip install git+https://github.com/edenartlab/comfyui_service

# Copy local files
COPY snapshots /root/snapshots
COPY workflows /root/workflows
COPY endpoints /root/endpoints

# Run the install script
ARG WORKFLOW=img2vid

RUN comfyui_service install \
    --workflow /root/workflows/${WORKFLOW}.json \
    --snapshot /root/snapshots/${WORKFLOW}.json \
    --downloads /root/snapshots/_downloads.json \
    --comfyui-home /root/ComfyUI

# For Development
# COPY .. /root/comfyui_service
# RUN pip uninstall -y comfyui_service
# WORKDIR /root/comfyui_service
# RUN pip install -e .
# WORKDIR /root


# Setup server to catch any leftover dependencies/downloads
# RUN comfyui_service run \
#     --endpoint /root/endpoints/${WORKFLOW}.yaml \
#     --workflow /root/workflows/${WORKFLOW}.json \ 
#     --comfyui-home /root/ComfyUI

