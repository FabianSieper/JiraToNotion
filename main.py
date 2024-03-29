from notion_client import Client
from jira import JIRA
from bin.config import *
from bin.helper_functions import *
from bin.notion_jira_connector import *
import os

def setup():

    global JIRA_AUTH_TOKEN
    global JIRA_SERVER_URL
    global ISSUES_DATABASE_NAME
    global ISSUES_DATABASE_URL
    global SPRINTS_DATABASE_NAME
    global SPRINTS_DATABASE_URL
    global EPICS_DATABASE_NAME
    global EPICS_DATABASE_URL
    global NOTION_API_KEY
    
    # Fetch environment variables
    if "NOTION_API_KEY" in os.environ:    
        NOTION_API_KEY = os.environ["NOTION_API_KEY"]
    
    if "JIRA_AUTH_TOKEN" in os.environ:
        JIRA_AUTH_TOKEN = os.environ["JIRA_AUTH_TOKEN"]

    # Initialize clients
    notion = Client(auth=NOTION_API_KEY)
    jira = JIRA(server=JIRA_SERVER_URL, token_auth=JIRA_AUTH_TOKEN, validate=True)

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
    epics, issues, update_notion, update_jira, sprints = parse_cmd_args()

    if update_notion:
        print_info("Fetching all Notion Issues")
        notion_issues = get_notion_pages(notion_client, issue_database_id)

        update_existing_notion_issues(notion_client, jira_client, issue_database_id, sprints_database_id, notion_issues)
        print_info("Successfully updated existing Notion pages")

        add_missing_notion_issues(jira_client, notion_client, issue_database_id, epic_database_id, sprints_database_id, notion_issues)
        print_info("Successfully added missing Notion pages")

    elif update_jira:

        print_warning("This functionality is currently in beta - use with caution.")
        answer = input("Are you sure you would like to proceed? [Y]es/[N]o")

        if answer.lower() == "y":
            print_info("Fetching all Notion Issues")
            notion_issues = get_notion_pages(notion_client, issue_database_id)

            update_jira_issues(notion_client, jira_client, sprints_database_id, notion_issues)
    
    elif epics:

        issue_list = get_jira_issue_list_from_ispis(jira_client, epics, isEpic=True, convert_to_ispi_strings=False)
        existing_ispis = get_already_migrated_entries(notion_client, issue_database_id, issue_list=issue_list, convert_to_ispis_strings=True)

        skipped_issues = add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)
        issues_added = [issue.key for issue in issue_list if issue not in skipped_issues] if issue_list != -1 else []
        amount_issues_added = len(issues_added)

        if amount_issues_added > 0:
            print_info(str(amount_issues_added) + " issues added to Notion database: " + str(issues_added))
        else:
            print_info("No issue(s) were added to Notion.")

    elif issues:

        issue_list = get_jira_issue_list_from_ispis(jira_client, issues, isEpic=False, convert_to_ispi_strings=False)

        existing_ispis = get_already_migrated_entries(notion_client, issue_database_id, issue_list=issue_list, convert_to_ispis_strings=True)

        skipped_issues = add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)
        issues_added = [issue.key for issue in issue_list if issue not in skipped_issues] if issue_list != -1 else []
        amount_issues_added = len(issues_added)

        if amount_issues_added > 0:
            print_info(str(amount_issues_added) + " issues added to Notion database: " + str(issues_added))
        else:
            print_info("No issue(s) were added to Notion.")

    elif sprints:
        issue_list = get_jira_issue_list_from_ispis(jira_client, None, isEpic=False, convert_to_ispi_strings=False)
        existing_ispis = get_already_migrated_entries(notion_client, issue_database_id, issue_list=issue_list, convert_to_ispis_strings=True)

        skipped_issues = add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)
        issues_added = [issue.key for issue in issue_list if issue not in skipped_issues] if issue_list != -1 else []
        amount_issues_added = len(issues_added)

        if amount_issues_added > 0:
            print_info(str(amount_issues_added) + " issues added to Notion database: " + str(issues_added))
        else:
            print_info("No issue(s) were added to Notion.")

    else:

        print_info("The selected mode does not exist!")
        
if __name__ == "__main__":
    main()