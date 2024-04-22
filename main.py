import uuid
import modal
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from comfyui_server import ComfyUI


snapshots = ["txt2img", "txt2vid_lcm"]

app = modal.App(
    name="eden-comfyui",
    secrets=[
        modal.Secret.from_name("s3-credentials")
    ],
)

class ComfyUIServerBase:
    @modal.enter()
    def startup(self):
        start = timer()
        self.comfyui = ComfyUI()
        self.comfyui.setup()
        end = timer()
        print("Boot ComfyUI time:", end - start)

    @modal.exit()
    def shutdown(self):
        self.comfyui.stop_server()

    @modal.method()
    def run(self, workflow, config, client_id):
        outputs = self.comfyui.run_workflow(workflow, config, client_id)
        urls = [upload_file(output, png_to_jpg=True) for output in outputs]
        # self.comfyu.cleanup()
        return {"urls": urls}


ComfyUIServers = {}
for snapshot in snapshots:
    image = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("git", "libgl1-mesa-glx", "libglib2.0-0", "libmagic1")
        .run_commands(
            "cd /root && mkdir ComfyUI && cd ComfyUI && git init .",
            "cd /root/ComfyUI && git remote add --fetch origin https://github.com/comfyanonymous/ComfyUI",
            "cd /root/ComfyUI && git checkout 45ec1cbe963055798765645c4f727122a7d3e35e",
            "cd /root/ComfyUI && pip install xformers!=0.0.18 -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121",
            "pip install httpx requests PyYAML tqdm websocket-client gitpython boto3 python-dotenv python-magic",
        )
        .copy_local_dir("snapshots", remote_path="/root/snapshots")
        .copy_local_file("install.py", remote_path="/root/install.py")
        .run_commands(
            f"cd /root && python install.py --snapshot snapshots/{snapshot}.json --comfyui-home ./ComfyUI",
        )
        .copy_local_dir("workflows", remote_path="/root/workflows")
        .copy_local_dir("endpoints", remote_path="/root/endpoints")
        .copy_local_file("comfyui_server.py", remote_path="/root/comfyui_server.py")
        .copy_local_file("s3.py", remote_path="/root/s3.py")
    ) 

    with image.imports():
        from comfyui_server import ComfyUI
        from s3 import upload_file
        from timeit import default_timer as timer

    cls_name = f"ComfyUIServer_{snapshot}"
    cls = type(cls_name, (ComfyUIServerBase,), {})
    
    # Decorate the class with @app.cls
    decorated_cls = app.cls(
        gpu=modal.gpu.A100(), 
        container_idle_timeout=30, 
        image=image
    )(cls)
    
    # Add the class to the global namespace
    globals()[cls_name] = decorated_cls

    # Create an instance of the class and add it to ComfyUIServers
    ComfyUIServers[snapshot] = decorated_cls()


web_app = FastAPI()

class WorkflowRequest(BaseModel):
    workflow: str
    config: Dict[str, Any]
    client_id: Optional[str] = None

@app.function()
@web_app.post("/run_workflow")
async def run_workflow(request: WorkflowRequest):
    if request.workflow not in ComfyUIServers:
        raise HTTPException(status_code=400, detail="Invalid workflow")

    if request.client_id is None:
        client_id = str(uuid.uuid4())

    comfyui = ComfyUIServers[request.workflow]
    result = comfyui.run.remote(
        request.workflow, 
        request.config.dict(), 
        client_id
    )
    return result

@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app
