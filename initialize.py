#!/usr/bin/env python3
"""
Smart Kart Initialization Script
-------------------------------
This script initializes the project structure and creates necessary directories.
"""

import os
import sys
import shutil
from pathlib import Path
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Smart Kart Initialization")
    parser.add_argument('-f', '--force', action='store_true', help='Force recreation of directories')
    return parser.parse_args()

def create_directory(path, force=False):
    """Create a directory if it doesn't exist or if force is True."""
    path = Path(path)
    if path.exists() and not path.is_dir():
        print(f"Error: {path} exists but is not a directory")
        return False
        
    if path.exists() and path.is_dir() and force:
        shutil.rmtree(path)
        
    if not path.exists():
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")
        
    return True

def main():
    """Main initialization function."""
    args = parse_args()
    
    print("Smart Kart Project Initializer")
    print("==============================")
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    
    # Directories to create
    directories = [
        project_root / "src" / "sensors",
        project_root / "src" / "hardware",
        project_root / "src" / "utils",
        project_root / "src" / "controllers",
        project_root / "src" / "ui",
        project_root / "tests",
        project_root / "docs",
        project_root / "assets" / "audio",
        project_root / "assets" / "images",
        project_root / "data",
        project_root / "models",
        project_root / "logs"
    ]
    
    # Create directories
    for directory in directories:
        create_directory(directory, args.force)
    
    # Make sure __init__.py files exist in all Python package directories
    for directory in directories:
        if directory.parent.name == "src" or directory.name in ["sensors", "hardware", "utils", "controllers", "ui"]:
            init_file = directory / "__init__.py"
            if not init_file.exists():
                with open(init_file, 'w') as f:
                    f.write(f'"""\n{directory.name.capitalize()} package for Smart Kart\n"""\n')
                print(f"Created {init_file}")
    
    # Ensure config.yaml is in place
    config_file = project_root / "config.yaml"
    if not config_file.exists():
        print("Warning: config.yaml not found. Please create it or copy from an example.")
    else:
        print(f"Configuration file exists: {config_file}")
    
    # Create empty README files in empty directories
    for directory in directories:
        if not any(directory.iterdir()) and directory.is_dir():
            readme_file = directory / "README.md"
            with open(readme_file, 'w') as f:
                f.write(f"# {directory.name.capitalize()} Directory\n\n")
                f.write(f"This directory is used for {directory.name} files for the Smart Kart project.\n")
            print(f"Created README in empty directory: {directory}")
    
    print("\nInitialization complete!")
    print("You can now run the Smart Kart system with:")
    print("  python src/main.py")
    print("Or run the test script with:")
    print("  python test_system.py")

if __name__ == "__main__":
    main() 