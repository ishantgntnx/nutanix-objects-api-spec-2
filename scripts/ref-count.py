# This scripts reports referance count of each shape in the given API spec JSON file
# both in operations and other shapes. It also include transitive references.
# For example, if ShapeA references ShapeB and ShapeB references ShapeC,
# then ShapeA is considered to reference both ShapeB and ShapeC.
# Similarly, if OperationA references ShapeA, then OperationA is considered to reference
# ShapeA, ShapeB, and ShapeC.
# If any shape is not referenced by any operation or other shape, it is removed from the JSON file.
#

# Use --dry-run to only report the unreferenced shapes without removing them.


import json
from collections import defaultdict, deque
import argparse
import os

parser = argparse.ArgumentParser(description="Count references of shapes in a JSON file and remove unreferenced shapes.")
parser.add_argument("input_file", type=str, help="Path to the JSON file.")
parser.add_argument("--output-file", type=str, help="Path to the output JSON file after removing unreferenced shapes.")
parser.add_argument("--dry-run", action="store_true", help="Only report unreferenced shapes without removing them.")

args = parser.parse_args()
input_path = args.input_file
output_path = args.output_file
dry_run = args.dry_run

if not input_path:
    print("Error: input_file argument is required.")
    exit(1)

if not dry_run and not output_path:
    print("Error: output_file argument is required unless --dry-run is specified.")
    exit(1)

with open(input_path, "r") as f:
    data = json.load(f)

shapes = data.get("shapes", {})
operations = data.get("operations", {})

# Build reverse dependency graph: child -> [parents] for shapes references in other shapes
reverse_refs = defaultdict(set)
for parent, val in shapes.items():
    t = val.get("type")
    if t == "structure":
        for member in val.get("members", {}).values():
            reverse_refs[member.get("shape")].add(parent)
    elif t == "list":
        shape = val.get("member", {}).get("shape")
        if shape:
            reverse_refs[shape].add(parent)
    elif t == "map":
        if val.get("key", {}).get("shape"):
            reverse_refs[val["key"]["shape"]].add(parent)
        if val.get("value", {}).get("shape"):
            reverse_refs[val["value"]["shape"]].add(parent)

# Traverse once per shape using BFS on reverse_refs
shape_ref_count = {}
op_ref_count = {}
shapes_to_remove = []
for shape_key in shapes:
    visited = set()
    q = deque([shape_key])
    while q:
        cur = q.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        for parent in reverse_refs.get(cur, []):
            if parent not in visited:
                q.append(parent)

    shape_ref_count[shape_key] = len(visited) - 1  # exclude itself

    # Find operations referencing this shape or any of its ancestors
    op_dependencies = set()
    for op_name, op_data in operations.items():
        if op_data.get("input", {}).get("shape") in visited:
            op_dependencies.add(op_name)
        if op_data.get("output", {}).get("shape") in visited:
            op_dependencies.add(op_name)
        for error in op_data.get("errors", []):
            if error.get("shape") in visited:
                op_dependencies.add(op_name)

    op_ref_count[shape_key] = len(op_dependencies)

    print(f"{shape_key}: n(shapes)={shape_ref_count[shape_key]}, n(ops)={op_ref_count[shape_key]}")
    if shape_ref_count[shape_key] == 0 and op_ref_count[shape_key] == 0:
        shapes_to_remove.append(shape_key)

print("\n===================================\n")
print(f"Total unreferenced shapes: {len(shapes_to_remove)}")
for shape in shapes_to_remove:
    print(shape)

if dry_run:
    print("Dry run mode. No shapes will be removed.")
    exit(0)

# Remove unreferenced shapes from the original data
for shape in shapes_to_remove:
    if shape in data["shapes"]:
        del data["shapes"][shape]

# Write the updated data
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)
