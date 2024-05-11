import unittest
import argparse
import uuid
from comfyui_service.comfyui import ComfyUI

class TestComfyUIWorkflows(unittest.TestCase):
    def setUp(self):
        self.comfyui = ComfyUI()
        self.comfyui.setup()
        self.client_id = str(uuid.uuid4())

    def test_workflow_txt2img(self):
        args = argparse.Namespace(workflow="txt2img")
        config = {
            "prompt": "A cat and a dog eating a pizza",
            "negative_prompt": "lowres, bad anatomy, bad hands, text, jpg artifacts",
            "width": 768,
            "height": 768
        }
        endpoint_file = f"./example_endpoints/{args.workflow}.yaml"
        workflow_file = f"./example_workflows/{args.workflow}.json"
        result = self.comfyui.run_workflow(workflow_file, endpoint_file, config, self.client_id)
        self.assertIsNotNone(result)  # Example assertion

    def test_workflow_img2vid(self):
        args = argparse.Namespace(workflow="img2vid")
        config = {
            "image": "https://d14i3advvh2bvd.cloudfront.net/7f5d44ba6f4f2ab760a9315fd3907f421f1b077e81f737b5a49b6429475442a4.jpg"
        }
        endpoint_file = f"./example_endpoints/{args.workflow}.yaml"
        workflow_file = f"./example_workflows/{args.workflow}.json"
        result = self.comfyui.run_workflow(workflow_file, endpoint_file, config, self.client_id)
        self.assertIsNotNone(result)  # Example assertion

    def tearDown(self):
        self.comfyui.stop_server()

if __name__ == '__main__':
    unittest.main()