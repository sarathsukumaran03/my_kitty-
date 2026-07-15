import ast
import sys

BUILTIN_MODULES = {
    "sys", "os", "time", "threading", "tkinter",
    "json", "math", "re", "datetime", "pathlib"
}

with open("mouse_pointer.py", "r", encoding="utf-8") as f:
    tree = ast.parse(f.read())

imports = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for name in node.names:
            imports.add(name.name.split(".")[0])

    elif isinstance(node, ast.ImportFrom):
        if node.module:
            imports.add(node.module.split(".")[0])

requirements = sorted(imports - BUILTIN_MODULES)

with open("requirements.txt", "w") as f:
    for req in requirements:
        f.write(req + "\n")

print("requirements.txt generated")