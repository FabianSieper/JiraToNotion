# JIRA to Notion Sync
This Python script syncs JIRA issues with a Notion database. It creates entries in a Notion database for JIRA issues, including additional information. Linked epics and Sprints are automatically added to separate Notion databases and linked to added Notion Jira issues.

## Installation

Execute the script `setup.bat` as an administrator. 
The script will
- Install python, if not already existent
- Install pip, if not already existent
- Install all required python packages

## Configuration
To configure the script to your Jira and Notion databases, replace the following values in the file `config.py`:
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

## Execution
Run the script by using the command
```
python main.py
```

### Modes
There are three different modes:
1. Update
2. Add Issues by Epic ISPI
3. Add Issues by Issue ISPI

#### 1. Update
For this, you can execute the script as follows:
```
python main.py
```
This addes Issues to the Notion Issue database, which are linked to Epics, stored in the Notion Epics database. Already added Issues are not added again. Linked Sprints are added to the Notion Sprints database.

#### 2. Update issues
For this, you can execute the script as follows:
```
python main.py --update-issues
```
This updates the status of all issues in the Notion databse according to the status in Jira. No new Issues are added and no other properties are overwritten

#### 3. Add Issues by Epic ISPI
For this, you can execute the script as follows:
```
python main.py --epics ISPI-123456 ISPI-987654 
```
Here, `ISPI-123456` and `ISPI-987654` are ISPI's of Jira Epics.

This takes all Issues linked to the Jira Epics and adds them to the Notion Issue database. The epics are added in the Notion Epics database and linked Sprints are added to the Notion Sprints database.

#### 4. Add Issues by Epic ISPI
For this, you can execute the script as follows:
```
python main.py --issues ISPI-123456 ISPI-987654 
```
Here, `ISPI-123456` and `ISPI-987654` are ISPI's of Jira Issues.

This adds the defined Issues to the Notion Isuse databse. Linked epics are added in the Notion Epics database and linked Sprints are added to the Notion Sprints database.