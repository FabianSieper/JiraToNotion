from notion_client import Client
from jira import JIRA
from tqdm import tqdm
from bin.config import *
from bin.helper_functions import *
from bin.notion_jira_connector import *
# --------------------------------------------
# Dynamic variables
# --------------------------------------------
amount_issues_skipped = 0

# --------------------------------------------
# SCRIPT
# --------------------------------------------

def setup():

    # Initialize clients
    notion = Client(auth=NOTION_API_KEY)
    jira = JIRA(server=JIRA_SERVER_URL, basic_auth=(JIRA_USERNAME, JIRA_PASSWORD))

    # Retrieve the Notion-JIRA-issue database
    database_id = get_database_id(notion, NOTION_DATABASE_URL, NOTION_DATABASE_NAME)
    print_info("Found issues-database with id" + database_id)

    # Retrieve the Notion-Sprint database
    sprints_database_id = get_database_id(notion, SPRINTS_DATABASE_URL, SPRINTS_DATABASE_NAME)
    print_info("Found sprints-database with id " + sprints_database_id)

    # Retrieve the Notion-Epics database
    epics_database_id = get_database_id(notion, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)
    print_info("Found epics-database with id " + epics_database_id)

    return notion, jira, database_id, sprints_database_id, epics_database_id


def add_notion_entries_loop(jira, notion, database_id, sprints_database_id, epic_database_id, issues, existing_ispis):
    
    global amount_issues_skipped

    # Add JIRA issues to the Notion database if not already present
    for issue in tqdm(issues, "Writing issues to notion database ..."):

        issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, epic_ispi, issue_assignee = get_jira_issue_information(issue)

        # Skip issues
        if isIssueSkipped(issue, existing_ispis):
            print_info("Skipped JIRA issue '" + issue_summary + "'")
            amount_issues_skipped += 1
            continue

        # Get or create sprint pages in the sprints database, but only if Sprint name has prefix CAVORS_SPRINT_PREFIX
        sprint_pages = []
        if issue_sprints:
            sprint_pages = [{"id": get_or_create_sprint_page(notion, sprints_database_id, sprint)} for sprint in issue_sprints if sprint.startswith(CAVORS_SPRINT_PREFIX)]
            
        # Get or create epic pages in the epics database
        epic_page = None
        if epic_ispi:
            epic_page = [{"id": get_or_create_epic_page(jira, notion, epic_database_id, epic_ispi)}]

        # Create page in notion databse
        new_page = {
            "Summary": {"title": [{"text": {"content": issue_summary}}]},
            "Status": {"status": {"name": issue_status}},
            "URL": {"url": issue_url},
            "Description": {"rich_text": [{"text": {"content": issue_description if issue_description else ""}}]},
            "ISPI": {"rich_text": [{"text": {"content": issue_ispi}}]},
            "Priority": {"select": {"name": str(issue_priority)}},
            "Sprint": {"relation": sprint_pages},
            "Epic": {"relation": epic_page if epic_page and epic_page[0]["id"] else []},
            "Zeitlicher Fortschritt": {"number": 0}
        }

        notion.pages.create(parent={"database_id": database_id}, properties=new_page).get("id")

def main():

    notion, jira, database_id, sprints_database_id, epic_database_id = setup()
    _, _, update_issues = parse_cmd_args()
    issues = get_jira_issues(jira, notion, database_id)

    if update_issues:
        print_info("Updating Notion issues")
        update_all_notion_issues(notion, database_id, issues)
        print_info("Updated Notion issues")

    else:

        existing_ispis = get_already_migrated_entries(notion, database_id)

        add_notion_entries_loop(jira, notion, database_id, sprints_database_id, epic_database_id, issues, existing_ispis)
        print_info("Amount of JIRA issues added to notion database: " + str(len(issues) - amount_issues_skipped))


if __name__ == "__main__":
    main()