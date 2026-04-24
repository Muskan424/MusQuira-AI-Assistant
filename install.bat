@echo off
echo ============================================
echo     MusQuira AI Assistant - Installer
echo ============================================
echo.
echo [1/3] Installing core packages...
pip install openai SpeechRecognition pyttsx3 requests Pillow psutil

echo.
echo [2/3] Installing PyAudio...
pip install pyaudio
if %errorlevel% neq 0 (
    echo PyAudio failed. Trying pipwin fallback...
    pip install pipwin
    pipwin install pyaudio
)

echo.
echo [3/3] Installing face recognition (optional)...
echo Note: This may take a while. If it fails, set ENABLE_FACE_LOGIN=False in config.py
pip install cmake dlib face-recognition opencv-python numpy
if %errorlevel% neq 0 (
    echo face_recognition install failed - face login will be bypassed.
    echo You can still use all other features!
)

echo.
echo ============================================
echo   DONE! 
echo   1. Open config.py and add your OpenAI key
echo   2. Double-click run.bat to start MusQuira
echo ============================================
pause
