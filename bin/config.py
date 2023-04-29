# config.py

# Replace with your Notion API key and database URL
NOTION_API_KEY = "your_notion_api_key"
NOTION_DATABASE_URL = "your_notion_database_url"
NOTION_DATABASE_NAME = "Tasks"
SPRINTS_DATABASE_URL = "your_sprints_database_url"
SPRINTS_DATABASE_NAME = "Sprints"
EPICS_DATABASE_URL = "your_epics_database_url"
EPICS_DATABASE_NAME = "Epics"

# Maximum amount of characters a text property in notion can hold
NOTION_TEXT_FIELD_MAX_CHARS = 2000

# The JIRA issue type which is set, if none is given from JIRA
DEFAULT_NOTION_LABEL = "Empty"

# Amount of sites that are fetched from JIRA
AMOUNT_JIRA_RESULTS = 100

# Replace with your JIRA credentials
JIRA_SERVER_URL = "https://your_jira_server_url"
JIRA_USERNAME = "your_jira_username"
JIRA_PASSWORD = "your_jira_password"

CAVORS_SPRINT_PREFIX = "CaVORS-"

# Filter which jira issues to skip, based on the title
DESCRIPTION_FILTER_NEG = ["[GitHub]", "[Github]"]
SPRINT_FILTER_POS = [CAVORS_SPRINT_PREFIX]
LABEL_FILTER_NEG = ["Defect"]