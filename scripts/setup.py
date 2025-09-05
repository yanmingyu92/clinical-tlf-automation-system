"""
Setup script for R TLF System
This script performs initial setup tasks:
1. Create necessary directories
2. Copy RTF templates to the reference directory
3. Install required Python packages
4. Check R installation and required packages
"""
# Author: Jaime Yan
import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

def create_directories():
    """Create necessary directories for the project"""
    dirs_to_create = [
        os.path.join(project_root, "data", "cache"),
        os.path.join(project_root, "data", "reference_templates"),
        os.path.join(project_root, "data", "vector_db"),
    ]
    
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")

def copy_rtf_templates():
    """Copy RTF templates from the parent data directory to reference_templates"""
    parent_data_dir = os.path.abspath(os.path.join(project_root, "..", "data"))
    target_dir = os.path.join(project_root, "data", "reference_templates")
    
    # Check if source directory exists
    if not os.path.exists(parent_data_dir):
        logger.warning(f"Source directory not found: {parent_data_dir}")
        return
    
    # Copy RTF files
    rtf_files = [f for f in os.listdir(parent_data_dir) if f.lower().endswith('.rtf')]
    
    if not rtf_files:
        logger.warning(f"No RTF files found in {parent_data_dir}")
        return
    
    logger.info(f"Found {len(rtf_files)} RTF files to copy")
    
    for rtf_file in rtf_files:
        source_file = os.path.join(parent_data_dir, rtf_file)
        target_file = os.path.join(target_dir, rtf_file)
        
        if not os.path.exists(target_file):
            shutil.copy2(source_file, target_file)
            logger.info(f"Copied {rtf_file} to reference templates directory")
        else:
            logger.info(f"File already exists: {target_file}")

def install_python_packages():
    """Install required Python packages using pip"""
    requirements_file = os.path.join(project_root, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return
    
    logger.info("Installing Python packages...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            check=True
        )
        logger.info("Python packages installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing Python packages: {str(e)}")

def check_r_installation():
    """Check R installation and required packages"""
    logger.info("Checking R installation...")
    
    try:
        # Check R installation
        result = subprocess.run(
            ["Rscript", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            r_version = result.stderr.strip() or result.stdout.strip()
            logger.info(f"R is installed: {r_version}")
        else:
            logger.error("R installation check failed")
            return False
        
        # Create a temporary R script to check and install required packages
        r_script = """
        required_packages <- c(
          "tidyverse", "gt", "ggplot2", "knitr", "dplyr", "flextable", 
          "haven", "readxl", "rmarkdown", "officer"
        )
        
        missing_packages <- required_packages[!required_packages %in% installed.packages()[,"Package"]]
        
        if(length(missing_packages) > 0) {
          cat("Missing R packages:", paste(missing_packages, collapse=", "), "\n")
          cat("Installing missing R packages...\n")
          
          install.packages(missing_packages, repos="https://cran.rstudio.com/")
          
          still_missing <- missing_packages[!missing_packages %in% installed.packages()[,"Package"]]
          
          if(length(still_missing) > 0) {
            cat("Failed to install some packages:", paste(still_missing, collapse=", "), "\n")
            quit(status=1)
          } else {
            cat("All required R packages installed successfully\n")
          }
        } else {
          cat("All required R packages already installed\n")
        }
        """
        
        # Write the script to a temporary file
        script_path = os.path.join(project_root, "temp_r_check.R")
        with open(script_path, "w") as f:
            f.write(r_script)
        
        # Run the script
        try:
            r_result = subprocess.run(
                ["Rscript", script_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(r_result.stdout)
            
            if r_result.stderr:
                logger.warning(f"R package check warnings: {r_result.stderr}")
                
            if r_result.returncode != 0:
                logger.error("R package check failed")
                return False
        
        finally:
            # Clean up temporary script
            if os.path.exists(script_path):
                os.remove(script_path)
        
        return True
    
    except FileNotFoundError:
        logger.error("R executable not found. Please install R and make sure it's in your PATH.")
        return False
    
    except Exception as e:
        logger.error(f"Error checking R installation: {str(e)}")
        return False

def create_config_if_not_exists():
    """Create default config.json if it doesn't exist"""
    config_dir = os.path.join(project_root, "config")
    config_file = os.path.join(config_dir, "config.json")
    
    if os.path.exists(config_file):
        logger.info(f"Config file already exists: {config_file}")
        return
    
    logger.info(f"Creating default config file: {config_file}")
    
    # Make sure the directory exists
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    # Default configuration
    default_config = {
        "API": {
            "type": "deepseek",
            "base_url": "https://dseek.aikeji.vip",
            "API_KEY": "",
            "API_VERSION": "2023-12-01"
        },
        "model": {
            "default": {
                "model_name": "deepseek-chat",
                "available": True
            },
            "vision": {
                "model_name": "deepseek-vision",
                "available": False
            }
        },
        "model_context_window": {
            "deepseek-chat": 32000
        },
        "rag": {
            "embedding_model": "deepseek-embedding",
            "vector_db_path": "data/vector_db",
            "chunk_size": 512,
            "chunk_overlap": 128,
            "top_k": 5
        },
        "r_interpreter": {
            "use_rpy2": True,
            "r_home": "",
            "default_libraries": [
                "tidyverse",
                "gt",
                "ggplot2",
                "knitr",
                "dplyr",
                "flextable"
            ]
        },
        "template_storage": {
            "reference_path": "data/reference_templates"
        },
        "ui": {
            "theme": "light",
            "max_history": 50,
            "port": 7860
        }
    }
    
    # Write the configuration file
    import json
    with open(config_file, "w") as f:
        json.dump(default_config, f, indent=2)
    
    logger.info("Created default configuration file")

def main():
    """Main function to run setup tasks"""
    logger.info("Starting R TLF System setup")
    
    # Create directories
    create_directories()
    
    # Create config file if it doesn't exist
    create_config_if_not_exists()
    
    # Copy RTF templates
    copy_rtf_templates()
    
    # Install Python packages
    install_python_packages()
    
    # Check R installation
    r_check_result = check_r_installation()
    
    logger.info("Setup completed" + (" successfully" if r_check_result else " with warnings"))
    
    # Provide instructions for next steps
    print("\n=== Setup Completed ===")
    print("\nTo start the R TLF System, run:")
    print(f"cd {project_root}")
    print("python app/main.py")
    print("\nMake sure to set your DeepSeek API key in config/config.json before starting!")

if __name__ == "__main__":
    main() 