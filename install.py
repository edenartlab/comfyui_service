import os
import subprocess
import time
import argparse
import json
import httpx
from tqdm import tqdm
from pathlib import Path
from git import Repo, GitCommandError



def clone_and_install(repo_url, hash, clone_to="repo_dir", retries=5):
    for _ in range(retries):        
        try:
            repo = Repo.clone_from(repo_url, clone_to)
            repo.submodule_update(recursive=True)    
            try:
                repo.git.checkout(hash)
            except Exception as e:
                print(f"Error checking out hash: {e}")

            for root, dirs, files in os.walk(clone_to):
                for file in files:
                    if file.startswith("requirements") and file.endswith((".txt", ".pip")):
                        try:
                            requirements_path = os.path.join(root, file)
                            subprocess.run(["pip", "install", "-r", requirements_path], check=True)
                        except subprocess.CalledProcessError as e:
                            print(f"Error installing requirements: {e.stderr}")

            break

        except GitCommandError as e:
            print(f"Error cloning repo: {e}, retrying...")
            time.sleep(5)


def download_models(snapshot_path, comfyui_home):
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    downloads = snapshot["downloads"]

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
        hash, disabled = node["hash"], node["disabled"]
        repo_name = url.split("/")[-1].replace(".git", "")
        repo_dir = f"{comfyui_home}/custom_nodes/{repo_name}"
        clone_and_install(url, hash, clone_to=repo_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Install nodes and download models.')
    parser.add_argument('--snapshot', type=str, 
    required=True, help='Path to the snapshot file')
    parser.add_argument('--comfyui-home', type=str, 
    default='/root/ComfyUI', help='Path to the ComfyUI home directory')

    args = parser.parse_args()
    snapshot_path = args.snapshot
    comfyui_home = args.comfyui_home

    install_nodes(snapshot_path, comfyui_home)
    download_models(snapshot_path, comfyui_home)