# JIRA to Notion Sync
This Python script syncs JIRA issues with a Notion database. It creates entries in a Notion database for JIRA issues, including additional information. Linked epics and Sprints are automatically added to separate Notion databases and linked to added Notion Jira issues.

## Installation

Execute the script `setup.bat` as an administrator. 
The script will
- Install python, if not already existent
- Install pip, if not already existent
- Install all required python packages

## Configuration
To configure the script to your Jira and Notion databases, replace the following values in the file `bin/config.py`:
- NOTION_API_KEY: Your Notion API key
- NOTION_DATABASE_URL: The URL of your Notion database
- NOTION_DATABASE_NAME: The name of your Notion database (default: "Tasks")
- SPRINTS_DATABASE_URL: The URL of your Sprints database in Notion
- SPRINTS_DATABASE_NAME: The name of your Sprints database in Notion (default: "Sprints")
- EPICS_DATABASE_URL: The URL of your Epics database in Notion
- EPICS_DATABASE_NAME: The name of your Epics database in Notion (default: "Epics")
- JIRA_SERVER_URL: Your JIRA server URL
- JIRA_USERNAME: Your JIRA username
- JIRA_PASSWORD: Your JIRA password

Some of these values can also be set by creating equally named environment variables. Supported variables:
- NOTION_API_KEY
- JIRA_USERNAME
- JIRA_PASSWORD

## Execution and Modes

### Executing using Python
#### 1. Update
For this, you can execute the script as follows:
```
python main.py --update [--sprints sprint-90 sprint-91]
```
This addes Issues to the Notion Issue database, which are linked to Epics, stored in the Notion Epics database. Already added Issues are not added again. Also, already existent Notion Issues are updated. 
Issues to be updated can be narrowed down by setting the `--sprints` parameter. Only issues that belong to one of the defined sprints are updated.
Linked Sprints are added to the Notion Sprints database.

#### 2. Add Issues by Epic ISPI
For this, you can execute the script as follows:
```
python main.py --epics ISPI-123456 ISPI-987654 
```
Here, `ISPI-123456` and `ISPI-987654` are ISPI's of Jira Epics.

This takes all Issues linked to the Jira Epics and adds them to the Notion Issue database. The epics are added in the Notion Epics database and linked Sprints are added to the Notion Sprints database.

#### 3. Add Issues by Epic ISPI
For this, you can execute the script as follows:
```
python main.py --issues ISPI-123456 ISPI-987654 [--sprints sprint-90 sprint-91]
```
Here, `ISPI-123456` and `ISPI-987654` are ISPI's of Jira Issues.

This adds the defined Issues to the Notion Issue database. Issues to be added can be narrowed down by setting the `--sprints` parameter. Only issues that belong to one of the defined sprints are added.
Linked epics are added in the Notion Epics database and linked Sprints are added to the Notion Sprints database.

#### 4. Add Issues by Sprint
For this, you can execute the script as follows:
```
python main.py --sprints sprint-90 sprint-91
```

This adds Issues to the Notion Issue database which belong to at least one of the provided sprints. 
Linked epics are added in the Notion Epics database and linked Sprints are added to the Notion Sprints database.

### Alternative execution
The script can also be executed using `execute.bat` and `execute.sh`. They display all previsouly mentioned modes which can be selected by entering the corresponding number.