#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def explore_directory(path=".", max_depth=3, current_depth=0):
    """Recursively explore directory structure."""
    if current_depth > max_depth:
        return
    
    path = Path(path)
    if not path.exists():
        print(f"Path does not exist: {path}")
        return
    
    indent = "  " * current_depth
    if path.is_dir():
        print(f"{indent}{path.name}/")
        try:
            items = sorted(path.iterdir())
            for item in items:
                if item.is_dir():
                    explore_directory(item, max_depth, current_depth + 1)
                else:
                    print(f"{indent}  {item.name}")
        except PermissionError:
            print(f"{indent}  [Permission denied]")
    else:
        print(f"{indent}{path.name}")

def main():
    if len(sys.argv) > 1:
        explore_directory(sys.argv[1])
    else:
        explore_directory()

if __name__ == "__main__":
    main()
