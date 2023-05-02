
# --------------------------------------------
# STATIC VARIABLES
# --------------------------------------------

# Replace with your Notion API key and database URL
# The NOTION_API_KEY can also be set, by creating a environment variable "NOTION_API_KEY"
NOTION_API_KEY = "your-notion-api-token"
ISSUES_DATABASE_URL = "your-issues-databse-url"
ISSUES_DATABASE_NAME = "Issues"
SPRINTS_DATABASE_URL = "your-sprints-databse-url"
SPRINTS_DATABASE_NAME = "Cycles / Sprints"
EPICS_DATABASE_URL = "your-epics-databse-url"
EPICS_DATABASE_NAME = "Epics"

# Replace with your JIRA credentials
JIRA_SERVER_URL = "https://your-jira-url.net/jira"
# The credentials can also be set, by creating environment variables with names "JIRA_USERNAME" and "JIRA_PASSWORD"
JIRA_USERNAME = ""
JIRA_PASSWORD = ""

# Maximum amount of characters a text property in notion can hold
NOTION_TEXT_FIELD_MAX_CHARS = 2000

# KOBRA number, which is used in JIRA to identify which Issue is mapped to which team
KOBRA_IDENTIFIER = "6449"