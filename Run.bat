@ECHO off
IF EXIST venv\ (
    GOTO run
) ELSE (

    ECHO ======================================
    ECHO Installing required Python packages...
    ECHO ======================================
    GOTO install
)

:install
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
ECHO .
ECHO .
ECHO .
ECHO .
ECHO .
GOTO run

:run
ECHO ======================================
ECHO     Starting... (Ctrl-C to quit)      
ECHO ======================================
.\venv\Scripts\python main.py
