import json
from collections import defaultdict, deque
import argparse
import os

parser = argparse.ArgumentParser(description="For a giving operation, creates a graph of shapes it references in the order of dependency.")
parser.add_argument("input_file", type=str, help="Path to the JSON file.")
parser.add_argument("operation", type=str, help="Operation to analyze.")

args = parser.parse_args()
input_path = args.input_file
request_op = args.operation

with open(input_path, "r") as f:
    data = json.load(f)

shapes = data.get("shapes", {})
operations = data.get("operations", {})

# Build a dependency graph: parent -> [children] for shapes references in other shapes
refs = defaultdict(set)

if (operations.get(request_op) is None):
    print(f"Operation '{request_op}' not found in the JSON file.")
    exit(1)

if (operations.get(request_op, {}).get("input", {}).get("shape") is not None):
    refs[request_op].add(operations.get(request_op, {}).get("input", {}).get("shape"))
if (operations.get(request_op, {}).get("output", {}).get("shape") is not None):
    refs[request_op].add(operations.get(request_op, {}).get("output", {}).get("shape"))
if (operations.get(request_op, {}).get("errors") is not None):
    for error in operations[request_op]["errors"]:
        if (error.get("shape") is not None):
            refs[request_op].add(error.get("shape"))

for parent, val in shapes.items():
    t = val.get("type")
    if t == "structure":
        for member in val.get("members", {}).values():
            if member.get("isNtnxSupported", True) == False:
                continue
            refs[parent].add(member.get("shape"))
    elif t == "list":
        if val.get("isNtnxSupported", True) == False:
            continue
        shape = val.get("member", {}).get("shape")
        if shape:
            refs[parent].add(shape)
    elif t == "map":
        if val.get("isNtnxSupported", True) == False:
            continue
        if val.get("key", {}).get("shape"):
            refs[parent].add(val["key"]["shape"])
        if val.get("value", {}).get("shape"):
            refs[parent].add(val["value"]["shape"])

# Print the dependency graph
stack = [(request_op, 0)] 
while stack:
    current, depth = stack.pop()
    # print("  " * (depth-1) + "|-" * (depth > 0) + current)
    if (depth == 1 and shapes.get(current, {}).get("isNtnxSupported", True) == False):
        continue
    print("    " * depth + current)
    for child in sorted(refs.get(current, []), reverse=True):
        stack.append((child, depth + 1))
