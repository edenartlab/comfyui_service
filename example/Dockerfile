FROM python:3.11-slim

WORKDIR /root

RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0 

RUN pip install git+https://github.com/edenartlab/comfyui_service


# # Set the working directory in the docker image
# WORKDIR /root/ComfyUI

# # Clone the ComfyUI repository
# RUN git init . && \
#     git remote add origin https://github.com/comfyanonymous/ComfyUI && \
#     git fetch && \
#     git checkout 45ec1cbe963055798765645c4f727122a7d3e35e

# # Install Python dependencies
# RUN pip install -r requirements.txt && \
#     pip install httpx requests PyYAML tqdm websocket-client gitpython python-dotenv python-magic pydantic

# # Copy local files and code
COPY example_workflows /root/example_workflows
COPY example_endpoints /root/example_endpoints
COPY example_snapshot.json /root/example_snapshot.json
COPY downloads.json /root/downloads.json

# COPY comfyui.py /root/comfyui.py 
# COPY install.py /root/install.py
# COPY configs.py /root/configs.py
# COPY test.py /root/test.py

# WORKDIR /root

# # Run the install script
RUN comfyui_service install \
    --endpoint /root/example_endpoints/txt2img.json \
    --workflow /root/example_workflows/txtimg.json \
    --downloads /root/downloads.json \
    --comfyui-home /root/ComfyUI

# Setup server to catch any leftover dependencies/downloads
# #RUN comfyui_service run --endpoint-file /root/example_endpoints/txt2img.json --workflow-file /root/example_workflows/txtimg.json --comfyui-home /root/ComfyUI
