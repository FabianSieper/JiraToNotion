from bin.config import *
from bin.helper_functions import *
from bin.notion_connector import *
from bin.jira_connector import *

_existing_epic_pages = None

def get_issue_list_from_notion_epics(jira, notion_client, epic_database_id):

    print_info("Fetching Issues for already created Notion Epics")

    existing_epic_pages = get_notion_pages(notion_client, epic_database_id)

    epic_list = [page["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for page in existing_epic_pages if len(page["properties"]["ISPI"]["rich_text"]) > 0]
    print_info("Successfully fetched list of existing notion epic pages")

    issue_list = get_jira_issue_list_from_ispis(jira, epic_list, isEpic=True, convert_to_ispi_strings=False)
    print_info("Successfully fetched list of existing notion issue pages")

    return issue_list



def get_jira_issues(jira, notion_client, database_id, epic_database_id):

    epics, issues, update, update_issues = parse_cmd_args()
    issue_list = []

    # If a list of epic-ispis is given
    if epics:
        issue_list = get_jira_issue_list_from_ispis(jira, epics, isEpic=True, convert_to_ispi_strings=False)

    # If a list of issue-ispis is given
    elif issues:
        issue_list = get_jira_issue_list_from_ispis(jira, issues, isEpic=False, convert_to_ispi_strings=False)

    # If missing issues for the given notion epics shall be added
    elif update:
        issue_list = get_issue_list_from_notion_epics(jira, notion_client, epic_database_id)

    else:
        print_info("No valid  task was recognized.")

    return issue_list    



def get_or_create_epic_page(jira, notion_client, epic_database_id, epic_ispi):

    global _existing_epic_pages

    if not _existing_epic_pages:

        print_info("Fetching existing epic pages in Notion")

        existing_epic_pages_list = get_notion_pages(notion_client, epic_database_id)

        _existing_epic_pages = {epic_page['properties']['ISPI']['rich_text'][0]['text']['content'] : epic_page for epic_page in existing_epic_pages_list if len(epic_page['properties']['ISPI']['rich_text']) > 0}

    if epic_ispi in _existing_epic_pages:
        return _existing_epic_pages[epic_ispi]
    else:

        print_info("Creating new epic page in Notion")
        epic = get_jira_issue_list_from_ispis(jira, epic_ispi, isEpic=True, convert_to_ispi_strings=False)[0]

        _, summary, _, description, url, _, _, _, _ = get_jira_issue_information(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": summary}}]},
            "URL": {"url": url},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]},
            "Description": {"rich_text": [{"text": {"content": description if description else ""}}]},
        }

        new_epic_page = create_notion_page(notion_client, epic_database_id, new_epic_page)
        _existing_epic_pages[epic_ispi] = new_epic_page
        return new_epic_page



def update_all_notion_issues(notion_client, jira_client, database_id, sprints_database_id):

    # Get all notion issues
    print_info("Fetching all Notion Issues")
    notion_issues = get_notion_pages(notion_client, database_id)
    notion_issues_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    # Get corresponding jira issues
    print_info("Fetching all Jira Issues for found Notion Issues")
    jira_issues = get_jira_issue_list_from_ispis(jira_client, notion_issues_ispis, convert_to_ispi_strings=False)

    # Get list of jira issues, which have been updated
    updated_jira_issues = get_updated_jira_issues(notion_client, jira_issues, notion_issues, sprints_database_id)
    print_info("Found outdated Notion issues: " + str(len(updated_jira_issues)))

    # Update Notion issues, where the paramter of interest is differnt
    for jira_issue in tqdm(updated_jira_issues, "Updating Notion issues ... "):
        update_notion_issues(notion_client, database_id, sprints_database_id, jira_issue)

