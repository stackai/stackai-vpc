#!/usr/bin/env python3
"""
StackAI Version Manager

This script updates the Docker image versions for StackAI services based on a JSON configuration file.
It updates the following files:
- stackend/docker-compose.yml (stackend-backend and stackend-celery-worker images)
- stackweb/Dockerfile (stackweb image)
- stackrepl/docker-compose.yml (stackrepl image)

Usage:
    python update_stackai_versions.py <version>
    
Example:
    python update_stackai_versions.py 1.0.2
"""

import json
import sys
import os
import re
from pathlib import Path

def load_versions_config(config_path):
    """Load the versions configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)

def find_version_config(versions_config, target_version):
    """Find the version configuration for the target version."""
    for version_obj in versions_config:
        if target_version in version_obj:
            return version_obj[target_version]
    return None

def update_stackend_compose(stackend_version):
    """Update stackend/docker-compose.yml with new versions."""
    file_path = Path("stackend/docker-compose.yml")
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update stackend-celery-worker image
        content = re.sub(
            r'image: stackai\.azurecr\.io/stackai/stackend-celery-worker:[^\s]+',
            f'image: stackai.azurecr.io/stackai/stackend-celery-worker:{stackend_version}',
            content
        )
        
        # Update stackend-backend image
        content = re.sub(
            r'image: stackai\.azurecr\.io/stackai/stackend-backend:[^\s]+',
            f'image: stackai.azurecr.io/stackai/stackend-backend:{stackend_version}',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {file_path} with stackend version {stackend_version}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def update_stackweb_dockerfile(stackweb_version):
    """Update stackweb/Dockerfile with new version."""
    file_path = Path("stackweb/Dockerfile")
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update FROM line with new stackweb version
        content = re.sub(
            r'FROM stackai\.azurecr\.io/stackai/stackweb:[^\s]+',
            f'FROM stackai.azurecr.io/stackai/stackweb:{stackweb_version}',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {file_path} with stackweb version {stackweb_version}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def update_stackrepl_compose(stackrepl_version):
    """Update stackrepl/docker-compose.yml with new version."""
    file_path = Path("stackrepl/docker-compose.yml")
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update stackrepl image
        content = re.sub(
            r'image: stackai\.azurecr\.io/stackai/stackrepl/stack-repl:[^\s]+',
            f'image: stackai.azurecr.io/stackai/stackrepl/stack-repl:{stackrepl_version}',
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {file_path} with stackrepl version {stackrepl_version}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("❌ Error: Version argument is required")
        print("")
        print("Usage:")
        print("  python update_stackai_versions.py <version>")
        print("")
        print("Example:")
        print("  python update_stackai_versions.py 1.0.2")
        sys.exit(1)
    
    target_version = sys.argv[1]
    
    # Get the script directory and config file path
    script_dir = Path(__file__).parent
    config_path = script_dir / "stackai-versions.json"
    
    # Change to the repository root directory
    repo_root = script_dir.parent.parent
    os.chdir(repo_root)
    
    print(f"🔄 Updating StackAI services to version {target_version}...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📄 Config file: {config_path}")
    
    # Load versions configuration
    versions_config = load_versions_config(config_path)
    
    # Find the version configuration
    version_config = find_version_config(versions_config, target_version)
    if not version_config:
        print(f"❌ Error: Version {target_version} not found in configuration")
        print("")
        print("Available versions:")
        for version_obj in versions_config:
            for version in version_obj.keys():
                print(f"  - {version}")
        sys.exit(1)
    
    print(f"📋 Version configuration found:")
    for service, version in version_config.items():
        print(f"  - {service}: {version}")
    print("")
    
    # Update each service
    success = True
    
    # Update stackend
    if 'stackend' in version_config:
        success &= update_stackend_compose(version_config['stackend'])
    
    # Update stackweb
    if 'stackweb' in version_config:
        success &= update_stackweb_dockerfile(version_config['stackweb'])
    
    # Update stackrepl
    if 'stackrepl' in version_config:
        success &= update_stackrepl_compose(version_config['stackrepl'])
    
    if success:
        print("")
        print(f"🎉 Successfully updated all StackAI services to version {target_version}")
        print("")
        print("Next steps:")
        print("  1. Review the changes: git diff")
        print("  2. Rebuild and restart services: make update")
    else:
        print("")
        print("❌ Some updates failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
