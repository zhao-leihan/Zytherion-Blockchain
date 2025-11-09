@echo off
echo Setting up Zytherion test environment...

:: Create necessary directories
if not exist "..\data" mkdir "..\data"
if not exist "..\ai_validator\models" mkdir "..\ai_validator\models"

echo Setup complete! You can now run: docker-compose up -d
pause