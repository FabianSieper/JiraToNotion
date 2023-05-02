@echo off

:MENU
echo.
echo Select an option:
echo 1. --update: Update Notion issues and import missing Issues, based on imported Epics
echo 2. --issues: Import Notion Issues by providing a list of Issue ISPI's
echo 3. --epics: Import Notion Issues by providing a list of Epic ISPI's. Issues linked to Epics will be imported
echo 4. --sprints: Import Notion Issues by providing a list of sprints. Issues linked to at least one of those sprints will eb imported
echo.
set /p OPTION="Enter the option number: "

if %OPTION%==1 goto UPDATE
if %OPTION%==2 goto ISSUES
if %OPTION%==3 goto EPICS
if %OPTION%==4 goto SPRINTS

echo Invalid option. Exiting...
goto END

:UPDATE
set /p SPRINTS="Enter sprint names. You also can enter none. (space-separated): "
cmd /c python main.py --update --sprints %SPRINTS%
goto END

:ISSUES
set /p ISSUES="Enter the issue IDs (space-separated): "
cmd /c python main.py --issues %ISSUES%
goto END

:EPICS
set /p EPICS="Enter the epic IDs (space-separated): "
set /p SPRINTS="Enter sprint names. You also can enter none. (space-separated): "
cmd /c python main.py --epics %EPICS% --sprints %SPRINTS%
goto END

:SPRINTS
set /p SPRINTS="Enter sprint names. (space-separated): "
cmd /c python main.py --sprints %SPRINTS%
goto END

:END
