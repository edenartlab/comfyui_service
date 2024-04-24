
import json

def find_model_names(node, extensions, results):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "inputs":
                find_model_names(value, extensions, results)
            elif isinstance(value, str) and any(value.endswith(ext) for ext in extensions):
                results.append(value)
            else:
                find_model_names(value, extensions, results)
    elif isinstance(node, list):
        for item in node:
            find_model_names(item, extensions, results)


def generate_download_dict(workflow_path, models_dict, extensions_to_find = [".safetensors", ".ckpt", ".pth"]):
    with open(workflow_path, "r") as f:
        workflow_data = json.load(f)

    with open(models_dict, "r") as f:
        models_data = json.load(f)

    download_dict = {"downloads": {}}

    # Parse the workflow contents to find all model names that end with the extensions in extensions_to_find
    model_names_in_workflow = []
    find_model_names(workflow_data, extensions_to_find, model_names_in_workflow)
    
    # Find the matching entries in the models_data
    for key, value in models_data["downloads"].items():
        for model_name in model_names_in_workflow:
            if model_name in key:
                download_dict["downloads"][key] = value

    return download_dict



if __name__ == '__main__':

    workflow_path = "workflows/real2real_adiff.json"
    models_dict   = "snapshots/s3_models.json"
    download_dict = generate_download_dict(workflow_path, models_dict)

    # Pretty print the download_dict:
    print(json.dumps(download_dict, indent=4))
    