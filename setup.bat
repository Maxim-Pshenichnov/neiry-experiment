@echo off
echo Creating virtual environment...
python -m venv venv
echo Activating venv...
call venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
echo Setup complete!
echo To activate venv manually: venv\Scripts\activate
pause