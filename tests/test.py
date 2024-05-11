import argparse
import uuid

from comfyui import ComfyUI


parser = argparse.ArgumentParser(description='Run a specific workflow')
parser.add_argument('--workflow', type=str, required=True)
args = parser.parse_args()

comfyui = ComfyUI()
comfyui.setup()

client_id = str(uuid.uuid4())

if args.workflow == "txt2img" or args.workflow == "txt2vid_lcm":
    config = {
        "prompt": "A cat and a dog eating a pizza",
        "negative_prompt": "lowres, bad anatomy, bad hands, text, jpg artifacts",
        "width": 768,
        "height": 768
    }
elif args.workflow == "img2vid":
    config = {
        "image": "https://d14i3advvh2bvd.cloudfront.net/7f5d44ba6f4f2ab760a9315fd3907f421f1b077e81f737b5a49b6429475442a4.jpg"
    }
else:
    raise Exception("Invalid workflow")

try:
    endpoint_file = f"./example_endpoints/{args.workflow}.yaml"
    workflow_file = f"./example_workflows/{args.workflow}.json"
    result = comfyui.run_workflow(
        workflow_file,
        endpoint_file,
        config, 
        client_id
    )
    print(result)

except Exception as e:
    print(e)

comfyui.stop_server()
