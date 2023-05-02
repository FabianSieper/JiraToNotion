
# --------------------------------------------
# STATIC VARIABLES
# --------------------------------------------

# Replace with your Notion API key and database URL
NOTION_API_KEY = "your-notion-api-key"
NOTION_DATABASE_URL = "issues-database-url"
NOTION_DATABASE_NAME = "Issues"
SPRINTS_DATABASE_URL = "sprints-database-url"
SPRINTS_DATABASE_NAME = "Cycles / Sprints"
EPICS_DATABASE_URL = "epics-database-url"
EPICS_DATABASE_NAME = "Epics"

# Replace with your JIRA credentials
JIRA_SERVER_URL = "https://your-jira-url.com/issues"
JIRA_USERNAME = "jira-username"
JIRA_PASSWORD = "jira-password"

# Maximum amount of characters a text property in notion can hold
NOTION_TEXT_FIELD_MAX_CHARS = 2000

# The JIRA issue type which is set, if none is given from JIRA
DEFAULT_NOTION_LABEL = "Empty"

# Amount of sites that are fetched from JIRA
AMOUNT_JIRA_RESULTS = 300

# KOBRA number, which is used in JIRA to identify which Issue is mapped to which team
KOBRA_IDENTIFIER = "6449"