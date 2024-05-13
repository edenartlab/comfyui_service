import argparse
import uuid

from comfyui_service import ComfyUI

def main():
    parser = argparse.ArgumentParser(description='Run a specific workflow')
    parser.add_argument('--workflow', type=str, required=True, help='Path to the workflow file')
    parser.add_argument('--endpoint', type=str, required=True, help='Path to the endpoint file')

    args = parser.parse_args()

    comfyui = ComfyUI()
    comfyui.setup()

    client_id = str(uuid.uuid4())

    workflow_name = args.workflow_file.split("/")[-1].replace(".json", "")

    if workflow_name == "txt2img" or workflow_name == "txt2vid_lcm":
        config = {
            "prompt": "A cat and a dog eating a pizza"
        }
    elif workflow_name == "img2vid":
        config = {
            "image": "https://d14i3advvh2bvd.cloudfront.net/7f5d44ba6f4f2ab760a9315fd3907f421f1b077e81f737b5a49b6429475442a4.jpg"
        }
    else:
        raise Exception("Invalid workflow")

    try:
        result = comfyui.run_workflow(
            args.workflow,
            args.endpoint,
            config,
            client_id

            workflow_file, endpoint_file, config, client_id
        )
        print(result)

    except Exception as e:
        print(e)

    comfyui.stop_server()


if __name__ == "__main__":
    main()