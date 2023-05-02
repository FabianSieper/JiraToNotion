@echo off

:MENU
echo.
echo Select an option:
echo 1. --update
echo 2. --update-issues
echo 3. --issues
echo 4. --epics
echo.
set /p OPTION="Enter the option number: "

if %OPTION%==1 goto UPDATE
if %OPTION%==2 goto UPDATE_ISSUES
if %OPTION%==3 goto ISSUES
if %OPTION%==4 goto EPICS

echo Invalid option. Exiting...
goto END

:UPDATE
cmd /c python main.py --update
goto END

:UPDATE_ISSUES
cmd /c python main.py --update-issues
goto END

:ISSUES
set /p ISSUES="Enter the issue IDs (space-separated): "
cmd /c python main.py --issues %ISSUES%
goto END

:EPICS
set /p EPICS="Enter the epic IDs (space-separated): "
cmd /c python main.py --epics %EPICS%
goto END

:END
