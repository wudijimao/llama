#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

import os
import requests
import hashlib

def wget(url, file_path):
    wget_fake_header = {'User-Agent': 'Wget/1.20.3 (linux-gnu)'}
    temp_file_path = file_path + '.tmp'
    file_size = 0
    if os.path.exists(file_path):
        return file_path
    elif os.path.exists(temp_file_path):
        file_size = os.path.getsize(temp_file_path)
        headers = {'Range': f'bytes={file_size}-', 'User-Agent': 'Wget/1.20.3 (linux-gnu)'}
        response = requests.get(url, headers=headers, stream=True)
        mode = 'ab'
    else:
        response = requests.get(url, headers=wget_fake_header, stream=True)
        mode = 'wb'
    total_size = int(response.headers.get('Content-Length', 0))
    block_size = 8192
    wrote = file_size
    with open(temp_file_path, 'wb') as f:
        f.seek(0, os.SEEK_END)
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                wrote += len(chunk)
                progress = int(50 * wrote / total_size)
                print('\r[{}{}] {:.1f}%'.format('#' * progress, ' ' * (50 - progress), 100 * wrote / total_size), end='')
    os.rename(temp_file_path, file_path)
    return file_path

presigned_url = input("Enter the URL from email: ")
print("")
model_size = input("Enter the list of models to download without spaces (7B,13B,70B,7B-chat,13B-chat,70B-chat), or press Enter for all: ")
target_folder = "."             # where all files should end up
os.makedirs(target_folder, exist_ok=True)

if model_size == "":
    model_size = "7B,13B,70B,7B-chat,13B-chat,70B-chat"

print("Downloading LICENSE and Acceptable Usage Policy")
wget(presigned_url.replace('*', "LICENSE"), os.path.join(target_folder, "LICENSE"))
wget(presigned_url.replace('*', "USE_POLICY.md"), os.path.join(target_folder, "USE_POLICY.md"))

print("Downloading tokenizer")
wget(presigned_url.replace('*', "tokenizer.model"), os.path.join(target_folder, "tokenizer.model"))
wget(presigned_url.replace('*', "tokenizer_checklist.chk"), os.path.join(target_folder, "tokenizer_checklist.chk"))

def check_md5(file_path, checksum):
    with open(file_path, 'rb') as f:
        data = f.read()
        md5 = hashlib.md5(data).hexdigest()
        return md5 == checksum

def check_checksums(folder_path, checklist_path):
    with open(checklist_path) as f:
        for line in f:
            checksum, file_name = line.strip().split()
            file_path = os.path.join(folder_path, file_name)
            if check_md5(file_path, checksum):
                print(f"{file_name}: OK")
            else:
                print(f"{file_name}: FAILED")

check_checksums(target_folder, os.path.join(target_folder, "tokenizer_checklist.chk"))

for model in model_size.split(','):
    if model == "7B":
        shard = 0
        model_path = "llama-2-7b"
    elif model == "7B-chat":
        shard = 0
        model_path = "llama-2-7b-chat"
    elif model == "13B":
        shard = 1
        model_path = "llama-2-13b"
    elif model == "13B-chat":
        shard = 1
        model_path = "llama-2-13b-chat"
    elif model == "70B":
        shard = 7
        model_path = "llama-2-70b"
    elif model == "70B-chat":
        shard = 7
        model_path = "llama-2-70b-chat"

    print(f"Downloading {model_path}")
    os.makedirs(os.path.join(target_folder, model_path), exist_ok=True)

    for s in range(shard + 1):
        wget(presigned_url.replace('*', f"{model_path}/consolidated.{s:02d}.pth"), os.path.join(target_folder, model_path, f"consolidated.{s:02d}.pth"))

    wget(presigned_url.replace('*', f"{model_path}/params.json"), os.path.join(target_folder, model_path, "params.json"))
    wget(presigned_url.replace('*', f"{model_path}/checklist.chk"), os.path.join(target_folder, model_path, "checklist.chk"))
    
    print("Checking checksums")
    check_checksums(os.path.join(target_folder, model_path), os.path.join(target_folder, model_path, "checklist.chk"))
