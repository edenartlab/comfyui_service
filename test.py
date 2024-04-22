from comfyui_server import ComfyUI
import uuid


comfyui = ComfyUI()
comfyui.setup()

client_id = str(uuid.uuid4())

workflow = "txt2vid_lcm"

config = {
    "prompt": "An alien in Van Gogh's Starry Night style", 
    "negative_prompt": "lowres, bad anatomy, bad hands, text, jpg artifacts",
    "width": 768,
    "height": 1024,
}

result = comfyui.run_workflow(
    workflow, 
    config, 
    client_id
)

print(result)

comfyui.stop_server()
