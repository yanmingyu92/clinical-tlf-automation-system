# GitHub Upload Helper for Clinical TLF Automation System
# PowerShell Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Upload Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎯 Clinical TLF Automation System" -ForegroundColor Yellow
Write-Host "📤 Ready to upload to GitHub!" -ForegroundColor Green
Write-Host ""

Write-Host "📋 INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. First, create a GitHub repository:" -ForegroundColor White
Write-Host "   - Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   - Repository name: clinical-tlf-automation-system" -ForegroundColor Gray
Write-Host "   - Description: AI-Powered Clinical Trial Reporting System" -ForegroundColor Gray
Write-Host "   - Make it Public (recommended)" -ForegroundColor Gray
Write-Host "   - DON'T initialize with README (we have files already)" -ForegroundColor Gray
Write-Host "   - Click 'Create repository'" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Enter your GitHub username below:" -ForegroundColor White
Write-Host ""

$username = Read-Host "Enter your GitHub username"

if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "❌ Username cannot be empty!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🔗 Setting up remote repository..." -ForegroundColor Yellow

try {
    # Remove existing origin if it exists
    git remote remove origin 2>$null
    
    # Add new origin
    git remote add origin "https://github.com/$username/clinical-tlf-automation-system.git"
    
    Write-Host "✅ Remote repository configured" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Remote setup warning (this is usually fine): $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow

try {
    $result = git push -u origin main 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "🎉 SUCCESS! Repository uploaded!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 Your repository is now available at:" -ForegroundColor Cyan
        Write-Host "https://github.com/$username/clinical-tlf-automation-system" -ForegroundColor Blue
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Yellow
        Write-Host "1. Visit your repository on GitHub" -ForegroundColor Gray
        Write-Host "2. Add repository topics: clinical-trials, ai, r, fda, automation" -ForegroundColor Gray
        Write-Host "3. Create your first release (v1.0.0)" -ForegroundColor Gray
        Write-Host "4. Share with the community!" -ForegroundColor Gray
        Write-Host ""
        Write-Host "🎯 Your AI-powered clinical trial system is now live!" -ForegroundColor Green
        
        # Open the repository in browser
        $openBrowser = Read-Host "Would you like to open the repository in your browser? (y/n)"
        if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
            Start-Process "https://github.com/$username/clinical-tlf-automation-system"
        }
        
    } else {
        Write-Host ""
        Write-Host "❌ Upload failed. Error details:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        Write-Host ""
        Write-Host "Common solutions:" -ForegroundColor Yellow
        Write-Host "1. Make sure you created the GitHub repository first" -ForegroundColor Gray
        Write-Host "2. Check your GitHub username is correct" -ForegroundColor Gray
        Write-Host "3. Ensure you're logged into GitHub" -ForegroundColor Gray
        Write-Host "4. Try running manually: git push -u origin main" -ForegroundColor Gray
        Write-Host ""
        Write-Host "If you need to authenticate:" -ForegroundColor Yellow
        Write-Host "- Use GitHub Desktop, or" -ForegroundColor Gray
        Write-Host "- Set up a Personal Access Token" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Error during push: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
