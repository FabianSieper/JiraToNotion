from notion_client import Client
from jira import JIRA
from bin.config import *
from bin.helper_functions import *
from bin.notion_jira_connector import *
import os

def setup():

    # Fetch environment variables
    if "NOTION_API_KEY" in os.environ:    
        NOTION_API_KEY = os.environ["NOTION_API_KEY"]
    
    if "JIRA_USERNAME" in os.environ:    
        JIRA_USERNAME = os.environ["JIRA_USERNAME"]
    
    if "JIRA_PASSWORD" in os.environ:
        JIRA_PASSWORD = os.environ["JIRA_PASSWORD"]

    # Initialize clients
    notion = Client(auth=NOTION_API_KEY)
    jira = JIRA(server=JIRA_SERVER_URL, basic_auth=(JIRA_USERNAME, JIRA_PASSWORD))

    # Retrieve the Notion-JIRA-issue database
    database_id = get_database_id(notion, ISSUES_DATABASE_URL, ISSUES_DATABASE_NAME)
    print_info("Found issues-database with id" + database_id)

    # Retrieve the Notion-Sprint database
    sprints_database_id = get_database_id(notion, SPRINTS_DATABASE_URL, SPRINTS_DATABASE_NAME)
    print_info("Found sprints-database with id " + sprints_database_id)

    # Retrieve the Notion-Epics database
    epics_database_id = get_database_id(notion, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)
    print_info("Found epics-database with id " + epics_database_id)

    return notion, jira, database_id, sprints_database_id, epics_database_id


def main():

    notion_client, jira_client, issue_database_id, sprints_database_id, epic_database_id = setup()
    epics, issues, update = parse_cmd_args()

    if update:

        print_info("Fetching all Notion Issues")
        notion_issues = get_notion_pages(notion_client, issue_database_id)

        update_existing_notion_issues(notion_client, jira_client, issue_database_id, sprints_database_id, notion_issues)
        print_info("Successfully updated existing Notion pages")

        add_missing_notion_issues(jira_client, notion_client, issue_database_id, epic_database_id, sprints_database_id, notion_issues)
        print_info("Successfully added missing Notion pages")

    elif epics:

        issue_list = get_jira_issue_list_from_ispis(jira_client, epics, isEpic=True, convert_to_ispi_strings=False)
        existing_ispis = get_already_migrated_entries(notion_client, issue_database_id, convert_to_ispis_strings=True)

        amount_issues_skipped = add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)
        print_info("Amount of JIRA issues added to Notion database based on Epics: " + str(len(issue_list) - amount_issues_skipped))

    elif issues:

        issue_list = get_jira_issue_list_from_ispis(jira_client, issues, isEpic=False, convert_to_ispi_strings=False)
        existing_ispis = get_already_migrated_entries(notion_client, issue_database_id, convert_to_ispis_strings=True)

        amount_issues_skipped = add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)
        print_info("Amount of JIRA issues added to Notion database based on Issues: " + str(len(issue_list) - amount_issues_skipped))


if __name__ == "__main__":
    main()