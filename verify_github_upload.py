#!/usr/bin/env python3
"""
GitHub Upload Verification Script
Checks if all required files are properly tracked by git
Author: Jaime Yan
"""

import subprocess
import os
from pathlib import Path

def run_git_command(command):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def main():
    print("🔍 Verifying GitHub Upload Status...")
    print("=" * 50)
    
    # Check if we're in a git repository
    output, code = run_git_command("git status --porcelain")
    if code != 0:
        print("❌ Not in a git repository or git not available")
        return
    
    # Check git status
    print("📋 Git Status:")
    if output:
        print("⚠️ Uncommitted changes:")
        print(output)
    else:
        print("✅ Working directory clean")
    
    print()
    
    # Check if figures are tracked
    print("🎨 Checking Figure Files:")
    figure_files = [
        "github_assets/figures/fig1-system-architecture-overview.svg",
        "github_assets/figures/fig2-workflow-overview.svg", 
        "github_assets/figures/fig3-performance-overview.svg",
        "github_assets/figures/fig4-rag-overview.svg",
        "github_assets/figures/fig2a-step1-analysis.svg"
    ]
    
    for figure in figure_files:
        if Path(figure).exists():
            # Check if file is tracked by git
            output, code = run_git_command(f"git ls-files {figure}")
            if output:
                print(f"✅ {figure} - Tracked by git")
            else:
                print(f"❌ {figure} - NOT tracked by git")
        else:
            print(f"❌ {figure} - File missing")
    
    print()
    
    # Check remote repository
    print("🌐 Remote Repository:")
    output, code = run_git_command("git remote -v")
    if code == 0 and output:
        print("✅ Remote configured:")
        for line in output.split('\n'):
            if 'origin' in line:
                print(f"   {line}")
    else:
        print("❌ No remote repository configured")
    
    print()
    
    # Check last commit
    print("📝 Last Commit:")
    output, code = run_git_command("git log --oneline -1")
    if code == 0:
        print(f"✅ {output}")
    else:
        print("❌ No commits found")
    
    print()
    
    # Check if push is needed
    print("📤 Push Status:")
    output, code = run_git_command("git status -uno")
    if "Your branch is ahead" in output:
        print("⚠️ Local commits need to be pushed")
        print("Run: git push origin main")
    elif "Your branch is up to date" in output:
        print("✅ All commits pushed to remote")
    else:
        print("ℹ️ Status unclear - check manually")
    
    print()
    print("=" * 50)
    print("🎯 Summary:")
    print("If all figures show ✅ 'Tracked by git', your SVG files should")
    print("display properly on GitHub after pushing.")
    print()
    print("If any files show ❌, run:")
    print("  git add github_assets/figures/")
    print("  git commit -m 'Add missing figure files'")
    print("  git push origin main")

if __name__ == "__main__":
    main()
