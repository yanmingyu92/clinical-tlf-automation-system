#!/usr/bin/env python3
"""
Update Author Information Script
Changes all author references to Jaime Yan throughout the codebase
"""

import os
import re
from pathlib import Path

def update_author_in_file(file_path, author_name="Jaime Yan"):
    """Update author information in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Common author patterns to replace
        patterns = [
            # Python docstrings and comments
            (r'Author:\s*[^\n]*', f'Author: {author_name}'),
            (r'@author\s*[^\n]*', f'@author {author_name}'),
            (r'Created by:\s*[^\n]*', f'Created by: {author_name}'),
            (r'Developed by:\s*[^\n]*', f'Developed by: {author_name}'),
            (r'# Author:\s*[^\n]*', f'# Author: {author_name}'),
            (r'# Created by:\s*[^\n]*', f'# Created by: {author_name}'),
            
            # JavaScript/HTML comments
            (r'//\s*Author:\s*[^\n]*', f'// Author: {author_name}'),
            (r'/\*\s*Author:\s*[^\n]*\*/', f'/* Author: {author_name} */'),
            
            # R comments
            (r'#\s*Author:\s*[^\n]*', f'# Author: {author_name}'),
            
            # Generic patterns
            (r'author\s*=\s*["\'][^"\']*["\']', f'author = "{author_name}"'),
            (r'"author":\s*"[^"]*"', f'"author": "{author_name}"'),
        ]
        
        # Apply replacements
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Add author header if file doesn't have one (for Python files)
        if file_path.suffix == '.py' and 'Author:' not in content and len(content.strip()) > 0:
            lines = content.split('\n')
            if lines[0].startswith('#!') or lines[0].startswith('#!/'):
                # Insert after shebang
                lines.insert(1, f'# Author: {author_name}')
            elif lines[0].startswith('"""') or lines[0].startswith("'''"):
                # Find end of docstring and insert after
                for i, line in enumerate(lines[1:], 1):
                    if line.strip().endswith('"""') or line.strip().endswith("'''"):
                        lines.insert(i + 1, f'# Author: {author_name}')
                        break
            else:
                # Insert at beginning
                lines.insert(0, f'# Author: {author_name}')
            content = '\n'.join(lines)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    print("🔄 Updating author information to Jaime Yan...")
    print()
    
    # File extensions to process
    extensions = {'.py', '.js', '.html', '.css', '.r', '.R', '.md', '.json', '.yml', '.yaml'}
    
    # Directories to process
    directories = ['app', 'scripts', 'config', 'templates']
    
    updated_files = []
    
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"📁 Processing {directory}/...")
            
            for file_path in dir_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in extensions:
                    if update_author_in_file(file_path):
                        updated_files.append(str(file_path))
                        print(f"  ✅ Updated: {file_path}")
    
    # Update root files
    root_files = ['README.md', 'CONTRIBUTING.md', 'setup.py']
    for filename in root_files:
        file_path = Path(filename)
        if file_path.exists():
            if update_author_in_file(file_path):
                updated_files.append(str(file_path))
                print(f"✅ Updated: {file_path}")
    
    print()
    print(f"🎉 Author update completed!")
    print(f"📊 Updated {len(updated_files)} files")
    
    if updated_files:
        print("\n📋 Updated files:")
        for file_path in updated_files[:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(updated_files) > 10:
            print(f"  ... and {len(updated_files) - 10} more files")
    
    print(f"\n👤 All code now attributed to: Jaime Yan")

if __name__ == "__main__":
    main()
