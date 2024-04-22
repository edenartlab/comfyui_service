# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0

# Set the working directory in the docker image
WORKDIR /root/ComfyUI

# Clone the ComfyUI repository
RUN git init . && \
    git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI && \
    git checkout 45ec1cbe963055798765645c4f727122a7d3e35e

# Install Python dependencies
RUN pip install xformers!=0.0.18 -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121 && \
    pip install httpx requests PyYAML tqdm websocket-client gitpython boto3 python-dotenv python-magic

# Copy local directories and files to the docker image
COPY snapshots /root/snapshots
COPY install.py /root/install.py
COPY workflows /root/workflows
COPY endpoints /root/endpoints
COPY comfyui_server.py /root/comfyui_server.py
COPY s3.py /root/s3.py

WORKDIR /root

# Run the install script
RUN python install.py --snapshot snapshots/txt2vid_lcm.json --comfyui-home ./ComfyUI
