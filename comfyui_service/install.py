import sys
import os
import subprocess
import time
import argparse
import json
import httpx
import shutil
import importlib.util
from tqdm import tqdm
from pathlib import Path
from git import Repo, GitCommandError



def setup_comfyui(snapshot_path, comfyui_home):
    if not os.path.exists(snapshot_path):
        print(f"Error: Snapshot file {snapshot_path} does not exist")

    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)
    
    comfyui_hash = snapshot["comfyui"]

    comfyui_repo = "https://github.com/comfyanonymous/ComfyUI"
    if not os.path.exists(comfyui_home):
        os.makedirs(comfyui_home)
        repo = Repo.init(comfyui_home)
        origin = repo.create_remote("origin", comfyui_repo)
        origin.fetch()
        repo.git.checkout(comfyui_hash)

    requirements_path = os.path.join(comfyui_home, "requirements.txt")

    subprocess.run(["pip", "install", "xformers!=0.0.18", "-r", requirements_path, "--extra-index-url", "https://download.pytorch.org/whl/cu121"], check=True)

    install_nodes(snapshot_path, comfyui_home)


def clone_and_install(repo_url, hash, clone_to="repo_dir", retries=5):
    print("\n\n\n====== Installing", repo_url, hash, clone_to)
    for t in range(retries):        
        try:
            if os.path.exists(clone_to):
                shutil.rmtree(clone_to)
            repo = Repo.clone_from(repo_url, clone_to)
            repo.submodule_update(recursive=True)    
            try:
                repo.git.checkout(hash)
            except Exception as e:
                print(f"Error checking out hash: {e}")
            break

        except GitCommandError as e:
            print(f"Error cloning repo: {e}, retrying...")
            if t == retries - 1:
                raise e
            time.sleep(5)

    for root, dirs, files in os.walk(clone_to):
        try:
            for file in files:
                if file.startswith("requirements") and file.endswith((".txt", ".pip")):
                    try:
                        requirements_path = os.path.join(root, file)
                        print(f" --- Installing requirements from {requirements_path}")
                        subprocess.run(["pip", "install", "-r", requirements_path], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"Error installing requirements: {e.stderr}")
        except Exception as e:
            print(f"Error installing requirements for {root}: {e}")

    # Try to run __init__.py for node
    # try:
    #     repo_name = repo_url.split("/")[-1].replace(".git", "")
    #     repo_init = f"{clone_to}/__init__.py"
    #     spec = importlib.util.spec_from_file_location(repo_name, repo_init)
    #     module = importlib.util.module_from_spec(spec)
    #     sys.modules[repo_name] = module
    #     spec.loader.exec_module(module)

    # except Exception as e:
    #     print(f"Error running __init__.py for {root}: {e}")


def download_models(downloads, comfyui_home):
    for file_path, url in downloads.items():
        if os.path.exists(file_path):
            print(f"Skipping {url} as {file_path} already exists")
        
        local_filepath = Path(comfyui_home, file_path)
        local_filepath.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading {url} ... to {local_filepath}, ... , {local_filepath.parent}")
        with httpx.stream("GET", url, follow_redirects=True) as stream:
            total = int(stream.headers["Content-Length"])
            with open(local_filepath, "wb") as f, tqdm(
                total=total, unit_scale=True, unit_divisor=1024, unit="B"
            ) as progress:
                num_bytes_downloaded = stream.num_bytes_downloaded
                for data in stream.iter_bytes():
                    f.write(data)
                    progress.update(
                        stream.num_bytes_downloaded - num_bytes_downloaded
                    )
                    num_bytes_downloaded = stream.num_bytes_downloaded


def install_nodes(snapshot_path, comfyui_home):
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)
    nodes = snapshot["git_custom_nodes"]
    for url, node in nodes.items():
        hash, _ = node["hash"], node["disabled"]
        repo_name = url.split("/")[-1].replace(".git", "")
        repo_dir = f"{comfyui_home}/custom_nodes/{repo_name}"
        clone_and_install(url, hash, clone_to=repo_dir)
    extra_downloads = snapshot.get("downloads")
    if extra_downloads:
        download_models(extra_downloads, comfyui_home)


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

    model_names_in_workflow = []
    find_model_names(workflow_data, extensions_to_find, model_names_in_workflow)
    
    download_dict = {}
    for key, value in models_data.items():
        for model_name in model_names_in_workflow:
            if model_name in key:
                download_dict[key] = value

    return download_dict

