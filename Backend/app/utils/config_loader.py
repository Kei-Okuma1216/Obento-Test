import json
import os

def load_permission_map(path: str = "config/permission_map.json") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permissionマップファイルが見つかりません: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

