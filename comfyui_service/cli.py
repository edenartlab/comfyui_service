import os
import sys
import argparse
import uuid
from .comfyui import ComfyUI
from .install import generate_download_dict, setup_comfyui, download_models


def main():
    parser = argparse.ArgumentParser(description="ComfyUI Service Tool")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommands")

    # Subparser for the install command
    install_parser = subparsers.add_parser('install', help='Install nodes and download models.')
    install_parser.add_argument('--snapshot', type=str, required=True, help='Path to the snapshot file')
    install_parser.add_argument('--workflow', type=str, required=True, help='Path to the workflow file')
    install_parser.add_argument('--downloads', type=str, required=True, help='Path to the downloads list')
    install_parser.add_argument('--comfyui-home', type=str, default='/root/ComfyUI', help='Path to the ComfyUI home directory')
    install_parser.set_defaults(func=install_command)

    # Subparser for the run command
    run_parser = subparsers.add_parser('run', help='Run a specific workflow')
    run_parser.add_argument('--workflow', type=str, required=True, help='Path to the workflow JSON file')
    run_parser.add_argument('--endpoint', type=str, required=True, help='Path to the endpoint YAML file')
    run_parser.add_argument('--comfyui-home', type=str, default='/root/ComfyUI', help='Path to the ComfyUI home directory')
    run_parser.set_defaults(func=run_workflow)

    # Parse the arguments
    args = parser.parse_args()
    args.func(args)


def install_command(args):
    sys.path.append(args.comfyui_home)
    downloads = generate_download_dict(args.workflow, args.downloads)
    setup_comfyui(args.snapshot, args.comfyui_home)
    download_models(downloads, args.comfyui_home)
    print("Installation and model download completed.")


def run_workflow(args):
    print("Running workflow...")
    comfyui = ComfyUI(comfyui_root=args.comfyui_home)
    comfyui.setup()
    
    client_id = str(uuid.uuid4())
    workflow_name = os.path.basename(args.workflow).split(".")[0]
    
    print("WORKFLOW NAME:", workflow_name)

    if workflow_name == "txt2img" or workflow_name == "txt2vid_lcm":
        config = {
            "prompt": "A cat and a dog eating a pizza"
        }
    elif workflow_name == "img2vid":
        config = {
            "image": "https://d14i3advvh2bvd.cloudfront.net/7f5d44ba6f4f2ab760a9315fd3907f421f1b077e81f737b5a49b6429475442a4.jpg"
        }
    elif workflow_name == "vid2vid":
        config = {
            "image": "https://d14i3advvh2bvd.cloudfront.net/156856cb0e2a0bf3f84fb795997a36fbae42efc1d863b3d87c7e0cfbf8f9dab4.jpg",
            "video": "https://edenartlab-stage-data.s3.amazonaws.com/b09ed23211a88017430bd687b1989dcd41f18222343fcd8f133f7cda489100b0.mp4"   
        }                       
    elif workflow_name == "style_mixing":
        config = {
            "images": [
                "https://d14i3advvh2bvd.cloudfront.net/7f5d44ba6f4f2ab760a9315fd3907f421f1b077e81f737b5a49b6429475442a4.jpg",
                "https://d14i3advvh2bvd.cloudfront.net/156856cb0e2a0bf3f84fb795997a36fbae42efc1d863b3d87c7e0cfbf8f9dab4.jpg"
            ]
        }
    else:
        raise Exception("Invalid workflow type provided")


    print("THE CONFIG IS:", config)
    try:
        result = comfyui.run_workflow(args.workflow, args.endpoint, config, client_id)
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        comfyui.stop_server()


if __name__ == "__main__":
    main()
