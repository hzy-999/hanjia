@echo off
cd /d "%~dp0"
echo Installing requirements...
pip install pyinstaller customtkinter requests

echo Cleaning up...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo Building EXE...
pyinstaller --noconsole --onefile --name "AquaGuard" --collect-all customtkinter run.py

echo Done! Output is in dist/AquaGuard.exe
