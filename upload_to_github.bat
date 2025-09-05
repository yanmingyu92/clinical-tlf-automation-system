@echo off
echo ========================================
echo GitHub Upload Helper
echo ========================================
echo.

echo 🎯 Clinical TLF Automation System
echo 📤 Ready to upload to GitHub!
echo.

echo 📋 INSTRUCTIONS:
echo.
echo 1. First, create a GitHub repository:
echo    - Go to https://github.com/new
echo    - Repository name: clinical-tlf-automation-system
echo    - Description: AI-Powered Clinical Trial Reporting System
echo    - Make it Public (recommended)
echo    - DON'T initialize with README (we have files already)
echo    - Click "Create repository"
echo.

echo 2. Replace YOUR_USERNAME below with your actual GitHub username
echo.

set /p username="Enter your GitHub username: "

if "%username%"=="" (
    echo ❌ Username cannot be empty!
    pause
    exit /b 1
)

echo.
echo 🔗 Setting up remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/%username%/clinical-tlf-automation-system.git

echo.
echo 📤 Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 🎉 SUCCESS! Repository uploaded!
    echo ========================================
    echo.
    echo 🌐 Your repository is now available at:
    echo https://github.com/%username%/clinical-tlf-automation-system
    echo.
    echo 📋 Next steps:
    echo 1. Visit your repository on GitHub
    echo 2. Add repository topics: clinical-trials, ai, r, fda, automation
    echo 3. Create your first release (v1.0.0)
    echo 4. Share with the community!
    echo.
    echo 🎯 Your AI-powered clinical trial system is now live!
) else (
    echo.
    echo ❌ Upload failed. Common issues:
    echo 1. Make sure you created the GitHub repository first
    echo 2. Check your GitHub username is correct
    echo 3. Ensure you're logged into GitHub
    echo 4. Try running: git push -u origin main
)

echo.
echo Press any key to exit...
pause >nul
