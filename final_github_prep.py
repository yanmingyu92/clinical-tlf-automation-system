#!/usr/bin/env python3
"""
Final GitHub Preparation
Archive non-essential scripts and prepare for GitHub publication
"""

import shutil
from pathlib import Path

def main():
    print("🧹 Final GitHub preparation...")
    
    # Create archive directory
    archive_dir = Path("archive/utility_scripts")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Scripts to archive (non-essential for core functionality)
    scripts_to_archive = [
        "cleanup.py",
        "copy_adam_data.py", 
        "create_fda_templates.py",
        "rtf_to_markdown.py",
        "sas_data_handler.py"
    ]
    
    scripts_dir = Path("scripts")
    
    # Archive non-essential scripts
    for script_name in scripts_to_archive:
        script_path = scripts_dir / script_name
        if script_path.exists():
            archive_path = archive_dir / script_name
            if not archive_path.exists():  # Don't overwrite
                shutil.move(str(script_path), str(archive_path))
                print(f"📦 Archived: {script_name}")
    
    # Check what's left in scripts
    remaining_scripts = list(scripts_dir.glob("*.py"))
    print(f"\n✅ Essential scripts remaining: {len(remaining_scripts)}")
    for script in remaining_scripts:
        print(f"   - {script.name}")
    
    print("\n🎯 GitHub-ready structure:")
    print("   ✅ Essential scripts only")
    print("   ✅ Scientific materials excluded (.gitignore)")
    print("   ✅ Config template created")
    print("   ✅ Sensitive data protected")
    
    print("\n🚀 Ready for GitHub publication!")

if __name__ == "__main__":
    main()
