## ComfyUI Service

Virtual ComfyUI service that can be imported and run inside a python process.


## Installation

To install the service, you can use pip:

    pip install git+https://github.com/edenartlab/comfyui_service

## Usage

Install from a workflow file, snapshot, and downloads file:

    comfyui_service install --workflow /path/to/workflow.json --snapshot /path/to/snapshot.json --downloads /path/to/downloads.json --comfyui-home ./ComfyUI 

Then run a job:

    comfyui_service run --endpoint /path/to/endpoint.yaml --workflow /path/to/workflow.json --comfyui-home ./ComfyUI

Or, from a python shell:

    ```
    from comfyui_service import ComfyUI
    
    comfyui = ComfyUI()
    comfyui.setup()
    
    config = {
        "prompt": "A cat and a dog eating a pizza"
    }

    result = comfyui.run_workflow("/path/to/workflow.json", "/path/to/endpoint.yaml", config) 

    comfyui.stop_server()
    ```

See an example in the `examples` directory.