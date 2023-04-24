from notion_client import Client
from jira import JIRA
from tqdm import tqdm
from config import (
    NOTION_API_KEY,
    NOTION_DATABASE_URL,
    NOTION_DATABASE_NAME,
    SPRINTS_DATABASE_URL,
    SPRINTS_DATABASE_NAME,
    DEFAULT_NOTION_LABEL,
    AMOUNT_JIRA_RESULTS,
    JIRA_SERVER_URL,
    JIRA_USERNAME,
    JIRA_PASSWORD,
    CAVORS_SPRINT_PREFIX
)
from helper_functions import *
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


def add_notion_entries_loop(jira, notion, database_id, sprints_database_id, epic_database_id, issues, existing_titles):
    
    global amount_issues_skipped

    # Add JIRA issues to the Notion database if not already present
    for issue in tqdm(issues, "Writing issues to notion database ..."):

        _, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, epic_ispi = get_issue_information(issue)

        # Skip issues
        if isIssueSkipped(issue, existing_titles):
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
            "Story": {"title": [{"text": {"content": issue_summary}}]},
            "Status": {"status": {"name": issue_status}},
            "Story URL": {"url": issue_url},
            "Description": {"rich_text": [{"text": {"content": issue_description if issue_description else ""}}]},
            "Priority": {"select": {"name": str(issue_priority)}},
            "Sprint": {"relation": sprint_pages},
            "Epic": {"relation": epic_page if epic_page and epic_page[0]["id"] else []}
        }

        notion.pages.create(parent={"database_id": database_id}, properties=new_page).get("id")

def main():


    notion, jira, database_id, sprints_database_id, epic_database_id = setup()

    issues = get_jira_issues(jira, notion)

    existing_titles = get_already_migrated_entries(notion, database_id, issues)

    add_notion_entries_loop(jira, notion, database_id, sprints_database_id, epic_database_id, issues, existing_titles)

    print_info("Amount of JIRA issues added to notion database: " + str(len(issues) - amount_issues_skipped))


if __name__ == "__main__":
    main()