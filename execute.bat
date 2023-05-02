@echo off

:MENU
echo.
echo Select an option:
echo 1. Update Notion issues and import missing Issues, based on imported Epics
echo 2. Import Notion Issues by providing a list of Issue ISPI's
echo 3. Import Notion Issues by providing a list of Epic ISPI's. Issues linked to Epics will be imported
echo.
set /p OPTION="Enter the option number: "

if %OPTION%==1 goto UPDATE
if %OPTION%==2 goto ISSUES
if %OPTION%==3 goto EPICS

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
