import json
import argparse
import os
parser = argparse.ArgumentParser(description="List operations from a JSON file.")
parser.add_argument("file", type=str, help="Path to the JSON file.")
args = parser.parse_args()
file_path = args.file

with open(file_path, "r") as f:
    data = json.load(f)

operations = data.get("operations", {})

i = 0
for op_key, op_val in operations.items():
    if op_val.get("isNtnxSupported", True) is False:
        continue
    i += 1
    print(f"{i}. {op_key}")

